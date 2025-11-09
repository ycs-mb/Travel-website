# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Architecture

This is a **7-agent agentic workflow system** for intelligent travel photo organization. Each agent is a domain specialist that processes images in a coordinated pipeline.

### Agent Pipeline (DAG Structure)

```
Metadata Extraction (Agent 1)
    ├─→ Quality Assessment (Agent 2) ────┐
    └─→ Aesthetic Assessment (Agent 3) ──┴─→ Duplicate Detection (Agent 4)
                                              ├─→ Filtering/Categorization (Agent 5)
                                              └─→ Caption Generation (Agent 6)
                                                   └─→ Website Generation (Agent 7)
```

**Parallel Stages:**
- Agents 2 & 3 can run concurrently (both depend only on Agent 1)
- Agents 5 & 6 can run concurrently (both depend on Agents 2, 3, 4)

### Data Flow Between Agents

Each agent produces a list of dictionaries (one per image) that flows to downstream agents:
- **Agent 1** → image_id, filename, EXIF, GPS, camera_settings, flags
- **Agent 2** → quality_score (1-5), sharpness, exposure, noise, issues
- **Agent 3** → overall_aesthetic (1-5), composition, framing, lighting
- **Agent 4** → similarity groups with selected_best image per group
- **Agent 5** → category, subcategories, passes_filter, flags
- **Agent 6** → captions (concise/standard/detailed), keywords
- **Agent 7** → website files, README, sample data JSON

## Common Commands

### Run the Complete Workflow
```bash
python orchestrator.py
```

### View Final Report
```bash
cat output/reports/final_report.json | jq .
```

### Monitor Logs (Real-time)
```bash
tail -f output/logs/workflow.log
```

### Check Error Log
```bash
cat output/logs/errors.json | jq .
```

### View Individual Agent Outputs
```bash
ls output/reports/
cat output/reports/quality_assessment_output.json | jq .
```

### Test Single Agent (Python REPL)
```python
from agents.metadata_extraction import MetadataExtractionAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()
agent = MetadataExtractionAgent(config, logger)

image_paths = [Path("sample_images/test.jpg")]
metadata_list, validation = agent.run(image_paths)
print(validation)
```

### Generate Website Only
```python
from agents.website_generation import WebsiteGenerationAgent
from utils.helpers import load_config, load_json
from utils.logger import setup_logger

config = load_config("config.yaml")
logger = setup_logger()
agent = WebsiteGenerationAgent(config, logger)

# Load existing agent outputs
all_data = {
    'metadata': load_json(Path('output/reports/metadata_extraction_output.json')),
    'quality': load_json(Path('output/reports/quality_assessment_output.json')),
    # ... etc
}

output, validation = agent.run(all_data)
```

## Configuration System

### Configuration Flow
```
config.yaml → TravelPhotoOrchestrator.__init__()
           ├─→ setup_logger(logging config)
           ├─→ ensure_directories(paths config)
           └─→ Initialize 7 agents with (config, logger)
                └─→ Each agent extracts agent-specific config section
```

### Key Configuration Sections

**config.yaml structure:**
- `paths`: input_images, output directories (reports, website, logs, metadata)
- `agents.{agent_name}`: enabled, parallel_workers, batch_size, model, timeout_seconds
- `api`: Anthropic, OpenAI, Google API settings (model, max_tokens, temperature)
- `thresholds`: min_technical_quality (3), min_aesthetic_quality (3), duplicate_hamming_distance (10)
- `error_handling`: max_retries (3), continue_on_error (true)
- `logging`: level (INFO), format (json)
- `parallelization`: enable_parallel_agents (true), parallel_groups

### Agent-Specific Config Access Pattern
```python
class MyAgent:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('my_agent_key', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        self.model = self.agent_config.get('model', 'default-model')
```

