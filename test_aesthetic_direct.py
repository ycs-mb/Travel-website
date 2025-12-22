#!/usr/bin/env python3
"""Direct test of aesthetic agent"""

from pathlib import Path
import yaml
from agents.aesthetic_assessment import AestheticAssessmentAgent
from utils.logger import setup_logger

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Setup logger
logger = setup_logger("Test", "INFO")

# Initialize agent
print("Initializing aesthetic assessment agent...")
agent = AestheticAssessmentAgent(config, logger)

# Test image
image_path = Path("sample_images/IMG_3339.HEIC")
print(f"\nProcessing: {image_path}")

# Run agent
print("Running aesthetic assessment...")
results, validation = agent.run([image_path], [{}])

print(f"\nResults: {len(results)} images processed")
if results:
    result = results[0]
    print(f"\nResult keys: {result.keys()}")
    print(f"\nFull result:")
    import json
    print(json.dumps(result, indent=2))
else:
    print("No results returned")
