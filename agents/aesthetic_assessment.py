"""Agent 3: Aesthetic Assessment - Evaluate artistic and aesthetic quality."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
import random

from utils.logger import log_error, log_info, log_warning
from utils.validation import validate_agent_output, create_validation_summary


class AestheticAssessmentAgent:
    """
    Agent 3: Visual Curator

    System Prompt:
    You are a world-renowned photo curator and aesthetic expert with decades of
    experience in fine art and travel photography.

    Evaluate: Composition, Framing, Lighting Quality, Subject Interest, Overall Aesthetic.
    Scoring: 5=Museum quality, 4=Professional, 3=Good amateur, 2=Acceptable, 1=Poor.
    """

    SYSTEM_PROMPT = """
    You are a world-renowned photo curator and aesthetic expert with decades of
    experience in fine art and travel photography.

    Evaluate each image across these aesthetic dimensions:
    1. Composition (1-5): Rule of thirds, leading lines, balance, golden ratio
    2. Framing (1-5): Subject placement, negative space, cropping effectiveness
    3. Lighting Quality (1-5): Direction, color temperature, mood, golden/blue hour
    4. Subject Interest (1-5): Uniqueness, emotional impact, storytelling potential
    5. Overall Aesthetic (1-5): Holistic artistic merit

    Scoring guidelines:
    - 5: Museum/gallery quality, exceptional
    - 4: Professional portfolio worthy
    - 3: Good amateur/social media worthy
    - 2: Acceptable but unremarkable
    - 1: Poor aesthetic value

    Consider genre-specific criteria for travel photography: sense of place,
    cultural context, human interest.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Aesthetic Assessment Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('aesthetic_assessment', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)
        self.model = self.agent_config.get('model', 'gpt4v')
        # Get API config based on model
        if 'gemini' in self.model.lower():
            self.api_config = config.get('api', {}).get('google', {})
        else:
            self.api_config = config.get('api', {}).get('openai', {})

    def _call_vlm_api(self, image_path: Path, prompt: str) -> Dict[str, Any]:
        """
        Call VLM API for aesthetic assessment.

        In production, this would call GPT-4V or Gemini Vision.
        For demonstration, this returns simulated responses.

        Args:
            image_path: Path to image
            prompt: Assessment prompt

        Returns:
            Assessment scores and notes
        """
        # Check if API key is available based on model
        if 'gemini' in self.model.lower():
            api_key = os.getenv('GOOGLE_API_KEY')
        else:
            api_key = os.getenv('OPENAI_API_KEY')

        if api_key and len(api_key) > 10:
            try:
                # Real API call would go here
                # For OpenAI: from openai import OpenAI
                # For Google: import google.generativeai as genai
                log_info(self.logger, f"VLM API available for {image_path.name}", "Aesthetic Assessment")
            except Exception as e:
                log_warning(self.logger, f"VLM API call failed: {e}", "Aesthetic Assessment")

        # Simulated response for demonstration
        # In production, this would parse actual VLM output
        random.seed(hash(str(image_path)))  # Deterministic simulation

        assessment = {
            "composition": random.randint(2, 5),
            "framing": random.randint(2, 5),
            "lighting": random.randint(2, 5),
            "subject_interest": random.randint(2, 5),
            "notes": f"Simulated aesthetic assessment for {image_path.name}. "
                    "In production, this would contain detailed VLM analysis of "
                    "composition, rule of thirds adherence, lighting quality, "
                    "emotional impact, and artistic merit."
        }

        # Calculate overall aesthetic as weighted average
        assessment["overall_aesthetic"] = int(round(
            (assessment["composition"] * 0.30 +
             assessment["framing"] * 0.25 +
             assessment["lighting"] * 0.25 +
             assessment["subject_interest"] * 0.20)
        ))

        return assessment

    def assess_with_vlm(self, image_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess image aesthetics using VLM.

        Args:
            image_path: Path to image file
            metadata: Image metadata

        Returns:
            Aesthetic assessment dictionary
        """
        try:
            # Construct detailed prompt for VLM
            prompt = f"""
            {self.SYSTEM_PROMPT}

            Analyze this travel photograph and provide scores (1-5) for:
            1. Composition
            2. Framing
            3. Lighting Quality
            4. Subject Interest
            5. Overall Aesthetic

            Also provide brief notes on artistic merit and recommendations.

            Image metadata:
            - Capture time: {metadata.get('capture_datetime', 'unknown')}
            - Location: {metadata.get('gps', {}).get('latitude', 'unknown')}
            - Camera: {metadata.get('camera_settings', {}).get('camera_model', 'unknown')}

            Respond with a JSON object containing the scores and notes.
            """

            # Call VLM API
            assessment = self._call_vlm_api(image_path, prompt)

            # Add image_id
            assessment['image_id'] = metadata['image_id']

            # Validate output
            is_valid, error_msg = validate_agent_output("aesthetic_assessment", assessment)
            if not is_valid:
                log_error(
                    self.logger,
                    "Aesthetic Assessment",
                    "ValidationError",
                    f"Validation failed for {image_path.name}: {error_msg}",
                    "error"
                )

            return assessment

        except Exception as e:
            log_error(
                self.logger,
                "Aesthetic Assessment",
                "ProcessingError",
                f"Failed to assess {image_path.name}: {str(e)}",
                "error"
            )
            return {
                "image_id": metadata.get('image_id', image_path.stem),
                "composition": 3,
                "framing": 3,
                "lighting": 3,
                "subject_interest": 3,
                "overall_aesthetic": 3,
                "notes": f"Assessment failed: {str(e)}"
            }

    def run(self, image_paths: List[Path], metadata_list: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run aesthetic assessment on all images.

        Args:
            image_paths: List of image file paths
            metadata_list: List of metadata from Agent 1

        Returns:
            Tuple of (assessment_list, validation_summary)
        """
        log_info(self.logger, f"Starting aesthetic assessment for {len(image_paths)} images", "Aesthetic Assessment")

        # Create lookup for metadata
        metadata_map = {m['image_id']: m for m in metadata_list}

        assessment_list = []
        issues = []

        # Process images in parallel (with rate limiting for API calls)
        batch_size = self.agent_config.get('batch_size', 5)

        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]

            with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
                futures = []
                for path in batch_paths:
                    image_id = path.stem
                    metadata = metadata_map.get(image_id, {'image_id': image_id})
                    futures.append(executor.submit(self.assess_with_vlm, path, metadata))

                for future in as_completed(futures):
                    try:
                        assessment = future.result()
                        assessment_list.append(assessment)

                    except Exception as e:
                        error_msg = f"Failed to assess image: {str(e)}"
                        issues.append(error_msg)
                        log_error(
                            self.logger,
                            "Aesthetic Assessment",
                            "ExecutionError",
                            error_msg,
                            "error"
                        )

        # Calculate statistics
        if assessment_list:
            avg_aesthetic = sum(a['overall_aesthetic'] for a in assessment_list) / len(assessment_list)
            summary = f"Assessed {len(assessment_list)} images, average aesthetic: {avg_aesthetic:.2f}/5"
        else:
            summary = "No images were successfully assessed"

        # Create validation summary
        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")

        validation = create_validation_summary(
            agent="Aesthetic Assessment",
            stage="rating",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        log_info(self.logger, f"Aesthetic assessment completed: {summary}", "Aesthetic Assessment")

        return assessment_list, validation
