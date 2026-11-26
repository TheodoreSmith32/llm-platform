import json

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.pii.detector import detect
from app.pii.masker import Masker

H = {"Authorization": "Bearer sk-internal-dev"}


def test_detect_types():
    t = "NIK 3171014507900001, kartu 4111 1111 1111 1111, email a@b.com, hp 081234567890"
    types = {e.type for e in detect(t)}
    assert {"NIK", "CREDIT_CARD", "EMAIL", "PHONE_ID"} <= types


def test_luhn_rejects_random_16_digits():
    assert "CREDIT_CARD" not in {e.type for e in detect("kode 1234 5678 9012 3456")}


def test_mask_roundtrip_is_consistent():
    m = Masker()
    masked = m.mask("hubungi a@b.com lalu a@b.com").text
    assert masked == "hubungi [EMAIL_1] lalu [EMAIL_1]"
    assert m.unmask(masked) == "hubungi a@b.com lalu a@b.com"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "audit_log_path", str(tmp_path / "audit.jsonl"))
    sent = {}

    async def fake_complete(model, messages, **kw):
        sent["model"], sent["messages"] = model, messages
        return "ok: " + messages[-1]["content"]

    monkeypatch.setattr("app.providers.router.complete", fake_complete)
    c = TestClient(app)
    c.sent, c.audit = sent, tmp_path / "audit.jsonl"
    return c


def post(c, model, content):
    return c.post("/v1/chat/completions", headers=H,
                  json={"model": model, "messages": [{"role": "user", "content": content}]})


def test_low_pii_masked_before_leaving_and_unmasked_after(client):
    r = post(client, "gpt-4o", "email saya a@b.com")
    assert r.status_code == 200
    assert "a@b.com" not in json.dumps(client.sent["messages"])  # provider tidak melihat nilai asli
    assert "a@b.com" in r.json()["choices"][0]["message"]["content"]
    assert r.json()["policy"]["action"] == "mask"


def test_restricted_pii_routes_to_local(client):
    r = post(client, "gpt-4o", "NIK 3171014507900001")
    assert r.json()["policy"]["action"] == "route_local"
    assert client.sent["model"] == settings.local_model


def test_restricted_blocked_without_local_model(client, monkeypatch):
    monkeypatch.setattr(settings, "local_model", "")
    assert post(client, "gpt-4o", "NIK 3171014507900001").status_code == 422


def test_audit_never_stores_raw_content(client):
    post(client, "gpt-4o", "email saya a@b.com")
    raw = client.audit.read_text()
    assert "a@b.com" not in raw and "prompt_sha256" in raw


def test_requires_api_key(client):
    assert client.post("/v1/chat/completions", json={}).status_code == 401
