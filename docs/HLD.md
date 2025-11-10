# High-Level Design (HLD)
## Travel Photo Organization System

### System Overview

This is a **production-ready, 7-agent agentic workflow system** for intelligent travel photo organization. The system uses specialized AI agents working in a coordinated pipeline to automatically organize, assess, categorize, and showcase travel photographs.

**Key Statistics:**
- **7 AI Agents** - Each a domain specialist
- **Parallel Execution** - DAG-based workflow with 2 parallel stages
- **Scalable** - Configurable workers and batch sizes
- **Modular** - Each agent independent and testable
- **Observable** - Structured logging and validation

---

## System Architecture

### Agent Pipeline (DAG - Directed Acyclic Graph)

```
┌──────────────────────────────────────────────────────────────┐
│ INPUT: Travel Photos (JPG, PNG, HEIC, RAW, etc.)            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ AGENT 1:               │
        │ Metadata Extraction    │
        │ (EXIF, GPS, Settings)  │
        └────┬─────────────┬─────┘
             │             │
      ┌──────▼─┐    ┌──────▼──────────┐
      │ AGENT 2 │    │ AGENT 3        │  ◄── PARALLEL
      │ Quality │    │ Aesthetic      │
      │ Analysis│    │ Assessment     │
      └──────┬──┘    └──────┬─────────┘
             └───────┬──────┘
                     ▼
        ┌────────────────────────┐
        │ AGENT 4:               │
        │ Duplicate Detection    │
        │ (Similarity Groups)    │
        └────┬─────────────┬─────┘
             │             │
      ┌──────▼─┐    ┌──────▼──────────┐
      │ AGENT 5 │    │ AGENT 6        │  ◄── PARALLEL
      │Filtering│    │ Caption        │
      │ & Class │    │ Generation     │
      └──────┬──┘    └──────┬─────────┘
             └───────┬──────┘
                     ▼
        ┌────────────────────────┐
        │ AGENT 7:               │
        │ Website Generation     │
        │ (React/Material UI)    │
        └────┬─────────────┬─────┘
             │             │
      ┌──────▼──┐   ┌──────▼────────┐
      │ Reports │   │ Website       │
      │ & Logs  │   │ App + Gallery │
      └─────────┘   └───────────────┘
```

### Processing Stages

| Stage | Agents | Type | Duration |
|-------|--------|------|----------|
| **1. Ingestion** | Agent 1 | Sequential | Fast (I/O) |
| **2. Parallel Assessment** | Agents 2, 3 | Parallel | Medium (CPU/VLM) |
| **3. Deduplication** | Agent 4 | Sequential | Medium (Pairwise) |
| **4. Parallel Enrichment** | Agents 5, 6 | Parallel | Medium (VLM/LLM) |
| **5. Presentation** | Agent 7 | Sequential | Fast (Code Gen) |

---

## Data Flow Architecture

### Inter-Agent Communication

Each agent receives upstream data and produces structured output:

```
Agent 1: Metadata Extraction
  └─→ OUTPUT: image_id, filename, EXIF, GPS, camera_settings, flags
      └─→ INPUT to Agents 2, 3, 5, 6

Agent 2: Quality Assessment
  ├─ INPUT: Agent 1 output
  └─→ OUTPUT: quality_score (1-5), sharpness, exposure, noise, metrics
      └─→ INPUT to Agent 4, 5, 6

Agent 3: Aesthetic Assessment
  ├─ INPUT: Agent 1 output
  └─→ OUTPUT: overall_aesthetic (1-5), composition, framing, lighting
      └─→ INPUT to Agent 4, 5, 6

Agent 4: Duplicate Detection
  ├─ INPUT: Agents 2, 3 output
  └─→ OUTPUT: similarity_groups, selected_best_per_group
      └─→ INPUT to Agents 5, 6

Agent 5: Filtering & Categorization
  ├─ INPUT: Agents 1, 2, 3, 4 output
  └─→ OUTPUT: category, subcategories, location, passes_filter, flags
      └─→ INPUT to Agent 7

Agent 6: Caption Generation
  ├─ INPUT: Agents 1, 2, 3, 4, 5 output
  └─→ OUTPUT: captions (concise/standard/detailed), keywords
      └─→ INPUT to Agent 7

Agent 7: Website Generation
  ├─ INPUT: All agents output + configuration
  └─→ OUTPUT: React app, README, data files, documentation
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
    ├─→ paths: input_images, output directories
    ├─→ agents: per-agent settings (workers, model, timeout)
    ├─→ api: OpenAI, Google API credentials and parameters
    ├─→ thresholds: quality/aesthetic minimums
    ├─→ error_handling: retry strategy, continue_on_error
    ├─→ logging: level, format, output paths
    └─→ parallelization: enable_parallel, worker allocation
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
        self.model = self.agent_config.get('model', 'default')
        self.timeout = self.agent_config.get('timeout_seconds', 300)
```

### Environment Variables

