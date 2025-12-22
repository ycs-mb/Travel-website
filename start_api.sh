#!/bin/bash
# Start FastAPI server

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Start server
echo "🚀 Starting FastAPI server on http://localhost:${API_PORT:-8000}"
echo "📚 API docs available at http://localhost:${API_PORT:-8000}/docs"
echo ""
uv run uvicorn api.fastapi_server:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --reload
