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

**7-agent agentic workflow** for intelligent travel photo organization:

```
Agent 1: Metadata      → Agent 2: Quality   ─┐
  (EXIF, GPS)         & Agent 3: Aesthetic ─→ Agent 4: Duplicates
                                            ├→ Agent 5: Filtering
                                            └→ Agent 6: Captions
                                                  ↓
                                          Agent 7: Website
```

- **Input**: Travel photos (JPG, PNG, HEIC, RAW)
- **Output**: Organized website gallery + analytics
- **Parallelization**: 2 stages run concurrently
- **Models**: EXIF parsing, Vision APIs, LLMs for captions

---

## Quick Commands

```bash
# Setup (uv recommended)
uv sync
cp .env.example .env

# Run workflow
uv run python orchestrator.py

# View results
cat output/reports/final_report.json | jq .

# Monitor logs
tail -f output/logs/workflow.log

# Launch website
cd output/website && npm run dev
```

**Full setup guide**: See [QUICKSTART.md](./docs/QUICKSTART.md)

---

## 🎯 What Claude Should Focus On

### When Adding Features
1. Check **[LLD.md](./docs/LLD.md)** for agent specs and schemas
2. Follow agent template in `agents/base_agent.py`
3. Add validation schema to `utils/validation.py`
4. Update `config.yaml` with new settings
5. Register in `orchestrator.py`

### When Debugging
1. Check **[ACTIVITY_DIAGRAM.md](./docs/ACTIVITY_DIAGRAM.md)** for execution flow
2. Review error logs: `cat output/logs/errors.json | jq .`
3. Use agent testing code from **[QUICKSTART.md](./docs/QUICKSTART.md)**

### When Understanding Architecture
1. Start with **[HLD.md](./docs/HLD.md)** for overview
2. Review **[UML_DIAGRAMS.md](./docs/UML_DIAGRAMS.md)** for visual structure
3. Deep dive into **[LLD.md](./docs/LLD.md)** for implementation details

---

## Key Architectural Patterns

### Agent Template
```python
class AgentName:
    SYSTEM_PROMPT = """..."""

    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.agent_config = config['agents']['agent_key']
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)

    def run(self, image_paths: List[Path], *upstream) -> Tuple[List[Dict], Dict]:
        """Return (output_list, validation_dict)."""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = [executor.submit(self.process_image, path) for path in image_paths]
            results = [f.result() for f in as_completed(futures)]
        return results, validation_summary

    def process_image(self, path: Path) -> Dict:
        try:
            result = {...}
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

---

## Configuration

**Key sections in config.yaml:**

```yaml
paths:
  input_images: sample_images/
  output_dir: output/

agents:
  metadata_extraction:
    parallel_workers: 4        # I/O bound
  quality_assessment:
    parallel_workers: 2        # CPU bound
  aesthetic_assessment:
    parallel_workers: 2        # API rate limited
    model: "claude-3.5-sonnet"
  # ... etc

thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

error_handling:
  continue_on_error: true
```

**Environment variables (.env):**

```
OPENAI_API_KEY=sk-...          # For GPT-4 Vision agents
GOOGLE_API_KEY=AIza...         # For Gemini agents
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
├── orchestrator.py            # Main workflow
├── agents/                    # 7 agents
├── utils/                     # Logger, validation, helpers
├── sample_images/             # Input photos
└── output/                    # Generated outputs
    ├── reports/              # Agent outputs + final report
    ├── logs/                 # Workflow logs + errors
    └── website/              # React app
```

---

## VLM/LLM Integration

Agents 3, 5, 6 support Vision/Language models:

```python
# Check for API key
if os.getenv('OPENAI_API_KEY'):
    # Use OpenAI GPT-4 Vision
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Check for Google API key
if os.getenv('GOOGLE_API_KEY'):
    # Use Google Gemini
    import google.generativeai as genai
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
```

---

## Performance Targets

| Agent | Model Type | Throughput |
|-------|-----------|-----------|
| 1. Metadata | Library | ~100 img/min |
| 2. Quality | ML Model | ~10 img/min |
| 3. Aesthetic | VLM API | ~5 img/min |
| 4. Duplicates | Hash + Embed | ~1 min/150 img |
| 5. Filtering | VLM API | ~10 img/min |
| 6. Captions | LLM API | ~10 img/min |

**Total for 150 images: ~14 minutes** (with parallelization)

---

## Important Notes

- **Dependencies**: Managed by `uv` and `pyproject.toml`
- **Image Formats**: JPG, PNG, HEIC, RAW, CR2, NEF, ARW
- **Continue-on-Error**: Default enabled; failed images get placeholder results
- **Logging**: Structured JSON logs in `output/logs/`
- **Validation**: 3-tier system (agent output, summary, final report)

---

**For complete details, see the documentation directory `docs/`**