```bash
# .env file (NEVER commit to git)
OPENAI_API_KEY=sk-...          # For GPT-4 Vision (Agents 2, 3, 6)
GOOGLE_API_KEY=AIza...         # For Gemini Vision (Agents 3, 5, 6)
```

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
    "timestamp": "2024-11-10T14:30:45Z",
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
| **1. Metadata** | 4 | I/O bound (file reads) | Memory usage |
| **2. Quality** | 2 | CPU bound (image processing) | OpenCV overhead |
| **3. Aesthetic** | 2 | API rate limited | VLM API quotas |
| **4. Duplicates** | 1 | Pairwise comparisons | Quadratic complexity |
| **5. Filtering** | 2 | Balanced | VLM API quotas |
| **6. Captions** | 2 | API rate limited | LLM API quotas |

### Parallel Execution Groups

```
Group 1 (Sequential dependency):
  Agent 1 → Sequential execution

Group 2 (Parallel):
  Agent 2 ┐
          ├─→ Run concurrently (both depend on Agent 1)
  Agent 3 ┘

Group 3 (Sequential dependency):
  Agent 4 → Sequential execution (depends on Agents 2, 3)

Group 4 (Parallel):
  Agent 5 ┐
          ├─→ Run concurrently (both depend on Agent 4)
  Agent 6 ┘

Group 5 (Sequential dependency):
  Agent 7 → Sequential execution (depends on all)
```

---

## Output Structure

### Directory Organization

```
output/
├── reports/
│   ├── {agent_name}_output.json      # List[Dict] - one per image
│   ├── validations.json              # Array of validation summaries
│   └── final_report.json             # Aggregated statistics
├── logs/
│   ├── workflow.log                  # Structured JSON logs
│   └── errors.json                   # All errors with timestamps
├── metadata/                          # Optional EXIF cache
└── website/                           # Complete React application
    ├── package.json
    ├── README.md
    ├── FEATURES.md
    ├── src/
    ├── public/
    │   └── data/
    │       └── photos.json            # Website data payload
    └── node_modules/
```

### Report Schemas

**Agent Output**
```json
{
  "image_id": "string",
  "filename": "string",
  // Agent-specific fields
}
```

**Validation Summary**
```json
{
  "agent": "Agent Name",
  "stage": "processing_stage",
  "status": "success|warning|error",
  "summary": "Processed X/Y images successfully",
  "issues": ["list", "of", "issues"]
}
```

**Final Report**
```json
{
  "num_images_ingested": 150,
  "average_technical_score": 3.8,
  "average_aesthetic_score": 3.5,
  "num_duplicates_found": 12,
  "num_images_final_selected": 138,
  "category_distribution": {...},
  "quality_distribution": {...},
  "agent_performance": [...],
  "timestamp": "ISO 8601"
}
```

---

## Performance Characteristics

### Time Complexity by Agent

| Agent | Time Complexity | Notes |
|-------|-----------------|-------|
| **1. Metadata** | O(N) | Linear in image count, I/O bound |
| **2. Quality** | O(N) | Linear, CPU intensive |
| **3. Aesthetic** | O(N) | Linear, VLM API calls |
| **4. Duplicates** | O(N²) | Pairwise comparisons (mitigated by clustering) |
| **5. Filtering** | O(N) | Linear classification |
| **6. Captions** | O(N) | Linear, LLM API calls |
| **7. Website** | O(N) | Linear code generation |

### Resource Constraints

- **Memory**: ~100MB per parallel worker (image in memory)
- **CPU**: Agents 2, 4 are CPU-intensive
- **Network**: Agents 3, 5, 6 require API access
- **Storage**: ~10x input size for outputs and cache

---

## Extension Points

### Adding New Agents

1. Create agent class in `agents/new_agent.py`
2. Register in orchestrator
3. Add to workflow execution pipeline
4. Define validation schema
5. Configure in config.yaml

### Customizing Configuration

- Adjust `parallel_workers` per agent based on resources
- Tune `min_technical_quality` and `min_aesthetic_quality` thresholds
- Switch models between OpenAI, Google, Claude
- Enable/disable agents via `enabled: true/false`

### Implementing VLM Integration

- Check for API key: `os.getenv('OPENAI_API_KEY')`
- Implement `_call_vlm_api()` method
- Handle rate limiting with `batch_size` config
- Parse response and validate output schema

---

## Key Metrics & Monitoring

### Success Criteria

- ✅ All images processed without crashes
- ✅ Agent success rates > 95%
- ✅ Validation schemas all pass
- ✅ Output files contain expected data

### Performance Targets

- **Metadata**: ~100 images/minute (I/O bound)
- **Quality**: ~10 images/minute per worker
- **Aesthetic**: ~5 images/minute per worker (API limited)
- **Captions**: ~10 images/minute per worker (API limited)

### Observability

- Structured JSON logs in `output/logs/workflow.log`
- Error registry in `output/logs/errors.json`
- Real-time monitoring via `tail -f output/logs/workflow.log`
- Final report summarizes all statistics

---

**For detailed implementations, see [LLD.md](./LLD.md)**
**For architecture diagrams, see [UML_DIAGRAMS.md](./UML_DIAGRAMS.md)**
**For workflow visualization, see [ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)**
**For quick setup, see [QUICKSTART.md](./QUICKSTART.md)**
