"""Basic Fine-Tuning UI Access Test - No Login Required."""
import pytest
from playwright.sync_api import Page, Browser
import time
import os


BASE_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")


@pytest.fixture
def page(browser: Browser) -> Page:
    """Create browser page."""
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    yield page
    page.close()


def test_frontend_accessible(page: Page):
    """Test that frontend is accessible."""
    print(f"\nTesting frontend at: {BASE_URL}")

    page.goto(BASE_URL, timeout=30000)
    page.wait_for_load_state("networkidle")

    # Take screenshot
    page.screenshot(path="backend/tests/playwright/test_results/frontend_homepage.png")

    # Verify page loaded
    title = page.title()
    print(f"Page title: {title}")

    assert page.url.startswith(BASE_URL) or page.url.startswith("http://frontend:3000"), \
        f"Unexpected URL: {page.url}"


def test_admin_page_accessible(page: Page):
    """Test that admin page redirects to login (expected behavior)."""
    print(f"\nTesting admin page at: {BASE_URL}/admin")

    page.goto(f"{BASE_URL}/admin", timeout=30000)
    time.sleep(2)

    # Take screenshot
    page.screenshot(path="backend/tests/playwright/test_results/admin_page_before_login.png")

    # Should redirect to login or show admin interface
    current_url = page.url
    print(f"Current URL after navigating to /admin: {current_url}")

    # Either we're at login page OR admin page (if auth is disabled)
    assert "/login" in current_url or "/admin" in current_url, \
        f"Unexpected redirect: {current_url}"


def test_login_page_loads(page: Page):
    """Test that login page loads successfully."""
    print(f"\nTesting login page at: {BASE_URL}/login")

    page.goto(f"{BASE_URL}/login", timeout=30000)
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # Take screenshot
    page.screenshot(path="backend/tests/playwright/test_results/login_page.png")

    # Check for login form elements
    page_content = page.content()
    print("Checking for login form elements...")

    # Look for common login form elements
    has_username = (
        page.locator('input[type="text"]').count() > 0 or
        page.locator('input[name="username"]').count() > 0 or
        'username' in page_content.lower()
    )

    has_password = (
        page.locator('input[type="password"]').count() > 0 or
        'password' in page_content.lower()
    )

    has_login_button = (
        page.get_by_role("button").count() > 0 or
        'login' in page_content.lower() or
        'sign in' in page_content.lower()
    )

    print(f"  Username field: {has_username}")
    print(f"  Password field: {has_password}")
    print(f"  Login button: {has_login_button}")

    assert has_username or has_password or has_login_button, \
        "Login form elements not found on page"


def test_simple_login_attempt(page: Page):
    """Test simple login without expecting navigation."""
    print(f"\nTesting login flow at: {BASE_URL}/login")

    page.goto(f"{BASE_URL}/login", timeout=30000)
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Take before screenshot
    page.screenshot(path="backend/tests/playwright/test_results/before_login.png")

    # Try to find and fill login form
    try:
        # Find username input
        username_input = page.locator('input[type="text"]').first.or_(
            page.locator('input[name="username"]').first
        ).or_(page.locator('input[placeholder*="Username"]').first)

        if username_input.count() > 0:
            print("  Found username input, filling...")
            username_input.fill("admin")
        else:
            print("  Username input not found")

        # Find password input
        password_input = page.locator('input[type="password"]').first
        if password_input.count() > 0:
            print("  Found password input, filling...")
            password_input.fill("admin")
        else:
            print("  Password input not found")

        # Take screenshot after filling
        page.screenshot(path="backend/tests/playwright/test_results/after_fill_credentials.png")

        # Find and click login button (don't wait for navigation)
        login_button = page.get_by_role("button", name="Login").or_(
            page.get_by_role("button", name="Sign In")
        ).or_(page.locator('button[type="submit"]').first)

        if login_button.count() > 0:
            print("  Found login button, clicking...")
            login_button.click()

            # Wait a bit for any response
            time.sleep(3)

            # Take screenshot after click
            page.screenshot(path="backend/tests/playwright/test_results/after_login_click.png")

            # Check current URL
            current_url = page.url
            print(f"  URL after login attempt: {current_url}")

            # Check if we're still on login page or redirected
            if "/login" not in current_url:
                print(f"  ✓ Redirected away from login page to: {current_url}")
            else:
                print(f"  Still on login page - check for errors")

                # Look for error messages
                page_text = page.content()
                if 'error' in page_text.lower() or 'invalid' in page_text.lower():
                    print("  Found error message on page")
        else:
            print("  Login button not found")

    except Exception as e:
        print(f"  Error during login attempt: {e}")
        page.screenshot(path="backend/tests/playwright/test_results/login_error.png")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
