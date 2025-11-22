# UML Diagrams & Architecture Visualizations

---

## System Overview Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    COMPLETE SYSTEM ARCHITECTURE                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ WEB APPLICATION LAYER (Flask)                                        │
├──────────────────────────────────────────────────────────────────────┤
│  app.py (Port 5001)                                                  │
│  ├─ Routes: /, /upload, /report/<timestamp>, /status/<run_id>       │
│  ├─ Templates: base.html, index.html, report.html                   │
│  └─ Static: CSS (Clean SaaS design), JavaScript (tab switching)     │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP
                             │ POST /upload → triggers orchestrator
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ORCHESTRATION LAYER                                                  │
├──────────────────────────────────────────────────────────────────────┤
│  TravelPhotoOrchestrator                                             │
│  ├─ Sequential: Agent 1 (Metadata)                                   │
│  ├─ Parallel: Agents 2 & 3 (Quality, Aesthetic)                     │
│  ├─ Sequential: Agent 4 (Filtering)                                  │
│  └─ Sequential: Agent 5 (Captions)                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
│  Agent 1    │    │  Agents 2-3  │    │  Agents 4-5      │
│  Metadata   │    │  Assessment  │    │  Enrich          │
│             │    │              │    │                  │
│ • Pillow    │    │ • OpenCV     │    │ • Vertex AI      │
│ • piexif    │    │ • NumPy      │    │ • Rules          │
│ • geopy     │    │ • Vertex AI  │    │ • Token Track    │
│             │    │ • Token Track│    │                  │
└─────────────┘    └──────────────┘    └──────────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ VERTEX AI INTEGRATION                                                │
├──────────────────────────────────────────────────────────────────────┤
│  google.genai.Client (vertexai=True)                                 │
│  ├─ Project: your-gcp-project                                        │
│  ├─ Location: us-central1                                            │
│  ├─ Model: gemini-1.5-flash                                          │
│  └─ Authentication: Application Default Credentials (ADC)            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ OUTPUT LAYER                                                         │
├──────────────────────────────────────────────────────────────────────┤
│  output/YYYYMMDD_HHMMSS/                                             │
│  ├─ reports/                                                         │
│  │  ├─ metadata_extraction_output.json                               │
│  │  ├─ quality_assessment_output.json                                │
│  │  ├─ aesthetic_assessment_output.json (+ token_usage)              │
│  │  ├─ filtering_categorization_output.json (+ reasoning + tokens)   │
│  │  ├─ caption_generation_output.json (+ token_usage)                │
│  │  └─ final_report.json (+ total_tokens_used)                       │
│  ├─ logs/                                                            │
│  │  ├─ workflow.log                                                  │
│  │  └─ errors.json                                                   │
│  └─ processed_images/                                                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Class Diagram: Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      <<interface>>                              │
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
    ┌───────────┴──────┐  ┌───┴────────┐  ┌┴──────────────┐
    │  MetadataAgent   │  │QualityAgent│  │AestheticAgent │
    ├──────────────────┤  ├────────────┤  ├───────────────┤
    │ - exif_parser    │  │ - cv2      │  │ - vertex_client│
    │ - geolocator     │  │ - numpy    │  │ - model_name   │
    │ (Nominatim)      │  │            │  │ - token_tracker│
    ├──────────────────┤  ├────────────┤  ├───────────────┤
    │ + run()          │  │ + run()    │  │ + run()       │
    │ - extract_exif() │  │ - assess() │  │ - assess_vlm()│
    │ - extract_gps()  │  │ - sharpness│  │ - extract_toks│
    │ - reverse_geo()  │  │ - exposure │  └───────────────┘
    └──────────────────┘  │ - noise    │
                          └────────────┘

    ┌──────────────────┐  ┌──────────────────┐
    │FilteringAgent    │  │CaptionAgent      │
    ├──────────────────┤  ├──────────────────┤
    │ - vertex_client  │  │ - vertex_client  │
    │ - filter_rules   │  │ - model_name     │
    │ - thresholds     │  │ - token_tracker  │
    │ - reasoning_gen  │  │ - prompt_builder │
    ├──────────────────┤  ├──────────────────┤
    │ + run()          │  │ + run()          │
    │ - categorize()   │  │ - generate_caps()│
    │ - apply_filters()│  │ - extract_toks() │
    │ - build_reason() │  │ - context_build()│
    │ - extract_toks() │  └──────────────────┘
    └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      FlaskWebApp                                │
