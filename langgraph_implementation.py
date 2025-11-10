"""
LangGraph Implementation of Travel Photo Organization Workflow

This module demonstrates how to orchestrate the multi-agent workflow using LangGraph's
StateGraph with nodes, edges, conditional routing, and parallel execution.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from datetime import datetime
import operator
import base64

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Import original utilities
from utils.logger import setup_logger, log_error, log_info
from utils.helpers import load_config, save_json, get_image_files, ensure_directories
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim


# ============================================================================
# State Definition for LangGraph
# ============================================================================

class WorkflowState(TypedDict):
    """
    Shared state for the LangGraph workflow.

    This state is passed between all nodes in the graph.
    Using Annotated with operator.add for list fields ensures proper merging.
    """
    # Input
    image_paths: List[Path]
    config: Dict[str, Any]

    # Agent outputs (accumulated across workflow)
    metadata_list: Annotated[List[Dict], operator.add]
    quality_list: Annotated[List[Dict], operator.add]
    aesthetic_list: Annotated[List[Dict], operator.add]
    filtering_list: Annotated[List[Dict], operator.add]
    caption_list: Annotated[List[Dict], operator.add]

    # Workflow tracking
    current_stage: str
    errors: Annotated[List[str], operator.add]
    processed_count: int

    # Final output
    final_report: Optional[Dict[str, Any]]


# ============================================================================
# LangGraph Node Functions (Agent Implementations)
# ============================================================================

def metadata_extraction_node(state: WorkflowState) -> WorkflowState:
    """
    Node 1: Extract metadata from images.

    This is an entry node that processes raw images and extracts EXIF data.
    """
    print("\n[LangGraph] Stage 1: Metadata Extraction")

    image_paths = state["image_paths"]
    metadata_list = []

    for path in image_paths:
        try:
            with Image.open(path) as img:
                width, height = img.size
                img_format = img.format
                exif_data = img.getexif()

                exif_dict = {}
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        try:
                            if isinstance(value, bytes):
                                value = value.decode('utf-8', errors='ignore')
                            exif_dict[tag] = str(value)[:200]
                        except Exception:
                            pass

                metadata = {
                    "image_id": path.stem,
                    "filename": path.name,
                    "file_size_bytes": path.stat().st_size,
                    "format": img_format,
                    "dimensions": {"width": width, "height": height},
                    "capture_datetime": exif_dict.get("DateTimeOriginal"),
                    "gps": {"latitude": None, "longitude": None},
                    "camera_settings": {
                        "camera_model": exif_dict.get("Model"),
                        "iso": exif_dict.get("ISOSpeedRatings")
                    },
                    "flags": []
                }

                if not metadata["capture_datetime"]:
                    metadata["flags"].append("missing_datetime")

                metadata_list.append(metadata)

        except Exception as e:
            state["errors"].append(f"Metadata extraction failed for {path.name}: {str(e)}")

    print(f"[LangGraph] Extracted metadata for {len(metadata_list)} images")

    return {
        **state,
        "metadata_list": metadata_list,
        "current_stage": "metadata_complete",
        "processed_count": len(metadata_list)
    }


def quality_assessment_node(state: WorkflowState) -> WorkflowState:
    """
    Node 2: Assess technical quality of images.

    This node can run in parallel with aesthetic assessment.
    """
    print("\n[LangGraph] Stage 2a: Quality Assessment")

    metadata_list = state["metadata_list"]
    quality_list = []

    # Simplified quality assessment (in production, use actual CV models)
    for metadata in metadata_list:
        dimensions = metadata.get("dimensions", {})
        width = dimensions.get("width", 0)
        height = dimensions.get("height", 0)
        total_pixels = width * height

        # Simple heuristic based on resolution
        if total_pixels > 12000000:  # > 12MP
            quality_score = 5
        elif total_pixels > 8000000:  # > 8MP
            quality_score = 4
        elif total_pixels > 4000000:  # > 4MP
            quality_score = 3
        elif total_pixels > 2000000:  # > 2MP
            quality_score = 2
        else:
            quality_score = 1

        quality = {
            "image_id": metadata["image_id"],
            "quality_score": quality_score,
            "sharpness": 0.8,
            "noise_level": 0.2,
            "exposure_quality": 0.85,
            "color_accuracy": 0.9,
            "notes": f"Technical assessment based on {total_pixels} pixels"
        }
        quality_list.append(quality)

    print(f"[LangGraph] Assessed quality for {len(quality_list)} images")

    return {
        **state,
        "quality_list": quality_list,
        "current_stage": "quality_complete"
    }


def aesthetic_assessment_node(state: WorkflowState) -> WorkflowState:
    """
    Node 3: Assess aesthetic quality using VLM.

    This node runs in parallel with quality assessment and uses
    Gemini Vision API for aesthetic evaluation.
    """
    print("\n[LangGraph] Stage 2b: Aesthetic Assessment")

    config = state["config"]
    metadata_list = state["metadata_list"]
    image_paths = state["image_paths"]

    # Initialize Gemini VLM
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("[LangGraph] WARNING: GOOGLE_API_KEY not set, using default scores")
        # Return default assessments
        aesthetic_list = [
            {
                "image_id": m["image_id"],
                "composition": 3,
                "framing": 3,
                "lighting": 3,
                "subject_interest": 3,
                "overall_aesthetic": 3,
                "notes": "API key not available"
            }
            for m in metadata_list
        ]
        return {
            **state,
            "aesthetic_list": aesthetic_list,
            "current_stage": "aesthetic_complete"
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
            {"type": "text", "text": "Analyze this travel photograph and provide aesthetic scores."},
            {"type": "image_url", "image_url": "data:image/jpeg;base64,{image_data}"}
        ])
    ])

    chain = prompt | model | JsonOutputParser()

    aesthetic_list = []
    metadata_map = {m["image_id"]: m for m in metadata_list}

    for path in image_paths[:3]:  # Limit to first 3 for demo
        try:
            with open(path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            result = chain.invoke({"image_data": image_data})
            result["image_id"] = path.stem

            # Calculate overall
            result["overall_aesthetic"] = int(round(
                result.get("composition", 3) * 0.30 +
                result.get("framing", 3) * 0.25 +
                result.get("lighting", 3) * 0.25 +
                result.get("subject_interest", 3) * 0.20
            ))

            aesthetic_list.append(result)

        except Exception as e:
            aesthetic_list.append({
                "image_id": path.stem,
                "composition": 3,
                "framing": 3,
                "lighting": 3,
                "subject_interest": 3,
                "overall_aesthetic": 3,
                "notes": f"Error: {str(e)}"
            })

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

    print(f"[LangGraph] Assessed aesthetics for {len(aesthetic_list)} images")

    return {
        **state,
        "aesthetic_list": aesthetic_list,
        "current_stage": "aesthetic_complete"
    }


def filtering_categorization_node(state: WorkflowState) -> WorkflowState:
    """
    Node 4: Filter and categorize images based on quality thresholds.

    This node runs after both quality and aesthetic assessments complete.
    Demonstrates conditional logic based on prior agent outputs.
    """
    print("\n[LangGraph] Stage 3: Filtering & Categorization")

    config = state["config"]
    metadata_list = state["metadata_list"]
    quality_list = state["quality_list"]
    aesthetic_list = state["aesthetic_list"]

    # Get thresholds
    min_technical = config.get("thresholds", {}).get("min_technical_quality", 3)
    min_aesthetic = config.get("thresholds", {}).get("min_aesthetic_quality", 3)

    # Create lookup maps
    quality_map = {q["image_id"]: q for q in quality_list}
    aesthetic_map = {a["image_id"]: a for a in aesthetic_list}

    filtering_list = []

    for metadata in metadata_list:
        image_id = metadata["image_id"]
        quality = quality_map.get(image_id, {})
        aesthetic = aesthetic_map.get(image_id, {})

        quality_score = quality.get("quality_score", 0)
        aesthetic_score = aesthetic.get("overall_aesthetic", 0)

        # Apply filtering logic
        passes = (quality_score >= min_technical and aesthetic_score >= min_aesthetic)

        # Simple categorization
        if aesthetic.get("subject_interest", 3) >= 4:
            category = "Highlight"
        elif quality_score >= 4:
            category = "Premium"
        else:
            category = "Standard"

        filtering_result = {
            "image_id": image_id,
            "passes_filter": passes,
            "category": category,
            "primary_subject": "landscape",  # Simplified
            "flagged": not passes,
            "flag_reason": None if passes else "Below quality thresholds"
        }

        filtering_list.append(filtering_result)

    num_selected = sum(1 for f in filtering_list if f["passes_filter"])
    print(f"[LangGraph] Filtered: {num_selected}/{len(filtering_list)} images selected")

    return {
        **state,
        "filtering_list": filtering_list,
        "current_stage": "filtering_complete"
    }


def caption_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Node 5: Generate captions using LLM.

    Final processing node that synthesizes information from all prior agents.
    """
    print("\n[LangGraph] Stage 4: Caption Generation")

    config = state["config"]
    metadata_list = state["metadata_list"]
    quality_list = state["quality_list"]
    aesthetic_list = state["aesthetic_list"]
    filtering_list = state["filtering_list"]

    # Initialize LLM
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("[LangGraph] WARNING: GOOGLE_API_KEY not set, using default captions")
        caption_list = [
            {
                "image_id": m["image_id"],
                "caption": f"A travel photograph: {m['filename']}",
                "keywords": ["travel", "photography"],
                "description": "Unable to generate detailed caption without API key."
            }
            for m in metadata_list
        ]
        return {
            **state,
            "caption_list": caption_list,
            "current_stage": "caption_complete"
        }

    model = ChatGoogleGenerativeAI(
        model=config.get('api', {}).get('google', {}).get('model', 'gemini-2.0-flash-exp'),
        temperature=0.7,
        google_api_key=api_key
    )

    prompt = ChatPromptTemplate.from_template(
        """Create an engaging travel photo caption.

Location: {location}
Time: {time}
Quality: {quality}/5
Aesthetic: {aesthetic}/5
Category: {category}

Respond with JSON:
{{
    "caption": "<1-2 sentence engaging caption>",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "description": "<2-3 sentence detailed description>"
}}"""
    )

    chain = prompt | model | JsonOutputParser()

    # Create lookup maps
    quality_map = {q["image_id"]: q for q in quality_list}
    aesthetic_map = {a["image_id"]: a for a in aesthetic_list}
    filtering_map = {f["image_id"]: f for f in filtering_list}

    caption_list = []

    for metadata in metadata_list:
        image_id = metadata["image_id"]
        quality = quality_map.get(image_id, {})
        aesthetic = aesthetic_map.get(image_id, {})
        filtering = filtering_map.get(image_id, {})

        try:
            result = chain.invoke({
                "location": metadata.get("gps", {}).get("location", "Unknown location"),
                "time": metadata.get("capture_datetime", "Unknown time"),
                "quality": quality.get("quality_score", 3),
                "aesthetic": aesthetic.get("overall_aesthetic", 3),
                "category": filtering.get("category", "Standard")
            })

            result["image_id"] = image_id
            caption_list.append(result)

        except Exception as e:
            caption_list.append({
                "image_id": image_id,
                "caption": f"A travel photograph: {metadata['filename']}",
                "keywords": ["travel", "photography"],
                "description": f"Caption generation error: {str(e)}"
            })

    print(f"[LangGraph] Generated captions for {len(caption_list)} images")

    return {
        **state,
        "caption_list": caption_list,
        "current_stage": "caption_complete"
    }


