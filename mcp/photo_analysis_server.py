"""
MCP (Model Context Protocol) Server for Photo Analysis Agents

Exposes photo analysis capabilities as MCP tools for use with Claude Desktop
and other MCP-compatible applications.

Installation:
    1. Add to Claude Desktop config (~/.config/claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "photo-analysis": {
          "command": "uv",
          "args": ["run", "python", "/path/to/mcp/photo_analysis_server.py"]
        }
      }
    }

    2. Restart Claude Desktop

Usage in Claude:
    "Analyze this photo at /path/to/image.jpg and give me an aesthetic score"
    "Generate a caption for /path/to/vacation.jpg"
    "What's my token usage for today?"
"""

import asyncio
import json
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Import agents
from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.filtering_categorization import FilteringCategorizationAgent
from agents.caption_generation import CaptionGenerationAgent
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from utils.logger import setup_logger

# Initialize MCP server
server = Server("photo-analysis")

# Load configuration
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Setup logger - CRITICAL: Disable console output for MCP server
# MCP protocol uses stdout for communication, so we can only log to file
log_level = config.get('logging', {}).get('level', 'INFO')
log_dir = Path(__file__).parent.parent / 'output' / 'logs'
log_file = log_dir / 'mcp_server.log'

# Use robust setup_logger with mcp_mode=True to ensure NO stdout logging
logger = setup_logger(
    name="MCP",
    log_level=log_level,
    log_file=log_file,
    json_format=config.get('logging', {}).get('format', 'json') == 'json',
    mcp_mode=True
)

# Initialize agents
agents = {
    'metadata': MetadataExtractionAgent(config, logger),
    'quality': QualityAssessmentAgent(config, logger),
    'aesthetic': AestheticAssessmentAgent(config, logger),
    'filtering': FilteringCategorizationAgent(config, logger),
    'caption': CaptionGenerationAgent(config, logger)
}

# Global state for tracking
token_usage_history = []


# Tool Definitions

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="analyze_photo",
            description="Analyze a travel photo with full pipeline (aesthetic, filtering, caption generation). Returns comprehensive analysis including scores, categories, and captions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to the image file"
                    },
                    "include_aesthetic": {
                        "type": "boolean",
                        "description": "Include aesthetic quality assessment",
                        "default": True
                    },
                    "include_filtering": {
                        "type": "boolean",
                        "description": "Include filtering and categorization",
                        "default": True
                    },
                    "include_caption": {
                        "type": "boolean",
                        "description": "Include caption generation",
                        "default": True
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="assess_aesthetic_quality",
            description="Evaluate aesthetic quality of a photo. Returns scores for composition, framing, lighting, and subject interest (1-5 scale).",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to the image file"
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="extract_metadata",
            description="Extract EXIF, GPS, and technical metadata from a photo. Returns raw metadata fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to the image file"
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="categorize_photo",
            description="Categorize a travel photo by subject, time of day, and location. Determines if photo passes quality filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to the image file"
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="generate_caption",
            description="Generate three levels of captions for a travel photo: concise (<100 chars), standard (150-250 chars), and detailed (300-500 chars). Includes keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to the image file"
                    },
                    "caption_level": {
                        "type": "string",
                        "enum": ["concise", "standard", "detailed", "all"],
                        "description": "Which caption level to return",
                        "default": "all"
                    }
                },
                "required": ["image_path"]
            }
        ),
        Tool(
            name="get_token_usage",
            description="Get token usage statistics and cost estimates for recent photo analyses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent entries to include",
                        "default": 10
                    }
                }
            }
        )
    ]