├─────────────────────────────────────────────────────────────────┤
│ - app: Flask                                                    │
│ - upload_dir: Path                                              │
│ - output_dir: Path                                              │
├─────────────────────────────────────────────────────────────────┤
│ + index() -> HTML (dashboard + upload)                          │
│ + upload() -> JSON (run_id, status)                             │
│ + view_report(timestamp) -> HTML (tabbed report)                │
│ + check_status(run_id) -> JSON (status)                         │
│ - get_all_runs() -> List[Dict]                                  │
│ - load_agent_outputs(timestamp) -> Dict[str, Any]               │
│ - trigger_orchestrator(upload_dir) -> subprocess                │
└─────────────────────────────────────────────────────────────────┘
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
│ - timestamp: str (YYYYMMDD_HHMMSS)                               │
│ - output_dir: Path (output/{timestamp})                          │
├──────────────────────────────────────────────────────────────────┤
│ + run_workflow() -> bool                                         │
│ + _run_agent_stage(name, callable) -> (List[Dict], Dict)        │
│ + _validate_workflow_outputs() -> bool                           │
│ + _generate_final_report() -> Dict                               │
│ + _calculate_token_totals() -> int                               │
│ - _setup_logging() -> Logger                                     │
│ - _ensure_directories() -> None                                  │
│ - _load_images() -> List[Path]                                   │
│ - _initialize_agents() -> Dict                                   │
│ - _save_outputs() -> None                                        │
│ - _save_final_report() -> None                                   │
└──────────────────────────────────────────────────────────────────┘
            │
            │ uses (composition)
            │
            ├──→ Agent 1 (MetadataExtractionAgent)
            ├──→ Agent 2 (QualityAssessmentAgent)
            ├──→ Agent 3 (AestheticAssessmentAgent)
            ├──→ Agent 4 (FilteringCategorizationAgent)
            └──→ Agent 5 (CaptionGenerationAgent)
