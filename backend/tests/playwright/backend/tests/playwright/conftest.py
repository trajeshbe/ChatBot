"""Pytest configuration for Playwright E2E tests."""
import pytest
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import os
import time


# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
SCREENSHOT_ON_FAILURE = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the entire test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Create a new browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def logged_in_admin_page(context: BrowserContext):
    """
    Create a logged-in admin page for tests requiring authentication.

    This fixture:
    1. Creates a new page
    2. Navigates to frontend
    3. Checks if login is needed
    4. Logs in if necessary
    5. Returns the authenticated page
    """
    page = context.new_page()

    # Navigate to frontend
    page.goto(FRONTEND_URL, timeout=30000, wait_until="domcontentloaded")
    time.sleep(2)

    # Check if we're already logged in (by checking URL or looking for user menu)
    if not page.is_visible('button:has-text("Logout")'):
        # Look for login form (check for username or email input)
        if page.is_visible('#username') or page.is_visible('input[type="email"]'):
            # Fill login form
            try:
                # Fill username/email field
                if page.is_visible('#username'):
                    page.fill('#username', os.getenv("TEST_ADMIN_USERNAME", "admin"))
                elif page.is_visible('input[type="email"]'):
                    page.fill('input[type="email"]', os.getenv("TEST_ADMIN_EMAIL", "admin@example.com"))

                # Fill password field - default is "admin" not "admin123"
                page.fill('#password', os.getenv("TEST_ADMIN_PASSWORD", "admin"))

                # Click login button - don't wait for navigation as it might be SPA
                page.click('button[type="submit"]')

                # Wait for login to complete (less strict)
                time.sleep(5)  # Increased from 3 to 5 seconds

            except Exception as e:
                print(f"Login attempt failed: {e}")
                # Continue anyway - tests will fail if login was actually required

    yield page
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results and take screenshots on failure.
    """
    outcome = yield
    rep = outcome.get_result()

    if SCREENSHOT_ON_FAILURE and rep.when == "call" and rep.failed:
        # Get the page fixture if it exists
        page = None
        if "page" in item.funcargs:
            page = item.funcargs["page"]
        elif "logged_in_admin_page" in item.funcargs:
            page = item.funcargs["logged_in_admin_page"]
        elif "export_wizard_page" in item.funcargs:
            # export_wizard_page is a page object, get the underlying page
            export_wizard_page = item.funcargs["export_wizard_page"]
            if hasattr(export_wizard_page, "page"):
                page = export_wizard_page.page

        if page:
            # Take screenshot
            screenshot_dir = "test_results"
            os.makedirs(screenshot_dir, exist_ok=True)

            test_name = item.nodeid.replace("::", "_").replace("/", "_")
            screenshot_path = os.path.join(screenshot_dir, f"FAILED_{test_name}.png")

            try:
                page.screenshot(path=screenshot_path)
                print(f"\n📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"\n❌ Failed to capture screenshot: {e}")


# Pytest markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running (export completion, etc.)"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test (existing functionality)"
    )
    config.addinivalue_line(
        "markers", "new: mark test as testing new functionality"
    )
