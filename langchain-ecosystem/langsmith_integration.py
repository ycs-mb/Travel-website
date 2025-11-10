"""
LangSmith Integration for Travel Photo Organization Workflow

This module demonstrates how to integrate LangSmith for:
- Observability: Tracing LLM calls and agent executions
- Monitoring: Tracking performance, errors, and costs
- Evaluation: Running test datasets and comparing outputs
- Debugging: Inspecting intermediate states and outputs
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import time
import base64

# Add parent directory to path for importing from no-framework
sys.path.insert(0, str(Path(__file__).parent.parent / 'no-framework'))

from dotenv import load_dotenv
from langsmith import Client, traceable, trace
from langsmith.run_helpers import get_current_run_tree
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import original utilities from no-framework
from utils.logger import setup_logger, log_error, log_info
from utils.helpers import load_config, save_json, get_image_files, ensure_directories
from PIL import Image


# ============================================================================
# LangSmith Client Setup
# ============================================================================

def setup_langsmith_client() -> Client:
    """
    Initialize LangSmith client for observability.

    Environment variables required:
    - LANGCHAIN_API_KEY: Your LangSmith API key
    - LANGCHAIN_PROJECT: Project name (default: "travel-photo-workflow")
    - LANGCHAIN_TRACING_V2: Set to "true" to enable tracing
    """
    # Load environment variables from .env file
    load_dotenv()

    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("[LangSmith] WARNING: LANGCHAIN_API_KEY not set. Tracing disabled.")
        return None

    # Enable tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = os.getenv(
        "LANGCHAIN_PROJECT",
        "travel-photo-workflow"
    )

    client = Client()
    print(f"[LangSmith] Connected to project: {os.environ['LANGCHAIN_PROJECT']}")

    return client


# ============================================================================
# Traceable Agent Functions
# ============================================================================

@traceable(
    name="metadata_extraction",
    run_type="chain",
    metadata={"agent": "metadata_extraction", "version": "1.0"}
)
def extract_metadata_with_tracing(image_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from image with LangSmith tracing.

    The @traceable decorator automatically:
    - Logs inputs (image_path)
    - Logs outputs (metadata dict)
    - Tracks execution time
    - Records errors if any
    - Links to parent trace
    """
    start_time = time.time()

    try:
        with Image.open(image_path) as img:
            width, height = img.size
            img_format = img.format
            exif_data = img.getexif()

            metadata = {
                "image_id": image_path.stem,
                "filename": image_path.name,
                "file_size_bytes": image_path.stat().st_size,
                "format": img_format,
                "dimensions": {"width": width, "height": height},
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }

            # Add custom metadata to current trace
            run_tree = get_current_run_tree()
            if run_tree:
                run_tree.extra = {
                    "image_dimensions": f"{width}x{height}",
                    "file_size_mb": round(metadata["file_size_bytes"] / 1024 / 1024, 2),
                    "format": img_format
                }

            return metadata

    except Exception as e:
        # Errors are automatically logged by @traceable
        raise


@traceable(
    name="aesthetic_assessment",
    run_type="llm",
    metadata={"agent": "aesthetic_assessment", "model": "gemini-2.0-flash-exp"}
)
def assess_aesthetics_with_tracing(
    image_path: Path,
    metadata: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assess image aesthetics using VLM with LangSmith tracing.

    LangSmith will automatically capture:
    - Prompt sent to LLM
    - LLM response
    - Token usage
    - Latency
    - Cost estimation
    """
    # Load environment variables from .env file
    load_dotenv()

    start_time = time.time()

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return {
            "image_id": metadata["image_id"],
            "composition": 3,
            "framing": 3,
            "lighting": 3,
            "subject_interest": 3,
            "overall_aesthetic": 3,
            "notes": "API key not available"
        }

    model = ChatGoogleGenerativeAI(
        model=config.get('api', {}).get('google', {}).get('model', 'gemini-2.0-flash-exp'),
        temperature=0.7,
        google_api_key=api_key
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a world-renowned photo curator and aesthetic expert.
Evaluate images on: composition (1-5), framing (1-5), lighting (1-5), subject_interest (1-5).
Respond with JSON: {"composition": X, "framing": Y, "lighting": Z, "subject_interest": W, "notes": "..."}"""),
        ("human", [
            {"type": "text", "text": "Analyze this travel photograph for aesthetic quality."},
            {"type": "image_url", "image_url": "data:image/jpeg;base64,{image_data}"}
        ])
    ])

    chain = prompt | model | JsonOutputParser()

    try:
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        result = chain.invoke({"image_data": image_data})
        result["image_id"] = metadata["image_id"]

        # Calculate overall aesthetic
        result["overall_aesthetic"] = int(round(
            result.get("composition", 3) * 0.30 +
            result.get("framing", 3) * 0.25 +
            result.get("lighting", 3) * 0.25 +
            result.get("subject_interest", 3) * 0.20
        ))

        # Add custom metrics to trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.extra = {
                "overall_score": result["overall_aesthetic"],
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "image_id": metadata["image_id"]
            }

        return result

    except Exception as e:
        # Log error with context
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.extra = {"error": str(e)}

        return {
            "image_id": metadata["image_id"],
            "composition": 3,
            "framing": 3,
            "lighting": 3,
            "subject_interest": 3,
            "overall_aesthetic": 3,
            "notes": f"Error: {str(e)}"
        }


