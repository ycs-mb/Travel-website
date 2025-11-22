# CLAUDE.md

Guidance for Claude Code when working with this travel photo organization system.

## 📚 Documentation Index

This repository has comprehensive, well-organized documentation:

| Document | Purpose | Best For |
|----------|---------|----------|
| **[QUICKSTART.md](./docs/QUICKSTART.md)** | 5-minute setup + common commands | Getting started quickly |
| **[HLD.md](./docs/HLD.md)** | High-level system architecture | Understanding the overall design |
| **[LLD.md](./docs/LLD.md)** | Agent specs, schemas, patterns | Implementation details |
| **[UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md)** | Class, sequence, components | Visual architecture |
| **[ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md)** | Workflow flows, state machines | Understanding execution flow |
| **[README.md](./README.md)** | Project overview and features | Feature overview |

**START HERE**: [QUICKSTART.md](./docs/QUICKSTART.md) for 5-minute setup!

---

## System Overview

**5-agent agentic workflow** for intelligent travel photo organization with **Flask web application**:

```
Web UI (Flask)
     ↓ Upload Photos
Agent 1: Metadata Extraction
  (EXIF, GPS + Reverse Geocoding, Camera Settings)
           ↓
    ┌──────┴──────┐
    ↓             ↓
Agent 2:      Agent 3:
Quality       Aesthetic      ← PARALLEL (ThreadPoolExecutor)
Assessment    Assessment        + Token Usage Tracking
    └──────┬──────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
Agent 4:      Agent 5:
Filtering &   Caption        ← Sequential (Agent 5 needs Agent 4)
Categorization Generation     + Reasoning + Token Tracking
     ↓
Web UI: Interactive Report
  - Tabbed interface
  - Token usage display
  - Detailed agent outputs
```

- **Input**: Travel photos via web upload or CLI (JPG, PNG, HEIC, RAW)
- **Output**: Interactive web reports with tabbed views + JSON files
- **Parallelization**: ThreadPoolExecutor for concurrent per-agent processing
- **Models**: Vertex AI (Gemini 1.5 Flash), OpenCV, geopy
- **Web Framework**: Flask with Clean SaaS UI design

---

## Quick Commands

```bash
# Setup (uv recommended)
uv sync
cp .env.example .env

# Configure Vertex AI
gcloud auth application-default login
nano config.yaml  # Set vertex_ai.project and vertex_ai.location

# Start web application (RECOMMENDED)
uv run python web_app/app.py
open http://localhost:5001

# Run CLI workflow (alternative)
uv run python orchestrator.py

# View results
cat output/{timestamp}/reports/final_report.json | jq .

# Monitor logs
tail -f output/{timestamp}/logs/workflow.log
```

**Full setup guide**: See [QUICKSTART.md](./docs/QUICKSTART.md)

---

## 🎯 What Claude Should Focus On

### When Adding Features
1. Check **[LLD.md](./docs/LLD.md)** for agent specs and schemas
2. Follow agent template pattern (see below)
3. Add validation schema to `utils/validation.py`
4. Update `config.yaml` with new settings
5. Register in `orchestrator.py`
6. Update web UI templates in `web_app/templates/` if needed

### When Debugging
1. Check **[ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md)** for execution flow
2. Review error logs: `cat output/{timestamp}/logs/errors.json | jq .`
3. Use agent testing code from **[QUICKSTART.md](./docs/QUICKSTART.md)**
4. Check Flask logs in terminal where `app.py` is running
5. Inspect browser console for frontend issues

### When Understanding Architecture
1. Start with **[HLD.md](./docs/HLD.md)** for overview
2. Review **[UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md)** for visual structure
3. Deep dive into **[LLD.md](./docs/LLD.md)** for implementation details
4. Check `web_app/app.py` for web application logic

---

## Key Architectural Patterns

