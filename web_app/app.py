import os
import json
import threading
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify

# Import the orchestrator
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator import TravelPhotoOrchestrator

app = Flask(__name__)

# Configuration
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = BASE_DIR / 'output'
REPORTS_DIR = OUTPUT_DIR / 'reports'
UPLOAD_DIR = BASE_DIR / 'uploads'

# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

# Global state for run status
current_run = {
    'status': 'idle', # idle, running, completed, failed
    'start_time': None,
    'end_time': None,
    'log': [],
    'report_path': None,
    'run_id': None
}

def run_workflow_thread(input_path):
    """Runs the workflow in a separate thread."""
    global current_run
    current_run['status'] = 'running'
    current_run['start_time'] = datetime.now().isoformat()
    current_run['log'] = []
    
    try:
        # Initialize orchestrator with override for input images
        orchestrator = TravelPhotoOrchestrator(
            config_overrides={'paths': {'input_images': str(input_path)}}
        )
        
        # Run workflow
        report = orchestrator.run_workflow()
        
        # Update state
        current_run['status'] = 'completed'
        current_run['end_time'] = datetime.now().isoformat()
        
        # Find the latest report path
        latest_dir = max([d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name.startswith('20')], key=os.path.getmtime)
        report_path = latest_dir / 'reports' / 'final_report.json'
        
        if report_path.exists():
             current_run['report_path'] = str(report_path)
             current_run['run_id'] = latest_dir.name
        
    except Exception as e:
        current_run['status'] = 'failed'
        current_run['log'].append(str(e))
        print(f"Workflow failed: {e}")

@app.route('/')
def index():
    """Home page."""
    # Get list of past runs
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
    # We need to find which upload directory corresponds to this run
    # The timestamp in the URL is the OUTPUT timestamp
    # But we need the INPUT upload directory
    # For simplicity, we can try to find the file in the uploads directory recursively
    # OR, better, we can look at the metadata in the report to find the original path
    
    # Let's try to find the file in the uploads directory
    # Since we don't store the mapping between output run and input upload dir easily here without DB
    # We will rely on the fact that we need to serve the file that was processed.
    
    # Option 1: Check if it's in sample_images (legacy support)
    sample_img = BASE_DIR / 'sample_images' / filename
    if sample_img.exists():
        return send_from_directory(BASE_DIR / 'sample_images', filename)
        
    # Option 2: Search in uploads
    # This is a bit hacky but works for this simple app
    for upload_run in UPLOAD_DIR.iterdir():
        if upload_run.is_dir():
            target_file = upload_run / filename
            if target_file.exists():
                return send_from_directory(upload_run, filename)
                
    return "Image not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
