# Travel Photo Organization Workflow

> **AI-Powered Agentic System for Intelligent Travel Photo Management**

A sophisticated, production-ready system that uses 7 specialized AI agents to automatically organize, assess, categorize, and showcase travel photographs with professional-grade metadata, quality scoring, and a beautiful Material UI web interface.

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

**Option A: No-Framework Implementation**

```bash
# Execute the original implementation
uv run python no-framework/orchestrator.py

# Or with activated venv
source .venv/bin/activate
python no-framework/orchestrator.py
```

**Option B: LangChain Ecosystem Implementation**

```bash
# LangChain implementation
python langchain-ecosystem/langchain_implementation.py

# LangGraph implementation (faster with parallel execution)
python langchain-ecosystem/langgraph_implementation.py

# LangSmith integration (with observability)
python langchain-ecosystem/langsmith_integration.py
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
├── config.yaml                 # Workflow configuration
├── .env.example                # Environment variables template
├── sample_images/              # Input photos (add yours here)
├── output/                     # Generated outputs
│
├── no-framework/               # 🔧 Original Implementation (No Framework)
│   ├── orchestrator.py         # Main workflow orchestrator
│   ├── agents/                 # 5 AI agent implementations
│   ├── utils/                  # Logging, validation, helpers
│   └── README.md               # No-framework documentation
│
├── langchain-ecosystem/        # 🚀 LangChain Ecosystem Implementation
│   ├── langchain_implementation.py   # LangChain chains & prompts
│   ├── langgraph_implementation.py   # StateGraph workflow
│   ├── langsmith_integration.py      # Observability & tracing
│   ├── LANGCHAIN_CONVERSION.md       # Detailed conversion guide
│   ├── LANGCHAIN_QUICKSTART.md       # Quick start guide
│   └── README.md                     # LangChain ecosystem docs
│
└── docs/                       # 📚 Documentation
    ├── HLD.md                  # High-level design
    ├── LLD.md                  # Low-level design
    ├── QUICKSTART.md           # Quick start guide
    └── ...
```

## 🎭 Two Implementations

This project provides **two complete implementations** of the same workflow:

### 1. **No-Framework** (`no-framework/`)
- ✅ **Custom multi-agent system** built from scratch
- ✅ **Full control** over every aspect
- ✅ **Easy to understand** - see how it works under the hood
- ✅ **Minimal dependencies** - no framework lock-in
- 📖 [Read the no-framework docs](./no-framework/README.md)

### 2. **LangChain Ecosystem** (`langchain-ecosystem/`)
- ✅ **LangChain** for chains, prompts, and models
- ✅ **LangGraph** for stateful workflow orchestration
- ✅ **LangSmith** for observability and monitoring
- ✅ **33% less code**, 29% faster execution
- ✅ **Production-ready** with built-in best practices
- 📖 [Read the LangChain ecosystem docs](./langchain-ecosystem/README.md)

**Choose based on your needs:**
- **Learning/Research**: Start with no-framework
- **Production/Scale**: Use LangChain ecosystem

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

**No-Framework Implementation:**

```bash
# Run workflow
uv run python no-framework/orchestrator.py

# View report
cat output/<timestamp>/reports/final_report.json | jq .

# Check logs
tail -f output/<timestamp>/logs/workflow.log
```

**LangChain Ecosystem:**

```bash
# LangChain implementation
python langchain-ecosystem/langchain_implementation.py

# LangGraph (with parallel execution)
python langchain-ecosystem/langgraph_implementation.py

# LangSmith (with tracing - requires LANGCHAIN_API_KEY)
python langchain-ecosystem/langsmith_integration.py

# View traces at https://smith.langchain.com
```

**Development:**

```bash
# Add new dependency
uv add package-name

# Update dependencies
uv sync --upgrade

# Activate virtual environment
source .venv/bin/activate
```

## 📧 Support

Open an issue or check documentation files for details.

---

**Ready to organize your travel photos? Add images to `sample_images/` and run `python orchestrator.py`!** 📸