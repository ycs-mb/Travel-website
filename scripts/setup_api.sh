#!/bin/bash
# Setup script for FastAPI server

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

echo "🚀 Setting up FastAPI Photo Analysis Server..."

# Check if we're in the right directory
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found in $PROJECT_DIR"
    exit 1
fi

# 1. Install dependencies
echo "📦 Installing FastAPI dependencies..."
uv add fastapi uvicorn python-multipart

# 2. Create necessary directories
echo "📁 Creating directories..."
mkdir -p api
mkdir -p uploads
mkdir -p cache
mkdir -p output

# 3. Set up environment variables
echo "🔧 Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "# API Configuration
API_KEY=your-secret-api-key-$(openssl rand -hex 16)
API_HOST=0.0.0.0
API_PORT=8000
" > .env
    echo "✅ Created .env file with random API key"
else
    echo "✅ .env file already exists"
fi

# 4. Verify Vertex AI credentials
echo "🔑 Checking Vertex AI credentials..."
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "   You can set it with: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
    echo "   Or use: gcloud auth application-default login"
else
    echo "✅ GOOGLE_APPLICATION_CREDENTIALS is set"
fi

# 5. Test imports
echo "🧪 Testing Python imports..."
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

echo ""
echo "✅ FastAPI setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update config.yaml with your GCP project ID (api.google.project)"
echo "2. Set up Vertex AI credentials:"
echo "   gcloud auth application-default login"
echo "3. Start the server:"
echo "   ./scripts/start_api.sh"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
