# High-Level Design (HLD)
## Travel Photo Organization System

### System Overview

This is a **production-ready, 5-agent agentic workflow system** with **multiple deployment options** for intelligent travel photo organization. The system uses specialized AI agents powered by Vertex AI working in a coordinated pipeline to automatically organize, assess, categorize, and enhance travel photographs.

**Key Statistics:**
- **5 AI Agents** - Each a domain specialist
- **Parallel Execution** - ThreadPoolExecutor-based concurrent processing
- **Scalable** - Configurable workers and batch sizes
- **Modular** - Each agent independent and testable
- **Observable** - Structured logging, validation, and token tracking
- **Multiple Interfaces** - Docker, FastAPI, Flask Web UI, CLI, Batch CSV, MCP Server
- **Production Ready** - Containerized deployment with health checks and auto-restart

**Deployment Options:**
1. **Docker Compose** - Production containerized deployment (Recommended)
2. **FastAPI Server** - RESTful API for web/mobile apps
3. **Flask Web UI** - Interactive interface for manual uploads
4. **CLI Orchestrator** - Command-line workflow execution
5. **Batch CSV Tool** - Process folders and export to spreadsheet
6. **MCP Server** - Claude Desktop integration via Model Context Protocol

---

## System Architecture

### Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │ Docker       │  │ FastAPI      │  │ Flask Web UI │  │ Batch CSV   ││
│  │ Compose      │  │ REST Server  │  │ (Port 5001)  │  │ Processor   ││
│  │ (Port 8000)  │  │ (Port 8000)  │  │ Calls API    │  │ Calls API   ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘│
│         │                  │                  │                  │       │
│         └─────────────────┬┴──────────────────┴──────────────────┘       │
│                           │                                              │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │ HTTP/REST API or Direct Invocation
                            ▼
              ┌─────────────────────────────┐
              │ ORCHESTRATOR / API HANDLER  │
              │  - Request routing          │
              │  - Agent coordination       │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │ AGENT 1:                 │
              │ Metadata Extraction      │
              │ + Reverse Geocoding      │
              │   (Nominatim/OSM)        │
              └────┬─────────────┬───────┘
                   │             │
            ┌──────▼──┐    ┌─────▼──────────┐
            │ AGENT 2 │    │ AGENT 3        │  ◄── PARALLEL
            │ Quality │    │ Aesthetic      │      (ThreadPoolExecutor)
            │ OpenCV  │    │ Vertex AI      │      + Token Tracking
            └──────┬──┘    └──────┬─────────┘
                   └────────┬──────┘
                            │
            ┌───────────────┴─────────────┐
            │ AGENT 4: Filtering &        │  ◄── Sequential
            │ Categorization              │      + Reasoning
            │ (Vertex AI + Rules)         │      + Token Tracking
            └───────────────┬─────────────┘
                            │
            ┌───────────────▼─────────────┐
            │ AGENT 5: Caption Generation │  ◄── Token Tracking
            │ (Vertex AI)                 │
            └───────────────┬─────────────┘
                            │
                            ▼
              ┌────────────────────────┐
              │ OUTPUTS:               │
              │ - JSON Reports         │
              │ - CSV Export           │
              │ - Logs + Token Usage   │
              │ - Web UI Display       │
              │ - API Response         │
              └────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐         │
│  │ Web Report   │  │ API JSON     │  │ CSV Export    │         │
│  │ View         │  │ Response     │  │ (Spreadsheet) │         │
│  │ - Gallery    │  │ - Structured │  │ - Flat table  │         │
│  │ - Tabbed UI  │  │ - REST       │  │ - Bulk data   │         │
│  │ - Token viz  │  │ - Programm.  │  │ - Analysis    │         │
│  └──────────────┘  └──────────────┘  └───────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Processing Stages

| Stage | Agents | Type | Duration | Token Usage |
|-------|--------|------|----------|-------------|
| **1. Ingestion** | Agent 1 | Sequential | Fast (I/O) | None |
| **2. Parallel Assessment** | Agents 2, 3 | Parallel | Medium (CPU/VLM) | ~500-1000/img |
| **3. Filtering** | Agent 4 | Sequential | Medium (VLM) | ~300-600/img |
| **4. Captions** | Agent 5 | Sequential | Medium (VLM) | ~600-1200/img |

---

## Deployment Architectures

### 1. Docker Compose Deployment (Production)

