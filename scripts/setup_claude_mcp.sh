#!/bin/bash
# Setup Photo Analysis MCP Server for Claude Desktop

set -e

echo "🔧 Setting up Photo Analysis MCP Server for Claude Desktop"
echo ""

# Get the absolute path to the project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo "📁 Project directory: $PROJECT_DIR"
echo "📝 Claude config file: $CONFIG_FILE"
echo ""

# Check if Claude Desktop is installed
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Claude Desktop config file not found!"
    echo "   Please install Claude Desktop first: https://claude.ai/download"
    exit 1
fi

# Backup existing config
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup: $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"

# Read existing config
EXISTING_CONFIG=$(cat "$CONFIG_FILE")

# Check if photo-analysis server already exists
if echo "$EXISTING_CONFIG" | grep -q '"photo-analysis"'; then
    echo "⚠️  Photo-analysis MCP server already configured!"
    echo "   Updating configuration..."
fi

# Create new config with photo-analysis server
python3 << EOF
import json
import sys
import os

config_file = "$CONFIG_FILE"
project_dir = "$PROJECT_DIR"

# Find uv path
uv_path = os.path.expanduser("~/.local/bin/uv")
if not os.path.exists(uv_path):
    # Fallback to which command
    import subprocess
    try:
        result = subprocess.run(['which', 'uv'], capture_output=True, text=True)
        if result.returncode == 0:
            uv_path = result.stdout.strip()
        else:
            uv_path = "uv"  # Fallback to command name
    except:
        uv_path = "uv"

# Read existing config
with open(config_file, 'r') as f:
    config = json.load(f)

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add or update photo-analysis server with absolute path
config['mcpServers']['photo-analysis'] = {
    "command": uv_path,
    "args": [
        "run",
        "--directory",
        project_dir,
        "python",
        "mcp/photo_analysis_server.py"
    ]
}

# Write updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Configuration updated successfully!")
print(f"Using uv at: {uv_path}")
EOF

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Restart Claude Desktop (Cmd+Q to quit, then reopen)"
echo "   2. Look for the MCP icon (🔌) in Claude Desktop"
echo "   3. Verify 'photo-analysis' appears in connected servers"
echo ""
echo "🧪 Test with these prompts in Claude Desktop:"
echo "   • 'What photo analysis tools do you have?'"
echo "   • 'Analyze the photo at $PROJECT_DIR/sample_images/IMG_3339.HEIC'"
echo "   • 'Generate a caption for my travel photo at [path]'"
echo ""
echo "📚 For more info, see: docs/MCP_SETUP.md"
echo ""
