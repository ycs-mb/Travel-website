# Low-Level Design (LLD)
## Agent Specifications & Implementation Details

---

## Agent 1: Metadata Extraction

### Purpose
Extract comprehensive EXIF, GPS, and technical metadata from image files with reverse geocoding for GPS coordinates.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | Library-based (deterministic) |
| **I/O** | I/O bound + Network (geocoding API) |
| **Workers** | 4 (from config) |
| **Libraries** | Pillow, piexif, pillow-heif, geopy (Nominatim) |
| **Timeout** | 10 seconds per image |

### Key Features
- ✅ Direct HEIC/HEIF reading (no conversion)
- ✅ Reverse geocoding (GPS → location name)
- ✅ Fallback datetime extraction from filename
- ✅ Comprehensive camera settings extraction

### System Prompt
```
You are a world-class metadata extraction specialist. Your task is to ingest photo files
and extract comprehensive metadata using industry-leading methods.

Extract the following for each image:
- Filename, file size, format
- Capture date/time (EXIF DateTime, DateTimeOriginal, DateTimeDigitized)
- GPS coordinates (latitude, longitude, altitude) with reverse geocoded location
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
    "latitude": 49.398750,
    "longitude": 8.672434,
    "altitude": 115.5,
    "location": "Church of the Holy Spirit, Fischmarkt, Altstadt, Heidelberg, Baden-Württemberg, 69117, Germany"
  },
  "camera_settings": {
    "iso": 200,
    "aperture": "f/2.8",
    "shutter_speed": "1/125s",
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

### Implementation Pattern

```python
from geopy.geocoders import Nominatim
from concurrent.futures import ThreadPoolExecutor, as_completed