**Components:**
- **API Container** (photo-api) - FastAPI server on port 8000
- **MCP Container** (photo-mcp) - MCP server for Claude Desktop
- **Shared Volumes** - keys.json, config.yaml, output, cache

**Architecture:**
```
┌─────────────────────────────────────┐
│ Docker Compose Environment          │
│                                      │
│  ┌────────────────┐  ┌────────────┐│
│  │ photo-api      │  │ photo-mcp  ││
│  │ Port: 8000     │  │ stdio      ││
│  │ Health checks  │  │ interactive││
│  │ Auto-restart   │  │            ││
│  └────────────────┘  └────────────┘│
│         │                    │      │
│         └────────┬───────────┘      │
│                  │                  │
│  ┌──────────────▼──────────────┐   │
│  │ Shared Volumes:             │   │
│  │ - keys.json (credentials)   │   │
│  │ - config.yaml (config)      │   │
│  │ - output/ (results)         │   │
│  │ - cache/ (geocoding)        │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Benefits:**
- ✅ Production-ready containerization
- ✅ Automatic health checks
- ✅ Auto-restart on failure
- ✅ Isolated environment
- ✅ Easy scaling and deployment

**Usage:**
```bash
docker compose up --build      # Start all services
docker compose up api          # Start only API
docker compose logs -f api     # View logs
docker compose down            # Stop all services
```

### 2. FastAPI Server Deployment

**Architecture:**
```
┌─────────────────────────────────────┐
│ Client Applications                 │
│ (Web, Mobile, Scripts, Batch tool)  │
└──────────────┬──────────────────────┘
               │ HTTP REST API
               ▼
┌─────────────────────────────────────┐
│ FastAPI Server (Port 8000)          │
│                                      │
│ Endpoints:                           │
│  /health - Health check              │
│  /analyze - Full pipeline            │
│  /analyze/metadata - Agent 1         │
│  /analyze/quality - Agent 2          │
│  /analyze/aesthetic - Agent 3        │
│  /analyze/filter - Agent 4           │
│  /analyze/caption - Agent 5          │
│  /docs - Swagger UI                  │
│  /redoc - ReDoc                      │
│                                      │
│ Features:                            │
│  - API key authentication            │
│  - CORS enabled                      │
│  - Auto-generated docs               │
│  - Async request handling            │
│  - Background jobs                   │
└─────────────────────────────────────┘
```

**Benefits:**
- 🚀 RESTful API for programmatic access
- 📚 Auto-generated documentation
- 🔑 Secure API key authentication
- 🧪 Easy testing via Swagger UI
- 🔄 Background job processing

**Usage:**
```bash
./scripts/setup_api.sh         # Setup
./scripts/start_api.sh         # Start server
./scripts/test_api_server.sh   # Test endpoints
curl http://localhost:8000/health
```

### 3. Flask Web UI Deployment

**Architecture:**
```
┌─────────────────────────────────────┐
│ Browser (User Interface)            │
└──────────────┬──────────────────────┘
               │ HTTP
               ▼
┌─────────────────────────────────────┐
│ Flask Web Server (Port 5001)        │
│                                      │
│ Routes:                              │
│  / - Dashboard + Upload              │
│  /upload - Handle uploads            │
│  /report/<id> - View results         │
│  /status/<id> - Poll status          │
│                                      │
└──────────────┬──────────────────────┘
               │ Calls FastAPI
               ▼
┌─────────────────────────────────────┐
│ FastAPI Server (Port 8000)          │
└─────────────────────────────────────┘
```

**Benefits:**
- 📤 Drag-and-drop file upload
- 📊 Interactive tabbed reports
- 📈 Real-time progress tracking
- 🎨 Clean SaaS UI design
- 🔢 Token usage visualization

**Usage:**
```bash
./scripts/start_api.sh         # Start API first
uv run python web_app/app.py   # Start web UI
# Visit http://localhost:5001
```

### 4. CLI Orchestrator Deployment

**Architecture:**
```
┌─────────────────────────────────────┐
│ Command Line Interface              │
└──────────────┬──────────────────────┘
               │ Direct Invocation
               ▼
