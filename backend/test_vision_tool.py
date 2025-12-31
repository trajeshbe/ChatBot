#!/usr/bin/env python3
"""
Test Vision Tool with Construction Drawing PDF

This script tests the vision_analysis tool with the actual construction
drawing PDF to verify intelligent tool selection and vision capabilities.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app')

from app.agents.tool_registry import tool_registry


async def test_vision_tool():
    """Test the vision tool with construction drawing PDF"""

    print("\n" + "="*80)
    print("🔍 VISION TOOL TEST - Construction Drawing Analysis")
    print("="*80 + "\n")

    # Path to the construction drawing PDF (copied to /tmp in container)
    pdf_path = "/tmp/construction_drawing.pdf"

    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: PDF not found at {pdf_path}")
        return

    file_size = os.path.getsize(pdf_path)
    print(f"📄 Testing with: A 1101 [C].pdf")
    print(f"   Size: {file_size/1024:.1f} KB")
    print(f"   Type: Construction Drawing (Galleon Gardens Clubhouse)\n")

    # Show available tools
    print("🔧 Available Tools in Registry:")
    all_tools = tool_registry.get_all_tools()
    for tool in all_tools:
        print(f"   - {tool.tool_id}: {tool.name}")
    print()

    # Get the vision tool
    vision_tool = tool_registry.get_tool("vision_analysis")

    if not vision_tool:
        print("❌ ERROR: vision_analysis tool not found in registry!")
        return

    print(f"✅ Found vision_analysis tool")
    print(f"   Description: {vision_tool.description[:100]}...")
    print()

    # Test 1: General analysis (no specific question)
    print("="*80)
    print("TEST 1: General Vision Analysis (Text Extraction + Description)")
    print("="*80 + "\n")

    try:
        print("🚀 Calling vision tool with PDF (general analysis)...")
        result1 = await vision_tool.function(
            image_path=pdf_path,
            question=None  # General analysis
        )

        print(f"\n📊 Result:")
        print(f"   Success: {result1.get('success', False)}")
        print(f"   Model: {result1.get('model', 'N/A')}")

        if result1.get('success'):
            analysis = result1.get('analysis', '')
            print(f"\n📝 Vision Analysis (first 500 chars):")
            print("-" * 80)
            print(analysis[:500])
            if len(analysis) > 500:
                print(f"... ({len(analysis) - 500} more characters)")
            print("-" * 80)
        else:
            print(f"   Error: {result1.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n")

    # Test 2: Specific question - floor count
    print("="*80)
    print("TEST 2: Specific Question - Floor Count")
    print("="*80 + "\n")

    try:
        print("🚀 Calling vision tool with question: 'How many floors are in this building?'")
        result2 = await vision_tool.function(
            image_path=pdf_path,
            question="How many floors are in this building? Please analyze the architectural drawing carefully."
        )

        print(f"\n📊 Result:")
        print(f"   Success: {result2.get('success', False)}")
        print(f"   Model: {result2.get('model', 'N/A')}")

        if result2.get('success'):
            answer = result2.get('analysis', '')
            print(f"\n🏢 Floor Count Analysis:")
            print("-" * 80)
            print(answer)
            print("-" * 80)
        else:
            print(f"   Error: {result2.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n")

    # Test 3: Gross Floor Area question
    print("="*80)
    print("TEST 3: Specific Question - Gross Floor Area (GFA)")
    print("="*80 + "\n")

    try:
        print("🚀 Calling vision tool with question: 'What is the Gross Floor Area?'")
        result3 = await vision_tool.function(
            image_path=pdf_path,
            question="What is the Gross Floor Area (GFA) shown in this architectural drawing?"
        )

        print(f"\n📊 Result:")
        print(f"   Success: {result3.get('success', False)}")
        print(f"   Model: {result3.get('model', 'N/A')}")

        if result3.get('success'):
            answer = result3.get('analysis', '')
            print(f"\n📐 GFA Analysis:")
            print("-" * 80)
            print(answer)
            print("-" * 80)
        else:
            print(f"   Error: {result3.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Test 3 Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("✅ VISION TOOL TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_vision_tool())
