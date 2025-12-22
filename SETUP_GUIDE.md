# Setup & Testing Guide

Complete guide to set up and test both the FastAPI REST API and MCP server.

## Prerequisites

- Python 3.11+
- `uv` package manager installed
- Google Cloud Platform account with Vertex AI enabled
- Sample images for testing

## Quick Setup (Both APIs)

### 1. Initial Setup

```bash
cd /Users/ycs/photo-app/Travel-website

# Make scripts executable
chmod +x scripts/*.sh

# Install base dependencies
uv sync
```

### 2. Configure Google Cloud

```bash
# Option A: Use Application Default Credentials (recommended)
gcloud auth application-default login

# Option B: Use service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 3. Update Configuration

Edit `config.yaml`:
```yaml
api:
  google:
    project: "your-actual-gcp-project-id"  # ← Update this
    location: "us-central1"
```

---

## Option 1: FastAPI REST API

### Setup

```bash
# Run setup script
./scripts/setup_api.sh
```

This will:
- ✅ Install FastAPI, Uvicorn, and dependencies
- ✅ Create necessary directories (api/, uploads/, cache/)
- ✅ Generate `.env` file with random API key
- ✅ Create `start_api.sh` startup script
- ✅ Verify all agent imports

### Configuration

1. **Update API Key** in `.env`:
```bash
nano .env
```

Change:
```
API_KEY=your-secret-api-key-12345...
```

2. **Verify GCP Project** in `config.yaml`:
```yaml
api:
  google:
    project: "your-project-id"  # Must match your GCP project
```

### Start the Server

```bash
./start_api.sh
```

Or manually:
```bash
uvicorn api.fastapi_server:app --host 0.0.0.0 --port 8000 --reload
```

### Access the API

- **Swagger UI (Interactive Docs)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Test the API

```bash
# Install test dependencies
uv add requests python-dotenv

# Run test suite
python tests/test_api.py
```

### Example Usage

**Python:**
```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"  # From .env file

headers = {"X-API-Key": API_KEY}

# Analyze image
with open("photo.jpg", "rb") as f:
    response = requests.post(
        f"{API_URL}/api/v1/analyze/image",
        headers=headers,
        files={"file": f},
        data={"agents": '["aesthetic", "caption"]'}
    )

result = response.json()
print(f"Aesthetic Score: {result['aesthetic']['overall_aesthetic']}/5")
print(f"Caption: {result['caption']['concise']}")
print(f"Cost: ${result['total_cost_usd']:.4f}")
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/image" \
  -H "X-API-Key: your-api-key" \
  -F "file=@sample_images/photo.jpg"
```

---

## Option 2: MCP Server (Claude Desktop)

### Setup

```bash
# Run setup script
./scripts/setup_mcp.sh
```

This will:
- ✅ Install MCP Python package
- ✅ Detect Claude Desktop config location
- ✅ Create/update `claude_desktop_config.json`
- ✅ Create test script
- ✅ Verify agent imports

### Manual Configuration (if needed)

**macOS:**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux:**
```bash
nano ~/.config/claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration:
```json
{
  "mcpServers": {
    "photo-analysis": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/Users/ycs/photo-app/Travel-website/mcp/photo_analysis_server.py"
      ]
    }
  }
}
```

**Important**: Use the absolute path to `photo_analysis_server.py` on your system!

### Restart Claude Desktop

After configuring, **completely quit and restart** Claude Desktop:
- Mac: Cmd+Q, then reopen
- Windows: Close from system tray, then reopen

### Verify Installation

1. Open Claude Desktop
2. Click the 🔌 (plug) icon in the bottom-left
3. Look for "photo-analysis" in the MCP servers list
4. Should show "Connected" status

### Test the MCP Server

```bash
# Quick test (just list tools)
python tests/test_mcp.py --quick

# Full test suite
python tests/test_mcp.py
```

### Usage in Claude Desktop

Once connected, you can use natural language:

**Example 1: Full Analysis**
```
Analyze this photo: /Users/ycs/Photos/vacation.jpg
```

**Example 2: Just Aesthetic**
```
What's the aesthetic quality of /Users/ycs/Downloads/sunset.jpg?
```

**Example 3: Caption Only**
```
Generate a caption for this image: ~/Pictures/mountain.jpg
```

**Example 4: Check Costs**
```
How much have I spent on photo analysis?
```

**Example 5: Batch Processing**
```
Analyze all photos in /Users/ycs/Photos/Trip2024/ and tell me which ones have the highest aesthetic scores
```