@traceable(
    name="caption_generation",
    run_type="llm",
    metadata={"agent": "caption_generation", "model": "gemini-2.0-flash-exp"}
)
def generate_caption_with_tracing(
    metadata: Dict[str, Any],
    quality: Dict[str, Any],
    aesthetic: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate caption with LangSmith tracing.

    Demonstrates chaining multiple LLM calls with nested tracing.
    """
    # Load environment variables from .env file
    load_dotenv()

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return {
            "image_id": metadata["image_id"],
            "caption": f"A travel photograph: {metadata['filename']}",
            "keywords": ["travel", "photography"],
            "description": "API key not available"
        }

    model = ChatGoogleGenerativeAI(
        model=config.get('api', {}).get('google', {}).get('model', 'gemini-2.0-flash-exp'),
        temperature=0.7,
        google_api_key=api_key
    )

    prompt = ChatPromptTemplate.from_template(
        """Create an engaging travel photo caption.

Quality: {quality}/5
Aesthetic: {aesthetic}/5
Filename: {filename}

Respond with JSON:
{{
    "caption": "<1-2 sentence engaging caption>",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "description": "<2-3 sentence detailed description>"
}}"""
    )

    chain = prompt | model | JsonOutputParser()

    try:
        result = chain.invoke({
            "quality": quality.get("quality_score", 3),
            "aesthetic": aesthetic.get("overall_aesthetic", 3),
            "filename": metadata.get("filename", "unknown")
        })

        result["image_id"] = metadata["image_id"]

        # Add metrics to trace
        run_tree = get_current_run_tree()
        if run_tree:
            run_tree.extra = {
                "caption_length": len(result.get("caption", "")),
                "num_keywords": len(result.get("keywords", [])),
                "image_id": metadata["image_id"]
            }

        return result

    except Exception as e:
        return {
            "image_id": metadata["image_id"],
            "caption": f"A travel photograph: {metadata.get('filename', 'unknown')}",
            "keywords": ["travel", "photography"],
            "description": f"Error: {str(e)}"
        }


# ============================================================================
# Workflow-Level Tracing
# ============================================================================

@traceable(
    name="travel_photo_workflow",
    run_type="chain",
    metadata={"workflow": "complete", "version": "1.0"}
)
def run_workflow_with_tracing(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute complete workflow with LangSmith tracing.

    This creates a top-level trace that contains all agent traces as children.
    Provides a hierarchical view of the entire workflow execution.
    """
    print("\n[LangSmith] Starting traced workflow execution")

    # Get input images
    input_dir = Path(config['paths']['input_images'])
    image_paths = get_image_files(input_dir)

    if not image_paths:
        raise ValueError(f"No images found in {input_dir}")

    print(f"[LangSmith] Processing {len(image_paths)} images")

    # Stage 1: Metadata Extraction (traced)
    print("\n[LangSmith] Stage 1: Metadata Extraction")
    metadata_list = []
    for path in image_paths:
        metadata = extract_metadata_with_tracing(path)
        metadata_list.append(metadata)

    # Stage 2: Quality Assessment (simplified, would use actual model)
    print("\n[LangSmith] Stage 2: Quality Assessment")
    quality_list = []
    for metadata in metadata_list:
        dimensions = metadata.get("dimensions", {})
        total_pixels = dimensions.get("width", 0) * dimensions.get("height", 0)

        quality = {
            "image_id": metadata["image_id"],
            "quality_score": 4 if total_pixels > 8000000 else 3,
            "sharpness": 0.8,
            "notes": f"Based on {total_pixels} pixels"
        }
        quality_list.append(quality)

    # Stage 3: Aesthetic Assessment (traced with LLM calls)
    print("\n[LangSmith] Stage 3: Aesthetic Assessment")
    aesthetic_list = []
    for i, path in enumerate(image_paths[:3]):  # Limit for demo
        aesthetic = assess_aesthetics_with_tracing(path, metadata_list[i], config)
        aesthetic_list.append(aesthetic)

    # Fill remaining with defaults
    for metadata in metadata_list[3:]:
        aesthetic_list.append({
            "image_id": metadata["image_id"],
            "composition": 3,
            "framing": 3,
            "lighting": 3,
            "subject_interest": 3,
            "overall_aesthetic": 3,
            "notes": "Skipped for demo"
        })

    # Stage 4: Caption Generation (traced with LLM calls)
    print("\n[LangSmith] Stage 4: Caption Generation")
    caption_list = []
    quality_map = {q["image_id"]: q for q in quality_list}
    aesthetic_map = {a["image_id"]: a for a in aesthetic_list}

    for metadata in metadata_list[:3]:  # Limit for demo
        caption = generate_caption_with_tracing(
            metadata,
            quality_map.get(metadata["image_id"], {}),
            aesthetic_map.get(metadata["image_id"], {}),
            config
        )
        caption_list.append(caption)

    # Fill remaining with defaults
    for metadata in metadata_list[3:]:
        caption_list.append({
            "image_id": metadata["image_id"],
            "caption": f"A travel photograph: {metadata['filename']}",
            "keywords": ["travel"],
            "description": "Skipped for demo"
        })

    # Generate final report
    avg_quality = sum(q["quality_score"] for q in quality_list) / len(quality_list)
    avg_aesthetic = sum(a["overall_aesthetic"] for a in aesthetic_list) / len(aesthetic_list)

    final_report = {
        "workflow": "LangSmith Traced Workflow",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "num_images_processed": len(metadata_list),
        "average_quality": round(avg_quality, 2),
        "average_aesthetic": round(avg_aesthetic, 2),
        "stages_completed": [
            "metadata_extraction",
            "quality_assessment",
            "aesthetic_assessment",
            "caption_generation"
        ]
    }

    # Add workflow-level metrics to trace
    run_tree = get_current_run_tree()
    if run_tree:
        run_tree.extra = {
            "total_images": len(image_paths),
            "avg_quality": final_report["average_quality"],
            "avg_aesthetic": final_report["average_aesthetic"]
        }

    print(f"\n[LangSmith] Workflow completed: {final_report['num_images_processed']} images")

    return {
        "report": final_report,
        "metadata": metadata_list,
        "quality": quality_list,
        "aesthetic": aesthetic_list,
        "captions": caption_list
    }


# ============================================================================
# Evaluation with LangSmith
# ============================================================================

def create_evaluation_dataset(client: Client, dataset_name: str = "travel-photo-eval"):
    """
    Create a LangSmith dataset for evaluation.

    Datasets allow you to:
    - Store test cases with expected outputs
    - Run evaluations across multiple runs
    - Compare model versions
    - Track performance metrics over time
    """
    try:
        # Create or get dataset
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Evaluation dataset for travel photo workflow"
        )
        print(f"[LangSmith] Created dataset: {dataset_name}")

        # Add example test cases
        examples = [
            {
                "inputs": {
                    "image_id": "test_img_001",
                    "quality_score": 5,
                    "aesthetic_score": 5
                },
                "outputs": {
                    "caption_length_min": 50,
                    "has_keywords": True,
                    "tone": "engaging"
                }
            },
            {
                "inputs": {
                    "image_id": "test_img_002",
                    "quality_score": 3,
                    "aesthetic_score": 3
                },
                "outputs": {
                    "caption_length_min": 30,
                    "has_keywords": True,
                    "tone": "descriptive"
                }
            }
        ]

        for example in examples:
            client.create_example(
                inputs=example["inputs"],
                outputs=example["outputs"],
                dataset_id=dataset.id
            )

        print(f"[LangSmith] Added {len(examples)} examples to dataset")

        return dataset

    except Exception as e:
        print(f"[LangSmith] Error creating dataset: {str(e)}")
        return None


