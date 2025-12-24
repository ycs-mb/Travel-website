"""Agent 5: Filtering and Categorization - Filter and categorize images."""

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


class FilteringCategorizationAgent:
    """
    Agent 5: Semantic Classifier

    System Prompt:
    You are a specialist in semantic image classification and filtering using
    travel photography best practices.

    Filter by: Technical score, aesthetic score, GPS, time range, camera settings.
    Categorize by: Subject (Landscape, Architecture, People, Food, Wildlife, etc.),
                    Time (Golden Hour, Blue Hour, Day, Night),
                    Location (from GPS),
                    Activity type.
    """

    # Concise system prompt (optimized)
    SYSTEM_PROMPT_CONCISE = """Categorize travel photo by subject.
Categories: Landscape, Architecture, Urban, People, Food, Cultural, Wildlife, Adventure.
Return ONLY valid JSON."""

    # Full system prompt
    SYSTEM_PROMPT_FULL = """
    You are a specialist in semantic image classification and filtering using
    travel photography best practices.

    Filtering criteria:
    - Minimum technical score: 3/5 (configurable)
    - Minimum aesthetic score: 3/5 (configurable)
    - Flag images below thresholds but don't delete
    - Allow filtering by GPS region, time range, camera settings

    Categorization taxonomy for travel photos:
    1. By Subject: Landscape, Architecture, People/Portraits, Food, Wildlife, Urban, Cultural
    2. By Time: Golden Hour, Blue Hour, Daytime, Night, Sunset/Sunrise
    3. By Location: City/Country from GPS or EXIF
    4. By Activity: Adventure, Relaxation, Dining, Transportation, Events

    Special flags:
    - missing_gps: No location data, needs manual tagging
    - low_quality: Below technical threshold
    - low_aesthetic: Below aesthetic threshold
    - uncategorized: Cannot determine category
    - manual_review: Ambiguous or edge case

    Use VLM for semantic classification when metadata is insufficient.
    """

    # Category keywords for simple classification
    CATEGORIES = {
        'Landscape': ['mountain', 'beach', 'forest', 'lake', 'valley', 'canyon', 'desert'],
        'Architecture': ['building', 'church', 'temple', 'monument', 'bridge', 'castle'],
        'Urban': ['city', 'street', 'skyline', 'traffic', 'metro', 'downtown'],
        'People': ['portrait', 'person', 'group', 'selfie', 'crowd'],
        'Food': ['meal', 'restaurant', 'dish', 'cuisine', 'dining'],
        'Cultural': ['festival', 'ceremony', 'traditional', 'art', 'museum'],
        'Wildlife': ['animal', 'bird', 'safari', 'nature'],
        'Adventure': ['hiking', 'climbing', 'diving', 'skiing']
    }

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Filtering and Categorization Agent.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('filtering_categorization', {})
        self.min_technical = self.agent_config.get('min_technical_score', 3)
        self.min_aesthetic = self.agent_config.get('min_aesthetic_score', 3)

        # Configure Gemini API
        self.api_config = config.get('api', {}).get('google', {})
        self.model_name = self.api_config.get('model')
        if not self.model_name:
            log_warning(self.logger, "Google API model not specified in config, defaulting to 'gemini-1.5-flash'", "Filtering & Categorization")
            self.model_name = "gemini-1.5-flash"

        # Initialize Vertex AI client
        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.api_config.get('project'),
                location=self.api_config.get('location', 'us-central1')
            )
            log_info(self.logger, f"Initialized Vertex AI client for project {self.api_config.get('project')}", "Filtering & Categorization")
        except Exception as e:
            log_warning(self.logger, f"Failed to initialize Vertex AI client: {e}", "Filtering & Categorization")
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

    def categorize_by_time(self, metadata: Dict[str, Any]) -> str:
        """Categorize image by time of day from metadata."""
        datetime_str = metadata.get('capture_datetime')
        if not datetime_str:
            return 'Unknown'

        try:
            # Extract hour
            hour = int(datetime_str.split('T')[1].split(':')[0])

            if 5 <= hour < 7:
                return 'Sunrise'
            elif 7 <= hour < 10:
                return 'Morning'
            elif 17 <= hour < 19:
                return 'Golden Hour'
            elif 19 <= hour < 21:
                return 'Sunset'
            elif 21 <= hour < 23 or hour < 5:
                return 'Night'
            else:
                return 'Daytime'

        except Exception:
            return 'Unknown'

    def categorize_by_location(self, metadata: Dict[str, Any]) -> str:
        """Get location from GPS coordinates."""
        gps = metadata.get('gps', {})
        lat = gps.get('latitude')
        lon = gps.get('longitude')

        if lat and lon:
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="travel_agent")
                location = geolocator.reverse((lat, lon), language='en')
                if location:
                    address = location.raw.get('address', {})
                    city = address.get('city') or address.get('town') or address.get('village')
                    country = address.get('country')
                    if city and country:
                        return f"{city}, {country}"
                    return f"{location.address} ({lat:.4f}, {lon:.4f})"
            except Exception as e:
                log_warning(self.logger, f"Reverse geocoding failed: {e}", "Filtering")
            # Fallback: return coordinates
            return f"({lat:.4f}, {lon:.4f})"
        return None

    def categorize_by_content(self, image_path: Path, image_id: str = None) -> tuple[str, List[str], Dict[str, Any]]:
        """
        Categorize image by content using Gemini Vision API.

        Args:
            image_path: Path to image
            image_id: Image identifier for token tracking

        Returns:
            Tuple of (main_category, subcategories, token_usage)
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
                    log_warning(self.logger, f"Failed to resize image, using original: {e}", "Filtering & Categorization")
                    with open(image_path, 'rb') as f:
                        image_bytes = f.read()
                    media_type = get_optimized_media_type(image_path)
            else:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                media_type = get_optimized_media_type(image_path)

            # Create optimized prompt for categorization
            categories_list = ', '.join(self.CATEGORIES.keys())

            if self.use_concise_prompts:
                # Optimized concise prompt
                prompt = f"""{self.SYSTEM_PROMPT}

