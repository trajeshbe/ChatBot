"""
Test the fixed Screener.in template
"""
import asyncio
import json
from app.services.template_extraction_service import template_extraction_service, get_screener_in_template

async def test_template():
    """Test the fixed template"""

    print("\n" + "="*80)
    print("🧪 TESTING FIXED SCREENER.IN TEMPLATE")
    print("="*80 + "\n")

    try:
        # Initialize service
        print("📦 Initializing template extraction service...")
        await template_extraction_service.initialize()
        print("✅ Service initialized\n")

        # Get template
        template = get_screener_in_template()
        print(f"📋 Template: {template.name}")
        print(f"📝 Description: {template.description}")
        print(f"🔍 Wait for selector: {template.wait_for_selector}")
        print(f"🔢 Fields: {len(template.fields)}\n")

        # Print fields
        print("📊 Fields to extract:")
        for idx, field in enumerate(template.fields, 1):
            print(f"  {idx}. {field.name:20} → selector: {field.selector or 'default'}")

        # Test extraction
        url = "https://www.screener.in/company/RELIANCE/consolidated/"
        print(f"\n🌐 Testing extraction from: {url}\n")

        result = await template_extraction_service.extract_data(
            url=url,
            template=template,
            session_id="test_session"
        )

        print("\n" + "="*80)
        print("📊 EXTRACTION RESULTS")
        print("="*80 + "\n")

        print(f"✅ Success: {result['success']}")
        print(f"📍 URL: {result['url']}")
        print(f"📋 Template: {result['template_name']}")
        print(f"🔢 Rows extracted: {result['row_count']}")

        if result['success'] and result['data']:
            print(f"\n📄 Extracted data:")
            data = result['data'][0]  # First row
            for field_name, value in data.items():
                value_display = str(value)[:60] if value else "None"
                print(f"  {field_name:20} = {value_display}")

            # Count successful extractions
            non_empty = sum(1 for v in data.values() if v and v not in [None, "N/A", ""])
            total = len(data)
            print(f"\n📊 Extraction rate: {non_empty}/{total} fields ({non_empty/total*100:.1f}%)")

        else:
            print(f"\n❌ Extraction failed:")
            print(f"   Error: {result.get('error', 'Unknown error')}")

        print("\n" + "="*80)
        print("✅ TEST COMPLETED")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        await template_extraction_service.close()
        print("✅ Cleanup complete\n")

if __name__ == "__main__":
    asyncio.run(test_template())