def evaluate_workflow(client: Client, dataset_name: str = "travel-photo-eval"):
    """
    Evaluate workflow using LangSmith.

    Demonstrates:
    - Running evaluations on test datasets
    - Custom evaluator functions
    - Comparing multiple runs
    - Tracking metrics over time
    """
    print("\n[LangSmith] Running workflow evaluation")

    def caption_quality_evaluator(run, example):
        """Custom evaluator for caption quality."""
        try:
            outputs = run.outputs
            expected = example.outputs

            caption = outputs.get("caption", "")
            keywords = outputs.get("keywords", [])

            # Check caption length
            length_ok = len(caption) >= expected.get("caption_length_min", 0)

            # Check keywords present
            keywords_ok = len(keywords) > 0 if expected.get("has_keywords") else True

            # Overall score
            score = 1.0 if (length_ok and keywords_ok) else 0.5

            return {
                "key": "caption_quality",
                "score": score,
                "comment": f"Length: {len(caption)}, Keywords: {len(keywords)}"
            }

        except Exception as e:
            return {"key": "caption_quality", "score": 0.0, "comment": f"Error: {str(e)}"}

    # Run evaluation
    try:
        results = evaluate(
            lambda inputs: generate_caption_with_tracing(
                {"image_id": inputs["image_id"], "filename": "test.jpg"},
                {"quality_score": inputs["quality_score"]},
                {"overall_aesthetic": inputs["aesthetic_score"]},
                {}
            ),
            data=dataset_name,
            evaluators=[caption_quality_evaluator],
            experiment_prefix="caption-eval"
        )

        print(f"[LangSmith] Evaluation completed: {results}")

        return results

    except Exception as e:
        print(f"[LangSmith] Evaluation error: {str(e)}")
        return None


