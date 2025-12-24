"""
Test script for MCP server running in Docker

This tests the MCP server implementation running in the Docker container.

Run with: python tests/test_mcp.py
Or with flags:
  --quick    Just list tools
  --docker   Use Docker container (default)
  --local    Use local Python
  --image    Path to test image
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def find_test_image() -> str:
    """Find a test image in sample_images directory."""
    sample_dir = Path("sample_images")
    if sample_dir.exists():
        images = (
            list(sample_dir.glob("*.jpg")) + 
            list(sample_dir.glob("*.jpeg")) +
            list(sample_dir.glob("*.png")) +
            list(sample_dir.glob("*.HEIC")) +
            list(sample_dir.glob("*.heic"))
        )
        if images:
            return str(images[0].absolute())
    return "/path/to/your/test/image.jpg"


def get_docker_server_params() -> StdioServerParameters:
    """Get MCP server parameters for Docker container."""
    return StdioServerParameters(
        command="docker",
        args=[
            "exec", "-i", "photo-mcp",
            "python", "mcp/photo_analysis_server.py"
        ],
    )


def get_local_server_params() -> StdioServerParameters:
    """Get MCP server parameters for local Python."""
    server_script = Path(__file__).parent.parent / "mcp" / "photo_analysis_server.py"
    return StdioServerParameters(
        command="uv",
        args=["run", "python", str(server_script)],
    )


async def test_mcp_server(use_docker: bool = True, test_image: str = None):
    """Test MCP server functionality"""

    print("=" * 60)
    print("🧪 MCP Server Test Suite")
    print(f"   Mode: {'Docker Container' if use_docker else 'Local Python'}")
    print("=" * 60)

    # Find a test image
    if not test_image:
        test_image = find_test_image()
    
    # For Docker, we need to use container-internal paths
    if use_docker:
        # Map local path to container path
        local_path = Path(test_image)
        if local_path.exists():
            # The container mounts sample_images, so use relative path
            container_image = f"/app/sample_images/{local_path.name}"
            print(f"\n📁 Local image: {test_image}")
            print(f"📦 Container path: {container_image}")
            test_image = container_image
        else:
            print(f"⚠️  Warning: Test image not found: {test_image}")
    else:
        print(f"\n📁 Test image: {test_image}")

    # Get server parameters based on mode
    if use_docker:
        server_params = get_docker_server_params()
        print(f"\n🐳 Using Docker container: photo-mcp")
    else:
        server_params = get_local_server_params()
        print(f"\n🐍 Using local Python")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                print("\n1️⃣  Initializing session...")
                await session.initialize()
                print("✅ Session initialized")

                # List available tools
                print("\n2️⃣  Listing available tools...")
                tools = await session.list_tools()

                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    desc = tool.description[:60] + "..." if len(tool.description) > 60 else tool.description
                    print(f"   - {tool.name}: {desc}")

                # Test 1: Aesthetic assessment
                print("\n3️⃣  Testing aesthetic assessment...")
                try:
                    result = await session.call_tool(
                        "assess_aesthetic_quality",
                        arguments={"image_path": test_image}
                    )

                    if result.content:
                        print("✅ Aesthetic assessment successful")
                        print("\n" + result.content[0].text)
                    else:
                        print("❌ No content returned")

                except Exception as e:
                    print(f"❌ Aesthetic assessment failed: {e}")

                # Test 2: Categorization
                print("\n4️⃣  Testing categorization...")
                try:
                    result = await session.call_tool(
                        "categorize_photo",
                        arguments={"image_path": test_image}
                    )

                    if result.content:
                        print("✅ Categorization successful")
                        print("\n" + result.content[0].text)
                    else:
                        print("❌ No content returned")

                except Exception as e:
                    print(f"❌ Categorization failed: {e}")

                # Test 3: Caption generation
                print("\n5️⃣  Testing caption generation...")
                try:
                    result = await session.call_tool(
                        "generate_caption",
                        arguments={
                            "image_path": test_image,
                            "caption_level": "concise"
                        }
                    )

                    if result.content:
                        print("✅ Caption generation successful")
                        print("\n" + result.content[0].text)
                    else:
                        print("❌ No content returned")

                except Exception as e:
                    print(f"❌ Caption generation failed: {e}")

                # Test 4: Full analysis
                print("\n6️⃣  Testing full analysis...")
                try:
                    result = await session.call_tool(
                        "analyze_photo",
                        arguments={
                            "image_path": test_image,
                            "include_aesthetic": True,
                            "include_filtering": True,
                            "include_caption": True
                        }
                    )

                    if result.content:
                        print("✅ Full analysis successful")
                        text = result.content[0].text
                        print("\n" + (text[:500] + "..." if len(text) > 500 else text))
                    else:
                        print("❌ No content returned")

                except Exception as e:
                    print(f"❌ Full analysis failed: {e}")

                # Test 5: Token usage
                print("\n7️⃣  Testing token usage stats...")
                try:
                    result = await session.call_tool(
                        "get_token_usage",
                        arguments={"limit": 5}
                    )

                    if result.content:
                        print("✅ Token usage retrieval successful")
                        print("\n" + result.content[0].text)
                    else:
                        print("❌ No content returned")

                except Exception as e:
                    print(f"❌ Token usage failed: {e}")

                print("\n" + "=" * 60)
                print("✅ All MCP tests completed!")
                print("=" * 60)

    except Exception as e:
        print(f"\n❌ MCP server test failed: {e}")
        import traceback
        traceback.print_exc()
        
        if use_docker:
            print("\n💡 Make sure Docker container is running:")
            print("   docker compose up mcp -d")
            print("   docker ps  # should show photo-mcp container")


async def test_mcp_tools_list(use_docker: bool = True):
    """Quick test to just list available tools"""
    print("🧪 Quick MCP Tools Test")
    print(f"   Mode: {'Docker Container' if use_docker else 'Local Python'}")
    print("-" * 40)

    if use_docker:
        server_params = get_docker_server_params()
    else:
        server_params = get_local_server_params()

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()

                print(f"\n✅ MCP Server is working!")
                print(f"\nAvailable tools ({len(tools.tools)}):\n")

                for i, tool in enumerate(tools.tools, 1):
                    print(f"{i}. {tool.name}")
                    print(f"   {tool.description}")
                    print()

    except Exception as e:
        print(f"❌ Failed: {e}")
        if use_docker:
            print("\n💡 Make sure Docker container is running:")
            print("   docker compose up mcp -d")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP server")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test (just list tools)"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        default=True,
        help="Use Docker container (default)"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local Python instead of Docker"
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to test image"
    )

    args = parser.parse_args()
    
    # Determine mode
    use_docker = not args.local

    if args.quick:
        asyncio.run(test_mcp_tools_list(use_docker=use_docker))
    else:
        asyncio.run(test_mcp_server(use_docker=use_docker, test_image=args.image))