def final_report_node(state: WorkflowState) -> WorkflowState:
    """
    Final node: Generate comprehensive workflow report.

    Aggregates statistics from all agents and creates final output.
    """
    print("\n[LangGraph] Stage 5: Final Report Generation")

    metadata_list = state["metadata_list"]
    quality_list = state["quality_list"]
    aesthetic_list = state["aesthetic_list"]
    filtering_list = state["filtering_list"]
    caption_list = state["caption_list"]

    # Calculate statistics
    avg_quality = sum(q["quality_score"] for q in quality_list) / len(quality_list) if quality_list else 0
    avg_aesthetic = sum(a["overall_aesthetic"] for a in aesthetic_list) / len(aesthetic_list) if aesthetic_list else 0
    num_selected = sum(1 for f in filtering_list if f["passes_filter"])
    num_flagged = sum(1 for f in filtering_list if f["flagged"])

    # Category distribution
    categories = {}
    for f in filtering_list:
        cat = f["category"]
        categories[cat] = categories.get(cat, 0) + 1

    final_report = {
        "workflow": "LangGraph Multi-Agent System",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "num_images_processed": len(metadata_list),
        "average_technical_score": round(avg_quality, 2),
        "average_aesthetic_score": round(avg_aesthetic, 2),
        "num_images_selected": num_selected,
        "num_images_flagged": num_flagged,
        "category_distribution": categories,
        "errors": state["errors"],
        "stages_completed": [
            "metadata_extraction",
            "quality_assessment",
            "aesthetic_assessment",
            "filtering_categorization",
            "caption_generation"
        ]
    }

    print(f"\n[LangGraph] Final Report:")
    print(f"  - Images Processed: {final_report['num_images_processed']}")
    print(f"  - Avg Quality: {final_report['average_technical_score']}/5")
    print(f"  - Avg Aesthetic: {final_report['average_aesthetic_score']}/5")
    print(f"  - Selected: {final_report['num_images_selected']}")
    print(f"  - Flagged: {final_report['num_images_flagged']}")

    return {
        **state,
        "final_report": final_report,
        "current_stage": "complete"
    }


