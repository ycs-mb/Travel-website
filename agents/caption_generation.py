"""Agent 6: Caption Generation - Generate multi-level captions for images."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List
import base64
import json
import re

from google import genai
from google.genai import types

from utils.logger import log_error, log_info, log_warning
from utils.validation import validate_agent_output, create_validation_summary
from utils.heic_reader import is_heic_file, open_heic_with_pil
from utils.token_tracker import TokenTracker, resize_image_for_api, get_optimized_media_type


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

    # Concise system prompt (optimized for token reduction)
    SYSTEM_PROMPT_CONCISE = """Generate travel photo captions.
Return 3 levels: concise (<100 chars), standard (150-250 chars), detailed (300-500 chars).
Add keywords. Respond with ONLY valid JSON."""

    # Full system prompt
    SYSTEM_PROMPT_FULL = """
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

        # Configure Gemini API
        self.api_config = config.get('api', {}).get('google', {})
        self.model_name = self.api_config.get('model')
        if not self.model_name:
            log_warning(self.logger, "Google API model not specified in config, defaulting to 'gemini-1.5-flash'", "Caption Generation")
            self.model_name = "gemini-1.5-flash"

        # Initialize Vertex AI client
        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.api_config.get('project'),
                location=self.api_config.get('location', 'us-central1')
            )
            log_info(self.logger, f"Initialized Vertex AI client for project {self.api_config.get('project')}", "Caption Generation")
        except Exception as e:
            log_warning(self.logger, f"Failed to initialize Vertex AI client: {e}", "Caption Generation")
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

    def _call_llm_api(
        self,
        image_path: Path,
        metadata: Dict[str, Any],
        quality: Dict[str, Any],
        aesthetic: Dict[str, Any],
        category: Dict[str, Any],
        image_id: str = None
    ) -> Dict[str, Any]:
        """
        Call Gemini API for caption generation.

        Args:
            image_path: Path to image
            metadata: Image metadata
            quality: Quality assessment
            aesthetic: Aesthetic assessment
            category: Categorization
            image_id: Image identifier for token tracking

        Returns:
            Captions dictionary
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
                except Exception as e:
                    log_warning(self.logger, f"Failed to resize image, using original: {e}", "Caption Generation")
                    with open(image_path, 'rb') as f:
                        image_bytes = f.read()
                    media_type = get_optimized_media_type(image_path)
            else:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                media_type = get_optimized_media_type(image_path)

            # Build context for captions
            location = category.get('location', 'the location')
            time_cat = category.get('time_category', 'daytime')
            main_cat = category.get('category', 'a scene')
            subcats = ', '.join(category.get('subcategories', ['visual elements']))

            # Create prompt for caption generation (concise or detailed)
            if self.use_concise_prompts:
                # Optimized concise prompt
                prompt = f"""{self.SYSTEM_PROMPT}

Category: {main_cat}, Time: {time_cat}.

{{
    "concise": "<max 100 chars>",
    "standard": "<150-250 chars>",
    "detailed": "<300-500 chars>",
    "keywords": ["<kw1>", "<kw2>"]
}}"""
            else:
                # Full detailed prompt
                prompt = f"""{self.SYSTEM_PROMPT}

CONTEXT:
- Image category: {main_cat}
- Key elements: {subcats}
- Time of day: {time_cat}
- Location: {location}
- Technical quality score: {quality.get('quality_score', 3)}/5
- Aesthetic score: {aesthetic.get('overall_aesthetic', 3)}/5
- Camera: {metadata.get('camera_settings', {}).get('camera_model', 'Professional camera')}
- Aperture: {metadata.get('camera_settings', {}).get('aperture', 'unknown')}
- ISO: {metadata.get('camera_settings', {}).get('iso', 'unknown')}

RESPONSE FORMAT: Generate three levels of captions as a JSON object:
{{
    "concise": "<1 line, max 100 chars, punchy Twitter-style>",
    "standard": "<2-3 lines, 150-250 chars, Instagram-style narrative>",
    "detailed": "<paragraph style, 300-500 chars, editorial depth>",
    "keywords": ["<keyword1>", "<keyword2>", ...]
}}

