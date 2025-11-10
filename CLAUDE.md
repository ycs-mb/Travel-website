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

### Setup with uv (Recommended)

This project uses **uv** for fast, reliable Python package management.

```bash
# Install dependencies
uv sync

# Run the workflow
uv run python orchestrator.py
# OR activate the virtual environment first
source .venv/bin/activate
python orchestrator.py

# Add new dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

### Run the Complete Workflow
```bash
uv run python orchestrator.py
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

### Run Individual Agents with Images

Each agent can be tested independently with image inputs. Below are Python REPL examples for agents that can process images directly.

#### Agent 1: Metadata Extraction
Extract EXIF metadata, GPS coordinates, camera settings from images.

**Python REPL:**
```bash
uv run python
```

```python
from agents.metadata_extraction import MetadataExtractionAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()
agent = MetadataExtractionAgent(config, logger)

# Process images
image_paths = [Path("sample_images/photo1.jpg"), Path("sample_images/photo2.jpg")]
metadata_list, validation = agent.run(image_paths)

# View results
print(f"Status: {validation['status']}")
print(f"Summary: {validation['summary']}")
for metadata in metadata_list:
    print(f"\nImage: {metadata['filename']}")
    print(f"  GPS: {metadata['gps']}")
    print(f"  Camera: {metadata['camera_settings']}")
    print(f"  DateTime: {metadata['capture_datetime']}")
```

**Output:** Metadata with GPS coordinates (including reverse-geocoded location), camera settings, EXIF data

---

#### Agent 2: Quality Assessment
Evaluate technical quality (sharpness, exposure, noise) of images.

**Python REPL:**
```bash
uv run python
```

```python
from agents.quality_assessment import QualityAssessmentAgent
from agents.metadata_extraction import MetadataExtractionAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

# Agent 2 depends on Agent 1 output
metadata_agent = MetadataExtractionAgent(config, logger)
image_paths = [Path("sample_images/photo1.jpg"), Path("sample_images/photo2.jpg")]
metadata_list, _ = metadata_agent.run(image_paths)

# Run quality assessment
quality_agent = QualityAssessmentAgent(config, logger)
quality_list, validation = quality_agent.run(image_paths, metadata_list)

# View results
print(f"Status: {validation['status']}")
for quality in quality_list:
    print(f"\nImage: {quality['image_id']}")
    print(f"  Quality Score: {quality['quality_score']}/5")
    print(f"  Sharpness: {quality['sharpness']}")
    print(f"  Exposure: {quality['exposure']}")
    print(f"  Noise: {quality['noise_level']}")
```

**Output:** Quality scores (1-5), sharpness, exposure, noise analysis

---

#### Agent 3: Aesthetic Assessment
Evaluate artistic quality (composition, framing, lighting) of images using Gemini Vision API.

**Python REPL:**
```bash
uv run python
```

```python
from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.metadata_extraction import MetadataExtractionAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

# Agent 3 depends on Agent 1 output
metadata_agent = MetadataExtractionAgent(config, logger)
image_paths = [Path("sample_images/photo1.jpg"), Path("sample_images/photo2.jpg")]
metadata_list, _ = metadata_agent.run(image_paths)

# Run aesthetic assessment (requires GOOGLE_API_KEY environment variable)
aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, validation = aesthetic_agent.run(image_paths, metadata_list)

# View results
print(f"Status: {validation['status']}")
for aesthetic in aesthetic_list:
    print(f"\nImage: {aesthetic['image_id']}")
    print(f"  Overall Aesthetic: {aesthetic['overall_aesthetic']}/5")
    print(f"  Composition: {aesthetic['composition']}/5")
    print(f"  Framing: {aesthetic['framing']}/5")
    print(f"  Lighting: {aesthetic['lighting']}/5")
    print(f"  Notes: {aesthetic['notes']}")
```

**Output:** Aesthetic scores (1-5) for composition, framing, lighting, subject interest; overall assessment

---

#### Agent 5: Filtering & Categorization
Categorize images by content, time, location and filter by quality thresholds using Gemini Vision API.

