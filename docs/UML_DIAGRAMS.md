# UML Diagrams & Architecture Visualizations

---

## Class Diagram: Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      <<abstract>>                               │
│                      BaseAgent                                  │
├─────────────────────────────────────────────────────────────────┤
│ - config: Dict[str, Any]                                        │
│ - logger: Logger                                                │
│ - agent_config: Dict[str, Any]                                  │
│ - parallel_workers: int                                         │
│ - agent_name: str                                               │
├─────────────────────────────────────────────────────────────────┤
│ + run(image_paths, *upstream) -> (List[Dict], Dict)             │
│ + process_image(path, metadata) -> Dict                         │
│ + validate_output(output) -> (bool, str)                        │
│ + get_default_result() -> Dict                                  │
│ # _log_error(error_type, summary, severity)                     │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │
                ┌─────────────┼─────────────┬──────────────┐
                │             │             │              │
    ┌───────────┴──────┐  ┌───┴────────┐  ┌┴──────────────┐  ...
    │  MetadataAgent   │  │QualityAgent│  │AestheticAgent │
    ├──────────────────┤  ├────────────┤  ├───────────────┤
    │ - exif_parser    │  │ - iqa_model│  │ - vlm_client  │
    │ - gps_geocoder   │  │ - cv2      │  │ - vision_api  │
    ├──────────────────┤  ├────────────┤  ├───────────────┤
    │ + run()          │  │ + run()    │  │ + run()       │
    │ - extract_exif() │  │ - assess() │  │ - rate_image()│
    └──────────────────┘  └────────────┘  └───────────────┘

    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │DuplicateAgent    │  │FilteringAgent    │  │CaptionAgent      │
    ├──────────────────┤  ├──────────────────┤  ├──────────────────┤
    │ - clip_embedder  │  │ - vlm_classifier │  │ - llm_client     │
    │ - hash_engine    │  │ - filter_rules   │  │ - prompt_builder │
    ├──────────────────┤  ├──────────────────┤  ├──────────────────┤
    │ + run()          │  │ + run()          │  │ + run()          │
    │ - find_groups()  │  │ - categorize()   │  │ - generate_caps()│
    └──────────────────┘  └──────────────────┘  └──────────────────┘

    ┌──────────────────┐
    │WebsiteAgent      │
    ├──────────────────┤
    │ - react_template │
    │ - mui_config     │
    ├──────────────────┤
    │ + run()          │
    │ - generate_jsx() │
    └──────────────────┘
```

---

## Orchestrator Class Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│              TravelPhotoOrchestrator                             │
├──────────────────────────────────────────────────────────────────┤
│ - config: Dict[str, Any]                                         │
│ - logger: Logger                                                 │
│ - agents: Dict[str, BaseAgent]                                   │
│ - outputs: Dict[str, List[Dict]]                                 │
│ - validations: List[Dict]                                        │
│ - start_time: datetime                                           │
├──────────────────────────────────────────────────────────────────┤
│ + run_workflow() -> bool                                         │
│ + _run_agent_stage(name, callable) -> (List[Dict], Dict)        │
│ + _validate_workflow_outputs() -> bool                           │
│ + _generate_final_report() -> Dict                               │
│ - _setup_logging() -> Logger                                     │
│ - _ensure_directories() -> None                                  │
│ - _load_images() -> List[Path]                                   │
│ - _initialize_agents() -> Dict                                   │
│ - _save_outputs() -> None                                        │
│ - _save_final_report() -> None                                   │
└──────────────────────────────────────────────────────────────────┘
            │
            │ uses
            │ (composition)
            │
            ├──→ Agent 1 (MetadataExtractionAgent)
            ├──→ Agent 2 (QualityAssessmentAgent)
            ├──→ Agent 3 (AestheticAssessmentAgent)
            ├──→ Agent 4 (DuplicateDetectionAgent)
            ├──→ Agent 5 (FilteringCategorizationAgent)
            ├──→ Agent 6 (CaptionGenerationAgent)
            └──→ Agent 7 (WebsiteGenerationAgent)
```

---

## Data Flow Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ Sequence: Complete Workflow Execution                               │
└─────────────────────────────────────────────────────────────────────┘

Orchestrator          Agent1            Agent2,3         Agent4    Agent5,6
    │                  │                  │               │          │
    │─load_images()──→ │                  │               │          │
    │                  │                  │               │          │
    │                  │──extract_metadata→               │          │
    │◄─────output1─────│                  │               │          │
    │                  │                  │               │          │
    │                  │                  │               │          │
    ├─────────────────────run_parallel──────────────→    │          │
    │                  │                  │               │          │
    │                  │             [assess]             │          │
    │◄─────────────────────────output2,3─────────────────│          │
    │                  │                  │               │          │
    │                  │                  │   find_dups→  │          │
    │◄────────────────────────output4──────────────────│          │
    │                  │                  │               │          │
    ├─────────────────────run_parallel──────────────────────────→   │
    │                  │                  │               │          │
    │                  │             [enrich]            │          │
    │◄────────────────────────────output5,6──────────────┤          │
    │                  │                  │               │          │
    │                  │─→ Agent 7 (Website Gen)        │          │
    │◄─────────output7─────────────────────────────────────────────│
    │                  │                  │               │          │
    │─save_all_outputs───────────────────────────────────────────→  │
    │                  │                  │               │          │
    │─generate_report──────────────────────────────────────────────│
    │                  │                  │               │          │