Make captions specific, avoid clichés, and incorporate the actual visual elements."""

            # Call Gemini API with image via Vertex AI
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
            log_info(self.logger, f"Received Gemini captions for {image_path.name}", "Caption Generation")

            # Extract captions
            captions = self._parse_caption_response(response_text)

            # Track token usage and calculate cost
            if hasattr(response, 'usage_metadata'):
                usage_record = self.token_tracker.track_usage(response.usage_metadata, image_id)
                captions['token_usage'] = usage_record

                # Log per-image cost if enabled
                cost_config = self.config.get('cost_tracking', {})
                if cost_config.get('log_per_image', True):
                    log_info(
                        self.logger,
                        f"Token cost for {image_path.name}: ${usage_record['estimated_cost_usd']:.4f} "
                        f"({usage_record['total_token_count']} tokens)",
                        "Caption Generation"
                    )

            return captions

        except Exception as e:
            log_error(
                self.logger,
                "Caption Generation",
                "APIError",
                f"Gemini API call failed for {image_path.name}: {str(e)}",
                "error"
            )
            # Return default captions on API failure
            return {
                'captions': {
                    'concise': 'Travel photograph',
                    'standard': 'A beautiful travel photograph capturing a memorable moment.',
                    'detailed': 'This travel photograph documents a moment from a journey, '
                               'preserving the essence of exploration and discovery.'
                },
                'keywords': ['travel', 'photography', 'journey']
            }

    def _parse_caption_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini API response to extract captions and keywords.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Dictionary with captions and keywords
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_json = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                response_json = self._extract_captions_from_text(response_text)

            captions = {
                'concise': response_json.get('concise', 'Travel photograph'),
                'standard': response_json.get('standard', 'A travel photograph.'),
                'detailed': response_json.get('detailed', 'A travel photograph.')
            }

            # Enforce length constraints
            if len(captions['concise']) > 100:
                captions['concise'] = captions['concise'][:97] + "..."

            if len(captions['standard']) > 250:
                captions['standard'] = captions['standard'][:247] + "..."

            if len(captions['detailed']) > 500:
                captions['detailed'] = captions['detailed'][:497] + "..."

            # Ensure minimum lengths
            if len(captions['detailed']) < 100:
                captions['detailed'] = captions['detailed'] + " This photograph captures a unique travel moment."

            keywords = response_json.get('keywords', ['travel', 'photography'])
            if not isinstance(keywords, list):
                keywords = ['travel', 'photography']

            return {
                'captions': captions,
                'keywords': keywords[:10]  # Limit to 10 keywords
            }

        except Exception as e:
            log_warning(self.logger, f"Failed to parse caption response: {str(e)}", "Caption Generation")
            return {
                'captions': {
                    'concise': 'Travel photograph',
                    'standard': 'A travel photograph capturing a memorable moment.',
                    'detailed': 'This travel photograph documents a moment from a journey, '
                               'preserving the essence of exploration and discovery.'
                },
                'keywords': ['travel', 'photography', 'journey']
            }

    def _extract_captions_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract captions from natural language response.

        Args:
            text: Natural language response text

        Returns:
            Dictionary with extracted captions
        """
        captions = {
            'concise': text.split('\n')[0][:100] if text else 'Travel photograph',
            'standard': text[:250] if text else 'A travel photograph.',
            'detailed': text[:500] if text else 'A travel photograph.'
        }

        keywords = []
        # Try to extract keywords from common patterns
        if 'keyword' in text.lower():
            keyword_section = text.lower().split('keyword')[1]
            words = re.findall(r'\b\w+\b', keyword_section)
            keywords = words[:10]

        if not keywords:
            keywords = ['travel', 'photography']

        return {
            'concise': captions['concise'],
            'standard': captions['standard'],
            'detailed': captions['detailed'],
            'keywords': keywords
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
            image_id = metadata.get('image_id', image_path.stem)

            # Generate captions
            caption_data = self._call_llm_api(
                image_path,
                metadata,
                quality,
                aesthetic,
                category,
                image_id
            )

            result = {
                'image_id': image_id,
                'captions': caption_data['captions'],
                'keywords': caption_data['keywords']
            }

            if 'token_usage' in caption_data:
                result['token_usage'] = caption_data['token_usage']

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

        # Get token usage summary
        usage_summary = self.token_tracker.get_summary()
        if usage_summary['images_processed'] > 0:
            log_info(
                self.logger,
                f"Total tokens used: {usage_summary['total_tokens']['total_tokens']:,} "
                f"(input: {usage_summary['total_tokens']['prompt_tokens']:,}, "
                f"output: {usage_summary['total_tokens']['completion_tokens']:,})",
                "Caption Generation"
            )
            log_info(
                self.logger,
                f"Estimated cost: ${usage_summary['estimated_cost_usd']:.4f} "
                f"(avg: ${usage_summary['estimated_cost_usd']/usage_summary['images_processed']:.4f} per image)",
                "Caption Generation"
            )

            # Check if cost exceeds threshold
            cost_config = self.config.get('cost_tracking', {})
            threshold = cost_config.get('alert_threshold_usd', 1.0)
            if usage_summary['estimated_cost_usd'] > threshold:
                log_warning(
                    self.logger,
                    f"Cost ${usage_summary['estimated_cost_usd']:.4f} exceeds threshold ${threshold:.2f}",
                    "Caption Generation"
                )

        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")

        validation = create_validation_summary(
            agent="Caption Generation",
            stage="writing",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        # Add token usage to validation
        if usage_summary['images_processed'] > 0:
            validation['token_usage'] = usage_summary

        log_info(self.logger, f"Caption generation completed: {summary}", "Caption Generation")

        return captions_list, validation
