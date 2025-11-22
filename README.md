# Travel Photo Organization Workflow

> **AI-Powered Agentic System for Intelligent Travel Photo Management**

A sophisticated, production-ready system that uses 5 specialized AI agents to automatically organize, assess, categorize, and caption travel photographs with professional-grade metadata, quality scoring, and intelligent categorization. Includes a modern Flask web application with a Clean SaaS UI for easy interaction and visualization.

## 🎯 Overview

This workflow orchestrates a team of world-class AI agents, each expert in a specific domain:

1. **Metadata Extraction Agent** - Extracts comprehensive EXIF, GPS, camera data with reverse geocoding
2. **Quality Assessment Agent** - Evaluates technical quality (sharpness, exposure, noise)
3. **Aesthetic Assessment Agent** - Assesses aesthetic merit and artistic composition
4. **Filtering & Categorization Agent** - Categorizes by content, location, time and filters by quality thresholds with detailed reasoning
5. **Caption Generation Agent** - Generates multi-level captions (concise, standard, detailed) with keywords

## ✨ Features

### Core Workflow
- 📸 **Automated EXIF Extraction** - GPS coordinates with reverse geocoding to location names, camera settings, timestamps
- 🎨 **Dual Quality Assessment** - Technical metrics (OpenCV) + aesthetic evaluation (Gemini Vision)
- 🏷️ **Intelligent Categorization** - Scene recognition, time-of-day, location filtering with reasoning
- ✍️ **AI Caption Generation** - Three caption levels with keywords (powered by Gemini via Vertex AI)
- 📊 **Comprehensive Statistics** - Quality distributions, category breakdowns, performance metrics
- ⚡ **Parallel Processing** - Optimized workflow with ThreadPoolExecutor for concurrent execution
- 🔧 **Production-Ready** - Structured logging, error handling, 3-tier validation
- 🎯 **Smart Filtering** - Configurable quality/aesthetic thresholds with flagging system
- 📱 **Native HEIC Support** - Direct reading of HEIC/HEIF files from iPhone (no conversion needed)
- 💎 **Token Usage Tracking** - Monitor LLM API usage for cost optimization

### Web Application
- 🌐 **Flask Web App** - Modern, responsive web interface
- 🎨 **Clean SaaS UI** - Professional design with Inter font and modern aesthetics
- 📤 **Drag-and-Drop Upload** - Easy photo upload interface
- 📊 **Interactive Reports** - Tabbed interface showing:
  - **Metadata Tab** - Date, camera, location, dimensions
  - **Quality Tab** - Overall score, sharpness, noise, exposure with detailed breakdowns
  - **Aesthetic Tab** - Composition, lighting, framing, subject scores with AI analysis
  - **Filtering Tab** - Category, status, reasoning for pass/reject decisions
  - **Caption Tab** - Concise, standard captions with keywords
- 🔢 **Token Usage Display** - View LLM token consumption per image
- 📈 **Run History** - Track all workflow executions with status
- 🖼️ **Image Gallery** - Responsive masonry grid with metadata overlays

## 📋 Prerequisites

- **Python 3.9+**
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager (recommended)
- **Google Cloud Project** with Vertex AI API enabled
- **Application Default Credentials (ADC)** configured for Vertex AI

## 🚀 Quick Start

### 1. Installation

**Using uv (Recommended - Fast & Reliable):**

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all Python dependencies
uv sync

# Copy environment template
cp .env.example .env
```

**Alternative - Using pip:**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Configure Vertex AI

```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Or set credentials manually
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Update config.yaml with your project details
nano config.yaml
# Set: vertex_ai.project and vertex_ai.location
```

### 3. Start the Web Application

```bash
# Start Flask server
uv run python web_app/app.py

# Or activate virtual environment first
source .venv/bin/activate
python web_app/app.py

# Access at http://localhost:5001
```

### 4. Upload and Process Photos

1. Open browser to `http://localhost:5001`
2. Drag and drop your travel photos or click to upload
3. Click "Upload and Process"
4. Monitor progress in the dashboard
5. View detailed results in the interactive report

### Alternative: CLI Workflow

```bash
# Prepare images
mkdir -p sample_images
cp /path/to/your/photos/*.{jpg,png,heic} sample_images/

# Run workflow directly
uv run python orchestrator.py

# View results
cat output/reports/final_report.json | jq .
```

## 📁 Project Structure

```
Travel-website/
├── README.md                   # This file
├── CLAUDE.md                   # AI assistant guidance
├── config.yaml                 # Workflow configuration
├── orchestrator.py             # Main workflow orchestrator
├── agents/                     # 5 AI agent implementations
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
├── utils/                      # Logging, validation, helpers
│   ├── logger.py
│   ├── validation.py
│   └── helpers.py
├── web_app/                    # Flask web application
│   ├── app.py                 # Flask server
│   ├── templates/             # Jinja2 templates
│   │   ├── base.html         # Clean SaaS base template
│   │   ├── index.html        # Dashboard with upload
│   │   └── report.html       # Detailed results view
│   └── static/                # Static assets
├── sample_images/              # Input photos (add yours here)
├── uploads/                    # Web upload temporary storage
├── output/                     # Generated outputs (timestamped runs)
│   └── YYYYMMDD_HHMMSS/
│       ├── reports/           # JSON outputs from agents
│       ├── logs/              # Workflow logs
│       └── processed_images/  # Processed images
└── docs/                       # Comprehensive documentation
    ├── QUICKSTART.md
    ├── HLD.md
    ├── LLD.md
    ├── UML_DIAGRAMS.md
    └── ACTIVITY_DIAGRAM.md
```

