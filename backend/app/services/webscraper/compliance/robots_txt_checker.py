"""
Robots.txt Parser and Validator

This module provides functionality to parse and validate robots.txt files
to ensure compliance with website scraping policies.
"""

import httpx
import logging
from typing import Optional, Dict
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RobotsTxtChecker:
    """
    Robots.txt parser and validator for web scraping compliance
    """

    def __init__(self, cache_duration_hours: int = 24):
        """
        Initialize robots.txt checker with caching

        Args:
            cache_duration_hours: How long to cache robots.txt files (default: 24 hours)
        """
        self.cache: Dict[str, tuple[RobotFileParser, datetime]] = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    def _get_robots_url(self, url: str) -> str:
        """
        Get the robots.txt URL for a given URL

        Args:
            url: The URL to check

        Returns:
            The robots.txt URL
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    async def _fetch_robots_txt(self, robots_url: str) -> Optional[str]:
        """
        Fetch robots.txt content from URL

        Args:
            robots_url: The robots.txt URL

        Returns:
            The robots.txt content, or None if not found
        """
        try:
            response = await self.http_client.get(robots_url)
            if response.status_code == 200:
                return response.text
            else:
                logger.debug(f"Robots.txt not found at {robots_url} (status {response.status_code})")
                return None
        except Exception as e:
            logger.warning(f"Error fetching robots.txt from {robots_url}: {e}")
            return None

    async def _get_robot_parser(self, url: str) -> Optional[RobotFileParser]:
        """
        Get or create a RobotFileParser for the given URL

        Args:
            url: The URL to check

        Returns:
            RobotFileParser instance, or None if robots.txt not available
        """
        robots_url = self._get_robots_url(url)

        # Check cache
        if robots_url in self.cache:
            parser, cached_at = self.cache[robots_url]
            if datetime.now() - cached_at < self.cache_duration:
                return parser

        # Fetch and parse robots.txt
        robots_content = await self._fetch_robots_txt(robots_url)
        if not robots_content:
            # No robots.txt means everything is allowed
            return None

        # Parse robots.txt
        parser = RobotFileParser()
        parser.parse(robots_content.splitlines())

        # Cache the parser
        self.cache[robots_url] = (parser, datetime.now())

        return parser

    async def can_fetch(
        self,
        url: str,
        user_agent: str = "*"
    ) -> bool:
        """
        Check if the given URL can be fetched according to robots.txt

        Args:
            url: The URL to check
            user_agent: The user agent to check for (default: "*")

        Returns:
            True if the URL can be fetched, False otherwise
        """
        try:
            parser = await self._get_robot_parser(url)

            # If no robots.txt, allow everything
            if not parser:
                return True

            # Check if URL can be fetched
            return parser.can_fetch(user_agent, url)

        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # On error, be conservative and allow
            return True

    async def get_crawl_delay(
        self,
        url: str,
        user_agent: str = "*"
    ) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt

        Args:
            url: The URL to check
            user_agent: The user agent to check for (default: "*")

        Returns:
            The crawl delay in seconds, or None if not specified
        """
        try:
            parser = await self._get_robot_parser(url)

            if not parser:
                return None

            # Get crawl delay
            delay = parser.crawl_delay(user_agent)
            return float(delay) if delay else None

        except Exception as e:
            logger.error(f"Error getting crawl delay for {url}: {e}")
            return None

    async def get_request_rate(
        self,
        url: str,
        user_agent: str = "*"
    ) -> Optional[tuple[int, int]]:
        """
        Get the request rate specified in robots.txt

        Args:
            url: The URL to check
            user_agent: The user agent to check for (default: "*")

        Returns:
            Tuple of (requests, seconds), or None if not specified
        """
        try:
            parser = await self._get_robot_parser(url)

            if not parser:
                return None

            # Get request rate
            rate = parser.request_rate(user_agent)
            if rate:
                return (rate.requests, rate.seconds)

            return None

        except Exception as e:
            logger.error(f"Error getting request rate for {url}: {e}")
            return None

    def clear_cache(self):
        """Clear the robots.txt cache"""
        self.cache.clear()
        logger.info("Robots.txt cache cleared")


# Singleton instance
robots_txt_checker = RobotsTxtChecker()
