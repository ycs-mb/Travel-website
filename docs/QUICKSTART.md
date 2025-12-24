# Quick Start Guide

Get up and running in 5 minutes!

---

## 🚀 Setup (5 minutes)

### 1. Install Dependencies

**Using uv (Recommended):**

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies
uv sync

# Copy environment template
cp .env.example .env
```

**Using pip:**

```bash
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure Vertex AI

```bash
# Install gcloud CLI if not already installed
# Visit: https://cloud.google.com/sdk/docs/install

# Set up Application Default Credentials
gcloud auth application-default login

# Or use service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### 3. Update Configuration

```bash
# Edit config.yaml
nano config.yaml

# Set your Vertex AI settings:
vertex_ai:
  project: "your-google-cloud-project-id"
  location: "us-central1"  # or your preferred region
  model: "gemini-1.5-flash"
```

---

## ▶️ Running the Application

### Option 1: Docker Deployment (Recommended for Production)

```bash
# Start all services with Docker Compose
docker compose up --build

# Or start just the API server
docker compose up api

# Access:
# - API Server: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

**Docker Features:**
- ✅ Production-ready containerized deployment
- 🔧 Auto-restart on failure
- 📊 Health checks built-in
- 🔒 Isolated environment
- 📦 Easy scaling with docker-compose

**See [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) for complete Docker guide**

### Option 2: FastAPI Server (API Access)

```bash
# Setup and start API server
./scripts/setup_api.sh
./scripts/start_api.sh

# Access:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

**API Features:**
- 🚀 RESTful endpoints for all agents
- 📚 Auto-generated documentation
- 🔑 API key authentication
- 🧪 Easy testing with Swagger UI
- 📊 JSON responses

**Generate API Key:**
```bash
./scripts/generate_api_key.sh
```

**See [API_README.md](./API_README.md) for complete API guide**

### Option 3: Web Application (Interactive UI)

```bash
# NOTE: Web app now requires FastAPI server running
# Start API server first
./scripts/start_api.sh

# Then start Flask web interface
uv run python web_app/app.py

# OR activate venv first
source .venv/bin/activate
python web_app/app.py