```

---

## Data Flow Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ Sequence: Complete Workflow Execution (Web Upload)                  │
└─────────────────────────────────────────────────────────────────────┘

User        WebApp       Orchestrator    Agent1    Agent2,3   Agent4    Agent5
 │           │               │             │          │         │         │
 │──upload──→│               │             │          │         │         │
 │           │               │             │          │         │         │
 │           │─save_files──→ │             │          │         │         │
 │           │               │             │          │         │         │
 │           │─trigger_orch──→             │          │         │         │
 │           │               │             │          │         │         │
 │◄──run_id──┤               │             │          │         │         │
 │           │               │             │          │         │         │
 │           │           load_images()     │          │         │         │
 │           │               │             │          │         │         │
 │           │               │──extract──→ │          │         │         │
 │           │               │             │          │         │         │
 │           │               │         [+geocode]     │         │         │
 │           │               │◄─output1────│          │         │         │
 │           │               │             │          │         │         │
 │           │               ├───────run_parallel────→│         │         │
 │           │               │             │          │         │         │
 │           │               │         [assess]       │         │         │
 │           │               │         [+tokens]      │         │         │
 │           │               │◄────output2,3──────────│         │         │
 │           │               │             │          │         │         │
 │           │               │─────filter──────────────────────→│         │
 │           │               │             │          │         │         │
 │           │               │         [categorize + reasoning]  │         │
 │           │               │         [+tokens]                │         │
 │           │               │◄────output4─────────────────────│         │
 │           │               │             │          │         │         │
 │           │               │─────caption────────────────────────────→   │
 │           │               │             │          │         │         │
 │           │               │         [generate + context + tokens]      │
 │           │               │◄────output5─────────────────────┤         │
 │           │               │             │          │         │         │
 │           │               │─save_all_outputs────────────────────────→  │
 │           │               │             │          │         │         │
 │           │               │─generate_report──────────────────────────→ │
 │           │               │             │          │         │         │
 │──poll────→│               │             │          │         │         │
 │           │               │             │          │         │         │
 │◄─status───┤               │             │          │         │         │
 │           │               │             │          │         │         │
 │─view_rep──→               │             │          │         │         │
 │           │               │             │          │         │         │
 │           │─load_outputs──────────────────────────────────────────────→│
 │           │               │             │          │         │         │
 │◄──HTML────┤               │             │          │         │         │
 │  (tabs)   │               │             │          │         │         │
```

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                   Travel Photo Organization System               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           WEB UI LAYER (Flask)                          │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  • Templates (Jinja2): base, index, report              │    │
│  │  • Static: Clean SaaS CSS, JavaScript                   │    │
│  │  • Routes: Upload, Report View, Status Polling          │    │
│  └────────────────┬────────────────────────────────────────┘    │
│                   │                                              │
│  ┌────────────────▼────────────────────────────────────────┐    │
│  │           INPUT LAYER                                   │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  • Image Files (JPG, PNG, HEIC, RAW) via upload/        │    │
│  │  • config.yaml (configuration)                          │    │
│  │  • ADC (Vertex AI credentials)                          │    │
│  └────────────────┬────────────────────────────────────────┘    │
│                   │                                              │
│  ┌────────────────▼────────────────────────────────────────┐    │
│  │         ORCHESTRATION LAYER                             │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │  TravelPhotoOrchestrator                                │    │
│  │  • Workflow execution (sequential + parallel)           │    │
│  │  • Agent coordination                                   │    │
│  │  • Result aggregation                                   │    │
│  │  • Token usage tracking                                 │    │
│  └────┬─────────────┬─────────────┬──────────────────────┘    │
│       │             │             │                           │
│  ┌────▼──┐  ┌──────▼────┐  ┌────▼─────┐                      │
│  │ Agent │  │   Agent   │  │  Agent   │                      │
│  │  1    │  │   2-3     │  │   4-5    │                      │
│  │Meta   │  │ Assess    │  │ Enrich   │                      │
│  └──┬─────┘  └───┬───────┘  └────┬─────┘                      │
│     │            │               │                           │
│  ┌──▼────────────▼───────────────▼──────────────────────┐    │
│  │        UTILITY LAYER                                 │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  • Logger (structured JSON logging)                 │    │
│  │  • Validation (schema enforcement)                  │    │
│  │  • Helpers (file I/O, config loading)               │    │
│  │  • Error Registry (centralized error tracking)      │    │
│  │  • Token Tracking (usage aggregation)               │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │                                           │
│  ┌────────────────▼──────────────────────────────────────┐    │
│  │         EXTERNAL INTEGRATIONS                         │    │
│  ├───────────────────────────────────────────────────────┤    │
│  │  • Vertex AI (Gemini 1.5 Flash)                      │    │
│  │  • Nominatim (Reverse Geocoding)                     │    │
│  │  • OpenCV (Image Processing)                         │    │
│  └────────────────┬──────────────────────────────────────┘    │
│                   │                                           │
│  ┌────────────────▼──────────────────────────────────────┐    │
│  │         OUTPUT LAYER                                  │    │
│  ├───────────────────────────────────────────────────────┤    │
│  │  • Reports/ (Agent outputs + token usage)            │    │
│  │  • Logs/ (workflow.log, errors.json)                 │    │
│  │  • Processed_images/ (uploaded files)                │    │
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
│  Python Runtime (3.9+)                                         │
│  ├─ uv (Package Manager)                                       │
│  └─ Virtual Environment (.venv/)                               │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Web Entry Point: web_app/app.py (Flask)             │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ • Port 5001                                          │    │
│  │ • Drag-and-drop upload interface                     │    │
│  │ • Triggers orchestrator.py as subprocess             │    │
│  │ • Serves tabbed reports                              │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                          │
│  ┌──────────────────▼───────────────────────────────────┐    │
│  │ CLI Entry Point: orchestrator.py                     │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │                                                      │    │
│  │ ThreadPoolExecutor Pools (per agent):               │    │
│  │ ├─ Agent 1: 4 workers (I/O + Geocoding)            │    │
│  │ ├─ Agent 2: 2 workers (CPU - OpenCV)               │    │
│  │ ├─ Agent 3: 2 workers (API - Vertex AI)            │    │
│  │ ├─ Agent 4: 2 workers (API - Vertex AI)            │    │
│  │ └─ Agent 5: 2 workers (API - Vertex AI)            │    │
│  │                                                      │    │
│  └──────────────────┬───────────────────────────────────┘    │
│                     │                                          │
│  ┌──────────────────▼───────────────────────────────────┐    │
│  │         External API Integrations                    │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ • Vertex AI (Gemini 1.5 Flash)                      │    │
│  │   - Project: your-gcp-project                       │    │
│  │   - Location: us-central1                           │    │
│  │   - Auth: Application Default Credentials (ADC)     │    │
│  │                                                      │    │
│  │ • Nominatim (geopy - Reverse Geocoding)             │    │
│  │   - User-Agent: travel-photo-workflow               │    │
│  │   - Timeout: 10 seconds                             │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## State Transition Diagram