class MetadataExtractionAgent:
    SYSTEM_PROMPT = """..."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config['agents']['metadata_extraction']
        self.parallel_workers = self.agent_config.get('parallel_workers', 4)
        
        # Initialize geocoder for reverse geocoding
        self.geolocator = Nominatim(user_agent="travel-photo-workflow")

    def run(self, image_paths: List[Path]) -> Tuple[List[Dict], Dict]:
        """Extract metadata from all images."""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = [executor.submit(self.process_image, path)
                      for path in image_paths]
            results = [f.result() for f in as_completed(futures)]
        return results, validation_summary

    def extract_gps_info(self, exif_data: Dict) -> Dict[str, Optional[float]]:
        """Extract GPS coordinates and reverse geocode to location."""
        gps_info = {
            "latitude": None,
            "longitude": None,
            "altitude": None,
            "location": None
        }
        
        # Extract coordinates from EXIF
        # ... coordinate extraction logic ...
        
        # Reverse geocode to get location name
        if gps_info['latitude'] and gps_info['longitude']:
            try:
                location_obj = self.geolocator.reverse(
                    (gps_info['latitude'], gps_info['longitude']),
                    exactly_one=True,
                    language='en',
                    timeout=10
                )
                if location_obj:
                    gps_info['location'] = location_obj.address
            except Exception as e:
                self.logger.warning(f"Reverse geocoding failed: {e}")
        
        return gps_info
```

---

## Agent 2: Quality Assessment

### Purpose
Evaluate technical quality (sharpness, exposure, noise) using OpenCV algorithms.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | OpenCV-based (algorithmic) |
| **I/O** | CPU bound |
| **Workers** | 2 |
| **Libraries** | OpenCV, NumPy |
| **Timeout** | 30 seconds per image |

### System Prompt
```
You are an elite image quality analyst with expertise in computational photography.
Evaluate each photograph using state-of-the-art quality metrics.

Assess the following technical dimensions:
1. Sharpness/Focus Quality (1-5): Measure edge acuity and blur using Laplacian variance
2. Exposure (1-5): Evaluate histogram distribution, clipping, dynamic range
3. Noise Level (1-5): Detect ISO noise, compression artifacts using patch variance
4. Resolution Adequacy (1-5): Assess if resolution meets modern standards

Provide structured output with scores and detected issues.
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
  "issues": ["slight_noise"],
  "metrics": {
    "blur_variance": 285.5,
    "histogram_clipping_percent": 2.3,
    "snr_db": 28.5
  }
}
```

### Key Algorithms

**Sharpness (Laplacian Variance):**
```python
def assess_sharpness(self, image: np.ndarray) -> tuple[int, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    
    # Score based on variance thresholds
    if variance > 500: score = 5
    elif variance > 300: score = 4
    elif variance > 150: score = 3
    elif variance > 75: score = 2
    else: score = 1
    
    return score, variance
```

**Noise (Patch Variance):**
```python
def assess_noise(self, image: np.ndarray) -> tuple[int, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    patches = extract_smooth_patches(gray)
    variance = np.mean([np.var(patch) for patch in patches])
    
    # Lower variance = less noise = higher score
    if variance < 50: score = 5
    elif variance < 100: score = 4
    elif variance < 200: score = 3
    elif variance < 400: score = 2
    else: score = 1
    
    return score, variance
```

---

## Agent 3: Aesthetic Assessment

### Purpose
Evaluate artistic quality (composition, framing, lighting) using Vertex AI (Gemini Vision).

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | VLM (Vision Language Model) |
| **I/O** | API bound |
| **Workers** | 2 |
| **Model** | Gemini 1.5 Flash (Vertex AI) |
| **Batch Size** | 5 images |
| **Timeout** | 60 seconds per image |
| **Token Tracking** | ✅ Enabled |

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

Provide structured JSON output with scores and brief notes.
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
  "notes": "Excellent golden hour shot with strong compositional elements",
  "token_usage": {
    "prompt_token_count": 312,
    "candidates_token_count": 89,
    "total_token_count": 401
  }
}
```

### Implementation Pattern

```python
from google import genai
from google.genai import types

class AestheticAssessmentAgent:
    def __init__(self, config: Dict, logger: Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config['agents']['aesthetic_assessment']
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        
        # Vertex AI client initialization
        vertex_config = config.get('vertex_ai', {})
        self.client = genai.Client(
            vertexai=True,
            project=vertex_config.get('project'),
            location=vertex_config.get('location')
        )
        self.model_name = vertex_config.get('model', 'gemini-1.5-flash')

    def assess_with_vlm(self, image_path: Path) -> Dict[str, Any]:
        """Assess aesthetics using Vertex AI."""
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        
        # Call Vertex AI
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_text(text=self.SYSTEM_PROMPT),
                types.Part.from_bytes(
                    data=base64.standard_b64decode(image_data),
                    mime_type='image/jpeg'
                )
            ]
        )
        
        # Parse response
        assessment = self._parse_vlm_response(response.text)
        
        # Extract token usage
        if hasattr(response, 'usage_metadata'):
            assessment['token_usage'] = {
                'prompt_token_count': response.usage_metadata.prompt_token_count,
                'candidates_token_count': response.usage_metadata.candidates_token_count,
                'total_token_count': response.usage_metadata.total_token_count
            }
        
        return assessment
```

---

## Agent 4: Filtering & Categorization

### Purpose
Filter by quality thresholds and categorize images by content using Vertex AI, with reasoning for decisions.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | VLM + Rule-based |
| **I/O** | API bound |
| **Workers** | 2 |
| **Model** | Gemini 1.5 Flash (Vertex AI) |
| **Timeout** | 45 seconds per image |
| **Token Tracking** | ✅ Enabled |
| **Reasoning** | ✅ Explains pass/reject |

### Categorization Taxonomy

**By Subject:**
- Landscape, Architecture, People/Portraits, Food, Wildlife, Urban, Cultural, Adventure

**By Time:**
- Golden Hour, Blue Hour, Daytime, Night, Sunset/Sunrise

**By Location:**
- Extracted from GPS reverse geocoding or EXIF

### Filtering Rules with Reasoning

```python
# Construct reasoning
if passes_filter:
    reasoning = f"Passed all criteria. Quality Score: {quality}/{min_quality}, Aesthetic Score: {aesthetic}/{min_aesthetic}."
else:
    reasons = []
    if quality < min_quality:
        reasons.append(f"Quality score ({quality}) below threshold ({min_quality})")
    if aesthetic < min_aesthetic:
        reasons.append(f"Aesthetic score ({aesthetic}) below threshold ({min_aesthetic})")
    reasoning = f"Rejected: {'; '.join(reasons)}."
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
  "reasoning": "Passed all criteria. Quality Score: 4/3, Aesthetic Score: 4/3.",
  "flagged": false,
  "flags": [],
  "token_usage": {
    "prompt_token_count": 189,
    "candidates_token_count": 67,
    "total_token_count": 256
  }
}
```

### Implementation Pattern

```python
def categorize_by_content(self, image_path: Path) -> tuple[str, List[str], dict]:
    """Categorize using Vertex AI with token tracking."""
    # Call Vertex AI
    response = self.client.models.generate_content(
        model=self.model_name,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=media_type)
        ]
    )
    
    # Parse categories
    main_cat, subcats = self._parse_categorization_response(response.text)
    
    # Extract token usage
    token_usage = None
    if hasattr(response, 'usage_metadata'):
        token_usage = {
            'prompt_token_count': response.usage_metadata.prompt_token_count,
            'candidates_token_count': response.usage_metadata.candidates_token_count,
            'total_token_count': response.usage_metadata.total_token_count
        }
    
    return main_cat, subcats, token_usage
```

---

## Agent 5: Caption Generation

### Purpose
Generate multi-level captions (concise/standard/detailed) with keywords using Vertex AI.

### Specifications

| Aspect | Details |
|--------|---------|
| **Type** | VLM (Vision Language Model) |
| **I/O** | API bound |
| **Workers** | 2 |
| **Model** | Gemini 1.5 Flash (Vertex AI) |
| **Timeout** | 45 seconds per image |
| **Token Tracking** | ✅ Enabled |

### System Prompt
```
You are an award-winning travel writer and photo journalist. Generate engaging,
informative captions that bring images to life.

Caption levels:
1. CONCISE (1 line, <100 chars): Twitter-style, punchy description
2. STANDARD (2-3 lines, 150-250 chars): Instagram-style, engaging narrative
3. DETAILED (paragraph, 300-500 chars): Editorial-style, comprehensive story

Incorporate:
- Location from GPS or metadata
- Time of day and lighting conditions
- Technical details (camera settings) in detailed captions
- Cultural or historical context
- Emotional resonance and storytelling
- Keywords for searchability

Respond in JSON format with all three caption levels and keywords array.
```

### Output Schema

```json
{
  "image_id": "img_001",
  "captions": {
    "concise": "Golden sunset over Santorini's iconic blue domes",
    "standard": "As the sun dips below the Aegean Sea, Santorini's famous blue-domed churches glow in golden light, creating the quintessential Greek island moment.",
    "detailed": "This photograph captures the quintessential Santorini experience during golden hour. The iconic blue-domed churches of Oia, with their striking contrast against white-washed walls, are bathed in warm sunset light. Shot at f/2.8 with the Canon EOS R5, the image showcases the romantic beauty that has made this Cycladic island one of the world's most photographed destinations."
  },
  "keywords": ["sunset", "architecture", "mediterranean", "travel", "golden-hour", "greece", "santorini"],
  "token_usage": {
    "prompt_token_count": 567,
    "candidates_token_count": 198,
    "total_token_count": 765
  }
}
```

### Context Integration

The caption agent receives full context from all upstream agents:

```python
def _call_llm_api(self, image_path, metadata, quality, aesthetic, category):
    """Generate captions with full context."""
    # Build comprehensive prompt with all upstream data
    context = f"""