# Tool Handlers

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from MCP clients"""

    try:
        if name == "analyze_photo":
            return await handle_analyze_photo(arguments)

        elif name == "assess_aesthetic_quality":
            return await handle_aesthetic_assessment(arguments)

        elif name == "categorize_photo":
            return await handle_categorization(arguments)

        elif name == "generate_caption":
            return await handle_caption_generation(arguments)

        elif name == "extract_metadata":
            return await handle_extract_metadata(arguments)

        elif name == "get_token_usage":
            return await handle_token_usage(arguments)

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool call failed: {name} - {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


def normalize_path(path_str: str) -> Path:
    """
    Normalize a path string from various formats (URI, relative, etc.)
    
    Args:
        path_str: String representation of the path
        
    Returns:
        pathlib.Path: Normalized absolute path
    """
    if not path_str:
        return Path(".")
        
    # Handle URI format (file://...)
    if path_str.startswith("file://"):
        path_str = path_str[7:]
        # On windows, file:///C:/path becomes /C:/path, so we strip leading slash if needed
        if os.name == 'nt' and path_str.startswith("/"):
            path_str = path_str[1:]
            
    # Unquote URL-encoded characters (e.g., %20 -> space)
    path_str = urllib.parse.unquote(path_str)
    
    # Expand user directory (~)
    path_str = os.path.expanduser(path_str)
    
    # Resolve to absolute path
    path = Path(path_str).resolve()
    
    return path


async def handle_analyze_photo(args: Dict[str, Any]) -> List[TextContent]:
    """Run full photo analysis pipeline"""
    image_path = normalize_path(args["image_path"])

    if not image_path.exists():
        return [TextContent(type="text", text=f"Error: Image not found at {image_path}")]

    logger.info(f"Analyzing photo: {image_path}")

    result = {}
    total_cost = 0.0

    # Run metadata extraction
    metadata_list, _ = agents['metadata'].run([image_path])
    metadata = metadata_list[0] if metadata_list else {}
    result['metadata'] = metadata

    # Run quality assessment
    quality_list, _ = agents['quality'].run([image_path], [metadata])
    quality = quality_list[0] if quality_list else {}
    result['quality'] = quality

    # Run aesthetic assessment
    if args.get("include_aesthetic", True):
        aesthetic_list, validation = agents['aesthetic'].run([image_path], [metadata])
        aesthetic = aesthetic_list[0] if aesthetic_list else {}
        result['aesthetic'] = aesthetic

        if 'token_usage' in aesthetic:
            total_cost += aesthetic['token_usage'].get('estimated_cost_usd', 0)
    else:
        aesthetic = {}

    # Run filtering & categorization
    if args.get("include_filtering", True):
        filtering_list, validation = agents['filtering'].run(
            [image_path], [metadata], [quality], [aesthetic] if aesthetic else [{}]
        )
        filtering = filtering_list[0] if filtering_list else {}
        result['filtering'] = filtering

        if 'token_usage' in filtering:
            total_cost += filtering['token_usage'].get('estimated_cost_usd', 0)
    else:
        filtering = {}

    # Run caption generation
    if args.get("include_caption", True):
        caption_list, validation = agents['caption'].run(
            [image_path], [metadata], [quality], [aesthetic] if aesthetic else [{}], [filtering] if filtering else [{}]
        )
        caption = caption_list[0] if caption_list else {}
        result['caption'] = caption

        if 'token_usage' in caption:
            total_cost += caption['token_usage'].get('estimated_cost_usd', 0)

    result['total_cost_usd'] = total_cost

    # Track usage
    token_usage_history.append({
        'image': str(image_path),
        'cost': total_cost,
        'timestamp': Path(image_path).stat().st_mtime
    })

    # Format response
    response = format_analysis_result(result)

    return [TextContent(type="text", text=response)]


async def handle_aesthetic_assessment(args: Dict[str, Any]) -> List[TextContent]:
    """Run aesthetic assessment only"""
    image_path = normalize_path(args["image_path"])

    if not image_path.exists():
        return [TextContent(type="text", text=f"Error: Image not found at {image_path}")]

    # Run metadata first
    metadata_list, _ = agents['metadata'].run([image_path])
    metadata = metadata_list[0] if metadata_list else {}

    # Run aesthetic assessment
    aesthetic_list, validation = agents['aesthetic'].run([image_path], [metadata])
    aesthetic = aesthetic_list[0] if aesthetic_list else {}

    # Format response
    response = f"""**Aesthetic Quality Assessment**

**Overall Score**: {aesthetic.get('overall_aesthetic', 'N/A')}/5

**Detailed Scores**:
- Composition: {aesthetic.get('composition', 'N/A')}/5
- Framing: {aesthetic.get('framing', 'N/A')}/5
- Lighting: {aesthetic.get('lighting', 'N/A')}/5
- Subject Interest: {aesthetic.get('subject_interest', 'N/A')}/5

