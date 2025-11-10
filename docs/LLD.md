# Low-Level Design (LLD)
## Agent Specifications & Implementation Details

---

## Agent 1: Metadata Extraction

### Purpose
Extract comprehensive EXIF, GPS, and technical metadata from image files.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | Library-based (deterministic) |
| **I/O** | I/O bound |
| **Workers** | 4 (from config) |
| **Model** | ExifTool / piexif / Pillow |
| **Timeout** | 10 seconds per image |

### System Prompt
```
You are a world-class metadata extraction specialist. Your task is to ingest photo files
and extract comprehensive metadata using industry-leading methods.

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

### Input Schema

```json
{
  "image_paths": [
    "path/to/image1.jpg",
    "path/to/image2.png"
  ]
}
```

### Output Schema

```json
{
  "image_id": "img_001",
  "filename": "vacation_photo.jpg",
  "file_size_bytes": 2048576,
  "format": "JPEG",
  "dimensions": {
    "width": 4000,
    "height": 3000
  },
  "capture_datetime": "2024-06-15T14:30:45Z",
  "gps": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "altitude": 15.5
  },
  "camera_settings": {
    "iso": 200,
    "aperture": "f/2.8",
    "shutter_speed": "1/125",
    "focal_length": "50mm",
    "camera_model": "Canon EOS R5",
    "lens_model": "RF 50mm F1.2"
  },
  "exif_raw": {
    "Make": "Canon",
    "Model": "EOS R5",
    "ColorSpace": "RGB"
  },
  "flags": []
}
```

### Validation Schema

```json
{
  "agent": "Metadata Extraction",
  "stage": "ingestion",
  "status": "success|warning|error",
  "summary": "Extracted metadata from 150/150 images",
  "issues": []
}
```

### Implementation Pattern

```python
class MetadataExtractionAgent:
    SYSTEM_PROMPT = "..."

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config['agents']['metadata_extraction']
        self.parallel_workers = self.agent_config.get('parallel_workers', 4)

    def run(self, image_paths: List[Path]) -> Tuple[List[Dict], Dict]:
        """Extract metadata from all images."""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = [executor.submit(self.process_image, path)
                      for path in image_paths]
            results = [f.result() for f in as_completed(futures)]
        return results, validation_summary

    def process_image(self, image_path: Path) -> Dict[str, Any]:
        """Extract metadata from single image."""
        try:
            # Use Pillow + piexif for EXIF data
            img = Image.open(image_path)
            exif_data = img._getexif() if hasattr(img, '_getexif') else {}

            # Parse GPS from EXIF
            gps = self._extract_gps(exif_data)

            # Parse camera settings
            settings = self._extract_camera_settings(exif_data)

            result = {
                'image_id': self._generate_image_id(image_path),
                'filename': image_path.name,
                'dimensions': {'width': img.width, 'height': img.height},
                'gps': gps,
                'camera_settings': settings,
                'flags': []
            }

            is_valid, error = validate_agent_output('metadata_extraction', result)
            return result
        except Exception as e:
            log_error(self.logger, "Metadata Extraction", "ProcessingError", str(e), "error")
            return default_result
```

---

## Agent 2: Quality Assessment

### Purpose
Evaluate technical quality (sharpness, exposure, noise) of images.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | ML Model + VLM |
| **I/O** | CPU bound |
| **Workers** | 2 |
| **Models** | CLIP-IQA / MUSIQ / GPT-4 Vision |
| **Timeout** | 30 seconds per image |

### System Prompt
```
You are an elite image quality analyst with expertise in computational photography.
Evaluate each photograph using state-of-the-art quality metrics.

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

### Input Schema

```json
{
  "image_id": "img_001",
  "image_path": "path/to/image.jpg",
  "metadata": {
    "dimensions": {"width": 4000, "height": 3000},
    "camera_model": "Canon EOS R5"
  }
}
```

### Output Schema

```json
{
  "image_id": "img_001",
  "quality_score": 4,
  "sharpness": 4,
  "exposure": 5,
  "noise": 3,
  "resolution": 5,
  "issues": [],
  "metrics": {
    "blur_variance": 0.85,
    "histogram_clipping_percent": 2.3,
    "snr_db": 28.5
  }
}
```

