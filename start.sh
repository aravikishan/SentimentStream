#!/usr/bin/env bash
# Start the SentimentStream application with uvicorn.
set -euo pipefail

PORT="${PORT:-8009}"

echo "=== SentimentStream ==="
echo "Starting on http://0.0.0.0:$PORT"

exec uvicorn app:app --host 0.0.0.0 --port "$PORT" --reload
