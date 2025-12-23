# Photo Analysis API Documentation

Complete guide for using the Travel Photo Analysis agents as APIs.

## 🎯 What's Available

You now have **TWO** ways to use your photo analysis agents:

### 1️⃣ **REST API (FastAPI)** - For Web/Mobile Apps
- **Perfect for**: Web applications, mobile apps, microservices, any HTTP client
- **Documentation**: Auto-generated at `/docs` (Swagger UI)
- **Authentication**: API key based
- **Protocol**: HTTP/HTTPS
- **Status**: ✅ **Ready to use**

### 2️⃣ **MCP Server** - For Claude Desktop
- **Perfect for**: Claude Desktop integration, AI-native workflows
- **Documentation**: Built into Claude Desktop
- **Authentication**: Local (no auth needed)
- **Protocol**: Model Context Protocol (MCP)
- **Status**: ✅ **Ready to use**

---

## 🚀 Quick Start (Choose One)

### Option A: REST API

```bash
# 1. Setup
./scripts/setup_api.sh

# 2. Start server
./scripts/start_api.sh

# 3. Test
curl http://localhost:8000/health
```

**Access API docs**: http://localhost:8000/docs

### Option B: MCP Server

```bash
# 1. Setup
./scripts/setup_mcp.sh

# 2. Restart Claude Desktop

# 3. Use in Claude
"Analyze this photo: /path/to/image.jpg"
```

---

## 📚 Complete Documentation

| Document | Description |
|----------|-------------|
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | ⭐ **START HERE** - Complete setup & testing guide |
| **[API_QUICKSTART.md](docs/API_QUICKSTART.md)** | Quick examples for both APIs |
| **[API_INTEGRATION_OPTIONS.md](docs/API_INTEGRATION_OPTIONS.md)** | 8 different integration approaches |
| **[TOKEN_OPTIMIZATION.md](docs/TOKEN_OPTIMIZATION.md)** | Cost optimization strategies |

---

## 📂 File Structure

```
Travel-website/
├── api/
│   └── fastapi_server.py       # ✅ REST API server
│
├── mcp/
│   └── photo_analysis_server.py # ✅ MCP server
│
├── scripts/
│   ├── setup_api.sh            # Setup REST API
│   └── setup_mcp.sh            # Setup MCP server
│
├── tests/
│   ├── test_api.py             # REST API tests
│   └── test_mcp.py             # MCP server tests
│
├── examples/
│   └── api_client_example.py   # Python client examples
│
├── docs/
│   ├── API_QUICKSTART.md
│   ├── API_INTEGRATION_OPTIONS.md
│   └── TOKEN_OPTIMIZATION.md
│
├── SETUP_GUIDE.md              # ⭐ Main setup guide
└── API_README.md               # This file
```

---

## 💡 Quick Examples

### REST API (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyze/image",
    headers={"X-API-Key": "your-key"},
    files={"file": open("photo.jpg", "rb")}
)

result = response.json()
print(f"Score: {result['aesthetic']['overall_aesthetic']}/5")
print(f"Cost: ${result['total_cost_usd']:.4f}")
```

### REST API (cURL)

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/image" \
  -H "X-API-Key: your-key" \
  -F "file=@photo.jpg"
```

### REST API (JavaScript)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/analyze/image', {
  method: 'POST',
  headers: { 'X-API-Key': 'your-key' },
  body: formData
});

const result = await response.json();
console.log('Aesthetic:', result.aesthetic.overall_aesthetic);
```

### MCP Server (Claude Desktop)

Just talk naturally to Claude:

```
User: "Analyze this travel photo: /Users/ycs/Photos/vacation.jpg"

Claude: [Uses analyze_photo tool automatically]

Photo Analysis Report

Aesthetic Quality: 5/5
- Composition: 4/5
- Framing: 5/5
- Lighting: 4/5
...

Total Cost: $0.0045
```

---

## 🔧 Configuration

All settings in `config.yaml`:

```yaml
# Token optimization (reduces costs by 50-60%)
api:
  google:
    optimization:
      enable_image_resizing: true      # Resize images
      max_image_dimension: 1024        # Max size
      use_concise_prompts: true        # Short prompts
      skip_captions_for_rejected: true # Skip rejected

# Cost tracking
cost_tracking:
  enabled: true
  log_per_image: true
  alert_threshold_usd: 1.0
