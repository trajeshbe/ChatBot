"""
Proxy Manager

This module provides rotating proxy support for web scraping to distribute
requests and avoid IP-based blocking.
"""

import random
import logging
from typing import List, Optional, Dict
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Rotating proxy manager for web scraping
    """

    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        test_proxies: bool = True
    ):
        """
        Initialize proxy manager

        Args:
            proxies: List of proxy URLs (e.g., ["http://proxy1:8080", "socks5://proxy2:1080"])
            test_proxies: Whether to test proxies on initialization (default: True)
        """
        self.proxies: List[str] = proxies or []
        self.working_proxies: List[str] = []
        self.failed_proxies: Dict[str, int] = {}  # proxy -> failure count
        self.current_index = 0
        self.max_failures = 3  # Max failures before removing proxy

        if self.proxies and test_proxies:
            self._test_proxies_sync()

    def _test_proxies_sync(self):
        """Test proxies synchronously during initialization"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # Already in async context, skip testing
            self.working_proxies = self.proxies.copy()
            logger.info(f"Proxy manager initialized with {len(self.proxies)} proxies (testing skipped)")
        else:
            loop.run_until_complete(self.test_all_proxies())

    async def test_proxy(self, proxy: str, test_url: str = "https://httpbin.org/ip") -> bool:
        """
        Test if a proxy is working

        Args:
            proxy: The proxy URL to test
            test_url: URL to test the proxy with (default: httpbin.org)

        Returns:
            True if proxy is working, False otherwise
        """
        try:
            async with httpx.AsyncClient(
                proxies=proxy,
                timeout=10.0,
                verify=False  # Don't verify SSL for proxy testing
            ) as client:
                response = await client.get(test_url)
                if response.status_code == 200:
                    logger.info(f"Proxy {proxy} is working")
                    return True
                else:
                    logger.warning(f"Proxy {proxy} returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Proxy {proxy} failed test: {e}")
            return False

    async def test_all_proxies(self):
        """Test all proxies and populate working_proxies list"""
        if not self.proxies:
            logger.info("No proxies configured")
            return

        logger.info(f"Testing {len(self.proxies)} proxies...")
        self.working_proxies = []

        for proxy in self.proxies:
            if await self.test_proxy(proxy):
                self.working_proxies.append(proxy)

        logger.info(f"Proxy testing complete: {len(self.working_proxies)}/{len(self.proxies)} working")

    def get_random(self) -> Optional[str]:
        """
        Get a random working proxy

        Returns:
            A random proxy URL, or None if no proxies available
        """
        if not self.working_proxies:
            return None

        return random.choice(self.working_proxies)

    def get_next(self) -> Optional[str]:
        """
        Get the next proxy in rotation

        Returns:
            The next proxy URL, or None if no proxies available
        """
        if not self.working_proxies:
            return None

        proxy = self.working_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.working_proxies)
        return proxy

    def get_proxy_dict(self, proxy_url: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get proxy dict in httpx format

        Args:
            proxy_url: Specific proxy URL to use, or None to get next in rotation

        Returns:
            Proxy dict for httpx, or None if no proxies available
        """
        if proxy_url is None:
            proxy_url = self.get_next()

        if not proxy_url:
            return None

        # httpx expects proxies in dict format
        # For HTTP/HTTPS proxies, use "all://" to apply to all schemes
        return {"all://": proxy_url}

    def report_failure(self, proxy: str):
        """
        Report a proxy failure

        Args:
            proxy: The proxy that failed
        """
        if proxy not in self.failed_proxies:
            self.failed_proxies[proxy] = 0

        self.failed_proxies[proxy] += 1
        logger.warning(f"Proxy {proxy} failure count: {self.failed_proxies[proxy]}")

        # Remove proxy if it has failed too many times
        if self.failed_proxies[proxy] >= self.max_failures:
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
                logger.error(f"Removed proxy {proxy} after {self.max_failures} failures")

    def report_success(self, proxy: str):
        """
        Report a proxy success (resets failure count)

        Args:
            proxy: The proxy that succeeded
        """
        if proxy in self.failed_proxies:
            self.failed_proxies[proxy] = 0

    def add_proxy(self, proxy: str):
        """
        Add a new proxy

        Args:
            proxy: The proxy URL to add
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.working_proxies.append(proxy)
            logger.info(f"Added new proxy: {proxy}")

    def remove_proxy(self, proxy: str):
        """
        Remove a proxy

        Args:
            proxy: The proxy URL to remove
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
        if proxy in self.failed_proxies:
            del self.failed_proxies[proxy]
        logger.info(f"Removed proxy: {proxy}")

    def get_status(self) -> Dict:
        """
        Get proxy manager status

        Returns:
            Dict with proxy statistics
        """
        return {
            "total_proxies": len(self.proxies),
            "working_proxies": len(self.working_proxies),
            "failed_proxies": len([p for p, c in self.failed_proxies.items() if c >= self.max_failures]),
            "proxies": self.proxies,
            "working": self.working_proxies,
            "failures": self.failed_proxies
        }

    def is_enabled(self) -> bool:
        """
        Check if proxy rotation is enabled

        Returns:
            True if there are working proxies, False otherwise
        """
        return len(self.working_proxies) > 0


# Singleton instance (initially without proxies)
proxy_manager = ProxyManager(proxies=[], test_proxies=False)
