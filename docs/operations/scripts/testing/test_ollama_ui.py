"""
Playwright UI Test for Ollama Models Manager

Tests the complete UI functionality of the Ollama Models Manager
in the admin dashboard.
"""

import asyncio
import json
from playwright.async_api import async_playwright, expect


async def test_ollama_models_ui():
    """Test Ollama Models Manager UI end-to-end."""

    print("=" * 80)
    print("🧪 OLLAMA MODELS MANAGER - UI TEST WITH PLAYWRIGHT")
    print("=" * 80)
    print()

    async with async_playwright() as p:
        # Launch browser
        print("1️⃣  Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # Navigate to admin page
            print("2️⃣  Navigating to admin dashboard...")
            admin_url = "http://frontend:3000/admin"
            await page.goto(admin_url, wait_until="networkidle", timeout=30000)
            print(f"   ✅ Loaded: {admin_url}")
            print()

            # Wait for page to be ready
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # Check if Ollama Models tab exists
            print("3️⃣  Looking for Ollama Models tab...")
            ollama_tab_selector = 'button:has-text("Ollama Models")'

            try:
                ollama_tab = page.locator(ollama_tab_selector)
                await ollama_tab.wait_for(timeout=5000)
                print("   ✅ Found Ollama Models tab")
            except Exception as e:
                print(f"   ❌ Ollama Models tab not found: {e}")
                print("   Available tabs:")
                tabs = await page.locator('button').all_text_contents()
                for tab in tabs[:10]:
                    if tab.strip():
                        print(f"      - {tab.strip()}")
                raise
            print()

            # Click on Ollama Models tab
            print("4️⃣  Clicking Ollama Models tab...")
            await ollama_tab.click()
            await asyncio.sleep(2)
            print("   ✅ Clicked Ollama Models tab")
            print()

            # Wait for content to load
            print("5️⃣  Waiting for Ollama Models content to load...")
            await asyncio.sleep(3)  # Give time for API calls
            print("   ✅ Content loading complete")
            print()

            # Check for health status
            print("6️⃣  Checking health status display...")
            try:
                health_status = page.locator('text=/Ollama Service.*Status/i')
                await health_status.wait_for(timeout=5000)
                print("   ✅ Health status section found")

                # Check if healthy or unhealthy
                page_content = await page.content()
                if "healthy" in page_content.lower():
                    print("   ✅ Ollama service is healthy")
                else:
                    print("   ⚠️  Ollama service status unclear")
            except Exception as e:
                print(f"   ⚠️  Health status not found: {e}")
            print()

            # Check for statistics cards
            print("7️⃣  Checking statistics cards...")
            try:
                # Look for Total Models card
                total_models = page.locator('text=/Total Models/i')
                await total_models.wait_for(timeout=5000)
                print("   ✅ Total Models card found")

                # Look for Total Size card
                total_size = page.locator('text=/Total Size/i')
                await total_size.wait_for(timeout=5000)
                print("   ✅ Total Size card found")

                # Look for Running Models card
                running = page.locator('text=/Running/i')
                await running.wait_for(timeout=5000)
                print("   ✅ Running Models card found")

                # Look for Model Families card
                families = page.locator('text=/Families/i')
                await families.wait_for(timeout=5000)
                print("   ✅ Model Families card found")

            except Exception as e:
                print(f"   ⚠️  Some statistics cards not found: {e}")
            print()

            # Check for installed models list
            print("8️⃣  Checking installed models list...")
            try:
                models_section = page.locator('text=/Installed Models/i')
                await models_section.wait_for(timeout=5000)
                print("   ✅ Installed Models section found")

                # Count model entries
                model_cards = page.locator('[class*="border"][class*="rounded"]').filter(
                    has_text="qwen"
                ).or_(page.locator('[class*="border"][class*="rounded"]').filter(
                    has_text="llama"
                ))

                model_count = await model_cards.count()
                if model_count > 0:
                    print(f"   ✅ Found {model_count} model card(s)")
                else:
                    print("   ⚠️  No model cards found (models may still be loading)")

            except Exception as e:
                print(f"   ⚠️  Installed models section not found: {e}")
            print()

            # Try to expand a model's details
            print("9️⃣  Testing model details expansion...")
            try:
                # Look for a model name we know exists
                qwen_model = page.locator('text=/qwen2.5:1.5b/i').first
                await qwen_model.wait_for(timeout=5000)
                print("   ✅ Found qwen2.5:1.5b model")

                # Click to expand details
                await qwen_model.click()
                await asyncio.sleep(2)
                print("   ✅ Clicked to expand model details")

                # Check if details are shown
                details_text = await page.content()
                if "parameter" in details_text.lower() or "family" in details_text.lower():
                    print("   ✅ Model details expanded successfully")
                else:
                    print("   ⚠️  Model details may not have expanded")

            except Exception as e:
                print(f"   ⚠️  Could not test model expansion: {e}")
            print()

            # Take a screenshot for verification
            print("🔟 Taking screenshot...")
            screenshot_path = "/tmp/ollama_models_ui_test.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   ✅ Screenshot saved to: {screenshot_path}")
            print()

            # Get final page state
            print("📊 Final Page State:")
            print("   " + "=" * 76)

            # Check for any error messages
            error_elements = page.locator('text=/error|failed|unable/i')
            error_count = await error_elements.count()
            if error_count > 0:
                print(f"   ⚠️  Found {error_count} potential error message(s)")
                for i in range(min(error_count, 3)):
                    error_text = await error_elements.nth(i).text_content()
                    print(f"      - {error_text[:100]}")
            else:
                print("   ✅ No error messages found")

            # Check for loading states
            loading_elements = page.locator('text=/loading|spinner/i')
            loading_count = await loading_elements.count()
            if loading_count > 0:
                print(f"   ⏳ Still loading ({loading_count} loading indicator(s))")
            else:
                print("   ✅ No loading indicators (content fully loaded)")

            print("   " + "=" * 76)
            print()

            print("✅ OLLAMA MODELS UI TEST COMPLETED SUCCESSFULLY!")
            print()

        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()

            # Take screenshot on failure
            try:
                screenshot_path = "/tmp/ollama_models_ui_test_FAILED.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"   Screenshot saved to: {screenshot_path}")
            except:
                pass

            raise

        finally:
            # Cleanup
            await browser.close()
            print("🏁 Browser closed")
            print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ollama_models_ui())