**Python REPL:**
```bash
uv run python
```

```python
from agents.filtering_categorization import FilteringCategorizationAgent
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from utils.helpers import load_config
from utils.logger import setup_logger
from pathlib import Path

config = load_config("config.yaml")
logger = setup_logger()

# Run prerequisite agents
image_paths = [Path("sample_images/photo1.jpg"), Path("sample_images/photo2.jpg")]
metadata_agent = MetadataExtractionAgent(config, logger)
metadata_list, _ = metadata_agent.run(image_paths)

quality_agent = QualityAssessmentAgent(config, logger)
quality_list, _ = quality_agent.run(image_paths, metadata_list)

aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, _ = aesthetic_agent.run(image_paths, metadata_list)

# Run filtering & categorization
filtering_agent = FilteringCategorizationAgent(config, logger)
categories, validation = filtering_agent.run(image_paths, metadata_list, quality_list, aesthetic_list)

# View results
print(f"Status: {validation['status']}")
for cat in categories:
    print(f"\nImage: {cat['image_id']}")
    print(f"  Category: {cat['category']}")
    print(f"  Subcategories: {cat['subcategories']}")
    print(f"  Time: {cat['time_category']}")
    print(f"  Location: {cat['location']}")
    print(f"  Passes Filter: {cat['passes_filter']}")
    if cat['flags']:
        print(f"  Flags: {cat['flags']}")
```

**Output:** Image categories, subcategories, time classification, location, pass/fail filter status

---

#### Agent 6: Caption Generation
Generate multi-level captions (concise/standard/detailed) for images using Gemini API.

**Python REPL:**
```bash
uv run python
```

```python
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

# Run prerequisite agents
image_paths = [Path("sample_images/photo1.jpg"), Path("sample_images/photo2.jpg")]
metadata_agent = MetadataExtractionAgent(config, logger)
metadata_list, _ = metadata_agent.run(image_paths)

quality_agent = QualityAssessmentAgent(config, logger)
quality_list, _ = quality_agent.run(image_paths, metadata_list)

aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, _ = aesthetic_agent.run(image_paths, metadata_list)

filtering_agent = FilteringCategorizationAgent(config, logger)
categories, _ = filtering_agent.run(image_paths, metadata_list, quality_list, aesthetic_list)

# Run caption generation
caption_agent = CaptionGenerationAgent(config, logger)
captions, validation = caption_agent.run(image_paths, metadata_list, quality_list, aesthetic_list, categories)

# View results
print(f"Status: {validation['status']}")
for caption in captions:
    print(f"\nImage: {caption['image_id']}")
    print(f"  Concise: {caption['captions']['concise']}")
    print(f"  Standard: {caption['captions']['standard']}")
    print(f"  Detailed: {caption['captions']['detailed']}")
    print(f"  Keywords: {caption['keywords']}")
```

**Output:** Three-level captions (concise/standard/detailed), keywords for searchability

---

### Run All Agents with Image Input Script

For convenience, create a Python script to process images through multiple agents at once:

