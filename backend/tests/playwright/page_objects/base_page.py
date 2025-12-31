"""Base Page Object for Playwright tests."""
from playwright.sync_api import Page, expect
from typing import Optional
import time


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        self.page = page
        self.base_url = base_url

    def navigate_to(self, path: str):
        """Navigate to a specific path."""
        self.page.goto(f"{self.base_url}{path}")
        self.page.wait_for_load_state("networkidle")

    def wait_for_element(self, selector: str, timeout: int = 10000):
        """Wait for an element to be visible."""
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)

    def click(self, selector: str):
        """Click an element."""
        self.page.click(selector)

    def fill(self, selector: str, value: str):
        """Fill a text input."""
        self.page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self.page.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return self.page.is_visible(selector)

    def screenshot(self, filename: str):
        """Take a screenshot."""
        self.page.screenshot(path=f"backend/tests/playwright/test_results/{filename}")

    def wait_for_navigation(self):
        """Wait for navigation to complete."""
        self.page.wait_for_load_state("networkidle")
