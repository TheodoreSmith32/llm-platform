from fastapi import FastAPI

from app.api import chat

# Upload file / S3 (app.api.files) sementara tidak dipasang.
app = FastAPI(title="LLM Platform")
app.include_router(chat.api)


@app.get("/healthz")
def healthz():
    return {"ok": True}
