"""Direct HEIC file reader without conversion using pillow-heif."""

import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

from PIL import Image
import cv2


def register_heic_support():
    """Register HEIC support with Pillow."""
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        logging.debug("HEIC support registered with Pillow")
    except ImportError:
        logging.warning(
            "pillow-heif not installed. HEIC files will not be readable. "
            "Install with: pip install pillow-heif"
        )
    except Exception as e:
        logging.warning(f"Failed to register HEIC support: {e}")


def is_heic_file(image_path: Path) -> bool:
    """
    Check if file is HEIC/HEIF format.

    Args:
        image_path: Path to image file

    Returns:
        True if file is HEIC/HEIF format
    """
    return image_path.suffix.lower() in ['.heic', '.heif', '.hic']


def open_heic_with_pil(image_path: Path) -> Image.Image:
    """
    Open HEIC file directly with PIL/Pillow (via pillow-heif).

    Args:
        image_path: Path to HEIC file

    Returns:
        PIL Image object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be opened as HEIC
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if not is_heic_file(image_path):
        raise ValueError(f"File is not HEIC format: {image_path}")

    try:
        # Register HEIC support
        register_heic_support()

        # Open HEIC file directly with PIL
        img = Image.open(image_path)
        logging.debug(f"Opened HEIC file: {image_path.name}")
        return img

    except Exception as e:
        raise ValueError(f"Failed to open HEIC file {image_path.name}: {e}")


def read_heic_as_numpy(image_path: Path) -> np.ndarray:
    """
    Read HEIC file directly and return as numpy array (for OpenCV).

    Args:
        image_path: Path to HEIC file

    Returns:
        numpy array in BGR format (OpenCV compatible)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be opened as HEIC
    """
    try:
        # Open HEIC with PIL
        img = open_heic_with_pil(image_path)

        # Convert to RGB if needed
        if img.mode != 'RGB':
            if img.mode in ('RGBA', 'LA', 'P'):
                # Handle alpha channel by creating white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            else:
                img = img.convert('RGB')

        # Convert to numpy array
        img_array = np.array(img)

        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        logging.debug(f"Converted HEIC to numpy array: {image_path.name}")
        return img_bgr

    except Exception as e:
        raise ValueError(f"Failed to read HEIC as numpy array {image_path.name}: {e}")


def get_heic_dimensions(image_path: Path) -> Tuple[int, int]:
    """
    Get dimensions of HEIC image without full decode.

    Args:
        image_path: Path to HEIC file

    Returns:
        Tuple of (width, height)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If cannot read dimensions
    """
    try:
        img = open_heic_with_pil(image_path)
        width, height = img.size
        img.close()
        return width, height
    except Exception as e:
        raise ValueError(f"Failed to get HEIC dimensions: {e}")


def get_heic_exif(image_path: Path) -> dict:
    """
    Extract EXIF data from HEIC file directly.

    Args:
        image_path: Path to HEIC file

    Returns:
        Dictionary with EXIF data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If cannot read EXIF
    """
    try:
        img = open_heic_with_pil(image_path)
        exif_data = img.getexif()
        img.close()

        if not exif_data:
            logging.debug(f"No EXIF data in HEIC: {image_path.name}")
            return {}

        # Convert to dictionary
        exif_dict = dict(exif_data)
        logging.debug(f"Extracted {len(exif_dict)} EXIF tags from HEIC: {image_path.name}")
        return exif_dict

    except Exception as e:
        logging.warning(f"Failed to extract EXIF from HEIC: {e}")
        return {}


def heic_to_pil(image_path: Path) -> Image.Image:
    """
    Read HEIC directly and return PIL Image (for metadata agents).

    Args:
        image_path: Path to HEIC file

    Returns:
        PIL Image object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If cannot open HEIC
    """
    return open_heic_with_pil(image_path)


def heic_to_opencv(image_path: Path) -> np.ndarray:
    """
    Read HEIC directly and return OpenCV compatible array.

    Args:
        image_path: Path to HEIC file

    Returns:
        numpy array in BGR format

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If cannot read HEIC
    """
    return read_heic_as_numpy(image_path)
