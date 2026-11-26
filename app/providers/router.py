"""Panggilan ke provider lewat LiteLLM (satu format untuk OpenAI/Gemini/Claude/Ollama)."""
import litellm

from app.config import settings
from app.policy.engine import is_local


async def complete(model: str, messages: list[dict], **kwargs) -> str:
    extra = {"api_base": settings.local_api_base} if is_local(model) else {}
    resp = await litellm.acompletion(model=model, messages=messages, **extra, **kwargs)
    return resp.choices[0].message.content or ""
