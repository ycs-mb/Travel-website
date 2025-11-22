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

### Web Application (Recommended)

```bash
# Start Flask server with uv
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

### CLI Workflow (Alternative)

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
├── web_app/
│   └── app.py                 # Flask web server (start here!)
├── orchestrator.py             # CLI workflow entry point
│
├── sample_images/              # Add your photos here (CLI mode)
│   ├── photo1.jpg
│   └── ...
│
├── uploads/                    # Web upload temporary storage
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
│   └── helpers.py             # File I/O
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

1. **Start web app** → `uv run python web_app/app.py`
2. **Upload photos** → Drag and drop on `http://localhost:5001`
3. **Process images** → Click "Upload and Process"
4. **View results** → Click on completed run
5. **Explore tabs** → See metadata, quality, aesthetic, filtering, captions
6. **Check tokens** → Monitor API usage at bottom of tabs
7. **Read detailed docs** → See Documentation Structure above

---

## 💡 Tips

- **Web UI is recommended** for ease of use and visualization
- **First run takes longer** due to dependency loading and model initialization
- **Subsequent runs faster** with warm caches
- **Monitor token usage** to optimize API costs
- **Adjust thresholds** for your use case in `config.yaml`
- **Use reverse geocoding** to get location names from GPS coordinates
- **Check filtering reasoning** to understand automated decisions

---

**Questions?** Check the detailed documentation files or examine agent code directly.
