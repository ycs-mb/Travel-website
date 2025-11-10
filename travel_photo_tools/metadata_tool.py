"""Metadata Extraction Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import existing metadata extraction logic
from agents.metadata_extraction import MetadataExtractionAgent


class MetadataExtractionInput(BaseModel):
    """Input schema for Metadata Extraction Tool."""
    pass  # No runtime arguments needed


class MetadataExtractionTool(BaseTool):
    """
    Tool for extracting comprehensive metadata from travel photos.

    Extracts EXIF data, GPS coordinates, camera settings, and flags issues.
    """

    name: str = "Metadata Extraction Tool"
    description: str = (
        "Extracts comprehensive metadata from travel photos including "
        "EXIF data, GPS coordinates, capture date/time, camera settings, "
        "and flags images with missing or corrupted metadata. "
        "Call this tool without any arguments to process all images."
    )
    args_schema: Type[BaseModel] = MetadataExtractionInput

    # Store image paths and config as instance variables
    _image_paths: List[str] = []
    _config: Dict[str, Any] = {}

    def __init__(self, image_paths: Optional[List[str]] = None, config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize with image paths and config."""
        super().__init__(**kwargs)
        if image_paths:
            self._image_paths = image_paths
        if config:
            self._config = config

    def _run(self) -> str:
        """
        Execute metadata extraction on configured images.

        Returns:
            JSON string containing metadata for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in self._image_paths]

        # Setup logger
        logger = logging.getLogger("MetadataExtractionTool")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

        # Create agent instance and run
        agent = MetadataExtractionAgent(config=self._config, logger=logger)
        metadata_list, validation = agent.run(paths)

        # Return results as JSON
        result = {
            "metadata": metadata_list,
            "validation": validation,
            "summary": f"Extracted metadata from {len(metadata_list)} images"
        }

        return json.dumps(result, indent=2)
