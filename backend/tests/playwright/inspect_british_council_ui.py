"""
Inspect British Council UI to see what buttons are present
"""
import time
import os
from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("FRONTEND_URL", "http://frontend:3000")
LOGIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
LOGIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")


def perform_login(page):
    """Perform login to access the application."""
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Check if already logged in
    try:
        if page.locator('text=/module|vertical|dashboard/i').count() > 0:
            return
    except:
        pass

    # Perform login
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
        print(f"Login failed or not required: {e}")


def navigate_to_british_council(page):
    """Navigate to British Council module."""
    perform_login(page)

    # Click on "Customer Solutions" to access tier 3 modules
    try:
        page.get_by_text("Customer Solutions", exact=False).click(timeout=15000)
        time.sleep(2)
    except Exception as e:
        print(f"Could not click Customer Solutions: {e}")
        try:
            page.get_by_text("POC", exact=False).click(timeout=15000)
            time.sleep(2)
        except:
            pass

    # Click on British Council module
    try:
        page.get_by_text("british", exact=False).click(timeout=30000)
    except:
        try:
            page.get_by_text("British Council", exact=False).click(timeout=30000)
        except:
            page.locator("text=/british|council/i").first.click(timeout=30000)

    time.sleep(2)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to British Council
            navigate_to_british_council(page)

            print("\n" + "=" * 80)
            print("BRITISH COUNCIL MODULE - UI INSPECTION")
            print("=" * 80 + "\n")

            # Check for all buttons
            all_buttons = page.locator('button').all()
            print(f"Total buttons found: {len(all_buttons)}\n")

            for i, button in enumerate(all_buttons, 1):
                try:
                    text = button.text_content()
                    title = button.get_attribute('title')
                    class_name = button.get_attribute('class')
                    is_visible = button.is_visible()

                    if text or title:
                        print(f"Button {i}:")
                        if text:
                            print(f"  Text: {text[:100]}")
                        if title:
                            print(f"  Title: {title}")
                        print(f"  Visible: {is_visible}")
                        if "export" in text.lower() or (title and "export" in title.lower()):
                            print(f"  ⭐ EXPORT BUTTON FOUND!")
                            print(f"  Class: {class_name}")
                        print()
                except Exception as e:
                    pass

            # Check for Export-related elements
            print("\n" + "=" * 80)
            print("SEARCHING FOR EXPORT-RELATED ELEMENTS")
            print("=" * 80 + "\n")

            export_patterns = [
                'button:has-text("Export")',
                'button:has-text("export")',
                '[title*="Export"]',
                '[title*="export"]',
                'text=/export/i',
                '*:has-text("Export")',
            ]

            for pattern in export_patterns:
                elements = page.locator(pattern).all()
                if elements:
                    print(f"Pattern '{pattern}': {len(elements)} matches")
                    for elem in elements:
                        try:
                            if elem.is_visible():
                                print(f"  - Visible: {elem.text_content()[:100]}")
                        except:
                            pass

            # Save HTML for inspection
            html_content = page.content()
            with open('/app/tests/playwright/test_results/british_council_page.html', 'w') as f:
                f.write(html_content)
            print("\n✅ HTML saved to: /app/tests/playwright/test_results/british_council_page.html")

            # Take screenshot
            page.screenshot(path='/app/tests/playwright/test_results/british_council_ui.png', full_page=True)
            print("✅ Screenshot saved to: /app/tests/playwright/test_results/british_council_ui.png")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
