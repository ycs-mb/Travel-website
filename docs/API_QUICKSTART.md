# API Integration Quick Start

This guide shows you how to quickly get started with the two most popular integration options.

## Option 1: REST API (FastAPI)

### Setup & Installation

1. **Install dependencies**:
```bash
cd /path/to/Travel-website
uv add fastapi uvicorn python-multipart
```

2. **Configure API key** (in `api/fastapi_server.py`):
```python
API_KEY = "your-secret-api-key-here"  # Change this!
```

3. **Start the server**:
```bash
uvicorn api.fastapi_server:app --host 0.0.0.0 --port 8000 --reload
```

4. **Access the API documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Usage Examples

#### Python Client

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"

headers = {"X-API-Key": API_KEY}

# Analyze single image
with open("vacation_photo.jpg", "rb") as f:
    files = {"file": f}
    data = {"agents": ["aesthetic", "caption"]}

    response = requests.post(
        f"{API_URL}/api/v1/analyze/image",
        headers=headers,
        files=files,
        data=data
    )

result = response.json()
print(f"Aesthetic Score: {result['aesthetic']['overall_aesthetic']}/5")
print(f"Caption: {result['caption']['concise']}")
print(f"Cost: ${result['total_cost_usd']:.4f}")
```

#### cURL

```bash
# Analyze image
curl -X POST "http://localhost:8000/api/v1/analyze/image" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@vacation_photo.jpg" \
  -F "agents=aesthetic" \
  -F "agents=caption"

# Get aesthetic score only
curl -X POST "http://localhost:8000/api/v1/agents/aesthetic" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@photo.jpg"
```

#### JavaScript/TypeScript

```typescript
const API_URL = 'http://localhost:8000';
const API_KEY = 'your-secret-api-key-here';

async function analyzePhoto(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('agents', 'aesthetic');
  formData.append('agents', 'caption');

  const response = await fetch(`${API_URL}/api/v1/analyze/image`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY
    },
    body: formData
  });

  const result = await response.json();
  return result;
}

// Usage
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];
const analysis = await analyzePhoto(file);

console.log('Aesthetic:', analysis.aesthetic.overall_aesthetic);
console.log('Caption:', analysis.caption.concise);
```

### API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analyze/image` | POST | Full analysis of single image |
| `/api/v1/analyze/batch` | POST | Submit batch job (async) |
| `/api/v1/analyze/status/{job_id}` | GET | Check batch job status |
| `/api/v1/agents/aesthetic` | POST | Aesthetic assessment only |
| `/api/v1/agents/filtering` | POST | Categorization only |
| `/api/v1/agents/caption` | POST | Caption generation only |
| `/api/v1/usage/tokens` | GET | Token usage statistics |
| `/health` | GET | Health check |

### Response Format

```json
{
  "job_id": "uuid",
  "status": "completed",
  "image_id": "photo_001",
  "aesthetic": {
    "composition": 4,
    "framing": 5,
    "lighting": 4,
    "subject_interest": 5,
    "overall_aesthetic": 5,
    "notes": "Exceptional composition with rule of thirds..."
  },
  "filtering": {
    "category": "Landscape",
    "subcategories": ["mountain", "sunset"],
    "time_category": "Golden Hour",
    "location": "(45.1234, -122.5678)",
    "passes_filter": true,
    "flagged": false,
    "flags": [],
    "reasoning": "Passed all criteria. Quality Score: 4/3..."
  },
  "caption": {
    "concise": "Golden sunset over mountain peaks",
    "standard": "As golden hour light bathes the mountain peaks...",
    "detailed": "This photograph captures...",
    "keywords": ["mountain", "sunset", "landscape", "golden hour"]
  },
  "token_usage": {
    "aesthetic": {
      "prompt_token_count": 1234,
      "candidates_token_count": 567,
      "total_token_count": 1801,
      "estimated_cost_usd": 0.0023
    },
    "caption": { ... }
  },
  "total_cost_usd": 0.0045,
  "processing_time_seconds": 3.2
}
```

---

## Option 2: MCP Server (Claude Desktop Integration)

### Setup & Installation

1. **Install MCP SDK**:
```bash
cd /path/to/Travel-website
uv add mcp
```

2. **Configure Claude Desktop**:

Edit `~/.config/claude/claude_desktop_config.json` (Mac/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

3. **Restart Claude Desktop**

4. **Verify installation**:
In Claude Desktop, you should see "photo-analysis" in the MCP servers list (🔌 icon).

### Usage in Claude Desktop

Once configured, you can use natural language in Claude Desktop:

**Example 1: Full Analysis**
```
User: "Analyze this photo: /Users/ycs/Photos/vacation.jpg"

Claude: [Uses analyze_photo tool]

Photo Analysis Report

Aesthetic Quality: 5/5
- Composition: 4/5
- Framing: 5/5
- Lighting: 4/5
- Subject Interest: 5/5

Exceptional composition with rule of thirds...

Categorization: ✅ PASSED
- Category: Landscape
- Time: Golden Hour
- Location: (45.1234, -122.5678)

Captions:
Concise: Golden sunset over mountain peaks
Standard: As golden hour light bathes the mountain peaks...
...

Total Cost: $0.0045
```

**Example 2: Just Aesthetic Score**
```
User: "What's the aesthetic quality of /path/to/photo.jpg?"

Claude: [Uses assess_aesthetic_quality tool]

Aesthetic Quality Assessment

Overall Score: 4/5

Detailed Scores:
- Composition: 4/5
- Framing: 4/5
- Lighting: 3/5
- Subject Interest: 5/5

Analysis: Strong composition following rule of thirds...
Cost: $0.0012 (1234 tokens)
```

**Example 3: Caption Generation**
```
User: "Generate a caption for this image: /path/to/sunset.jpg"

Claude: [Uses generate_caption tool]

Photo Captions

Concise (45 chars):
Golden sunset over coastal cliffs

Standard (180 chars):
As the sun dips below the Pacific horizon, warm golden light illuminates the rugged coastal cliffs. The dramatic interplay of light and shadow creates a stunning natural spectacle.

Detailed (420 chars):
This photograph captures the quintessential Pacific Northwest sunset along the Oregon coast. The golden hour light bathes the ancient basalt cliffs in warm tones, while the rhythmic waves below add motion to the composition. Shot at f/8 with ISO 200, the image preserves detail from the shadowed foreground through to the distant horizon. The composition follows the rule of thirds, placing the sun at the visual sweet spot for maximum impact.

Keywords: sunset, coast, cliffs, golden hour, ocean

Cost: $0.0018
```

**Example 4: Check Token Usage**
```
User: "How much have I spent on photo analysis today?"

Claude: [Uses get_token_usage tool]

Token Usage Statistics

Recent Analyses: 5
Total Cost: $0.0223
Average Cost per Image: $0.0045

Recent Entries:
1. vacation.jpg: $0.0045
2. sunset.jpg: $0.0038
3. mountain.jpg: $0.0051
...
```

### Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_photo` | Full analysis pipeline | `image_path`, optional flags |
| `assess_aesthetic_quality` | Aesthetic scoring only | `image_path` |
| `categorize_photo` | Categorization only | `image_path` |
| `generate_caption` | Caption generation | `image_path`, `caption_level` |
| `get_token_usage` | Usage statistics | `limit` |

### Programmatic MCP Client (Python)

You can also use MCP from your own Python applications:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to MCP server
server_params = StdioServerParameters(
    command="uv",
    args=["run", "python", "/path/to/mcp/photo_analysis_server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()

        # Call tool
        result = await session.call_tool(
            "analyze_photo",
            arguments={"image_path": "/path/to/photo.jpg"}
        )

        print(result.content[0].text)
```

---

## Deployment Options

### Docker Deployment (REST API)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000

CMD ["uvicorn", "api.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t photo-analysis-api .
docker run -p 8000:8000 photo-analysis-api
```

### Cloud Deployment

#### Google Cloud Run

```bash
gcloud run deploy photo-analysis \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### AWS Lambda (Serverless)

Use `mangum` adapter:
```python
from mangum import Mangum
from api.fastapi_server import app

handler = Mangum(app)
```

---

## Authentication

### REST API

Currently uses simple API key in header:
```
X-API-Key: your-secret-api-key-here
```

**Production recommendations**:
- Use OAuth 2.0 / JWT tokens
- Implement rate limiting
- Use HTTPS only
- Store API keys in environment variables

### MCP Server

MCP servers run locally and inherit user's permissions. No additional authentication needed for Claude Desktop integration.

---

## Monitoring & Logging

### REST API Logs

```bash
# Check logs
tail -f /var/log/photo-analysis-api.log

# Or with Docker
docker logs -f photo-analysis-api
```

### MCP Server Logs

MCP server logs to the main application logger. Check Claude Desktop logs:
- Mac: `~/Library/Logs/Claude/`
- Windows: `%APPDATA%\Claude\Logs\`

---

## Troubleshooting

### REST API

**Issue**: 401 Unauthorized
- **Fix**: Check API key in request header

**Issue**: 500 Internal Server Error
- **Fix**: Check logs, verify Vertex AI credentials configured

**Issue**: Slow response times
- **Fix**: Enable image resizing optimization in config.yaml

### MCP Server

**Issue**: Server not appearing in Claude Desktop
- **Fix**: Check JSON syntax in config file, restart Claude Desktop

**Issue**: Tool calls failing
- **Fix**: Verify absolute paths to images, check file permissions

**Issue**: "Command not found: uv"
- **Fix**: Use full path to uv or python in MCP config

---

## Next Steps

1. **Secure your API**: Implement proper authentication
2. **Add caching**: Cache results for duplicate images
3. **Set up monitoring**: Track usage, errors, performance
4. **Scale horizontally**: Deploy multiple instances behind load balancer
5. **Optimize costs**: Enable all optimization flags in config.yaml

For more options, see [API_INTEGRATION_OPTIONS.md](./API_INTEGRATION_OPTIONS.md)
