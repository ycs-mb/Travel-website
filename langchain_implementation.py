"""
LangChain Implementation of Travel Photo Organization Workflow

This module demonstrates how to convert the agentic workflow to use LangChain
primitives: chains, prompts, models, output parsers, and runnables.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
import json

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from pydantic import BaseModel, Field, validator

# Import original utilities
from utils.logger import setup_logger, log_error, log_info
from utils.helpers import load_config, save_json, get_image_files, ensure_directories
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
from geopy.geocoders import Nominatim


# ============================================================================
# Pydantic Output Schemas (replaces validation.py)
# ============================================================================

class MetadataOutput(BaseModel):
    """Schema for metadata extraction output."""
    image_id: str
    filename: str
    file_size_bytes: int
    format: str
    dimensions: Dict[str, int]
    capture_datetime: Optional[str] = None
    gps: Dict[str, Optional[float]]
    camera_settings: Dict[str, Any]
    flags: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class AestheticOutput(BaseModel):
    """Schema for aesthetic assessment output."""
    image_id: str
    composition: int = Field(ge=1, le=5)
    framing: int = Field(ge=1, le=5)
    lighting: int = Field(ge=1, le=5)
    subject_interest: int = Field(ge=1, le=5)
    overall_aesthetic: int = Field(ge=1, le=5)
    notes: str

    @validator('overall_aesthetic', pre=True, always=True)
    def calculate_overall(cls, v, values):
        """Calculate overall aesthetic as weighted average."""
        if v is None or v == 0:
            return int(round(
                values.get('composition', 3) * 0.30 +
                values.get('framing', 3) * 0.25 +
                values.get('lighting', 3) * 0.25 +
                values.get('subject_interest', 3) * 0.20
            ))
        return v


class QualityOutput(BaseModel):
    """Schema for quality assessment output."""
    image_id: str
    quality_score: int = Field(ge=1, le=5)
    sharpness: float = Field(ge=0, le=1)
    noise_level: float = Field(ge=0, le=1)
    exposure_quality: float = Field(ge=0, le=1)
    color_accuracy: float = Field(ge=0, le=1)
    notes: str


class FilteringOutput(BaseModel):
    """Schema for filtering and categorization output."""
    image_id: str
    passes_filter: bool
    category: str
    primary_subject: str
    flagged: bool
    flag_reason: Optional[str] = None


class CaptionOutput(BaseModel):
    """Schema for caption generation output."""
    image_id: str
    caption: str
    keywords: List[str]
    description: str


# ============================================================================
# LangChain Agents
# ============================================================================

class LangChainMetadataAgent:
    """
    Agent 1: Metadata Extraction using LangChain patterns.

    This agent doesn't use LLMs but demonstrates LangChain's Runnable interface
    for consistency across the workflow.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('metadata_extraction', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 4)
        self.geolocator = Nominatim(user_agent="travel-photo-workflow")

    def _extract_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Extract metadata from image file."""
        flags = []
        exif_raw = {}

        try:
            file_size = image_path.stat().st_size

            with Image.open(image_path) as img:
                width, height = img.size
                img_format = img.format
                exif_data = img.getexif()

                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        try:
                            if isinstance(value, bytes):
                                value = value.decode('utf-8', errors='ignore')
                            else:
                                value = str(value)[:200]
                            exif_raw[tag] = value
                        except Exception:
                            pass

                if not exif_data:
                    flags.append("missing_exif")

            # Extract structured data
            gps_info = self._extract_gps(exif_raw)
            camera_settings = self._extract_camera_settings(exif_raw)
            capture_datetime = self._extract_datetime(exif_raw)

            if not capture_datetime:
                flags.append("missing_datetime")
            if not any(gps_info.values()):
                flags.append("missing_gps")

            metadata = {
                "image_id": image_path.stem,
                "filename": image_path.name,
                "file_size_bytes": file_size,
                "format": img_format,
                "dimensions": {"width": width, "height": height},
                "capture_datetime": capture_datetime,
                "gps": gps_info,
                "camera_settings": camera_settings,
                "exif_raw": exif_raw,
                "flags": flags
            }

            # Validate using Pydantic
            validated = MetadataOutput(**metadata)
            return validated.dict()

        except Exception as e:
            log_error(self.logger, "Metadata Extraction", "ProcessingError", str(e), "error")
            return MetadataOutput(
                image_id=image_path.stem,
                filename=image_path.name,
                file_size_bytes=0,
                format="unknown",
                dimensions={"width": 0, "height": 0},
                gps={"latitude": None, "longitude": None, "altitude": None},
                camera_settings={},
                flags=["processing_error"]
            ).dict()

    def _extract_gps(self, exif_data: Dict) -> Dict[str, Optional[float]]:
        """Extract GPS coordinates."""
        return {
            "latitude": None,
            "longitude": None,
            "altitude": None,
            "location": None
        }

    def _extract_camera_settings(self, exif_data: Dict) -> Dict[str, Any]:
        """Extract camera settings."""
        return {
            "iso": exif_data.get("ISOSpeedRatings"),
            "aperture": None,
            "shutter_speed": None,
            "focal_length": None,
            "camera_model": exif_data.get("Model"),
            "lens_model": exif_data.get("LensModel")
        }

    def _extract_datetime(self, exif_data: Dict) -> Optional[str]:
        """Extract capture datetime."""
        for field in ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']:
            if field in exif_data:
                return exif_data[field]
        return None

    def run(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """Run metadata extraction in parallel."""
        log_info(self.logger, f"Processing {len(image_paths)} images", "Metadata Extraction")

        results = []
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {executor.submit(self._extract_metadata, path): path for path in image_paths}
            for future in as_completed(futures):
                results.append(future.result())

        return results


class LangChainAestheticAgent:
    """
    Agent 3: Aesthetic Assessment using LangChain's VLM integration.

    Uses ChatGoogleGenerativeAI with vision capabilities.
    """

    SYSTEM_PROMPT = """You are a world-renowned photo curator and aesthetic expert with decades of
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
    - 1: Poor aesthetic value"""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('aesthetic_assessment', {})
        self.parallel_workers = self.agent_config.get('parallel_workers', 2)

        # Load environment variables from .env file
        load_dotenv()

        # Initialize LangChain VLM
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        self.model = ChatGoogleGenerativeAI(
            model=config.get('api', {}).get('google', {}).get('model', 'gemini-2.0-flash-exp'),
            temperature=0.7,
            google_api_key=api_key
        )

        # Create LangChain prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", [
                {
                    "type": "text",
                    "text": """Analyze this travel photograph and provide aesthetic assessment scores.

