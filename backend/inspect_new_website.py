"""
Template script to inspect a new website and find CSS selectors

INSTRUCTIONS:
1. Change the URL to your target website
2. Add selectors you want to test in the selectors_to_check list
3. Run: docker-compose exec backend python inspect_new_website.py
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_website():
    """Inspect website to find correct selectors"""

    # ============================================
    # CHANGE THIS URL TO YOUR TARGET WEBSITE
    # ============================================
    url = "https://example.com/page-to-scrape"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("\n" + "="*80)
        print(f"🔍 INSPECTING: {url}")
        print("="*80 + "\n")

        # Navigate to page
        print(f"📍 Loading page...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        print("✅ Page loaded\n")

        # Get page title
        title = await page.title()
        print(f"📄 Page title: {title}\n")

        # ============================================
        # ADD YOUR SELECTORS TO TEST HERE
        # ============================================
        selectors_to_check = [
            "h1",                          # Main heading
            "h1.title",                    # Heading with class
            "#main-content",               # Element with ID
            ".price",                      # Elements with class
            "div.product-info",            # Div with class
            "table tr",                    # Table rows
            "ul.stats > li",               # List items
            "span.value",                  # Span elements
        ]

        print("🔎 Testing selectors:")
        print("-" * 60)

        for selector in selectors_to_check:
            count = await page.locator(selector).count()
            if count > 0:
                # Get first element's text content
                first_elem = page.locator(selector).first
                text = await first_elem.text_content()
                text_clean = text.strip()[:60] if text else ""
                print(f"  ✅ {selector:40} → {count} elements | '{text_clean}'")
            else:
                print(f"  ❌ {selector:40} → NOT FOUND")

        # ============================================
        # INSPECT SPECIFIC ELEMENTS (customize this)
        # ============================================
        print("\n📝 Finding all H1 elements:")
        h1_elements = await page.locator("h1").all()
        for idx, h1 in enumerate(h1_elements):
            text = await h1.text_content()
            classes = await h1.get_attribute("class")
            print(f"  h1[{idx}]: {text} (class='{classes}')")

        print("\n📝 Finding divs with IDs:")
        divs_with_ids = await page.locator("div[id]").all()
        for idx, div in enumerate(divs_with_ids[:10]):
            div_id = await div.get_attribute("id")
            print(f"  div#{div_id}")

        await browser.close()

        print("\n" + "="*80)
        print("✅ INSPECTION COMPLETE")
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(inspect_website())