CONTEXT:
- Location: {category.get('location', 'Unknown')}
- Category: {category.get('category', 'Scene')}
- Time: {category.get('time_category', 'Daytime')}
- Quality Score: {quality.get('quality_score', 3)}/5
- Aesthetic Score: {aesthetic.get('overall_aesthetic', 3)}/5
- Camera: {metadata.get('camera_settings', {}).get('camera_model', 'Camera')}
- Settings: ISO {metadata.get('camera_settings', {}).get('iso', 'auto')}, {metadata.get('camera_settings', {}).get('aperture', 'N/A')}
"""
    
    # Call Vertex AI with image and context
    response = self.client.models.generate_content(...)
    
    # Extract captions and token usage
    captions = self._parse_caption_response(response.text)
    if hasattr(response, 'usage_metadata'):
        captions['token_usage'] = {...}
    
    return captions
```

---

## Web Application Integration

### Flask Route Patterns

```python
from flask import Flask, render_template, request, jsonify
import subprocess
from pathlib import Path

app = Flask(__name__)

@app.route('/')
def index():
    """Dashboard with upload and run history."""
    runs = []
    output_dir = Path('output')
    
    # Get all timestamped run directories
    for run_dir in sorted(output_dir.glob('2*'), reverse=True):
        status = 'completed'  # Check if workflow.log shows completion
        runs.append({
            'timestamp': run_dir.name,
            'status': status,
            'link': f'/report/{run_dir.name}'
        })
    
    return render_template('index.html', runs=runs)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle photo upload and trigger workflow."""
    files = request.files.getlist('photos')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save uploaded files
    upload_dir = Path('uploads') / timestamp
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        file.save(upload_dir / file.filename)
    
    # Trigger orchestrator in background
    subprocess.Popen([
        'python', 'orchestrator.py',
        '--input', str(upload_dir),
        '--output', f'output/{timestamp}'
    ])
    
    return jsonify({'run_id': timestamp, 'status': 'running'})

