# Travel Photo Organization Workflow

> **AI-Powered Agentic System for Intelligent Travel Photo Management**

A production-ready system using 5 specialized AI agents to automatically organize, assess, categorize, and caption travel photographs. Features a modern Flask web UI, a FastAPI backend, an MCP server for Claude Desktop integration, and a standalone HD viewer.

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

## Build / Run

### 1. Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env
```

### 2. Configure Vertex AI

```bash
gcloud auth application-default login

# Edit config.yaml and set your project ID
# api.google.project: "your-gcp-project-id"
```

### 3. Run the Applications

**Flask Web App (Primary UI):**
```bash
uv run python web_app/app.py
# Open http://localhost:5001
```

**FastAPI Server (API Backend):**
```bash
uv run uvicorn api.fastapi_server:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

**MCP Server (for Claude Desktop):**
```bash
# Add to Claude Desktop config, then restart:
# ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "photo-analysis": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp/photo_analysis_server.py"]
    }
  }
}
```

**HD Viewer (Standalone):**
```bash
python -m http.server 8000
# Open http://localhost:8000/hd_viewer/
# Drag and drop a report JSON to view.
```

**CLI Workflow:**
```bash
uv run python orchestrator.py
```

---

## Project Tree

```
Travel-website/
├── orchestrator.py              # Main workflow engine
├── config.yaml                  # Central configuration
│
├── agents/                      # 5 AI Agents
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
│
├── api/
│   └── fastapi_server.py        # FastAPI backend
│
├── mcp/
│   └── photo_analysis_server.py # MCP server for Claude
│
├── web_app/                     # Flask UI
│   ├── app.py
│   ├── templates/
│   └── static/
│
├── hd_viewer/                   # Standalone HD Viewer (NEW)
│   ├── index.html
│   ├── styles.css
│   └── script.js
│
├── utils/                       # Shared utilities
│   ├── logger.py
│   ├── validation.py
│   ├── helpers.py
│   ├── heic_reader.py
│   ├── reverse_geocoding.py
│   └── token_tracker.py
│
├── docs/                        # Documentation
├── tests/                       # Pytest suite
├── sample_images/               # Input photos
├── uploads/                     # Web upload storage
└── output/                      # Generated reports (timestamped)
```

---

## Core Features

- 📸 **EXIF & GPS Extraction** with reverse geocoding
- 🎨 **Dual Quality Assessment** (Technical + Aesthetic)
- 🏷️ **Intelligent Categorization** with AI reasoning
- ✍️ **Multi-Level Captions** (Concise, Standard, Detailed)
- 📱 **Native HEIC Support**
- ⚡ **Parallel Processing** via `ThreadPoolExecutor`
- 💰 **Token Usage Tracking** for cost optimization
- 🌐 **Multiple Interfaces**: Flask UI, FastAPI, MCP, HD Viewer

---

## Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](./docs/QUICKSTART.md) | 5-minute setup guide |
| [HLD.md](./docs/HLD.md) | High-Level Design |
| [LLD.md](./docs/LLD.md) | Low-Level Design & Schemas |
| [UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md) | Architecture diagrams |
| [ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md) | Workflow visualization |
| [CLAUDE.md](./CLAUDE.md) | AI assistant context |

---

## License

MIT