# ============================================================================
# Conditional Routing Logic
# ============================================================================

def should_continue_to_filtering(state: WorkflowState) -> str:
    """
    Conditional edge function: Check if both quality and aesthetic are complete.

    This demonstrates LangGraph's conditional routing capabilities.
    """
    current_stage = state.get("current_stage", "")

    # Check if both parallel stages are complete
    has_quality = len(state.get("quality_list", [])) > 0
    has_aesthetic = len(state.get("aesthetic_list", [])) > 0

    if has_quality and has_aesthetic:
        print("[LangGraph] Both quality and aesthetic complete, proceeding to filtering")
        return "proceed"
    else:
        print("[LangGraph] Waiting for parallel stages to complete...")
        return "wait"


# ============================================================================
# LangGraph Construction
# ============================================================================

def create_workflow_graph() -> StateGraph:
    """
    Create the LangGraph StateGraph for the travel photo workflow.

    Graph structure:
                    START
                      ↓
              metadata_extraction
                      ↓
            ┌─────────┴─────────┐
            ↓                   ↓
      quality_assessment  aesthetic_assessment
            └─────────┬─────────┘
                      ↓
        filtering_categorization
                      ↓
          caption_generation
                      ↓
            final_report
                      ↓
                     END
    """

    # Create workflow graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("metadata_extraction", metadata_extraction_node)
    workflow.add_node("quality_assessment", quality_assessment_node)
    workflow.add_node("aesthetic_assessment", aesthetic_assessment_node)
    workflow.add_node("filtering_categorization", filtering_categorization_node)
    workflow.add_node("caption_generation", caption_generation_node)
    workflow.add_node("final_report", final_report_node)

    # Set entry point
    workflow.set_entry_point("metadata_extraction")

    # Add edges (workflow transitions)
    # Stage 1 -> Stage 2 (parallel branches)
    workflow.add_edge("metadata_extraction", "quality_assessment")
    workflow.add_edge("metadata_extraction", "aesthetic_assessment")

    # Stage 2 (both branches) -> Stage 3
    workflow.add_edge("quality_assessment", "filtering_categorization")
    workflow.add_edge("aesthetic_assessment", "filtering_categorization")

    # Stage 3 -> Stage 4
    workflow.add_edge("filtering_categorization", "caption_generation")

    # Stage 4 -> Final Report
    workflow.add_edge("caption_generation", "final_report")

    # Final Report -> END
    workflow.add_edge("final_report", END)

    return workflow