┌─────────────────────────────────────┐
│ Orchestrator (orchestrator.py)      │
│  - Loads config.yaml                │
│  - Initializes all 5 agents         │
│  - Runs sequential pipeline         │
│  - Saves JSON reports               │
└─────────────────────────────────────┘
```

**Benefits:**
- 🖥️ Direct local execution
- 📁 Batch processing from folder
- 📝 Detailed JSON output
- 🔍 Full control over config

**Usage:**
```bash
uv run python orchestrator.py
# Results in output/{timestamp}/reports/
```

### 5. Batch CSV Tool Deployment

**Architecture:**
```
┌─────────────────────────────────────┐
│ Batch Script (main.py)              │
│  - Scans folder for images          │
│  - Calls FastAPI for each image     │
│  - Collects results                 │
│  - Exports to CSV                   │
└──────────────┬──────────────────────┘
               │ HTTP REST API
               ▼
┌─────────────────────────────────────┐
│ FastAPI Server (Port 8000)          │
└─────────────────────────────────────┘
```

**Benefits:**
- 📊 CSV export for spreadsheets
- 🔄 Recursive folder scanning
- 📈 Progress tracking
- ⚠️ Error logging to separate CSV

**Usage:**
```bash
cd batch-run-photo-json2csv
python main.py /path/to/images output.csv --api-key KEY --recursive
```

### 6. MCP Server Deployment

**Architecture:**
```
┌─────────────────────────────────────┐
│ Claude Desktop Application          │
└──────────────┬──────────────────────┘
               │ MCP Protocol (stdio)
               ▼
┌─────────────────────────────────────┐
│ MCP Server (photo_analysis_server)  │
│  - Exposes agents as MCP tools      │
│  - JSON-RPC communication           │
│  - Direct agent invocation          │
└─────────────────────────────────────┘
```

**Benefits:**
- 🤖 Native Claude Desktop integration
- 💬 Conversational interface
- 🔧 No HTTP overhead
- 🎯 Context-aware analysis

**Usage:**
```bash
./scripts/setup_mcp.sh              # Setup
./scripts/setup_claude_mcp.sh       # Configure Claude Desktop
# Restart Claude Desktop
# Use: "Analyze this photo: /path/to/image.jpg"
```

---

## Data Flow Architecture

### Inter-Agent Communication

Each agent receives upstream data and produces structured output:

```
Agent 1: Metadata Extraction
  └─→ OUTPUT: image_id, filename, EXIF, GPS (with reverse geocoded location), 
              camera_settings, dimensions, flags
      └─→ INPUT to Agents 2, 3, 4, 5

Agent 2: Quality Assessment (OpenCV)
  ├─ INPUT: Agent 1 output
  └─→ OUTPUT: quality_score (1-5), sharpness, exposure, noise, resolution, 
              issues, metrics
      └─→ INPUT to Agents 4, 5

Agent 3: Aesthetic Assessment (Vertex AI)
  ├─ INPUT: Agent 1 output
  └─→ OUTPUT: overall_aesthetic (1-5), composition, framing, lighting, 
              subject_interest, notes, token_usage
      └─→ INPUT to Agents 4, 5

Agent 4: Filtering & Categorization (Vertex AI + Rules)
  ├─ INPUT: Agents 1, 2, 3 output
  └─→ OUTPUT: category, subcategories, time_category, location, 
              passes_filter, reasoning, flags, token_usage
      └─→ INPUT to Agent 5

Agent 5: Caption Generation (Vertex AI)
  ├─ INPUT: Agents 1, 2, 3, 4 output (full context)
  └─→ OUTPUT: captions (concise/standard/detailed), keywords, token_usage
```

### Data Structure Pattern

All inter-agent data flows as **list of dictionaries**:

```python
# Generic flow
output = [
    {
        "image_id": "img_001",
        "filename": "vacation_photo.jpg",
        # Agent-specific fields
        "quality_score": 4,
        "aesthetic_score": 5,
        "category": "Landscape",
        "token_usage": {  # For VLM agents
            "prompt_token_count": 245,
            "candidates_token_count": 156,
            "total_token_count": 401
        },
        # ... etc
    },
    # ... one dict per image
]
```

---

## Configuration System

### Configuration Hierarchy

```
config.yaml (root configuration)
    │
    ├─→ paths: input_images, output directories, upload directories, cache
    ├─→ vertex_ai: project, location, model settings, pricing, optimization
    ├─→ reverse_geocoding: enabled, caching, timeout, user_agent
    ├─→ agents: per-agent settings (workers, batch_size, timeout)
    ├─→ thresholds: quality/aesthetic minimums
    ├─→ error_handling: retry strategy, continue_on_error
    ├─→ logging: level, format, output paths
    ├─→ api: host, port, reload settings
    └─→ parallelization: worker allocation per agent
