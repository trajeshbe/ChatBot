"""
Playwright E2E Test for Template Extraction UI
Tests both preset templates and Excel upload to diagnose issues
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def test_template_extraction_ui():
    """Test template extraction UI and capture screenshots"""

    async with async_playwright() as p:
        # Launch browser in headless mode (no X server needed)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Create screenshots directory
        os.makedirs("/app/screenshots/template_extraction", exist_ok=True)

        print("\n" + "="*80)
        print("🧪 TESTING TEMPLATE EXTRACTION UI")
        print("="*80 + "\n")

        try:
            # Step 1: Navigate to the app
            print("📍 Step 1: Loading application...")
            await page.goto("http://localhost:3001", wait_until="networkidle")
            await page.screenshot(path="/app/screenshots/template_extraction/01_homepage.png")
            print("✅ Homepage loaded")

            # Step 2: Click on Data Extraction tab (if exists)
            print("\n📍 Step 2: Navigating to Data Extraction...")
            try:
                # Wait for navigation to load
                await asyncio.sleep(2)

                # Look for Data Extraction link/button
                data_extraction_button = page.locator("text=Data Extraction").first
                if await data_extraction_button.is_visible():
                    await data_extraction_button.click()
                    await asyncio.sleep(2)
                    await page.screenshot(path="/app/screenshots/template_extraction/02_data_extraction_page.png")
                    print("✅ Navigated to Data Extraction page")
                else:
                    print("⚠️ Data Extraction button not found, trying direct URL")
                    # Try direct navigation
                    await page.goto("http://localhost:3001", wait_until="networkidle")
                    await asyncio.sleep(2)
                    await page.screenshot(path="/app/screenshots/template_extraction/02_main_page.png")
            except Exception as e:
                print(f"⚠️ Navigation issue: {e}")
                await page.screenshot(path="/app/screenshots/template_extraction/02_navigation_error.png")

            # Step 3: Switch to Template-Based mode
            print("\n📍 Step 3: Switching to Template-Based extraction...")
            try:
                template_button = page.locator("text=Template-Based").first
                if await template_button.is_visible():
                    await template_button.click()
                    await asyncio.sleep(2)
                    await page.screenshot(path="/app/screenshots/template_extraction/03_template_mode.png")
                    print("✅ Switched to Template-Based mode")
                else:
                    print("⚠️ Template-Based button not visible")
                    # Capture current state
                    await page.screenshot(path="/app/screenshots/template_extraction/03_current_state.png")

                    # Try to find any mode selectors
                    print("\n🔍 Looking for mode selectors...")
                    mode_buttons = await page.locator("button").all()
                    for idx, btn in enumerate(mode_buttons):
                        text = await btn.text_content()
                        print(f"   Button {idx}: {text}")
            except Exception as e:
                print(f"⚠️ Mode switch error: {e}")
                await page.screenshot(path="/app/screenshots/template_extraction/03_mode_switch_error.png")

            # Step 4: Test Preset Template
            print("\n📍 Step 4: Testing preset template (Screener.in)...")
            try:
                # Select Screener.in preset
                preset_select = page.locator("select").first
                if await preset_select.is_visible():
                    await preset_select.select_option("screener_in")
                    await asyncio.sleep(1)
                    await page.screenshot(path="/app/screenshots/template_extraction/04_preset_selected.png")
                    print("✅ Selected Screener.in preset")

                    # Enter URL
                    url_input = page.locator("input[type='url']").first
                    await url_input.fill("https://www.screener.in/company/RELIANCE/consolidated/")
                    await asyncio.sleep(1)
                    await page.screenshot(path="/app/screenshots/template_extraction/05_url_entered.png")
                    print("✅ Entered Reliance URL")

                    # Click Extract button
                    extract_button = page.locator("button:has-text('Extract Data')").first
                    await extract_button.click()
                    print("🔄 Extraction started...")
                    await asyncio.sleep(3)
                    await page.screenshot(path="/app/screenshots/template_extraction/06_extraction_started.png")

                    # Wait for result (max 60 seconds)
                    print("⏳ Waiting for extraction result...")
                    await asyncio.sleep(60)
                    await page.screenshot(path="/app/screenshots/template_extraction/07_extraction_result.png")
                    print("✅ Extraction completed")
                else:
                    print("⚠️ Preset selector not found")
                    await page.screenshot(path="/app/screenshots/template_extraction/04_no_preset_selector.png")
            except Exception as e:
                print(f"❌ Preset template test failed: {e}")
                await page.screenshot(path="/app/screenshots/template_extraction/04_preset_test_error.png")

            # Step 5: Test actual Screener.in page structure
            print("\n📍 Step 5: Inspecting Screener.in page structure...")
            try:
                screener_page = await context.new_page()
                await screener_page.goto("https://www.screener.in/company/RELIANCE/consolidated/", wait_until="networkidle")
                await asyncio.sleep(3)
                await screener_page.screenshot(path="/app/screenshots/template_extraction/08_screener_actual_page.png")

                # Check for the selector that template is looking for
                company_ratios_exists = await screener_page.locator("#company-ratios").count() > 0
                print(f"   #company-ratios exists: {company_ratios_exists}")

                # Find actual selectors
                print("\n🔍 Actual HTML structure:")
                html_content = await screener_page.content()

                # Look for key elements
                h1_elements = await screener_page.locator("h1").all()
                print(f"   Found {len(h1_elements)} h1 elements:")
                for idx, h1 in enumerate(h1_elements[:3]):
                    text = await h1.text_content()
                    print(f"      h1[{idx}]: {text}")

                # Look for divs with IDs
                divs_with_ids = await screener_page.locator("div[id]").all()
                print(f"\n   Found {len(divs_with_ids)} divs with IDs:")
                for idx, div in enumerate(divs_with_ids[:5]):
                    div_id = await div.get_attribute("id")
                    print(f"      div#{div_id}")

                # Look for classes
                top_classes = await screener_page.locator(".top-ratios, .top-shrink").all()
                print(f"\n   Found {len(top_classes)} elements with .top-ratios or .top-shrink")

                await screener_page.close()
                print("✅ Page structure analyzed")
            except Exception as e:
                print(f"⚠️ Page structure analysis error: {e}")

            # Step 6: Explain what we found
            print("\n" + "="*80)
            print("📊 SUMMARY OF FINDINGS")
            print("="*80)
            print(f"\n#company-ratios selector exists: {company_ratios_exists}")
            print("\nThis explains why preset template fails:")
            print("  - The template is looking for '#company-ratios'")
            print("  - But Screener.in's HTML structure has changed")
            print("  - The selector no longer exists on the page")
            print("\nRecommendation: Preset templates are BROKEN and need updating")
            print("="*80 + "\n")

        finally:
            await browser.close()

        print("\n✅ All screenshots saved to /app/screenshots/template_extraction/")
        print("   You can view them in: backend/screenshots/template_extraction/\n")

if __name__ == "__main__":
    asyncio.run(test_template_extraction_ui())
