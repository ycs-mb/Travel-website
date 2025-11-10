# Travel Photo Organization Workflow

> **AI-Powered Agentic System for Intelligent Travel Photo Management**

A sophisticated, production-ready system that uses specialized AI agents to automatically organize, assess, categorize, and showcase travel photographs with professional-grade metadata, quality scoring, and a beautiful Material UI web interface.

## 🆕 CrewAI Implementation Available!

This project now includes a **CrewAI-based implementation** alongside the original custom agent system. CrewAI provides a modern, standardized framework for building collaborative AI agent systems.

**Choose your implementation:**
- **Original**: `orchestrator.py` - Custom agent orchestration
- **CrewAI**: `crewai_orchestrator.py` - Framework-powered workflow

📖 **See [CREWAI_CONVERSION.md](./CREWAI_CONVERSION.md) for detailed comparison and migration guide.**

## 🎯 Overview

This workflow orchestrates a team of world-class AI agents, each expert in a specific domain:

1. **Metadata Expert** - Extracts comprehensive EXIF, GPS, and camera data
2. **Image Quality Analyst** - Evaluates technical quality (sharpness, exposure, noise)
3. **Visual Curator** - Assesses aesthetic merit and artistic composition
4. **Visual Comparator** - Detects duplicates and similar images
5. **Semantic Classifier** - Categorizes by content, location, and time
6. **Caption Writer** - Generates multi-level captions (concise, standard, detailed)
7. **Material UI Web Expert** - Builds responsive React showcase website

## ✨ Features

- 📸 **Automated EXIF Extraction** - GPS, camera settings, timestamps
- 🎨 **Dual Quality Assessment** - Technical metrics + aesthetic evaluation
- 🔍 **Smart Duplicate Detection** - Perceptual hashing + visual similarity
- 🏷️ **Intelligent Categorization** - Scene recognition, time-of-day, location
- ✍️ **AI Caption Generation** - Three caption levels with keywords
- 🌐 **Beautiful Web Gallery** - Material UI React app with filters and search
- 📊 **Comprehensive Statistics** - Quality distributions, category breakdowns
- ⚡ **Parallel Processing** - Optimized workflow with concurrent execution
- 🔧 **Production-Ready** - Structured logging, error handling, validation

## 📋 Prerequisites

- **Python 3.10+** (updated for CrewAI compatibility)
- **Node.js 18+** (for website)
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager (recommended)
- **npm** (for website)
- Optional: API keys for OpenAI/Gemini (for LLM-powered agents)

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

**Option A: Original Custom System**

```bash
# Execute the custom workflow
uv run python orchestrator.py
```

**Option B: CrewAI System (NEW!)**

```bash
# Execute the CrewAI workflow
uv run python crewai_orchestrator.py
```

**Or activate virtual environment first:**

```bash
source .venv/bin/activate
python orchestrator.py          # Original
# OR
python crewai_orchestrator.py   # CrewAI
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
├── README.md                   # This file
├── CREWAI_CONVERSION.md        # CrewAI implementation guide
├── config.yaml                 # Workflow configuration
├── orchestrator.py             # Original workflow orchestrator
├── crewai_orchestrator.py      # CrewAI workflow orchestrator (NEW!)
├── agents/                     # Original AI agent implementations
├── travel_photo_tools/         # CrewAI tools (wraps agents)
├── crewai_config_agents.yaml   # CrewAI agent definitions
├── crewai_config_tasks.yaml    # CrewAI task definitions
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