### Agent Template
```python
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor, as_completed

class AgentName:
    SYSTEM_PROMPT = """..."""

    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.agent_config = config['agents']['agent_key']
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        
        # Vertex AI client initialization
        vertex_config = config.get('vertex_ai', {})
        self.client = genai.Client(
            vertexai=True,
            project=vertex_config.get('project'),
            location=vertex_config.get('location')
        )
        self.model_name = vertex_config.get('model', 'gemini-1.5-flash')

    def run(self, image_paths: List[Path], *upstream) -> Tuple[List[Dict], Dict]:
        """Return (output_list, validation_dict)."""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = [executor.submit(self.process_image, path) for path in image_paths]
            results = [f.result() for f in as_completed(futures)]
        return results, validation_summary

    def process_image(self, path: Path) -> Dict:
        try:
            # Call Vertex AI
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type)
                ]
            )
            
            # Extract token usage
            result = parse_response(response.text)
            if hasattr(response, 'usage_metadata'):
                result['token_usage'] = {
                    'prompt_token_count': response.usage_metadata.prompt_token_count,
                    'candidates_token_count': response.usage_metadata.candidates_token_count,
                    'total_token_count': response.usage_metadata.total_token_count
                }
            
            is_valid, error = validate_agent_output('agent_key', result)
            return result
        except Exception as e:
            log_error(self.logger, "Agent Name", type(e).__name__, str(e), "error")
            return self.default_result()
```

### Error Handling
```python
# Errors are logged but don't stop execution (graceful degradation)
# Configure in config.yaml → error_handling.continue_on_error: true

log_error(
    logger=self.logger,
    agent="Agent Name",
    error_type="ProcessingError|APIError|ValidationError",
    summary="Human-readable description",
    severity="info|warning|error|critical"
)
```

### Parallelization
```python
# All agents use ThreadPoolExecutor with configurable workers
# Worker counts from config.yaml: Agent1:4, Agent2:2, Agent3:2, etc.

with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
    futures = [executor.submit(self.process_image, path) for path in image_paths]
    for future in as_completed(futures):
        results.append(future.result())
```

### Web Application Pattern
```python
# Flask routes in web_app/app.py
@app.route('/')
def index():
    # List all workflow runs
    runs = get_all_runs()
    return render_template('index.html', runs=runs)

@app.route('/upload', methods=['POST'])
def upload():
    # Handle file upload
    files = request.files.getlist('photos')
    # Save to uploads/
    # Trigger orchestrator in background
    return jsonify({'run_id': run_id})

@app.route('/report/<timestamp>')
def view_report(timestamp):
    # Load all agent outputs
    images_data = load_agent_outputs(timestamp)
    return render_template('report.html', images=images_data)
```

---

## Configuration

**Key sections in config.yaml:**

```yaml
paths:
  input_images: sample_images/
  output_dir: output/
  upload_dir: uploads/

# Vertex AI Configuration (REQUIRED)
vertex_ai:
  project: "your-project-id"      # GCP project ID
  location: "us-central1"         # GCP region  
  model: "gemini-1.5-flash"       # Model name

agents:
  metadata_extraction:
    parallel_workers: 4        # I/O bound
  quality_assessment:
    parallel_workers: 2        # CPU bound
  aesthetic_assessment:
    parallel_workers: 2        # API rate limited
    batch_size: 5
  filtering_categorization:
    parallel_workers: 2
  caption_generation:
    parallel_workers: 2

thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

error_handling:
  continue_on_error: true
```

**Environment variables (.env):**

```bash
# Vertex AI uses Application Default Credentials (ADC)
# Set up with: gcloud auth application-default login
# Or: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

---

## File Structure

```
Travel-website/
├── CLAUDE.md                   # This file
├── docs/
│   ├── HLD.md                 # High-level design
│   ├── LLD.md                 # Low-level design
│   ├── UML_DIAGRAMS.md        # Architecture diagrams
│   ├── ACTIVITY_DIAGRAM.md    # Workflow flows
│   └── QUICKSTART.md          # Quick start guide
│
├── config.yaml                # Configuration
├── orchestrator.py            # Main workflow (CLI)
├── web_app/                   # Flask web application
│   ├── app.py                # Flask server + routes
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html        # Clean SaaS base template
│   │   ├── index.html       # Dashboard + upload
│   │   └── report.html      # Detailed tabbed report
│   └── static/              # CSS, JS, images
│
├── agents/                    # 5 agents
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
│
├── utils/                     # Logger, validation, helpers
├── sample_images/             # Input photos (CLI mode)
├── uploads/                   # Web upload storage
└── output/                    # Generated outputs (timestamped)
    └── YYYYMMDD_HHMMSS/
        ├── reports/          # Agent outputs + final report
        ├── logs/             # Workflow logs + errors
        └── processed_images/ # Processed images
```

---

## Vertex AI Integration

All vision/language agents (3, 4, 5) use Vertex AI:

```python
from google import genai
from google.genai import types