```
                    ┌─────────────────┐
                    │    IDLE         │
                    │ (Web UI ready)  │
                    └────────┬────────┘
                             │ User uploads photos
                             ▼
                    ┌─────────────────┐
                    │  UPLOAD STAGE   │
                    │ • Save files    │
                    │ • Create run_id │
                    └────────┬────────┘
                             │ Trigger orchestrator
                             ▼
                    ┌─────────────────┐
                    │   INGESTION     │◄──────┐
                    │ (Agent 1 runs)  │       │
                    │ + Geocoding     │       │
                    └────────┬────────┘       │
                             │                │
                      (continues on error)───┘
                             │
                             ▼
         ┌─────────────────────────────────────┐
         │     PARALLEL ASSESSMENT             │
         │ (Agents 2 & 3 run concurrently)    │
         │ ┌──────────────┐   ┌──────────────┐│
         │ │ Quality (2)  │   │ Aesthetic(3) ││
         │ │ OpenCV       │   │ Vertex AI    ││
         │ │              │   │ +tokens      ││
         │ └──────────────┘   └──────────────┘│
         └────────┬──────────────────┬────────┘
                  │                  │
           (continues on error)
                  │                  │
                  └────────┬─────────┘
                           ▼
                    ┌──────────────────┐
                    │  FILTERING       │
                    │ (Agent 4 runs)   │
                    │ + Reasoning      │
                    │ + Tokens         │
                    └────────┬─────────┘
                             │
                      (continues on error)
                             │
                             ▼
                    ┌──────────────────┐
                    │ CAPTION GEN      │
                    │ (Agent 5 runs)   │
                    │ + Full Context   │
                    │ + Tokens         │
                    └────────┬─────────┘
                             │
                      (continues on error)
                             │
                             ▼
                    ┌──────────────────┐
                    │ VALIDATION &     │
                    │ REPORTING        │
                    │ + Token totals   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   COMPLETE       │
                    │ (Output written) │
                    │ Web UI updated   │
                    └──────────────────┘
```

---

## Data Structure Relationships

```
Image Entry {
  image_id: str ──────┐
  filename: str ──────├──────→ Metadata {
  file_size: int ──────┤         gps { lat, lon, location (geocoded) }
  format: str ─────────┤         camera_settings,
                       └──────→  capture_datetime }

  quality_score: int ──┐
  sharpness: int ───────┤───→ Quality Assessment {
  exposure: int ─────────┤     noise, resolution,
  noise: int ────────────┤     metrics, issues
                          └──→ }

  overall_aesthetic: int ─┐
  composition: int ────────┼──→ Aesthetic Assessment {
  framing: int ───────────┤     lighting, subject_interest,
  lighting: int ──────────┤     notes,
  subject_interest: int ───┤     token_usage {
  token_usage: {...} ──────┘       prompt_token_count,
              └──────→              candidates_token_count,
                                   total_token_count } }

  category: str ───────┐
  subcategories: [str]─┼──→ Categorization {
  time_category: str ──┤     location, passes_filter,
  location: str ───────┤     reasoning (explains decision),
  reasoning: str ───────┤     flags,
  passes_filter: bool ──┤     token_usage {...}
  flags: [str]─────────┤
  token_usage: {...} ───┘
            └──────→ }

  captions: {
    concise: str ────────┐
    standard: str ───────┼──→ Captions & Keywords {
    detailed: str ───────┤     keywords: [str],
  }                      │     token_usage {...}
  keywords: [str]────────┤
  token_usage: {...} ────┘
            └──────→ }
}
```

---

## Token Usage Flow

