# Travel Photo Organization System

> **Production-Ready AI-Powered Photo Analysis with Multiple Deployment Options**

A complete system using 5 specialized AI agents to automatically organize, assess, categorize, and caption travel photographs. Features Docker deployment, FastAPI REST API, Flask web UI, batch CSV processing, MCP server for Claude Desktop, and comprehensive documentation.

**🐳 Production Ready:** Docker Compose deployment with health checks and auto-restart
**📊 Batch Processing:** Process folders of images and export to CSV
**🌐 Multiple Interfaces:** REST API, Web UI, CLI, Claude Desktop integration
**💰 Cost Optimized:** Token tracking and optimization strategies

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | `>=3.10` | Runtime |
| **[uv](https://github.com/astral-sh/uv)** | Latest | Fast package manager (recommended) |
| **Google Cloud SDK** | Latest | Vertex AI authentication |

**Google Cloud:**
- A GCP Project with the **Vertex AI API** enabled.
- Application Default Credentials (ADC) configured.

---

## 🚀 Quick Start

### Option 1: Docker (Production) - Recommended

```bash
# Start all services
docker compose up --build

# Access API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**See [docs/DOCKER_DEPLOYMENT.md](./docs/DOCKER_DEPLOYMENT.md) for complete guide**

### Option 2: Local Development

```bash
# 1. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 2. Configure Vertex AI
gcloud auth application-default login
nano config.yaml  # Set your GCP project ID

# 3. Start FastAPI server
./scripts/start_api.sh

# 4. Start Flask web UI (optional)
uv run python web_app/app.py
# Open http://localhost:5001
```

### Option 3: Batch CSV Processing

```bash
# Process folder of images to CSV
cd batch-run-photo-json2csv
python main.py /path/to/photos results.csv --api-key YOUR_KEY

# Open in Excel/Google Sheets
open results.csv
```

**See [docs/BATCH_PROCESSING.md](./docs/BATCH_PROCESSING.md) for complete guide**

### Option 4: Claude Desktop Integration

```bash
# Setup MCP server
./scripts/setup_mcp.sh
./scripts/setup_claude_mcp.sh

# Restart Claude Desktop
# Use: "Analyze this photo: /path/to/image.jpg"
```

**See [docs/MCP_SETUP.md](./docs/MCP_SETUP.md) for complete guide**

### Option 5: CLI Workflow

```bash
# Direct orchestrator execution
mkdir -p sample_images
cp /path/to/photos/*.jpg sample_images/
uv run python orchestrator.py

# Results in output/{timestamp}/reports/
```

**See [docs/QUICKSTART.md](./docs/QUICKSTART.md) for 5-minute setup guide**

---

## 📁 Project Structure

```
Travel-website/
├── docker-compose.yml           # Docker deployment config
├── orchestrator.py              # Main workflow engine
├── config.yaml                  # Central configuration
├── keys.json                    # GCP credentials (don't commit!)
│
├── agents/                      # 5 AI Agents
│   ├── metadata_extraction.py  # Agent 1: EXIF + GPS + Reverse Geocoding
│   ├── quality_assessment.py   # Agent 2: Technical quality (OpenCV)
│   ├── aesthetic_assessment.py # Agent 3: Aesthetic scoring (Vertex AI)
│   ├── filtering_categorization.py # Agent 4: Categorization (Vertex AI)
│   └── caption_generation.py   # Agent 5: Caption generation (Vertex AI)
│
├── api/
│   └── fastapi_server.py        # FastAPI REST server (port 8000)
│
├── mcp/
│   └── photo_analysis_server.py # MCP server for Claude Desktop
│
├── web_app/                     # Flask web UI (port 5001)
│   ├── app.py                   # Calls FastAPI for processing
│   ├── templates/               # Jinja2 templates
│   └── static/                  # CSS, JS
│
├── batch-run-photo-json2csv/    # Batch CSV processing tool
│   ├── main.py                  # Batch processor
│   ├── README.md                # Usage guide
│   └── requirements.txt
│
├── docker/
│   ├── api.Dockerfile           # API container image
│   └── mcp.Dockerfile           # MCP container image
│
├── scripts/                     # Automation scripts
│   ├── start_api.sh             # Start FastAPI server
│   ├── setup_api.sh             # Setup API environment
│   ├── setup_mcp.sh             # Setup MCP server
│   ├── setup_claude_mcp.sh      # Configure Claude Desktop
│   ├── generate_api_key.sh      # Generate secure API key
│   ├── test_api_server.sh       # Test API endpoints
│   └── test_mcp.sh              # Test MCP server
│
├── utils/                       # Shared utilities
│   ├── logger.py                # Structured logging
│   ├── validation.py            # Schema validation
│   ├── helpers.py               # File I/O utilities
│   ├── heic_reader.py           # HEIC format support
│   ├── reverse_geocoding.py     # GPS → Location names
│   └── token_tracker.py         # Token usage tracking
│
├── docs/                        # Comprehensive documentation
│   ├── QUICKSTART.md            # ⭐ 5-minute setup guide
│   ├── DOCKER_DEPLOYMENT.md     # Docker & production
│   ├── BATCH_PROCESSING.md      # Batch CSV guide
│   ├── API_README.md            # API documentation
│   ├── MCP_SETUP.md             # Claude Desktop setup
│   ├── HLD.md                   # High-level design
│   ├── LLD.md                   # Low-level design
│   └── ...                      # More docs
│
├── tests/                       # Test suites
│   ├── test_api.py              # API endpoint tests
│   ├── test_mcp.py              # MCP server tests
│   └── test_full_pipeline.py    # End-to-end tests
│
├── sample_images/               # Input photos (CLI mode)
├── uploads/                     # Web upload storage
├── cache/                       # Geocoding cache
└── output/                      # Generated reports (timestamped)
    └── YYYYMMDD_HHMMSS/
        ├── reports/             # Agent outputs + final report
        ├── logs/                # Workflow logs
        └── processed_images/    # Processed images
```

---

## ✨ Core Features

### AI Agents (5-Agent Pipeline)
- 📸 **Agent 1:** EXIF & GPS Extraction with reverse geocoding (OpenStreetMap)
- 🔍 **Agent 2:** Technical Quality Assessment (OpenCV - sharpness, exposure, noise)
- 🎨 **Agent 3:** Aesthetic Assessment (Vertex AI - composition, lighting, framing)
- 🏷️ **Agent 4:** Intelligent Categorization with AI reasoning (Vertex AI)
- ✍️ **Agent 5:** Multi-Level Caption Generation (Vertex AI - concise, standard, detailed)

### Deployment Options
- 🐳 **Docker:** Production-ready containerized deployment with health checks
- 🚀 **FastAPI:** RESTful API server with Swagger documentation
- 🌐 **Flask Web UI:** Interactive upload and visualization interface
- 📊 **Batch CSV:** Process folders and export to spreadsheets
- 🤖 **MCP Server:** Native Claude Desktop integration

### Technical Features
- ⚡ **Parallel Processing:** ThreadPoolExecutor for concurrent agent execution
- 💰 **Token Tracking:** Real-time cost monitoring and optimization
- 🌍 **Reverse Geocoding:** GPS coordinates → location names (free!)
- 📱 **HEIC Support:** Native support for iPhone photos
- 🔄 **Caching:** Result and geocoding caching to reduce costs
- 📝 **Structured Logging:** JSON-formatted logs with error tracking
- ✅ **Validation:** 3-tier validation system for data integrity

---

## 📚 Documentation

### Getting Started
| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](./docs/QUICKSTART.md)** | ⭐ 5-minute setup guide - start here! |
| **[DOCKER_DEPLOYMENT.md](./docs/DOCKER_DEPLOYMENT.md)** | Docker & production deployment guide |
| **[BATCH_PROCESSING.md](./docs/BATCH_PROCESSING.md)** | Batch CSV processing for large datasets |
| **[API_README.md](./docs/API_README.md)** | Complete API documentation & examples |
| **[MCP_SETUP.md](./docs/MCP_SETUP.md)** | Claude Desktop integration guide |

### Architecture & Design
| Document | Description |
|----------|-------------|
| **[HLD.md](./docs/HLD.md)** | High-level system design & deployment options |
| **[LLD.md](./docs/LLD.md)** | Low-level design, agent specs & schemas |
| **[UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md)** | Architecture diagrams (class, sequence, component) |
| **[ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md)** | Workflow visualization & state machines |

### Additional Resources
| Document | Description |
|----------|-------------|
| **[TOKEN_OPTIMIZATION.md](./docs/TOKEN_OPTIMIZATION.md)** | Cost reduction strategies (50-60% savings) |
| **[SETUP_GUIDE.md](./docs/SETUP_GUIDE.md)** | Detailed setup & testing guide |
| **[CLAUDE.md](./CLAUDE.md)** | AI assistant guidance for development |

---

## License

MIT