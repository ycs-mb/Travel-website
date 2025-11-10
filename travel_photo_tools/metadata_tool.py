"""Metadata Extraction Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import existing metadata extraction logic
from agents.metadata_extraction import MetadataExtractionAgent


class MetadataExtractionInput(BaseModel):
    """Input schema for Metadata Extraction Tool."""

    image_paths: List[str] = Field(
        ...,
        description="List of image file paths to extract metadata from"
    )
    config: Dict[str, Any] = Field(
        ...,
        description="Configuration dictionary for the tool"
    )


class MetadataExtractionTool(BaseTool):
    """
    Tool for extracting comprehensive metadata from travel photos.

    Extracts EXIF data, GPS coordinates, camera settings, and flags issues.
    """

    name: str = "Metadata Extraction Tool"
    description: str = (
        "Extracts comprehensive metadata from travel photos including "
        "EXIF data, GPS coordinates, capture date/time, camera settings, "
        "and flags images with missing or corrupted metadata."
    )
    args_schema: Type[BaseModel] = MetadataExtractionInput

    def _run(
        self,
        image_paths: List[str],
        config: Dict[str, Any]
    ) -> str:
        """
        Execute metadata extraction on provided images.

        Args:
            image_paths: List of image file paths
            config: Configuration dictionary

        Returns:
            JSON string containing metadata for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in image_paths]

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
        agent = MetadataExtractionAgent(config=config, logger=logger)
        metadata_list, validation = agent.run(paths)

        # Return results as JSON
        result = {
            "metadata": metadata_list,
            "validation": validation,
            "summary": f"Extracted metadata from {len(metadata_list)} images"
        }

        return json.dumps(result, indent=2)
