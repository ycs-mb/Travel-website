#!/bin/bash
# Start FastAPI server for Photo Analysis API

set -e

echo "🚀 Starting Photo Analysis API Server..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Set Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_DIR/keys.json"

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  Warning: keys.json not found at $GOOGLE_APPLICATION_CREDENTIALS"
    echo "   The API will use default Google Cloud credentials"
    echo ""
fi

# Load environment variables from .env file
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source <(grep -v '^#' "$PROJECT_DIR/.env" | grep -v '^$' | sed 's/\r$//')
    set +a
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  No .env file found, using defaults"
fi

# Set API key (will use value from .env if loaded, otherwise use default)
export API_KEY

echo "📝 Configuration:"
echo "   - Google Cloud credentials: $GOOGLE_APPLICATION_CREDENTIALS"
echo "   - API Key: ${API_KEY:0:10}..."
echo ""

# Start the server
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""

uv run uvicorn api.fastapi_server:app --host 0.0.0.0 --port 8000 --reload
