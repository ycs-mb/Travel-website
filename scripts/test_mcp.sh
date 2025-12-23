#!/bin/bash
# Test MCP server directly

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

echo "🧪 Testing MCP server..."
echo ""
echo "Starting MCP server (Ctrl+C to stop)..."
echo "The server should start without errors."
echo ""

uv run python mcp/photo_analysis_server.py
