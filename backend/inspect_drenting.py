"""
Inspect drenting.com using Playwright (can bypass some anti-bot checks)
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_drenting():
    """Inspect drenting.com with Playwright"""

    url = "https://www.drenting.com/"

    async with async_playwright() as p:
        # Launch browser with realistic settings to avoid detection
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Create context with realistic viewport and user agent
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        print("\n" + "="*80)
        print(f"🔍 INSPECTING: {url}")
        print("="*80 + "\n")

        try:
            # Navigate with realistic wait
            print(f"📍 Loading page...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("✅ Page loaded\n")

            # Get page title
            title = await page.title()
            print(f"📄 Page title: {title}\n")

            # Check for common selectors
            print("🔎 Testing selectors:")
            print("-" * 60)

            selectors_to_check = [
                "h1",
                "h2",
                "h3",
                ".property",
                ".listing",
                ".price",
                ".title",
                "article",
                ".card",
                "#content",
                "main",
            ]

            for selector in selectors_to_check:
                count = await page.locator(selector).count()
                if count > 0:
                    first_elem = page.locator(selector).first
                    text = await first_elem.text_content()
                    text_clean = text.strip()[:60] if text else ""
                    print(f"  ✅ {selector:40} → {count} elements | '{text_clean}'")
                else:
                    print(f"  ❌ {selector:40} → NOT FOUND")

            # Get page screenshot for debugging
            await page.screenshot(path='/tmp/drenting_screenshot.png')
            print(f"\n📸 Screenshot saved to /tmp/drenting_screenshot.png")

            # Get page HTML structure
            html_snippet = await page.content()
            print(f"\n📄 Page has {len(html_snippet)} characters of HTML")

            # Check if it's a captcha or block page
            if "captcha" in html_snippet.lower() or "blocked" in html_snippet.lower():
                print("\n⚠️  WARNING: Page may contain captcha or block message")

        except Exception as e:
            print(f"\n❌ Error loading page: {e}")
            print("\nThis usually means:")
            print("  1. Website is blocking automated access")
            print("  2. Need to use proxies or more advanced anti-detection")
            print("  3. Website requires JavaScript/cookies/authentication")

        finally:
            await browser.close()

        print("\n" + "="*80)
        print("✅ INSPECTION COMPLETE")
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(inspect_drenting())
