"""Filtering and Categorization Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel

# Import existing filtering logic
from agents.filtering_categorization import FilteringCategorizationAgent


class FilteringCategorizationInput(BaseModel):
    """Input schema for Filtering and Categorization Tool."""
    metadata_json: str
    quality_json: str
    aesthetic_json: str


class FilteringCategorizationTool(BaseTool):
    """
    Tool for filtering and categorizing travel photos.

    Filters photos based on quality/aesthetic thresholds and categorizes by content.
    """

    name: str = "Filtering and Categorization Tool"
    description: str = (
        "Filters travel photos based on quality and aesthetic thresholds, "
        "and categorizes them by content type (landmarks, nature, food, etc.). "
        "Determines which photos pass selection criteria for final gallery. "
        "Inputs: metadata_json, quality_json, aesthetic_json (JSON strings from previous tasks)"
    )
    args_schema: Type[BaseModel] = FilteringCategorizationInput

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

    def _run(self, metadata_json: str, quality_json: str, aesthetic_json: str) -> str:
        """
        Execute filtering and categorization on provided images.

        Args:
            metadata_json: JSON string with metadata results
            quality_json: JSON string with quality results
            aesthetic_json: JSON string with aesthetic results

        Returns:
            JSON string containing filtering results and categorizations
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in self._image_paths]

        # Parse previous results from JSON
        metadata_result = json.loads(metadata_json)
        quality_result = json.loads(quality_json)
        aesthetic_result = json.loads(aesthetic_json)

        metadata_list = metadata_result.get("metadata", [])
        quality_list = quality_result.get("quality_assessments", [])
        aesthetic_list = aesthetic_result.get("aesthetic_assessments", [])

        # Setup logger
        logger = logging.getLogger("FilteringCategorizationTool")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

        # Create agent instance and run
        agent = FilteringCategorizationAgent(config=self._config, logger=logger)
        filtering_list, validation = agent.run(
            paths, metadata_list, quality_list, aesthetic_list
        )

        # Return results as JSON
        result = {
            "filtering_categorizations": filtering_list,
            "validation": validation,
            "summary": f"Filtered and categorized {len(filtering_list)} images"
        }

        return json.dumps(result, indent=2)
