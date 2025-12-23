import os
import sys
from pathlib import Path
from typing import List, Optional
import time

import pandas as pd
import requests
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

app = typer.Typer(help="Batch process photos using the Photo Analysis API")
console = Console()

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.JPG', '.JPEG', '.PNG', '.WEBP', '.HEIC'}

def flatten_response(filename: str, path: str, data: dict) -> dict:
    """Flatten the API response into a single row for CSV"""
    row = {
        'filename': filename,
        'path': path,
        'job_id': data.get('job_id'),
        'status': data.get('status'),
        'processing_time': data.get('processing_time_seconds'),
        'total_cost': data.get('total_cost_usd', 0.0)
    }

    # Aesthetic
    aesthetic = data.get('aesthetic', {})
    if aesthetic:
        row.update({
            'aesthetic_score': aesthetic.get('overall_aesthetic'),
            'aesthetic_composition': aesthetic.get('composition'),
            'aesthetic_framing': aesthetic.get('framing'),
            'aesthetic_lighting': aesthetic.get('lighting'),
            'aesthetic_subject': aesthetic.get('subject_interest'),
            'aesthetic_notes': aesthetic.get('notes')
        })

    # Filtering/Categorization
    filtering = data.get('filtering', {})
    if filtering:
        row.update({
            'category': filtering.get('category'),
            'subcategories': ", ".join(filtering.get('subcategories', [])),
            'time': filtering.get('time_category'),
            'location': filtering.get('location'),
            'passes_filter': filtering.get('passes_filter'),
            'is_flagged': filtering.get('flagged'),
            'reasoning': filtering.get('reasoning')
        })

    # Caption
    caption = data.get('caption', {})
    if caption:
        row.update({
            'caption_concise': caption.get('concise'),
            'caption_standard': caption.get('standard'),
            'caption_detailed': caption.get('detailed'),
            'keywords': ", ".join(caption.get('keywords', []))
        })

    return row

@app.command()
def process(
    input_dir: Path = typer.Argument(..., help="Directory containing images to process", exists=True, file_okay=False, dir_okay=True),
    output_csv: Path = typer.Argument(..., help="Output CSV file path"),
    api_url: str = typer.Option("http://localhost:8000", help="Base URL of the API"),
    api_key: str = typer.Option(..., envvar="API_KEY", help="API Key for authentication"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively search for images"),
    concurrency: int = typer.Option(1, help="Number of concurrent requests (not fully implemented in this sync version, kept for future)")
):
    """
    Batch process images from a directory and save results to a CSV file.
    """
    
    # 1. Find images
    if recursive:
        files = [p for p in input_dir.rglob("*") if p.suffix in SUPPORTED_EXTENSIONS]
    else:
        files = [p for p in input_dir.glob("*") if p.suffix in SUPPORTED_EXTENSIONS]
    
    if not files:
        console.print(f"[red]No images found in {input_dir}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]Found {len(files)} images to process[/green]")

    results = []
    errors = []
    
    # Analyze endpoint
    endpoint = f"{api_url.rstrip('/')}/api/v1/analyze/image"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Processing images...", total=len(files))
        
        for file_path in files:
            progress.update(task, description=f"Processing {file_path.name}")
            
            try:
                with open(file_path, 'rb') as f:
                    # Construct request
                    files_payload = {'file': (file_path.name, f, 'image/jpeg')} # Mime type validation might be needed but requests handles usually
                    headers = {'x-api-key': api_key}
                    
                    # We request all agents
                    params = [('agents', 'metadata'), ('agents', 'quality'), ('agents', 'aesthetic'), ('agents', 'filtering'), ('agents', 'caption')]
                    
                    response = requests.post(endpoint, files=files_payload, headers=headers, params=params, timeout=60)
                    
                    if response.status_code == 200:
                        data = response.json()
                        flat_data = flatten_response(file_path.name, str(file_path.absolute()), data)
                        results.append(flat_data)
                    else:
                        error_msg = f"API Error {response.status_code}: {response.text}"
                        errors.append({'filename': file_path.name, 'path': str(file_path), 'error': error_msg})
                        # console.print(f"[yellow]Failed {file_path.name}: {error_msg}[/yellow]")

            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                errors.append({'filename': file_path.name, 'path': str(file_path), 'error': error_msg})
                # console.print(f"[red]Error {file_path.name}: {error_msg}[/red]")
            
            progress.advance(task)

    # Save Results
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)
        console.print(f"[bold green]Successfully saved results for {len(results)} images to {output_csv}[/bold green]")
    else:
        console.print("[yellow]No successful results to save.[/yellow]")

    # Save Errors
    if errors:
        error_csv = output_csv.with_name(f"{output_csv.stem}_errors.csv")
        pd.DataFrame(errors).to_csv(error_csv, index=False)
        console.print(f"[bold red]{len(errors)} errors occurred. Details saved to {error_csv}[/bold red]")

if __name__ == "__main__":
    app()
