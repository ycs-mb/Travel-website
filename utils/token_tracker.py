"""Token usage tracking and cost estimation utilities."""

from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image
import io


class TokenTracker:
    """
    Track token usage and estimate costs for Vertex AI API calls.

    Pricing based on Gemini 1.5 Flash (as of December 2025):
    - Input: $0.075 per 1M tokens (≤128K context)
    - Output: $0.30 per 1M tokens
    """

    # Default pricing (per 1000 tokens)
    DEFAULT_PRICING = {
        'input_per_1k': 0.000075,   # $0.075 per 1M tokens
        'output_per_1k': 0.0003     # $0.30 per 1M tokens
    }

    def __init__(self, pricing: Optional[Dict[str, float]] = None):
        """
        Initialize token tracker.

        Args:
            pricing: Optional custom pricing dict with 'input_per_1k' and 'output_per_1k' keys
        """
        self.pricing = pricing or self.DEFAULT_PRICING
        self.total_tokens = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }
        self.per_image_usage = []

    def track_usage(self, usage_metadata: Any, image_id: str = None) -> Dict[str, Any]:
        """
        Track token usage from Vertex AI response metadata.

        Args:
            usage_metadata: Response.usage_metadata from Vertex AI
            image_id: Optional image identifier

        Returns:
            Dictionary with token counts and estimated cost
        """
        prompt_tokens = getattr(usage_metadata, 'prompt_token_count', 0)
        completion_tokens = getattr(usage_metadata, 'candidates_token_count', 0)
        total_tokens = getattr(usage_metadata, 'total_token_count', 0)

        # Calculate cost for this request
        input_cost = (prompt_tokens / 1000) * self.pricing['input_per_1k']
        output_cost = (completion_tokens / 1000) * self.pricing['output_per_1k']
        total_cost = input_cost + output_cost

        # Update running totals
        self.total_tokens['prompt_tokens'] += prompt_tokens
        self.total_tokens['completion_tokens'] += completion_tokens
        self.total_tokens['total_tokens'] += total_tokens

        # Track per-image usage
        usage_record = {
            'image_id': image_id,
            'prompt_token_count': prompt_tokens,
            'candidates_token_count': completion_tokens,
            'total_token_count': total_tokens,
            'estimated_cost_usd': total_cost
        }
        self.per_image_usage.append(usage_record)

        return usage_record

    def get_summary(self) -> Dict[str, Any]:
        """
        Get aggregated token usage summary.

        Returns:
            Dictionary with total tokens, costs, and breakdown
        """
        input_cost = (self.total_tokens['prompt_tokens'] / 1000) * self.pricing['input_per_1k']
        output_cost = (self.total_tokens['completion_tokens'] / 1000) * self.pricing['output_per_1k']
        total_cost = input_cost + output_cost

        return {
            'total_tokens': self.total_tokens,
            'estimated_cost_usd': total_cost,
            'cost_breakdown': {
                'input_cost': input_cost,
                'output_cost': output_cost
            },
            'pricing': self.pricing,
            'images_processed': len(self.per_image_usage)
        }

    def reset(self):
        """Reset all tracking data."""
        self.total_tokens = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }
        self.per_image_usage = []


def resize_image_for_api(image_path: Path, max_dimension: int = 1024, quality: int = 85) -> bytes:
    """
    Resize image to reduce token usage while maintaining quality.

    Larger images consume more tokens in vision API calls. Resizing to 1024px
    can reduce token usage by 50-70% with minimal quality loss.

    Args:
        image_path: Path to image file
        max_dimension: Maximum width or height in pixels (default: 1024)
        quality: JPEG quality for output (1-100, default: 85)

    Returns:
        Image bytes ready for API upload
    """
    try:
        # Open image
        img = Image.open(image_path)

        # Convert to RGB if necessary
        if img.mode not in ('RGB', 'L'):
            if img.mode in ('RGBA', 'LA', 'P'):
                # Handle transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert('RGB')

        # Resize if needed (preserve aspect ratio)
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # Convert to bytes
        buffer = io.BytesIO()
        output_format = 'JPEG' if image_path.suffix.lower() in ['.jpg', '.jpeg'] else 'PNG'

        if output_format == 'JPEG':
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
        else:
            img.save(buffer, format='PNG', optimize=True)

        return buffer.getvalue()

    except Exception as e:
        # Fallback: return original file if resize fails
        with open(image_path, 'rb') as f:
            return f.read()


def get_optimized_media_type(image_path: Path) -> str:
    """
    Get appropriate media type for API upload.

    Args:
        image_path: Path to image file

    Returns:
        MIME type string
    """
    suffix = image_path.suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.heic': 'image/jpeg',  # HEIC converted to JPEG
    }
    return media_type_map.get(suffix, 'image/jpeg')
