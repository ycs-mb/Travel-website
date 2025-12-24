# Batch CSV Processing Guide

Process folders of travel photos and export results to CSV format for analysis in spreadsheets.

---

## Overview

The batch CSV tool (`batch-run-photo-json2csv`) allows you to:
- Process entire folders of images automatically
- Search recursively through subdirectories
- Export results to CSV for Excel/Google Sheets
- Track progress in real-time
- Log errors to separate CSV file

**Architecture:**
```
┌─────────────────────────────────────┐
│ Your Photo Folder                   │
│  ├── vacation/                      │
│  │   ├── IMG_001.jpg               │
│  │   └── IMG_002.jpg               │
│  ├── IMG_003.jpg                   │
│  └── ...                            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Batch Processor (main.py)           │
│  - Scans for images                 │
│  - Sends to FastAPI server          │
│  - Collects responses               │
│  - Writes to CSV                    │
└──────────────┬──────────────────────┘
               │ HTTP REST API
               ▼
┌─────────────────────────────────────┐
│ FastAPI Server (localhost:8000)     │
│  - Runs 5-agent pipeline            │
│  - Returns JSON results             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ CSV Output Files                    │
│  - results.csv (successful)         │
│  - results_errors.csv (failed)      │
└─────────────────────────────────────┘
```

---

## Prerequisites

### 1. FastAPI Server Running

The batch tool requires the FastAPI server to be running:

```bash
# Terminal 1: Start the API server
cd /path/to/Travel-website
./scripts/start_api.sh

# Verify it's running
curl http://localhost:8000/health
```

### 2. API Key

Generate an API key if you haven't already:

```bash
./scripts/generate_api_key.sh
```

This will create/update `.env` with a secure API key.

### 3. Install Dependencies

```bash
cd batch-run-photo-json2csv

# Using pip
pip install -r requirements.txt

# Or using uv
uv pip install -r requirements.txt
```

---

## Quick Start

### Basic Usage

```bash
cd batch-run-photo-json2csv

python main.py /path/to/photos output_results.csv --api-key YOUR_API_KEY
```

### Using Environment Variable

```bash
# Set API key in environment
export API_KEY=your_api_key_here

# Run without --api-key flag
python main.py /path/to/photos output_results.csv
```

### Recursive Mode

Search all subdirectories for images:

```bash
python main.py /path/to/photos output_results.csv --recursive
```

### Custom API URL

If your API is on a different host/port:

```bash
python main.py /path/to/photos output.csv \
  --api-url http://192.168.1.100:8000 \
  --api-key YOUR_API_KEY
```

---

## Command-Line Options

```bash
python main.py [OPTIONS] INPUT_DIR OUTPUT_CSV
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `INPUT_DIR` | Yes | Directory containing images |
| `OUTPUT_CSV` | Yes | Path for output CSV file |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--api-url` | `-u` | `http://localhost:8000` | FastAPI server URL |
| `--api-key` | `-k` | From env `API_KEY` | API authentication key |
| `--recursive` | `-r` | `False` | Search subdirectories |

---

## Output Format

### Success CSV (`output_results.csv`)

Contains all successfully processed images with columns:

| Column | Description | Example |
|--------|-------------|---------|
| `filename` | Full path to image | `/photos/IMG_001.jpg` |
| `date_taken` | Date from EXIF | `2024-07-15` |
| `camera_model` | Camera used | `iPhone 14 Pro` |
| `gps_latitude` | GPS latitude | `37.7749` |
| `gps_longitude` | GPS longitude | `-122.4194` |
| `location` | Reverse geocoded location | `San Francisco, CA, USA` |
| `quality_score` | Technical quality (1-5) | `4` |
| `sharpness` | Sharpness score (1-5) | `4` |
| `exposure` | Exposure score (1-5) | `5` |
| `noise` | Noise score (1-5) | `3` |
| `aesthetic_score` | Overall aesthetic (1-5) | `5` |
| `composition` | Composition score (1-5) | `4` |
| `lighting` | Lighting score (1-5) | `5` |
| `framing` | Framing score (1-5) | `4` |
| `category` | Primary category | `Landscape` |
| `passes_filter` | Pass/reject decision | `True` |
| `caption_concise` | Short caption | `Golden Gate Bridge at sunset` |
| `caption_standard` | Standard caption | `Majestic view of the Golden Gate Bridge...` |
| `keywords` | Comma-separated tags | `bridge,sunset,landscape,water` |
| `token_usage` | Total API tokens used | `1247` |
| `estimated_cost` | Estimated cost (USD) | `0.0042` |

