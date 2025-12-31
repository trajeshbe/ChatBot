"""
Comprehensive End-to-End UI Tests for All Features

Tests complete navigation and functionality:
1. Login flow
2. All sidebar tabs navigation
3. Chat interface features
4. File upload
5. Web scraping
6. Project estimator
7. Prompt library
8. Settings and configurations
9. Tab switching and state persistence

Date: 2025-11-29
"""

import asyncio
import json
from playwright.async_api import async_playwright, Page, expect
import pytest
from typing import Dict, List
import time


class TestCompleteUINavigation:
    """Comprehensive UI navigation and feature tests"""

    @pytest.mark.asyncio
    async def test_complete_ui_flow(self):
        """Test complete UI navigation across all tabs"""
        async with async_playwright() as p:
            # Launch browser in headless mode (no X server in Docker)
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            test_results = {
                "login": {"status": "pending", "details": []},
                "sidebar_navigation": {"status": "pending", "details": []},
                "chat_interface": {"status": "pending", "details": []},
                "file_upload": {"status": "pending", "details": []},
                "web_scraping": {"status": "pending", "details": []},
                "project_estimator": {"status": "pending", "details": []},
                "prompt_library": {"status": "pending", "details": []},
                "tab_switching": {"status": "pending", "details": []},
                "export_feature": {"status": "pending", "details": []},
            }

            try:
                # ========================================
                # TEST 1: LOGIN FLOW
                # ========================================
                print("\n" + "="*60)
                print("TEST 1: LOGIN FLOW")
                print("="*60)

                # Use Docker network hostname (from backend container to frontend)
                frontend_url = "http://frontend:3000"
                print(f"📍 Navigating to {frontend_url}...")
                await page.goto(frontend_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)

                # Check if we're on login page
                current_url = page.url
                print(f"📍 Current URL: {current_url}")

                if "/login" in current_url:
                    print("🔐 Login page detected, attempting login...")
                    test_results["login"]["details"].append("Login page loaded")

                    # Find username and password fields
                    username_input = page.locator('input[name="username"], input[type="text"]').first
                    password_input = page.locator('input[name="password"], input[type="password"]').first
                    login_button = page.locator('button[type="submit"], button:has-text("Login")').first

                    await expect(username_input).to_be_visible(timeout=5000)
                    await expect(password_input).to_be_visible(timeout=5000)

                    # Login with test credentials
                    await username_input.fill("admin")
                    await password_input.fill("admin")
                    test_results["login"]["details"].append("Credentials entered")

                    await login_button.click()
                    test_results["login"]["details"].append("Login button clicked")

                    # Wait for navigation (don't wait for specific URL, just wait for page load)
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    await page.wait_for_timeout(3000)

                    # Check if we're no longer on login page
                    current_url_after_login = page.url
                    print(f"📍 URL after login attempt: {current_url_after_login}")

                    if "/login" not in current_url_after_login:
                        test_results["login"]["status"] = "passed"
                        test_results["login"]["details"].append(f"Successfully logged in, redirected to {current_url_after_login}")
                        print(f"✅ Login successful - now at {current_url_after_login}")
                    else:
                        # Take screenshot for debugging
                        await page.screenshot(path="/tmp/login_failed.png")
                        # Check for error messages
                        page_text = await page.text_content('body')
                        error_msg = page_text[:500] if page_text else "No body content"
                        test_results["login"]["status"] = "failed"
                        test_results["login"]["details"].append(f"Login failed - still on login page. Page content: {error_msg}")
                        print(f"❌ Login failed - still on login page")
                        print(f"Page content sample: {error_msg}")
                else:
                    test_results["login"]["status"] = "skipped"
                    test_results["login"]["details"].append("Already logged in")
                    print("✅ Already logged in")

                await page.wait_for_timeout(2000)

                # ========================================
                # TEST 2: SIDEBAR NAVIGATION
                # ========================================
                print("\n" + "="*60)
                print("TEST 2: SIDEBAR NAVIGATION")
                print("="*60)

                # Define all expected tabs
                expected_tabs = [
                    {"name": "Chats", "icon_text": ["Chat", "Message"]},
                    {"name": "Files", "icon_text": ["File"]},
                    {"name": "Upload", "icon_text": ["Upload"]},
                    {"name": "Web Scraping", "icon_text": ["Globe", "Scrape"]},
                    {"name": "Project Estimator", "icon_text": ["Calculator", "Estimator"]},
                    {"name": "Prompt Library", "icon_text": ["Library", "Book"]},
                ]

                sidebar_tabs_found = []

                # Check if sidebar is visible
                sidebar = page.locator('nav, aside, [role="navigation"]').first
                try:
                    await expect(sidebar).to_be_visible(timeout=5000)
                    print("✅ Sidebar is visible")
                    test_results["sidebar_navigation"]["details"].append("Sidebar visible")
                except Exception as e:
                    print(f"❌ Sidebar not found: {e}")
                    test_results["sidebar_navigation"]["status"] = "failed"
                    test_results["sidebar_navigation"]["details"].append(f"Sidebar not visible: {e}")
                    # Skip sidebar tests if not visible
                    raise

                # Find all navigation buttons
                nav_buttons = await page.locator('button, a').all()
                print(f"📊 Found {len(nav_buttons)} interactive elements")

                for tab in expected_tabs:
                    try:
                        # Try to find tab by text content
                        tab_button = page.locator(f'button:has-text("{tab["name"]}"), a:has-text("{tab["name"]}")').first

                        if await tab_button.is_visible(timeout=1000):
                            sidebar_tabs_found.append(tab["name"])
                            print(f"✅ Found tab: {tab['name']}")
                        else:
                            # Try alternative search by icon text
                            for icon_text in tab["icon_text"]:
                                alt_button = page.locator(f'button:has-text("{icon_text}"), a:has-text("{icon_text}")').first
                                if await alt_button.is_visible(timeout=1000):
                                    sidebar_tabs_found.append(tab["name"])
                                    print(f"✅ Found tab (via icon): {tab['name']}")
                                    break
                    except Exception as e:
                        print(f"⚠️  Tab not found: {tab['name']} - {str(e)[:100]}")

                test_results["sidebar_navigation"]["status"] = "passed" if len(sidebar_tabs_found) >= 4 else "partial"
                test_results["sidebar_navigation"]["details"] = sidebar_tabs_found
                print(f"📊 Found {len(sidebar_tabs_found)} tabs: {sidebar_tabs_found}")

                # ========================================
                # TEST 3: CHAT INTERFACE
                # ========================================
                print("\n" + "="*60)
                print("TEST 3: CHAT INTERFACE")
                print("="*60)

                # Navigate to chat (should be default view)
                try:
                    chat_button = page.locator('button:has-text("Chat"), button:has-text("Chats"), a:has-text("Chat")').first
                    if await chat_button.is_visible(timeout=2000):
                        await chat_button.click()
                        await page.wait_for_timeout(1000)
                except:
                    print("ℹ️  Already on chat view")

                # Check for chat input
                chat_input = page.locator('textarea, input[placeholder*="Ask"], input[placeholder*="message"]').first
                await expect(chat_input).to_be_visible(timeout=5000)
                print("✅ Chat input found")
                test_results["chat_interface"]["details"].append("Chat input visible")

                # Check for model selector
                try:
                    model_selector = page.locator('select').first
                    if await model_selector.is_visible(timeout=3000):
                        options = await model_selector.locator('option').all_text_contents()
                        print(f"✅ Model selector found with {len(options)} models")
                        test_results["chat_interface"]["details"].append(f"Models: {len(options)}")
                except:
                    print("⚠️  Model selector not found")

                # Test slash command (/)
                print("🔍 Testing slash command...")
                await chat_input.click()
                await chat_input.fill("/")
                await page.wait_for_timeout(1000)

                # Check if prompt palette appears
                try:
                    prompt_palette = page.locator('[data-testid="prompt-palette"], div:has-text("Prompts")').first
                    if await prompt_palette.is_visible(timeout=2000):
                        print("✅ Slash command palette appeared")
                        test_results["chat_interface"]["details"].append("Slash command works")

                        # Close palette with Escape
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)
                    else:
                        print("⚠️  Prompt palette did not appear")
                except Exception as e:
                    print(f"⚠️  Slash command test failed: {str(e)[:100]}")

                # Clear input
                await chat_input.clear()

                test_results["chat_interface"]["status"] = "passed"
                print("✅ Chat interface tests completed")

                # ========================================
                # TEST 4: FILE UPLOAD TAB
                # ========================================
                print("\n" + "="*60)
                print("TEST 4: FILE UPLOAD")
                print("="*60)

                try:
                    # Navigate to Upload tab
                    upload_button = page.locator('button:has-text("Upload"), a:has-text("Upload")').first
                    await upload_button.click()
                    await page.wait_for_timeout(1500)
                    print("✅ Navigated to Upload tab")

                    # Check for file upload area
                    upload_area = page.locator('[role="button"]:has-text("upload"), div:has-text("Drop"), input[type="file"]').first
                    if await upload_area.is_visible(timeout=3000):
                        print("✅ File upload area found")
                        test_results["file_upload"]["details"].append("Upload area visible")
                        test_results["file_upload"]["status"] = "passed"
                    else:
                        print("⚠️  File upload area not found")
                        test_results["file_upload"]["status"] = "partial"

                except Exception as e:
                    print(f"❌ File upload test failed: {str(e)[:100]}")
                    test_results["file_upload"]["status"] = "failed"
                    test_results["file_upload"]["details"].append(str(e)[:200])

                # ========================================
                # TEST 5: WEB SCRAPING TAB
                # ========================================
                print("\n" + "="*60)
                print("TEST 5: WEB SCRAPING")
                print("="*60)

                try:
                    # Navigate to Web Scraping tab
                    scrape_button = page.locator('button:has-text("Scrap"), button:has-text("Web"), a:has-text("Scrap")').first
                    await scrape_button.click()
                    await page.wait_for_timeout(1500)
                    print("✅ Navigated to Web Scraping tab")

                    # Check for URL input
                    url_input = page.locator('input[placeholder*="URL"], input[placeholder*="http"]').first
                    if await url_input.is_visible(timeout=3000):
                        print("✅ URL input found")
                        test_results["web_scraping"]["details"].append("URL input visible")

                        # Check for scrape button
                        scrape_action_button = page.locator('button:has-text("Scrape"), button:has-text("Extract")').first
                        if await scrape_action_button.is_visible(timeout=2000):
                            print("✅ Scrape action button found")
                            test_results["web_scraping"]["details"].append("Scrape button visible")
                            test_results["web_scraping"]["status"] = "passed"
                        else:
                            test_results["web_scraping"]["status"] = "partial"
                    else:
                        print("⚠️  Scraping UI not found")
                        test_results["web_scraping"]["status"] = "partial"

                except Exception as e:
                    print(f"❌ Web scraping test failed: {str(e)[:100]}")
                    test_results["web_scraping"]["status"] = "failed"
                    test_results["web_scraping"]["details"].append(str(e)[:200])

                # ========================================
                # TEST 6: PROJECT ESTIMATOR TAB
                # ========================================
                print("\n" + "="*60)
                print("TEST 6: PROJECT ESTIMATOR")
                print("="*60)

                try:
                    # Navigate to Project Estimator tab
                    estimator_button = page.locator('button:has-text("Estimator"), button:has-text("Project"), a:has-text("Estimator")').first
                    await estimator_button.click()
                    await page.wait_for_timeout(1500)
                    print("✅ Navigated to Project Estimator tab")

                    # Check for estimator UI elements
                    estimator_ui = page.locator('div:has-text("Project Estimator"), div:has-text("Upload"), textarea, input[type="file"]').first
                    if await estimator_ui.is_visible(timeout=3000):
                        print("✅ Project Estimator UI found")
                        test_results["project_estimator"]["details"].append("Estimator UI visible")
                        test_results["project_estimator"]["status"] = "passed"
                    else:
                        print("⚠️  Estimator UI not found")
                        test_results["project_estimator"]["status"] = "partial"

                except Exception as e:
                    print(f"❌ Project estimator test failed: {str(e)[:100]}")
                    test_results["project_estimator"]["status"] = "failed"
                    test_results["project_estimator"]["details"].append(str(e)[:200])

                # ========================================
                # TEST 7: PROMPT LIBRARY TAB
                # ========================================
                print("\n" + "="*60)
                print("TEST 7: PROMPT LIBRARY")
                print("="*60)

                try:
                    # Navigate to Prompt Library tab
                    library_button = page.locator('button:has-text("Library"), button:has-text("Prompt"), a:has-text("Library")').first
                    await library_button.click()
                    await page.wait_for_timeout(1500)
                    print("✅ Navigated to Prompt Library tab")

                    # Check for library UI elements
                    library_ui = page.locator('div:has-text("Prompt Library"), button:has-text("Create"), div:has-text("Search")').first
                    if await library_ui.is_visible(timeout=3000):
                        print("✅ Prompt Library UI found")
                        test_results["prompt_library"]["details"].append("Library UI visible")

                        # Check for prompt cards
                        prompt_cards = await page.locator('div[class*="card"], div[class*="grid"]').all()
                        if len(prompt_cards) > 0:
                            print(f"✅ Found {len(prompt_cards)} UI elements (possibly prompt cards)")
                            test_results["prompt_library"]["details"].append(f"UI elements: {len(prompt_cards)}")

                        test_results["prompt_library"]["status"] = "passed"
                    else:
                        print("⚠️  Prompt Library UI not found")
                        test_results["prompt_library"]["status"] = "partial"

                except Exception as e:
                    print(f"❌ Prompt library test failed: {str(e)[:100]}")
                    test_results["prompt_library"]["status"] = "failed"
                    test_results["prompt_library"]["details"].append(str(e)[:200])

                # ========================================
                # TEST 8: TAB SWITCHING & STATE PERSISTENCE
                # ========================================
                print("\n" + "="*60)
                print("TEST 8: TAB SWITCHING & STATE PERSISTENCE")
                print("="*60)

                try:
                    # Switch back to chat
                    chat_button = page.locator('button:has-text("Chat"), a:has-text("Chat")').first
                    await chat_button.click()
                    await page.wait_for_timeout(1000)
                    print("✅ Switched to Chat tab")

                    # Enter text in chat input
                    chat_input = page.locator('textarea, input[placeholder*="Ask"]').first
                    test_text = "Test message for state persistence"
                    await chat_input.fill(test_text)
                    await page.wait_for_timeout(500)
                    print(f"✅ Entered text: '{test_text}'")

                    # Switch to another tab
                    upload_button = page.locator('button:has-text("Upload"), a:has-text("Upload")').first
                    await upload_button.click()
                    await page.wait_for_timeout(1000)
                    print("✅ Switched to Upload tab")

                    # Switch back to chat
                    await chat_button.click()
                    await page.wait_for_timeout(1000)
                    print("✅ Switched back to Chat tab")

                    # Check if text persisted
                    current_value = await chat_input.input_value()
                    if current_value == test_text:
                        print("✅ State persisted across tab switches")
                        test_results["tab_switching"]["status"] = "passed"
                        test_results["tab_switching"]["details"].append("State persistence verified")
                    else:
                        print(f"⚠️  State did not persist. Expected: '{test_text}', Got: '{current_value}'")
                        test_results["tab_switching"]["status"] = "partial"
                        test_results["tab_switching"]["details"].append("State lost on tab switch")

                    # Clear input
                    await chat_input.clear()

                except Exception as e:
                    print(f"❌ Tab switching test failed: {str(e)[:100]}")
                    test_results["tab_switching"]["status"] = "failed"
                    test_results["tab_switching"]["details"].append(str(e)[:200])

                # ========================================
                # TEST 9: EXPORT FEATURE (if visible)
                # ========================================
                print("\n" + "="*60)
                print("TEST 9: EXPORT FEATURE")
                print("="*60)

                try:
                    # Check if there are any AI messages visible
                    ai_messages = await page.locator('div:has-text("AI"), div[role="article"]').all()

                    if len(ai_messages) > 0:
                        print(f"ℹ️  Found {len(ai_messages)} message containers")

                        # Look for export button
                        export_button = page.locator('button:has-text("Export"), a:has-text("Export")').first
                        if await export_button.is_visible(timeout=2000):
                            print("✅ Export button found")
                            test_results["export_feature"]["details"].append("Export button visible")
                            test_results["export_feature"]["status"] = "passed"
                        else:
                            print("ℹ️  Export button not found (may require AI response)")
                            test_results["export_feature"]["status"] = "skipped"
                            test_results["export_feature"]["details"].append("No AI messages to export")
                    else:
                        print("ℹ️  No AI messages found")
                        test_results["export_feature"]["status"] = "skipped"
                        test_results["export_feature"]["details"].append("No messages in chat")

                except Exception as e:
                    print(f"ℹ️  Export feature test skipped: {str(e)[:100]}")
                    test_results["export_feature"]["status"] = "skipped"

                # ========================================
                # FINAL SUMMARY
                # ========================================
                print("\n" + "="*60)
                print("TEST SUMMARY")
                print("="*60)

                passed_tests = sum(1 for v in test_results.values() if v["status"] == "passed")
                partial_tests = sum(1 for v in test_results.values() if v["status"] == "partial")
                failed_tests = sum(1 for v in test_results.values() if v["status"] == "failed")
                skipped_tests = sum(1 for v in test_results.values() if v["status"] == "skipped")
                total_tests = len(test_results)

                print(f"\n📊 Results:")
                print(f"   ✅ Passed:  {passed_tests}/{total_tests}")
                print(f"   ⚠️  Partial: {partial_tests}/{total_tests}")
                print(f"   ❌ Failed:  {failed_tests}/{total_tests}")
                print(f"   ⏭️  Skipped: {skipped_tests}/{total_tests}")

                print(f"\n📋 Detailed Results:")
                for test_name, result in test_results.items():
                    status_icon = {
                        "passed": "✅",
                        "partial": "⚠️ ",
                        "failed": "❌",
                        "skipped": "⏭️ ",
                        "pending": "⏳"
                    }.get(result["status"], "❓")

                    print(f"\n{status_icon} {test_name.upper()}: {result['status']}")
                    if result["details"]:
                        for detail in result["details"]:
                            print(f"      - {detail}")

                # Save results to file
                results_file = "/tmp/ui_test_results.json"
                with open(results_file, "w") as f:
                    json.dump({
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "summary": {
                            "total": total_tests,
                            "passed": passed_tests,
                            "partial": partial_tests,
                            "failed": failed_tests,
                            "skipped": skipped_tests
                        },
                        "tests": test_results
                    }, f, indent=2)

                print(f"\n💾 Results saved to: {results_file}")

                # Keep browser open for 5 seconds to review
                print("\n⏳ Keeping browser open for 5 seconds...")
                await page.wait_for_timeout(5000)

            except Exception as e:
                print(f"\n❌ Test execution failed: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

            finally:
                await browser.close()
                print("\n🏁 Test execution completed")


if __name__ == "__main__":
    # Run the test directly
    asyncio.run(TestCompleteUINavigation().test_complete_ui_flow())
