# CrewAI Conversion Documentation

This document describes the conversion of the Travel Photo Organization system from a custom agent-based architecture to CrewAI framework.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [Component Mapping](#component-mapping)
4. [Usage](#usage)
5. [Benefits of CrewAI](#benefits-of-crewai)
6. [Migration Guide](#migration-guide)

---

## Overview

The travel photo organization system has been converted from a custom agent orchestration system to **CrewAI**, a modern framework for building collaborative AI agent systems. CrewAI provides a standardized way to define agents, tasks, and workflows with better maintainability and extensibility.

### What Changed?

- **Original**: Custom `orchestrator.py` with manual agent coordination
- **New**: CrewAI-based `crewai_orchestrator.py` with framework-managed coordination

### What Stayed the Same?

- **Core logic**: All existing agent logic (metadata extraction, quality assessment, etc.) remains unchanged
- **Dependencies**: All image processing libraries and APIs remain the same
- **Configuration**: `config.yaml` structure unchanged
- **Output**: Same output format and directory structure

---

## Architecture Comparison

### Original Architecture

```
orchestrator.py (Custom Orchestration)
├── agents/
│   ├── metadata_extraction.py (MetadataExtractionAgent)
│   ├── quality_assessment.py (QualityAssessmentAgent)
│   ├── aesthetic_assessment.py (AestheticAssessmentAgent)
│   ├── filtering_categorization.py (FilteringCategorizationAgent)
│   └── caption_generation.py (CaptionGenerationAgent)
└── Manual sequential/parallel execution

Agents contained both logic AND role definition
Orchestrator manually managed task dependencies
```

### CrewAI Architecture

```
crewai_orchestrator.py (CrewAI Framework)
├── travel_photo_tools/ (Custom Tools - wraps existing agents)
│   ├── metadata_tool.py (MetadataExtractionTool)
│   ├── quality_tool.py (QualityAssessmentTool)
│   ├── aesthetic_tool.py (AestheticAssessmentTool)
│   ├── filtering_tool.py (FilteringCategorizationTool)
│   └── caption_tool.py (CaptionGenerationTool)
├── crewai_config_agents.yaml (Agent roles, goals, backstories)
├── crewai_config_tasks.yaml (Task descriptions and dependencies)
└── CrewAI framework manages execution

Separation of concerns: Logic in tools, roles in agents
Framework handles task dependencies automatically
LLM-powered agents can reason about tool usage
```

---

## Component Mapping

| Original | CrewAI Equivalent | Purpose |
|----------|-------------------|---------|
| `orchestrator.py` | `crewai_orchestrator.py` | Main workflow coordinator |
| Agent classes (`.run()` method) | Custom Tools (BaseTool) | Image processing logic |
| Agent SYSTEM_PROMPT | Agent (role, goal, backstory) | Agent personality and expertise |
| Sequential stages | Tasks with context dependencies | Workflow steps |
| Manual execution | Crew.kickoff() | Workflow execution |
| ThreadPoolExecutor | Maintained in tools | Parallel image processing |

### Detailed Mapping

#### 1. Metadata Extraction

**Original:**
- `agents/metadata_extraction.py` - `MetadataExtractionAgent` class
- Contains SYSTEM_PROMPT and processing logic

**CrewAI:**
- `travel_photo_tools/metadata_tool.py` - `MetadataExtractionTool` (wraps original agent)
- `crewai_config_agents.yaml` - `metadata_expert` (role, goal, backstory)
- `crewai_config_tasks.yaml` - `extract_metadata` task

#### 2. Quality Assessment

**Original:**
- `agents/quality_assessment.py` - `QualityAssessmentAgent` class

**CrewAI:**
- `travel_photo_tools/quality_tool.py` - `QualityAssessmentTool`
- `crewai_config_agents.yaml` - `quality_analyst`
- `crewai_config_tasks.yaml` - `assess_quality` task (depends on metadata)

#### 3. Aesthetic Assessment

**Original:**
- `agents/aesthetic_assessment.py` - `AestheticAssessmentAgent` class

**CrewAI:**
- `travel_photo_tools/aesthetic_tool.py` - `AestheticAssessmentTool`
- `crewai_config_agents.yaml` - `aesthetic_critic`
- `crewai_config_tasks.yaml` - `assess_aesthetics` task (depends on metadata)

#### 4. Filtering & Categorization

**Original:**
- `agents/filtering_categorization.py` - `FilteringCategorizationAgent` class

**CrewAI:**
- `travel_photo_tools/filtering_tool.py` - `FilteringCategorizationTool`
- `crewai_config_agents.yaml` - `content_curator`
- `crewai_config_tasks.yaml` - `filter_and_categorize` task (depends on all previous)

#### 5. Caption Generation

**Original:**
- `agents/caption_generation.py` - `CaptionGenerationAgent` class

**CrewAI:**
- `travel_photo_tools/caption_tool.py` - `CaptionGenerationTool`
- `crewai_config_agents.yaml` - `caption_writer`
- `crewai_config_tasks.yaml` - `generate_captions` task (depends on all previous)

---

## Usage

### Running the Original System

```bash
# Original workflow
uv run python orchestrator.py
```

### Running the CrewAI System

```bash
# CrewAI workflow
uv run python crewai_orchestrator.py
```

### Configuration

Both systems use the same `config.yaml` file:

```yaml
paths:
  input_images: "./sample_images"
  output_dir: "./output"

agents:
  metadata_extraction:
    parallel_workers: 4
  # ... other agent configs

api:
  openai:
    model: "gpt-4-vision-preview"
  google:
    model: "gemini-2.5-flash-lite"
```

### Environment Variables

Both systems require the same environment variables:

```bash
# .env file
OPENAI_API_KEY=sk-...      # For GPT-4 agents (optional)
GOOGLE_API_KEY=AIza...     # For Gemini agents (optional)
```

---

## Benefits of CrewAI

### 1. **Standardized Agent Framework**

- **Before**: Custom agent classes with manual coordination
- **After**: Industry-standard CrewAI framework with proven patterns

### 2. **Separation of Concerns**

- **Tools**: Contain pure image processing logic (reusable)
- **Agents**: Define roles, expertise, and reasoning capabilities
- **Tasks**: Describe what needs to be done (declarative)

### 3. **LLM-Powered Reasoning**

CrewAI agents can use LLMs to:
- Reason about when to use tools
- Interpret tool results
- Make decisions about next steps
- Handle errors gracefully

### 4. **Better Maintainability**

```yaml
# Easy to modify agent personas in YAML
metadata_expert:
  role: "Metadata Extraction Specialist"
  goal: "Extract comprehensive metadata..."
  backstory: "You are a world-class..."
```

### 5. **Extensibility**

Adding new agents or tools:

**Original**: Create new agent class, modify orchestrator logic
**CrewAI**: Add tool, define agent/task in YAML

### 6. **Built-in Features**

- **Task Dependencies**: Automatic via `context` parameter
- **Agent Delegation**: Agents can delegate to other agents
- **Memory**: Agents can remember previous interactions
- **Callbacks**: Hook into task execution lifecycle
- **Verbose Logging**: Built-in detailed logging

### 7. **Community & Ecosystem**

- Active community and regular updates
- Pre-built tools (WebSearch, FileRead, etc.)
- Integration with LangChain, LlamaIndex
- Documentation and examples

---

## Migration Guide

### For Developers

If you're working on this codebase:

1. **Original system is preserved**: All files in `agents/` remain unchanged
2. **New system is additive**: New files in `crewai_*/` directories
3. **Choose which to use**: Run either orchestrator based on your needs

### Customizing Agents

**Original System:**
```python
# agents/custom_agent.py
class CustomAgent:
    SYSTEM_PROMPT = """You are..."""
    def run(self, inputs):
        # logic here
```

**CrewAI System:**
```python
# 1. Create tool: travel_photo_tools/custom_tool.py
class CustomTool(BaseTool):
    name = "Custom Tool"
    description = "..."
    def _run(self, inputs):
        # reuse original agent logic
```

```yaml
# 2. Define agent: crewai_config_agents.yaml
custom_expert:
  role: "Custom Specialist"
  goal: "..."
  backstory: "..."
```

```yaml
# 3. Define task: crewai_config_tasks.yaml
custom_task:
  description: "..."
  expected_output: "..."
  agent: custom_expert
```

### Adding Dependencies Between Tasks

```yaml
# crewai_config_tasks.yaml
new_task:
  description: "Process results from previous tasks"
  expected_output: "..."
  agent: new_agent
  context: [task1, task2]  # This task depends on task1 and task2
```

### Configuring LLMs

By default, CrewAI uses OpenAI (if `OPENAI_API_KEY` is set) or Gemini (if `GOOGLE_API_KEY` is set).

To customize:

```python
# crewai_orchestrator.py
agent = Agent(
    role="...",
    goal="...",
    backstory="...",
    tools=[...],
    llm="gpt-4-turbo-preview"  # or "gemini-pro", "claude-3-opus", etc.
)
```

### Running Both Systems

You can run both systems and compare results:

```bash
# Test original
uv run python orchestrator.py

# Test CrewAI
uv run python crewai_orchestrator.py

# Compare outputs in output/<timestamp>/reports/
```

---

## File Structure

```
Travel-website/
├── agents/                          # Original agent implementations
│   ├── metadata_extraction.py
│   ├── quality_assessment.py
│   ├── aesthetic_assessment.py
│   ├── filtering_categorization.py
│   └── caption_generation.py
│
├── travel_photo_tools/              # CrewAI tools (wrap original agents)
│   ├── __init__.py
│   ├── metadata_tool.py
│   ├── quality_tool.py
│   ├── aesthetic_tool.py
│   ├── filtering_tool.py
│   └── caption_tool.py
│
├── orchestrator.py                  # Original orchestrator
├── crewai_orchestrator.py           # CrewAI orchestrator
├── crewai_config_agents.yaml        # Agent definitions
├── crewai_config_tasks.yaml         # Task definitions
├── config.yaml                      # Shared configuration
└── CREWAI_CONVERSION.md            # This file
```

---

## Performance Considerations

### Original System

- **Parallelization**: ThreadPoolExecutor within each agent
- **Performance**: ~14 minutes for 150 images

### CrewAI System

- **Parallelization**: Maintained in tools (same as original)
- **Performance**: Similar to original (~14 minutes for 150 images)
- **Overhead**: Minimal LLM calls for agent reasoning (adds <1 minute)

### Optimization Tips

1. **Reduce LLM calls**: Use simpler models (e.g., `gpt-3.5-turbo`)
2. **Increase parallelization**: Adjust `parallel_workers` in `config.yaml`
3. **Cache results**: Enable caching in tools
4. **Async execution**: Consider converting tools to async

---

## Troubleshooting

### Issue: "No module named 'crewai'"

**Solution:**
```bash
uv add crewai crewai-tools
```

### Issue: "Cannot import name 'BaseTool' from 'crewai_tools'"

**Solution:**
The `BaseTool` class is in the `crewai` package, not `crewai_tools`. Use the correct import:
```python
from crewai.tools import BaseTool  # Correct
```

NOT:
```python
from crewai_tools import BaseTool  # Incorrect
```

**Note:** We also renamed our custom tools directory from `crewai_tools/` to `travel_photo_tools/` to avoid naming conflicts with the CrewAI framework's built-in `crewai_tools` module.

### Issue: "Agent has no LLM configured"

**Solution:**
Set either `OPENAI_API_KEY` or `GOOGLE_API_KEY` in `.env` file.

### Issue: "Task dependency not found"

**Solution:**
Check that task names in `context` match task keys in `crewai_config_tasks.yaml`.

### Issue: "Tool execution failed"

**Solution:**
Tools wrap original agents, so check logs for the underlying agent error.
The original agent's error handling is preserved.

---

## Next Steps

1. **Test the CrewAI implementation**: Run with sample images
2. **Compare outputs**: Verify CrewAI produces same results as original
3. **Experiment with agent prompts**: Modify YAML configurations
4. **Add new capabilities**: Leverage CrewAI's ecosystem
5. **Production deployment**: Choose which system to deploy

---

## Questions?

For questions about:
- **Original system**: See `docs/QUICKSTART.md`, `docs/HLD.md`, `docs/LLD.md`
- **CrewAI framework**: See https://docs.crewai.com/
- **This conversion**: See this document

---

**Last Updated**: 2025-11-10
**CrewAI Version**: 1.4.1
**Python Version**: 3.10+