# Access at http://localhost:5001
```

**Web Features:**
- 📤 Drag-and-drop photo upload
- 📊 Interactive tabbed reports
- 📈 Run history and status tracking
- 🎨 Clean SaaS UI design
- 🔢 Token usage visualization
- 🔄 Calls FastAPI server for analysis

### Option 4: CLI Workflow

```bash
# Prepare images
mkdir -p sample_images
cp /path/to/your/photos/*.{jpg,png,heic} sample_images/

# Run workflow
uv run python orchestrator.py

# Expected output:
# → Loading configuration...
# → Initializing 5 agents...
# → Stage 1: Metadata Extraction...
# → Stage 2: Quality & Aesthetic (Parallel)...
# → Stage 3: Filtering & Captions...
# ✓ Workflow complete
```

### Option 5: Batch CSV Processing

```bash
# Process folder of images and export to CSV
cd batch-run-photo-json2csv
python main.py /path/to/images output.csv --api-key YOUR_API_KEY

# Recursive mode (searches subdirectories)
python main.py /path/to/images output.csv --recursive
```

**See [BATCH_PROCESSING.md](./BATCH_PROCESSING.md) for complete batch guide**

---

## 📊 View Results

### Web UI (Recommended)

```bash
# Navigate to http://localhost:5001
# Click on any completed run
# Explore tabbed interface:
#   - Metadata: Date, camera, GPS location
#   - Quality: Sharpness, noise, exposure
#   - Aesthetic: Composition, lighting, framing
#   - Filtering: Category, reasoning
#   - Caption: Multi-level captions
```

### CLI Results

```bash
# View summary statistics
cat output/{timestamp}/reports/final_report.json | jq .

# View metadata with locations
cat output/{timestamp}/reports/metadata_extraction_output.json | jq '.[] | {filename, gps}'

# View quality scores
cat output/{timestamp}/reports/quality_assessment_output.json | jq '.[] | {filename, quality_score, sharpness, noise, exposure}'

# View aesthetic scores
cat output/{timestamp}/reports/aesthetic_assessment_output.json | jq '.[] | {filename, overall_aesthetic, composition, lighting}'

# View filtering decisions
cat output/{timestamp}/reports/filtering_categorization_output.json | jq '.[] | {filename, category, passes_filter, reasoning}'

# View captions
cat output/{timestamp}/reports/caption_generation_output.json | jq '.[] | {filename, captions}'
```

### Token Usage Analysis

```bash
# Check token consumption
cat output/{timestamp}/reports/aesthetic_assessment_output.json | jq '.[] | {filename, token_usage}'
cat output/{timestamp}/reports/caption_generation_output.json | jq '.[] | {filename, token_usage}'
cat output/{timestamp}/reports/filtering_categorization_output.json | jq '.[] | {filename, token_usage}'
```

### View Logs

```bash
# Real-time monitoring
tail -f output/{timestamp}/logs/workflow.log

# Check for errors
cat output/{timestamp}/logs/errors.json | jq '.[] | {agent, error_type, summary}'

# Count errors by agent
jq 'group_by(.agent) | map({agent: .[0].agent, count: length})' output/{timestamp}/logs/errors.json
```

---

## 🌐 Web Application Guide

### Upload Photos

1. **Access Dashboard**: Open `http://localhost:5001`
2. **Upload Images**: 
   - Drag and drop photos onto upload zone
   - Or click "Browse Files" to select
3. **Submit**: Click "Upload and Process"
4. **Monitor**: Watch progress in dashboard

### View Reports

1. **Run List**: See all processing runs with timestamps
2. **Click Run**: Open detailed report
3. **Browse Images**: Scroll through processed photos
4. **View Details**: Click tabs for different agent outputs
5. **Check Tokens**: See API usage at bottom of each tab

---

## 🧪 Test Individual Agents

### Agent 1: Metadata Extraction

```bash
uv run python << 'EOF'
from agents.metadata_extraction import MetadataExtractionAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()
agent = MetadataExtractionAgent(config, logger)

# Process images
image_paths = [Path("sample_images/photo1.jpg")]
metadata_list, validation = agent.run(image_paths)

# View results
print(f"Status: {validation['status']}")
print(f"Image: {metadata_list[0]['filename']}")
print(f"GPS: {metadata_list[0]['gps']}")
if metadata_list[0]['gps'].get('location'):
    print(f"Location: {metadata_list[0]['gps']['location']}")
print(f"Camera: {metadata_list[0]['camera_settings']}")
EOF
```

### Agent 2: Quality Assessment

```bash
uv run python << 'EOF'
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

# First get metadata
metadata_agent = MetadataExtractionAgent(config, logger)
image_paths = [Path("sample_images/photo1.jpg")]
metadata_list, _ = metadata_agent.run(image_paths)

# Then assess quality
quality_agent = QualityAssessmentAgent(config, logger)
quality_list, validation = quality_agent.run(image_paths, metadata_list)

# View results
print(f"Status: {validation['status']}")
for q in quality_list:
    print(f"Image: {q['image_id']}")
    print(f"  Quality Score: {q['quality_score']}/5")
    print(f"  Sharpness: {q['sharpness']}, Exposure: {q['exposure']}, Noise: {q['noise']}")
    print(f"  Issues: {q['issues']}")
EOF
```

### Agent 3: Aesthetic Assessment

```bash
uv run python << 'EOF'
from agents.metadata_extraction import MetadataExtractionAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

metadata_agent = MetadataExtractionAgent(config, logger)
image_paths = [Path("sample_images/photo1.jpg")]
metadata_list, _ = metadata_agent.run(image_paths)

aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, validation = aesthetic_agent.run(image_paths, metadata_list)

print(f"Status: {validation['status']}")
for a in aesthetic_list:
    print(f"Image: {a['image_id']}")
    print(f"  Overall: {a['overall_aesthetic']}/5")
    print(f"  Composition: {a['composition']}, Lighting: {a['lighting']}, Framing: {a['framing']}")
    print(f"  Notes: {a['notes']}")
    if 'token_usage' in a:
        print(f"  Tokens: {a['token_usage']['total_token_count']}")
EOF
```

### Agent 4: Filtering & Categorization

```bash
uv run python << 'EOF'
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.filtering_categorization import FilteringCategorizationAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

image_paths = [Path("sample_images/photo1.jpg")]

# Run prerequisites
metadata_agent = MetadataExtractionAgent(config, logger)
metadata_list, _ = metadata_agent.run(image_paths)

quality_agent = QualityAssessmentAgent(config, logger)
quality_list, _ = quality_agent.run(image_paths, metadata_list)

aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, _ = aesthetic_agent.run(image_paths, metadata_list)

# Run filtering
filtering_agent = FilteringCategorizationAgent(config, logger)
categories, validation = filtering_agent.run(image_paths, metadata_list, quality_list, aesthetic_list)

print(f"Status: {validation['status']}")
for c in categories:
    print(f"Image: {c['image_id']}")
    print(f"  Category: {c['category']}")
    print(f"  Passes Filter: {c['passes_filter']}")
    print(f"  Reasoning: {c['reasoning']}")
    if 'token_usage' in c:
        print(f"  Tokens: {c['token_usage']['total_token_count']}")
EOF
```

### Agent 5: Caption Generation

```bash
uv run python << 'EOF'
from agents.caption_generation import CaptionGenerationAgent
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.filtering_categorization import FilteringCategorizationAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

image_paths = [Path("sample_images/photo1.jpg")]

# Run all prerequisites
metadata_agent = MetadataExtractionAgent(config, logger)
metadata_list, _ = metadata_agent.run(image_paths)

quality_agent = QualityAssessmentAgent(config, logger)
quality_list, _ = quality_agent.run(image_paths, metadata_list)

aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, _ = aesthetic_agent.run(image_paths, metadata_list)

filtering_agent = FilteringCategorizationAgent(config, logger)
categories, _ = filtering_agent.run(image_paths, metadata_list, quality_list, aesthetic_list)

# Generate captions
caption_agent = CaptionGenerationAgent(config, logger)
captions, validation = caption_agent.run(image_paths, metadata_list, quality_list, aesthetic_list, categories)

print(f"Status: {validation['status']}")
for cap in captions:
    print(f"Image: {cap['image_id']}")
    print(f"  Concise: {cap['captions']['concise']}")
    print(f"  Standard: {cap['captions']['standard']}")
    print(f"  Keywords: {', '.join(cap['keywords'])}") 
    if 'token_usage' in cap:
        print(f"  Tokens: {cap['token_usage']['total_token_count']}")
EOF
```

---

## 📁 Common Paths

```
Travel-website/
├── config.yaml                 # Configuration file
├── .env                        # Environment variables (don't commit!)
├── keys.json                   # GCP service account key (don't commit!)
├── docker-compose.yml          # Docker deployment config
│
├── web_app/
│   └── app.py                 # Flask web server (calls API)
├── orchestrator.py             # CLI workflow entry point
│
├── api/
│   └── fastapi_server.py      # FastAPI REST server
│
├── mcp/
│   └── photo_analysis_server.py # MCP server (Claude Desktop)
│
├── docker/
│   ├── api.Dockerfile         # API container image
│   └── mcp.Dockerfile         # MCP container image
│
├── scripts/
│   ├── start_api.sh           # Start FastAPI server
│   ├── setup_api.sh           # Setup API environment
│   ├── setup_mcp.sh           # Setup MCP server
│   ├── generate_api_key.sh    # Generate secure API key
│   ├── test_api_server.sh     # Test API endpoints
│   └── test_mcp.sh            # Test MCP server
│
├── batch-run-photo-json2csv/  # Batch CSV processing tool
│   ├── main.py               # Batch processor
│   └── README.md             # Batch tool docs
│
├── sample_images/              # Add your photos here (CLI mode)
│   ├── photo1.jpg
│   └── ...
│
├── uploads/                    # Web upload temporary storage
├── cache/                      # Geocoding & results cache
│
├── agents/                     # Agent implementations
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
│
├── utils/                      # Shared utilities
│   ├── logger.py              # Logging
│   ├── validation.py          # Schemas
│   ├── helpers.py             # File I/O
│   └── reverse_geocoding.py   # GPS → Location names
│
├── tests/                      # Test suites
│   ├── test_api.py            # API tests
│   ├── test_mcp.py            # MCP tests
│   └── test_full_pipeline.py  # End-to-end tests
│
├── docs/                       # Documentation
│   ├── QUICKSTART.md          # This file
│   ├── HLD.md                 # High-level design
│   ├── LLD.md                 # Low-level design
│   ├── API_README.md          # API documentation
│   ├── MCP_SETUP.md           # MCP setup guide
│   ├── DOCKER_DEPLOYMENT.md   # Docker guide
│   └── ...
│
└── output/                     # Generated outputs (timestamped)
    └── YYYYMMDD_HHMMSS/
        ├── reports/           # Agent outputs + final report
        ├── logs/              # Workflow logs
        └── processed_images/  # Processed images
```

---

## ⚙️ Configuration Quick Reference

### Key Settings in config.yaml

```yaml
# Vertex AI Configuration
vertex_ai:
  project: "your-project-id"      # Your GCP project ID
  location: "us-central1"         # GCP region
  model: "gemini-1.5-flash"       # Model to use

# Reverse Geocoding (GPS → Location Names)
reverse_geocoding:
  enabled: true                   # Enable location name lookup
  cache_enabled: true             # Cache results to reduce API calls
  cache_ttl_hours: 24            # Cache validity (hours)
  timeout_seconds: 5             # Request timeout
  user_agent: "TravelPhotoAnalysis/1.0"

# Thresholds
thresholds:
  min_technical_quality: 3      # Minimum quality score (1-5)
  min_aesthetic_quality: 3      # Minimum aesthetic score (1-5)

# Parallelization
agents:
  metadata_extraction:
    parallel_workers: 4          # I/O bound
  quality_assessment:
    parallel_workers: 2          # CPU bound
  aesthetic_assessment:
    parallel_workers: 2          # API rate limited
    batch_size: 5
  filtering_categorization:
    parallel_workers: 2
  caption_generation:
    parallel_workers: 2

# Error handling
error_handling:
  max_retries: 3
  continue_on_error: true        # Don't stop on single image failure

# API Configuration
api:
  host: "0.0.0.0"
  port: 8000
  reload: true                   # Auto-reload on code changes (dev only)
```

---

## 🔧 Troubleshooting

### Issue: "Vertex AI credentials not found"

```bash
# Set up ADC
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Verify
python -c "import google.auth; print(google.auth.default())"
```

### Issue: "Vertex AI API not enabled"

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Or visit: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
```

### Issue: "Port 5001 already in use"

```bash
# Check what's using the port
lsof -i:5001

# Kill the process or change port in app.py:
# app.run(debug=True, port=5002)
```

### Issue: "No images found" (CLI mode)

```bash
# Check that images exist
ls sample_images/

# Check file permissions
chmod 644 sample_images/*.jpg

# Verify config paths
cat config.yaml | grep input_images
```

### Issue: Out of Memory

```bash
# Reduce parallel workers
nano config.yaml

# Change:
# parallel_workers: 2  →  parallel_workers: 1
```

### Issue: Slow Performance

```bash
# Monitor progress
tail -f output/{timestamp}/logs/workflow.log

# Check Flask logs
# (displayed in terminal where app.py is running)

# Reduce batch size for API agents
nano config.yaml
# batch_size: 5  →  batch_size: 2
```

---

## 📚 Documentation Structure

- **[HLD.md](./HLD.md)** - High-level system architecture and overview
- **[LLD.md](./LLD.md)** - Detailed agent specs, schemas, implementation patterns
- **[UML_DIAGRAMS.md](./UML_DIAGRAMS.md)** - Class, sequence, component diagrams
- **[ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)** - Workflow and execution flows
- **[README.md](../README.md)** - Project overview and features
- **[CLAUDE.md](../CLAUDE.md)** - AI assistant guidance

---

## 🎯 Next Steps

**For Quick Testing:**
1. **Start API server** → `./scripts/start_api.sh`
2. **Test API** → Visit `http://localhost:8000/docs`
3. **Try endpoints** → Use Swagger UI to upload images

**For Production Deployment:**
1. **Setup Docker** → `docker compose up --build`
2. **Verify health** → `curl http://localhost:8000/health`
3. **View logs** → `docker compose logs -f api`

**For Interactive Use:**
1. **Start API server** → `./scripts/start_api.sh`
2. **Start web app** → `uv run python web_app/app.py`
3. **Upload photos** → Drag and drop on `http://localhost:5001`
4. **Process images** → Click "Upload and Process"
5. **View results** → Click on completed run
6. **Explore tabs** → See metadata, quality, aesthetic, filtering, captions
7. **Check tokens** → Monitor API usage at bottom of tabs

**For Batch Processing:**
1. **Setup batch tool** → `cd batch-run-photo-json2csv`
2. **Process folder** → `python main.py /path/to/images output.csv`
3. **Open CSV** → View results in Excel/Google Sheets

**For Claude Desktop Integration:**
1. **Setup MCP** → `./scripts/setup_mcp.sh`
2. **Configure Claude** → `./scripts/setup_claude_mcp.sh`
3. **Restart Claude** → Restart Claude Desktop app
4. **Use in Claude** → "Analyze this photo: /path/to/image.jpg"

**Read detailed docs** → See Documentation Structure below

---

## 💡 Tips

- **Docker is recommended for production** - Easy deployment, health checks, auto-restart
- **API server for integration** - RESTful endpoints for apps and services
- **Web UI for interactive use** - Best for exploring results visually
- **Batch CSV for large datasets** - Process hundreds of images to spreadsheet
- **First run takes longer** due to dependency loading and model initialization
- **Subsequent runs faster** with warm caches
- **Monitor token usage** to optimize API costs
- **Adjust thresholds** for your use case in `config.yaml`
- **Use reverse geocoding** to get location names from GPS coordinates (free!)
- **Check filtering reasoning** to understand automated decisions
- **Generate secure API keys** with `./scripts/generate_api_key.sh`
- **Test before deploying** with `./scripts/test_api_server.sh`

---

**Questions?** Check the detailed documentation files or examine agent code directly.
