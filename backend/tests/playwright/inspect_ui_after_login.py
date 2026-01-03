#!/usr/bin/env python3
"""
UI Inspection After Login - Identify module selectors post-authentication
"""
from playwright.sync_api import sync_playwright
import time

def inspect_ui_after_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("=" * 80)
        print("POST-LOGIN UI INSPECTION - Module Selectors")
        print("=" * 80)
        print()

        # Navigate and login
        print("[1] Navigating to http://frontend:3000 and logging in...")
        page.goto('http://frontend:3000', wait_until='networkidle', timeout=60000)
        time.sleep(2)

        # Perform login
        try:
            username_input = page.locator('input[type="text"]').first
            username_input.fill("admin", timeout=10000)

            password_input = page.locator('input[type="password"]').first
            password_input.fill("admin", timeout=10000)

            sign_in_button = page.get_by_role("button", name="Sign In")
            sign_in_button.click(timeout=10000)

            # Wait for navigation after login
            page.wait_for_load_state("networkidle")
            time.sleep(5)
            print("✓ Login successful")
        except Exception as e:
            print(f"✗ Login failed: {e}")
            browser.close()
            return

        print()

        # Take screenshot after login
        screenshot_path = '/app/tests/playwright/test_results/ui_after_login.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"✓ Screenshot saved: {screenshot_path}")
        print()

        # Get visible text after login
        print("[2] Extracting visible text after login...")
        body_text = page.inner_text('body')
        print("First 3000 characters of visible text:")
        print("-" * 80)
        print(body_text[:3000])
        print("-" * 80)
        print()

        # Save full HTML
        html_content = page.content()
        with open('/app/tests/playwright/test_results/ui_after_login.html', 'w') as f:
            f.write(html_content)
        print(f"✓ HTML saved: /app/tests/playwright/test_results/ui_after_login.html")
        print()

        # Search for module-specific patterns
        print("[3] Searching for module elements...")

        # Look for all clickable elements
        clickable_elements = page.locator('button, a, [role="button"], [onclick], div[class*="card"]').all()
        print(f"Found {len(clickable_elements)} potentially clickable elements")

        # Print first 20 with text content
        for i, elem in enumerate(clickable_elements[:20]):
            try:
                text = elem.inner_text()
                if text and text.strip():
                    print(f"   [{i+1}] {text[:100]}")
            except:
                pass

        print()
        print("[4] Searching for tier2/tier3 module keywords...")
        keywords = [
            "talent", "taxonomy", "planning", "procurement", "matcher",
            "analytics", "construction", "hr", "vertical", "module",
            "customer-churn", "financial-anomaly", "estimator", "mine-scope"
        ]

        for keyword in keywords:
            count = page.locator(f"text=/{keyword}/i").count()
            if count > 0:
                print(f"✓ Found '{keyword}' in {count} elements")

        print()
        print("=" * 80)
        print("POST-LOGIN UI INSPECTION COMPLETE")
        print("=" * 80)

        browser.close()

if __name__ == "__main__":
    inspect_ui_after_login()
