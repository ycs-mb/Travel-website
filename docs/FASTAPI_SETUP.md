# FastAPI Server Setup Guide

## Quick Start

### 1. Start the Server

```bash
./scripts/start_api.sh
```

The server will start on `http://localhost:8000`

### 2. Test the Server

```bash
./scripts/test_api_server.sh
```

### 3. View API Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

The server uses Google Cloud service account keys from `keys.json` for Vertex AI authentication.

**Setup:**
1. Place your service account JSON file as `keys.json` in the project root
2. The server will automatically use it via `GOOGLE_APPLICATION_CREDENTIALS`

**API Key:**
- Default: `your-secret-api-key-here`
- Change via environment variable: `export API_KEY="your-custom-key"`
- Include in requests: `-H "X-API-Key: your-key"`

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Analyze Image (Full Pipeline)
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/image" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@path/to/image.jpg"
```

### Aesthetic Assessment Only
```bash
curl -X POST "http://localhost:8000/api/v1/agents/aesthetic" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@path/to/image.jpg"
```

### Categorization Only
```bash
curl -X POST "http://localhost:8000/api/v1/agents/filtering" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@path/to/image.jpg"
```

### Caption Generation Only
```bash
curl -X POST "http://localhost:8000/api/v1/agents/caption" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@path/to/image.jpg"
```

## Python Client Example

```python
import requests

# Analyze image
with open("photo.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze/image",
        headers={"X-API-Key": "your-secret-api-key-here"},
        files={"file": f}
    )

result = response.json()
print(f"Aesthetic Score: {result['aesthetic']['overall_aesthetic']}/5")
print(f"Category: {result['filtering']['category']}")
print(f"Caption: {result['caption']['concise']}")
print(f"Cost: ${result['total_cost_usd']:.4f}")
```

## Configuration

All settings are in `config.yaml`:

```yaml
api:
  google:
    project: "gcloud-photo-project"
    location: "us-central1"
    optimization:
      enable_image_resizing: true
      max_image_dimension: 1024
```

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i:8000)
```

### Authentication errors
```bash
# Verify keys.json exists
ls -la keys.json

# Check credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS
```

### Agent errors
Check the logs in the terminal where the server is running.

## Files Modified

- `api/fastapi_server.py` - Added Google Cloud authentication setup
- `scripts/start_api.sh` - Updated to export GOOGLE_APPLICATION_CREDENTIALS
- `scripts/test_api_server.sh` - Test script

## Next Steps

1. ✅ Start server: `./scripts/start_api.sh`
2. ✅ Test endpoints: `./scripts/test_api_server.sh`
3. ✅ View docs: http://localhost:8000/docs
4. 🚀 Integrate with your application!