### Environment Variables
Create `.env` file for API keys (see `.env.example`):
- `ANTHROPIC_API_KEY` - For Claude 3.5 Sonnet (Agents 3, 5, 6)
- `OPENAI_API_KEY` - For GPT-4 Vision (alternative for Agents 2, 3)
- `GOOGLE_API_KEY` - For Gemini (alternative for Agent 6)

## Critical Architecture Patterns

### 1. Agent Implementation Template

All agents follow this structure:
```python
class AgentName:
    SYSTEM_PROMPT = """Expert-level prompt describing agent role..."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('agent_key', {})
        # Extract settings: parallel_workers, batch_size, model, etc.

    def run(self, image_paths: List[Path], *upstream_outputs) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process all images and return (output_list, validation_summary).

        Returns:
            Tuple of:
            - List of dicts (one per image with processing results)
            - Validation dict: {"agent": str, "stage": str, "status": str, "summary": str, "issues": List[str]}
        """
        # Use ThreadPoolExecutor for parallel processing
        # Collect results
        # Return (results, validation)

    def process_image(self, image_path: Path, metadata: Dict) -> Dict[str, Any]:
        """Process single image with error handling."""
        try:
            # Core logic
            result = {...}
            # Validate output
            is_valid, error_msg = validate_agent_output("agent_key", result)
            return result
        except Exception as e:
            log_error(self.logger, "Agent Name", "ErrorType", str(e), "error")
            return default_result
```

### 2. Three-Tier Validation System

**Tier 1: Agent Output Schema Validation** (`utils/validation.py` AGENT_SCHEMAS)
- Each agent output must match its JSON schema
- Called via `validate_agent_output(agent_key, output)`

**Tier 2: Validation Summary Format**
Every agent returns:
```python
{
    "agent": "Agent Name",
    "stage": "processing_stage",
    "status": "success|warning|error",
    "summary": "Processed X/Y images successfully",
    "issues": ["optional", "list", "of", "issues"]
}
```

**Tier 3: Final Report Validation** (`validate_final_report()`)
Orchestrator generates final report with required fields:
- num_images_ingested, average_technical_score, average_aesthetic_score
- num_duplicates_found, num_images_final_selected, num_images_flagged_for_manual_review
- agent_performance, category_distribution, quality_distribution, agent_errors

### 3. Error Handling & Logging

**Structured Error Logging:**
```python
from utils.logger import log_error

log_error(
    logger=self.logger,
    agent="Agent Name",
    error_type="ProcessingError|ValidationError|NetworkError",
    summary="Human-readable error description",
    severity="info|warning|error|critical",
    details={"optional": "context"}
)
```

**Global Error Registry:**
- All errors accumulate in `utils.logger.ERROR_LOG` (global list)
- Saved to `output/logs/errors.json` at workflow completion
- Included in final report's `agent_errors` array

**Severity Levels:**
- `info`: Informational, no action needed
- `warning`: Potential issue, agent continues processing
- `error`: Failed for specific image, agent continues with other images
- `critical`: Agent or workflow failure, execution stops

**Continue-on-Error Behavior:**
- Configured via `config.yaml` → `error_handling.continue_on_error: true`
- If agent throws exception, orchestrator logs error but continues to next agent
- Failed images get default/placeholder results

### 4. Parallelization Strategy

**ThreadPoolExecutor Pattern (all agents):**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
    futures = [executor.submit(self.process_image, path, metadata) for path in image_paths]
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
```

**Worker Counts (from config.yaml):**
- Agent 1 (Metadata): 4 workers (I/O bound)
- Agent 2 (Quality): 2 workers (CPU bound - OpenCV)
- Agent 3 (Aesthetic): 2 workers (API rate limited)
- Agent 4 (Duplicates): 1 worker (pairwise comparisons)
- Agent 5 (Filtering): 2 workers
- Agent 6 (Captions): 2 workers (API rate limited)

## Output Structure

```
output/
├── reports/
│   ├── {agent_name}_output.json     # List of dicts, one per image
│   ├── validations.json             # Array of all 7 validation summaries
│   └── final_report.json            # Aggregated statistics
├── logs/
│   ├── workflow.log                 # Structured JSON logs
│   └── errors.json                  # All errors with timestamps
├── metadata/                        # Optional EXIF cache
└── website/                         # Complete React app
    ├── package.json
    ├── README.md
    ├── FEATURES.md
    └── public/data/photos.json      # Website data payload
