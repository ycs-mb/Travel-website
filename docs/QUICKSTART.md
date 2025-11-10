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

### 2. Prepare Your Images

```bash
# Create images directory if needed
mkdir -p sample_images

# Copy your photos (JPG, PNG, HEIC, RAW formats supported)
cp /path/to/your/photos/*.jpg sample_images/
```

### 3. Configure (Optional)

```bash
# Edit config.yaml to adjust:
# - Quality thresholds
# - API models
# - Parallel workers

nano config.yaml
```

### 4. Add API Keys (Optional)

```bash
# Edit .env for actual VLM/LLM features
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=AIza...

nano .env
```

---

## ▶️ Running the Workflow

### Complete Workflow

```bash
# Run with uv (recommended)
uv run python orchestrator.py

# OR activate venv first
source .venv/bin/activate
python orchestrator.py
```

**Expected output:**
```
→ Loading configuration...
→ Initializing 7 agents...
→ Stage 1/5: Metadata Extraction...
→ Stage 2/5: Quality & Aesthetic Assessment...
→ Stage 3/5: Duplicate Detection...
→ Stage 4/5: Filtering & Caption Generation...
→ Stage 5/5: Website Generation...
→ Generating reports...
✓ Workflow complete in 14.5 minutes
```

---

## 📊 View Results

### Check Final Report

```bash
# View summary statistics
cat output/reports/final_report.json | jq .

# Pretty print
cat output/reports/final_report.json | jq '.'
```

### View Logs

```bash
# Real-time monitoring
tail -f output/logs/workflow.log

# Check for errors
cat output/logs/errors.json | jq '.[] | {agent, error_type, summary}'

# Count errors by agent
jq 'group_by(.agent) | map({agent: .[0].agent, count: length})' output/logs/errors.json
```

### Check Agent Outputs

```bash
# List all agent reports
ls output/reports/

# View metadata extraction results
cat output/reports/metadata_extraction_output.json | jq '.[] | {image_id, filename, gps}'

# View quality scores
cat output/reports/quality_assessment_output.json | jq '.[] | {image_id, quality_score, sharpness, exposure}'

# View captions
cat output/reports/caption_generation_output.json | jq '.[] | {image_id, captions}'
```

---

## 🌐 Launch Website

### Start Development Server

```bash
cd output/website

# Install dependencies
npm install

# Run development server
npm run dev

# Server running at http://localhost:5173
```

### Build for Production

```bash
cd output/website

npm run build

# Outputs to dist/
```

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
    print(f"  Composition: {a['composition']}, Lighting: {a['lighting']}")
EOF
```

### Agent 5: Filtering & Categorization

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
    print(f"  Location: {c['location']}")
    print(f"  Passes Filter: {c['passes_filter']}")
EOF
```

### Agent 6: Caption Generation

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
EOF
```

---

## 📁 Common Paths

```
Travel-website/
├── config.yaml                 # Configuration file
├── .env                        # API keys (don't commit!)
├── orchestrator.py             # Main entry point
│
├── sample_images/              # Add your photos here
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── ...
│
├── agents/                     # Agent implementations
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── duplicate_detection.py
│   ├── filtering_categorization.py
│   ├── caption_generation.py
│   └── website_generation.py
│
├── utils/                      # Shared utilities
│   ├── logger.py              # Logging
│   ├── validation.py          # Schemas
│   ├── helpers.py             # File I/O
│   └── errors.py              # Error tracking
│
└── output/                     # Generated outputs
    ├── reports/               # Agent outputs + final report
    ├── logs/                  # Workflow logs
    ├── metadata/              # EXIF cache
    └── website/               # React app
        ├── src/
        ├── public/
        │   └── data/
        │       └── photos.json
        ├── package.json
        └── README.md
```

---

## ⚙️ Configuration Quick Reference

### Key Settings in config.yaml

```yaml
# Thresholds
thresholds:
  min_technical_quality: 3      # Minimum quality score (1-5)
  min_aesthetic_quality: 3      # Minimum aesthetic score (1-5)
  duplicate_hamming_distance: 10 # Similarity threshold

# Parallelization
agents:
  metadata_extraction:
    parallel_workers: 4          # I/O bound
  quality_assessment:
    parallel_workers: 2          # CPU bound
  aesthetic_assessment:
    parallel_workers: 2          # API rate limited
  filtering_categorization:
    parallel_workers: 2
  caption_generation:
    parallel_workers: 2

# Models
  aesthetic_assessment:
    model: "claude-3.5-sonnet"
  caption_generation:
    model: "claude-3.5-sonnet"

# Error handling
error_handling:
  max_retries: 3
  continue_on_error: true        # Don't stop on single image failure
```

---

## 🔧 Troubleshooting

### Issue: "No images found"

```bash
# Check that images exist
ls sample_images/

# Check file permissions
chmod 644 sample_images/*.jpg

# Verify config paths
cat config.yaml | grep input_images
```

### Issue: API Key Errors

```bash
# Verify .env file exists
ls -la .env

# Check API key format
grep OPENAI_API_KEY .env
grep GOOGLE_API_KEY .env

# Test API access
python -c "import os; print('OpenAI:', 'configured' if os.getenv('OPENAI_API_KEY') else 'missing')"
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
tail -f output/logs/workflow.log

# Check CPU usage
top

# Check memory usage
free -h
```

---

## 📚 Documentation Structure

- **[HLD.md](./HLD.md)** - High-level system architecture and overview
- **[LLD.md](./LLD.md)** - Detailed agent specs, schemas, implementation patterns
- **[UML_DIAGRAMS.md](./UML_DIAGRAMS.md)** - Class, sequence, component diagrams
- **[ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)** - Workflow and execution flows
- **[README.md](../README.md)** - Project overview and features

---

## 🎯 Next Steps

1. **Add images** → `sample_images/`
2. **Run workflow** → `uv run python orchestrator.py`
3. **View results** → `cat output/reports/final_report.json`
4. **Launch website** → `cd output/website && npm run dev`
5. **Read detailed docs** → See Documentation Structure above

---

## 💡 Tips

- **First run takes longer** due to dependency loading
- **Subsequent runs faster** with warm caches
- **Monitor logs** in real-time: `tail -f output/logs/workflow.log`
- **Adjust thresholds** for your use case in `config.yaml`
- **Use API keys** for production-quality results

---

**Questions?** Check the detailed documentation files or examine agent code directly.
