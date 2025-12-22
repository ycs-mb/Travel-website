#!/usr/bin/env python3
"""Quick test of the FastAPI server"""

import requests
from pathlib import Path
import json

API_URL = "http://localhost:8000"
API_KEY = "c3c1059abb9100b9a91eab76b91002fcf61f3fae7e90dfe86954ccf446621c8b"

# Test 1: Health check
print("=" * 60)
print("Test 1: Health Check")
print("=" * 60)
response = requests.get(f"{API_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 2: Analyze image (aesthetic only for speed)
print("\n" + "=" * 60)
print("Test 2: Aesthetic Assessment")
print("=" * 60)

image_path = Path("sample_images/IMG_3339.HEIC")
if not image_path.exists():
    print(f"❌ Image not found: {image_path}")
    exit(1)

headers = {"X-API-Key": API_KEY}

print(f"Analyzing: {image_path.name}")
print("Running aesthetic assessment agent only...")

with open(image_path, "rb") as f:
    files = {"file": f}
    data = {"agents": json.dumps(["aesthetic"])}

    response = requests.post(
        f"{API_URL}/api/v1/analyze/image",
        headers=headers,
        files=files,
        data=data
    )

print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    result = response.json()

    print("\n✅ Analysis Complete!")
    print("\nJob ID:", result['job_id'])
    print("Image:", result['image_id'])

    if 'aesthetic' in result:
        aesthetic = result['aesthetic']
        print("\n📊 Aesthetic Scores:")
        print(f"  Overall: {aesthetic['overall_aesthetic']}/5")
        print(f"  Composition: {aesthetic['composition']}/5")
        print(f"  Framing: {aesthetic['framing']}/5")
        print(f"  Lighting: {aesthetic['lighting']}/5")
        print(f"  Subject Interest: {aesthetic['subject_interest']}/5")
        print(f"\n  Notes: {aesthetic['notes']}")

    if 'token_usage' in result:
        usage = result['token_usage']
        print("\n💰 Token Usage:")
        print(f"  Total Tokens: {usage['total_token_count']}")
        print(f"  Estimated Cost: ${usage['estimated_cost_usd']:.4f}")

    print(f"\n⏱️  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")

else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
