"""
Test script for FastAPI server

Run with: python tests/test_api.py (from project root)
Or: cd tests && python test_api.py
"""

import requests
import json
from pathlib import Path
import time

# Get project directory
PROJECT_DIR = Path(__file__).parent.parent
SAMPLE_IMAGES_DIR = PROJECT_DIR / "sample_images"

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"  # Update with your actual API key

# Test image path (update with an actual image)
TEST_IMAGE = None
if SAMPLE_IMAGES_DIR.exists():
    jpg_files = list(SAMPLE_IMAGES_DIR.glob("*.jpg"))
    if jpg_files:
        TEST_IMAGE = jpg_files[0]


def test_health_check():
    """Test health check endpoint"""
    print("🧪 Testing health check...")

    response = requests.get(f"{API_URL}/health")

    assert response.status_code == 200, f"Health check failed: {response.status_code}"

    data = response.json()
    print(f"✅ Health check passed: {data['status']}")
    return True


def test_root_endpoint():
    """Test root endpoint"""
    print("\n🧪 Testing root endpoint...")

    response = requests.get(f"{API_URL}/")

    assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"

    data = response.json()
    print(f"✅ Root endpoint passed: {data['name']}")
    return True


def test_analyze_image_no_auth():
    """Test that API requires authentication"""
    print("\n🧪 Testing authentication requirement...")

    if TEST_IMAGE is None:
        print("⚠️  Skipping: No test image found")
        return True

    with open(TEST_IMAGE, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/api/v1/analyze/image", files=files)

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    print("✅ Authentication requirement works")
    return True


def test_analyze_image_aesthetic():
    """Test aesthetic assessment only"""
    print("\n🧪 Testing aesthetic assessment...")

    if TEST_IMAGE is None:
        print("⚠️  Skipping: No test image found")
        return True

    headers = {"X-API-Key": API_KEY}

    with open(TEST_IMAGE, "rb") as f:
        files = {"file": f}
        data = {
            "agents": json.dumps(["aesthetic"]),
            "include_token_usage": "true"
        }

        start_time = time.time()
        response = requests.post(
            f"{API_URL}/api/v1/analyze/image",
            headers=headers,
            files=files,
            data=data
        )
        elapsed = time.time() - start_time

    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()

    # Verify structure
    assert "aesthetic" in result, "Missing aesthetic scores"
    assert "job_id" in result, "Missing job_id"
    assert "total_cost_usd" in result, "Missing cost information"

    aesthetic = result["aesthetic"]
    print(f"✅ Aesthetic assessment completed in {elapsed:.2f}s")
    print(f"   Overall Score: {aesthetic['overall_aesthetic']}/5")
    print(f"   - Composition: {aesthetic['composition']}/5")
    print(f"   - Framing: {aesthetic['framing']}/5")
    print(f"   - Lighting: {aesthetic['lighting']}/5")
    print(f"   - Subject Interest: {aesthetic['subject_interest']}/5")

    if "token_usage" in result:
        print(f"   Token Cost: ${result['total_cost_usd']:.4f}")

    return True


def test_analyze_image_full():
    """Test full analysis pipeline"""
    print("\n🧪 Testing full analysis pipeline...")

    if TEST_IMAGE is None:
        print("⚠️  Skipping: No test image found")
        return True

    headers = {"X-API-Key": API_KEY}

    with open(TEST_IMAGE, "rb") as f:
        files = {"file": f}
        data = {
            "agents": json.dumps(["aesthetic", "filtering", "caption"]),
            "include_token_usage": "true"
        }

        start_time = time.time()
        response = requests.post(
            f"{API_URL}/api/v1/analyze/image",
            headers=headers,
            files=files,
            data=data
        )
        elapsed = time.time() - start_time

    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()

    # Verify all components
    assert "aesthetic" in result, "Missing aesthetic"
    assert "filtering" in result, "Missing filtering"
    assert "caption" in result, "Missing caption"

    print(f"✅ Full analysis completed in {elapsed:.2f}s")

    # Print results
    aesthetic = result["aesthetic"]
    print(f"\n📊 Aesthetic: {aesthetic['overall_aesthetic']}/5")

    filtering = result["filtering"]
    status = "✅ PASSED" if filtering['passes_filter'] else "❌ REJECTED"
    print(f"📁 Category: {filtering['category']} {status}")

    caption = result["caption"]
    print(f"📝 Caption (concise): {caption['concise']}")

    if "total_cost_usd" in result:
        print(f"💰 Total Cost: ${result['total_cost_usd']:.4f}")

    print(f"⏱️  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")

    return True


def test_individual_agents():
    """Test individual agent endpoints"""
    print("\n🧪 Testing individual agent endpoints...")

    if TEST_IMAGE is None:
        print("⚠️  Skipping: No test image found")
        return True

    headers = {"X-API-Key": API_KEY}

    endpoints = [
        "/api/v1/agents/aesthetic",
        "/api/v1/agents/filtering",
        "/api/v1/agents/caption"
    ]

    for endpoint in endpoints:
        with open(TEST_IMAGE, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{API_URL}{endpoint}",
                headers=headers,
                files=files
            )

        if response.status_code == 200:
            print(f"   ✅ {endpoint.split('/')[-1]}")
        else:
            print(f"   ❌ {endpoint.split('/')[-1]} - {response.status_code}")
            return False

    return True


def test_token_usage_endpoint():
    """Test token usage statistics endpoint"""
    print("\n🧪 Testing token usage endpoint...")

    headers = {"X-API-Key": API_KEY}

    response = requests.get(
        f"{API_URL}/api/v1/usage/tokens",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Token usage endpoint works")
        print(f"   Total requests: {data['total_requests']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 FastAPI Server Test Suite")
    print("=" * 60)

    # Check if server is running
    try:
        requests.get(f"{API_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ Server is not running!")
        print("   Start it with: ./scripts/start_api.sh")
        print("   Or: uvicorn api.fastapi_server:app --port 8000 --reload")
        return

    if TEST_IMAGE is None:
        print("\n⚠️  Warning: No test images found in sample_images/")
        print("   Some tests will be skipped")
    else:
        print(f"\n📁 Using test image: {TEST_IMAGE}")

    tests = [
        test_health_check,
        test_root_endpoint,
        test_analyze_image_no_auth,
        test_analyze_image_aesthetic,
        test_individual_agents,
        test_token_usage_endpoint,
        test_analyze_image_full,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ {test.__name__} failed with exception:")
            print(f"   {e}")
            results.append((test.__name__, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    # Update API_KEY from environment or .env file
    import os
    from dotenv import load_dotenv

    # Load .env from project root
    load_dotenv(PROJECT_DIR / ".env")
    API_KEY = os.getenv("API_KEY", API_KEY)

    run_all_tests()