## 📊 Workflow Stages

1. **Metadata Extraction** → Extract EXIF, GPS (with reverse geocoding), camera settings
2. **Quality + Aesthetic** → Parallel technical and artistic assessment
3. **Filtering + Captions** → Categorize with reasoning and generate descriptions

## ⚙️ Configuration

Edit `config.yaml` to customize thresholds, models, and settings:

```yaml
# Vertex AI Configuration
vertex_ai:
  project: "your-project-id"
  location: "us-central1"
  model: "gemini-1.5-flash"

# Quality Thresholds
thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

# Agent Configuration
agents:
  metadata_extraction:
    parallel_workers: 4
  quality_assessment:
    parallel_workers: 2
  aesthetic_assessment:
    parallel_workers: 2
    batch_size: 5
  filtering_categorization:
    parallel_workers: 2
  caption_generation:
    parallel_workers: 2
```

## 📈 Outputs

### Web Application
- **Dashboard**: View all workflow runs with status
- **Interactive Reports**: Detailed per-image analysis with tabs
- **Token Usage**: Monitor API consumption
- **Image Gallery**: Browse processed photos with metadata

### CLI/Direct Access
- **Agent Reports**: `output/{timestamp}/reports/*.json`
- **Final Statistics**: `output/{timestamp}/reports/final_report.json`
- **Logs**: `output/{timestamp}/logs/workflow.log`
- **Errors**: `output/{timestamp}/logs/errors.json`

## 🎨 Web UI Features

### Dashboard
- Drag-and-drop photo upload
- Run history with timestamps
- Status tracking (Running/Completed/Failed)
- Direct links to reports

### Report View
- **Stats Overview**: Total images, passed/rejected, average scores
- **Image Cards**: Responsive grid with thumbnails
- **Tabbed Details**: 
  - Metadata (date, camera, GPS location, dimensions)
  - Quality (overall + component scores, issues)
  - Aesthetic (composition, lighting, framing, AI analysis)
  - Filtering (category, pass/reject status, reasoning)
  - Caption (concise + standard versions, keywords)
- **Token Usage**: API consumption per agent

## 📝 Documentation

- **[QUICKSTART.md](./docs/QUICKSTART.md)** - 5-minute setup guide
- **[HLD.md](./docs/HLD.md)** - High-level system architecture
- **[LLD.md](./docs/LLD.md)** - Detailed agent specs and schemas
- **[UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md)** - Architecture diagrams
- **[ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md)** - Workflow visualization
- **[CLAUDE.md](./CLAUDE.md)** - AI assistant guidance

## 🚀 Quick Commands

**Web Application:**

```bash
# Start web server
uv run python web_app/app.py

# Access dashboard
open http://localhost:5001
```

**CLI Workflow:**

```bash
# Run workflow
uv run python orchestrator.py

# View report
cat output/{timestamp}/reports/final_report.json | jq .

# Check logs
tail -f output/{timestamp}/logs/workflow.log

# View specific agent output
cat output/{timestamp}/reports/metadata_extraction_output.json | jq .
```

**Using activated virtualenv:**

```bash
source .venv/bin/activate
python web_app/app.py
# or
python orchestrator.py
```

## 🔧 Technical Stack

### Backend
- **Python 3.9+** - Core language
- **Flask** - Web framework
- **Vertex AI** - Google's unified AI platform
- **google-genai** - Vertex AI Python SDK
- **OpenCV** - Image processing
- **Pillow** - Image I/O with HEIC support
- **geopy** - Reverse geocoding

### Frontend
- **HTML5 + CSS3** - Structure and styling
- **JavaScript (Vanilla)** - Interactivity
- **Jinja2** - Templating

### AI/ML
- **Gemini 1.5 Flash** - Vision and language model via Vertex AI
- **ThreadPoolExecutor** - Parallel processing

## 🌟 Key Features Deep Dive

### Reverse Geocoding
- Converts GPS coordinates to human-readable addresses
- Uses Nominatim geocoder
- Fallback to coordinates if geocoding fails

### Token Usage Tracking
- Captures prompt, response, and total tokens
- Displayed per image in UI
- Helps optimize API costs

### Smart Filtering with Reasoning
- Explains why images pass or fail quality thresholds
- Shows specific scores vs. thresholds
- Helps understand automated decisions

### Parallel Execution
- Metadata extraction: 4 workers
- Quality assessment: 2 workers (CPU-bound)
- Aesthetic/Caption/Filtering: 2 workers (API rate-limited)

## 📧 Support

For detailed guidance, check the documentation files in `docs/` directory or examine agent code directly.

---

**Ready to organize your travel photos? Start the web app with `uv run python web_app/app.py` and upload your images!** 📸