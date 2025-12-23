#!/usr/bin/env python3
"""Direct test of aesthetic agent

Run with: python tests/test_aesthetic_direct.py (from project root)
Or: cd tests && python test_aesthetic_direct.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import yaml
from agents.aesthetic_assessment import AestheticAssessmentAgent
from utils.logger import setup_logger

# Load config
with open(PROJECT_DIR / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Setup logger
logger = setup_logger("Test", "INFO")

# Initialize agent
print("Initializing aesthetic assessment agent...")
agent = AestheticAssessmentAgent(config, logger)

# Test image
image_path = PROJECT_DIR / "sample_images/IMG_3339.HEIC"
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
