"""Login Page Object."""
from playwright.sync_api import Page, expect
from .base_page import BasePage
import time


class LoginPage(BasePage):
    """Page object for login functionality."""

    # Selectors
    USERNAME_INPUT = 'input[type="text"], input[name="username"], input[placeholder*="Username"]'
    PASSWORD_INPUT = 'input[type="password"], input[name="password"], input[placeholder*="Password"]'
    LOGIN_BUTTON = 'button:has-text("Login"), button:has-text("Sign In"), button[type="submit"]'

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url)

    def navigate(self):
        """Navigate to login page."""
        self.navigate_to("/login")
        time.sleep(1)  # Wait for page to stabilize

    def login(self, username: str, password: str):
        """Perform login."""
        # Wait for login form to be visible
        self.wait_for_element(self.USERNAME_INPUT)

        # Fill credentials
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)

        # Wait for navigation and click login button
        # Use expect_navigation to properly wait for redirect
        with self.page.expect_navigation(timeout=10000, wait_until="networkidle"):
            self.click(self.LOGIN_BUTTON)

        # Additional wait to ensure page is fully loaded
        time.sleep(1)

    def is_logged_in(self) -> bool:
        """Check if user is logged in by checking for admin link or user menu."""
        # After login, should be redirected away from login page
        return "/login" not in self.page.url