```

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   Travel Photo Organization System              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           INPUT LAYER                                   │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  • Image Files (JPG, PNG, HEIC, RAW)                    │    │
│  │  • config.yaml (configuration)                          │    │
│  │  • .env (API keys)                                      │    │
│  └────────────────┬────────────────────────────────────────┘    │
│                   │                                              │
│  ┌────────────────▼────────────────────────────────────────┐    │
│  │         ORCHESTRATION LAYER                             │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │  TravelPhotoOrchestrator                                │    │
│  │  • Workflow DAG execution                               │    │
│  │  • Parallel agent coordination                          │    │
│  │  • Result aggregation                                   │    │
│  └────┬─────────────┬─────────────┬──────────────────────┘    │
│       │             │             │                           │
│  ┌────▼──┐  ┌──────▼────┐  ┌────▼─────┐  ┌──────────────┐   │
│  │ Agent │  │   Agent   │  │  Agent   │  │    Agent     │   │
│  │  1-4  │  │   5-6     │  │    7     │  │  (Optional)  │   │
│  │Layer  │  │  Layer    │  │  Layer   │  │   Custom     │   │
│  └──┬─────┘  └───┬───────┘  └────┬─────┘  └──────────────┘   │
│     │            │               │                           │
│  ┌──▼────────────▼───────────────▼──────────────────────┐    │
│  │        UTILITY LAYER                                 │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  • Logger (structured JSON logging)                 │    │
│  │  • Validation (schema enforcement)                  │    │
│  │  • Helpers (file I/O, config loading)               │    │
│  │  • Error Registry (centralized error tracking)      │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │                                           │
│  ┌────────────────▼──────────────────────────────────────┐    │
│  │         OUTPUT LAYER                                  │    │
│  ├───────────────────────────────────────────────────────┤    │
│  │  • Reports/ (Agent outputs, validations)             │    │
│  │  • Logs/ (workflow.log, errors.json)                 │    │
│  │  • Website/ (React app with photos.json)             │    │
│  │  • Metadata/ (EXIF cache)                            │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Deployment & Execution Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    EXECUTION ENVIRONMENT                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Python Runtime (3.9+)                                       │
│  ├─ uv (Package Manager)                                     │
│  └─ Virtual Environment (.venv/)                             │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Main Entry Point: orchestrator.py                    │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │                                                      │    │
│  │ ThreadPoolExecutor Pools (per agent):               │    │
│  │ ├─ Agent 1: 4 workers (I/O)                         │    │
│  │ ├─ Agent 2: 2 workers (CPU)                         │    │
│  │ ├─ Agent 3: 2 workers (API)                         │    │
│  │ ├─ Agent 4: 1 worker  (Quadratic)                   │    │
│  │ ├─ Agent 5: 2 workers (VLM)                         │    │
│  │ ├─ Agent 6: 2 workers (LLM)                         │    │
│  │ └─ Agent 7: 1 worker  (Sequential)                  │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                           │                                    │
│  ┌────────────────────────▼─────────────────────────────┐    │
│  │         External API Integrations                    │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ • OpenAI API (GPT-4 Vision, gpt-4-turbo)            │    │
│  │ • Google Gemini API (Vision + LLM)                  │    │
│  │ • Anthropic Claude API (Vision + LLM)               │    │
│  │ • Reverse Geocoding APIs (optional)                 │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## State Transition Diagram

```
                    ┌─────────────────┐
                    │    IDLE         │
                    │ (Awaiting input)│
                    └────────┬────────┘
                             │ run_workflow()
                             ▼
                    ┌─────────────────┐
                    │   INGESTION     │◄──────┐
                    │ (Agent 1 runs)  │       │
                    └────────┬────────┘       │
                             │               │
                      (continues on error)───┘
                             │
                             ▼
         ┌─────────────────────────────────────┐
         │     PARALLEL ASSESSMENT             │
         │ (Agents 2 & 3 run concurrently)    │
         │ ┌──────────────┐   ┌──────────────┐│
         │ │ Quality (2)  │   │ Aesthetic(3) ││
         │ └──────────────┘   └──────────────┘│
         └────────┬──────────────────┬────────┘
                  │                  │
           (continues on error)
                  │                  │
                  └────────┬─────────┘
                           ▼
                    ┌──────────────────┐
                    │ DEDUPLICATION    │
                    │ (Agent 4 runs)   │
                    └────────┬─────────┘
                             │
                      (continues on error)
                             │
                             ▼
         ┌─────────────────────────────────────┐
         │  PARALLEL ENRICHMENT                │
         │ (Agents 5 & 6 run concurrently)    │
         │ ┌──────────────┐   ┌──────────────┐│
         │ │ Filter (5)   │   │ Caption (6)  ││
         │ └──────────────┘   └──────────────┘│
         └────────┬──────────────────┬────────┘
                  │                  │
           (continues on error)
                  │                  │
                  └────────┬─────────┘
                           ▼
                    ┌──────────────────┐
                    │ PRESENTATION     │
                    │ (Agent 7 runs)   │
                    └────────┬─────────┘
                             │
                      (continues on error)
                             │
                             ▼
                    ┌──────────────────┐
                    │ VALIDATION &     │
                    │ REPORTING        │
                    │ (Generate reports)
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   COMPLETE       │
                    │ (Output written) │
                    └──────────────────┘
