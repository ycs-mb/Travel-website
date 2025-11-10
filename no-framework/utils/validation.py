"""Validation utilities for agent outputs and final reports."""

import json
from typing import Any, Dict, List, Optional, Tuple
from jsonschema import validate, ValidationError


# Agent output schemas
AGENT_SCHEMAS = {
    "metadata_extraction": {
        "type": "object",
        "required": ["image_id", "filename", "file_size_bytes", "format"],
        "properties": {
            "image_id": {"type": "string"},
            "filename": {"type": "string"},
            "file_size_bytes": {"type": "integer"},
            "format": {"type": "string"},
            "dimensions": {
                "type": "object",
                "properties": {
                    "width": {"type": "integer"},
                    "height": {"type": "integer"}
                }
            },
            "capture_datetime": {"type": ["string", "null"]},
            "gps": {
                "type": "object",
                "properties": {
                    "latitude": {"type": ["number", "null"]},
                    "longitude": {"type": ["number", "null"]},
                    "altitude": {"type": ["number", "null"]}
                }
            },
            "flags": {"type": "array", "items": {"type": "string"}}
        }
    },
    "quality_assessment": {
        "type": "object",
        "required": ["image_id", "quality_score"],
        "properties": {
            "image_id": {"type": "string"},
            "quality_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "sharpness": {"type": "integer", "minimum": 1, "maximum": 5},
            "exposure": {"type": "integer", "minimum": 1, "maximum": 5},
            "noise": {"type": "integer", "minimum": 1, "maximum": 5},
            "resolution": {"type": "integer", "minimum": 1, "maximum": 5},
            "issues": {"type": "array", "items": {"type": "string"}}
        }
    },
    "aesthetic_assessment": {
        "type": "object",
        "required": ["image_id", "overall_aesthetic"],
        "properties": {
            "image_id": {"type": "string"},
            "composition": {"type": "integer", "minimum": 1, "maximum": 5},
            "framing": {"type": "integer", "minimum": 1, "maximum": 5},
            "lighting": {"type": "integer", "minimum": 1, "maximum": 5},
            "subject_interest": {"type": "integer", "minimum": 1, "maximum": 5},
            "overall_aesthetic": {"type": "integer", "minimum": 1, "maximum": 5},
            "notes": {"type": "string"}
        }
    },
    "duplicate_detection": {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["group_id", "image_ids", "selected_best"],
            "properties": {
                "group_id": {"type": "string"},
                "image_ids": {"type": "array", "items": {"type": "string"}},
                "selected_best": {"type": "string"},
                "similarity_metric": {"type": "number"},
                "similarity_type": {"type": "string"}
            }
        }
    },
    "filtering_categorization": {
        "type": "object",
        "required": ["image_id", "category", "passes_filter", "flagged"],
        "properties": {
            "image_id": {"type": "string"},
            "category": {"type": "string"},
            "subcategories": {"type": "array", "items": {"type": "string"}},
            "time_category": {"type": "string"},
            "location": {"type": ["string", "null"]},
            "passes_filter": {"type": "boolean"},
            "flagged": {"type": "boolean"},
            "flags": {"type": "array", "items": {"type": "string"}}
        }
    },
    "caption_generation": {
        "type": "object",
        "required": ["image_id", "captions"],
        "properties": {
            "image_id": {"type": "string"},
            "captions": {
                "type": "object",
                "required": ["concise", "standard", "detailed"],
                "properties": {
                    "concise": {"type": "string", "maxLength": 100},
                    "standard": {"type": "string", "minLength": 150, "maxLength": 250},
                    "detailed": {"type": "string", "minLength": 300, "maxLength": 500}
                }
            },
            "keywords": {"type": "array", "items": {"type": "string"}}
        }
    }
}

# Validation format schema
VALIDATION_SCHEMA = {
    "type": "object",
    "required": ["agent", "stage", "status", "summary"],
    "properties": {
        "agent": {"type": "string"},
        "stage": {"type": "string"},
        "status": {"type": "string", "enum": ["success", "warning", "error"]},
        "summary": {"type": "string"},
        "issues": {"type": "array", "items": {"type": "string"}}
    }
}

# Final report schema
FINAL_REPORT_SCHEMA = {
    "type": "object",
    "required": [
        "num_images_ingested",
        "num_images_flagged_metadata",
        "average_technical_score",
        "average_aesthetic_score",
        "num_duplicates_found",
        "num_images_final_selected",
        "num_images_flagged_for_manual_review",
        "agent_errors",
        "timestamp"
    ],
    "properties": {
        "num_images_ingested": {"type": "integer", "minimum": 0},
        "num_images_flagged_metadata": {"type": "integer", "minimum": 0},
        "average_technical_score": {"type": "number", "minimum": 0, "maximum": 5},
        "average_aesthetic_score": {"type": "number", "minimum": 0, "maximum": 5},
        "num_duplicates_found": {"type": "integer", "minimum": 0},
        "num_images_final_selected": {"type": "integer", "minimum": 0},
        "num_images_flagged_for_manual_review": {"type": "integer", "minimum": 0},
        "processing_time_seconds": {"type": "number", "minimum": 0},
        "timestamp": {"type": "string"}
    }
}


def validate_agent_output(
    agent_name: str,
    output: Any,
    schema_key: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate agent output against schema.

    Args:
        agent_name: Name of the agent
        output: Output data to validate
        schema_key: Schema key (defaults to agent_name)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if schema_key is None:
        schema_key = agent_name

    if schema_key not in AGENT_SCHEMAS:
        return False, f"No schema found for {schema_key}"

    try:
        validate(instance=output, schema=AGENT_SCHEMAS[schema_key])
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message}"


def validate_validation_format(validation_output: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the validation format itself.

    Args:
        validation_output: Validation output to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate(instance=validation_output, schema=VALIDATION_SCHEMA)
        return True, None
    except ValidationError as e:
        return False, f"Validation format error: {e.message}"


def validate_final_report(report: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate final statistics report.

    Args:
        report: Final report to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate(instance=report, schema=FINAL_REPORT_SCHEMA)
        return True, None
    except ValidationError as e:
        return False, f"Final report validation error: {e.message}"


def create_validation_summary(
    agent: str,
    stage: str,
    status: str,
    summary: str,
    issues: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized validation summary.

    Args:
        agent: Agent name
        stage: Processing stage
        status: Status (success, warning, error)
        summary: Summary message
        issues: List of issues (optional)

    Returns:
        Validation summary dictionary
    """
    validation = {
        "agent": agent,
        "stage": stage,
        "status": status,
        "summary": summary
    }

    if issues:
        validation["issues"] = issues

    return validation
