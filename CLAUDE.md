# CLAUDE.md

Guidance for Claude Code when working with this travel photo organization system.

## 📚 Documentation Index

This repository has comprehensive, well-organized documentation:

| Document | Purpose | Best For |
|----------|---------|----------|
| **[README.md](./README.md)** | Project overview and features | Feature overview and quick start |
| **[QUICKSTART.md](./docs/QUICKSTART.md)** | 5-minute setup + common commands | Getting started quickly |
| **[GEMINI.md](./GEMINI.md)** | Quick overview for LLMs | High-level understanding |
| **[HLD.md](./docs/HLD.md)** | High-level system architecture | Understanding the overall design |
| **[LLD.md](./docs/LLD.md)** | Agent specs, schemas, patterns | Implementation details |
| **[UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md)** | Class, sequence, components | Visual architecture |
| **[ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md)** | Workflow flows, state machines | Understanding execution flow |

**START HERE**: [README.md](./README.md) for quick setup or [QUICKSTART.md](./docs/QUICKSTART.md) for detailed guide!

---

## System Overview

**Production-ready 5-agent agentic workflow** for intelligent travel photo organization with modern Flask web application.

### What Makes This System Unique

1. **Multi-Agent Architecture**: 5 specialized agents with distinct expertise areas
2. **Parallel Execution**: Optimized pipeline with concurrent agent processing
3. **Vertex AI Integration**: Uses Google's Gemini 2.0 Flash Lite for vision/language tasks
4. **Native HEIC Support**: Direct reading of iPhone HEIC files without conversion
5. **Token Usage Tracking**: Built-in cost monitoring for LLM API calls
6. **Graceful Degradation**: Continue-on-error design with placeholder results
7. **Interactive Web UI**: Clean SaaS design with tabbed reports
8. **3-Tier Validation**: Agent output → summary → final report validation
9. **Structured Logging**: JSON logs with error tracking and performance metrics
10. **Reverse Geocoding**: GPS coordinates → location names automatically

### Architecture Flow

```
Web UI (Flask) or CLI
     ↓ Upload/Select Photos
Agent 1: Metadata Extraction
  (EXIF, GPS + Reverse Geocoding, Camera Settings, Timestamps)
           ↓
    ┌──────┴──────┐
    ↓             ↓
Agent 2:      Agent 3:
Quality       Aesthetic      ← PARALLEL (ThreadPoolExecutor)
Assessment    Assessment        Computer Vision + Gemini Vision
(OpenCV)      (Vertex AI)       + Token Usage Tracking
    └──────┬──────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
Agent 4:      Agent 5:
Filtering &   Caption        ← PARALLEL (with Agent 4 data available to Agent 5)
Categorization Generation      Both use Vertex AI + Reasoning
(Vertex AI)   (Vertex AI)      + Token Tracking
     ↓             ↓
     └──────┬──────┘
            ↓
Web UI: Interactive Report
  - Image gallery with metadata overlays
  - Per-image tabbed interface (5 tabs)
  - Token usage display per agent
  - Quality distribution charts
  - Category breakdowns
  - Filtering reasoning
```

**Technical Stack:**
- **Input**: JPG, PNG, HEIC, RAW (via web upload or CLI)
- **Output**: Interactive HTML reports + JSON files + structured logs
- **Parallelization**: ThreadPoolExecutor within agents + orchestrator-level parallel groups
- **Vision/Language Models**: Vertex AI Gemini 2.0 Flash Lite
- **Computer Vision**: OpenCV + scikit-image
- **Geolocation**: geopy with Nominatim reverse geocoding
- **Web Framework**: Flask 3.0+ with Jinja2 templates
- **Package Manager**: uv (modern, fast Python package manager)

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

### Agent Template Pattern

All agents follow this consistent structure:

