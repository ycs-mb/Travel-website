"""Agent 1: Metadata Extraction - Extract EXIF and metadata from images."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
from geopy.geocoders import Nominatim

from utils.logger import log_error, log_info
from utils.validation import validate_agent_output, create_validation_summary


class MetadataExtractionAgent:
    """
    Agent 1: Metadata Expert

    System Prompt:
    You are a world-class metadata extraction specialist. Your task is to ingest
    photo files and extract comprehensive metadata using industry-leading methods.

    Extract: filename, file size, format, capture date/time, GPS coordinates,
    camera settings, full EXIF data.

    Flag images with missing or corrupted metadata for review.
    """

    SYSTEM_PROMPT = """
    You are a world-class metadata extraction specialist. Your task is to ingest
    photo files and extract comprehensive metadata using industry-leading methods.

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
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Metadata Extraction Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('metadata_extraction', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 4)
        # Initialize geocoder for reverse geocoding
        self.geolocator = Nominatim(user_agent="travel-photo-workflow")

    def _dms_to_decimal(self, degrees: float, minutes: float, seconds: float) -> float:
        """
        Convert degrees, minutes, seconds to decimal degrees.

        Args:
            degrees: Degree value
            minutes: Minute value
            seconds: Second value

        Returns:
            Decimal degrees
        """
        return degrees + minutes / 60.0 + seconds / 3600.0

    def _get_location_address(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Get location address from coordinates using reverse geocoding.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Location address or None
        """
        try:
            location = self.geolocator.reverse((latitude, longitude), exactly_one=True, language='en', timeout=10)
            return location.address if location else None
        except Exception as e:
            self.logger.warning(f"Reverse geocoding failed for ({latitude}, {longitude}): {e}")
            return None

    def extract_gps_info(self, exif_data: Dict) -> Dict[str, Optional[float]]:
        """Extract GPS coordinates from EXIF data with reverse geocoding."""
        gps_info = {
            "latitude": None,
            "longitude": None,
            "altitude": None,
            "location": None
        }

        if 'GPS' not in exif_data:
            return gps_info

        try:
            gps = exif_data['GPS']

            # Extract latitude
            if 'GPSLatitude' in gps and 'GPSLatitudeRef' in gps:
                lat = gps['GPSLatitude']
                lat_ref = gps['GPSLatitudeRef']

                # Convert DMS to decimal using proper method
                try:
                    # Handle both tuple and regular number formats
                    if isinstance(lat[0], (tuple, list)):
                        lat_deg = lat[0][0] / lat[0][1] if lat[0][1] != 0 else lat[0][0]
                        lat_min = lat[1][0] / lat[1][1] if lat[1][1] != 0 else lat[1][0]
                        lat_sec = lat[2][0] / lat[2][1] if lat[2][1] != 0 else lat[2][0]
                    else:
                        lat_deg, lat_min, lat_sec = lat[0], lat[1], lat[2]

                    latitude = self._dms_to_decimal(float(lat_deg), float(lat_min), float(lat_sec))
                    if lat_ref == 'S':
                        latitude = -latitude
                    gps_info['latitude'] = round(latitude, 6)
                except Exception as e:
                    self.logger.warning(f"Error converting latitude: {e}")

            # Extract longitude
            if 'GPSLongitude' in gps and 'GPSLongitudeRef' in gps:
                lon = gps['GPSLongitude']
                lon_ref = gps['GPSLongitudeRef']

                try:
                    # Handle both tuple and regular number formats
                    if isinstance(lon[0], (tuple, list)):
                        lon_deg = lon[0][0] / lon[0][1] if lon[0][1] != 0 else lon[0][0]
                        lon_min = lon[1][0] / lon[1][1] if lon[1][1] != 0 else lon[1][0]
                        lon_sec = lon[2][0] / lon[2][1] if lon[2][1] != 0 else lon[2][0]
                    else:
                        lon_deg, lon_min, lon_sec = lon[0], lon[1], lon[2]

                    longitude = self._dms_to_decimal(float(lon_deg), float(lon_min), float(lon_sec))
                    if lon_ref == 'W':
                        longitude = -longitude
                    gps_info['longitude'] = round(longitude, 6)
                except Exception as e:
                    self.logger.warning(f"Error converting longitude: {e}")

            # Extract altitude
            if 'GPSAltitude' in gps:
                try:
                    alt = gps['GPSAltitude']
                    if isinstance(alt, (tuple, list)):
                        gps_info['altitude'] = round(alt[0] / alt[1] if alt[1] != 0 else alt[0], 2)
                    else:
                        gps_info['altitude'] = round(float(alt), 2)
                except Exception as e:
                    self.logger.warning(f"Error extracting altitude: {e}")

            # Get location address from coordinates using reverse geocoding
            if gps_info['latitude'] is not None and gps_info['longitude'] is not None:
                try:
                    location = self._get_location_address(gps_info['latitude'], gps_info['longitude'])
                    if location:
                        gps_info['location'] = location
                        self.logger.info(f"Reverse geocoding found: {location}")
                except Exception as e:
                    self.logger.warning(f"Error performing reverse geocoding: {e}")

        except Exception as e:
            self.logger.warning(f"Error extracting GPS data: {e}")

        return gps_info

    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to degrees."""
        d, m, s = value
        if isinstance(d, tuple):
            d = d[0] / d[1] if d[1] != 0 else d[0]
        if isinstance(m, tuple):
            m = m[0] / m[1] if m[1] != 0 else m[0]
        if isinstance(s, tuple):
            s = s[0] / s[1] if s[1] != 0 else s[0]
        return d + (m / 60.0) + (s / 3600.0)

    def extract_camera_settings(self, exif_data: Dict) -> Dict[str, Any]:
        """Extract camera settings from EXIF data."""
        settings = {
            "iso": None,
            "aperture": None,
            "shutter_speed": None,
            "focal_length": None,
            "camera_model": None,
            "lens_model": None
        }

        try:
            # ISO
            if 'ISOSpeedRatings' in exif_data:
                settings['iso'] = exif_data['ISOSpeedRatings']

            # Aperture (F-number)
            if 'FNumber' in exif_data:
                f_num = exif_data['FNumber']
                if isinstance(f_num, tuple):
                    settings['aperture'] = f"f/{f_num[0] / f_num[1]:.1f}"
                else:
                    settings['aperture'] = f"f/{f_num}"

            # Shutter speed
            if 'ExposureTime' in exif_data:
                exp = exif_data['ExposureTime']
                if isinstance(exp, tuple):
                    if exp[0] < exp[1]:
                        settings['shutter_speed'] = f"{exp[0]}/{exp[1]}s"
                    else:
                        settings['shutter_speed'] = f"{exp[0] / exp[1]}s"
                else:
                    settings['shutter_speed'] = f"{exp}s"

            # Focal length
            if 'FocalLength' in exif_data:
                focal = exif_data['FocalLength']
                if isinstance(focal, tuple):
                    settings['focal_length'] = f"{focal[0] / focal[1]:.0f}mm"
                else:
                    settings['focal_length'] = f"{focal}mm"

            # Camera model
            if 'Model' in exif_data:
                settings['camera_model'] = exif_data['Model']

            # Lens model
            if 'LensModel' in exif_data:
                settings['lens_model'] = exif_data['LensModel']

        except Exception as e:
            self.logger.warning(f"Error extracting camera settings: {e}")

        return settings

    def extract_datetime(self, exif_data: Dict) -> Optional[str]:
        """Extract capture datetime from EXIF data."""
        datetime_fields = ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']

        for field in datetime_fields:
            if field in exif_data:
                try:
                    dt_str = exif_data[field]
                    # Convert EXIF datetime format to ISO 8601
                    dt = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                    return dt.isoformat() + 'Z'
                except Exception as e:
                    self.logger.warning(f"Error parsing datetime from {field}: {e}")

        return None

    def process_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a single image.

        Args:
            image_path: Path to image file

        Returns:
            Metadata dictionary
        """
        flags = []
        exif_raw = {}

        try:
            # Basic file info
            file_size = image_path.stat().st_size

            # Open image and get basic info
            with Image.open(image_path) as img:
                width, height = img.size
                img_format = img.format

                # Try to extract EXIF data using PIL first
                exif_data = img.getexif()

                # If PIL fails, try using piexif
                if not exif_data:
                    try:
                        exif_dict = piexif.load(str(image_path))
                        # Convert piexif format to standard format
                        for ifd_name in ("0th", "Exif", "GPS", "1st"):
                            ifd = exif_dict[ifd_name]
                            for tag_id, value in ifd.items():
                                tag_name = piexif.TAGS[ifd_name][tag_id]["name"]
                                try:
                                    if isinstance(value, bytes):
                                        value = value.decode('utf-8', errors='ignore')
                                    exif_raw[tag_name] = str(value)[:200]
                                except Exception:
                                    exif_raw[tag_name] = str(value)[:200]
                    except Exception as e:
                        self.logger.warning(f"piexif extraction failed for {image_path.name}: {e}")

                # Process PIL EXIF data
                if exif_data:
                    # Convert EXIF to readable format
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)

                        try:
                            # Handle different value types
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode('utf-8', errors='ignore')
                                except Exception:
                                    value = str(value)[:100]
                            else:
                                value = str(value)[:200]

                            exif_raw[tag] = value

                            # Handle GPS data separately
                            if tag == 'GPSInfo':
                                gps_data = {}
                                for gps_tag_id, gps_value in value.items():
                                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                    gps_data[gps_tag] = gps_value
                                exif_raw['GPS'] = gps_data
                        except Exception as e:
                            self.logger.warning(f"Error processing EXIF tag {tag}: {e}")

                if not exif_data and not exif_raw:
                    flags.append("missing_exif")
                    log_error(
                        self.logger,
                        "Metadata Extraction",
                        "MissingEXIF",
                        f"No EXIF data found in {image_path.name}",
                        "warning"
                    )

            # Extract structured metadata
            gps_info = self.extract_gps_info(exif_raw)
            camera_settings = self.extract_camera_settings(exif_raw)
            capture_datetime = self.extract_datetime(exif_raw)

            # Flag missing data
            if not capture_datetime:
                flags.append("missing_datetime")

            if not any(gps_info.values()):
                flags.append("missing_gps")

            # Create metadata object
            metadata = {
                "image_id": image_path.stem,
                "filename": image_path.name,
                "file_size_bytes": file_size,
                "format": img_format,
                "dimensions": {
                    "width": width,
                    "height": height
                },
                "capture_datetime": capture_datetime,
                "gps": gps_info,
                "camera_settings": camera_settings,
                "exif_raw": exif_raw,
                "flags": flags
            }

            # Validate output
            is_valid, error_msg = validate_agent_output("metadata_extraction", metadata)
            if not is_valid:
                log_error(
                    self.logger,
                    "Metadata Extraction",
                    "ValidationError",
                    f"Validation failed for {image_path.name}: {error_msg}",
                    "error"
                )
                flags.append("validation_failed")
                metadata["flags"] = flags

            return metadata

        except Exception as e:
            log_error(
                self.logger,
                "Metadata Extraction",
                "ProcessingError",
                f"Failed to process {image_path.name}: {str(e)}",
                "error"
            )
            return {
                "image_id": image_path.stem,
                "filename": image_path.name,
                "file_size_bytes": 0,
                "format": "unknown",
                "dimensions": {"width": 0, "height": 0},
                "capture_datetime": None,
                "gps": {"latitude": None, "longitude": None, "altitude": None, "location": None},
                "camera_settings": {},
                "exif_raw": {},
                "flags": ["processing_error"]
            }

    def run(self, image_paths: List[Path]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run metadata extraction on all images.

        Args:
            image_paths: List of image file paths

        Returns:
            Tuple of (metadata_list, validation_summary)
        """
        log_info(self.logger, f"Starting metadata extraction for {len(image_paths)} images", "Metadata Extraction")

        metadata_list = []
        issues = []

        # Process images in parallel
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            future_to_path = {executor.submit(self.process_image, path): path for path in image_paths}

            for future in as_completed(future_to_path):
                try:
                    metadata = future.result()
                    metadata_list.append(metadata)

                    if metadata.get('flags'):
                        issues.append(f"{metadata['filename']}: {', '.join(metadata['flags'])}")

                except Exception as e:
                    path = future_to_path[future]
                    error_msg = f"Failed to extract metadata from {path.name}: {str(e)}"
                    issues.append(error_msg)
                    log_error(
                        self.logger,
                        "Metadata Extraction",
                        "ExecutionError",
                        error_msg,
                        "error"
                    )

        # Create validation summary
        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")
        summary = f"Extracted metadata from {len(metadata_list)}/{len(image_paths)} images"

        validation = create_validation_summary(
            agent="Metadata Extraction",
            stage="ingestion",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        log_info(self.logger, f"Metadata extraction completed: {summary}", "Metadata Extraction")

        return metadata_list, validation
