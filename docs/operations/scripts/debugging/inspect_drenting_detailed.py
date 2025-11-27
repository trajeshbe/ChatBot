"""
Detailed inspection of drenting.com car listings
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_drenting_detailed():
    """Inspect drenting.com car listing structure"""

    url = "https://www.drenting.com/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        print("\n" + "="*80)
        print("🚗 INSPECTING DRENTING.COM CAR LISTINGS")
        print("="*80 + "\n")

        await page.goto(url, wait_until="networkidle", timeout=60000)

        # Find car cards
        print("📋 Analyzing car listing cards:\n")

        cards = await page.locator(".card").all()
        print(f"Found {len(cards)} car cards\n")

        if len(cards) > 0:
            # Inspect first card in detail
            first_card = cards[0]

            print("🔍 First card structure:")
            print("-" * 60)

            # Try common selectors
            selectors_to_test = [
                "h3",
                ".card-title",
                ".price",
                ".monthly",
                ".modelo",
                ".marca",
                "span",
                "p",
                "a",
            ]

            for selector in selectors_to_test:
                elements = await first_card.locator(selector).all()
                if elements:
                    text = await elements[0].text_content()
                    print(f"  {selector:20} → '{text.strip()[:60]}'")

            # Get all text content
            print("\n📄 Full card text:")
            full_text = await first_card.text_content()
            print(full_text[:300])

        # Look for price patterns
        print("\n\n💰 Looking for prices:")
        print("-" * 60)

        # Common price selectors
        price_selectors = [
            "text=/€/",
            "text=/mes/",
            "span:has-text('€')",
            ".price",
            ".precio",
        ]

        for selector in price_selectors:
            elements = await page.locator(selector).all()
            if elements and len(elements) > 0:
                text = await elements[0].text_content()
                print(f"  {selector:30} → '{text.strip()[:60]}'")

        await browser.close()

        print("\n" + "="*80)
        print("✅ DETAILED INSPECTION COMPLETE")
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(inspect_drenting_detailed())