### Error CSV (`output_results_errors.csv`)

Contains failed images with columns:

| Column | Description |
|--------|-------------|
| `filename` | Path to image that failed |
| `error` | Error message |

---

## Examples

### Example 1: Single Folder

```bash
# Process all images in a folder
python main.py ~/Pictures/Vacation2024 vacation_analysis.csv

# Output:
# Processing: 100%|████████████████████| 150/150 [12:30<00:00, 5.00s/image]
# ✓ Successfully processed: 147 images
# ✗ Failed: 3 images
# Results saved to: vacation_analysis.csv
# Errors saved to: vacation_analysis_errors.csv
```

### Example 2: Recursive Search

```bash
# Process entire photo library with subfolders
python main.py ~/Pictures vacation_full.csv --recursive

# Scans:
# ~/Pictures/Vacation2023/
# ~/Pictures/Vacation2024/Europe/
# ~/Pictures/Vacation2024/Asia/
# ~/Pictures/Random/
# ... etc
```

### Example 3: Remote API Server

```bash
# Use API server on different machine
python main.py /photos results.csv \
  --api-url http://192.168.1.100:8000 \
  --api-key abc123def456
```

### Example 4: Integration with uv

```bash
# Run with uv (if installed in parent project)
cd batch-run-photo-json2csv
uv run python main.py /photos output.csv
```

---

## Output Analysis

### Opening in Spreadsheet Applications

**Excel:**
1. Open Excel
2. File → Open → Select `output_results.csv`
3. Data should auto-import with proper columns

**Google Sheets:**
1. Open Google Sheets
2. File → Import → Upload → Select `output_results.csv`
3. Import settings: Detect automatically
4. Click "Import data"

### Useful Analyses

**1. Filter High-Quality Images:**
```
Filter: quality_score >= 4 AND aesthetic_score >= 4
```

**2. Group by Category:**
```
Create Pivot Table:
Rows: category
Values: COUNT(filename)
```

**3. Find Most Expensive Images:**
```
Sort by: estimated_cost (descending)
```

**4. Location-Based Analysis:**
```
Filter: location IS NOT EMPTY
Group by: location
Count images per location
```

**5. Budget Analysis:**
```
Sum: estimated_cost
Average: estimated_cost / COUNT(*)
```

---

## Performance

### Processing Speed

| Images | Time | Rate |
|--------|------|------|
| 10 | ~1 min | ~6s/image |
| 50 | ~5 min | ~6s/image |
| 100 | ~10 min | ~6s/image |
| 500 | ~50 min | ~6s/image |

*Times vary based on:*
- Image size and complexity
- API server hardware
- Network latency
- Vertex AI response times

### Cost Estimates

For 100 images (with optimizations enabled):
- **Token usage:** ~200K-400K tokens
- **Estimated cost:** $0.15-$0.45 USD
- **Per-image cost:** ~$0.002-0.004 USD

See [TOKEN_OPTIMIZATION.md](./TOKEN_OPTIMIZATION.md) for reducing costs.

---

## Troubleshooting

### Issue: "Connection refused" Error

**Problem:** Can't connect to API server

**Solution:**
```bash
# Verify API server is running
curl http://localhost:8000/health

# If not running, start it:
cd /path/to/Travel-website
./scripts/start_api.sh

# Wait for "Application startup complete" message
```

### Issue: "Unauthorized" Error

**Problem:** Invalid or missing API key

**Solution:**
```bash
# Generate new API key
cd /path/to/Travel-website
./scripts/generate_api_key.sh

# Copy the key and use it:
python main.py /photos output.csv --api-key YOUR_NEW_KEY
```

### Issue: "No images found"

**Problem:** No supported images in directory

**Solution:**
```bash
# Check supported formats
ls /path/to/photos/*.{jpg,jpeg,png,heic,heif}

# Try recursive mode
python main.py /photos output.csv --recursive
```

### Issue: Slow Processing

**Problem:** Taking too long to process

**Solutions:**

1. **Reduce image sizes** (edit `config.yaml` in main project):
```yaml
vertex_ai:
  optimization:
    max_image_dimension: 768  # Lower = faster, but less accurate
```

