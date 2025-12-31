"""
Test CSS selector-based extraction with Bharti Airtel URL
"""
import asyncio
from app.services.template_extraction_service import template_extraction_service, get_screener_in_template

async def test_bharti_extraction():
    """Test extraction with Bharti Airtel company page"""

    print("\n" + "="*80)
    print("🧪 TESTING CSS SELECTOR EXTRACTION - BHARTI AIRTEL")
    print("="*80 + "\n")

    try:
        # Initialize service
        print("📦 Initializing template extraction service...")
        await template_extraction_service.initialize()
        print("✅ Service initialized\n")

        # Get template
        template = get_screener_in_template()
        print(f"📋 Template: {template.name}")
        print(f"🔢 Fields configured: {len(template.fields)}\n")

        # Test URL
        url = "https://www.screener.in/company/BHARTIARTL/consolidated/"
        print(f"🌐 Testing extraction from: {url}\n")
        print("⏳ Extracting data (this may take 10-30 seconds)...\n")

        # Extract data
        result = await template_extraction_service.extract_data(
            url=url,
            template=template,
            session_id="test_bharti"
        )

        print("\n" + "="*80)
        print("📊 EXTRACTION RESULTS")
        print("="*80 + "\n")

        print(f"✅ Success: {result['success']}")
        print(f"📍 URL: {result['url']}")
        print(f"📋 Template: {result['template_name']}")
        print(f"🔢 Rows extracted: {result['row_count']}\n")

        if result['success'] and result['data']:
            print(f"📄 Extracted data for Bharti Airtel:\n")
            data = result['data'][0]  # First row

            # Print each field with formatting
            for field_name, value in data.items():
                # Format the value for display
                if value:
                    value_display = str(value)[:80]
                    print(f"  ✓ {field_name:25} : {value_display}")
                else:
                    print(f"  ✗ {field_name:25} : (not extracted)")

            # Count successful extractions
            non_empty = sum(1 for v in data.values() if v and v not in [None, "N/A", ""])
            total = len(data)
            success_rate = (non_empty/total*100) if total > 0 else 0

            print(f"\n📊 Extraction Statistics:")
            print(f"   Fields extracted: {non_empty}/{total}")
            print(f"   Success rate: {success_rate:.1f}%")

            if success_rate >= 80:
                print(f"\n✅ EXCELLENT! Extraction working perfectly!")
            elif success_rate >= 60:
                print(f"\n⚠️  GOOD but some fields missing")
            else:
                print(f"\n❌ POOR extraction rate - needs investigation")

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
    asyncio.run(test_bharti_extraction())
