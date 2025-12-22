"""
Test script for MCP server

This tests the MCP server implementation locally.

Run with: python tests/test_mcp.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test MCP server functionality"""

    print("=" * 60)
    print("🧪 MCP Server Test Suite")
    print("=" * 60)

    # Find a test image
    test_image = None
    sample_dir = Path("sample_images")
    if sample_dir.exists():
        images = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
        if images:
            test_image = str(images[0].absolute())

    if not test_image:
        print("\n⚠️  Warning: No test images found in sample_images/")
        print("   Creating a placeholder...")
        # You'll need to provide an actual image path
        test_image = "/path/to/your/test/image.jpg"

    print(f"\n📁 Test image: {test_image}")

    # Set up MCP server parameters
    server_script = Path(__file__).parent.parent / "mcp" / "photo_analysis_server.py"

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", str(server_script)],
    )

    print(f"\n🚀 Starting MCP server: {server_script}")

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
                    print(f"   - {tool.name}: {tool.description[:60]}...")

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
                        print("\n" + result.content[0].text[:500] + "...")
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


async def test_mcp_tools_list():
    """Quick test to just list available tools"""
    print("🧪 Quick MCP Tools Test")
    print("-" * 40)

    server_script = Path(__file__).parent.parent / "mcp" / "photo_analysis_server.py"

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", str(server_script)],
    )

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP server")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test (just list tools)"
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to test image"
    )

    args = parser.parse_args()

    if args.quick:
        asyncio.run(test_mcp_tools_list())
    else:
        asyncio.run(test_mcp_server())
