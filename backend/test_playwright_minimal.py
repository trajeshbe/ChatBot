"""
Minimal Playwright test to diagnose the issue
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_playwright():
    """Test Playwright initialization"""
    try:
        logger.info("="*80)
        logger.info("MINIMAL PLAYWRIGHT TEST")
        logger.info("="*80)

        chromium_path = "/ms-playwright/chromium-1140/chrome-linux/chrome"
        logger.info(f"Using chromium path: {chromium_path}")

        # Check if file exists
        import os
        if os.path.exists(chromium_path):
            logger.info(f"✅ Chromium executable exists")
            logger.info(f"   Executable: {os.access(chromium_path, os.X_OK)}")
        else:
            logger.error(f"❌ Chromium executable NOT found")
            return

        # Try initializing Playwright
        logger.info("Initializing async_playwright()...")
        playwright = await async_playwright().start()
        logger.info("✅ Playwright initialized")

        # Try launching with explicit path
        logger.info(f"Launching chromium with explicit path...")
        browser = await playwright.chromium.launch(
            executable_path=chromium_path,
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        logger.info(f"✅ Browser launched: {browser}")

        await browser.close()
        await playwright.stop()
        logger.info("✅ TEST PASSED!")

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_playwright())