@app.route('/report/<timestamp>')
def view_report(timestamp):
    """Load and display detailed report."""
    report_dir = Path('output') / timestamp / 'reports'
    
    # Load all agent outputs
    images_data = {}
    
    # Load metadata
    with open(report_dir / 'metadata_extraction_output.json') as f:
        metadata = json.load(f)
        for img in metadata:
            images_data[img['image_id']] = {'metadata': img}
    
    # Load quality
    with open(report_dir / 'quality_assessment_output.json') as f:
        quality = json.load(f)
        for img in quality:
            if img['image_id'] in images_data:
                images_data[img['image_id']]['quality'] = img
    
    # Load aesthetic
    with open(report_dir / 'aesthetic_assessment_output.json') as f:
        aesthetic = json.load(f)
        for img in aesthetic:
            if img['image_id'] in images_data:
                images_data[img['image_id']]['aesthetic'] = img
    
    # Load filtering
    with open(report_dir / 'filtering_categorization_output.json') as f:
        filtering = json.load(f)
        for img in filtering:
            if img['image_id'] in images_data:
                images_data[img['image_id']]['filtering'] = img
    
    # Load captions
    with open(report_dir / 'caption_generation_output.json') as f:
        captions = json.load(f)
        for img in captions:
            if img['image_id'] in images_data:
                images_data[img['image_id']]['captions'] = img.get('captions', {})
    
    return render_template('report.html', images=images_data, timestamp=timestamp)
```

---

## Validation Schemas

### Token Usage Validation

```python
TOKEN_USAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt_token_count": {"type": "integer", "minimum": 0},
        "candidates_token_count": {"type": "integer", "minimum": 0},
        "total_token_count": {"type": "integer", "minimum": 0}
    },
    "required": ["total_token_count"]
}
```

### Agent Output Validation

```python
AGENT_SCHEMAS = {
    'metadata_extraction': {
        "type": "object",
        "required": ["image_id", "filename", "gps", "camera_settings"],
        "properties": {
            "image_id": {"type": "string"},
            "filename": {"type": "string"},
            "gps": {
                "type": "object",
                "properties": {
                    "latitude": {"type": ["number", "null"]},
                    "longitude": {"type": ["number", "null"]},
                    "location": {"type": ["string", "null"]}  # Reverse geocoded
                }
            }
        }
    },
    'aesthetic_assessment': {
        "type": "object",
        "required": ["image_id", "overall_aesthetic"],
        "properties": {
            "token_usage": TOKEN_USAGE_SCHEMA  # Optional but validated if present
        }
    },
    # ... similar for all agents
}
```

---

## Configuration Integration

### Complete config.yaml Structure

```yaml
# Paths
paths:
  input_images: sample_images/
  output_dir: output/
  upload_dir: uploads/

# Vertex AI Configuration (REQUIRED)
vertex_ai:
  project: "your-google-cloud-project-id"
  location: "us-central1"  # or your preferred region  
  model: "gemini-1.5-flash"

# Agent-specific settings
agents:
  metadata_extraction:
    enabled: true
    parallel_workers: 4

  quality_assessment:
    enabled: true
    parallel_workers: 2

  aesthetic_assessment:
    enabled: true
    parallel_workers: 2
    batch_size: 5

  filtering_categorization:
    enabled: true
    parallel_workers: 2

  caption_generation:
    enabled: true
    parallel_workers: 2

# Quality thresholds
thresholds:
  min_technical_quality: 3
  min_aesthetic_quality: 3

# Error handling
error_handling:
  max_retries: 3
  continue_on_error: true
