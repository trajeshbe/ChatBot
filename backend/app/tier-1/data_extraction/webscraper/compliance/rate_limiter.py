"""
Rate Limiter for Web Scraping

This module provides per-domain rate limiting to ensure polite scraping
and compliance with website policies.
"""

import asyncio
import logging
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Per-domain rate limiter using Redis for distributed rate limiting
    """

    def __init__(
        self,
        redis_url: str = "redis://redis:6379",
        default_delay: float = 1.0,
        default_max_requests: int = 10,
        default_time_window: int = 60
    ):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
            default_delay: Default delay between requests in seconds
            default_max_requests: Default maximum requests in time window
            default_time_window: Default time window in seconds
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.default_delay = default_delay
        self.default_max_requests = default_max_requests
        self.default_time_window = default_time_window

        # In-memory cache for when Redis is unavailable
        self.local_cache: Dict[str, float] = {}
        self.local_request_counts: Dict[str, list] = {}

    async def init(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
            logger.warning("Using in-memory rate limiting (not distributed)")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()

    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL

        Args:
            url: The URL to parse

        Returns:
            The domain name
        """
        parsed = urlparse(url)
        return parsed.netloc

    async def _wait_with_redis(
        self,
        domain: str,
        delay: float,
        max_requests: int,
        time_window: int
    ) -> float:
        """
        Wait based on Redis-backed rate limiting

        Args:
            domain: The domain to rate limit
            delay: Delay between requests
            max_requests: Maximum requests in time window
            time_window: Time window in seconds

        Returns:
            The actual wait time in seconds
        """
        try:
            # Key for last request timestamp
            last_request_key = f"ratelimit:last:{domain}"
            # Key for request count
            count_key = f"ratelimit:count:{domain}"

            # Get last request time
            last_request_time = await self.redis_client.get(last_request_key)

            current_time = time.time()
            wait_time = 0.0

            if last_request_time:
                last_request_time = float(last_request_time)
                time_since_last = current_time - last_request_time

                # Calculate wait time based on delay
                if time_since_last < delay:
                    wait_time = delay - time_since_last

            # Check request count in time window
            request_count = await self.redis_client.get(count_key)
            if request_count:
                request_count = int(request_count)
                if request_count >= max_requests:
                    # Wait for the time window to reset
                    ttl = await self.redis_client.ttl(count_key)
                    if ttl > 0:
                        wait_time = max(wait_time, ttl)

            # Wait if necessary
            if wait_time > 0:
                logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            # Update last request time
            await self.redis_client.set(last_request_key, time.time())

            # Increment request count
            pipe = self.redis_client.pipeline()
            pipe.incr(count_key)
            pipe.expire(count_key, time_window)
            await pipe.execute()

            return wait_time

        except Exception as e:
            logger.error(f"Error in Redis rate limiting for {domain}: {e}")
            # Fall back to local rate limiting
            return await self._wait_with_local_cache(domain, delay)

    async def _wait_with_local_cache(
        self,
        domain: str,
        delay: float
    ) -> float:
        """
        Wait based on local in-memory rate limiting (fallback)

        Args:
            domain: The domain to rate limit
            delay: Delay between requests

        Returns:
            The actual wait time in seconds
        """
        current_time = time.time()
        last_request_time = self.local_cache.get(domain, 0)

        time_since_last = current_time - last_request_time
        wait_time = 0.0

        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s (local)")
            await asyncio.sleep(wait_time)

        # Update last request time
        self.local_cache[domain] = time.time()

        return wait_time

    async def wait_if_needed(
        self,
        url: str,
        delay: Optional[float] = None,
        max_requests: Optional[int] = None,
        time_window: Optional[int] = None
    ) -> float:
        """
        Wait if needed based on rate limiting rules

        Args:
            url: The URL being requested
            delay: Override delay between requests (default: use default_delay)
            max_requests: Override maximum requests in time window
            time_window: Override time window in seconds

        Returns:
            The actual wait time in seconds
        """
        domain = self._get_domain(url)

        delay = delay if delay is not None else self.default_delay
        max_requests = max_requests if max_requests is not None else self.default_max_requests
        time_window = time_window if time_window is not None else self.default_time_window

        if self.redis_client:
            return await self._wait_with_redis(domain, delay, max_requests, time_window)
        else:
            return await self._wait_with_local_cache(domain, delay)

    async def reset_domain(self, url: str):
        """
        Reset rate limiting for a domain

        Args:
            url: URL of the domain to reset
        """
        domain = self._get_domain(url)

        if self.redis_client:
            try:
                await self.redis_client.delete(
                    f"ratelimit:last:{domain}",
                    f"ratelimit:count:{domain}"
                )
                logger.info(f"Reset rate limiting for {domain}")
            except Exception as e:
                logger.error(f"Error resetting rate limit for {domain}: {e}")
        else:
            self.local_cache.pop(domain, None)
            self.local_request_counts.pop(domain, None)

    async def clear_all(self):
        """Clear all rate limiting data"""
        if self.redis_client:
            try:
                # Find all rate limiting keys
                keys = []
                async for key in self.redis_client.scan_iter(match="ratelimit:*"):
                    keys.append(key)

                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} rate limiting keys")
            except Exception as e:
                logger.error(f"Error clearing rate limiting data: {e}")
        else:
            self.local_cache.clear()
            self.local_request_counts.clear()
            logger.info("Cleared local rate limiting cache")


# Singleton instance
rate_limiter = RateLimiter()
