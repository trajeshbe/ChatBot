"""
Check for console errors preventing ExportWizardButton from rendering
"""
import time
import os
from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("FRONTEND_URL", "http://frontend:3000")
LOGIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
LOGIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")


console_messages = []
console_errors = []


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture console messages
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        try:
            # Login
            page.goto(f"{BASE_URL}/")
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            try:
                username_input = page.locator('input[type="text"], input[name="username"]').first
                username_input.fill(LOGIN_USERNAME, timeout=10000)

                password_input = page.locator('input[type="password"]').first
                password_input.fill(LOGIN_PASSWORD, timeout=10000)

                sign_in_button = page.get_by_role("button", name="Sign In")
                if not sign_in_button.is_visible():
                    sign_in_button = page.locator('button:has-text("Sign In")').first

                sign_in_button.click(timeout=10000)
                page.wait_for_load_state("networkidle")
                time.sleep(3)
            except Exception as e:
                print(f"Login: {e}")

            # Navigate to British Council
            try:
                page.get_by_text("Customer Solutions", exact=False).click(timeout=15000)
                time.sleep(2)
            except:
                pass

            try:
                page.get_by_text("British Council", exact=False).click(timeout=30000)
            except:
                try:
                    page.locator("text=/british|council/i").first.click(timeout=30000)
                except:
                    pass

            time.sleep(5)  # Wait for component to render

            print("\n" + "=" * 80)
            print("CONSOLE MESSAGES")
            print("=" * 80)
            for msg in console_messages:
                print(msg)

            print("\n" + "=" * 80)
            print("CONSOLE ERRORS")
            print("=" * 80)
            for err in console_errors:
                print(err)

            # Check if ExportWizardButton is in DOM at all
            print("\n" + "=" * 80)
            print("CHECKING FOR EXPORT WIZARD BUTTON IN DOM")
            print("=" * 80)

            # Try multiple selectors
            selectors = [
                'button:has-text("Export Module")',
                '[class*="Export"]',
                'div:has-text("Export Module")',
                '*[class*="export"]',
            ]

            for selector in selectors:
                elements = page.locator(selector).all()
                if elements:
                    print(f"\n✓ Found {len(elements)} elements matching: {selector}")
                    for elem in elements[:3]:
                        try:
                            print(f"  - {elem.text_content()[:100]}")
                        except:
                            pass
                else:
                    print(f"✗ No elements found for: {selector}")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