# Initialize client (in agent __init__)
vertex_config = config.get('vertex_ai', {})
self.client = genai.Client(
    vertexai=True,
    project=vertex_config.get('project'),
    location=vertex_config.get('location')
)
self.model_name = vertex_config.get('model', 'gemini-1.5-flash')

# Call API
response = self.client.models.generate_content(
    model=self.model_name,
    contents=[
        types.Part.from_text(text=prompt),
        types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
    ]
)

# Extract response
text = response.text

# Extract token usage
if hasattr(response, 'usage_metadata'):
    tokens = {
        'prompt_token_count': response.usage_metadata.prompt_token_count,
        'candidates_token_count': response.usage_metadata.candidates_token_count,
        'total_token_count': response.usage_metadata.total_token_count
    }
```

---

## Web UI Features

### Templates (Jinja2)

**base.html:**
- Clean SaaS design system
- Inter font
- CSS variables for theming
- Responsive layout

**index.html:**
- Drag-and-drop upload zone
- Run history list
- Status badges (Running/Completed/Failed)
- Auto-refresh for running workflows

**report.html:**
- Stats overview (total images, passed, scores)
- Image grid (responsive masonry)
- Per-image tabbed interface:
  - **Metadata**: Date, camera, GPS location, dimensions
  - **Quality**: Overall score + sharpness/noise/exposure + issues
  - **Aesthetic**: Overall score + composition/lighting/framing + notes
  - **Filtering**: Status, category, reasoning
  - **Caption**: Concise, standard, keywords
- Token usage display at bottom of applicable tabs

### Key UI Patterns

**Tab Switching (JavaScript):**
```javascript
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        // Switch active tab
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        // Switch content
        const target = this.dataset.target;
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelector(`.${target}`).classList.add('active');
    });
});
```

**Status Polling:**
```javascript
function pollStatus(runId) {
    fetch(`/status/${runId}`)
        .then(r => r.json())
        .then(data => {
            if (data.status === 'running') {
                setTimeout(() => pollStatus(runId), 3000);
            } else {
                window.location.reload();
            }
        });
}
```

---

## Performance Targets

| Agent | Model Type | Throughput | Token Usage |
|-------|-----------|------------|-------------|
| 1. Metadata Extraction | Library (Pillow + geopy) | ~100 img/min | N/A |
| 2. Quality Assessment | OpenCV + Algorithms | ~10 img/min | N/A |
| 3. Aesthetic Assessment | Vertex AI (Gemini 1.5 Flash) | ~5 img/min | ~500-1000/img |
| 4. Filtering & Categorization | Vertex AI (Gemini 1.5 Flash) | ~10 img/min | ~300-600/img |
| 5. Caption Generation | Vertex AI (Gemini 1.5 Flash) | ~10 img/min | ~600-1200/img |

**Total for 150 images: ~8-12 minutes** (with parallelization)
**Total token usage: ~200K-400K tokens** (varies by image complexity)

---

## Important Notes

- **Dependencies**: Managed by `uv` and `pyproject.toml`
- **Image Formats**: JPG, PNG, HEIC, RAW (HEIC read directly with pillow-heif)
- **Continue-on-Error**: Default enabled; failed images get placeholder results
- **Logging**: Structured JSON logs in `output/{timestamp}/logs/`
- **Validation**: 3-tier system (agent output, summary, final report)
- **Token Tracking**: Captured for all Vertex AI API calls
- **Reverse Geocoding**: GPS coordinates → location names using Nominatim
- **Filtering Reasoning**: Explains pass/reject decisions based on thresholds

---

## Key Changes from Original Design

1. **Vertex AI Migration**: 
   - Changed from `google-generativeai` to `google-genai` (Vertex AI SDK)
   - Uses Application Default Credentials instead of API keys
   - Requires GCP project configuration

2. **Web Application**:
   - Added Flask web server (`web_app/app.py`)
   - Created Clean SaaS UI templates
   - Drag-and-drop upload interface
   - Interactive tabbed reports

3. **Enhanced Features**:
   - Token usage tracking for cost optimization
   - Reverse geocoding for GPS coordinates
   - Filtering reasoning explanations
   - Per-agent detailed output display

4. **Parallel Execution**:
   - Using ThreadPoolExecutor within each agent
   - Metadata + Quality/Aesthetic run in parallel at workflow level

---

**For complete details, see the documentation directory `docs/`**
