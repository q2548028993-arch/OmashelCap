#!/usr/bin/env bash
# Start API and frontend dev servers concurrently
# Usage: ./dev.sh

trap 'kill 0' EXIT

echo "Starting API on http://localhost:8000 ..."
uv run uvicorn api.main:app --reload --port 8000 &

echo "Starting frontend on http://localhost:5173 ..."
cd frontend && pnpm dev &

wait