# ============================================================================
# LangSmith Orchestrator
# ============================================================================

class LangSmithOrchestrator:
    """
    Orchestrator with full LangSmith integration.

    Provides:
    - Automatic tracing of all operations
    - Performance monitoring
    - Error tracking
    - Cost estimation
    - Evaluation capabilities
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)

        # Setup LangSmith
        self.client = setup_langsmith_client()

        # Setup logging
        self.timestamped_output = Path(self.config['paths']['output_dir'])
        self.logger = setup_logger(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.timestamped_output / 'logs' / 'langsmith_workflow.log',
            json_format=True
        )

        ensure_directories(self.config)

        log_info(self.logger, "LangSmith orchestrator initialized", "Orchestrator")

        if self.client:
            print(f"[LangSmith] Tracing enabled. View traces at: https://smith.langchain.com")
            print(f"[LangSmith] Project: {os.environ.get('LANGCHAIN_PROJECT')}")

    def run_workflow(self) -> Dict[str, Any]:
        """Execute workflow with full LangSmith tracing."""
        log_info(self.logger, "Starting LangSmith-traced workflow", "Orchestrator")

        # Run traced workflow
        result = run_workflow_with_tracing(self.config)

        # Save outputs
        output_dir = Path(self.config['paths']['reports_output'])
        save_json(result["report"], output_dir / "langsmith_final_report.json")
        save_json(result["metadata"], output_dir / "langsmith_metadata.json")
        save_json(result["aesthetic"], output_dir / "langsmith_aesthetic.json")
        save_json(result["captions"], output_dir / "langsmith_captions.json")

        log_info(self.logger, "LangSmith workflow completed", "Orchestrator")

        return result["report"]

    def create_evaluation_dataset(self):
        """Create evaluation dataset in LangSmith."""
        if self.client:
            return create_evaluation_dataset(self.client)
        else:
            print("[LangSmith] Client not initialized, skipping dataset creation")
            return None

    def run_evaluation(self):
        """Run workflow evaluation."""
        if self.client:
            return evaluate_workflow(self.client)
        else:
            print("[LangSmith] Client not initialized, skipping evaluation")
            return None


def main():
    """Main entry point for LangSmith integration."""
    # Load environment variables from .env file
    load_dotenv()

    print("\n" + "=" * 80)
    print("LANGSMITH INTEGRATION - Travel Photo Organization")
    print("Observability, Monitoring, and Evaluation")
    print("=" * 80 + "\n")

    try:
        orchestrator = LangSmithOrchestrator()

        # Run traced workflow
        print("\n[LangSmith] Running traced workflow...")
        final_report = orchestrator.run_workflow()

        print("\n" + "=" * 80)
        print("[LangSmith] WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"Images Processed: {final_report['num_images_processed']}")
        print(f"Average Quality: {final_report['average_quality']}/5")
        print(f"Average Aesthetic: {final_report['average_aesthetic']}/5")
        print("=" * 80 + "\n")

        # Create evaluation dataset (optional)
        # print("\n[LangSmith] Creating evaluation dataset...")
        # orchestrator.create_evaluation_dataset()

        # Run evaluation (optional)
        # print("\n[LangSmith] Running evaluation...")
        # orchestrator.run_evaluation()

        print("\n✓ LangSmith integration completed successfully!")
        print("\nView traces at: https://smith.langchain.com")

    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