**Analysis**: {aesthetic.get('notes', 'No notes available')}
"""

    if 'token_usage' in aesthetic:
        usage = aesthetic['token_usage']
        response += f"\n**Cost**: ${usage.get('estimated_cost_usd', 0):.4f} ({usage.get('total_token_count', 0)} tokens)"

    return [TextContent(type="text", text=response)]


async def handle_extract_metadata(args: Dict[str, Any]) -> List[TextContent]:
    """Run metadata extraction only"""
    image_path = normalize_path(args["image_path"])

    if not image_path.exists():
        return [TextContent(type="text", text=f"Error: Image not found at {image_path}")]

    # Run metadata extraction
    metadata_list, _ = agents['metadata'].run([image_path])
    metadata = metadata_list[0] if metadata_list else {}

    # Format response
    response = "**Photo Metadata**\n\n"
    
    # Basic Info
    response += f"- **Filename**: {metadata.get('filename', 'Unknown')}\n"
    response += f"- **Format**: {metadata.get('format', 'Unknown')}\n"
    response += f"- **Size**: {metadata.get('file_size_mb', 0):.2f} MB\n"
    response += f"- **Dimensions**: {metadata.get('width', 0)} x {metadata.get('height', 0)}\n\n"
    
    # Capture Info
    response += f"**Capture Details**:\n"
    response += f"- **Date**: {metadata.get('capture_time', 'Unknown')}\n"
    response += f"- **Camera**: {metadata.get('camera_make', '')} {metadata.get('camera_model', 'Unknown')}\n"
    response += f"- **Lens**: {metadata.get('lens_model', 'Unknown')}\n\n"
    
    # Settings
    response += f"**Settings**:\n"
    response += f"- **ISO**: {metadata.get('iso', 'N/A')}\n"
    response += f"- **Aperture**: {metadata.get('aperture', 'N/A')}\n"
    response += f"- **Shutter**: {metadata.get('shutter_speed', 'N/A')}\n"
    response += f"- **Focal Length**: {metadata.get('focal_length', 'N/A')}\n\n"
    
    # Location
    response += f"**Location**:\n"
    if metadata.get('gps'):
        gps = metadata['gps']
        response += f"- **Coords**: {gps.get('latitude', 0):.4f}, {gps.get('longitude', 0):.4f}\n"
        if gps.get('altitude'):
            response += f"- **Altitude**: {gps.get('altitude', 0):.1f}m\n"
        
        # Add address if available (from reverse geocoding)
        if gps.get('latitude') and gps.get('longitude'):
             # We can manually trigger reverse geocoding if not already present, 
             # but the metadata agent should have handled it if configured.
             # Check if address is directly in metadata (it might be added by the agent in future)
             # For now just show coords
             pass
    else:
        response += "- No GPS data available\n"

    return [TextContent(type="text", text=response)]


async def handle_categorization(args: Dict[str, Any]) -> List[TextContent]:
    """Run filtering & categorization only"""
    image_path = normalize_path(args["image_path"])

    if not image_path.exists():
        return [TextContent(type="text", text=f"Error: Image not found at {image_path}")]

    # Run prerequisites
    metadata_list, _ = agents['metadata'].run([image_path])
    metadata = metadata_list[0] if metadata_list else {}

    quality_list, _ = agents['quality'].run([image_path], [metadata])
    quality = quality_list[0] if quality_list else {}

    aesthetic_list, _ = agents['aesthetic'].run([image_path], [metadata])
    aesthetic = aesthetic_list[0] if aesthetic_list else {}

    # Run filtering
    filtering_list, validation = agents['filtering'].run(
        [image_path], [metadata], [quality], [aesthetic]
    )
    filtering = filtering_list[0] if filtering_list else {}

    # Format response
    status = "✅ PASSED" if filtering.get('passes_filter') else "❌ REJECTED"

    response = f"""**Photo Categorization**

**Status**: {status}
**Category**: {filtering.get('category', 'Unknown')}
**Subcategories**: {', '.join(filtering.get('subcategories', []))}
**Time**: {filtering.get('time_category', 'Unknown')}
**Location**: {filtering.get('location', 'Not available')}