```
┌─────────────────────────────────────────────────┐
│  Token Usage Tracking (Per VLM Agent)          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ Agent calls         │
         │ Vertex AI API       │
         └─────────┬───────────┘
                   │
                   ▼
         ┌──────────────────────────┐
         │ response object received │
         └─────────┬────────────────┘
                   │
                   ▼
         ┌──────────────────────────────────┐
         │ Extract usage_metadata           │
         │ if hasattr(response, 'usage...'): │
         │   prompt_token_count             │
         │   candidates_token_count         │
         │   total_token_count              │
         └─────────┬────────────────────────┘
                   │
                   ▼
         ┌──────────────────────────────┐
         │ Add to result dict           │
         │ result['token_usage'] = {...}│
         └─────────┬──────────────────────┘
                   │
                   ▼
         ┌──────────────────────────────┐
         │ Save to JSON output          │
         │ aesthetic_assessment_output   │
         │ filtering_categorization...   │
         │ caption_generation_output     │
         └─────────┬──────────────────────┘
                   │
                   ▼
         ┌──────────────────────────────┐
         │ Display in Web UI            │
         │ • Aesthetic tab              │
         │ • Filtering tab              │
         │ • Caption tab                │
         │ (at bottom of each tab)      │
         └─────────┬──────────────────────┘
                   │
                   ▼
         ┌──────────────────────────────┐
         │ Aggregate in final_report    │
         │ total_tokens_used: NNNNN     │
         └──────────────────────────────┘
```

---

## Web UI Component Structure

```
┌──────────────────────────────────────────────────────────┐
│                    base.html                             │
│  (Clean SaaS Design System)                             │
├──────────────────────────────────────────────────────────┤
│  • Inter font family                                     │
│  • CSS variables (--primary, --text, --border)          │
│  • Responsive layout                                     │
│  • Modern color palette                                  │
└────────────────┬─────────────────┬─────────────────────┘
                 │                 │
     ┌───────────┴──────┐  ┌──────┴──────────┐
     │                  │  │                 │
     ▼                  ▼  ▼                 ▼
┌──────────┐    ┌──────────────────────────────────┐
│index.html│    │        report.html               │
├──────────┤    ├──────────────────────────────────┤
│Dashboard │    │ Stats Overview                   │
│          │    │ ├─ Total images                  │
│• Upload  │    │ ├─ Passed/Rejected               │
│  Zone    │    │ └─ Average scores                │
│          │    │                                  │
│• Run     │    │ Image Grid (responsive)          │
│  History │    │ ├─ Thumbnails                    │
│  List    │    │ └─ Per-image cards               │
│          │    │                                  │
│• Status  │    │ Tabbed Interface (per image)     │
│  Badges  │    │ ├─ Metadata Tab                  │
│          │    │ │  ├─ Date, camera               │
│          │    │ │  ├─ GPS location (geocoded)    │
│          │    │ │  └─ Dimensions                 │
│          │    │ │                                │
│• JS Poll │    │ ├─ Quality Tab                   │
│  Status  │    │ │  ├─ Overall score              │
│          │    │ │  ├─ Sharpness, noise, exposure │
│          │    │ │  └─ Issues                     │
│          │    │ │                                │
└──────────┘    │ ├─ Aesthetic Tab                 │
                │ │  ├─ Overall, composition       │
                │ │  ├─ Lighting, framing, subject │
                │ │  ├─ AI analysis notes          │
                │ │  └─ Token usage                │
                │ │                                │
                │ ├─ Filtering Tab                 │
                │ │  ├─ Status (pass/reject)       │
                │ │  ├─ Category                   │
                │ │  ├─ Reasoning (explains why)   │
                │ │  └─ Token usage                │
                │ │                                │
                │ └─ Caption Tab                   │
                │    ├─ Concise caption            │
                │    ├─ Standard caption           │
                │    ├─ Keywords                   │
                │    └─ Token usage                │
                │                                  │
                │ JavaScript                       │
                │ ├─ Tab switching                 │
                │ └─ Image card interactions       │
                └──────────────────────────────────┘
```

---

**For high-level overview, see [HLD.md](./HLD.md)**
**For detailed specifications, see [LLD.md](./LLD.md)**
**For workflow visualization, see [ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)**
**For quick setup, see [QUICKSTART.md](./QUICKSTART.md)**
