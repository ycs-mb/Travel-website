#!/usr/bin/env python3
"""Correct API test with proper request format

Run with: python tests/test_api_correct.py (from project root)
Or: cd tests && python test_api_correct.py
"""

import requests
from pathlib import Path
import json

# Get project directory
PROJECT_DIR = Path(__file__).parent.parent

API_URL = "http://localhost:8000"
API_KEY = "c3c1059abb9100b9a91eab76b91002fcf61f3fae7e90dfe86954ccf446621c8b"

print("Testing FastAPI Server with Aesthetic Assessment")
print("=" * 60)

image_path = PROJECT_DIR / "sample_images/PXL_20241003_105856630.MP.jpg"
headers = {"X-API-Key": API_KEY}

# Method 1: Send agents as multipart form fields
print("\nSending request...")
with open(image_path, "rb") as f:
    files = {"file": (image_path.name, f, "image/heic")}
    # FastAPI Depends(AnalysisRequest) expects the data as Form fields
    # We need to send each agent as a separate field
    data = {
        "agents": "aesthetic",  # Send as a single string
        "include_token_usage": "true"
    }

    response = requests.post(
        f"{API_URL}/api/v1/analyze/image",
        headers=headers,
        files=files,
        data=data
    )

print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    result = response.json()

    print("✅ Analysis Complete!")
    print(f"\nJob ID: {result['job_id']}")
    print(f"Image: {result['image_id']}")

    if result.get('aesthetic'):
        aesthetic = result['aesthetic']
        print("\n📊 Aesthetic Scores:")
        print(f"  Overall: {aesthetic['overall_aesthetic']}/5")
        print(f"  Composition: {aesthetic['composition']}/5")
        print(f"  Framing: {aesthetic['framing']}/5")
        print(f"  Lighting: {aesthetic['lighting']}/5")
        print(f"  Subject Interest: {aesthetic['subject_interest']}/5")
        print(f"\n  Notes: {aesthetic['notes']}")
    else:
        print("\n❌ No aesthetic data in response")

    if result.get('token_usage'):
        print("\n💰 Token Usage:")
        if 'aesthetic' in result['token_usage']:
            usage = result['token_usage']['aesthetic']
            print(f"  Total Tokens: {usage['total_token_count']}")
            print(f"  Input: {usage['prompt_token_count']}, Output: {usage['candidates_token_count']}")
            print(f"  Estimated Cost: ${usage['estimated_cost_usd']:.4f}")

    print(f"\n⏱️  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
    print(f"💵 Total Cost: ${result.get('total_cost_usd', 0):.4f}")

else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

print("\n" + "=" * 60)
print("Full Response:")
print(json.dumps(response.json(), indent=2))
