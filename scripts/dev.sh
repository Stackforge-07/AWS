#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8010 &
api_pid=$!
(cd frontend && npm run dev) &
ui_pid=$!
trap 'kill "$api_pid" "$ui_pid" 2>/dev/null || true' EXIT INT TERM
wait "$api_pid" "$ui_pid"