### Validation Schema

```json
{
  "agent": "Technical Assessment",
  "stage": "scoring",
  "status": "success|warning|error",
  "summary": "Assessed quality of 150/150 images",
  "issues": []
}
```

---

## Agent 3: Aesthetic Assessment

### Purpose
Evaluate artistic quality (composition, framing, lighting) using vision models.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | VLM (Vision Language Model) |
| **I/O** | API bound |
| **Workers** | 2 |
| **Models** | Claude 3.5 Sonnet / GPT-4 Vision / Gemini 1.5 |
| **Batch Size** | 5-10 images |
| **Timeout** | 60 seconds per image |

### System Prompt
```
You are a world-renowned photo curator and aesthetic expert with decades of
experience in fine art and travel photography.

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

Consider genre-specific criteria for travel photography: sense of place,
cultural context, human interest.
```

### Input Schema

```json
{
  "image_id": "img_001",
  "image_path": "path/to/image.jpg",
  "metadata": {
    "capture_datetime": "2024-06-15T14:30:45Z",
    "gps": {"latitude": 40.7128, "longitude": -74.0060}
  }
}
```

### Output Schema

```json
{
  "image_id": "img_001",
  "composition": 5,
  "framing": 4,
  "lighting": 5,
  "subject_interest": 4,
  "overall_aesthetic": 4,
  "notes": "Excellent golden hour shot with strong compositional elements"
}
```

### Validation Schema

```json
{
  "agent": "Aesthetic Assessment",
  "stage": "rating",
  "status": "success|warning|error",
  "summary": "Rated aesthetics of 150/150 images",
  "issues": []
}
```

---

## Agent 4: Filtering & Categorization

### Purpose
Filter by quality thresholds and categorize images by content, location, time.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | VLM + Rule-based |
| **I/O** | API bound |
| **Workers** | 2 |
| **Models** | Claude 3.5 Sonnet / GPT-4 Vision |
| **Batch Size** | 10-20 images |
| **Timeout** | 45 seconds per batch |

### Categorization Taxonomy

**By Subject:**
- Landscape, Architecture, People/Portraits, Food, Wildlife, Urban, Cultural

**By Time:**
- Golden Hour, Blue Hour, Daytime, Night, Sunset/Sunrise

**By Location:**
- City/Country from GPS or EXIF

**By Activity:**
- Adventure, Relaxation, Dining, Transportation, Events

### Filtering Rules

```
if (technical_score < min_technical_quality):
    passes_filter = False
    flags.append("low_quality")

if (aesthetic_score < min_aesthetic_quality):
    passes_filter = False
    flags.append("low_aesthetic")

if (not has_gps_data):
    flags.append("missing_gps")

if (cannot_determine_category):
    flags.append("uncategorized")
```

### Input Schema

```json
{
  "image_id": "img_001",
  "image_path": "path/to/image.jpg",
  "metadata": {...},
  "technical_score": 4,
  "aesthetic_score": 4,
  "filter_config": {
    "min_technical": 3,
    "min_aesthetic": 3
  }
}
```

### Output Schema

```json
{
  "image_id": "img_001",
  "category": "Landscape",
  "subcategories": ["Mountain", "Sunset"],
  "time_category": "Golden Hour",
  "location": "Yosemite, California, USA",
  "passes_filter": true,
  "flagged": false,
  "flags": []
}
```

---

## Agent 5: Caption Generation

### Purpose
Generate multi-level captions (concise/standard/detailed) with keywords.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | LLM + VLM |
| **I/O** | API bound |
| **Workers** | 2 |
| **Models** | Claude 3.5 Sonnet / GPT-4 Vision |
| **Batch Size** | 5-10 images |
| **Timeout** | 45 seconds per image |

### Caption Levels

| Level | Format | Length | Example |
|-------|--------|--------|---------|
| **Concise** | Twitter-style | <100 chars | "Golden sunset over Santorini's blue domes" |
| **Standard** | Instagram-style | 150-250 chars | "As the sun dips below the Aegean Sea, Santorini's famous blue-domed churches glow in golden light..." |
| **Detailed** | Editorial-style | 300-500 chars | "This photograph captures the quintessential Santorini experience during golden hour. The iconic blue-domed churches of Oia, with their striking contrast against white-washed walls, are bathed in warm sunset light..." |