**Reasoning**: {filtering.get('reasoning', 'No reasoning provided')}
"""

    if filtering.get('flags'):
        response += f"\n**Flags**: {', '.join(filtering.get('flags', []))}"

    if 'token_usage' in filtering:
        usage = filtering['token_usage']
        response += f"\n**Cost**: ${usage.get('estimated_cost_usd', 0):.4f}"

    return [TextContent(type="text", text=response)]


async def handle_caption_generation(args: Dict[str, Any]) -> List[TextContent]:
    """Run caption generation only"""
    image_path = normalize_path(args["image_path"])
    caption_level = args.get("caption_level", "all")

    if not image_path.exists():
        return [TextContent(type="text", text=f"Error: Image not found at {image_path}")]

    # Run prerequisites
    metadata_list, _ = agents['metadata'].run([image_path])
    metadata = metadata_list[0] if metadata_list else {}

    quality_list, _ = agents['quality'].run([image_path], [metadata])
    quality = quality_list[0] if quality_list else {}

    aesthetic_list, _ = agents['aesthetic'].run([image_path], [metadata])
    aesthetic = aesthetic_list[0] if aesthetic_list else {}

    filtering_list, _ = agents['filtering'].run([image_path], [metadata], [quality], [aesthetic])
    filtering = filtering_list[0] if filtering_list else {}

    # Run caption generation
    caption_list, validation = agents['caption'].run(
        [image_path], [metadata], [quality], [aesthetic], [filtering]
    )
    caption = caption_list[0] if caption_list else {}

    captions = caption.get('captions', {})
    keywords = caption.get('keywords', [])

    # Format response based on level
    if caption_level == "all":
        response = f"""**Photo Captions**

**Concise** ({len(captions.get('concise', ''))} chars):
{captions.get('concise', 'N/A')}

**Standard** ({len(captions.get('standard', ''))} chars):
{captions.get('standard', 'N/A')}

**Detailed** ({len(captions.get('detailed', ''))} chars):
{captions.get('detailed', 'N/A')}

**Keywords**: {', '.join(keywords)}
"""
    else:
        response = captions.get(caption_level, f"Caption level '{caption_level}' not available")

    if 'token_usage' in caption:
        usage = caption['token_usage']
        response += f"\n**Cost**: ${usage.get('estimated_cost_usd', 0):.4f}"

    return [TextContent(type="text", text=response)]


async def handle_token_usage(args: Dict[str, Any]) -> List[TextContent]:
    """Get token usage statistics"""
    limit = args.get("limit", 10)

    if not token_usage_history:
        return [TextContent(type="text", text="No token usage data available yet.")]

    recent = token_usage_history[-limit:]

    total_cost = sum(entry['cost'] for entry in recent)
    avg_cost = total_cost / len(recent) if recent else 0

    response = f"""**Token Usage Statistics**

**Recent Analyses**: {len(recent)}
**Total Cost**: ${total_cost:.4f}
**Average Cost per Image**: ${avg_cost:.4f}

**Recent Entries**:
"""

    for i, entry in enumerate(reversed(recent), 1):
        response += f"\n{i}. {Path(entry['image']).name}: ${entry['cost']:.4f}"

    return [TextContent(type="text", text=response)]


# Helper Functions

def format_analysis_result(result: Dict[str, Any]) -> str:
    """Format full analysis result as markdown"""
    output = "# Photo Analysis Report\n\n"

    # Aesthetic scores
    if 'aesthetic' in result:
        aesthetic = result['aesthetic']
        output += f"""## Aesthetic Quality: {aesthetic.get('overall_aesthetic', 'N/A')}/5

- **Composition**: {aesthetic.get('composition', 'N/A')}/5
- **Framing**: {aesthetic.get('framing', 'N/A')}/5
- **Lighting**: {aesthetic.get('lighting', 'N/A')}/5
- **Subject Interest**: {aesthetic.get('subject_interest', 'N/A')}/5

*{aesthetic.get('notes', 'No notes')}*

"""

    # Categorization
    if 'filtering' in result:
        filtering = result['filtering']
        status = "✅ PASSED" if filtering.get('passes_filter') else "❌ REJECTED"
        output += f"""## Categorization: {status}

- **Category**: {filtering.get('category', 'Unknown')}
- **Subcategories**: {', '.join(filtering.get('subcategories', []))}
- **Time**: {filtering.get('time_category', 'Unknown')}
- **Location**: {filtering.get('location', 'N/A')}

*{filtering.get('reasoning', '')}*

"""

    # Captions
    if 'caption' in result:
        captions = result['caption'].get('captions', {})
        keywords = result['caption'].get('keywords', [])

        output += f"""## Captions

**Concise**: {captions.get('concise', 'N/A')}

**Standard**: {captions.get('standard', 'N/A')}

**Detailed**: {captions.get('detailed', 'N/A')}

**Keywords**: {', '.join(keywords)}

"""

    # Cost
    output += f"\n---\n**Total Cost**: ${result.get('total_cost_usd', 0):.4f}"

    return output


# Main entry point

async def main():
    """Run MCP server"""
    logger.info("Starting Photo Analysis MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
