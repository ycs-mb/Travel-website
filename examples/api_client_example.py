"""
Example client for FastAPI Photo Analysis API

This demonstrates how to use the API from a Python application.
"""

import requests
from pathlib import Path
from typing import List, Dict, Any
import json


class PhotoAnalysisClient:
    """
    Client for interacting with the Photo Analysis API

    Example:
        client = PhotoAnalysisClient(
            api_url="http://localhost:8000",
            api_key="your-api-key"
        )

        result = client.analyze_image("photo.jpg")
        print(f"Aesthetic Score: {result['aesthetic']['overall_aesthetic']}")
    """

    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize client

        Args:
            api_url: Base URL of the API server
            api_key: API key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def health_check(self) -> Dict[str, Any]:
        """Check if API server is healthy"""
        response = self.session.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()

    def analyze_image(
        self,
        image_path: str,
        agents: List[str] = None,
        include_token_usage: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a single image

        Args:
            image_path: Path to image file
            agents: List of agents to run (default: all)
            include_token_usage: Include token/cost information

        Returns:
            Analysis results dictionary
        """
        if agents is None:
            agents = ["aesthetic", "filtering", "caption"]

        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {
                "agents": json.dumps(agents),
                "include_token_usage": str(include_token_usage).lower()
            }

            response = self.session.post(
                f"{self.api_url}/api/v1/analyze/image",
                files=files,
                data=data
            )

        response.raise_for_status()
        return response.json()

    def assess_aesthetic(self, image_path: str) -> Dict[str, Any]:
        """Run aesthetic assessment only"""
        with open(image_path, "rb") as f:
            response = self.session.post(
                f"{self.api_url}/api/v1/agents/aesthetic",
                files={"file": f}
            )

        response.raise_for_status()
        return response.json()

    def categorize(self, image_path: str) -> Dict[str, Any]:
        """Run categorization only"""
        with open(image_path, "rb") as f:
            response = self.session.post(
                f"{self.api_url}/api/v1/agents/filtering",
                files={"file": f}
            )

        response.raise_for_status()
        return response.json()

    def generate_caption(self, image_path: str) -> Dict[str, Any]:
        """Run caption generation only"""
        with open(image_path, "rb") as f:
            response = self.session.post(
                f"{self.api_url}/api/v1/agents/caption",
                files={"file": f}
            )

        response.raise_for_status()
        return response.json()

    def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        response = self.session.get(f"{self.api_url}/api/v1/usage/tokens")
        response.raise_for_status()
        return response.json()


def example_1_basic_analysis():
    """Example 1: Basic image analysis"""
    print("=" * 60)
    print("Example 1: Basic Image Analysis")
    print("=" * 60)

    client = PhotoAnalysisClient(
        api_url="http://localhost:8000",
        api_key="your-api-key-here"  # Update with your API key
    )

    # Check health
    health = client.health_check()
    print(f"✅ API Status: {health['status']}")

    # Analyze image
    image_path = "sample_images/photo.jpg"  # Update with your image

    print(f"\n📸 Analyzing: {image_path}")

    result = client.analyze_image(image_path)

    # Print results
    print(f"\n📊 Results:")
    print(f"   Job ID: {result['job_id']}")

    if 'aesthetic' in result:
        aesthetic = result['aesthetic']
        print(f"   Aesthetic Score: {aesthetic['overall_aesthetic']}/5")
        print(f"   - Composition: {aesthetic['composition']}/5")
        print(f"   - Lighting: {aesthetic['lighting']}/5")

    if 'filtering' in result:
        filtering = result['filtering']
        status = "PASSED" if filtering['passes_filter'] else "REJECTED"
        print(f"   Category: {filtering['category']} ({status})")

    if 'caption' in result:
        caption = result['caption']
        print(f"   Caption: {caption['concise']}")

    if 'total_cost_usd' in result:
        print(f"   Cost: ${result['total_cost_usd']:.4f}")

    print(f"   Processing Time: {result.get('processing_time_seconds', 0):.2f}s")


def example_2_batch_processing():
    """Example 2: Process multiple images"""
    print("\n" + "=" * 60)
    print("Example 2: Batch Processing")
    print("=" * 60)

    client = PhotoAnalysisClient(
        api_url="http://localhost:8000",
        api_key="your-api-key-here"
    )

    # Get all images from directory
    image_dir = Path("sample_images")
    images = list(image_dir.glob("*.jpg"))[:5]  # Process first 5

    print(f"\n📸 Processing {len(images)} images...")

    results = []
    total_cost = 0.0

    for i, image_path in enumerate(images, 1):
        print(f"\n{i}. {image_path.name}")

        try:
            result = client.analyze_image(str(image_path))
            results.append(result)

            # Extract key info
            aesthetic = result.get('aesthetic', {}).get('overall_aesthetic', 0)
            cost = result.get('total_cost_usd', 0)
            total_cost += cost

            print(f"   Score: {aesthetic}/5 | Cost: ${cost:.4f}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Summary
    print(f"\n📊 Batch Summary:")
    print(f"   Images processed: {len(results)}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Average cost: ${total_cost/len(results):.4f} per image")

    # Find best images
    sorted_results = sorted(
        results,
        key=lambda x: x.get('aesthetic', {}).get('overall_aesthetic', 0),
        reverse=True
    )

    print(f"\n🏆 Top 3 Images:")
    for i, result in enumerate(sorted_results[:3], 1):
        aesthetic = result['aesthetic']
        print(f"   {i}. Score {aesthetic['overall_aesthetic']}/5 - {result['image_id']}")


def example_3_aesthetic_only():
    """Example 3: Quick aesthetic check"""
    print("\n" + "=" * 60)
    print("Example 3: Quick Aesthetic Check")
    print("=" * 60)

    client = PhotoAnalysisClient(
        api_url="http://localhost:8000",
        api_key="your-api-key-here"
    )

    image_path = "sample_images/photo.jpg"

    print(f"\n📸 Checking aesthetic quality of: {image_path}")

    result = client.assess_aesthetic(image_path)

    aesthetic = result['aesthetic']

    print(f"\n📊 Aesthetic Analysis:")
    print(f"   Overall: {aesthetic['overall_aesthetic']}/5")
    print(f"   Composition: {aesthetic['composition']}/5")
    print(f"   Framing: {aesthetic['framing']}/5")
    print(f"   Lighting: {aesthetic['lighting']}/5")
    print(f"   Subject Interest: {aesthetic['subject_interest']}/5")
    print(f"\n   Notes: {aesthetic['notes']}")


def example_4_error_handling():
    """Example 4: Proper error handling"""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)

    client = PhotoAnalysisClient(
        api_url="http://localhost:8000",
        api_key="your-api-key-here"
    )

    image_path = "sample_images/photo.jpg"

    try:
        # Check server health first
        health = client.health_check()
        if health['status'] != 'healthy':
            raise Exception(f"Server unhealthy: {health}")

        # Analyze image
        result = client.analyze_image(image_path)

        print(f"✅ Analysis successful!")
        print(f"   Aesthetic: {result['aesthetic']['overall_aesthetic']}/5")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server")
        print("   Make sure the server is running: ./start_api.sh")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Error: Unauthorized - check your API key")
        elif e.response.status_code == 500:
            print("❌ Error: Server error - check server logs")
        else:
            print(f"❌ HTTP Error: {e}")

    except FileNotFoundError:
        print(f"❌ Error: Image not found: {image_path}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_5_token_tracking():
    """Example 5: Monitor token usage and costs"""
    print("\n" + "=" * 60)
    print("Example 5: Token Usage Tracking")
    print("=" * 60)

    client = PhotoAnalysisClient(
        api_url="http://localhost:8000",
        api_key="your-api-key-here"
    )

    # Analyze a few images
    images = ["sample_images/photo1.jpg", "sample_images/photo2.jpg"]

    print(f"\n📸 Analyzing {len(images)} images with token tracking...\n")

    for image_path in images:
        result = client.analyze_image(image_path, include_token_usage=True)

        print(f"{Path(image_path).name}:")

        if 'token_usage' in result:
            for agent, usage in result['token_usage'].items():
                print(f"  {agent}:")
                print(f"    Tokens: {usage['total_token_count']}")
                print(f"    Cost: ${usage['estimated_cost_usd']:.4f}")

        print(f"  Total: ${result.get('total_cost_usd', 0):.4f}\n")

    # Get aggregate stats
    stats = client.get_token_usage()
    print(f"📊 Aggregate Statistics:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Total Cost: ${stats['total_cost_usd']:.4f}")


if __name__ == "__main__":
    # Update API_KEY from environment
    import os
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("API_KEY", "your-secret-api-key-here")

    print("🎨 Photo Analysis API Client Examples")
    print()
    print("Make sure:")
    print("1. API server is running: ./start_api.sh")
    print("2. API_KEY is set in .env file")
    print("3. Sample images exist in sample_images/")
    print()

    # Run examples
    try:
        example_1_basic_analysis()
        # example_2_batch_processing()
        # example_3_aesthetic_only()
        # example_4_error_handling()
        # example_5_token_tracking()

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