```python
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from google import genai
from google.genai import types
from PIL import Image

from utils.logger import log_error, log_info, log_warning
from utils.validation import validate_agent_output, create_validation_summary
from utils.heic_reader import is_heic_file, open_heic_with_pil

class AgentName:
    """
    Agent N: [Agent Name]

    System Prompt:
    [Description of agent's expertise and role]
    """

    SYSTEM_PROMPT = """
    [Detailed system prompt for the agent]
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """Initialize agent with config and logger."""
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('agent_key', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)

        # For agents using Vertex AI (Agents 3, 4, 5)
        self.api_config = config.get('api', {}).get('google', {})
        self.model_name = self.api_config.get('model', 'gemini-2.0-flash-lite')

        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.api_config.get('project'),
                location=self.api_config.get('location', 'us-central1')
            )
            log_info(self.logger, f"Initialized Vertex AI client", "Agent Name")
        except Exception as e:
            log_warning(self.logger, f"Failed to initialize Vertex AI client: {e}", "Agent Name")
            self.client = None

    def run(self, image_paths: List[Path], *upstream_data) -> Tuple[List[Dict], Dict]:
        """
        Process all images and return results with validation.

        Args:
            image_paths: List of image file paths
            *upstream_data: Optional upstream agent outputs

        Returns:
            Tuple of (results_list, validation_summary)
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {executor.submit(self.process_image, path, *upstream_data): path
                      for path in image_paths}

            for future in as_completed(futures):
                path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    log_error(self.logger, "Agent Name", type(e).__name__, str(e), "error")
                    results.append(self._default_result(path))

        # Validation
        validation_summary = create_validation_summary('agent_key', results)

        return results, validation_summary

    def process_image(self, image_path: Path, *upstream_data) -> Dict[str, Any]:
        """
        Process a single image.

        Args:
            image_path: Path to image file
            *upstream_data: Optional upstream agent outputs

        Returns:
            Processing results dictionary
        """
        try:
            # Load image (handles HEIC automatically)
            if is_heic_file(image_path):
                image = open_heic_with_pil(image_path)
            else:
                image = Image.open(image_path)

            # Convert to RGB if needed
            if image.mode not in ['RGB', 'RGBA']:
                image = image.convert('RGB')

            # For Vertex AI agents: prepare bytes
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()

            # Call API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_text(text=self._create_prompt()),
                    types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
                ]
            )

            # Parse response
            result = self._parse_response(response.text)
            result['image_path'] = str(image_path)
            result['filename'] = image_path.name

            # Extract token usage
            if hasattr(response, 'usage_metadata'):
                result['token_usage'] = {
                    'prompt_token_count': response.usage_metadata.prompt_token_count,
                    'candidates_token_count': response.usage_metadata.candidates_token_count,
                    'total_token_count': response.usage_metadata.total_token_count
                }

            # Validate
            is_valid, error = validate_agent_output('agent_key', result)
            if not is_valid:
                log_warning(self.logger, f"Validation failed: {error}", "Agent Name")

            return result

        except Exception as e:
            log_error(self.logger, "Agent Name", type(e).__name__, str(e), "error")
            return self._default_result(image_path)

    def _create_prompt(self) -> str:
        """Create agent-specific prompt."""
        return f"{self.SYSTEM_PROMPT}\n\n[Additional context]"

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse API response text into structured data."""
        # Implementation specific to each agent
        pass

    def _default_result(self, image_path: Path) -> Dict[str, Any]:
        """Return default/error result."""
        return {
            'image_path': str(image_path),
            'filename': image_path.name,
            'error': True,
            # Agent-specific default values
        }
```

**Key Patterns:**
- All agents return `(results_list, validation_summary)` from `run()`
- Use `ThreadPoolExecutor` with configurable workers
- HEIC support via `utils.heic_reader`
- Graceful error handling with default results
- Token usage tracking for Vertex AI agents
- Structured logging via `utils.logger`

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
  input_images: "./sample_images"
  output_dir: "./output"
  metadata_output: "./output/metadata"
  reports_output: "./output/reports"
  website_output: "./output/website"
  logs_output: "./output/logs"

# API Configuration (Vertex AI via Google GenAI)
api:
  openai:
    model: "gpt-4-vision-preview"
    max_tokens: 4096
    temperature: 0.7

  google:
    model: "gemini-2.0-flash-lite"       # Gemini model via Vertex AI
    project: "gcloud-photo-project"      # Your GCP project ID
    location: "us-central1"              # GCP region
    max_tokens: 2048
    temperature: 0.7

agents:
  metadata_extraction:
    enabled: true
    parallel_workers: 4        # I/O bound
    timeout_seconds: 30

  quality_assessment:
    enabled: true
    batch_size: 10
    model: "clip-iqa"          # Options: clip-iqa, gpt4v
    parallel_workers: 2        # CPU bound

  aesthetic_assessment:
    enabled: true
    batch_size: 5
    parallel_workers: 2        # API rate limited

  filtering_categorization:
    enabled: true
    min_technical_score: 3
    min_aesthetic_score: 3
    batch_size: 10

  caption_generation:
    enabled: true
    batch_size: 5
    include_keywords: true

thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3
  min_resolution_pixels: 2000000  # 2MP
  max_noise_threshold: 0.15
  min_sharpness_variance: 100

error_handling:
  max_retries: 3
  retry_delay_seconds: 2
  continue_on_error: true
  severity_levels: ["info", "warning", "error", "critical"]

# Parallelization Strategy
parallelization:
  enable_parallel_agents: true
  max_workers: 4
  parallel_groups:
    - ["quality_assessment", "aesthetic_assessment"]
    - ["filtering_categorization", "caption_generation"]
```

**Environment variables (.env):**

```bash
# Vertex AI uses Application Default Credentials (ADC)
# Set up with: gcloud auth application-default login
# Or: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Optional API keys (for OpenAI if needed)
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Workflow Configuration Overrides
INPUT_IMAGES_PATH=./sample_images
OUTPUT_DIR=./output
LOG_LEVEL=INFO
PARALLEL_WORKERS=4
```

---

## File Structure

```
Travel-website/
├── CLAUDE.md                   # This file - AI assistant guidance
├── GEMINI.md                   # Quick overview for LLMs
├── README.md                   # Project overview and quick start
├── .env.example                # Environment variable template
├── .python-version             # Python version specification
├── pyproject.toml              # Project dependencies and config
├── requirements.txt            # Pip requirements file
├── uv.lock                     # UV lock file for dependencies
├── config.yaml                 # Main workflow configuration
│
├── docs/                       # Comprehensive documentation
│   ├── QUICKSTART.md          # Quick start guide
│   ├── HLD.md                 # High-level design
│   ├── LLD.md                 # Low-level design specs
│   ├── UML_DIAGRAMS.md        # Architecture diagrams
│   └── ACTIVITY_DIAGRAM.md    # Workflow flow diagrams
│
├── orchestrator.py             # Main workflow orchestrator (CLI)
├── run_agents.py               # Agent runner utility
│
├── web_app/                    # Flask web application
│   ├── app.py                 # Flask server + routes
│   └── templates/             # Jinja2 templates (CSS/JS embedded)
│       ├── base.html         # Clean SaaS base template
│       ├── index.html        # Dashboard with drag-and-drop upload
│       └── report.html       # Interactive tabbed report view
│
├── agents/                     # 5 specialized AI agents
│   ├── __init__.py
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
│
├── utils/                      # Shared utilities
│   ├── __init__.py
│   ├── logger.py              # Structured logging setup
│   ├── validation.py          # 3-tier validation system
│   ├── helpers.py             # Config loading, file utilities
│   └── heic_reader.py         # HEIC/HEIF file support
│
├── sample_images/              # Sample input photos (CLI mode)
├── uploads/                    # Web upload storage (created on first upload)
└── output/                     # Generated outputs (timestamped runs)
    └── YYYYMMDD_HHMMSS/       # Each run gets unique timestamp
        ├── reports/           # Agent outputs + final_report.json
        ├── logs/              # workflow.log + errors.json
        ├── metadata/          # Extracted metadata files
        └── website/           # Generated website assets
```

**Note**: The `uploads/` and `output/` directories are created automatically on first use. No static assets directory exists - all CSS/JS is embedded in templates for simplicity.

---

## Vertex AI Integration

All vision/language agents (Agents 3, 4, 5) use Google's Vertex AI with the Gemini model:

```python
from google import genai
from google.genai import types
from PIL import Image
import base64

# Initialize client (in agent __init__)
api_config = config.get('api', {}).get('google', {})
self.client = genai.Client(
    vertexai=True,
    project=api_config.get('project'),
    location=api_config.get('location', 'us-central1')
)
self.model_name = api_config.get('model', 'gemini-2.0-flash-lite')

# Load and prepare image
image = Image.open(image_path)
# Convert to RGB if needed
if image.mode not in ['RGB', 'RGBA']:
    image = image.convert('RGB')

# Convert to bytes
import io
buffer = io.BytesIO()
image.save(buffer, format='JPEG')
image_bytes = buffer.getvalue()

# Call Vertex AI API
response = self.client.models.generate_content(
    model=self.model_name,
    contents=[
        types.Part.from_text(text=prompt),
        types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
    ]
)

