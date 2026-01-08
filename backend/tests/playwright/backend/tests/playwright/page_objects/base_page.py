"""Base Page Object class for Playwright tests."""
from playwright.sync_api import Page
import time


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        self.page = page
        self.base_url = base_url

    def navigate_to(self, path: str = "/"):
        """Navigate to a specific path."""
        url = f"{self.base_url}{path}"
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

    def wait_for_selector(self, selector: str, timeout: int = 10000):
        """Wait for a selector to appear."""
        self.page.wait_for_selector(selector, timeout=timeout)

    def click(self, selector: str):
        """Click an element."""
        self.page.click(selector)

    def fill(self, selector: str, value: str):
        """Fill an input field."""
        self.page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self.page.locator(selector).text_content()

    def is_visible(self, selector: str) -> bool:
        """Check if an element is visible."""
        return self.page.is_visible(selector)

    def wait(self, seconds: float):
        """Wait for a specified number of seconds."""
        time.sleep(seconds)