```

---

## Data Structure Relationships

```
Image Entry {
  image_id: str ──────┐
  filename: str ──────├──────→ Metadata {
  file_size: int ──────┤         gps, camera_settings,
  format: str ─────────┤         capture_datetime, etc.
                       └──────→ }

  quality_score: int ──┐
  sharpness: int ───────┤───→ Quality Assessment {
  exposure: int ─────────┤     metrics, issues
  noise: int ────────────┤     detected_problems
                          └──→ }

  overall_aesthetic: int ─┐
  composition: int ────────┼──→ Aesthetic Assessment {
  framing: int ───────────┤     composition, lighting,
  lighting: int ──────────┤     subject_interest
                          └──→ }

  category: str ───────┐
  subcategories: [str]─┼──→ Categorization {
  time_category: str ──┤     location, passes_filter,
  location: str ───────┤     flags
  flags: [str]─────────┘
            └──────→ }

  captions: {
    concise: str ────────┐
    standard: str ───────┼──→ Captions & Keywords {
    detailed: str ───────┤     keywords: [str]
  }                       └──→ }

  # From Agent 4
  group_id: str ──────→ Duplicate Group {
  selected_best: bool      image_ids, similarity
}
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────┐
│  Agent Processing with Error Handling           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
            ┌──────────────┐
            │ Try: Process │
            │   Image      │
            └──┬────────┬──┘
               │        │
         ┌─────▼─┐   ┌──▼────────────────────┐
         │Success│   │Exception Caught       │
         │       │   ├───────────────────────┤
         │       │   │ ├─ API Error          │
         │       │   │ ├─ Processing Error   │
         │       │   │ ├─ Validation Error   │
         │       │   │ └─ File I/O Error     │
         │       │   │                       │
         │       │   ├─ Log to ERROR_LOG     │
         │       │   ├─ Assign severity      │
         │       │   └─ Return default_result
         │       │      (with error flag)    │
         │       │                           │
         └───┬───┴───────────────────────┬──┘
             │                           │
             │ (continue to next image)  │
             │                           │
             └───────────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │ Collect Results      │
                  │ (successes + failures)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Generate Validation  │
                  │ Report & Errors Log  │
                  └──────────────────────┘
```

---

## Parallel Execution Timeline

```
Time
│
│ Agent 1 (Metadata)
├─────────────────────────────────────────────────────
│                                              Agent 4 (Dedup)
│  Agent 2 (Quality) ──┐                      ─────────────
│                       ├─→ Parallel         │
│  Agent 3 (Aesthetic) ──┘                    Agent 5 (Filter) ──┐
│                                                                 ├─→ Agent 7
│                                             Agent 6 (Caption) ──┘
│
└─────────────────────────────────────────────────────→

Wait points (must complete before next stage):
  ✓ Agent 1 → before Agents 2, 3
  ✓ Agents 2 & 3 → before Agent 4
  ✓ Agent 4 → before Agents 5 & 6
  ✓ Agents 5 & 6 → before Agent 7
```

---

## Configuration Loading Flow

```
┌───────────────────────────────┐
│   Application Startup         │
└──────────────┬────────────────┘
               │
    ┌──────────▼────────────┐
    │ Load config.yaml      │
    └──────────┬────────────┘
               │
    ┌──────────▼────────────┐
    │ Validate config       │
    │ against schema        │
    └──────────┬────────────┘
               │
    ┌──────────▼────────────┐
    │ Load .env variables   │
    └──────────┬────────────┘
               │
    ┌──────────▼────────────┐
    │ Create directories    │
    └──────────┬────────────┘
               │
    ┌──────────▼────────────────────────────────┐
    │ Initialize Agents                         │
    │ Each agent extracts:                      │
    │ config['agents']['agent_key']             │
    └──────────┬───────────────────────────────┘
               │
    ┌──────────▼────────────┐
    │ Setup Logger          │
    └──────────┬────────────┘
               │
    ┌──────────▼────────────┐
    │ Ready for execution   │
    └───────────────────────┘
```

---

**For high-level overview, see [HLD.md](./HLD.md)**
**For detailed specifications, see [LLD.md](./LLD.md)**
**For workflow visualization, see [ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)**
**For quick setup, see [QUICKSTART.md](./QUICKSTART.md)**
