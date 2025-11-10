# No-Framework Implementation

This folder contains the original **no-framework** implementation of the Travel Photo Organization Workflow. This is a custom multi-agent system built from scratch without using LangChain or similar frameworks.

## 📁 Structure

```
no-framework/
├── orchestrator.py          # Main workflow orchestrator
├── agents/                  # Agent implementations
│   ├── __init__.py
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
└── utils/                   # Utility modules
    ├── __init__.py
    ├── logger.py           # Logging utilities
    ├── helpers.py          # Configuration and file helpers
    └── validation.py       # Schema validation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From project root
uv sync
```

### 2. Configure Environment

```bash
# From project root
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Run the Workflow

```bash
# From project root
python no-framework/orchestrator.py

# Or using uv
uv run python no-framework/orchestrator.py
```

## 🎯 Architecture

### Orchestrator

The **orchestrator.py** coordinates the execution of 5 agents in sequence:

```
Agent 1: Metadata Extraction
    ↓
Agent 2: Quality Assessment + Agent 3: Aesthetic Assessment (parallel)
    ↓
Agent 4: Filtering & Categorization
    ↓
Agent 5: Caption Generation
```

### Agents

Each agent is a self-contained class with:
- `__init__(config, logger)` - Initialize with configuration
- `run(image_paths, *upstream_data)` - Execute agent logic
- `process_image(path)` - Process single image (called in parallel)

### Utilities

- **logger.py**: Structured logging with JSON format
- **helpers.py**: Configuration loading, file operations
- **validation.py**: JSON schema validation for agent outputs

## 📊 Agent Details

### 1. Metadata Extraction Agent
- **Input**: Image file paths
- **Output**: EXIF data, GPS coordinates, camera settings
- **Parallelization**: 4 workers (I/O bound)

### 2. Quality Assessment Agent
- **Input**: Image paths + metadata
- **Output**: Technical quality scores (sharpness, noise, exposure)
- **Parallelization**: 2 workers (CPU bound)

### 3. Aesthetic Assessment Agent
- **Input**: Image paths + metadata
- **Output**: Aesthetic scores (composition, lighting, framing)
- **Uses**: Gemini Vision API
- **Parallelization**: 2 workers (API rate limited)

### 4. Filtering & Categorization Agent
- **Input**: Image paths + metadata + quality + aesthetic
- **Output**: Filter decisions, categories, flags
- **Uses**: Gemini API
- **Logic**: Applies quality thresholds from config

### 5. Caption Generation Agent
- **Input**: All previous agent outputs
- **Output**: Captions, keywords, descriptions
- **Uses**: Gemini API
- **Logic**: Synthesizes all metadata into engaging captions

## ⚙️ Configuration

Edit **config.yaml** in the project root:

```yaml
paths:
  input_images: "./sample_images"
  output_dir: "./output"

agents:
  metadata_extraction:
    parallel_workers: 4

  aesthetic_assessment:
    parallel_workers: 2
    model: "gemini-2.5-flash-lite"

thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

error_handling:
  continue_on_error: true
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Images/Batch** | 150 images |
| **Total Time** | ~14 minutes |
| **Throughput** | ~10 images/minute |
| **Parallelization** | 2 stages run concurrently |

### Per-Agent Performance

| Agent | Model | Throughput |
|-------|-------|-----------|
| Metadata | Library | ~100 img/min |
| Quality | CV Model | ~10 img/min |
| Aesthetic | Gemini Vision | ~5 img/min |
| Filtering | Gemini | ~10 img/min |
| Captions | Gemini | ~10 img/min |

## 🔧 Key Features

### Error Handling
- **Graceful degradation**: Failed images get default values
- **Continue-on-error**: Workflow continues despite individual failures
- **Structured logging**: All errors logged to JSON with context

### Validation
- **3-tier validation**:
  1. Agent output validation (JSON schema)
  2. Summary validation (completeness check)
  3. Final report validation (statistics check)

### Parallelization
- **ThreadPoolExecutor** for concurrent image processing
- **Configurable workers** per agent
- **Two parallel stages**: Quality + Aesthetic run simultaneously

## 📝 Output

The workflow generates:

```
output/<timestamp>/
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
└── metadata/
    └── (EXIF data per image)
```

## 🆚 Comparison with LangChain Ecosystem

Want to see the same workflow implemented with modern frameworks? Check out the **[../langchain-ecosystem](../langchain-ecosystem)** folder.

| Aspect | No-Framework | LangChain Ecosystem |
|--------|--------------|---------------------|
| **Code Size** | 1,500 lines | 1,000 lines |
| **Setup** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Type Safety** | Manual | Pydantic |
| **Observability** | Logs | Full tracing |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Learning Curve** | Easy | Moderate |

## 🐛 Troubleshooting

### Import Errors

Make sure you're running from the project root:

```bash
python no-framework/orchestrator.py
```

### No Images Found

Check that `sample_images/` directory exists and contains images:

```bash
ls sample_images/
```

Update `config.yaml` if your images are in a different location.

### API Errors

Ensure your `.env` file contains valid API keys:

```bash
GOOGLE_API_KEY=your_key_here
```

## 📚 Documentation

For more details, see:
- **[../docs/HLD.md](../docs/HLD.md)** - High-level design
- **[../docs/LLD.md](../docs/LLD.md)** - Low-level design
- **[../docs/QUICKSTART.md](../docs/QUICKSTART.md)** - Quick start guide
- **[../README.md](../README.md)** - Project overview

## 🎓 Use Cases

This no-framework implementation is ideal for:
- **Learning**: Understand how multi-agent systems work under the hood
- **Customization**: Full control over every aspect of the workflow
- **Research**: Baseline for comparing frameworks
- **Production**: When you need maximum control and minimal dependencies

For production deployments with observability needs, consider the **LangChain ecosystem** implementation.