```

## Adding or Modifying Agents

### Required Integration Points

1. **Create Agent Class** (`agents/new_agent.py`):
   - Inherit pattern from existing agents
   - Define `SYSTEM_PROMPT` as class constant
   - Implement `__init__(config, logger)` and `run()` methods
   - Return `(List[Dict], validation_dict)` from `run()`

2. **Register in Orchestrator** (`orchestrator.py`):
   ```python
   from agents.new_agent import NewAgent

   self.agents = {
       # ... existing agents
       'new_agent': NewAgent(self.config, self.logger)
   }
   ```

3. **Add to Workflow Execution** (`orchestrator.py` → `run_workflow()`):
   ```python
   self._run_agent_stage(
       "New Agent Name",
       lambda: self.agents['new_agent'].run(
           image_paths,
           self.outputs.get('upstream_dependency', [])
       )
   )
   ```

4. **Add Validation Schema** (`utils/validation.py` → `AGENT_SCHEMAS`):
   ```python
   "new_agent": {
       "type": "object",
       "required": ["image_id", "key_field"],
       "properties": {...}
   }
   ```

5. **Add Configuration Section** (`config.yaml`):
   ```yaml
   agents:
     new_agent:
       enabled: true
       parallel_workers: 2
       model: "model-name"
   ```

### Agent Output Requirements

Each agent's `run()` method must return:
1. **Output List**: `List[Dict[str, Any]]` where each dict has `"image_id"` key
2. **Validation Dict**: Must contain `agent`, `stage`, `status`, `summary` keys

## VLM/LLM Integration Points

**Currently Simulated (Production-Ready Structure):**
- Agents 3, 5, 6 have VLM/LLM integration scaffolding
- Check `os.getenv('ANTHROPIC_API_KEY')` to detect API keys
- Implement actual API calls in `_call_vlm_api()` or `_call_llm_api()` methods

**Production Implementation Example:**
```python
# In aesthetic_assessment.py
from anthropic import Anthropic

def _call_vlm_api(self, image_path: Path, prompt: str) -> Dict[str, Any]:
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    response = client.messages.create(
        model=self.api_config.get('model', 'claude-3-5-sonnet-20241022'),
        max_tokens=self.api_config.get('max_tokens', 4096),
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": prompt}
            ]
        }]
    )

    return parse_response(response.content[0].text)
```

## Performance Considerations

- **Batch Processing**: Agents 3 & 6 use `batch_size` config for API rate limiting
- **Caching**: Enable `performance.cache_embeddings: true` in config for CLIP embeddings
- **Preview Sizes**: Configure `image_preview_size: [800, 800]` to resize images before quality analysis
- **Parallel Workers**: Adjust per agent based on I/O vs CPU vs API constraints
- **Memory**: Each worker holds one image in memory; reduce workers if OOM errors occur

## Important Notes

- **Dependencies**: Requires OpenCV, Pillow, imagehash, transformers (see requirements.txt)
- **Image Formats**: Supports .jpg, .jpeg, .png, .heic, .raw, .cr2, .nef, .arw (via Pillow)
- **GPS Reverse Geocoding**: Currently returns coordinates; production should use geopy or reverse-geocoder
- **Website Generation**: Creates React structure but not full component code (placeholder for expansion)
- **Model Selection**: config.yaml allows switching between clip-iqa, gpt4v, claude for each agent
- **Validation Failures**: Logged as warnings but don't stop execution (graceful degradation)
