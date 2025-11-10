# Travel Photo Organization Workflow

> **AI-Powered Agentic System for Intelligent Travel Photo Management**

A sophisticated, production-ready system that uses 5 specialized AI agents to automatically organize, assess, categorize, and caption travel photographs with professional-grade metadata, quality scoring, and intelligent categorization.

## 🎯 Overview

This workflow orchestrates a team of world-class AI agents, each expert in a specific domain:

1. **Metadata Extraction Agent** - Extracts comprehensive EXIF, GPS, and camera data
2. **Quality Assessment Agent** - Evaluates technical quality (sharpness, exposure, noise)
3. **Aesthetic Assessment Agent** - Assesses aesthetic merit and artistic composition
4. **Filtering & Categorization Agent** - Categorizes by content, location, time and filters by quality thresholds
5. **Caption Generation Agent** - Generates multi-level captions (concise, standard, detailed) with keywords

## ✨ Features

- 📸 **Automated EXIF Extraction** - GPS, camera settings, timestamps
- 🎨 **Dual Quality Assessment** - Technical metrics (OpenCV) + aesthetic evaluation (Gemini Vision)
- 🏷️ **Intelligent Categorization** - Scene recognition, time-of-day, location filtering
- ✍️ **AI Caption Generation** - Three caption levels with keywords (powered by Gemini)
- 📊 **Comprehensive Statistics** - Quality distributions, category breakdowns, performance metrics
- ⚡ **Parallel Processing** - Optimized workflow with 2 parallel stages
- 🔧 **Production-Ready** - Structured logging, error handling, 3-tier validation
- 🎯 **Smart Filtering** - Configurable quality/aesthetic thresholds with flagging system

## 📋 Prerequisites

- **Python 3.9+**
- **Node.js 18+** (for website)
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager (recommended)
- **npm** (for website)
- Optional: API keys for Claude/GPT-4 (for production VLM/LLM features)

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

### 2. Prepare Your Images

```bash
# Create sample images directory
mkdir -p sample_images

# Copy your travel photos
cp /path/to/your/photos/*.jpg sample_images/
```

### 3. Run the Workflow

**Using uv:**

```bash
# Execute the complete workflow
uv run python orchestrator.py
```

**Or activate virtual environment first:**

```bash
source .venv/bin/activate
python orchestrator.py
```

### 4. View Results

```bash
# Check final report
cat output/reports/final_report.json

# Run website
cd output/website && npm install && npm run dev
```

## 📁 Project Structure

```
Travel-website/
├── WORKFLOW_DESIGN.md          # Complete architecture documentation
├── config.yaml                 # Workflow configuration
├── orchestrator.py             # Main workflow orchestrator
├── agents/                     # 7 AI agent implementations
├── utils/                      # Logging, validation, helpers
├── sample_images/              # Input photos (add yours here)
└── output/                     # Generated outputs
```

## 📊 Workflow Stages

1. **Metadata Extraction** → Extract EXIF, GPS, camera settings
2. **Quality + Aesthetic** → Parallel technical and artistic assessment
3. **Duplicate Detection** → Find and group similar images
4. **Filtering + Captions** → Categorize and generate descriptions
5. **Website Generation** → Build Material UI React showcase

## ⚙️ Configuration

Edit `config.yaml` to customize thresholds, models, and settings:

```yaml
thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

agents:
  aesthetic_assessment:
    model: "claude-3.5-sonnet"
```

## 📈 Outputs

- **Agent Reports**: `output/reports/*.json`
- **Final Statistics**: `output/reports/final_report.json`
- **Website**: `output/website/`
- **Logs**: `output/logs/workflow.log`

## 🎨 Generated Website Features

- Responsive masonry grid
- Category/quality filters
- Search by caption/keyword
- Lightbox with metadata
- Statistics dashboard
- Dark/light theme
- Mobile optimized

## 📝 Documentation

- `WORKFLOW_DESIGN.md` - Complete workflow architecture and agent specifications
- Agent docstrings - Detailed implementation notes

## 🚀 Quick Commands

**Using uv:**

```bash
# Run workflow
uv run python orchestrator.py

# View report
cat output/reports/final_report.json | jq .

# Launch website
cd output/website && npm run dev

# Check logs
tail -f output/logs/workflow.log

# Add new dependency
uv add package-name

# Update dependencies
uv sync --upgrade
```

**Or with activated virtual environment:**

```bash
source .venv/bin/activate
python orchestrator.py
```

## 📧 Support

Open an issue or check documentation files for details.

---

**Ready to organize your travel photos? Add images to `sample_images/` and run `python orchestrator.py`!** 📸