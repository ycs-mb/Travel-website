"""
Flask Web App for Photo Analysis

This web app provides a UI for uploading and analyzing travel photos.
It calls the FastAPI server (photo-api) for analysis instead of running agents directly.
"""

import os
import json
import threading
import shutil
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify

app = Flask(__name__)

# Configuration
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = BASE_DIR / 'output'
UPLOAD_DIR = BASE_DIR / 'uploads'

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "r1JQVhAR2UejKbc4nK5sjSjeHiZIFMNMUbnAlD6O2wc")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}

# Global state for run status
current_run = {
    'status': 'idle',  # idle, running, completed, failed
    'start_time': None,
    'end_time': None,
    'log': [],
    'report_path': None,
    'run_id': None,
    'progress': 0,
    'total_images': 0,
    'processed_images': 0
}


def run_workflow_thread(input_path: Path):
    """
    Runs the workflow by calling the FastAPI server for each image.
    Results are saved to the output directory in the same format as the orchestrator.
    """
    global current_run
    current_run['status'] = 'running'
    current_run['start_time'] = datetime.now().isoformat()
    current_run['log'] = []
    current_run['progress'] = 0

    try:
        # Create output directory for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = OUTPUT_DIR / timestamp / 'reports'
        run_output_dir.mkdir(parents=True, exist_ok=True)

        # Find all image files
        image_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]

        current_run['total_images'] = len(image_files)
        current_run['log'].append(f"Found {len(image_files)} images to process")

        # Results containers
        all_results = []
        metadata_results = []
        quality_results = []
        aesthetic_results = []
        filtering_results = []
        caption_results = []

        # Process each image via API
        for idx, image_file in enumerate(image_files):
            current_run['log'].append(f"Processing: {image_file.name}")
            current_run['processed_images'] = idx + 1
            current_run['progress'] = int((idx + 1) / len(image_files) * 100)

            try:
                # Call the API
                with open(image_file, 'rb') as f:
                    response = requests.post(
                        f"{API_URL}/api/v1/analyze/image",
                        headers={"x-api-key": API_KEY},
                        files={"file": (image_file.name, f, "image/jpeg")},
                        timeout=120
                    )

                if response.status_code == 200:
                    result = response.json()
                    image_id = image_file.stem

                    # Store full result
                    all_results.append(result)

                    # Extract and store individual agent results
                    # Metadata
                    if result.get('metadata'):
                        meta = result['metadata']
                        metadata_results.append(meta)
                    else:
                        metadata_results.append({
                            'image_id': image_id,
                            'filename': image_file.name
                        })

                    # Aesthetic scores
                    if result.get('aesthetic'):
                        aes = result['aesthetic']
                        aesthetic_results.append({
                            'image_id': image_id,
                            'composition': aes.get('composition', 0),
                            'framing': aes.get('framing', 0),
                            'lighting': aes.get('lighting', 0),
                            'subject_interest': aes.get('subject_interest', 0),
                            'overall_aesthetic': aes.get('overall_aesthetic', 0),
                            'notes': aes.get('notes', '')
                        })

                    # Quality
                    if result.get('quality'):
                        qual = result['quality']
                        quality_results.append(qual)
                    else:
                        quality_results.append({
                            'image_id': image_id,
                            'quality_score': 4
                        })

                    # Filtering
                    if result.get('filtering'):
                        filt = result['filtering']
                        filtering_results.append({
                            'image_id': image_id,
                            'category': filt.get('category', 'Uncategorized'),
                            'subcategories': filt.get('subcategories', []),
                            'time_category': filt.get('time_category', ''),
                            'location': filt.get('location', ''),
                            'passes_filter': filt.get('passes_filter', True),
                            'flagged': filt.get('flagged', False),
                            'flags': filt.get('flags', []),
                            'reasoning': filt.get('reasoning', '')
                        })

                    # Captions
                    if result.get('caption'):
                        cap = result['caption']
                        caption_results.append({
                            'image_id': image_id,
                            'captions': {
                                'concise': cap.get('concise', ''),
                                'standard': cap.get('standard', ''),
                                'detailed': cap.get('detailed', ''),
                                'keywords': cap.get('keywords', [])
                            },
                            'keywords': cap.get('keywords', [])
                        })

                    current_run['log'].append(f"✓ {image_file.name} processed successfully")
                else:
                    current_run['log'].append(f"✗ {image_file.name} failed: {response.status_code}")

            except requests.exceptions.Timeout:
                current_run['log'].append(f"✗ {image_file.name} timed out")
            except Exception as e:
                current_run['log'].append(f"✗ {image_file.name} error: {str(e)}")

        # Save results to JSON files (matching orchestrator output format)
        with open(run_output_dir / 'metadata_extraction_output.json', 'w') as f:
            json.dump(metadata_results, f, indent=2)

        with open(run_output_dir / 'quality_assessment_output.json', 'w') as f:
            json.dump(quality_results, f, indent=2)

        with open(run_output_dir / 'aesthetic_assessment_output.json', 'w') as f:
            json.dump(aesthetic_results, f, indent=2)

        with open(run_output_dir / 'filtering_categorization_output.json', 'w') as f:
            json.dump(filtering_results, f, indent=2)

        with open(run_output_dir / 'caption_generation_output.json', 'w') as f:
            json.dump(caption_results, f, indent=2)

        # Create final report
        final_report = {
            'workflow_timestamp': timestamp,
            'num_images_ingested': len(image_files),
            'num_images_final_selected': len([f for f in filtering_results if f.get('passes_filter', True)]),
            'processing_method': 'api',
            'api_url': API_URL,
            'results': all_results
        }

        with open(run_output_dir / 'final_report.json', 'w') as f:
            json.dump(final_report, f, indent=2)

        # Update state
        current_run['status'] = 'completed'
        current_run['end_time'] = datetime.now().isoformat()
        current_run['report_path'] = str(run_output_dir / 'final_report.json')
        current_run['run_id'] = timestamp
        current_run['log'].append(f"Workflow completed: {len(image_files)} images processed")

    except Exception as e:
        current_run['status'] = 'failed'
        current_run['log'].append(f"Workflow failed: {str(e)}")
        print(f"Workflow failed: {e}")