```

---

## Error Handling Patterns

### Vertex AI Error Handling

```python
def assess_with_vlm(self, image_path: Path) -> Dict[str, Any]:
    """Assess with comprehensive error handling."""
    try:
        response = self.client.models.generate_content(...)
        
        # Validate response
        if not response.text:
            raise ValueError("Empty response from Vertex AI")
        
        # Parse and validate
        result = self._parse_vlm_response(response.text)
        
        # Extract token usage
        if hasattr(response, 'usage_metadata'):
            result['token_usage'] = {...}
        
        return result
        
    except Exception as e:
        log_error(
            self.logger,
            "Aesthetic Assessment",
            "APIError",
            f"Vertex AI call failed: {str(e)}",
            "error"
        )
        return {
            "composition": 3,
            "framing": 3,
            "lighting": 3,
            "subject_interest": 3,
            "overall_aesthetic": 3,
            "notes": f"API error: {str(e)}"
        }
```

---

## Utility Modules

### Reverse Geocoding (`utils/reverse_geocoding.py`)

**Purpose:** Convert GPS coordinates to human-readable location names using OpenStreetMap's Nominatim service.

**Specifications:**

| Aspect | Details |
|--------|---------|
| **Service** | Nominatim (OpenStreetMap) |
| **Caching** | Local JSON file cache |
| **Rate Limiting** | 1 request/second (Nominatim TOS) |
| **Cache TTL** | 24 hours (configurable) |
| **Fallback** | Graceful degradation if service unavailable |

**Implementation:**

```python
class ReverseGeocoder:
    def __init__(self, config: Dict, logger: logging.Logger):
        self.logger = logger
        self.config = config.get('reverse_geocoding', {})

        # Configuration
        self.enabled = self.config.get('enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 24)
        self.timeout = self.config.get('timeout_seconds', 5)
        self.user_agent = self.config.get('user_agent', 'TravelPhotoAnalysis/1.0')

        # Initialize geocoder
        if self.enabled:
            self.geolocator = Nominatim(user_agent=self.user_agent, timeout=self.timeout)

        # Load cache
        self.cache_file = Path(__file__).parent.parent / 'cache' / 'geocoding_cache.json'
        self.cache = self._load_cache() if self.cache_enabled else {}

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds

    def get_location_name(self, lat: float, lon: float) -> Optional[str]:
        """Convert GPS coordinates to location name with caching."""
        if not self.enabled:
            return None

        # Check cache first
        cache_key = self._get_cache_key(lat, lon)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            return self.cache[cache_key]['location']

        # Rate limiting
        self._rate_limit()

        try:
            # Call Nominatim API
            location = self.geolocator.reverse(f"{lat}, {lon}")
            location_name = location.address if location else None

            # Cache the result
            if self.cache_enabled and location_name:
                self.cache[cache_key] = {
                    'location': location_name,
                    'timestamp': datetime.now().isoformat()
                }
                self._save_cache()

            return location_name

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            log_error(self.logger, "ReverseGeocoding", "ServiceError", str(e), "warning")
            return None
```

**Cache Format:**

```json
{
  "49.3988,8.6724": {
    "location": "Church of the Holy Spirit, Fischmarkt, Altstadt, Heidelberg...",
    "timestamp": "2024-12-24T10:30:00"
  }
}
```

**Benefits:**
- ✅ Free service (no API key required)
- ✅ Persistent caching (reduces API calls)
- ✅ Rate limiting (respects Nominatim TOS)
- ✅ Graceful fallback (continues if service down)
- ✅ Cache expiry (ensures fresh data)

---

## API Server Integration

### FastAPI Server (`api/fastapi_server.py`)

**Purpose:** Expose all 5 agents as RESTful API endpoints for programmatic access.

**Specifications:**

| Aspect | Details |
|--------|---------|
| **Framework** | FastAPI 0.100+ |
| **Port** | 8000 (configurable) |
| **Authentication** | API key (X-API-Key header) |
| **Documentation** | Auto-generated (Swagger UI, ReDoc) |
| **CORS** | Enabled (configurable origins) |

**Endpoints:**

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/analyze")
async def analyze_full_pipeline(
    file: UploadFile = File(...),
    api_key: str = Header(..., alias="X-API-Key")
):
    """Run complete 5-agent pipeline on uploaded image."""
    # 1. Validate API key
    # 2. Save uploaded file
    # 3. Run all agents sequentially
    # 4. Return combined results with token usage
    pass

@app.post("/analyze/metadata")
async def analyze_metadata(file: UploadFile, api_key: str = Header(...)):
    """Run Agent 1 only."""
    pass

@app.post("/analyze/quality")
async def analyze_quality(file: UploadFile, api_key: str = Header(...)):
    """Run Agents 1+2."""
    pass

@app.post("/analyze/aesthetic")
async def analyze_aesthetic(file: UploadFile, api_key: str = Header(...)):
    """Run Agents 1+3."""
    pass

@app.post("/analyze/filter")
async def analyze_filter(file: UploadFile, api_key: str = Header(...)):
    """Run Agents 1+2+3+4."""
    pass

@app.post("/analyze/caption")
async def analyze_caption(file: UploadFile, api_key: str = Header(...)):
    """Run complete pipeline (Agents 1+2+3+4+5)."""
    pass
```

**Response Format:**

```json
{
  "image_id": "img_20241224_103045",
  "filename": "vacation.jpg",
  "metadata": {...},
  "quality": {...},
  "aesthetic": {...},
  "filtering": {...},
  "caption": {...},
  "token_usage": {
    "total_tokens": 2847,
    "estimated_cost_usd": 0.0031
  },
  "processing_time_seconds": 4.2
}
```

---

## Batch Processing Tool

### CSV Exporter (`batch-run-photo-json2csv/main.py`)

**Purpose:** Process folders of images and export results to CSV for spreadsheet analysis.

**Specifications:**

| Aspect | Details |
|--------|---------|
| **Input** | Folder path (with optional recursion) |
| **Output** | CSV file + errors CSV |
| **API** | Calls FastAPI server for each image |
| **Progress** | Real-time progress bar |
| **Error Handling** | Separate error CSV file |

**Implementation Pattern:**

```python
def process_folder(folder_path: Path, output_csv: Path, api_url: str, api_key: str, recursive: bool = False):
    """Process all images in folder and export to CSV."""

    # 1. Find all image files
    image_files = find_images(folder_path, recursive)

    # 2. Process each image via API
    results = []
    errors = []

    for img_path in tqdm(image_files, desc="Processing"):
        try:
            # Call FastAPI /analyze endpoint
            response = requests.post(
                f"{api_url}/analyze",
                files={'file': open(img_path, 'rb')},
                headers={'X-API-Key': api_key},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            # Flatten for CSV
            flat_result = flatten_result(result)
            results.append(flat_result)

        except Exception as e:
            errors.append({'filename': str(img_path), 'error': str(e)})

    # 3. Write results to CSV
    write_csv(results, output_csv)

    # 4. Write errors to separate CSV
    if errors:
        write_csv(errors, output_csv.with_suffix('.errors.csv'))

    return len(results), len(errors)
```

**CSV Columns:**

```csv
filename,date_taken,camera_model,gps_latitude,gps_longitude,location,quality_score,sharpness,exposure,noise,aesthetic_score,composition,lighting,framing,category,passes_filter,caption_concise,caption_standard,keywords,token_usage,estimated_cost
```

---

## Docker Deployment

### Containerization

**API Container (`docker/api.Dockerfile`):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server
CMD ["uv", "run", "uvicorn", "api.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose (`docker-compose.yml`):**

```yaml
services:
  api:
    build:
      context: .
      dockerfile: docker/api.Dockerfile
    container_name: photo-api
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/keys.json
      - API_KEY=${API_KEY:-your-secret-api-key-here}
    volumes:
      - ./keys.json:/app/secrets/keys.json:ro
      - ./config.yaml:/app/config.yaml:ro
      - ./output:/app/output
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

## Related Documentation

**For high-level overview, see [HLD.md](./HLD.md)**
**For architecture diagrams, see [UML_DIAGRAMS.md](./UML_DIAGRAMS.md)**
**For workflow visualization, see [ACTIVITY_DIAGRAM.md](./ACTIVITY_DIAGRAM.md)**
**For quick setup, see [QUICKSTART.md](./QUICKSTART.md)**
**For Docker deployment, see [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)**
**For batch processing, see [BATCH_PROCESSING.md](./BATCH_PROCESSING.md)**
**For API documentation, see [API_README.md](./API_README.md)**
