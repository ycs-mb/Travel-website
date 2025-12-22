"""Agent 3: Aesthetic Assessment - Evaluate artistic and aesthetic quality."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
import json
import re
import io

from PIL import Image
from google import genai
from google.genai import types

from utils.logger import log_error, log_info, log_warning
from utils.validation import validate_agent_output, create_validation_summary
from utils.heic_reader import is_heic_file, open_heic_with_pil
from utils.token_tracker import TokenTracker, resize_image_for_api, get_optimized_media_type


class AestheticAssessmentAgent:
    """
    Agent 3: Visual Curator

    System Prompt:
    You are a world-renowned photo curator and aesthetic expert with decades of
    experience in fine art and travel photography.

    Evaluate: Composition, Framing, Lighting Quality, Subject Interest, Overall Aesthetic.
    Scoring: 5=Museum quality, 4=Professional, 3=Good amateur, 2=Acceptable, 1=Poor.
    """

    # Concise system prompt (optimized for token reduction)
    SYSTEM_PROMPT_CONCISE = """Evaluate travel photo aesthetic quality.
Rate (1-5): composition, framing, lighting, subject_interest.
5=Exceptional, 4=Professional, 3=Good, 2=Acceptable, 1=Poor.
Respond with ONLY valid JSON."""

    # Full system prompt (for reference/fallback)
    SYSTEM_PROMPT_FULL = """
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

        # Configure Gemini API
        self.api_config = config.get('api', {}).get('google', {})
        self.model_name = self.api_config.get('model')
        if not self.model_name:
            log_warning(self.logger, "Google API model not specified in config, defaulting to 'gemini-1.5-flash'", "Aesthetic Assessment")
            self.model_name = "gemini-1.5-flash"

        # Initialize Vertex AI client
        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.api_config.get('project'),
                location=self.api_config.get('location', 'us-central1')
            )
            log_info(self.logger, f"Initialized Vertex AI client for project {self.api_config.get('project')}", "Aesthetic Assessment")
        except Exception as e:
            log_warning(self.logger, f"Failed to initialize Vertex AI client: {e}", "Aesthetic Assessment")
            self.client = None

        # Token tracking setup
        pricing_config = self.api_config.get('pricing', {})
        pricing = {
            'input_per_1k': pricing_config.get('input_per_1k_tokens', 0.000075),
            'output_per_1k': pricing_config.get('output_per_1k_tokens', 0.0003)
        }
        self.token_tracker = TokenTracker(pricing=pricing)

        # Optimization settings
        self.optimization = self.api_config.get('optimization', {})
        self.enable_resizing = self.optimization.get('enable_image_resizing', True)
        self.max_dimension = self.optimization.get('max_image_dimension', 1024)
        self.jpeg_quality = self.optimization.get('jpeg_quality', 85)
        self.use_concise_prompts = self.optimization.get('use_concise_prompts', True)

        # Select prompt based on optimization setting
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPT_CONCISE if self.use_concise_prompts else self.SYSTEM_PROMPT_FULL

    def _call_vlm_api(self, image_path: Path, prompt: str, image_id: str = None) -> Dict[str, Any]:
        """
        Call Gemini Vision API for aesthetic assessment.

        Args:
            image_path: Path to image
            prompt: Assessment prompt
            image_id: Image identifier for token tracking

        Returns:
            Assessment scores and notes
        """
        try:
            # Use optimized image resizing if enabled
            if self.enable_resizing:
                try:
                    image_bytes = resize_image_for_api(
                        image_path,
                        max_dimension=self.max_dimension,
                        quality=self.jpeg_quality
                    )
                    media_type = get_optimized_media_type(image_path)
                    log_info(self.logger, f"Resized image for API (max_dim={self.max_dimension}): {image_path.name}", "Aesthetic Assessment")
                except Exception as e:
                    log_warning(self.logger, f"Failed to resize image, using original: {e}", "Aesthetic Assessment")
                    # Fallback to original
                    with open(image_path, 'rb') as f:
                        image_bytes = f.read()
                    media_type = get_optimized_media_type(image_path)
            else:
                # Read original image
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                media_type = get_optimized_media_type(image_path)

            # Call Gemini Vision API via Vertex AI
            if not self.client:
                raise Exception("Vertex AI client not initialized")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=media_type
                    )
                ]
            )

            # Parse response
            response_text = response.text
            log_info(self.logger, f"Received Gemini response for {image_path.name}", "Aesthetic Assessment")

            # Extract JSON from response
            assessment = self._parse_vlm_response(response_text)

            # Track token usage and calculate cost
            if hasattr(response, 'usage_metadata'):
                usage_record = self.token_tracker.track_usage(response.usage_metadata, image_id)
                assessment['token_usage'] = usage_record

                # Log per-image cost if enabled
                cost_config = self.config.get('cost_tracking', {})
                if cost_config.get('log_per_image', True):
                    log_info(
                        self.logger,
                        f"Token cost for {image_path.name}: ${usage_record['estimated_cost_usd']:.4f} "
                        f"({usage_record['total_token_count']} tokens)",
                        "Aesthetic Assessment"
                    )

            return assessment

        except Exception as e:
            log_error(
                self.logger,
                "Aesthetic Assessment",
                "APIError",
                f"Gemini API call failed for {image_path.name}: {str(e)}",
                "error"
            )
            # Return default values on API failure
            return {
                "composition": 3,
                "framing": 3,
                "lighting": 3,
                "subject_interest": 3,
                "overall_aesthetic": 3,
                "notes": f"API error: {str(e)}"
            }

    def _parse_vlm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini Vision API response to extract aesthetic scores.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Dictionary with aesthetic scores
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_json = json.loads(json_match.group())
            else:
                # If no JSON found, parse the text response
                response_json = self._extract_scores_from_text(response_text)

            # Ensure all required fields are present
            assessment = {
                "composition": int(response_json.get("composition", 3)),
                "framing": int(response_json.get("framing", 3)),
                "lighting": int(response_json.get("lighting", 3)),
                "subject_interest": int(response_json.get("subject_interest", 3)),
                "notes": response_json.get("notes", response_text[:200])
            }

            # Clamp scores to 1-5 range
            for key in ["composition", "framing", "lighting", "subject_interest"]:
                assessment[key] = max(1, min(5, assessment[key]))

            # Calculate overall aesthetic as weighted average
            assessment["overall_aesthetic"] = int(round(
                (assessment["composition"] * 0.30 +
                 assessment["framing"] * 0.25 +
                 assessment["lighting"] * 0.25 +
                 assessment["subject_interest"] * 0.20)
            ))

            return assessment

        except Exception as e:
            log_warning(self.logger, f"Failed to parse VLM response: {str(e)}", "Aesthetic Assessment")
            return {
                "composition": 3,
                "framing": 3,
                "lighting": 3,
                "subject_interest": 3,
                "overall_aesthetic": 3,
                "notes": f"Parse error: {str(e)}"
            }

    def _extract_scores_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract scores from natural language response.

        Args:
            text: Natural language response text

        Returns:
            Dictionary with extracted scores
        """
        scores = {}
        score_patterns = {
            "composition": r"composition[:\s]*(\d)",
            "framing": r"framing[:\s]*(\d)",
            "lighting": r"lighting[:\s]*(\d)",
            "subject_interest": r"subject.?interest[:\s]*(\d)"
        }

        for key, pattern in score_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                scores[key] = int(match.group(1))

        scores["notes"] = text[:200]
        return scores

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
            image_id = metadata.get('image_id', image_path.stem)

            # Construct prompt (concise if optimization enabled, detailed otherwise)
            if self.use_concise_prompts:
                # Optimized concise prompt (reduces input tokens by ~80%)
                prompt = f"""{self.SYSTEM_PROMPT}