# Extract response text
result = response.text

# Extract token usage (for cost tracking)
if hasattr(response, 'usage_metadata'):
    token_usage = {
        'prompt_token_count': response.usage_metadata.prompt_token_count,
        'candidates_token_count': response.usage_metadata.candidates_token_count,
        'total_token_count': response.usage_metadata.total_token_count
    }
```

**Important Notes:**
- Uses `google-genai` package (not `google-generativeai`)
- Requires GCP project with Vertex AI API enabled
- Configuration is in `config.yaml` under `api.google`
- Supports HEIC files via `pillow-heif` (converted to PIL Image automatically)

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
| 1. Metadata Extraction | Pillow + geopy (reverse geocoding) | ~100 img/min | N/A |
| 2. Quality Assessment | OpenCV + Computer Vision | ~10-20 img/min | N/A |
| 3. Aesthetic Assessment | Vertex AI (Gemini 2.0 Flash Lite) | ~5-10 img/min | ~500-1000/img |
| 4. Filtering & Categorization | Vertex AI (Gemini 2.0 Flash Lite) | ~10-15 img/min | ~300-600/img |
| 5. Caption Generation | Vertex AI (Gemini 2.0 Flash Lite) | ~8-12 img/min | ~600-1200/img |

**Parallel Execution Strategy:**
- Stage 1: Metadata Extraction (Agent 1) runs first
- Stage 2: Quality + Aesthetic (Agents 2 & 3) run in parallel
- Stage 3: Filtering + Caption (Agents 4 & 5) can run in parallel but Agent 5 may use Agent 4's output

**Estimates for 150 images:**
- Total processing time: ~8-15 minutes (with parallelization)
- Total token usage: ~200K-400K tokens (varies by image complexity)
- Cost: ~$0.50-$2.00 (depending on Gemini pricing tier)

---

## Development Workflows

### Testing Individual Agents

Use `run_agents.py` to test agents individually:

```bash
# Test a specific agent
uv run python run_agents.py --agent metadata

# Test with custom config
uv run python run_agents.py --agent quality --config custom_config.yaml

# Test on specific images
uv run python run_agents.py --agent aesthetic --images "sample_images/*.jpg"
```

### Adding a New Agent

1. **Create agent file** in `agents/` following the template pattern
2. **Add configuration** to `config.yaml`:
   ```yaml
   agents:
     new_agent:
       enabled: true
       parallel_workers: 2
       batch_size: 5
   ```
3. **Add validation schema** in `utils/validation.py`:
   ```python
   SCHEMAS['new_agent'] = {
       'type': 'object',
       'required': ['filename', 'result_field'],
       'properties': {...}
   }
   ```
4. **Register in orchestrator** (`orchestrator.py`):
   ```python
   from agents import NewAgent
   # In __init__:
   self.agents['new_agent'] = NewAgent(self.config, self.logger)
   # In run_workflow: add to execution sequence
   ```
5. **Update web templates** if needed to display new agent outputs

### Modifying Agent Prompts

Agent prompts are defined in each agent class as `SYSTEM_PROMPT`:

```python
# agents/aesthetic_assessment.py
SYSTEM_PROMPT = """
You are a world-renowned photo curator...
[Modify prompt here]
"""
```

**Testing prompt changes:**
1. Modify the `SYSTEM_PROMPT` in the agent file
2. Test with a small batch: `uv run python run_agents.py --agent aesthetic --images "sample_images/test*.jpg"`
3. Review outputs in `output/{timestamp}/reports/`
4. Iterate until satisfied

### Updating Dependencies

```bash
# Add new dependency
uv add package-name

# Update existing dependency
uv add package-name --upgrade

# Sync all dependencies
uv sync

# Export to requirements.txt for compatibility
uv pip compile pyproject.toml -o requirements.txt
```

### Code Quality

The project uses Black, Ruff, and MyPy for code quality:

```bash
# Format code
uv run black agents/ utils/ orchestrator.py web_app/

# Lint code
uv run ruff check agents/ utils/ orchestrator.py

# Type checking
uv run mypy agents/ utils/ orchestrator.py
```

### Git Workflow

The repository uses feature branches:

```bash
# Create feature branch
git checkout -b feature/agent-improvements

# Make changes and commit
git add .
git commit -m "feat: improve aesthetic assessment scoring"

# Push to remote
git push -u origin feature/agent-improvements

