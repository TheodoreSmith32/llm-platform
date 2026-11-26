"""Audit log JSONL. Tidak pernah menyimpan isi prompt, hanya metadata + hash."""
import hashlib
import json
import time
from collections import Counter

from app.config import settings
from app.pii.detector import Entity


def record(*, user: str, requested_model: str, final_model: str, action: str,
           reason: str, entities: list[Entity], prompt: str) -> dict:
    entry = {
        "ts": time.time(),
        "user": user,
        "requested_model": requested_model,
        "final_model": final_model,
        "action": action,
        "reason": reason,
        "entities": dict(Counter(e.type for e in entities)),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    }
    with open(settings.audit_log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