@app.route('/')
def index():
    """Home page with upload form and run history."""
    runs = []
    if OUTPUT_DIR.exists():
        for d in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith('20'):
                report_file = d / 'reports' / 'final_report.json'
                if report_file.exists():
                    try:
                        with open(report_file, 'r') as f:
                            data = json.load(f)
                            runs.append({
                                'timestamp': d.name,
                                'images': data.get('num_images_ingested', 0),
                                'selected': data.get('num_images_final_selected', 0),
                                'path': str(d)
                            })
                    except:
                        pass

    return render_template('index.html', runs=runs, current_run=current_run)


@app.route('/run', methods=['POST'])
def trigger_run():
    """Trigger a new workflow run with uploaded files."""
    if current_run['status'] == 'running':
        return jsonify({'status': 'error', 'message': 'Workflow already running'}), 400

    # Create a unique directory for this upload
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_upload_dir = UPLOAD_DIR / timestamp
    run_upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = request.files.getlist('photos')

    if not uploaded_files or uploaded_files[0].filename == '':
        return redirect(url_for('index'))

    for file in uploaded_files:
        if file.filename:
            file.save(run_upload_dir / file.filename)

    thread = threading.Thread(target=run_workflow_thread, args=(run_upload_dir,))
    thread.start()

    return redirect(url_for('index'))


@app.route('/status')
def get_status():
    """Get current run status (for polling)."""
    return jsonify(current_run)


@app.route('/report/<timestamp>')
def view_report(timestamp):
    """View a specific report."""
    report_dir = OUTPUT_DIR / timestamp / 'reports'
    final_report_path = report_dir / 'final_report.json'

    if not final_report_path.exists():
        return "Report not found", 404

    with open(final_report_path, 'r') as f:
        report = json.load(f)

    # Load detailed image data
    images_data = {}

    # Load metadata
    try:
        with open(report_dir / 'metadata_extraction_output.json', 'r') as f:
            metadata = json.load(f)
            for img in metadata:
                images_data[img['image_id']] = {'metadata': img}
    except:
        pass

    # Load captions
    try:
        with open(report_dir / 'caption_generation_output.json', 'r') as f:
            captions = json.load(f)
            for img in captions:
                if img['image_id'] in images_data:
                    images_data[img['image_id']]['captions'] = img.get('captions', {})
    except:
        pass

    # Load filtering
    try:
        with open(report_dir / 'filtering_categorization_output.json', 'r') as f:
            filtering = json.load(f)
            for img in filtering:
                if img['image_id'] in images_data:
                    images_data[img['image_id']]['filtering'] = img
                    images_data[img['image_id']]['category'] = img.get('category', 'Uncategorized')
                    images_data[img['image_id']]['passes_filter'] = img.get('passes_filter', False)
    except:
        pass

    # Load quality
    try:
        with open(report_dir / 'quality_assessment_output.json', 'r') as f:
            quality = json.load(f)
            for img in quality:
                if img['image_id'] in images_data:
                    images_data[img['image_id']]['quality'] = img
                    images_data[img['image_id']]['quality_score'] = img.get('quality_score', 0)
    except:
        pass

    # Load aesthetic
    try:
        with open(report_dir / 'aesthetic_assessment_output.json', 'r') as f:
            aesthetic = json.load(f)
            for img in aesthetic:
                if img['image_id'] in images_data:
                    images_data[img['image_id']]['aesthetic'] = img
                    images_data[img['image_id']]['aesthetic_score'] = img.get('overall_aesthetic', 0)
    except:
        pass

    return render_template('report.html', report=report, images=images_data, timestamp=timestamp)


@app.route('/images/<timestamp>/<path:filename>')
def serve_image(timestamp, filename):
    """Serve images from the upload directory corresponding to the run."""
    # Check sample_images first (legacy support)
    sample_img = BASE_DIR / 'sample_images' / filename
    if sample_img.exists():
        return send_from_directory(BASE_DIR / 'sample_images', filename)

    # Search in uploads
    for upload_run in UPLOAD_DIR.iterdir():
        if upload_run.is_dir():
            target_file = upload_run / filename
            if target_file.exists():
                return send_from_directory(upload_run, filename)

    return "Image not found", 404


if __name__ == '__main__':
    print(f"API URL: {API_URL}")
    print(f"Starting Flask web app on port 5001...")
    app.run(debug=True, port=5001)
