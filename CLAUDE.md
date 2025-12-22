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

### Token Optimization Priority

**CRITICAL**: All Vertex AI agents (3, 4, 5) must implement token tracking and optimization:

1. **Track every API call**: Capture `usage_metadata` and calculate costs
2. **Implement optimizations**: Image resizing, concise prompts, skip rejected captions
3. **Display costs**: Show per-image and aggregate costs in UI and reports
4. **Monitor thresholds**: Alert when costs exceed configured limits
5. **See dedicated section**: [Token Usage Tracking & Cost Monitoring](#token-usage-tracking--cost-monitoring)

**Expected Results:**
- Per-image cost tracking: ✅
- Aggregate cost reports: ✅
- 50-60% cost reduction with optimizations: ✅
- Real-time cost display in web UI: ✅

### When Adding Features
1. Check **[LLD.md](./docs/LLD.md)** for agent specs and schemas
2. Follow agent template pattern (see below)
3. **Add token tracking** if using Vertex AI (required!)
4. Add validation schema to `utils/validation.py`
5. Update `config.yaml` with new settings (including optimization flags)
6. Register in `orchestrator.py`
7. Update web UI templates in `web_app/templates/` if needed

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

### Agent Template (with Token Tracking)
```python
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import io
from PIL import Image

class AgentName:
    SYSTEM_PROMPT = """Analyze this travel photo. Return JSON only."""

    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.logger = logger
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

        # Token tracking
        self.total_tokens = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

        # Pricing (Gemini 1.5 Flash - Dec 2025)
        pricing_config = vertex_config.get('pricing', {})
        self.pricing = {
            'input_per_1k': pricing_config.get('input_per_1k_tokens', 0.000075),
            'output_per_1k': pricing_config.get('output_per_1k_tokens', 0.0003)
        }

        # Optimization settings
        self.optimization = vertex_config.get('optimization', {})
        self.max_image_dimension = self.optimization.get('max_image_dimension', 1024)
        self.enable_caching = self.optimization.get('enable_caching', False)

    def run(self, image_paths: List[Path], *upstream) -> Tuple[List[Dict], Dict]:
        """Return (output_list, validation_dict)."""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = [executor.submit(self.process_image, path) for path in image_paths]
            results = [f.result() for f in as_completed(futures)]

        # Generate usage summary
        usage_summary = self.get_usage_summary()
        self.logger.info(f"Agent completed. Total cost: ${usage_summary['estimated_cost_usd']:.4f}")

        return results, validation_summary

    def resize_image(self, path: Path) -> bytes:
        """Resize image to reduce token usage."""
        img = Image.open(path)

        if max(img.size) > self.max_image_dimension:
            img.thumbnail((self.max_image_dimension, self.max_image_dimension), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format=img.format or 'JPEG', quality=85)
        return buffer.getvalue()

    def process_image(self, path: Path) -> Dict:
        try:
            # Resize image if optimization enabled
            if self.max_image_dimension:
                image_bytes = self.resize_image(path)
                media_type = 'image/jpeg'
            else:
                with open(path, 'rb') as f:
                    image_bytes = f.read()
                media_type = f'image/{path.suffix[1:]}'

            # Build concise prompt
            prompt = f"{self.SYSTEM_PROMPT}\n\nRespond with ONLY valid JSON."

            # Call Vertex AI
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type)
                ]
            )

            # Parse response
            result = parse_response(response.text)
            result['filename'] = str(path)

            # Extract and track token usage
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata

                # Calculate cost for this image
                input_cost = (usage.prompt_token_count / 1000) * self.pricing['input_per_1k']
                output_cost = (usage.candidates_token_count / 1000) * self.pricing['output_per_1k']

                result['token_usage'] = {
                    'prompt_token_count': usage.prompt_token_count,
                    'candidates_token_count': usage.candidates_token_count,
                    'total_token_count': usage.total_token_count,
                    'estimated_cost_usd': input_cost + output_cost
                }

                # Update running totals
                self.total_tokens['prompt_tokens'] += usage.prompt_token_count
                self.total_tokens['completion_tokens'] += usage.candidates_token_count
                self.total_tokens['total_tokens'] += usage.total_token_count

            is_valid, error = validate_agent_output('agent_key', result)
            if not is_valid:
                self.logger.warning(f"Validation failed for {path.name}: {error}")

            return result

        except Exception as e:
            log_error(self.logger, "Agent Name", type(e).__name__, str(e), "error")
            return self.default_result()

    def get_usage_summary(self) -> Dict:
        """Return aggregated token usage and costs."""
        input_cost = (self.total_tokens['prompt_tokens'] / 1000) * self.pricing['input_per_1k']
        output_cost = (self.total_tokens['completion_tokens'] / 1000) * self.pricing['output_per_1k']

        return {
            'total_tokens': self.total_tokens,
            'estimated_cost_usd': input_cost + output_cost,
            'cost_breakdown': {
                'input_cost': input_cost,
                'output_cost': output_cost
            }
        }

    def default_result(self) -> Dict:
        """Return placeholder result on error."""
        return {
            'error': True,
            'filename': '',
            'token_usage': {
                'prompt_token_count': 0,
                'candidates_token_count': 0,
                'total_token_count': 0,
                'estimated_cost_usd': 0.0
            }
        }
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
  cache_dir: cache/              # For result caching

# Vertex AI Configuration (REQUIRED)
vertex_ai:
  project: "your-project-id"      # GCP project ID
  location: "us-central1"         # GCP region
  model: "gemini-1.5-flash"       # Model name

  # Token optimization settings
  pricing:
    input_per_1k_tokens: 0.000075   # $0.075 per 1M input tokens
    output_per_1k_tokens: 0.0003    # $0.30 per 1M output tokens

  optimization:
    enable_caching: true            # Cache API results
    max_image_dimension: 1024       # Resize images (reduces tokens)
    skip_captions_for_rejected: true # Don't caption rejected images
    use_concise_prompts: true       # Minimize prompt length

agents:
  metadata_extraction:
    parallel_workers: 4        # I/O bound
  quality_assessment:
    parallel_workers: 2        # CPU bound
  aesthetic_assessment:
    parallel_workers: 2        # API rate limited
    batch_size: 5
    enable_token_tracking: true
  filtering_categorization:
    parallel_workers: 2
    enable_token_tracking: true
  caption_generation:
    parallel_workers: 2
    enable_token_tracking: true
    skip_rejected: true        # Only caption passed images

thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

error_handling:
  continue_on_error: true

# Cost monitoring
cost_tracking:
  enabled: true
  log_per_image: true           # Log cost for each image
  display_in_ui: true           # Show costs in web UI
  alert_threshold_usd: 1.0      # Warn if batch exceeds threshold
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

## Token Usage Tracking & Cost Monitoring

### Implementation Pattern

All Vertex AI agents track token usage per image and aggregate costs:

```python
class AgentWithTokenTracking:
    def __init__(self, config: Dict, logger: Logger):
        # ... initialization ...
        self.total_tokens = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

        # Gemini 1.5 Flash pricing (as of Dec 2025)
        self.pricing = {
            'input_per_1k': 0.000075,   # $0.075 per 1M tokens
            'output_per_1k': 0.0003      # $0.30 per 1M tokens
        }

    def process_image(self, path: Path) -> Dict:
        try:
            response = self.client.models.generate_content(...)

            # Extract and store token usage
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                token_data = {
                    'prompt_token_count': usage.prompt_token_count,
                    'candidates_token_count': usage.candidates_token_count,
                    'total_token_count': usage.total_token_count
                }

                # Calculate cost for this image
                input_cost = (usage.prompt_token_count / 1000) * self.pricing['input_per_1k']
                output_cost = (usage.candidates_token_count / 1000) * self.pricing['output_per_1k']
                token_data['estimated_cost_usd'] = input_cost + output_cost

                # Add to running totals
                self.total_tokens['prompt_tokens'] += usage.prompt_token_count
                self.total_tokens['completion_tokens'] += usage.candidates_token_count
                self.total_tokens['total_tokens'] += usage.total_token_count

                result['token_usage'] = token_data

            return result
        except Exception as e:
            # Handle errors...

    def get_usage_summary(self) -> Dict:
        """Return aggregated token usage and costs."""
        total_input_cost = (self.total_tokens['prompt_tokens'] / 1000) * self.pricing['input_per_1k']
        total_output_cost = (self.total_tokens['completion_tokens'] / 1000) * self.pricing['output_per_1k']

        return {
            'total_tokens': self.total_tokens,
            'estimated_cost_usd': total_input_cost + total_output_cost,
            'cost_breakdown': {
                'input_cost': total_input_cost,
                'output_cost': total_output_cost
            }
        }
```

### Web UI Display

**Per-Image Token Display (report.html):**
```html
{% if image.token_usage %}
<div class="token-usage">
    <h4>Token Usage</h4>
    <table>
        <tr>
            <td>Input Tokens:</td>
            <td>{{ image.token_usage.prompt_token_count | number_format }}</td>
        </tr>
        <tr>
            <td>Output Tokens:</td>
            <td>{{ image.token_usage.candidates_token_count | number_format }}</td>
        </tr>
        <tr>
            <td>Total Tokens:</td>
            <td><strong>{{ image.token_usage.total_token_count | number_format }}</strong></td>
        </tr>
        <tr>
            <td>Estimated Cost:</td>
            <td><strong>${{ "%.4f" | format(image.token_usage.estimated_cost_usd) }}</strong></td>
        </tr>
    </table>
</div>
{% endif %}
```

**Aggregate Report Summary:**
```html
<div class="cost-summary">
    <h3>Workflow Cost Summary</h3>
    <div class="stats-grid">
        <div class="stat">
            <label>Total Tokens Used</label>
            <value>{{ total_tokens | number_format }}</value>
        </div>
        <div class="stat">
            <label>Estimated Total Cost</label>
            <value>${{ "%.2f" | format(total_cost) }}</value>
        </div>
        <div class="stat">
            <label>Avg Cost per Image</label>
            <value>${{ "%.4f" | format(avg_cost_per_image) }}</value>
        </div>
    </div>

    <h4>By Agent</h4>
    <table>
        <tr>
            <th>Agent</th>
            <th>Total Tokens</th>
            <th>Cost</th>
            <th>% of Total</th>
        </tr>
        <tr>
            <td>Aesthetic Assessment</td>
            <td>{{ aesthetic_tokens | number_format }}</td>
            <td>${{ "%.2f" | format(aesthetic_cost) }}</td>
            <td>{{ "%.1f" | format(aesthetic_pct) }}%</td>
        </tr>
        <tr>
            <td>Filtering & Categorization</td>
            <td>{{ filtering_tokens | number_format }}</td>
            <td>${{ "%.2f" | format(filtering_cost) }}</td>
            <td>{{ "%.1f" | format(filtering_pct) }}%</td>
        </tr>
        <tr>
            <td>Caption Generation</td>
            <td>{{ caption_tokens | number_format }}</td>
            <td>${{ "%.2f" | format(caption_cost) }}</td>
            <td>{{ "%.1f" | format(caption_pct) }}%</td>
        </tr>
    </table>
</div>
```

### Final Report Schema

```json
{
  "summary": {
    "total_images_processed": 150,
    "images_passed": 87,
    "images_rejected": 63,
    "token_usage": {
      "aesthetic_assessment": {
        "total_tokens": 125000,
        "prompt_tokens": 100000,
        "completion_tokens": 25000,
        "estimated_cost_usd": 0.15
      },
      "filtering_categorization": {
        "total_tokens": 85000,
        "prompt_tokens": 70000,
        "completion_tokens": 15000,
        "estimated_cost_usd": 0.10
      },
      "caption_generation": {
        "total_tokens": 150000,
        "prompt_tokens": 110000,
        "completion_tokens": 40000,
        "estimated_cost_usd": 0.20
      },
      "total": {
        "total_tokens": 360000,
        "estimated_cost_usd": 0.45,
        "cost_per_image": 0.003
      }
    }
  },
  "images": [...]
}
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

| Agent | Model Type | Throughput | Token Usage | Complexity |
|-------|-----------|------------|-------------|------------|
| 1. Metadata Extraction | Library (Pillow + geopy) | ~100 img/min | N/A | O(N) |
| 2. Quality Assessment | OpenCV + Algorithms | ~10 img/min | N/A | O(N) |
| 3. Aesthetic Assessment | Vertex AI (Gemini 1.5 Flash) | ~5 img/min | ~500-1000/img | O(N) Linear, API calls |
| 4. Filtering & Categorization | Vertex AI (Gemini 1.5 Flash) | ~10 img/min | ~300-600/img | O(N) Linear, API + rules |
| 5. Caption Generation | Vertex AI (Gemini 1.5 Flash) | ~10 img/min | ~600-1200/img | O(N) Linear, API calls |

**Total for 150 images: ~8-12 minutes** (with parallelization)
**Total token usage: ~200K-400K tokens** (varies by image complexity)

### Token Optimization Strategies

**Current Implementation:**
- Agents 3, 4, 5 use Vertex AI with token tracking
- Token usage captured per image in `token_usage` field
- Displayed in web UI per-image tabs

**Cost Estimation (Gemini 1.5 Flash pricing as of Dec 2025):**
- Input tokens: $0.000075 per 1K tokens (prompts ≤128K)
- Output tokens: $0.0003 per 1K tokens
- Typical per-image cost: $0.001-0.003

| Batch Size | Token Usage | Est. Cost | Time |
|------------|-------------|-----------|------|
| 50 images | 70K-130K | $0.05-0.15 | 3-5 min |
| 150 images | 200K-400K | $0.15-0.45 | 8-12 min |
| 500 images | 700K-1.3M | $0.50-1.50 | 25-40 min |

**Optimization Techniques:**
1. **Prompt Engineering**: Minimize system prompts, use concise instructions
2. **Batch Processing**: Process multiple images per API call where possible
3. **Conditional Processing**: Skip caption generation for rejected images
4. **Response Format**: Request JSON-only output (no markdown wrapping)
5. **Image Resizing**: Downscale images before API calls (reduces token usage)
6. **Caching**: Cache results for duplicate/similar images

### Implementing Token Optimizations

**1. Conditional Caption Generation (Skip rejected images):**
```python
# In orchestrator.py
def run_workflow(self, image_paths: List[Path]):
    # ... run agents 1-4 ...

    # Filter to only process passed images for captions
    passed_images = [
        img for img in filtering_results
        if img.get('filtering_decision', {}).get('status') == 'pass'
    ]

    passed_paths = [Path(img['filename']) for img in passed_images]

    # Only run caption agent on passed images (saves ~40% tokens)
    if passed_paths:
        caption_results, _ = self.caption_agent.run(passed_paths, filtering_results)
        self.logger.info(f"Generated captions for {len(passed_paths)} passed images")
```

**2. Image Resizing (Reduce token consumption):**
```python
# In utils/image_helpers.py
from PIL import Image

def resize_for_api(image_path: Path, max_dimension: int = 1024) -> bytes:
    """Resize image to max dimension while preserving aspect ratio."""
    img = Image.open(image_path)

    # Only resize if needed
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format=img.format or 'JPEG', quality=85)
    return buffer.getvalue()

# In agent code:
image_bytes = resize_for_api(path, max_dimension=1024)  # Reduces tokens by ~50-70%
```

**3. Optimized System Prompts (Reduce input tokens):**
```python
# BAD: Verbose prompt (uses ~500 tokens)
SYSTEM_PROMPT_VERBOSE = """
You are an expert travel photography curator with years of experience...
Please analyze the following image carefully and provide a comprehensive...
Make sure to consider all aspects including composition, lighting, subject matter...
"""

# GOOD: Concise prompt (uses ~100 tokens)
SYSTEM_PROMPT_CONCISE = """
Analyze this travel photo for aesthetic quality.
Rate (1-5): composition, lighting, color, framing.
Return JSON only."""

# Saves ~400 tokens per image
```

**4. Request JSON-Only Response:**
```python
# In agent prompts, add:
prompt = f"""
{SYSTEM_PROMPT}

Respond with ONLY valid JSON. No markdown, no code blocks, no explanations.

{{
  "overall_score": <1-5>,
  "composition": <1-5>,
  ...
}}
"""

# This prevents the model from wrapping response in ```json``` blocks
# Saves ~10-20 output tokens per image
```

**5. Implement Result Caching:**
```python
# In utils/cache.py
import hashlib
import json
from pathlib import Path

class ResultCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_image_hash(self, image_path: Path) -> str:
        """Generate hash of image content."""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get(self, agent_name: str, image_path: Path) -> Optional[Dict]:
        """Retrieve cached result if exists."""
        img_hash = self.get_image_hash(image_path)
        cache_file = self.cache_dir / f"{agent_name}_{img_hash}.json"

        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None

    def set(self, agent_name: str, image_path: Path, result: Dict):
        """Cache agent result."""
        img_hash = self.get_image_hash(image_path)
        cache_file = self.cache_dir / f"{agent_name}_{img_hash}.json"

        with open(cache_file, 'w') as f:
            json.dump(result, f)

# In agent code:
def process_image(self, path: Path) -> Dict:
    # Check cache first
    cached = self.cache.get(self.agent_name, path)
    if cached:
        self.logger.info(f"Using cached result for {path.name}")
        return cached

    # Process normally
    result = self._call_api(path)

    # Cache result
    self.cache.set(self.agent_name, path, result)
    return result
```

**Expected Token Savings:**

| Optimization | Token Reduction | Cost Savings |
|--------------|-----------------|--------------|
| Skip rejected image captions | 40% fewer caption calls | ~$0.08 per 150 images |
| Image resizing (1024px) | 50-70% per API call | ~$0.15-0.25 per 150 images |
| Concise prompts | 80% fewer input tokens | ~$0.05 per 150 images |
| JSON-only responses | 5-10% fewer output tokens | ~$0.01-0.02 per 150 images |
| Result caching | 100% on duplicates | Varies by duplicate % |

**Combined savings: ~50-60% total cost reduction**
- Original: $0.45 per 150 images
- Optimized: $0.18-0.22 per 150 images

---

## Important Notes

- **Dependencies**: Managed by `uv` and `pyproject.toml`
- **Image Formats**: JPG, PNG, HEIC, RAW (HEIC read directly with pillow-heif)
- **Continue-on-Error**: Default enabled; failed images get placeholder results
- **Logging**: Structured JSON logs in `output/{timestamp}/logs/`
- **Validation**: 3-tier system (agent output, summary, final report)
- **Token Tracking**: Captured for all Vertex AI API calls with per-image and aggregate costs
- **Cost Monitoring**: Real-time tracking with alerts for budget thresholds
- **Reverse Geocoding**: GPS coordinates → location names using Nominatim
- **Filtering Reasoning**: Explains pass/reject decisions based on thresholds

### Token Optimization Checklist

Before running large batches, ensure optimizations are enabled:

- [ ] **Image resizing enabled**: `vertex_ai.optimization.max_image_dimension: 1024`
- [ ] **Skip rejected captions**: `agents.caption_generation.skip_rejected: true`
- [ ] **Caching enabled**: `vertex_ai.optimization.enable_caching: true`
- [ ] **Concise prompts**: Review agent system prompts for brevity
- [ ] **Cost alerts configured**: Set `cost_tracking.alert_threshold_usd` appropriately
- [ ] **Monitor token usage**: Check `output/{timestamp}/reports/token_usage.json`

### Quick Cost Estimation

Before processing, estimate costs:

```bash
# For 100 images with optimizations enabled:
# - Aesthetic: 100 × 500 tokens × $0.000375 = $0.019
# - Filtering: 100 × 400 tokens × $0.000375 = $0.015
# - Captions (60% pass): 60 × 800 tokens × $0.000375 = $0.018
# Total: ~$0.05

# Without optimizations:
# Total: ~$0.30 (6x more expensive)
```

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
