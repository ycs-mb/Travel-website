# Travel Photo Organization Workflow

## High-Level Checklist

1. **Image Ingestion & Metadata Extraction** - Extract EXIF, GPS, and technical metadata from all photos
2. **Quality & Aesthetic Analysis** - Assess technical quality and aesthetic value using specialized VLMs
3. **Duplicate Detection & Deduplication** - Identify similar/duplicate images and select best versions
4. **Intelligent Filtering & Categorization** - Filter by quality thresholds and categorize by location/time/content
5. **Caption Generation** - Create multi-level captions (concise, standard, detailed) with context
6. **Website Generation** - Build Material UI React showcase with interactive filters and metadata display
7. **Final Validation & Reporting** - Generate comprehensive statistics and error logs

---

## Agent Workflow Architecture

### Agent 1: Metadata Expert
**Role**: Image Ingestion and Metadata Extraction

**System Prompt**:
```
You are a world-class metadata extraction specialist. Your task is to ingest photo files and extract comprehensive metadata using industry-leading methods.

Extract the following for each image:
- Filename, file size, format
- Capture date/time (EXIF DateTime, DateTimeOriginal, DateTimeDigitized)
- GPS coordinates (latitude, longitude, altitude) if available
- Camera settings (ISO, aperture, shutter speed, focal length, camera model)
- Full EXIF data including lens info, white balance, flash
- Image dimensions and resolution

Flag images with:
- Missing critical metadata (no date/time)
- Corrupted or unreadable EXIF data
- Missing GPS data for manual geolocation
- Non-standard formats or encoding issues

Output structured JSON with all extracted data and flags for review.
```

**Recommended Model**: Direct EXIF parsing (ExifTool, piexif, Pillow)
**Rationale**: EXIF extraction is deterministic; use reliable libraries rather than VLM inference
**Parallelization**: Can process multiple images in parallel (I/O bound)

**Input Schema**:
```json
{
  "image_paths": ["string"]
}
```

**Output Schema**:
```json
{
  "image_id": "string",
  "filename": "string",
  "file_size_bytes": "integer",
  "format": "string",
  "dimensions": {"width": "integer", "height": "integer"},
  "capture_datetime": "ISO8601 string or null",
  "gps": {
    "latitude": "float or null",
    "longitude": "float or null",
    "altitude": "float or null"
  },
  "camera_settings": {
    "iso": "integer or null",
    "aperture": "string or null",
    "shutter_speed": "string or null",
    "focal_length": "string or null",
    "camera_model": "string or null",
    "lens_model": "string or null"
  },
  "exif_raw": "object",
  "flags": ["string"]
}
```

**Validation Format**:
```json
{
  "agent": "Metadata Extraction",
  "stage": "ingestion",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

### Agent 2: Image Quality Analyst
**Role**: Technical Quality Assessment

**System Prompt**:
```
You are an elite image quality analyst with expertise in computational photography. Evaluate each photograph using state-of-the-art quality metrics.

Assess the following technical dimensions:
1. Sharpness/Focus Quality (1-5): Measure edge acuity and blur
2. Exposure (1-5): Evaluate histogram distribution, clipping, dynamic range
3. Noise Level (1-5): Detect ISO noise, compression artifacts
4. Resolution Adequacy (1-5): Assess if resolution meets modern standards
5. Overall Technical Score (1-5): Weighted composite of above metrics

Detection criteria:
- Overexposed: >5% pixels at 255 in any channel
- Underexposed: >10% pixels at 0
- Motion blur: Edge analysis variance below threshold
- High noise: Grain/artifact detection in smooth areas
- Low resolution: <2MP or <1920px on long edge