```

### Vertex AI Configuration (Required)

```yaml
vertex_ai:
  project: "your-google-cloud-project-id"
  location: "us-central1"  # or your preferred region
  model: "gemini-1.5-flash"

  # Token optimization settings
  pricing:
    input_per_1k_tokens: 0.000075   # $0.075 per 1M input tokens
    output_per_1k_tokens: 0.0003    # $0.30 per 1M output tokens

  optimization:
    enable_caching: true            # Cache API results
    max_image_dimension: 1024       # Resize images (reduces tokens)
    skip_captions_for_rejected: true # Don't caption rejected images
    use_concise_prompts: true       # Minimize prompt length
```

### Reverse Geocoding Configuration

```yaml
reverse_geocoding:
  enabled: true                     # Enable GPS → location name lookup
  cache_enabled: true               # Cache results locally
  cache_ttl_hours: 24              # Cache validity period
  timeout_seconds: 5               # Request timeout
  user_agent: "TravelPhotoAnalysis/1.0"  # Required by Nominatim
```

**Features:**
- Uses OpenStreetMap's Nominatim service (free!)
- Converts GPS coordinates to human-readable location names
- Automatic caching to minimize API calls (stored in `cache/geocoding_cache.json`)
- Rate limiting (max 1 request/second) to respect Nominatim TOS
- Falls back gracefully if service unavailable

### API Configuration

```yaml
api:
  host: "0.0.0.0"                  # Bind address
  port: 8000                       # Port for FastAPI server
  reload: true                     # Auto-reload on code changes (dev only)
```

### Agent-Specific Configuration

Each agent extracts its config section:

```python
# Pattern used by all agents
class MyAgent:
    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.agent_config = config['agents']['agent_key']
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        
        # Vertex AI client initialization (for VLM agents)
        vertex_config = config.get('vertex_ai', {})
        self.client = genai.Client(
            vertexai=True,
            project=vertex_config.get('project'),
            location=vertex_config.get('location')
        )
        self.model_name = vertex_config.get('model', 'gemini-1.5-flash')
```

### Authentication

**Vertex AI uses Application Default Credentials (ADC):**

```bash
# Set up ADC
gcloud auth application-default login

# Or use service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

---

## Web Application Architecture

### Flask Application (`web_app/app.py`)

**Architecture Change:** Flask web app now acts as a frontend that calls the FastAPI server instead of running agents directly.

```python
# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "your-api-key")

# Key routes
@app.route('/')
def index():
    """Dashboard with upload and run history."""
    runs = get_all_workflow_runs()
    return render_template('index.html', runs=runs)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle photo upload and call FastAPI for analysis."""
    files = request.files.getlist('photos')

    # Save uploaded files
    upload_dir = save_uploads(files)

    # Process images by calling FastAPI
    threading.Thread(
        target=run_workflow_thread,
        args=(upload_dir,)
    ).start()

    return jsonify({'run_id': run_id, 'status': 'running'})

def run_workflow_thread(input_path):
    """Call FastAPI server for each image."""
    for image_file in image_files:
        # Call FastAPI /analyze endpoint
        response = requests.post(
            f"{API_URL}/analyze",
            files={'file': open(image_file, 'rb')},
            headers={'X-API-Key': API_KEY}
        )
        results.append(response.json())

    # Save results to output directory
    save_results(results)

@app.route('/report/<timestamp>')
def view_report(timestamp):
    """Load and display detailed report."""
    images_data = load_all_agent_outputs(timestamp)
    return render_template('report.html', images=images_data)

@app.route('/status/<run_id>')
def check_status(run_id):
    """Poll workflow status."""
    return jsonify({'status': get_run_status(run_id)})
```

**Benefits of API-based architecture:**
- 🔄 Separation of concerns (UI vs. processing)
- 🚀 Can scale API and UI independently
- 🔌 Multiple UIs can share same API backend
- 🧪 Easier testing and development
- 📊 API can serve web UI, batch tool, and other clients

### UI Templates

**base.html:**
- Clean SaaS design system
- Inter font family
- CSS variables for theming
- Responsive layout
- Modern color palette

