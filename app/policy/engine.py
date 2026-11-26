"""Policy: putuskan apa yang boleh keluar ke provider eksternal."""
from dataclasses import dataclass
from enum import Enum

from app.config import settings
from app.pii.detector import Entity

# Level sensitivitas per tipe entitas.
LOW = {"EMAIL", "PHONE_ID"}  # boleh keluar setelah di-mask
RESTRICTED = {"NIK", "CREDIT_CARD", "ACCOUNT_NO", "NPWP"}  # tidak boleh keluar sama sekali


class Action(str, Enum):
    ALLOW = "allow"
    MASK = "mask"
    ROUTE_LOCAL = "route_local"
    BLOCK = "block"


@dataclass(frozen=True)
class Decision:
    action: Action
    model: str
    reason: str


def is_local(model: str) -> bool:
    return model.startswith(("ollama/", "hosted_vllm/"))


def decide(model: str, entities: list[Entity]) -> Decision:
    if not entities:
        return Decision(Action.ALLOW, model, "no PII detected")
    if is_local(model):
        return Decision(Action.ALLOW, model, "local model, data stays on-prem")

    types = {e.type for e in entities}
    if types & RESTRICTED:
        if settings.local_model:
            return Decision(
                Action.ROUTE_LOCAL,
                settings.local_model,
                f"restricted PII {sorted(types & RESTRICTED)} -> local model only",
            )
        return Decision(Action.BLOCK, model, "restricted PII and no local model configured")
    return Decision(Action.MASK, model, f"low-sensitivity PII {sorted(types)} masked")