2. **Process subset first**:
```bash
# Test with small subset
mkdir /tmp/test_photos
cp /photos/*.jpg /tmp/test_photos/ | head -10
python main.py /tmp/test_photos test_output.csv
```

3. **Check API server logs**:
```bash
# In terminal where start_api.sh is running
# Look for errors or warnings
```

### Issue: High Costs

**Problem:** Token usage is too expensive

**Solution:** Enable optimizations in main project `config.yaml`:

```yaml
vertex_ai:
  optimization:
    enable_caching: true                # Cache results
    max_image_dimension: 1024           # Resize images
    skip_captions_for_rejected: true    # Skip bad images
    use_concise_prompts: true           # Shorter prompts
```

See [TOKEN_OPTIMIZATION.md](./TOKEN_OPTIMIZATION.md) for details.

---

## Advanced Usage

### Custom Processing Script

```python
import requests
import csv
from pathlib import Path

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

def process_image(image_path):
    """Send image to API and get results."""
    with open(image_path, 'rb') as f:
        response = requests.post(
            f"{API_URL}/analyze",
            files={'file': f},
            headers={'X-API-Key': API_KEY}
        )
    return response.json()

# Process images
results = []
for img_path in Path('/photos').glob('*.jpg'):
    try:
        result = process_image(img_path)
        results.append(result)
        print(f"✓ {img_path.name}")
    except Exception as e:
        print(f"✗ {img_path.name}: {e}")

# Write to CSV
with open('results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
```

### Parallel Processing

For faster processing, modify `main.py` to use ThreadPoolExecutor:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_batch(image_paths, max_workers=5):
    """Process multiple images in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_image, path): path
            for path in image_paths
        }

        for future in as_completed(futures):
            path = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {path}: {e}")

    return results
```

**Warning:** Be mindful of API rate limits and server capacity.

---

## Integration with Other Tools

### Excel VBA Macro

```vba
' Import and analyze CSV in Excel
Sub ImportPhotoAnalysis()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets.Add

    ' Import CSV
    With ws.QueryTables.Add(Connection:="TEXT;C:\path\to\output.csv", _
                            Destination:=ws.Range("A1"))
        .TextFileParseType = xlDelimited
        .TextFileCommaDelimiter = True
        .Refresh
    End With

    ' Add conditional formatting for quality scores
    ws.Range("H2:H1000").FormatConditions.AddColorScale ColorScaleType:=3
End Sub
```

### Google Sheets Apps Script

```javascript
// Auto-import CSV from Google Drive
function importPhotoAnalysis() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var file = DriveApp.getFilesByName('vacation_analysis.csv').next();
  var csvData = Utilities.parseCsv(file.getBlob().getDataAsString());

  sheet.getRange(1, 1, csvData.length, csvData[0].length).setValues(csvData);

  // Add conditional formatting
  var qualityRange = sheet.getRange('H2:H');
  var rule = SpreadsheetApp.newConditionalFormatRule()
    .setGradientMaxpoint("#00FF00")
    .setGradientMinpoint("#FF0000")
    .setRanges([qualityRange])
    .build();
  sheet.setConditionalFormatRules([rule]);
}
```

### Python Data Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv('vacation_analysis.csv')

# Summary statistics
print(f"Total images: {len(df)}")
print(f"Passed filter: {df['passes_filter'].sum()}")
print(f"Average quality: {df['quality_score'].mean():.2f}")
print(f"Total cost: ${df['estimated_cost'].sum():.2f}")

# Plot quality distribution
df['quality_score'].hist(bins=5)
plt.xlabel('Quality Score')
plt.ylabel('Count')
plt.title('Image Quality Distribution')
plt.show()

# Group by category
category_counts = df['category'].value_counts()
print("\nImages by category:")
print(category_counts)
```

---

## Related Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - General setup guide
- **[API_README.md](./API_README.md)** - FastAPI server documentation
- **[TOKEN_OPTIMIZATION.md](./TOKEN_OPTIMIZATION.md)** - Reducing API costs
- **[DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)** - Production deployment

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review FastAPI logs where `start_api.sh` is running
3. Test with single image first: `python main.py /path/to/one_photo test.csv`
4. Check that Vertex AI credentials are configured correctly

---

**Happy batch processing!** 📊📷
