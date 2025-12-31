"""Playwright test fixtures and configuration."""
import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from page_objects.login_page import LoginPage
from page_objects.admin_dashboard_page import AdminDashboardPage
import os


# Configuration
BASE_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))  # Slow down by N ms
SCREENSHOT_ON_FAILURE = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"


@pytest.fixture(scope="session")
def playwright_instance():
    """Create Playwright instance for the session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Create browser instance for the session."""
    browser = playwright_instance.chromium.launch(
        headless=HEADLESS,
        slow_mo=SLOW_MO
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser):
    """Create a new browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def logged_in_admin_page(page):
    """Create a page with admin already logged in."""
    login_page = LoginPage(page, BASE_URL)
    login_page.navigate()
    login_page.login(ADMIN_USERNAME, ADMIN_PASSWORD)

    # Verify login successful
    assert login_page.is_logged_in(), "Admin login failed"

    yield page


@pytest.fixture(scope="function")
def admin_dashboard(logged_in_admin_page):
    """Create admin dashboard page object with logged in admin."""
    dashboard = AdminDashboardPage(logged_in_admin_page, BASE_URL)
    dashboard.navigate_to_admin()
    return dashboard


@pytest.fixture(scope="function")
def login_page_object(page):
    """Create login page object."""
    return LoginPage(page, BASE_URL)


@pytest.fixture(scope="function")
def admin_dashboard_object(page):
    """Create admin dashboard page object (without login)."""
    return AdminDashboardPage(page, BASE_URL)


# Hooks for test reporting and screenshots
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results and take screenshots on failure."""
    outcome = yield
    rep = outcome.get_result()

    # Take screenshot on failure if enabled
    if rep.when == "call" and rep.failed and SCREENSHOT_ON_FAILURE:
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            test_name = item.name
            screenshot_path = f"backend/tests/playwright/test_results/FAILED_{test_name}.png"
            try:
                page.screenshot(path=screenshot_path)
                print(f"\nScreenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"\nFailed to take screenshot: {e}")


# Helper function for test data cleanup
@pytest.fixture(scope="function")
def cleanup_test_user(admin_dashboard):
    """Fixture to clean up test users after test."""
    created_users = []

    def _add_user(username: str):
        created_users.append(username)

    yield _add_user

    # Cleanup after test
    admin_dashboard.click_users_tab()
    for username in created_users:
        if admin_dashboard.find_user_in_table(username):
            try:
                admin_dashboard.click_delete_user(username)
                admin_dashboard.confirm_delete()
            except Exception as e:
                print(f"Failed to cleanup user {username}: {e}")


@pytest.fixture(scope="function")
def cleanup_test_role(admin_dashboard):
    """Fixture to clean up test roles after test."""
    created_roles = []

    def _add_role(role_name: str):
        created_roles.append(role_name)

    yield _add_role

    # Cleanup after test
    admin_dashboard.click_roles_tab()
    for role_name in created_roles:
        if admin_dashboard.find_role_in_table(role_name):
            try:
                admin_dashboard.click_delete_role(role_name)
                admin_dashboard.confirm_delete()
            except Exception as e:
                print(f"Failed to cleanup role {role_name}: {e}")


@pytest.fixture(scope="function")
def cleanup_test_department(admin_dashboard):
    """Fixture to clean up test departments after test."""
    created_departments = []

    def _add_department(dept_name: str):
        created_departments.append(dept_name)

    yield _add_department

    # Note: Currently no DELETE endpoint for departments
    # This fixture is a placeholder for future implementation
