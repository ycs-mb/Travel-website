"""Aesthetic Assessment Tool for CrewAI."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import existing aesthetic assessment logic
from agents.aesthetic_assessment import AestheticAssessmentAgent


class AestheticAssessmentInput(BaseModel):
    """Input schema for Aesthetic Assessment Tool."""

    image_paths: List[str] = Field(
        ...,
        description="List of image file paths to assess aesthetics"
    )
    metadata_json: str = Field(
        ...,
        description="JSON string containing metadata from previous stage"
    )
    config: Dict[str, Any] = Field(
        ...,
        description="Configuration dictionary for the tool"
    )


class AestheticAssessmentTool(BaseTool):
    """
    Tool for assessing aesthetic appeal of travel photos.

    Evaluates composition, lighting, color harmony, emotional impact, and provides aesthetic scores.
    """

    name: str = "Aesthetic Assessment Tool"
    description: str = (
        "Assesses aesthetic appeal of travel photos by evaluating "
        "composition, lighting quality, color harmony, subject interest, "
        "and emotional impact. Provides aesthetic scores (1-5) and analysis."
    )
    args_schema: Type[BaseModel] = AestheticAssessmentInput

    def _run(
        self,
        image_paths: List[str],
        metadata_json: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Execute aesthetic assessment on provided images.

        Args:
            image_paths: List of image file paths
            metadata_json: JSON string with metadata results
            config: Configuration dictionary

        Returns:
            JSON string containing aesthetic assessments for all images
        """
        # Convert string paths to Path objects
        paths = [Path(p) for p in image_paths]

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
        agent = AestheticAssessmentAgent(config=config, logger=logger)
        aesthetic_list, validation = agent.run(paths, metadata_list)

        # Return results as JSON
        result = {
            "aesthetic_assessments": aesthetic_list,
            "validation": validation,
            "summary": f"Assessed aesthetics for {len(aesthetic_list)} images"
        }

        return json.dumps(result, indent=2)