# Create PR via GitHub UI
```

### Common Troubleshooting

**Vertex AI Authentication Issues:**
```bash
# Re-authenticate
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token

# Check project/location in config.yaml
```

**HEIC File Support:**
```bash
# Ensure pillow-heif is installed
uv add pillow-heif

# Test HEIC reading
python -c "from utils.heic_reader import is_heic_file; print('HEIC support OK')"
```

**Token Usage Concerns:**
- Check `result['token_usage']` in agent outputs
- Monitor costs in GCP Console → Vertex AI
- Adjust batch sizes in `config.yaml` to control API rate
- Use smaller test batches during development

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

## Web Application Details

### Flask Routes (`web_app/app.py`)

```python
@app.route('/')
def index():
    """Home page - shows run history and upload interface"""
    # Lists all past workflow runs from output/ directory
    # Displays run status, image counts, timestamps

@app.route('/run', methods=['POST'])
def trigger_run():
    """Handle photo upload and trigger workflow"""
    # Creates timestamped upload directory
    # Saves uploaded files
    # Starts workflow in background thread
    # Returns run_id for status tracking

@app.route('/status/<run_id>')
def check_status(run_id):
    """Check workflow execution status"""
    # Returns JSON: {status: 'idle|running|completed|failed'}
    # Used by frontend for polling

@app.route('/report/<timestamp>')
def view_report(timestamp):
    """View detailed interactive report"""
    # Loads final_report.json and all agent outputs
    # Renders tabbed interface with image gallery
    # Shows token usage, quality distributions, etc.

@app.route('/output/<path:filepath>')
def serve_output(filepath):
    """Serve images and output files"""
    # Static file serving for processed images
```

### Template Structure

**base.html**:
- Clean SaaS design system with CSS variables
- Inter font from Google Fonts
- Responsive layout with mobile support
- Dark/light theming via CSS variables
- All CSS/JS embedded (no separate static files)

**index.html**:
- Drag-and-drop upload zone (JavaScript FileReader API)
- Run history table with sortable columns
- Status badges (running/completed/failed)
- Auto-refresh for active runs (3-second polling)

**report.html**:
- Statistics overview (total images, passed/filtered, avg scores)
- Responsive image gallery (masonry grid layout)
- Per-image expandable cards with 5 tabs:
  1. **Metadata**: EXIF, GPS, camera, location name
  2. **Quality**: Overall score, sharpness, noise, exposure, issues
  3. **Aesthetic**: Overall score, composition, lighting, framing, notes
  4. **Filtering**: Pass/reject status, category, reasoning
  5. **Caption**: Concise/standard captions, keywords
- Token usage display (per image and totals)
- Export options (JSON download)

### Background Processing

The web app uses threading for non-blocking workflow execution:

```python
def run_workflow_thread(input_path):
    """Runs workflow in background thread"""
    global current_run
    current_run['status'] = 'running'

    try:
        orchestrator = TravelPhotoOrchestrator(
            config_overrides={'paths': {'input_images': str(input_path)}}
        )
        report = orchestrator.run_workflow()
        current_run['status'] = 'completed'
        current_run['run_id'] = latest_timestamp
    except Exception as e:
        current_run['status'] = 'failed'
        current_run['log'].append(str(e))