**index.html:**
- Drag-and-drop upload zone
- Run history with timestamps
- Status badges (Running/Completed/Failed)
- JavaScript polling for active runs

**report.html:**
- Stats overview (total, passed, average scores)
- Image grid (responsive masonry)
- Per-image tabbed interface:
  - **Metadata Tab**: Date, camera, GPS location (reverse geocoded), dimensions
  - **Quality Tab**: Overall + component scores, issues list
  - **Aesthetic Tab**: Scores + AI analysis notes
  - **Filtering Tab**: Category, pass/reject status, reasoning
  - **Caption Tab**: Multiple caption levels, keywords
- Token usage display per agent

---

## Validation Framework

### Three-Tier Validation

**Tier 1: Agent Output Schema**
- Each agent output validated against JSON schema
- Enforced by `validate_agent_output()` function
- Ensures data consistency between agents

**Tier 2: Validation Summary**
- Every agent returns validation dict with status (success/warning/error)
- Includes summary and list of issues encountered
- Aggregated in workflow logs

**Tier 3: Final Report Validation**
- Orchestrator validates complete workflow output
- Checks statistical consistency and completeness
- Generates comprehensive final_report.json

---

## Error Handling Strategy

### Structured Error Logging

```python
# All errors logged as JSON objects
{
    "timestamp": "2024-11-23T02:30:45Z",
    "agent": "Aesthetic Assessment",
    "error_type": "APIError|ProcessingError|ValidationError",
    "summary": "Human-readable description",
    "severity": "info|warning|error|critical",
    "details": {...}
}
```

### Severity Levels

| Level | Behavior | Recovery |
|-------|----------|----------|
| **info** | Informational | No action needed |
| **warning** | Potential issue | Agent continues |
| **error** | Single image fails | Agent skips image, continues |
| **critical** | Agent/workflow fails | Execution halts |

### Continue-on-Error Pattern

- Controlled by `config.yaml` → `error_handling.continue_on_error: true`
- If agent throws exception: log error, assign placeholder result, continue
- Failed images tagged with error flags for review
- Downstream agents handle missing/placeholder data gracefully

---

## Parallelization Strategy

### Agent Worker Allocation

| Agent | Workers | Reason | Constraint |
|-------|---------|--------|-----------|
| **1. Metadata** | 4 | I/O bound (file reads + geocoding) | Memory usage |
| **2. Quality** | 2 | CPU bound (OpenCV processing) | CPU overhead |
| **3. Aesthetic** | 2 | API rate limited | Vertex AI quotas |
| **4. Filtering** | 2 | Balanced | Vertex AI quotas |
| **5. Captions** | 2 | API rate limited | Vertex AI quotas |

### Execution Pattern

**Within Each Agent:**
```python
with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
    futures = [executor.submit(self.process_image, path) 
               for path in image_paths]
    results = [f.result() for f in as_completed(futures)]
```

**Workflow Level:**
```
Sequential: Agent 1
Parallel:   Agents 2 & 3 (both depend on Agent 1)
Sequential: Agent 4 (depends on 1, 2, 3)
Sequential: Agent 5 (depends on 1, 2, 3, 4)
```

---

## Output Structure

### Directory Organization

```
output/
└── YYYYMMDD_HHMMSS/              # Timestamped run
    ├── reports/
    │   ├── metadata_extraction_output.json
    │   ├── quality_assessment_output.json
    │   ├── aesthetic_assessment_output.json
    │   ├── filtering_categorization_output.json
    │   ├── caption_generation_output.json
    │   ├── validations.json
    │   └── final_report.json
    ├── logs/
    │   ├── workflow.log
    │   └── errors.json
    └── processed_images/           # Uploaded images
```

### Report Schemas

**Agent Output (with token usage):**
```json
{
  "image_id": "string",
  "filename": "string",
  // Agent-specific fields
  "token_usage": {  // For VLM agents only
    "prompt_token_count": 245,
    "candidates_token_count": 156,
    "total_token_count": 401
  }
}
```

**Final Report:**
```json
{
  "num_images_ingested": 150,
  "average_technical_score": 3.8,
  "average_aesthetic_score": 3.5,
  "num_images_final_selected": 138,
  "num_images_flagged_for_manual_review": 10,
  "category_distribution": {...},
  "quality_distribution": {...},
  "total_tokens_used": 185430,
  "agent_performance": [...],
  "timestamp": "ISO 8601"
}
```

