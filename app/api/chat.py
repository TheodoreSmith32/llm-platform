from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import current_user
from app.audit import log as audit
from app.pii.detector import detect
from app.pii.masker import Masker
from app.policy.engine import Action, decide
from app.providers import router as providers

api = APIRouter(prefix="/v1")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]


@api.post("/chat/completions")
async def chat(req: ChatRequest, user: str = Depends(current_user)):
    full_text = "\n".join(m.content for m in req.messages)
    entities = detect(full_text)
    decision = decide(req.model, entities)

    audit.record(
        user=user, requested_model=req.model, final_model=decision.model,
        action=decision.action.value, reason=decision.reason,
        entities=entities, prompt=full_text,
    )

    if decision.action is Action.BLOCK:
        raise HTTPException(422, f"blocked by policy: {decision.reason}")

    masker = Masker()
    # Restricted/route_local tidak keluar ke eksternal, jadi tidak perlu mask.
    messages = [m.model_dump() for m in req.messages]
    if decision.action is Action.MASK:
        for m in messages:
            m["content"] = masker.mask(m["content"]).text

    try:
        answer = await providers.complete(decision.model, messages)
    except Exception as exc:  # error provider (key salah, model tidak ada, dll.)
        raise HTTPException(502, f"provider error ({decision.model}): {exc}") from exc
    if decision.action is Action.MASK:
        answer = masker.unmask(answer)

    return {
        "model": decision.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}}],
        "policy": {"action": decision.action.value, "reason": decision.reason},
    }
