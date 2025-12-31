"""
Minimal Playwright test endpoint for debugging
"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/test", tags=["Playwright Tests"])


@router.get("/playwright-minimal")
async def test_playwright_minimal():
    """
    Minimal Playwright test endpoint - directly initializes and launches browser
    """
    try:
        import os

        # CRITICAL: Set PLAYWRIGHT_BROWSERS_PATH BEFORE importing playwright
        # Workaround for volume mounting issue where docker-compose env vars aren't seen by Python
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/ms-playwright'

        # Now import playwright AFTER setting the env var
        from playwright.async_api import async_playwright

        logger.info("="*80)
        logger.info("MINIMAL PLAYWRIGHT TEST IN FASTAPI")
        logger.info("="*80)

        # Check environment
        env_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', 'NOT SET')
        logger.info(f"PLAYWRIGHT_BROWSERS_PATH env: {env_path}")

        chromium_path = "/ms-playwright/chromium-1140/chrome-linux/chrome"
        logger.info(f"Target chromium path: {chromium_path}")

        # Check if file exists
        if os.path.exists(chromium_path):
            logger.info(f"✅ Chromium executable exists")
            logger.info(f"   Executable: {os.access(chromium_path, os.X_OK)}")
        else:
            logger.error(f"❌ Chromium executable NOT found")
            return {
                "success": False,
                "error": f"Chromium not found at {chromium_path}",
                "env": env_path
            }

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

        # Get version
        version = browser.version
        logger.info(f"Browser version: {version}")

        await browser.close()
        await playwright.stop()
        logger.info("✅ TEST PASSED IN FASTAPI!")

        return {
            "success": True,
            "message": "Playwright works in FastAPI!",
            "browser_version": version,
            "chromium_path": chromium_path,
            "env": env_path
        }

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
