"""
Compliance Engine

This module orchestrates all compliance components to ensure ethical and legal
web scraping based on configurable compliance levels: strict, balanced, aggressive.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum
from urllib.parse import urlparse
import httpx

from .robots_txt_checker import robots_txt_checker
from .rate_limiter import rate_limiter
from .user_agent_rotator import user_agent_rotator
from .proxy_manager import proxy_manager
from .auth_manager import auth_manager, AuthType

logger = logging.getLogger(__name__)


class ComplianceLevel(str, Enum):
    """Compliance levels for web scraping"""
    STRICT = "strict"          # Maximum compliance: respect all rules, use bot user agent
    BALANCED = "balanced"      # Reasonable compliance: respect robots.txt, polite rate limiting
    AGGRESSIVE = "aggressive"  # Minimal compliance: fast scraping, minimal delays


class ComplianceEngine:
    """
    Main compliance engine that orchestrates all compliance components
    """

    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.BALANCED):
        """
        Initialize compliance engine

        Args:
            compliance_level: The compliance level to use
        """
        self.compliance_level = compliance_level
        self.initialized = False

        # Compliance settings per level
        self.settings = self._get_settings_for_level(compliance_level)

        logger.info(f"Compliance engine initialized with level: {compliance_level}")

    def _get_settings_for_level(self, level: ComplianceLevel) -> Dict[str, Any]:
        """
        Get compliance settings for a specific level

        Args:
            level: The compliance level

        Returns:
            Dict of settings
        """
        if level == ComplianceLevel.STRICT:
            return {
                "check_robots_txt": True,
                "respect_crawl_delay": True,
                "respect_request_rate": True,
                "use_bot_user_agent": True,
                "use_proxies": False,  # Proxies might be seen as evasive
                "default_delay": 2.0,  # 2 seconds between requests
                "max_requests_per_minute": 10,
                "timeout": 60.0,
                "max_retries": 2,
                "follow_redirects": True,
            }

        elif level == ComplianceLevel.BALANCED:
            return {
                "check_robots_txt": True,
                "respect_crawl_delay": True,
                "respect_request_rate": False,  # Use our own rate limiting
                "use_bot_user_agent": False,
                "use_proxies": True,  # Optional proxy rotation
                "default_delay": 1.0,  # 1 second between requests
                "max_requests_per_minute": 30,
                "timeout": 30.0,
                "max_retries": 3,
                "follow_redirects": True,
            }

        elif level == ComplianceLevel.AGGRESSIVE:
            return {
                "check_robots_txt": False,  # Skip robots.txt
                "respect_crawl_delay": False,
                "respect_request_rate": False,
                "use_bot_user_agent": False,
                "use_proxies": True,  # Highly recommended for aggressive
                "default_delay": 0.1,  # 100ms between requests
                "max_requests_per_minute": 120,
                "timeout": 15.0,
                "max_retries": 5,
                "follow_redirects": True,
            }

        else:
            # Default to balanced
            return self._get_settings_for_level(ComplianceLevel.BALANCED)

    async def initialize(self):
        """Initialize all compliance components"""
        if self.initialized:
            return

        try:
            # Initialize rate limiter
            await rate_limiter.init()

            self.initialized = True
            logger.info("Compliance engine components initialized")

        except Exception as e:
            logger.error(f"Error initializing compliance engine: {e}")
            raise

    async def close(self):
        """Close all compliance components"""
        try:
            await robots_txt_checker.close()
            await rate_limiter.close()
            logger.info("Compliance engine components closed")
        except Exception as e:
            logger.error(f"Error closing compliance engine: {e}")

    async def check_url_allowed(
        self,
        url: str,
        user_agent: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a URL is allowed to be scraped

        Args:
            url: The URL to check
            user_agent: The user agent to use (optional)

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Skip robots.txt check if not required
        if not self.settings["check_robots_txt"]:
            return True, None

        # Get user agent
        if not user_agent:
            user_agent = self.get_user_agent()

        # Check robots.txt
        allowed = await robots_txt_checker.can_fetch(url, user_agent)

        if not allowed:
            return False, "Disallowed by robots.txt"

        return True, None

    async def get_delay_for_url(self, url: str) -> float:
        """
        Get the delay to use before scraping a URL

        Args:
            url: The URL to scrape

        Returns:
            Delay in seconds
        """
        delay = self.settings["default_delay"]

        # If respecting crawl delay, check robots.txt
        if self.settings["respect_crawl_delay"]:
            user_agent = self.get_user_agent()
            crawl_delay = await robots_txt_checker.get_crawl_delay(url, user_agent)

            if crawl_delay:
                delay = max(delay, crawl_delay)
                logger.debug(f"Using robots.txt crawl delay of {crawl_delay}s for {url}")

        # If respecting request rate, check robots.txt
        if self.settings["respect_request_rate"]:
            user_agent = self.get_user_agent()
            request_rate = await robots_txt_checker.get_request_rate(url, user_agent)

            if request_rate:
                requests, seconds = request_rate
                rate_delay = seconds / requests
                delay = max(delay, rate_delay)
                logger.debug(f"Using robots.txt request rate delay of {rate_delay}s for {url}")

        return delay

    async def apply_rate_limiting(self, url: str):
        """
        Apply rate limiting before making a request

        Args:
            url: The URL being requested
        """
        # Get delay
        delay = await self.get_delay_for_url(url)

        # Calculate max requests from delay
        max_requests = int(60 / delay) if delay > 0 else self.settings["max_requests_per_minute"]

        # Wait if needed
        await rate_limiter.wait_if_needed(
            url,
            delay=delay,
            max_requests=max_requests,
            time_window=60
        )

    def get_user_agent(self) -> str:
        """
        Get a user agent based on compliance level

        Returns:
            User agent string
        """
        if self.settings["use_bot_user_agent"]:
            # Use bot-friendly user agent
            rotator = user_agent_rotator.__class__(use_bot_agents=True)
            return rotator.get_random()
        else:
            # Use regular user agent
            return user_agent_rotator.get_random()

    def get_proxy(self) -> Optional[str]:
        """
        Get a proxy if proxy rotation is enabled

        Returns:
            Proxy URL, or None if proxies not enabled
        """
        if not self.settings["use_proxies"]:
            return None

        if not proxy_manager.is_enabled():
            return None

        return proxy_manager.get_next()

    def create_http_client(
        self,
        auth_config: Optional[Dict[str, Any]] = None
    ) -> httpx.AsyncClient:
        """
        Create an HTTP client with compliance settings

        Args:
            auth_config: Optional authentication configuration

        Returns:
            Configured HTTP client
        """
        # Get user agent
        user_agent = self.get_user_agent()

        # Base headers (enhanced to mimic modern browsers and avoid 403 errors)
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        # Get proxy
        proxy = self.get_proxy()
        proxies = proxy_manager.get_proxy_dict(proxy) if proxy else None

        # Create client
        client = httpx.AsyncClient(
            timeout=self.settings["timeout"],
            follow_redirects=self.settings["follow_redirects"],
            headers=headers,
            proxies=proxies,
            verify=True
        )

        # Apply authentication if provided
        if auth_config:
            client = auth_manager.apply_auth(client, auth_config)

        return client

    async def make_compliant_request(
        self,
        url: str,
        method: str = "GET",
        auth_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make a compliant HTTP request

        Args:
            url: The URL to request
            method: HTTP method (default: GET)
            auth_config: Optional authentication configuration
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            HTTP response

        Raises:
            Exception: If request fails or is not allowed
        """
        # Check if URL is allowed
        allowed, reason = await self.check_url_allowed(url)
        if not allowed:
            raise ValueError(f"URL not allowed: {reason}")

        # Apply rate limiting
        await self.apply_rate_limiting(url)

        # Track current proxy for retry logic
        current_proxy = self.get_proxy()

        # Create HTTP client
        client = self.create_http_client(auth_config)

        # Make request with retries
        max_retries = self.settings["max_retries"]
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()

                # Report proxy success if using proxy
                if current_proxy:
                    proxy_manager.report_success(current_proxy)

                await client.aclose()
                return response

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error {e.response.status_code} for {url} (attempt {attempt + 1}/{max_retries + 1})")
                last_error = e

                # Don't retry on 4xx errors (except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    await client.aclose()
                    raise

            except Exception as e:
                logger.warning(f"Request error for {url}: {e} (attempt {attempt + 1}/{max_retries + 1})")
                last_error = e

                # Report proxy failure if using proxy
                if current_proxy:
                    proxy_manager.report_failure(current_proxy)

                # Close current client and create new one with different proxy for next attempt
                await client.aclose()

                if proxy_manager.is_enabled() and attempt < max_retries:
                    current_proxy = proxy_manager.get_next()
                    if current_proxy:
                        logger.info(f"Retrying with different proxy: {current_proxy}")
                    client = self.create_http_client(auth_config)

        await client.aclose()

        # All retries failed
        raise last_error if last_error else Exception(f"Failed to fetch {url} after {max_retries + 1} attempts")

    def get_settings(self) -> Dict[str, Any]:
        """
        Get current compliance settings

        Returns:
            Dict of settings
        """
        return self.settings.copy()

    def update_settings(self, settings: Dict[str, Any]):
        """
        Update compliance settings

        Args:
            settings: Dict of settings to update
        """
        self.settings.update(settings)
        logger.info(f"Updated compliance settings: {settings}")

    def set_compliance_level(self, level: ComplianceLevel):
        """
        Set compliance level

        Args:
            level: The compliance level to use
        """
        self.compliance_level = level
        self.settings = self._get_settings_for_level(level)
        logger.info(f"Set compliance level to: {level}")


# Global instances for different compliance levels
strict_compliance = ComplianceEngine(ComplianceLevel.STRICT)
balanced_compliance = ComplianceEngine(ComplianceLevel.BALANCED)
aggressive_compliance = ComplianceEngine(ComplianceLevel.AGGRESSIVE)

# Default instance (balanced)
compliance_engine = balanced_compliance
