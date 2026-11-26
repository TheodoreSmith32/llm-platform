"""Chat interaktif di terminal lewat gateway (PII masking + policy tetap berlaku).

Jalankan gateway dulu:  uvicorn app.main:app
Lalu:                   python cli.py --model gpt-4o-mini
"""
import argparse
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.getenv("CHAT_MODEL", "gpt-4o-mini"))
    p.add_argument("--url", default=os.getenv("GATEWAY_URL", "http://localhost:8000"))
    p.add_argument("--key", default=os.getenv("GATEWAY_KEY", "sk-internal-dev"))
    args = p.parse_args()

    history: list[dict] = []
    print(f"model={args.model}  gateway={args.url}  (ketik /exit untuk keluar, /reset untuk ulang)\n")

    while True:
        try:
            text = input("kamu> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text == "/exit":
            break
        if text == "/reset":
            history.clear()
            print("[riwayat dihapus]")
            continue

        history.append({"role": "user", "content": text})
        try:
            r = httpx.post(
                f"{args.url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {args.key}"},
                json={"model": args.model, "messages": history},
                timeout=120,
            )
        except httpx.HTTPError as exc:
            print(f"[error] gateway tidak terjangkau: {exc}", file=sys.stderr)
            history.pop()
            continue

        if r.status_code != 200:
            try:
                detail = r.json().get("detail", r.text)
            except ValueError:
                detail = r.text
            print(f"[{r.status_code}] {detail}")
            history.pop()
            continue

        data = r.json()
        answer = data["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": answer})
        pol = data["policy"]
        print(f"ai> {answer}\n    [{pol['action']} via {data['model']}: {pol['reason']}]\n")


if __name__ == "__main__":
    main()
