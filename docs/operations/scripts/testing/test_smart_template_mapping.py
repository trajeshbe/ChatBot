"""
Test Script for Smart Template Mapping

This script demonstrates the new map_to_custom_template() method that intelligently
maps scraped web data to custom template columns using LLM.
"""

import asyncio
import logging
from app.services.llm_service import llm_service
from app.services.webscraper.extractors.llm_extractor import LLMExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_smart_mapping():
    """Test the smart template mapping functionality"""

    # Sample scraped data (example from screener.in)
    scraped_html = """
    <html>
    <body>
        <h1 class="h2">Reliance Industries Ltd.</h1>
        <div id="top-ratios">
            <ul>
                <li>
                    <span class="name">Market Cap</span>
                    <span class="number">₹ 17,88,392 Cr.</span>
                </li>
                <li>
                    <span class="name">Current Price</span>
                    <span class="number">₹ 2,645</span>
                </li>
                <li>
                    <span class="name">Stock P/E</span>
                    <span class="number">25.3</span>
                </li>
                <li>
                    <span class="name">Book Value</span>
                    <span class="number">₹ 1,289</span>
                </li>
                <li>
                    <span class="name">Dividend Yield</span>
                    <span class="number">0.34 %</span>
                </li>
                <li>
                    <span class="name">ROCE</span>
                    <span class="number">11.5 %</span>
                </li>
                <li>
                    <span class="name">ROE</span>
                    <span class="number">8.92 %</span>
                </li>
            </ul>
        </div>
        <section>
            <p>Reliance Industries is India's largest private sector company.</p>
        </section>
    </body>
    </html>
    """

    # Custom template columns (these would come from user's Excel template)
    template_columns = [
        "Company Name",
        "Market Cap",
        "Current Price",
        "Stock P/E",
        "Book Value",
        "Dividend Yield",
        "ROCE",
        "ROE",
        "Revenue Growth",  # This field is NOT in the scraped data
        "Market Position",
        "Source / Notes"
    ]

    # Optional: Example values from template
    template_examples = {
        "Market Cap": "1234",
        "Stock P/E": "25.3",
        "Revenue Growth": "15%"
    }

    try:
        # Initialize LLM service
        logger.info("Initializing LLM service...")
        await llm_service.initialize()

        # Create LLM extractor
        extractor = LLMExtractor(llm_service=llm_service)

        # Test the smart mapping
        logger.info("\n" + "="*80)
        logger.info("TESTING SMART TEMPLATE MAPPING")
        logger.info("="*80)
        logger.info(f"\nTemplate has {len(template_columns)} columns")
        logger.info(f"Scraped data length: {len(scraped_html)} characters")

        result = await extractor.map_to_custom_template(
            scraped_data=scraped_html,
            template_columns=template_columns,
            template_examples=template_examples,
            llm_provider="openai"  # Use OpenAI for best results
        )

        if result:
            logger.info("\n" + "="*80)
            logger.info("MAPPING RESULTS")
            logger.info("="*80)

            mapped_data = result['mapped_data']
            missing_fields = result['missing_fields']
            extraction_complete = result['extraction_complete']

            logger.info("\nMapped Data:")
            for col, value in mapped_data.items():
                status_icon = "✓" if value != "— (requires additional research)" else "✗"
                logger.info(f"  {status_icon} {col:25} : {value}")

            logger.info(f"\nExtraction Status:")
            logger.info(f"  - Complete: {extraction_complete}")
            logger.info(f"  - Fields requiring research: {len(missing_fields)}")

            if missing_fields:
                logger.info(f"\nMissing Fields:")
                for field in missing_fields:
                    logger.info(f"  - {field}")
        else:
            logger.error("Mapping failed - check LLM service configuration")

        logger.info("\n" + "="*80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        # Cleanup
        await llm_service.close()
        logger.info("Test completed")


async def test_with_minimal_data():
    """Test with minimal scraped data to show handling of missing fields"""

    scraped_text = """
    Company: Tech Corp
    Price: $150.25
    P/E Ratio: 18.5
    """

    template_columns = [
        "Company Name",
        "Current Price",
        "P/E Ratio",
        "Market Cap",
        "Revenue",
        "Profit Margin",
        "Debt to Equity"
    ]

    try:
        await llm_service.initialize()
        extractor = LLMExtractor(llm_service=llm_service)

        logger.info("\n" + "="*80)
        logger.info("TESTING WITH MINIMAL DATA (Many Missing Fields)")
        logger.info("="*80)

        result = await extractor.map_to_custom_template(
            scraped_data=scraped_text,
            template_columns=template_columns,
            llm_provider="openai"
        )

        if result:
            logger.info("\nMapped Data:")
            for col, value in result['mapped_data'].items():
                status_icon = "✓" if value != "— (requires additional research)" else "✗"
                logger.info(f"  {status_icon} {col:20} : {value}")

            logger.info(f"\n{len(result['missing_fields'])} fields require external research")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        await llm_service.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SMART TEMPLATE MAPPING TEST SUITE")
    print("="*80)
    print("\nThis test demonstrates the new map_to_custom_template() method")
    print("which uses LLM to map scraped data to custom template columns.")
    print("\nKey Features:")
    print("  - Never hallucinates values")
    print("  - Marks missing fields as '— (requires additional research)'")
    print("  - Provides transparency about data completeness")
    print("="*80 + "\n")

    # Run tests
    asyncio.run(test_smart_mapping())
    print("\n" + "-"*80 + "\n")
    asyncio.run(test_with_minimal_data())
