"""Helper utilities for Travel Photo Organization Workflow."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config


def save_json(data: Any, output_path: Path, indent: int = 2):
    """
    Save data to JSON file.

    Args:
        data: Data to save
        output_path: Output file path
        indent: JSON indentation
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(input_path: Path) -> Any:
    """
    Load data from JSON file.

    Args:
        input_path: Input file path

    Returns:
        Loaded data
    """
    if not input_path.exists():
        raise FileNotFoundError(f"JSON file not found: {input_path}")

    with open(input_path, 'r') as f:
        return json.load(f)


def get_image_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Get all image files from directory.

    Args:
        directory: Directory to search
        extensions: List of extensions (default: jpg, jpeg, png, heic, raw)

    Returns:
        List of image file paths
    """
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.heic', '.raw', '.cr2', '.nef', '.arw']

    image_files = []
    for ext in extensions:
        image_files.extend(directory.glob(f"**/*{ext}"))
        image_files.extend(directory.glob(f"**/*{ext.upper()}"))

    return sorted(image_files)


def ensure_directories(config: Dict[str, Any]):
    """
    Ensure all required directories exist.

    Args:
        config: Configuration dictionary
    """
    paths = config.get('paths', {})
    for key, path in paths.items():
        if 'output' in key:
            Path(path).mkdir(parents=True, exist_ok=True)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with mean, min, max, median
    """
    if not values:
        return {"mean": 0, "min": 0, "max": 0, "median": 0}

    sorted_values = sorted(values)
    n = len(values)

    return {
        "mean": sum(values) / n,
        "min": sorted_values[0],
        "max": sorted_values[-1],
        "median": sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    }