{{
    "composition": <1-5>,
    "framing": <1-5>,
    "lighting": <1-5>,
    "subject_interest": <1-5>,
    "notes": "<brief analysis>"
}}"""
            else:
                # Full detailed prompt
                gps = metadata.get('gps', {})
                location = f"{gps.get('latitude', 'unknown')}, {gps.get('longitude', 'unknown')}"

                prompt = f"""{self.SYSTEM_PROMPT}

TASK: Analyze this travel photograph and provide aesthetic assessment scores.

Evaluate the image across these dimensions:
1. Composition (1-5): Rule of thirds, leading lines, balance, golden ratio
2. Framing (1-5): Subject placement, negative space, cropping effectiveness
3. Lighting Quality (1-5): Direction, color temperature, mood, golden/blue hour quality
4. Subject Interest (1-5): Uniqueness, emotional impact, storytelling potential

Image metadata:
- Capture time: {metadata.get('capture_datetime', 'unknown')}
- Location: {location}
- Camera: {metadata.get('camera_settings', {}).get('camera_model', 'unknown')}
- ISO: {metadata.get('camera_settings', {}).get('iso', 'unknown')}
- Aperture: {metadata.get('camera_settings', {}).get('aperture', 'unknown')}
- Focal length: {metadata.get('camera_settings', {}).get('focal_length', 'unknown')}

RESPONSE FORMAT: Provide your response as a JSON object with this exact structure:
{{
    "composition": <1-5>,
    "framing": <1-5>,
    "lighting": <1-5>,
    "subject_interest": <1-5>,
    "notes": "<brief analysis of aesthetic strengths and weaknesses>"
}}

Be specific and reference the actual visual elements you observe in the photograph."""

            # Call VLM API with token tracking
            assessment = self._call_vlm_api(image_path, prompt, image_id)

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

            # Get token usage summary
            usage_summary = self.token_tracker.get_summary()

            summary = f"Assessed {len(assessment_list)} images, average aesthetic: {avg_aesthetic:.2f}/5"
            log_info(
                self.logger,
                f"Aesthetic assessment completed: {summary}",
                "Aesthetic Assessment"
            )
            log_info(
                self.logger,
                f"Total tokens used: {usage_summary['total_tokens']['total_tokens']:,} "
                f"(input: {usage_summary['total_tokens']['prompt_tokens']:,}, "
                f"output: {usage_summary['total_tokens']['completion_tokens']:,})",
                "Aesthetic Assessment"
            )
            log_info(
                self.logger,
                f"Estimated cost: ${usage_summary['estimated_cost_usd']:.4f} "
                f"(avg: ${usage_summary['estimated_cost_usd']/len(assessment_list):.4f} per image)",
                "Aesthetic Assessment"
            )

            # Check if cost exceeds threshold
            cost_config = self.config.get('cost_tracking', {})
            threshold = cost_config.get('alert_threshold_usd', 1.0)
            if usage_summary['estimated_cost_usd'] > threshold:
                log_warning(
                    self.logger,
                    f"Cost ${usage_summary['estimated_cost_usd']:.4f} exceeds threshold ${threshold:.2f}",
                    "Aesthetic Assessment"
                )
        else:
            summary = "No images were successfully assessed"
            usage_summary = None

        # Create validation summary
        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")

        validation = create_validation_summary(
            agent="Aesthetic Assessment",
            stage="rating",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        # Add token usage to validation
        if usage_summary:
            validation['token_usage'] = usage_summary

        return assessment_list, validation
