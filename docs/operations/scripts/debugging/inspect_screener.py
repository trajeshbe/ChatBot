"""
Inspect Screener.in page to find correct CSS selectors
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_screener():
    """Inspect Screener.in to find correct selectors"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("\n" + "="*80)
        print("🔍 INSPECTING SCREENER.IN PAGE STRUCTURE")
        print("="*80 + "\n")

        # Navigate to Screener.in
        url = "https://www.screener.in/company/RELIANCE/consolidated/"
        print(f"📍 Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        print("✅ Page loaded\n")

        # Get page title
        title = await page.title()
        print(f"📄 Page title: {title}\n")

        # Check for common selectors
        print("🔎 Checking for common selectors:")
        print("-" * 60)

        selectors_to_check = [
            "#company-ratios",
            "#top-ratios",
            ".top-ratios",
            "h1",
            "h1.h2",
            ".company-name",
            "#top-ratios > li",
            "ul.top-ratios",
            "ul.top-ratios > li",
        ]

        for selector in selectors_to_check:
            count = await page.locator(selector).count()
            print(f"  {selector:40} → {count} elements")

        # Find h1 elements
        print("\n📝 H1 Elements found:")
        h1_elements = await page.locator("h1").all()
        for idx, h1 in enumerate(h1_elements):
            text = await h1.text_content()
            classes = await h1.get_attribute("class")
            print(f"  h1[{idx}]: {text} (class='{classes}')")

        # Find divs with IDs
        print("\n📝 Divs with IDs:")
        divs_with_ids = await page.locator("div[id]").all()
        for idx, div in enumerate(divs_with_ids[:10]):
            div_id = await div.get_attribute("id")
            print(f"  div#{div_id}")

        # Find UL elements
        print("\n📝 UL Elements:")
        ul_elements = await page.locator("ul").all()
        for idx, ul in enumerate(ul_elements[:5]):
            classes = await ul.get_attribute("class")
            li_count = await ul.locator("li").count()
            print(f"  ul[{idx}]: class='{classes}', {li_count} li elements")

            # If this looks like the ratios list, print first few li elements
            if li_count > 0 and li_count < 20:
                lis = await ul.locator("li").all()
                for li_idx, li in enumerate(lis[:3]):
                    text = await li.text_content()
                    text_clean = text.strip().replace("\n", " ")[:60]
                    print(f"    li[{li_idx}]: {text_clean}...")

        # Try to find Market Cap specifically
        print("\n🎯 Looking for Market Cap:")
        possible_selectors = [
            "li:has-text('Market Cap') span.number",
            "li:has-text('Market Cap')",
            "ul li:nth-child(1)",
            "ul.top-ratios li:nth-child(1)",
        ]

        for selector in possible_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    print(f"  ✅ {selector:50} → {text.strip()[:60]}")
                else:
                    print(f"  ❌ {selector:50} → NOT FOUND")
            except Exception as e:
                print(f"  ❌ {selector:50} → ERROR: {e}")

        # Get first few ratio items
        print("\n📊 First 5 ratio items (if they exist):")
        try:
            ratio_items = page.locator("ul li")
            count = await ratio_items.count()
            print(f"  Found {count} li elements total")

            for i in range(min(5, count)):
                item = ratio_items.nth(i)
                text = await item.text_content()
                text_clean = text.strip().replace("\n", " ")
                print(f"  li[{i}]: {text_clean[:80]}")
        except Exception as e:
            print(f"  Error: {e}")

        await browser.close()

        print("\n" + "="*80)
        print("✅ INSPECTION COMPLETE")
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(inspect_screener())