# ============================================================================
# LangGraph Orchestrator
# ============================================================================

class LangGraphOrchestrator:
    """
    Main orchestrator using LangGraph for workflow management.

    Demonstrates stateful multi-agent orchestration with:
    - StateGraph for workflow definition
    - Parallel execution of quality and aesthetic agents
    - Conditional routing based on state
    - Checkpointing for workflow persistence
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)

        # Setup logging
        self.timestamped_output = Path(self.config['paths']['output_dir'])
        self.logger = setup_logger(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.timestamped_output / 'logs' / 'langgraph_workflow.log',
            json_format=True
        )

        ensure_directories(self.config)

        # Create LangGraph workflow
        self.workflow_graph = create_workflow_graph()

        # Add memory checkpointer for persistence
        self.memory = MemorySaver()

        # Compile the graph
        self.app = self.workflow_graph.compile(checkpointer=self.memory)

        log_info(self.logger, "LangGraph orchestrator initialized", "Orchestrator")

        print("\n[LangGraph] Workflow graph created with nodes:")
        print("  1. metadata_extraction")
        print("  2. quality_assessment (parallel)")
        print("  3. aesthetic_assessment (parallel)")
        print("  4. filtering_categorization")
        print("  5. caption_generation")
        print("  6. final_report")

    def run_workflow(self) -> Dict[str, Any]:
        """
        Execute the LangGraph workflow.

        Returns:
            Final workflow report
        """
        log_info(self.logger, "Starting LangGraph workflow", "Orchestrator")

        # Get input images
        input_dir = Path(self.config['paths']['input_images'])
        image_paths = get_image_files(input_dir)

        if not image_paths:
            log_error(self.logger, "Orchestrator", "NoImages", f"No images in {input_dir}", "error")
            return {}

        log_info(self.logger, f"Processing {len(image_paths)} images", "Orchestrator")

        # Initialize state
        initial_state: WorkflowState = {
            "image_paths": image_paths,
            "config": self.config,
            "metadata_list": [],
            "quality_list": [],
            "aesthetic_list": [],
            "filtering_list": [],
            "caption_list": [],
            "current_stage": "initialized",
            "errors": [],
            "processed_count": 0,
            "final_report": None
        }

        # Execute workflow with checkpointing
        config = {"configurable": {"thread_id": "travel-photo-workflow-1"}}

        print("\n" + "=" * 80)
        print("[LangGraph] Executing workflow...")
        print("=" * 80)

        # Run the graph
        final_state = self.app.invoke(initial_state, config=config)

        # Save outputs
        output_dir = Path(self.config['paths']['reports_output'])
        save_json(final_state["metadata_list"], output_dir / "langgraph_metadata.json")
        save_json(final_state["quality_list"], output_dir / "langgraph_quality.json")
        save_json(final_state["aesthetic_list"], output_dir / "langgraph_aesthetic.json")
        save_json(final_state["filtering_list"], output_dir / "langgraph_filtering.json")
        save_json(final_state["caption_list"], output_dir / "langgraph_captions.json")
        save_json(final_state["final_report"], output_dir / "langgraph_final_report.json")

        log_info(self.logger, "LangGraph workflow completed", "Orchestrator")

        return final_state["final_report"]


def main():
    """Main entry point for LangGraph implementation."""
    print("\n" + "=" * 80)
    print("LANGGRAPH IMPLEMENTATION - Travel Photo Organization")
    print("Stateful Multi-Agent Workflow Orchestration")
    print("=" * 80 + "\n")

    try:
        orchestrator = LangGraphOrchestrator()
        final_report = orchestrator.run_workflow()

        print("\n" + "=" * 80)
        print("[LangGraph] WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"Images Processed: {final_report['num_images_processed']}")
        print(f"Average Quality: {final_report['average_technical_score']}/5")
        print(f"Average Aesthetic: {final_report['average_aesthetic_score']}/5")
        print(f"Selected: {final_report['num_images_selected']}")
        print(f"Flagged: {final_report['num_images_flagged']}")
        print(f"Categories: {final_report['category_distribution']}")
        print("=" * 80 + "\n")

        print("✓ LangGraph workflow completed successfully!")

    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
