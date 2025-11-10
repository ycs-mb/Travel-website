"""Caption Generation Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel

# Import existing caption generation logic
from agents.caption_generation import CaptionGenerationAgent


class CaptionGenerationInput(BaseModel):
    """Input schema for Caption Generation Tool."""
    metadata_json: str
    quality_json: str
    aesthetic_json: str
    filtering_json: str


class CaptionGenerationTool(BaseTool):
    """
    Tool for generating multi-level captions for travel photos.

    Generates concise, standard, and detailed captions with keywords.
    """

    name: str = "Caption Generation Tool"
    description: str = (
        "Generates engaging, informative captions for travel photos at three levels: "
        "concise (<100 chars), standard (150-250 chars), and detailed (300-500 chars). "
        "Incorporates location, technical details, and cultural context. "
        "Inputs: metadata_json, quality_json, aesthetic_json, filtering_json (JSON strings from previous tasks)"
    )
    args_schema: Type[BaseModel] = CaptionGenerationInput

    # Store image paths and config
    _image_paths: List[str] = []
    _config: Dict[str, Any] = {}

    def __init__(self, image_paths: Optional[List[str]] = None, config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize with image paths and config."""
        super().__init__(**kwargs)
        if image_paths:
            self._image_paths = image_paths
        if config:
            self._config = config

    def _run(self, metadata_json: str, quality_json: str, aesthetic_json: str, filtering_json: str) -> str:
        """
        Execute caption generation on provided images.

        Args:
            metadata_json: JSON string with metadata results
            quality_json: JSON string with quality results
            aesthetic_json: JSON string with aesthetic results
            filtering_json: JSON string with filtering results

        Returns:
            JSON string containing captions for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in self._image_paths]

        # Parse previous results from JSON
        metadata_result = json.loads(metadata_json)
        quality_result = json.loads(quality_json)
        aesthetic_result = json.loads(aesthetic_json)
        filtering_result = json.loads(filtering_json)

        metadata_list = metadata_result.get("metadata", [])
        quality_list = quality_result.get("quality_assessments", [])
        aesthetic_list = aesthetic_result.get("aesthetic_assessments", [])
        filtering_list = filtering_result.get("filtering_categorizations", [])

        # Setup logger
        logger = logging.getLogger("CaptionGenerationTool")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

        # Create agent instance and run
        agent = CaptionGenerationAgent(config=self._config, logger=logger)
        captions_list, validation = agent.run(
            paths, metadata_list, quality_list, aesthetic_list, filtering_list
        )

        # Return results as JSON
        result = {
            "captions": captions_list,
            "validation": validation,
            "summary": f"Generated captions for {len(captions_list)} images"
        }

        return json.dumps(result, indent=2)
