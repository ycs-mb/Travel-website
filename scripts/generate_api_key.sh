#!/bin/bash
# Generate a secure API key and update .env file

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

echo "🔐 Generating secure API key..."
echo ""

# Generate a secure random key
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "Generated API Key:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$API_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .env exists
if [ -f .env ]; then
    # Update existing .env file
    if grep -q "^API_KEY=" .env; then
        # Replace existing API_KEY
        sed -i.bak "s|^API_KEY=.*|API_KEY=$API_KEY|" .env
        echo "✅ Updated API_KEY in .env file"
    else
        # Add API_KEY to .env
        echo "API_KEY=$API_KEY" >> .env
        echo "✅ Added API_KEY to .env file"
    fi
else
    # Create new .env file
    echo "API_KEY=$API_KEY" > .env
    echo "✅ Created .env file with API_KEY"
fi

echo ""
echo "📝 Next steps:"
echo "   1. Restart the API server: ./scripts/start_api.sh"
echo "   2. Use this key in your API requests:"
echo "      -H \"X-API-Key: $API_KEY\""
echo ""
echo "⚠️  Keep this key secret! Don't commit it to git."
