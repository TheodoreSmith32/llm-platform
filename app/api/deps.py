from fastapi import Header, HTTPException

from app.config import settings


def current_user(authorization: str = Header(default="")) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    if token not in settings.api_keys:
        raise HTTPException(401, "invalid API key")
    return token[:8]  # identitas kasar untuk audit; ganti dengan user store nanti
