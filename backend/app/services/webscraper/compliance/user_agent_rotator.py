"""
User Agent Rotator

This module provides user agent rotation to avoid detection and blocking
while maintaining ethical scraping practices.
"""

import random
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class UserAgentRotator:
    """
    User agent rotation for web scraping
    """

    # Comprehensive list of realistic user agents
    DEFAULT_USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",

        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",

        # Firefox on Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",

        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",

        # Safari on iOS
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",

        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",

        # Chrome on Android
        "Mozilla/5.0 (Linux; Android 13; SM-S918U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]

    # Bot-friendly user agents (for strict compliance mode)
    BOT_USER_AGENTS = [
        "EnterpriseRAGBot/1.0 (+https://github.com/yourusername/ChatBot)",
        "DataExtractionBot/1.0 (Enterprise RAG Chatbot; +https://github.com/yourusername/ChatBot)",
    ]

    def __init__(
        self,
        custom_user_agents: Optional[List[str]] = None,
        use_bot_agents: bool = False
    ):
        """
        Initialize user agent rotator

        Args:
            custom_user_agents: Optional list of custom user agents
            use_bot_agents: Whether to use bot-friendly user agents (default: False)
        """
        if custom_user_agents:
            self.user_agents = custom_user_agents
        elif use_bot_agents:
            self.user_agents = self.BOT_USER_AGENTS
        else:
            self.user_agents = self.DEFAULT_USER_AGENTS

        self.current_index = 0
        logger.info(f"User agent rotator initialized with {len(self.user_agents)} user agents")

    def get_random(self) -> str:
        """
        Get a random user agent

        Returns:
            A random user agent string
        """
        return random.choice(self.user_agents)

    def get_next(self) -> str:
        """
        Get the next user agent in rotation

        Returns:
            The next user agent string
        """
        user_agent = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return user_agent

    def get_by_platform(self, platform: str) -> str:
        """
        Get a user agent for a specific platform

        Args:
            platform: Platform name (windows, macos, linux, ios, android)

        Returns:
            A user agent string for the specified platform
        """
        platform = platform.lower()
        platform_agents = [
            ua for ua in self.user_agents
            if platform in ua.lower()
        ]

        if platform_agents:
            return random.choice(platform_agents)
        else:
            logger.warning(f"No user agents found for platform: {platform}, using random")
            return self.get_random()

    def get_by_browser(self, browser: str) -> str:
        """
        Get a user agent for a specific browser

        Args:
            browser: Browser name (chrome, firefox, safari, edge)

        Returns:
            A user agent string for the specified browser
        """
        browser = browser.lower()
        browser_agents = [
            ua for ua in self.user_agents
            if browser in ua.lower()
        ]

        if browser_agents:
            return random.choice(browser_agents)
        else:
            logger.warning(f"No user agents found for browser: {browser}, using random")
            return self.get_random()

    def add_custom_agent(self, user_agent: str):
        """
        Add a custom user agent to the pool

        Args:
            user_agent: The user agent string to add
        """
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
            logger.info(f"Added custom user agent: {user_agent[:50]}...")

    def get_all(self) -> List[str]:
        """
        Get all available user agents

        Returns:
            List of all user agent strings
        """
        return self.user_agents.copy()

    def get_count(self) -> int:
        """
        Get the number of available user agents

        Returns:
            The number of user agents
        """
        return len(self.user_agents)


# Singleton instance
user_agent_rotator = UserAgentRotator()
