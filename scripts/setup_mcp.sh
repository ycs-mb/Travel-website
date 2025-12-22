#!/bin/bash
# Setup script for MCP server

set -e  # Exit on error

echo "🚀 Setting up MCP Photo Analysis Server..."

# Check if we're in the right directory
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: Please run this script from the Travel-website directory"
    exit 1
fi

# 1. Install MCP dependencies
echo "📦 Installing MCP dependencies..."
uv add mcp

# 2. Get the absolute path to the MCP server
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MCP_SERVER_PATH="$PROJECT_DIR/mcp/photo_analysis_server.py"

echo "📍 MCP server path: $MCP_SERVER_PATH"

# 3. Detect Claude Desktop config location
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CLAUDE_CONFIG="$HOME/.config/claude/claude_desktop_config.json"
else
    # Windows (Git Bash)
    CLAUDE_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
fi

echo "📁 Claude Desktop config: $CLAUDE_CONFIG"

# 4. Create Claude config directory if it doesn't exist
mkdir -p "$(dirname "$CLAUDE_CONFIG")"

# 5. Create or update Claude Desktop config
if [ -f "$CLAUDE_CONFIG" ]; then
    echo "📝 Claude Desktop config exists"
    echo "   Please manually add the following to mcpServers section:"
    echo ""
    echo '  "photo-analysis": {'
    echo '    "command": "uv",'
    echo '    "args": ['
    echo '      "run",'
    echo '      "python",'
    echo "      \"$MCP_SERVER_PATH\""
    echo '    ]'
    echo '  }'
    echo ""
else
    echo "✅ Creating new Claude Desktop config..."
    cat > "$CLAUDE_CONFIG" << EOF
{
  "mcpServers": {
    "photo-analysis": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "$MCP_SERVER_PATH"
      ]
    }
  }
}
EOF
    echo "✅ Config created at: $CLAUDE_CONFIG"
fi

# 6. Test MCP server
echo "🧪 Testing MCP server..."
python3 -c "
import sys
sys.path.append('.')
try:
    from agents.aesthetic_assessment import AestheticAssessmentAgent
    from agents.filtering_categorization import FilteringCategorizationAgent
    from agents.caption_generation import CaptionGenerationAgent
    print('✅ All agent imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# 7. Create test script
cat > test_mcp.sh << 'EOF'
#!/bin/bash
# Test MCP server directly

echo "🧪 Testing MCP server..."
echo ""
echo "Starting MCP server (Ctrl+C to stop)..."
echo "The server should start without errors."
echo ""

uv run python mcp/photo_analysis_server.py
EOF

chmod +x test_mcp.sh

echo ""
echo "✅ MCP setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Verify Claude Desktop config:"
if [ -f "$CLAUDE_CONFIG" ]; then
    echo "   cat '$CLAUDE_CONFIG'"
else
    echo "   Create: $CLAUDE_CONFIG"
fi
echo "2. Restart Claude Desktop"
echo "3. Look for 'photo-analysis' in the MCP servers list (🔌 icon)"
echo "4. Test with: ./test_mcp.sh"
echo ""
echo "💬 Usage in Claude Desktop:"
echo '   "Analyze this photo: /path/to/image.jpg"'
echo '   "What is the aesthetic quality of /path/to/photo.jpg?"'
echo ""
