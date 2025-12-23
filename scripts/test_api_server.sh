#!/bin/bash
# Quick test script for FastAPI server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

echo "🧪 Testing Photo Analysis API Server"
echo "===================================="
echo ""

# Create output directory for test results
OUTPUT_DIR="$PROJECT_DIR/test_results"
mkdir -p "$OUTPUT_DIR"

# Get current timestamp for filenames
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Get API key from environment or use default
API_KEY="${API_KEY:-your-secret-api-key-here}"

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server is not running!"
    echo "   Start it with: ./scripts/start_api.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test health endpoint
echo "1️⃣ Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "$HEALTH_RESPONSE" | python3 -m json.tool

# Save health check
echo "$HEALTH_RESPONSE" | python3 -m json.tool > "$OUTPUT_DIR/health_${TIMESTAMP}.json"
echo ""

# Test with sample image (if available)
SAMPLE_IMAGE=$(find "$PROJECT_DIR/sample_images" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.HEIC" -o -name "*.heic" \) | head -1)

if [ -n "$SAMPLE_IMAGE" ]; then
    echo "2️⃣ Testing image analysis..."
    echo "   Uploading: $SAMPLE_IMAGE"
    echo ""
    
    # Create request metadata
    REQUEST_FILE="$OUTPUT_DIR/request_${TIMESTAMP}.json"
    cat > "$REQUEST_FILE" << EOF
{
  "endpoint": "POST /api/v1/analyze/image",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "headers": {
    "X-API-Key": "${API_KEY:0:10}...${API_KEY: -4}"
  },
  "files": {
    "file": "$(basename "$SAMPLE_IMAGE")"
  },
  "form_data": {
    "agents": ["aesthetic", "filtering", "caption"]
  }
}
EOF
    
    echo "📝 Request saved to: $REQUEST_FILE"
    
    # Make API call and save response
    RESPONSE_FILE="$OUTPUT_DIR/response_${TIMESTAMP}.json"
    
    curl -X POST "http://localhost:8000/api/v1/analyze/image" \
        -H "X-API-Key: $API_KEY" \
        -F "file=@$SAMPLE_IMAGE" \
        -F "agents=aesthetic" \
        -F "agents=filtering" \
        -F "agents=caption" \
        -s -o "$RESPONSE_FILE"
    
    # Display response
    cat "$RESPONSE_FILE" | python3 -m json.tool
    
    echo ""
    echo "📝 Response saved to: $RESPONSE_FILE"
    echo ""
    echo "✅ Analysis complete!"
else
    echo "⚠️  No sample images found in sample_images/"
    echo "   Skipping image analysis test"
fi

echo ""
echo "===================================="
echo "✅ All tests completed!"
echo ""
echo "� Test results saved in: $OUTPUT_DIR/"
echo "�📚 View full API docs at: http://localhost:8000/docs"

