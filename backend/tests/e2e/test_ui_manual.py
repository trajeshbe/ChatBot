"""
Manual UI Test Script - No Login Required
Tests public-facing features that don't need authentication

Date: 2025-11-29
"""

import asyncio
import json
from playwright.async_api import async_playwright
from typing import Dict, List


async def test_ui_features():
    """Test UI features without authentication"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        test_results = {
            "page_load": {"status": "pending", "details": []},
            "login_page": {"status": "pending", "details": []},
            "ui_elements": {"status": "pending", "details": []},
        }

        try:
            print("\n" + "="*80)
            print("PLAYWRIGHT UI TEST - Manual Inspection")
            print("="*80)

            # Navigate to frontend
            frontend_url = "http://frontend:3000"
            print(f"\n📍 Navigating to {frontend_url}...")
            await page.goto(frontend_url, wait_until="networkidle", timeout=30000)
            test_results["page_load"]["status"] = "passed"
            test_results["page_load"]["details"].append("Page loaded successfully")

            await page.wait_for_timeout(2000)

            # Get current URL and title
            current_url = page.url
            title = await page.title()
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page Title: {title}")

            test_results["login_page"]["details"].append(f"URL: {current_url}")
            test_results["login_page"]["details"].append(f"Title: {title}")

            # Take screenshot of current page
            await page.screenshot(path="/tmp/ui_test_page.png", full_page=True)
            print("📸 Screenshot saved to /tmp/ui_test_page.png")

            # Get page HTML for inspection
            html_content = await page.content()
            with open("/tmp/ui_test_page.html", "w") as f:
                f.write(html_content)
            print("💾 HTML saved to /tmp/ui_test_page.html")

            # Check what elements are visible
            print("\n🔍 Checking visible elements...")

            # Check for login form elements
            has_username = await page.locator('input[name="username"], input[type="text"]').count()
            has_password = await page.locator('input[name="password"], input[type="password"]').count()
            has_submit = await page.locator('button[type="submit"]').count()

            print(f"  - Username input fields: {has_username}")
            print(f"  - Password input fields: {has_password}")
            print(f"  - Submit buttons: {has_submit}")

            test_results["ui_elements"]["details"].append(f"Username inputs: {has_username}")
            test_results["ui_elements"]["details"].append(f"Password inputs: {has_password}")
            test_results["ui_elements"]["details"].append(f"Submit buttons: {has_submit}")

            if has_username > 0 and has_password > 0 and has_submit > 0:
                test_results["login_page"]["status"] = "passed"
                test_results["login_page"]["details"].append("Login form found")
                test_results["ui_elements"]["status"] = "passed"
                print("\n✅ Login page detected with all required elements")

                # Try to fill and see what happens
                print("\n🔐 Attempting login...")
                username_input = page.locator('input[name="username"], input[type="text"]').first
                password_input = page.locator('input[name="password"], input[type="password"]').first
                login_button = page.locator('button[type="submit"]').first

                await username_input.fill("admin")
                await password_input.fill("admin")
                print("  - Credentials entered")

                # Take screenshot before clicking
                await page.screenshot(path="/tmp/ui_test_before_login.png", full_page=True)
                print("📸 Screenshot before login saved")

                await login_button.click()
                print("  - Login button clicked")

                # Wait for response
                await page.wait_for_timeout(5000)

                # Take screenshot after click
                await page.screenshot(path="/tmp/ui_test_after_login.png", full_page=True)
                print("📸 Screenshot after login saved")

                # Check URL change
                new_url = page.url
                print(f"📍 URL after login: {new_url}")

                if "/login" not in new_url:
                    print("✅ Login successful - redirected away from login page")
                    test_results["login_page"]["details"].append("Login successful")

                    # Check for sidebar
                    sidebar_count = await page.locator('nav, aside, [role="navigation"]').count()
                    print(f"\n🔍 Sidebar elements found: {sidebar_count}")

                    if sidebar_count > 0:
                        print("✅ Sidebar found after login")
                    else:
                        print("❌ No sidebar found after login")
                        # Get page content
                        page_text = await page.text_content('body')
                        print(f"Page content sample: {page_text[:500]}")
                else:
                    print("❌ Login failed - still on login page")
                    # Check for error messages
                    error_elements = await page.locator('[class*="error"], [class*="alert"], .text-red-500').all()
                    print(f"  - Error elements found: {len(error_elements)}")
                    if len(error_elements) > 0:
                        for i, elem in enumerate(error_elements[:3]):
                            text = await elem.text_content()
                            print(f"    Error {i+1}: {text}")
            else:
                test_results["login_page"]["status"] = "failed"
                test_results["ui_elements"]["status"] = "failed"
                print("\n❌ Login form not found or incomplete")

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Save results
            with open("/tmp/ui_test_results.json", "w") as f:
                json.dump(test_results, f, indent=2)
            print("\n📄 Results saved to /tmp/ui_test_results.json")

            await browser.close()
            print("\n🏁 Test completed")


if __name__ == "__main__":
    asyncio.run(test_ui_features())
