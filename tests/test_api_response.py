#!/usr/bin/env python3
"""Check what API is actually returning

Run with: python tests/test_api_response.py (from project root)
Or: cd tests && python test_api_response.py
"""

import requests
from pathlib import Path
import json

# Get project directory
PROJECT_DIR = Path(__file__).parent.parent

API_URL = "http://localhost:8000"
API_KEY = "c3c1059abb9100b9a91eab76b91002fcf61f3fae7e90dfe86954ccf446621c8b"

image_path = PROJECT_DIR / "sample_images/IMG_3339.HEIC"
headers = {"X-API-Key": API_KEY}

with open(image_path, "rb") as f:
    files = {"file": f}
    data = {"agents": json.dumps(["aesthetic"])}

    response = requests.post(
        f"{API_URL}/api/v1/analyze/image",
        headers=headers,
        files=files,
        data=data
    )

print(f"Status: {response.status_code}")
print("\nFull response:")
print(json.dumps(response.json(), indent=2))
