"""Agent 6: Caption Generation - Generate multi-level captions for images."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List
import random

from utils.logger import log_error, log_info
from utils.validation import validate_agent_output, create_validation_summary


class CaptionGenerationAgent:
    """
    Agent 6: Caption Writer & Storyteller

    System Prompt:
    You are an award-winning travel writer and photo journalist. Generate engaging,
    informative captions that bring images to life.

    Caption levels:
    1. CONCISE (1 line, <100 chars): Twitter-style, punchy description
    2. STANDARD (2-3 lines, 150-250 chars): Instagram-style, engaging narrative
    3. DETAILED (paragraph, 300-500 chars): Editorial-style, comprehensive story

    Incorporate location, time, technical details, and cultural context.
    """

    SYSTEM_PROMPT = """
    You are an award-winning travel writer and photo journalist. Generate engaging,
    informative captions that bring images to life.

    Caption levels:
    1. CONCISE (1 line, <100 chars): Twitter-style, punchy description
       Example: "Golden sunset over Santorini's iconic blue domes"

    2. STANDARD (2-3 lines, 150-250 chars): Instagram-style, engaging narrative
       Example: "As the sun dips below the Aegean Sea, Santorini's famous blue-domed
       churches glow in golden light. Captured during the magical hour when the island
       transforms into a photographer's dream."

    3. DETAILED (paragraph, 300-500 chars): Editorial-style, comprehensive story
       Example: "This photograph captures the quintessential Santorini experience during
       golden hour. The iconic blue-domed churches of Oia, with their striking contrast
       against white-washed walls, are bathed in warm sunset light. Shot at f/8 with
       ISO 200, the image preserves detail from the shadowed foreground through to the
       distant caldera. The composition follows the rule of thirds, placing the main
       dome at the intersection for maximum visual impact. Location: Oia, Santorini,
       Greece (36.4618° N, 25.3753° E)."

    Incorporate:
    - Location from GPS or metadata
    - Time of day and lighting conditions
    - Technical details (camera settings) in detailed captions
    - Cultural or historical context
    - Emotional resonance and storytelling
    - Keywords for searchability

    Avoid clichés; be specific and authentic.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Caption Generation Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('caption_generation', {})
        self.model = self.agent_config.get('model', 'gemini')

    def _call_llm_api(
        self,
        image_path: Path,
        metadata: Dict[str, Any],
        quality: Dict[str, Any],
        aesthetic: Dict[str, Any],
        category: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call LLM API for caption generation.

        In production, this would call GPT-4 or Gemini.
        For demonstration, returns simulated captions.

        Args:
            image_path: Path to image
            metadata: Image metadata
            quality: Quality assessment
            aesthetic: Aesthetic assessment
            category: Categorization

        Returns:
            Captions dictionary
        """
        # Check if API key is available based on model
        if 'gemini' in self.model.lower():
            api_key = os.getenv('GOOGLE_API_KEY')
        else:
            api_key = os.getenv('OPENAI_API_KEY')

        if api_key and len(api_key) > 10:
            # Real API call would go here
            # For OpenAI: from openai import OpenAI
            # For Google: import google.generativeai as genai
            pass

        # Simulated captions for demonstration
        # In production, LLM would analyze image and generate contextual captions

        # Extract info for captions
        location = category.get('location', 'unknown location')
        time_cat = category.get('time_category', 'daytime')
        main_cat = category.get('category', 'scene')
        camera = metadata.get('camera_settings', {}).get('camera_model', 'camera')

        # Generate captions
        captions = {
            'concise': f"Beautiful {main_cat.lower()} captured during {time_cat.lower()}",
            'standard': f"This stunning {main_cat.lower()} photograph was taken during "
                       f"{time_cat.lower()} at {location}. The lighting and composition "
                       f"create a memorable travel moment worth preserving.",
            'detailed': f"This {main_cat.lower()} photograph showcases exceptional "
                       f"travel photography captured during {time_cat.lower()}. "
                       f"Location: {location}. Shot with {camera}, the image demonstrates "
                       f"strong technical quality (score: {quality.get('quality_score', 3)}/5) "
                       f"and aesthetic appeal (score: {aesthetic.get('overall_aesthetic', 3)}/5). "
                       f"The composition features {', '.join(category.get('subcategories', ['compelling elements']))} "
                       f"that draw the viewer into the scene. This image represents the "
                       f"essence of travel photography: capturing a moment in time that "
                       f"tells a story and evokes emotion."
        }

        # Ensure length constraints
        if len(captions['concise']) > 100:
            captions['concise'] = captions['concise'][:97] + "..."

        if len(captions['standard']) > 250:
            captions['standard'] = captions['standard'][:247] + "..."

        if len(captions['detailed']) < 300:
            # Pad if too short
            captions['detailed'] += " This photograph preserves a unique travel memory."

        if len(captions['detailed']) > 500:
            captions['detailed'] = captions['detailed'][:497] + "..."

        # Generate keywords
        keywords = [
            main_cat.lower(),
            time_cat.lower(),
            'travel',
            'photography'
        ] + category.get('subcategories', [])

        return {
            'captions': captions,
            'keywords': keywords[:10]  # Limit to 10 keywords
        }

    def process_image(
        self,
        image_path: Path,
        metadata: Dict[str, Any],
        quality: Dict[str, Any],
        aesthetic: Dict[str, Any],
        category: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate captions for a single image.

        Args:
            image_path: Path to image
            metadata: Metadata from Agent 1
            quality: Quality from Agent 2
            aesthetic: Aesthetic from Agent 3
            category: Categorization from Agent 5

        Returns:
            Caption data
        """
        try:
            # Generate captions
            caption_data = self._call_llm_api(
                image_path,
                metadata,
                quality,
                aesthetic,
                category
            )

            result = {
                'image_id': metadata['image_id'],
                'captions': caption_data['captions'],
                'keywords': caption_data['keywords']
            }

            # Validate
            is_valid, error_msg = validate_agent_output("caption_generation", result)
            if not is_valid:
                log_error(
                    self.logger,
                    "Caption Generation",
                    "ValidationError",
                    f"Validation failed for {image_path.name}: {error_msg}",
                    "warning"
                )

            return result

        except Exception as e:
            log_error(
                self.logger,
                "Caption Generation",
                "ProcessingError",
                f"Failed to generate captions for {image_path.name}: {str(e)}",
                "error"
            )
            return {
                'image_id': metadata.get('image_id', image_path.stem),
                'captions': {
                    'concise': 'Travel photograph',
                    'standard': 'A travel photograph captured during a journey. ' * 2,
                    'detailed': 'A travel photograph that preserves a moment from the journey. '
                               'This image captures the essence of exploration and discovery, '
                               'offering viewers a glimpse into a unique location and experience. '
                               'The photograph serves as a visual memory of travel adventures and '
                               'the beauty found in exploring new places and cultures around the world.'
                },
                'keywords': ['travel', 'photography', 'journey']
            }

    def run(
        self,
        image_paths: List[Path],
        metadata_list: List[Dict[str, Any]],
        quality_assessments: List[Dict[str, Any]],
        aesthetic_assessments: List[Dict[str, Any]],
        categorizations: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate captions for all images.

        Args:
            image_paths: List of image paths
            metadata_list: Metadata from Agent 1
            quality_assessments: Quality from Agent 2
            aesthetic_assessments: Aesthetic from Agent 3
            categorizations: Categories from Agent 5

        Returns:
            Tuple of (captions_list, validation_summary)
        """
        log_info(self.logger, f"Starting caption generation for {len(image_paths)} images", "Caption Generation")

        # Create lookups
        metadata_map = {m['image_id']: m for m in metadata_list}
        quality_map = {q['image_id']: q for q in quality_assessments}
        aesthetic_map = {a['image_id']: a for a in aesthetic_assessments}
        category_map = {c['image_id']: c for c in categorizations}

        captions_list = []
        issues = []

        for path in image_paths:
            image_id = path.stem

            try:
                metadata = metadata_map.get(image_id, {'image_id': image_id})
                quality = quality_map.get(image_id, {})
                aesthetic = aesthetic_map.get(image_id, {})
                category = category_map.get(image_id, {})

                result = self.process_image(path, metadata, quality, aesthetic, category)
                captions_list.append(result)

            except Exception as e:
                error_msg = f"Failed to generate caption for {path.name}: {str(e)}"
                issues.append(error_msg)
                log_error(
                    self.logger,
                    "Caption Generation",
                    "ExecutionError",
                    error_msg,
                    "error"
                )

        summary = f"Generated captions for {len(captions_list)} images"

        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")

        validation = create_validation_summary(
            agent="Caption Generation",
            stage="writing",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        log_info(self.logger, f"Caption generation completed: {summary}", "Caption Generation")

        return captions_list, validation