Image metadata:
- Capture time: {capture_datetime}
- Location: {location}
- Camera: {camera_model}
- ISO: {iso}

RESPONSE FORMAT: Provide your response as a JSON object with this exact structure:
{{
    "composition": <1-5>,
    "framing": <1-5>,
    "lighting": <1-5>,
    "subject_interest": <1-5>,
    "notes": "<brief analysis of aesthetic strengths and weaknesses>"
}}"""
                },
                {
                    "type": "image_url",
                    "image_url": "data:image/jpeg;base64,{image_data}"
                }
            ])
        ])

        # Create output parser
        self.output_parser = JsonOutputParser(pydantic_object=AestheticOutput)

        # Create LangChain chain
        self.chain = self.prompt | self.model | self.output_parser

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64."""
        with open(image_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')

    def _assess_single(self, image_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess a single image using LangChain chain."""
        try:
            image_data = self._encode_image(image_path)
            gps = metadata.get('gps', {})
            camera = metadata.get('camera_settings', {})

            result = self.chain.invoke({
                "image_data": image_data,
                "capture_datetime": metadata.get('capture_datetime', 'unknown'),
                "location": f"{gps.get('latitude', 'N/A')}, {gps.get('longitude', 'N/A')}",
                "camera_model": camera.get('camera_model', 'unknown'),
                "iso": camera.get('iso', 'unknown')
            })

            # Add image_id
            result['image_id'] = metadata['image_id']

            # Validate using Pydantic
            validated = AestheticOutput(**result)
            return validated.dict()

        except Exception as e:
            log_error(self.logger, "Aesthetic Assessment", "APIError", str(e), "error")
            return AestheticOutput(
                image_id=metadata['image_id'],
                composition=3,
                framing=3,
                lighting=3,
                subject_interest=3,
                overall_aesthetic=3,
                notes=f"Assessment failed: {str(e)}"
            ).dict()

    def run(self, image_paths: List[Path], metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aesthetic assessment on all images."""
        log_info(self.logger, f"Assessing {len(image_paths)} images", "Aesthetic Assessment")

        metadata_map = {m['image_id']: m for m in metadata_list}
        results = []

        # Process in batches to respect API rate limits
        batch_size = self.agent_config.get('batch_size', 5)
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]

            with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
                futures = []
                for path in batch_paths:
                    metadata = metadata_map.get(path.stem, {'image_id': path.stem})
                    futures.append(executor.submit(self._assess_single, path, metadata))

                for future in as_completed(futures):
                    results.append(future.result())

        return results


class LangChainCaptionAgent:
    """
    Agent 6: Caption Generation using LangChain chains.

    Demonstrates LLMChain pattern with structured output.
    """

    SYSTEM_PROMPT = """You are an expert travel photography caption writer.
    Create engaging, descriptive captions that capture the essence of each photograph."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.agent_config = config.get('agents', {}).get('caption_generation', {})

        # Load environment variables from .env file
        load_dotenv()

        # Initialize LangChain LLM
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")

        self.model = ChatGoogleGenerativeAI(
            model=config.get('api', {}).get('google', {}).get('model', 'gemini-2.0-flash-exp'),
            temperature=0.7,
            google_api_key=api_key
        )

        # Create prompt template
        self.prompt = PromptTemplate.from_template(
            """You are an expert travel photography caption writer.

Create an engaging caption for this photograph:

Location: {location}
Capture Time: {capture_time}
Technical Quality: {quality_score}/5
Aesthetic Quality: {aesthetic_score}/5
Category: {category}

Provide a JSON response with:
{{
    "caption": "<engaging 1-2 sentence caption>",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "description": "<detailed 2-3 sentence description>"
}}"""
        )

        # Create output parser
        self.output_parser = JsonOutputParser(pydantic_object=CaptionOutput)

        # Create chain using LCEL (LangChain Expression Language)
        self.chain = self.prompt | self.model | self.output_parser

    def _generate_caption(
        self,
        image_path: Path,
        metadata: Dict,
        quality: Dict,
        aesthetic: Dict,
        filtering: Dict
    ) -> Dict[str, Any]:
        """Generate caption for a single image."""
        try:
            result = self.chain.invoke({
                "location": metadata.get('gps', {}).get('location', 'Unknown location'),
                "capture_time": metadata.get('capture_datetime', 'Unknown time'),
                "quality_score": quality.get('quality_score', 3),
                "aesthetic_score": aesthetic.get('overall_aesthetic', 3),
                "category": filtering.get('category', 'General')
            })

            result['image_id'] = metadata['image_id']

            # Validate
            validated = CaptionOutput(**result)
            return validated.dict()

        except Exception as e:
            log_error(self.logger, "Caption Generation", "GenerationError", str(e), "error")
            return CaptionOutput(
                image_id=metadata['image_id'],
                caption="A travel photograph.",
                keywords=["travel", "photography"],
                description="Unable to generate detailed description."
            ).dict()

    def run(
        self,
        image_paths: List[Path],
        metadata_list: List[Dict],
        quality_list: List[Dict],
        aesthetic_list: List[Dict],
        filtering_list: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate captions for all images."""
        log_info(self.logger, f"Generating captions for {len(image_paths)} images", "Caption Generation")

        # Create lookup maps
        metadata_map = {m['image_id']: m for m in metadata_list}
        quality_map = {q['image_id']: q for q in quality_list}
        aesthetic_map = {a['image_id']: a for a in aesthetic_list}
        filtering_map = {f['image_id']: f for f in filtering_list}

        results = []
        for path in image_paths:
            image_id = path.stem
            caption = self._generate_caption(
                path,
                metadata_map.get(image_id, {}),
                quality_map.get(image_id, {}),
                aesthetic_map.get(image_id, {}),
                filtering_map.get(image_id, {})
            )
            results.append(caption)

        return results


# ============================================================================
# LangChain Orchestrator
# ============================================================================

class LangChainOrchestrator:
    """
    Main orchestrator using LangChain patterns.

    Demonstrates sequential and parallel chain execution using RunnableParallel.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)

        # Setup logging
        self.timestamped_output = Path(self.config['paths']['output_dir'])
        self.logger = setup_logger(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.timestamped_output / 'logs' / 'langchain_workflow.log',
            json_format=True
        )

        ensure_directories(self.config)

        # Initialize LangChain agents
        self.metadata_agent = LangChainMetadataAgent(self.config, self.logger)
        self.aesthetic_agent = LangChainAestheticAgent(self.config, self.logger)
        self.caption_agent = LangChainCaptionAgent(self.config, self.logger)

        log_info(self.logger, "LangChain orchestrator initialized", "Orchestrator")

    def run_workflow(self) -> Dict[str, Any]:
        """Execute the workflow using LangChain patterns."""
        log_info(self.logger, "Starting LangChain workflow", "Orchestrator")

        # Get input images
        input_dir = Path(self.config['paths']['input_images'])
        image_paths = get_image_files(input_dir)

        if not image_paths:
            log_error(self.logger, "Orchestrator", "NoImages", f"No images in {input_dir}", "error")
            return {}

        log_info(self.logger, f"Processing {len(image_paths)} images", "Orchestrator")

        # Stage 1: Metadata Extraction
        metadata_list = self.metadata_agent.run(image_paths)

        # Stage 2: Aesthetic Assessment (parallel with Quality in full implementation)
        aesthetic_list = self.aesthetic_agent.run(image_paths, metadata_list)

        # For demo, create dummy quality and filtering outputs
        quality_list = [
            {"image_id": m['image_id'], "quality_score": 4, "notes": "Good quality"}
            for m in metadata_list
        ]
        filtering_list = [
            {"image_id": m['image_id'], "category": "Landscape", "passes_filter": True}
            for m in metadata_list
        ]

        # Stage 3: Caption Generation
        caption_list = self.caption_agent.run(
            image_paths,
            metadata_list,
            quality_list,
            aesthetic_list,
            filtering_list
        )

        # Save outputs
        output_dir = Path(self.config['paths']['reports_output'])
        save_json(metadata_list, output_dir / "langchain_metadata.json")
        save_json(aesthetic_list, output_dir / "langchain_aesthetic.json")
        save_json(caption_list, output_dir / "langchain_captions.json")

        log_info(self.logger, "LangChain workflow completed", "Orchestrator")

        return {
            "num_images": len(image_paths),
            "metadata": metadata_list,
            "aesthetic": aesthetic_list,
            "captions": caption_list
        }


def main():
    """Main entry point for LangChain implementation."""
    # Load environment variables from .env file
    load_dotenv()

    print("\n" + "=" * 80)
    print("LANGCHAIN IMPLEMENTATION - Travel Photo Organization")
    print("=" * 80 + "\n")

    try:
        orchestrator = LangChainOrchestrator()
        result = orchestrator.run_workflow()

        print(f"\n✓ Successfully processed {result['num_images']} images using LangChain")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
