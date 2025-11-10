"""Quality Assessment Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import existing quality assessment logic
from agents.quality_assessment import QualityAssessmentAgent


class QualityAssessmentInput(BaseModel):
    """Input schema for Quality Assessment Tool."""

    image_paths: List[str] = Field(
        ...,
        description="List of image file paths to assess quality"
    )
    metadata_json: str = Field(
        ...,
        description="JSON string containing metadata from previous stage"
    )
    config: Dict[str, Any] = Field(
        ...,
        description="Configuration dictionary for the tool"
    )


class QualityAssessmentTool(BaseTool):
    """
    Tool for assessing technical quality of travel photos.

    Evaluates sharpness, noise, exposure, composition, and provides quality scores.
    """

    name: str = "Quality Assessment Tool"
    description: str = (
        "Assesses technical quality of travel photos by evaluating "
        "sharpness, noise levels, exposure, composition, and resolution. "
        "Provides quality scores (1-5) and detailed technical analysis."
    )
    args_schema: Type[BaseModel] = QualityAssessmentInput

    def _run(
        self,
        image_paths: List[str],
        metadata_json: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Execute quality assessment on provided images.

        Args:
            image_paths: List of image file paths
            metadata_json: JSON string with metadata results
            config: Configuration dictionary

        Returns:
            JSON string containing quality assessments for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in image_paths]

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
        agent = QualityAssessmentAgent(config=config, logger=logger)
        quality_list, validation = agent.run(paths, metadata_list)

        # Return results as JSON
        result = {
            "quality_assessments": quality_list,
            "validation": validation,
            "summary": f"Assessed quality for {len(quality_list)} images"
        }

        return json.dumps(result, indent=2)