# Triggered in /run route:
thread = threading.Thread(target=run_workflow_thread, args=(upload_path,))
thread.daemon = True
thread.start()
```

**Note**: For production, consider using Celery/Redis for more robust background job handling.

---

## Key Architecture Decisions

### 1. Vertex AI vs OpenAI
- **Chosen**: Vertex AI with Gemini 2.0 Flash Lite
- **Rationale**: Better image understanding, lower cost, GCP integration
- **Config**: Uses Application Default Credentials (ADC) for auth

### 2. Embedded Templates vs Static Assets
- **Chosen**: All CSS/JS embedded in Jinja2 templates
- **Rationale**: Simpler deployment, fewer files, easier debugging
- **Trade-off**: Slightly larger HTML files, but better for this use case

### 3. Threading vs AsyncIO
- **Chosen**: ThreadPoolExecutor for agent parallelization
- **Rationale**: Simpler for I/O-bound tasks, better with GIL-bound CV ops
- **Note**: Each agent can process multiple images in parallel

### 4. Continue-on-Error Pattern
- **Chosen**: Failed images get placeholder results
- **Rationale**: Don't fail entire batch due to one bad image
- **Implementation**: Try/except in each agent's `process_image()`

### 5. 3-Tier Validation
- **Tier 1**: Individual agent output validation
- **Tier 2**: Agent summary validation (aggregate stats)
- **Tier 3**: Final report validation (all agents combined)
- **Rationale**: Catch errors at multiple levels, ensure data integrity

---

## Recent Major Changes

### Migration to Vertex AI (Nov 2024)
- Changed from `google-generativeai` to `google-genai` SDK
- Updated all agents (3, 4, 5) to use Vertex AI client
- Requires GCP project configuration in `config.yaml`
- Uses ADC for authentication instead of API keys

### Web Interface Addition (Nov 2024)
- Added Flask web application with Clean SaaS UI
- Drag-and-drop upload interface
- Interactive tabbed reports
- Background workflow execution
- Run history and status tracking

### HEIC Support (Nov 2024)
- Added `pillow-heif` integration
- Created `utils/heic_reader.py` for HEIC handling
- All agents automatically handle HEIC files
- No manual conversion needed

### Enhanced Features (Nov 2024)
- Token usage tracking for all Vertex AI calls
- Reverse geocoding (GPS → location names)
- Filtering reasoning explanations
- Per-agent detailed output in web UI
- Parallel execution optimization

---

## Quick Reference for AI Assistants

### File Navigation
- **Agent implementations**: `agents/*.py` (5 agents)
- **Orchestrator**: `orchestrator.py` (main workflow)
- **Web app**: `web_app/app.py` + `web_app/templates/*.html`
- **Utilities**: `utils/*.py` (logger, validation, helpers, heic_reader)
- **Config**: `config.yaml` (main config), `.env` (secrets)
- **Docs**: `docs/*.md` (comprehensive documentation)
- **Dependencies**: `pyproject.toml` (uv), `requirements.txt` (pip)

### Key Files to Check
- **Adding features**: Check `docs/LLD.md` for specs, then `utils/validation.py` for schemas
- **Debugging**: `output/{timestamp}/logs/workflow.log` and `errors.json`
- **Agent prompts**: Each agent file has `SYSTEM_PROMPT` constant
- **Validation schemas**: `utils/validation.py` → `SCHEMAS` dictionary
- **Web routes**: `web_app/app.py` → Flask routes
- **Templates**: `web_app/templates/` → `base.html`, `index.html`, `report.html`

### Common Commands
```bash
# Run web app (recommended)
uv run python web_app/app.py

# Run CLI workflow
uv run python orchestrator.py

# Test individual agent
uv run python run_agents.py --agent [metadata|quality|aesthetic|filtering|captions]

# Install/update dependencies
uv sync
uv add package-name

# Code quality
uv run black agents/ utils/ orchestrator.py web_app/
uv run ruff check agents/ utils/ orchestrator.py

# View results
cat output/*/reports/final_report.json | jq .
```

### Agent Quick Reference
| Agent | File | Uses Vertex AI | Key Function |
|-------|------|----------------|--------------|
| 1. Metadata | `metadata_extraction.py` | ❌ | Extract EXIF, GPS, reverse geocode |
| 2. Quality | `quality_assessment.py` | ❌ | OpenCV sharpness, noise, exposure |
| 3. Aesthetic | `aesthetic_assessment.py` | ✅ | Gemini composition, lighting eval |
| 4. Filtering | `filtering_categorization.py` | ✅ | Gemini categorize + filter by quality |
| 5. Caption | `caption_generation.py` | ✅ | Gemini concise/standard captions |

### Vertex AI Configuration
```yaml
# config.yaml
api:
  google:
    model: "gemini-2.0-flash-lite"
    project: "your-gcp-project-id"
    location: "us-central1"
```

```bash
# Authentication
gcloud auth application-default login
```

### When Things Break
1. **Check logs**: `output/{timestamp}/logs/workflow.log`
2. **Check errors**: `output/{timestamp}/logs/errors.json`
3. **Verify Vertex AI auth**: `gcloud auth application-default print-access-token`
4. **Check config**: Ensure `config.yaml` has correct project/location
5. **Test agent individually**: `uv run python run_agents.py --agent [name]`
6. **Check dependencies**: `uv sync`

---

**For complete details, see the documentation directory `docs/`**

**Last updated**: December 2024 (reflecting Vertex AI migration + web interface)