**File: `run_agents.py`**
```python
#!/usr/bin/env python3
"""Run multiple agents on image directory."""

from pathlib import Path
from utils.helpers import load_config, get_image_files, save_json
from utils.logger import setup_logger
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.filtering_categorization import FilteringCategorizationAgent
from agents.caption_generation import CaptionGenerationAgent

def main():
    config = load_config("config.yaml")
    logger = setup_logger()

    # Get images
    input_dir = Path(config['paths']['input_images'])
    image_paths = get_image_files(input_dir)
    print(f"Found {len(image_paths)} images")

    # Agent 1: Metadata
    print("\n→ Extracting metadata...")
    metadata_agent = MetadataExtractionAgent(config, logger)
    metadata_list, val1 = metadata_agent.run(image_paths)
    print(f"  {val1['summary']}")

    # Agent 2: Quality
    print("\n→ Assessing quality...")
    quality_agent = QualityAssessmentAgent(config, logger)
    quality_list, val2 = quality_agent.run(image_paths, metadata_list)
    print(f"  {val2['summary']}")

    # Agent 3: Aesthetic
    print("\n→ Assessing aesthetics...")
    aesthetic_agent = AestheticAssessmentAgent(config, logger)
    aesthetic_list, val3 = aesthetic_agent.run(image_paths, metadata_list)
    print(f"  {val3['summary']}")

    # Agent 5: Categorization
    print("\n→ Categorizing images...")
    filtering_agent = FilteringCategorizationAgent(config, logger)
    categories, val5 = filtering_agent.run(image_paths, metadata_list, quality_list, aesthetic_list)
    print(f"  {val5['summary']}")

    # Agent 6: Captions
    print("\n→ Generating captions...")
    caption_agent = CaptionGenerationAgent(config, logger)
    captions, val6 = caption_agent.run(image_paths, metadata_list, quality_list, aesthetic_list, categories)
    print(f"  {val6['summary']}")

    # Save results
    output_dir = Path("agent_outputs")
    output_dir.mkdir(exist_ok=True)
    save_json(metadata_list, output_dir / "metadata.json")
    save_json(quality_list, output_dir / "quality.json")
    save_json(aesthetic_list, output_dir / "aesthetic.json")
    save_json(categories, output_dir / "categories.json")
    save_json(captions, output_dir / "captions.json")

    print(f"\n✓ Results saved to {output_dir}")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
uv run python run_agents.py
```

---

### Generate Website Only
```bash
# Start Python REPL with uv
uv run python
```

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
- `api`: OpenAI, Google API settings (model, max_tokens, temperature)
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
- `OPENAI_API_KEY` - For GPT-4 Vision (Agents 2, 3, 6)
- `GOOGLE_API_KEY` - For Gemini Vision (Agents 3, 5, 6)

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
- Check `os.getenv('OPENAI_API_KEY')` or `os.getenv('GOOGLE_API_KEY')` to detect API keys
- Implement actual API calls in `_call_vlm_api()` or `_call_llm_api()` methods

**Production Implementation Example (OpenAI):**
```python
# In aesthetic_assessment.py
from openai import OpenAI
import base64

def _call_vlm_api(self, image_path: Path, prompt: str) -> Dict[str, Any]:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    response = client.chat.completions.create(
        model=self.api_config.get('model', 'gpt-4-vision-preview'),
        max_tokens=self.api_config.get('max_tokens', 4096),
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                {"type": "text", "text": prompt}
            ]
        }]
    )

    return parse_response(response.choices[0].message.content)
```

**Production Implementation Example (Gemini):**
```python
# In aesthetic_assessment.py
import google.generativeai as genai
from PIL import Image

def _call_vlm_api(self, image_path: Path, prompt: str) -> Dict[str, Any]:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel(self.api_config.get('model', 'gemini-1.5-pro'))

    img = Image.open(image_path)
    response = model.generate_content([prompt, img])

    return parse_response(response.text)
```

## Performance Considerations

- **Batch Processing**: Agents 3 & 6 use `batch_size` config for API rate limiting
- **Caching**: Enable `performance.cache_embeddings: true` in config for CLIP embeddings
- **Preview Sizes**: Configure `image_preview_size: [800, 800]` to resize images before quality analysis
- **Parallel Workers**: Adjust per agent based on I/O vs CPU vs API constraints
- **Memory**: Each worker holds one image in memory; reduce workers if OOM errors occur

## Important Notes

- **Dependencies**: Managed via `uv` and `pyproject.toml`. Install with `uv sync`. See pyproject.toml for full list (OpenCV, Pillow, imagehash, transformers, torch, etc.)
- **Image Formats**: Supports .jpg, .jpeg, .png, .heic, .raw, .cr2, .nef, .arw (via Pillow)
- **GPS Reverse Geocoding**: Currently returns coordinates; production should use geopy or reverse-geocoder
- **Website Generation**: Creates React structure but not full component code (placeholder for expansion)
- **Model Selection**: config.yaml allows switching between clip-iqa, gpt4v, gemini for each agent
- **Validation Failures**: Logged as warnings but don't stop execution (graceful degradation)
