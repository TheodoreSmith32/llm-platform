#!/usr/bin/env bash
# Jalankan gateway + CLI dalam satu terminal. Gateway mati otomatis saat CLI ditutup.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate

PORT="${PORT:-8000}"
uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --log-level warning &
GW_PID=$!
trap 'kill "$GW_PID" 2>/dev/null || true' EXIT

# tunggu gateway siap (maks ~15 detik)
for _ in $(seq 1 30); do
  if (echo > "/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then break; fi
  sleep 0.5
done

python cli.py --url "http://127.0.0.1:$PORT" "$@"