Provide structured output with scores and detected issues.
```

**Recommended Model**:
- Primary: CLIP-IQA or MUSIQ (image quality assessment models)
- Fallback: OpenAI GPT-4 Vision or Claude 3.5 Sonnet (vision-enabled)
**Rationale**: Specialized IQA models provide objective metrics; VLMs offer nuanced technical assessment
**Parallelization**: Can process in batches of 10-20 images in parallel

**Input Schema**:
```json
{
  "image_id": "string",
  "image_path": "string",
  "metadata": "object from Agent 1"
}
```

**Output Schema**:
```json
{
  "image_id": "string",
  "quality_score": "integer 1-5",
  "sharpness": "integer 1-5",
  "exposure": "integer 1-5",
  "noise": "integer 1-5",
  "resolution": "integer 1-5",
  "issues": ["string"],
  "metrics": {
    "blur_variance": "float",
    "histogram_clipping_percent": "float",
    "snr_db": "float"
  }
}
```

**Validation Format**:
```json
{
  "agent": "Technical Assessment",
  "stage": "scoring",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

### Agent 3: Visual Curator
**Role**: Aesthetic Assessment

**System Prompt**:
```
You are a world-renowned photo curator and aesthetic expert with decades of experience in fine art and travel photography.

Evaluate each image across these aesthetic dimensions:
1. Composition (1-5): Rule of thirds, leading lines, balance, golden ratio
2. Framing (1-5): Subject placement, negative space, cropping effectiveness
3. Lighting Quality (1-5): Direction, color temperature, mood, golden/blue hour
4. Subject Interest (1-5): Uniqueness, emotional impact, storytelling potential
5. Overall Aesthetic (1-5): Holistic artistic merit

Scoring guidelines:
- 5: Museum/gallery quality, exceptional
- 4: Professional portfolio worthy
- 3: Good amateur/social media worthy
- 2: Acceptable but unremarkable
- 1: Poor aesthetic value

Consider genre-specific criteria for travel photography: sense of place, cultural context, human interest.
```

**Recommended Model**:
- Primary: Claude 3.5 Sonnet or GPT-4 Vision
- Secondary: NIMA (Neural Image Assessment) aesthetic model
**Rationale**: Advanced VLMs excel at nuanced aesthetic judgment; NIMA provides complementary learned aesthetics
**Parallelization**: Process in batches of 5-10 images (VLM API rate limits)

**Input Schema**:
```json
{
  "image_id": "string",
  "image_path": "string",
  "metadata": "object"
}
```

**Output Schema**:
```json
{
  "image_id": "string",
  "composition": "integer 1-5",
  "framing": "integer 1-5",
  "lighting": "integer 1-5",
  "subject_interest": "integer 1-5",
  "overall_aesthetic": "integer 1-5",
  "notes": "string"
}
```

**Validation Format**:
```json
{
  "agent": "Aesthetic Assessment",
  "stage": "rating",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

### Agent 4: Visual Comparator
**Role**: Duplicate/Similarity Detection

**System Prompt**:
```
You are an expert in visual similarity analysis using cutting-edge computer vision algorithms.

Detect duplicates and visually similar images using:
1. Perceptual hashing (pHash, dHash, aHash)
2. Feature embedding similarity (CLIP, ResNet, VGG)
3. SSIM (Structural Similarity Index)

Thresholds:
- Duplicate: Hamming distance ≤ 5 OR embedding cosine similarity ≥ 0.98
- Near-duplicate: Hamming distance ≤ 10 OR embedding cosine similarity ≥ 0.95
- Similar: Hamming distance ≤ 15 OR embedding cosine similarity ≥ 0.90

For each similarity group:
1. Select the best image using combined scoring: technical_score * 0.4 + aesthetic_score * 0.6
2. If scores are tied, prefer higher resolution
3. Preserve originals in archive; mark others for removal/deduplication

Handle edge cases: burst shots, bracketed exposures, panorama sequences.
```

**Recommended Model**:
- Primary: CLIP embeddings for semantic similarity
- Secondary: ImageHash library for perceptual hashing
**Rationale**: CLIP captures semantic similarity; perceptual hashing detects pixel-level duplicates
**Parallelization**: Can parallelize pairwise comparisons; use batch embedding generation

**Input Schema**:
```json
{
  "images": [{
    "image_id": "string",
    "image_path": "string",
    "technical_score": "integer",
    "aesthetic_score": "integer",
    "resolution": "integer"
  }]
}
```

**Output Schema**:
```json
[{
  "group_id": "string",
  "image_ids": ["string"],
  "selected_best": "string",
  "similarity_metric": "float",
  "similarity_type": "duplicate|near-duplicate|similar"
}]
```

**Validation Format**:
```json
{
  "agent": "Duplicate Detection",
  "stage": "grouping",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

### Agent 5: Semantic Classifier
**Role**: Image Filtering and Categorization

**System Prompt**:
```
You are a specialist in semantic image classification and filtering using travel photography best practices.

Filtering criteria:
- Minimum technical score: 3/5 (configurable)
- Minimum aesthetic score: 3/5 (configurable)
- Flag images below thresholds but don't delete
- Allow filtering by GPS region, time range, camera settings

Categorization taxonomy for travel photos:
1. By Subject: Landscape, Architecture, People/Portraits, Food, Wildlife, Urban, Cultural
2. By Time: Golden Hour, Blue Hour, Daytime, Night, Sunset/Sunrise
3. By Location: City/Country from GPS or EXIF
4. By Activity: Adventure, Relaxation, Dining, Transportation, Events

Special flags:
- missing_gps: No location data, needs manual tagging
- low_quality: Below technical threshold
- low_aesthetic: Below aesthetic threshold
- uncategorized: Cannot determine category
- manual_review: Ambiguous or edge case

Use VLM for semantic classification when metadata is insufficient.
```

**Recommended Model**:
- Primary: Claude 3.5 Sonnet or GPT-4 Vision for semantic classification
- Secondary: ResNet or EfficientNet fine-tuned on travel photos
**Rationale**: VLMs excel at understanding context and scene types; CNNs provide fast classification
**Parallelization**: Batch classification requests (10-20 images per batch)

**Input Schema**:
```json
{
  "image_id": "string",
  "image_path": "string",
  "metadata": "object",
  "technical_score": "integer",
  "aesthetic_score": "integer",
  "filter_config": {
    "min_technical": "integer",
    "min_aesthetic": "integer"
  }
}
```

**Output Schema**:
```json
{
  "image_id": "string",
  "category": "string",
  "subcategories": ["string"],
  "time_category": "string",
  "location": "string or null",
  "passes_filter": "boolean",
  "flagged": "boolean",
  "flags": ["string"]
}
```

**Validation Format**:
```json
{
  "agent": "Filtering & Categorization",
  "stage": "classification",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

### Agent 6: Caption Writer & Storyteller
**Role**: Caption Generation

**System Prompt**:
```
You are an award-winning travel writer and photo journalist. Generate engaging, informative captions that bring images to life.

Caption levels:
1. CONCISE (1 line, <100 chars): Twitter-style, punchy description
   Example: "Golden sunset over Santorini's iconic blue domes"

2. STANDARD (2-3 lines, 150-250 chars): Instagram-style, engaging narrative
   Example: "As the sun dips below the Aegean Sea, Santorini's famous blue-domed churches glow in golden light. Captured during the magical hour when the island transforms into a photographer's dream."

3. DETAILED (paragraph, 300-500 chars): Editorial-style, comprehensive story
   Example: "This photograph captures the quintessential Santorini experience during golden hour. The iconic blue-domed churches of Oia, with their striking contrast against white-washed walls, are bathed in warm sunset light. Shot at f/8 with ISO 200, the image preserves detail from the shadowed foreground through to the distant caldera. The composition follows the rule of thirds, placing the main dome at the intersection for maximum visual impact. Location: Oia, Santorini, Greece (36.4618° N, 25.3753° E)."

Incorporate:
- Location from GPS or metadata
- Time of day and lighting conditions
- Technical details (camera settings) in detailed captions
- Cultural or historical context
- Emotional resonance and storytelling
- Keywords for searchability

Avoid clichés; be specific and authentic.
```

**Recommended Model**:
- Primary: Claude 3.5 Sonnet (excellent at nuanced writing)
- Alternative: GPT-4 Vision or Gemini 1.5 Pro
**Rationale**: Advanced language models excel at creative, context-aware caption generation
**Parallelization**: Batch process 5-10 images per API call

**Input Schema**:
```json
{
  "image_id": "string",
  "image_path": "string",
  "metadata": "object",
  "technical_assessment": "object",
  "aesthetic_assessment": "object",
  "category": "string"
}
```

**Output Schema**:
```json
{
  "image_id": "string",
  "captions": {
    "concise": "string (<100 chars)",
    "standard": "string (150-250 chars)",
    "detailed": "string (300-500 chars)"
  },
  "keywords": ["string"]
}
```

**Validation Format**:
```json
{
  "agent": "Caption Generation",
  "stage": "writing",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

### Agent 7: Material UI Web Expert
**Role**: User Interface Website Generation

**System Prompt**:
```
You are a senior full-stack developer specializing in Material UI and React. Create a beautiful, responsive photo showcase website.

Requirements:
1. Material UI v5 with modern design system
2. Responsive grid layout (masonry or card grid)
3. Interactive filters: category, location, date range, quality score
4. Image lightbox/modal with full metadata display
5. Statistics dashboard with charts (Chart.js or Recharts)
6. Search functionality (by caption, location, keywords)
7. Sort options: date, quality, aesthetic score, name
8. Export options: selected images, metadata CSV
9. Dark/light theme toggle
10. Mobile-optimized with touch gestures

Technical stack:
- React 18+ with hooks
- Material UI v5
- React Router for navigation
- Context API for state management
- Lazy loading for performance
- TypeScript for type safety

Deliverables:
- Complete React project with package.json
- README.md with setup and deployment instructions
- Sample JSON data file
- Feature documentation
- Environment configuration template
```

**Recommended Approach**: Code generation using templates and best practices
**Rationale**: Web development is deterministic; use proven patterns and libraries
**Parallelization**: N/A (single output artifact)

**Input Schema**:
```json
{
  "images": [{
    "image_id": "string",
    "image_path": "string",
    "metadata": "object",
    "technical_assessment": "object",
    "aesthetic_assessment": "object",
    "category": "object",
    "captions": "object"
  }],
  "statistics": "object from final report"
}
```

**Output Schema**:
```json
{
  "code_folder": "string (path)",
  "readme": "string",
  "sample_data": "string (json path)",
  "feature_doc": "string"
}
```

**Validation Format**:
```json
{
  "agent": "Website Generation",
  "stage": "build",
  "status": "success|warning|error",
  "summary": "string",
  "issues": ["string"]
}
```

---

## Error Handling Schema

All errors logged in structured JSON:

```json
{
  "timestamp": "ISO 8601 datetime",
  "agent": "string",
  "error_type": "string (MetadataError|QualityError|NetworkError|ValidationError|etc)",
  "summary": "string",
  "severity": "info|warning|error|critical",
  "details": "object (optional additional context)"
}
```

---

## Model Recommendation Summary

| Agent | Recommended Model | Model Type | Rationale |
|-------|------------------|------------|-----------|
| Metadata Expert | ExifTool/piexif | Library | Deterministic EXIF parsing, no inference needed |
| Image Quality Analyst | CLIP-IQA / GPT-4V | IQA Model / VLM | Specialized quality metrics + nuanced assessment |
| Visual Curator | Claude 3.5 Sonnet | VLM | Superior aesthetic judgment and nuanced evaluation |
| Visual Comparator | CLIP + ImageHash | Embedding + Hash | Semantic similarity + pixel-level duplicate detection |
| Semantic Classifier | Claude 3.5 Sonnet | VLM | Excellent scene understanding and categorization |
| Caption Writer | Claude 3.5 Sonnet | LLM | Best-in-class creative writing and context awareness |
| Material UI Expert | Code Templates | Framework | React/MUI best practices with TypeScript |

---

## Final Statistics Report Schema

```json
{
  "num_images_ingested": "integer",
  "num_images_flagged_metadata": "integer",
  "average_technical_score": "float",
  "average_aesthetic_score": "float",
  "num_duplicates_found": "integer",
  "num_images_final_selected": "integer",
  "num_images_flagged_for_manual_review": "integer",
  "processing_time_seconds": "float",
  "agent_performance": [{
    "agent": "string",
    "execution_time_seconds": "float",
    "images_processed": "integer",
    "success_rate": "float"
  }],
  "category_distribution": {
    "category_name": "integer count"
  },
  "quality_distribution": {
    "score_1": "integer",
    "score_2": "integer",
    "score_3": "integer",
    "score_4": "integer",
    "score_5": "integer"
  },
  "agent_errors": [{
    "timestamp": "ISO 8601",
    "agent": "string",
    "error_type": "string",
    "summary": "string",
    "severity": "string"
  }],
  "timestamp": "ISO 8601 string"
}
```

---

## Parallelization Strategy

**Parallel Execution Opportunities:**
1. Agent 1 (Metadata): Process all images in parallel (I/O bound)
2. Agent 2 & 3 (Quality + Aesthetic): Can run simultaneously after Agent 1
3. Agent 5 (Filtering) & Agent 6 (Captions): Can run in parallel after Agent 4

**Sequential Dependencies:**
- Agent 4 (Duplicates) requires Agent 2 & 3 outputs
- Agent 6 (Captions) requires all assessment data
- Agent 7 (Website) requires all previous agents' outputs

**Workflow DAG:**
```
Agent 1 (Metadata)
    ├─→ Agent 2 (Quality) ─┐
    └─→ Agent 3 (Aesthetic) ┴→ Agent 4 (Duplicates) ─┬─→ Agent 5 (Filtering) ─┐
                                                       └─→ Agent 6 (Captions) ──┴→ Agent 7 (Website)
```
