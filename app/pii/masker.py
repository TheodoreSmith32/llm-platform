"""Masking reversible: nilai asli diganti token, mapping hanya hidup di memori request."""
from dataclasses import dataclass, field

from app.pii.detector import Entity, detect


@dataclass
class MaskResult:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # token -> nilai asli
    entities: list[Entity] = field(default_factory=list)


class Masker:
    """Satu instance per request supaya token konsisten antar pesan."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._value_to_token: dict[str, str] = {}
        self.mapping: dict[str, str] = {}

    def _token(self, etype: str, value: str) -> str:
        if value in self._value_to_token:
            return self._value_to_token[value]
        n = self._counters.get(etype, 0) + 1
        self._counters[etype] = n
        tok = f"[{etype}_{n}]"
        self._value_to_token[value] = tok
        self.mapping[tok] = value
        return tok

    def mask(self, text: str, entities: list[Entity] | None = None) -> MaskResult:
        ents = detect(text) if entities is None else entities
        out, last = [], 0
        for e in ents:
            out.append(text[last:e.start])
            out.append(self._token(e.type, e.value))
            last = e.end
        out.append(text[last:])
        return MaskResult("".join(out), dict(self.mapping), ents)

    def unmask(self, text: str) -> str:
        for tok, val in self.mapping.items():
            text = text.replace(tok, val)
        return text
