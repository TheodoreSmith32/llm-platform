"""Deteksi PII berbasis regex + validasi (Luhn untuk kartu).

Sengaja dibuat sederhana dan deterministik. Antarmuka `detect()` bisa diganti
dengan Presidio/NER nanti tanpa mengubah modul lain.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Entity:
    type: str
    start: int
    end: int
    value: str


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


# Urutan = prioritas bila ada overlap (yang lebih spesifik dulu).
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("NIK", re.compile(r"(?<!\d)\d{16}(?!\d)")),  # divalidasi lagi di bawah
    ("NPWP", re.compile(r"(?<!\d)\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}(?!\d)")),
    ("CREDIT_CARD", re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")),
    ("PHONE_ID", re.compile(r"(?<!\d)(?:\+62|62|0)8\d{8,11}(?!\d)")),
    ("ACCOUNT_NO", re.compile(r"(?<!\d)\d{10,15}(?!\d)")),
]


def _valid_nik(v: str) -> bool:
    # NIK: 6 digit wilayah, tanggal lahir (DD, +40 untuk perempuan), bulan 01-12.
    day, month = int(v[6:8]), int(v[8:10])
    return (1 <= day <= 31 or 41 <= day <= 71) and 1 <= month <= 12


def detect(text: str) -> list[Entity]:
    found: list[Entity] = []
    taken: list[tuple[int, int]] = []

    for etype, pat in _PATTERNS:
        for m in pat.finditer(text):
            s, e = m.span()
            if any(s < te and e > ts for ts, te in taken):
                continue
            raw = m.group()
            digits = re.sub(r"\D", "", raw)
            if etype == "NIK" and not _valid_nik(raw):
                continue
            if etype == "CREDIT_CARD" and not (13 <= len(digits) <= 19 and _luhn_ok(digits)):
                continue
            found.append(Entity(etype, s, e, raw))
            taken.append((s, e))

    return sorted(found, key=lambda x: x.start)