### Input Schema

```json
{
  "image_id": "img_001",
  "image_path": "path/to/image.jpg",
  "metadata": {...},
  "technical_assessment": {...},
  "aesthetic_assessment": {...},
  "category": "Landscape"
}
```

### Output Schema

```json
{
  "image_id": "img_001",
  "captions": {
    "concise": "Golden sunset over iconic blue domes",
    "standard": "Santorini's famous blue-domed churches glow in golden hour light...",
    "detailed": "This photograph captures the quintessential Santorini experience..."
  },
  "keywords": ["sunset", "architecture", "mediterranean", "travel", "golden-hour"]
}
```

---

## Validation Schemas

### Agent Output Validation

```python
AGENT_SCHEMAS = {
    'metadata_extraction': {
        "type": "object",
        "required": ["image_id", "filename", "gps", "camera_settings"],
        "properties": {
            "image_id": {"type": "string"},
            "filename": {"type": "string"},
            "dimensions": {"type": "object"},
            "gps": {
                "type": "object",
                "properties": {
                    "latitude": {"type": ["number", "null"]},
                    "longitude": {"type": ["number", "null"]}
                }
            },
            "flags": {"type": "array"}
        }
    },
    # ... similar for all agents
}
```

### Validation Function Pattern

```python
def validate_agent_output(agent_key: str, output: Dict) -> Tuple[bool, str]:
    """Validate agent output against schema."""
    schema = AGENT_SCHEMAS[agent_key]
    try:
        jsonschema.validate(output, schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, str(e)
```

---

## Error Handling Patterns

### Try-Catch Template

```python
def process_image(self, image_path: Path) -> Dict[str, Any]:
    """Process with structured error handling."""
    try:
        # Core processing logic
        result = {...}

        # Validate output
        is_valid, error_msg = validate_agent_output(self.agent_key, result)
        if not is_valid:
            log_error(self.logger, self.agent_name, "ValidationError",
                     error_msg, "error")
            return self.default_result()

        return result

    except APIError as e:
        log_error(self.logger, self.agent_name, "APIError",
                 str(e), "error", {"api": "gemini", "status": e.status})
        return self.default_result()

    except Exception as e:
        log_error(self.logger, self.agent_name, "ProcessingError",
                 str(e), "error")
        return self.default_result()
```

### Default Result Pattern

```python
@staticmethod
def default_result(image_id: str) -> Dict[str, Any]:
    """Return placeholder result on error."""
    return {
        "image_id": image_id,
        "quality_score": 0,
        "aesthetic_score": 0,
        "error": "Processing failed",
        "flags": ["processing_error"]
    }
```

---

## Configuration Integration

### Agent Config Access Pattern

```python
class Agent:
    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.agent_config = config['agents']['agent_key']

        # Extract settings
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        self.batch_size = self.agent_config.get('batch_size', 10)
        self.model = self.agent_config.get('model', 'default')
        self.timeout_seconds = self.agent_config.get('timeout_seconds', 30)

        # API config if needed
        if self.agent_config.get('uses_api'):
            self.api_config = config['api'][self.agent_config['api_provider']]
```

### config.yaml Structure

```yaml
agents:
  metadata_extraction:
    enabled: true
    parallel_workers: 4
    model: "pillow"

  quality_assessment:
    enabled: true
    parallel_workers: 2
    model: "clip-iqa"
    timeout_seconds: 30

  aesthetic_assessment:
    enabled: true
    parallel_workers: 2
    model: "claude-3.5-sonnet"
    uses_api: true
    api_provider: "anthropic"
    batch_size: 5
    timeout_seconds: 60
```

---

**For high-level overview, see [HLD.md](./HLD.md)**
**For architecture diagrams, see [UML_DIAGRAMS.md](./UML_DIAGRAMS.md)**
**For workflow visualization, see [ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)**
**For quick setup, see [QUICKSTART.md](./QUICKSTART.md)**