```

---

## 📊 API Endpoints (REST API)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/analyze/image` | POST | Full analysis |
| `/api/v1/agents/aesthetic` | POST | Aesthetic only |
| `/api/v1/agents/filtering` | POST | Categorization only |
| `/api/v1/agents/caption` | POST | Caption only |
| `/api/v1/usage/tokens` | GET | Token stats |

**Full docs**: http://localhost:8000/docs

---

## 🛠️ MCP Tools

Available in Claude Desktop:

| Tool | Description |
|------|-------------|
| `analyze_photo` | Full analysis pipeline |
| `assess_aesthetic_quality` | Aesthetic scoring |
| `categorize_photo` | Categorization |
| `generate_caption` | Caption generation |
| `get_token_usage` | Cost statistics |

---

## 💰 Cost Optimization

**With optimizations enabled**:
- Image resizing: **50-70% savings**
- Concise prompts: **80% input token savings**
- Skip rejected: **40% fewer API calls**

**Total savings**: ~**55-60%**

**Example**:
- Without optimization: $0.45 per 150 images
- With optimization: $0.20 per 150 images
- **Savings**: $0.25 per batch

See [TOKEN_OPTIMIZATION.md](docs/TOKEN_OPTIMIZATION.md) for details.

---

## 🧪 Testing

### REST API

```bash
# Install test dependencies
uv add requests python-dotenv

# Run tests
python tests/test_api.py
```

### MCP Server

```bash
# Quick test
python tests/test_mcp.py --quick

# Full test
python tests/test_mcp.py
```

---

## 🐛 Troubleshooting

### REST API won't start

```bash
# Check if port in use
lsof -i :8000

# Use different port
uvicorn api.fastapi_server:app --port 8001
```

### MCP server not in Claude Desktop

1. Check config: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json`
2. Verify path is absolute
3. Restart Claude Desktop (Cmd+Q)
4. Check logs: `~/Library/Logs/Claude/`

### Vertex AI errors

```bash
# Authenticate
gcloud auth application-default login

# Verify project
gcloud config get-value project

# Update config.yaml
api:
  google:
    project: "your-actual-project-id"
```

---

## 🚀 Production Deployment

### Docker (REST API)

```bash
docker build -t photo-api .
docker run -p 8000:8000 photo-api
```

### Cloud Run (Google Cloud)

```bash
gcloud run deploy photo-analysis \
  --source . \
  --platform managed \
  --region us-central1
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Single image | 2-4 seconds |
| Batch (10 images) | 20-30 seconds |
| Max concurrent | 10 requests |
| Token usage | 1,500-2,500/image |
| Cost per image | $0.0013-0.0020 |

**Tips for better performance**:
- Enable image resizing
- Use parallel processing
- Cache results for duplicates

---

## 🔐 Security

**Production checklist**:
- [ ] Change default API key
- [ ] Use HTTPS only
- [ ] Implement rate limiting
- [ ] Add request validation
- [ ] Set up monitoring
- [ ] Restrict CORS origins
- [ ] Use OAuth 2.0
- [ ] Enable API key rotation

---

## 📝 Example Use Cases

### 1. Photo Gallery Website
→ Use **REST API** to analyze uploaded photos, show quality scores, generate captions

### 2. Mobile Photo App
→ Use **REST API** from iOS/Android to assess photo quality before upload

### 3. Travel Blog Platform
→ Use **REST API** to auto-categorize and caption travel photos

### 4. Claude Desktop Workflow
→ Use **MCP Server** to analyze photos while chatting with Claude

### 5. Photo Curation Service
→ Use **REST API** for batch processing large photo collections

### 6. Social Media Manager
→ Use **MCP Server** to get caption suggestions in Claude Desktop

---

## 🎓 Learning Resources

1. **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
2. **MCP Documentation**: https://modelcontextprotocol.io/
3. **Vertex AI Docs**: https://cloud.google.com/vertex-ai/docs
4. **Our Examples**: See `examples/api_client_example.py`

---

## 🤝 Support

- **Setup issues**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API questions**: Check http://localhost:8000/docs
- **Cost optimization**: See [TOKEN_OPTIMIZATION.md](docs/TOKEN_OPTIMIZATION.md)
- **Other integrations**: See [API_INTEGRATION_OPTIONS.md](docs/API_INTEGRATION_OPTIONS.md)

---

## 🎉 Next Steps

1. ✅ Choose your integration (REST API or MCP)
2. ✅ Run setup script (`./scripts/setup_api.sh` or `./scripts/setup_mcp.sh`)
3. ✅ Test with sample images
4. ✅ Monitor costs and optimize
5. 🚀 Deploy to production!

**Happy analyzing!** 📸✨
