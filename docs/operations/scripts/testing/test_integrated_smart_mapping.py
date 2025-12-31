"""
Test Integrated Smart Template Mapping

This script demonstrates the integration of map_to_custom_template() with:
1. New /smart-map-to-template endpoint
2. Enhanced /custom endpoint with use_smart_mapping flag
"""

import asyncio
import httpx
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def test_smart_map_endpoint():
    """Test the new /smart-map-to-template endpoint"""

    logger.info("\n" + "="*80)
    logger.info("TEST 1: NEW /smart-map-to-template ENDPOINT")
    logger.info("="*80)

    request_data = {
        "url": "https://www.screener.in/company/RELIANCE/",
        "template_columns": [
            "Company Name",
            "Market Cap",
            "Current Price",
            "Stock P/E",
            "Book Value",
            "Dividend Yield",
            "ROCE",
            "ROE",
            "Revenue Growth",  # This field may not be available
            "Market Position"
        ],
        "template_examples": {
            "Market Cap": "1,234 Cr",
            "Stock P/E": "25.3",
            "ROCE": "11.5 %"
        },
        "llm_provider": "openai",
        "output_format": "json"
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"\nSending request to {BASE_URL}/api/v1/extract/smart-map-to-template")
            logger.info(f"Template columns: {request_data['template_columns']}")

            response = await client.post(
                f"{BASE_URL}/api/v1/extract/smart-map-to-template",
                json=request_data
            )

            logger.info(f"\nResponse status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()

                logger.info("\n✓ SUCCESS!")
                logger.info(f"Template: {result['template_name']}")
                logger.info(f"URL: {result['url']}")
                logger.info(f"Rows: {result['row_count']}")

                if result['data']:
                    logger.info("\nExtracted Data:")
                    data = result['data'][0]

                    for col, value in data.items():
                        status = "✓" if value != "— (requires additional research)" else "✗"
                        logger.info(f"  {status} {col:25} : {value}")
                else:
                    logger.warning("No data extracted")
            else:
                logger.error(f"Request failed: {response.text}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_custom_template_with_smart_mapping():
    """Test the enhanced /custom endpoint with use_smart_mapping=true"""

    logger.info("\n" + "="*80)
    logger.info("TEST 2: ENHANCED /custom ENDPOINT WITH use_smart_mapping=true")
    logger.info("="*80)

    request_data = {
        "name": "Financial Data Extractor",
        "description": "Extract financial metrics using smart mapping",
        "url": "https://www.screener.in/company/RELIANCE/",
        "use_smart_mapping": True,  # This is the new flag!
        "fields": [
            {"name": "Company Name"},
            {"name": "Market Cap"},
            {"name": "Current Price"},
            {"name": "Stock P/E"},
            {"name": "Book Value"},
            {"name": "Dividend Yield"},
            {"name": "ROCE"},
            {"name": "ROE"},
            {"name": "Face Value"},
            {"name": "EPS Growth"},  # May not be available
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"\nSending request to {BASE_URL}/api/v1/extract/custom")
            logger.info("use_smart_mapping: TRUE")
            logger.info(f"Fields: {[f['name'] for f in request_data['fields']]}")

            response = await client.post(
                f"{BASE_URL}/api/v1/extract/custom",
                json=request_data
            )

            logger.info(f"\nResponse status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()

                logger.info("\n✓ SUCCESS!")
                logger.info(f"Template: {result['template_name']}")
                logger.info(f"URL: {result['url']}")
                logger.info(f"Rows: {result['row_count']}")

                if result['data']:
                    logger.info("\nExtracted Data:")
                    data = result['data'][0]

                    successful = 0
                    missing = 0

                    for col, value in data.items():
                        if value != "— (requires additional research)":
                            status = "✓"
                            successful += 1
                        else:
                            status = "✗"
                            missing += 1
                        logger.info(f"  {status} {col:25} : {value}")

                    logger.info(f"\nSummary: {successful}/{len(data)} fields extracted successfully")
                    if missing > 0:
                        logger.info(f"         {missing} fields require additional research")
                else:
                    logger.warning("No data extracted")
            else:
                logger.error(f"Request failed: {response.text}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_custom_template_selector_based():
    """Test the traditional selector-based extraction (for comparison)"""

    logger.info("\n" + "="*80)
    logger.info("TEST 3: TRADITIONAL /custom ENDPOINT (Selector-Based)")
    logger.info("="*80)
    logger.info("This is the OLD approach using CSS selectors")

    request_data = {
        "name": "Financial Data Extractor (Selectors)",
        "description": "Extract financial metrics using CSS selectors",
        "url": "https://www.screener.in/company/RELIANCE/",
        "use_smart_mapping": False,  # Use traditional selector-based extraction
        "fields": [
            {
                "name": "Company Name",
                "selector": "h1.h2",
                "data_type": "text"
            },
            {
                "name": "Market Cap",
                "selector": "#top-ratios > li:nth-child(1) > span.number",
                "data_type": "text"
            },
            {
                "name": "Current Price",
                "selector": "#top-ratios > li:nth-child(2) > span.number",
                "data_type": "text"
            },
            {
                "name": "Stock P/E",
                "selector": "#top-ratios > li:nth-child(3) > span.number",
                "data_type": "text"
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"\nSending request to {BASE_URL}/api/v1/extract/custom")
            logger.info("use_smart_mapping: FALSE (traditional selectors)")
            logger.info(f"Fields: {[f['name'] for f in request_data['fields']]}")

            response = await client.post(
                f"{BASE_URL}/api/v1/extract/custom",
                json=request_data
            )

            logger.info(f"\nResponse status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()

                logger.info("\n✓ SUCCESS!")
                logger.info(f"Template: {result['template_name']}")
                logger.info(f"Rows: {result['row_count']}")

                if result['data']:
                    logger.info("\nExtracted Data:")
                    data = result['data'][0]

                    for col, value in data.items():
                        status = "✓" if value else "✗"
                        logger.info(f"  {status} {col:25} : {value}")
                else:
                    logger.warning("No data extracted")
            else:
                logger.error(f"Request failed: {response.text}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_comparison():
    """Compare smart mapping vs selector-based extraction"""

    logger.info("\n" + "="*80)
    logger.info("COMPARISON: Smart Mapping vs Selector-Based")
    logger.info("="*80)

    logger.info("""
Smart Mapping Benefits:
- ✓ No need to write CSS selectors
- ✓ Adapts to page structure changes
- ✓ Never hallucinates missing values
- ✓ Clear marking of fields requiring research
- ✓ Works with any webpage structure

Selector-Based Benefits:
- ✓ Fast and precise
- ✓ Deterministic (same HTML → same result)
- ✓ No LLM API costs
- ✓ Works offline

When to Use Smart Mapping:
- Template extraction returning null values
- Page structure changes frequently
- Don't want to maintain selectors
- Extracting from multiple similar pages with variations
- Quick one-time data extraction

When to Use Selectors:
- Page structure is stable
- Need maximum speed
- Want zero LLM costs
- Extracting very large datasets
""")


async def main():
    """Run all tests"""

    print("\n" + "="*80)
    print("INTEGRATED SMART TEMPLATE MAPPING TESTS")
    print("="*80)
    print("\nThese tests demonstrate the new smart mapping integration:")
    print("1. New /smart-map-to-template endpoint")
    print("2. Enhanced /custom endpoint with use_smart_mapping flag")
    print("3. Comparison with traditional selector-based extraction")
    print("\nMake sure the backend is running on http://localhost:8000")
    print("="*80 + "\n")

    # Run tests
    await test_smart_map_endpoint()
    print("\n" + "-"*80)

    await test_custom_template_with_smart_mapping()
    print("\n" + "-"*80)

    await test_custom_template_selector_based()
    print("\n" + "-"*80)

    await test_comparison()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