---

## Performance Characteristics

### Time Complexity by Agent

| Agent | Time Complexity | Notes |
|-------|-----------------|-------|
| **1. Metadata** | O(N) | Linear in image count, I/O + geocoding API |
| **2. Quality** | O(N) | Linear, CPU intensive (OpenCV) |
| **3. Aesthetic** | O(N) | Linear, Vertex AI API calls |
| **4. Filtering** | O(N) | Linear, Vertex AI + rule evaluation |
| **5. Captions** | O(N) | Linear, Vertex AI API calls |

### Resource Constraints

- **Memory**: ~100MB per parallel worker (image in memory)
- **CPU**: Agent 2 is CPU-intensive (OpenCV)
- **Network**: Agents 3, 4, 5 require Vertex AI API access
- **Storage**: ~10x input size for outputs and cache
- **API Quotas**: Vertex AI rate limits apply

### Performance Targets

- **Metadata**: ~100 images/minute (I/O + geocoding)
- **Quality**: ~10 images/minute per worker
- **Aesthetic**: ~5 images/minute per worker (API limited)
- **Filtering**: ~10 images/minute per worker (API limited)
- **Captions**: ~10 images/minute per worker (API limited)

**Total for 150 images: ~8-12 minutes** (with parallelization)
**Total token usage: ~200K-400K tokens** (varies by complexity)

---

## Key Features

### Token Usage Tracking

All Vertex AI API calls capture token usage:
```python
if hasattr(response, 'usage_metadata'):
    result['token_usage'] = {
        'prompt_token_count': response.usage_metadata.prompt_token_count,
        'candidates_token_count': response.usage_metadata.candidates_token_count,
        'total_token_count': response.usage_metadata.total_token_count
    }
```

Displayed in:
- Web UI (per-image tabs)
- JSON output files
- Final report summary

### Reverse Geocoding

GPS coordinates automatically converted to location names:
```python
# Uses Nominatim (geopy)
location = self.geolocator.reverse(
    (latitude, longitude), 
    exactly_one=True, 
    language='en'
)
# Returns: "Church of the Holy Spirit, Fischmarkt, Altstadt, Heidelberg..."
```

### Filtering Reasoning

Explains why images pass or fail:
```python
if passes_filter:
    reasoning = f"Passed. Quality: {quality}/{min_quality}, Aesthetic: {aesthetic}/{min_aesthetic}"
else:
    reasons = []
    if quality < min_quality:
        reasons.append(f"Quality ({quality}) below threshold ({min_quality})")
    if aesthetic < min_aesthetic:
        reasons.append(f"Aesthetic ({aesthetic}) below threshold ({min_aesthetic})")
    reasoning = f"Rejected: {'; '.join(reasons)}"
```

---

## Extension Points

### Adding New Agents

1. Create agent class in `agents/new_agent.py`
2. Follow agent template pattern with Vertex AI client
3. Register in orchestrator
4. Add validation schema to `utils/validation.py`
5. Configure in `config.yaml`
6. Update web UI templates if needed

### Customizing Configuration

- Adjust `parallel_workers` per agent based on resources
- Tune `min_technical_quality` and `min_aesthetic_quality` thresholds
- Change Vertex AI model (e.g., `gemini-1.5-pro` for higher quality)
- Enable/disable agents via `enabled: true/false`
- Adjust batch sizes for API rate limiting

---

## Key Metrics & Monitoring

### Success Criteria

- ✅ All images processed without crashes
- ✅ Agent success rates > 95%
- ✅ Validation schemas all pass
- ✅ Output files contain expected data
- ✅ Token usage within budget

### Observability

- Structured JSON logs in `output/{timestamp}/logs/workflow.log`
- Error registry in `output/{timestamp}/logs/errors.json`
- Real-time monitoring via web UI status polling
- Token usage tracking per agent
- Final report summarizes all statistics

### Web Application Monitoring

- Flask debug logs in terminal
- Browser console for frontend issues
- Network tab for API calls
- Status polling for workflow progress

---

**For detailed implementations, see [LLD.md](./LLD.md)**
**For architecture diagrams, see [UML_DIAGRAMS.md](./UML_DIAGRAMS.md)**
**For workflow visualization, see [ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)**
**For quick setup, see [QUICKSTART.md](./QUICKSTART.md)**
