"""Aesthetic Assessment Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel

# Import existing aesthetic assessment logic
from agents.aesthetic_assessment import AestheticAssessmentAgent


class AestheticAssessmentInput(BaseModel):
    """Input schema for Aesthetic Assessment Tool."""
    metadata_json: str  # JSON from previous task


class AestheticAssessmentTool(BaseTool):
    """
    Tool for assessing aesthetic appeal of travel photos.

    Evaluates composition, lighting, color harmony, emotional impact, and provides aesthetic scores.
    """

    name: str = "Aesthetic Assessment Tool"
    description: str = (
        "Assesses aesthetic appeal of travel photos by evaluating "
        "composition, lighting quality, color harmony, subject interest, "
        "and emotional impact. Provides aesthetic scores (1-5) and analysis. "
        "Input: metadata_json (JSON string from metadata extraction)"
    )
    args_schema: Type[BaseModel] = AestheticAssessmentInput

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

    def _run(self, metadata_json: str) -> str:
        """
        Execute aesthetic assessment on provided images.

        Args:
            metadata_json: JSON string with metadata results

        Returns:
            JSON string containing aesthetic assessments for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in self._image_paths]

        # Parse metadata from JSON
        metadata_result = json.loads(metadata_json)
        metadata_list = metadata_result.get("metadata", [])

        # Setup logger
        logger = logging.getLogger("AestheticAssessmentTool")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

        # Create agent instance and run
        agent = AestheticAssessmentAgent(config=self._config, logger=logger)
        aesthetic_list, validation = agent.run(paths, metadata_list)

        # Return results as JSON
        result = {
            "aesthetic_assessments": aesthetic_list,
            "validation": validation,
            "summary": f"Assessed aesthetics for {len(aesthetic_list)} images"
        }

        return json.dumps(result, indent=2)
