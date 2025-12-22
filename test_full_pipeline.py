#!/usr/bin/env python3
"""Test full pipeline directly"""

from pathlib import Path
import yaml
from agents.metadata_extraction import MetadataExtractionAgent
from agents.aesthetic_assessment import AestheticAssessmentAgent
from utils.logger import setup_logger

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Setup logger
logger = setup_logger("Test", "INFO")

# Test image
image_path = Path("sample_images/IMG_3339.HEIC")
print(f"Processing: {image_path}\n")

# Step 1: Extract metadata
print("1. Extracting metadata...")
metadata_agent = MetadataExtractionAgent(config, logger)
metadata_list, _ = metadata_agent.run([image_path])
print(f"   Metadata extracted: {len(metadata_list)} images")

if metadata_list:
    metadata = metadata_list[0]
    print(f"   Image ID: {metadata.get('image_id')}")
    print(f"   Filename: {metadata.get('filename')}\n")
else:
    print("   ERROR: No metadata returned\n")
    exit(1)

# Step 2: Aesthetic assessment
print("2. Running aesthetic assessment...")
aesthetic_agent = AestheticAssessmentAgent(config, logger)
aesthetic_list, _ = aesthetic_agent.run([image_path], metadata_list)
print(f"   Aesthetic results: {len(aesthetic_list)} images")

if aesthetic_list:
    aesthetic = aesthetic_list[0]
    print(f"\n📊 Aesthetic Scores:")
    print(f"   Overall: {aesthetic.get('overall_aesthetic')}/5")
    print(f"   Composition: {aesthetic.get('composition')}/5")
    print(f"   Framing: {aesthetic.get('framing')}/5")
    print(f"   Lighting: {aesthetic.get('lighting')}/5")
    print(f"   Subject Interest: {aesthetic.get('subject_interest')}/5")
    print(f"   Notes: {aesthetic.get('notes')}")

    if 'token_usage' in aesthetic:
        usage = aesthetic['token_usage']
        print(f"\n💰 Token Usage:")
        print(f"   Total Tokens: {usage.get('total_token_count')}")
        print(f"   Input Tokens: {usage.get('prompt_token_count')}")
        print(f"   Output Tokens: {usage.get('candidates_token_count')}")
        print(f"   Estimated Cost: ${usage.get('estimated_cost_usd', 0):.4f}")
else:
    print("   ERROR: No aesthetic results returned")
