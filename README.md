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
- **pip** and **npm**
- Optional: API keys for Claude/GPT-4 (for production VLM/LLM features)

## 🚀 Quick Start

### 1. Installation

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

```bash
# Execute the complete workflow
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

```bash
# Run workflow
python orchestrator.py

# View report
cat output/reports/final_report.json | jq .

# Launch website
cd output/website && npm run dev

# Check logs
tail -f output/logs/workflow.log
```

## 📧 Support

Open an issue or check documentation files for details.

---

**Ready to organize your travel photos? Add images to `sample_images/` and run `python orchestrator.py`!** 📸