{{
    "main_category": "<{categories_list}>",
    "subcategories": ["<sub1>", "<sub2>"]
}}"""
            else:
                # Full detailed prompt
                prompt = f"""{self.SYSTEM_PROMPT}

TASK: Analyze this travel photograph and categorize it.

Valid main categories: {categories_list}

RESPONSE FORMAT: Provide response as a JSON object:
{{
    "main_category": "<one of the valid categories>",
    "subcategories": ["<subcategory1>", "<subcategory2>"]
}}

Choose the most appropriate main category and provide 1-2 specific subcategories that describe elements visible in the image.
Focus on travel photography context: sense of place, cultural elements, activity type."""

            # Call Gemini API via Vertex AI
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
            log_info(self.logger, f"Received Gemini categorization for {image_path.name}", "Filtering & Categorization")

            # Extract JSON from response
            main_cat, subcats = self._parse_categorization_response(response_text)

            # Track token usage and calculate cost
            token_usage = None
            if hasattr(response, 'usage_metadata'):
                token_usage = self.token_tracker.track_usage(response.usage_metadata, image_id)

                # Log per-image cost if enabled
                cost_config = self.config.get('cost_tracking', {})
                if cost_config.get('log_per_image', True):
                    log_info(
                        self.logger,
                        f"Token cost for {image_path.name}: ${token_usage['estimated_cost_usd']:.4f} "
                        f"({token_usage['total_token_count']} tokens)",
                        "Filtering & Categorization"
                    )

            return main_cat, subcats, token_usage

        except Exception as e:
            log_error(
                self.logger,
                "Filtering & Categorization",
                "APIError",
                f"Gemini API call failed for {image_path.name}: {str(e)}",
                "error"
            )
            # Return default category on failure
            return "Uncategorized", [], None

    def _parse_categorization_response(self, response_text: str) -> tuple[str, List[str]]:
        """
        Parse Gemini API response to extract category information.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Tuple of (main_category, subcategories)
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_json = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                response_json = self._extract_categories_from_text(response_text)

            main_category = response_json.get("main_category", "Uncategorized")
            subcategories = response_json.get("subcategories", [])

            # Validate main category is in our list
            valid_categories = list(self.CATEGORIES.keys())
            if main_category not in valid_categories:
                main_category = "Uncategorized"

            return main_category, subcategories

        except Exception as e:
            log_warning(self.logger, f"Failed to parse categorization response: {str(e)}", "Filtering & Categorization")
            return "Uncategorized", []

    def _extract_categories_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract categories from natural language response.

        Args:
            text: Natural language response text

        Returns:
            Dictionary with extracted categories
        """
        categories = {}

        # Try to find category keywords in text
        valid_categories = list(self.CATEGORIES.keys())
        for cat in valid_categories:
            if cat.lower() in text.lower():
                categories["main_category"] = cat
                break

        if "main_category" not in categories:
            categories["main_category"] = "Uncategorized"

        # Extract keywords as subcategories
        words = text.lower().split()
        subcategories = []
        for word in words:
            for cat, keywords in self.CATEGORIES.items():
                if word in keywords:
                    subcategories.append(word)

        categories["subcategories"] = list(set(subcategories))[:2]

        return categories

    def process_image(
        self,
        image_path: Path,
        metadata: Dict[str, Any],
        quality: Dict[str, Any],
        aesthetic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter and categorize a single image.

        Args:
            image_path: Path to image
            metadata: Metadata from Agent 1
            quality: Quality assessment from Agent 2
            aesthetic: Aesthetic assessment from Agent 3

        Returns:
            Categorization result
        """
        flags = []

        # Get scores
        technical_score = quality.get('quality_score', 3)
        aesthetic_score = aesthetic.get('overall_aesthetic', 3)

        # Apply filters
        passes_filter = (
            technical_score >= self.min_technical and
            aesthetic_score >= self.min_aesthetic
        )

        if technical_score < self.min_technical:
            flags.append('low_quality')

        if aesthetic_score < self.min_aesthetic:
            flags.append('low_aesthetic')

        # Check for missing data
        if not metadata.get('gps', {}).get('latitude'):
            flags.append('missing_gps')

        if not metadata.get('capture_datetime'):
            flags.append('missing_datetime')

        # Construct reasoning
        if passes_filter:
            reasoning = f"Passed all criteria. Quality Score: {technical_score}/5 (min: {self.min_technical}), Aesthetic Score: {aesthetic_score}/5 (min: {self.min_aesthetic})."
        else:
            reasons = []
            if technical_score < self.min_technical:
                reasons.append(f"Quality score ({technical_score}/5) below threshold ({self.min_technical})")
            if aesthetic_score < self.min_aesthetic:
                reasons.append(f"Aesthetic score ({aesthetic_score}/5) below threshold ({self.min_aesthetic})")
            reasoning = f"Rejected: {'; '.join(reasons)}."

        # Categorize
        try:
            image_id = metadata.get('image_id', image_path.stem)
            main_category, subcategories, token_usage = self.categorize_by_content(image_path, image_id)
            time_category = self.categorize_by_time(metadata)
            location = self.categorize_by_location(metadata)

            result = {
                'image_id': metadata['image_id'],
                'category': main_category,
                'subcategories': subcategories,
                'time_category': time_category,
                'location': location,
                'passes_filter': passes_filter,
                'flagged': len(flags) > 0,
                'flags': flags,
                'reasoning': reasoning
            }
            
            if token_usage:
                result['token_usage'] = token_usage

            # Validate
            is_valid, error_msg = validate_agent_output("filtering_categorization", result)
            if not is_valid:
                log_error(
                    self.logger,
                    "Filtering & Categorization",
                    "ValidationError",
                    f"Validation failed for {image_path.name}: {error_msg}",
                    "error"
                )

            return result

        except Exception as e:
            log_error(
                self.logger,
                "Filtering & Categorization",
                "ProcessingError",
                f"Failed to categorize {image_path.name}: {str(e)}",
                "error"
            )
            return {
                'image_id': metadata.get('image_id', image_path.stem),
                'category': 'Uncategorized',
                'subcategories': [],
                'time_category': 'Unknown',
                'location': None,
                'passes_filter': False,
                'flagged': True,
                'flags': ['processing_error']
            }

    def run(
        self,
        image_paths: List[Path],
        metadata_list: List[Dict[str, Any]],
        quality_assessments: List[Dict[str, Any]],
        aesthetic_assessments: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run filtering and categorization on all images.

        Args:
            image_paths: List of image paths
            metadata_list: Metadata from Agent 1
            quality_assessments: Quality assessments from Agent 2
            aesthetic_assessments: Aesthetic assessments from Agent 3

        Returns:
            Tuple of (categorization_list, validation_summary)
        """
        log_info(self.logger, f"Starting filtering and categorization for {len(image_paths)} images", "Filtering & Categorization")

        # Create lookups
        metadata_map = {m['image_id']: m for m in metadata_list}
        quality_map = {q['image_id']: q for q in quality_assessments}
        aesthetic_map = {a['image_id']: a for a in aesthetic_assessments}

        categorization_list = []
        issues = []

        for path in image_paths:
            image_id = path.stem

            try:
                metadata = metadata_map.get(image_id, {'image_id': image_id})
                quality = quality_map.get(image_id, {})
                aesthetic = aesthetic_map.get(image_id, {})

                result = self.process_image(path, metadata, quality, aesthetic)
                categorization_list.append(result)

                if result.get('flagged'):
                    issues.append(f"{image_id}: {', '.join(result['flags'])}")

            except Exception as e:
                error_msg = f"Failed to process {path.name}: {str(e)}"
                issues.append(error_msg)
                log_error(
                    self.logger,
                    "Filtering & Categorization",
                    "ExecutionError",
                    error_msg,
                    "error"
                )

        # Statistics
        passed = sum(1 for c in categorization_list if c['passes_filter'])
        flagged = sum(1 for c in categorization_list if c['flagged'])

        summary = f"Categorized {len(categorization_list)} images: {passed} passed filters, {flagged} flagged"

        # Get token usage summary
        usage_summary = self.token_tracker.get_summary()
        if usage_summary['images_processed'] > 0:
            log_info(
                self.logger,
                f"Total tokens used: {usage_summary['total_tokens']['total_tokens']:,} "
                f"(input: {usage_summary['total_tokens']['prompt_tokens']:,}, "
                f"output: {usage_summary['total_tokens']['completion_tokens']:,})",
                "Filtering & Categorization"
            )
            log_info(
                self.logger,
                f"Estimated cost: ${usage_summary['estimated_cost_usd']:.4f} "
                f"(avg: ${usage_summary['estimated_cost_usd']/usage_summary['images_processed']:.4f} per image)",
                "Filtering & Categorization"
            )

            # Check if cost exceeds threshold
            cost_config = self.config.get('cost_tracking', {})
            threshold = cost_config.get('alert_threshold_usd', 1.0)
            if usage_summary['estimated_cost_usd'] > threshold:
                log_warning(
                    self.logger,
                    f"Cost ${usage_summary['estimated_cost_usd']:.4f} exceeds threshold ${threshold:.2f}",
                    "Filtering & Categorization"
                )

        status = "success" if not issues else ("warning" if len(issues) < len(image_paths) else "error")

        validation = create_validation_summary(
            agent="Filtering & Categorization",
            stage="classification",
            status=status,
            summary=summary,
            issues=issues if issues else None
        )

        # Add token usage to validation
        if usage_summary['images_processed'] > 0:
            validation['token_usage'] = usage_summary

        log_info(self.logger, f"Filtering and categorization completed: {summary}", "Filtering & Categorization")

        return categorization_list, validation
