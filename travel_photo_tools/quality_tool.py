"""Quality Assessment Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel

# Import existing quality assessment logic
from agents.quality_assessment import QualityAssessmentAgent


class QualityAssessmentInput(BaseModel):
    """Input schema for Quality Assessment Tool."""
    metadata_json: str  # JSON from previous task


class QualityAssessmentTool(BaseTool):
    """
    Tool for assessing technical quality of travel photos.

    Evaluates sharpness, noise, exposure, composition, and provides quality scores.
    """

    name: str = "Quality Assessment Tool"
    description: str = (
        "Assesses technical quality of travel photos by evaluating "
        "sharpness, noise levels, exposure, composition, and resolution. "
        "Provides quality scores (1-5) and detailed technical analysis. "
        "Input: metadata_json (JSON string from metadata extraction)"
    )
    args_schema: Type[BaseModel] = QualityAssessmentInput

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
        Execute quality assessment on provided images.

        Args:
            metadata_json: JSON string with metadata results

        Returns:
            JSON string containing quality assessments for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in self._image_paths]

        # Parse metadata from JSON
        metadata_result = json.loads(metadata_json)
        metadata_list = metadata_result.get("metadata", [])

        # Setup logger
        logger = logging.getLogger("QualityAssessmentTool")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

        # Create agent instance and run
        agent = QualityAssessmentAgent(config=self._config, logger=logger)
        quality_list, validation = agent.run(paths, metadata_list)

        # Return results as JSON
        result = {
            "quality_assessments": quality_list,
            "validation": validation,
            "summary": f"Assessed quality for {len(quality_list)} images"
        }

        return json.dumps(result, indent=2)