---

## Troubleshooting

### FastAPI Issues

**Issue**: Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
uvicorn api.fastapi_server:app --port 8001
```

**Issue**: 401 Unauthorized
- Check API key in `.env` matches your request header
- Verify `X-API-Key` header is set correctly

**Issue**: 500 Internal Server Error
```bash
# Check logs
tail -f /var/log/photo-analysis.log

# Verify Vertex AI credentials
gcloud auth application-default print-access-token
```

**Issue**: "Vertex AI client not initialized"
- Run: `gcloud auth application-default login`
- OR set: `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"`
- Verify project ID in config.yaml matches your GCP project

### MCP Server Issues

**Issue**: Server not appearing in Claude Desktop
1. Check JSON syntax: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool`
2. Verify absolute path to `photo_analysis_server.py`
3. Restart Claude Desktop completely (Cmd+Q)
4. Check Claude Desktop logs: `~/Library/Logs/Claude/`

**Issue**: "Command not found: uv"
- Use full path: `/usr/local/bin/uv` or wherever uv is installed
- Find with: `which uv`

**Issue**: Tool calls failing
```bash
# Test MCP server directly
./test_mcp.sh

# Check for Python errors
uv run python mcp/photo_analysis_server.py
```

**Issue**: "Image not found"
- Use absolute paths: `/Users/ycs/Photos/image.jpg`
- Check file permissions: `ls -l /path/to/image.jpg`

### Common Issues (Both)

**Issue**: Import errors
```bash
# Reinstall dependencies
uv sync --reinstall

# Check Python version
python --version  # Should be 3.11+
```

**Issue**: High token costs
```yaml
# Enable optimizations in config.yaml
api:
  google:
    optimization:
      enable_image_resizing: true
      use_concise_prompts: true
      skip_captions_for_rejected: true
```

**Issue**: Slow processing
- Enable image resizing (reduces API processing time)
- Increase parallel workers in config.yaml
- Use smaller test images initially

---

## Performance Testing

### Load Test (FastAPI)

```bash
# Install Apache Bench
brew install httpd  # macOS

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 \
   -H "X-API-Key: your-key" \
   -p test_image.jpg \
   -T "multipart/form-data; boundary=----boundary" \
   http://localhost:8000/api/v1/analyze/image
```

### Benchmark Script

```python
import time
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-key"

# Test 10 images
times = []
for i in range(10):
    start = time.time()

    with open(f"sample_images/photo_{i}.jpg", "rb") as f:
        response = requests.post(
            f"{API_URL}/api/v1/analyze/image",
            headers={"X-API-Key": API_KEY},
            files={"file": f}
        )

    elapsed = time.time() - start
    times.append(elapsed)

    print(f"Image {i+1}: {elapsed:.2f}s")

print(f"\nAverage: {sum(times)/len(times):.2f}s")
```

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8000

CMD ["uvicorn", "api.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t photo-analysis-api .

# Run
docker run -p 8000:8000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -v /path/to/key.json:/app/key.json \
  photo-analysis-api
```

### Environment Variables (Production)

```bash
# .env.production
API_KEY=$(openssl rand -hex 32)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
ENABLE_CORS=false
ALLOWED_ORIGINS=https://yourdomain.com
```

### Security Checklist

- [ ] Change default API key
- [ ] Use HTTPS only (add SSL/TLS)
- [ ] Implement rate limiting
- [ ] Add request validation
- [ ] Set up monitoring/logging
- [ ] Restrict CORS origins
- [ ] Use OAuth 2.0 for production auth
- [ ] Enable API key rotation
- [ ] Set up firewall rules
- [ ] Regular security audits

---

## Next Steps

1. ✅ Complete setup for your chosen option (FastAPI or MCP)
2. ✅ Run test suite to verify everything works
3. ✅ Try analyzing a few sample images
4. ✅ Monitor token usage and costs
5. ✅ Optimize configuration based on your needs
6. 📚 Read [API_INTEGRATION_OPTIONS.md](docs/API_INTEGRATION_OPTIONS.md) for other integration methods
7. 🚀 Deploy to production when ready

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Check logs in `output/*/logs/`
- **Token costs**: Monitor with `/api/v1/usage/tokens` endpoint
- **Performance**: See [TOKEN_OPTIMIZATION.md](docs/TOKEN_OPTIMIZATION.md)

Happy analyzing! 📸
