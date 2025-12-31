"""
Authentication Manager

This module provides multi-auth support for web scraping, including
Basic Auth, Bearer tokens, OAuth2, JWT, and session-based authentication.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class AuthType(str, Enum):
    """Authentication types"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    SESSION = "session"
    CUSTOM = "custom"


class AuthManager:
    """
    Authentication manager for web scraping
    """

    def __init__(self):
        """Initialize authentication manager"""
        self.auth_cache: Dict[str, Dict[str, Any]] = {}

    def create_auth(
        self,
        auth_type: AuthType,
        credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create authentication configuration

        Args:
            auth_type: Type of authentication
            credentials: Authentication credentials

        Returns:
            Authentication configuration dict
        """
        if auth_type == AuthType.NONE:
            return None

        elif auth_type == AuthType.BASIC:
            return self._create_basic_auth(credentials)

        elif auth_type == AuthType.BEARER:
            return self._create_bearer_auth(credentials)

        elif auth_type == AuthType.API_KEY:
            return self._create_api_key_auth(credentials)

        elif auth_type == AuthType.OAUTH2:
            return self._create_oauth2_auth(credentials)

        elif auth_type == AuthType.JWT:
            return self._create_jwt_auth(credentials)

        elif auth_type == AuthType.SESSION:
            return self._create_session_auth(credentials)

        elif auth_type == AuthType.CUSTOM:
            return self._create_custom_auth(credentials)

        else:
            logger.error(f"Unsupported auth type: {auth_type}")
            return None

    def _create_basic_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Basic Authentication configuration

        Args:
            credentials: Dict with 'username' and 'password'

        Returns:
            Auth configuration
        """
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            raise ValueError("Basic auth requires username and password")

        return {
            "type": "basic",
            "auth": (username, password)
        }

    def _create_bearer_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Bearer Token authentication configuration

        Args:
            credentials: Dict with 'token'

        Returns:
            Auth configuration
        """
        token = credentials.get("token")

        if not token:
            raise ValueError("Bearer auth requires token")

        return {
            "type": "bearer",
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }

    def _create_api_key_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create API Key authentication configuration

        Args:
            credentials: Dict with 'api_key', 'header_name' (optional), 'query_param' (optional)

        Returns:
            Auth configuration
        """
        api_key = credentials.get("api_key")
        header_name = credentials.get("header_name", "X-API-Key")
        query_param = credentials.get("query_param")

        if not api_key:
            raise ValueError("API key auth requires api_key")

        config = {"type": "api_key"}

        # API key can be in header or query parameter
        if query_param:
            config["params"] = {query_param: api_key}
        else:
            config["headers"] = {header_name: api_key}

        return config

    def _create_oauth2_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create OAuth2 authentication configuration

        Args:
            credentials: Dict with 'access_token' or OAuth2 flow credentials

        Returns:
            Auth configuration
        """
        access_token = credentials.get("access_token")

        if not access_token:
            # TODO: Implement OAuth2 flow if credentials include client_id, client_secret, etc.
            raise ValueError("OAuth2 auth requires access_token")

        return {
            "type": "oauth2",
            "headers": {
                "Authorization": f"Bearer {access_token}"
            }
        }

    def _create_jwt_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create JWT authentication configuration

        Args:
            credentials: Dict with 'token'

        Returns:
            Auth configuration
        """
        token = credentials.get("token")

        if not token:
            raise ValueError("JWT auth requires token")

        return {
            "type": "jwt",
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }

    def _create_session_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create session-based authentication configuration

        Args:
            credentials: Dict with 'cookies' or session info

        Returns:
            Auth configuration
        """
        cookies = credentials.get("cookies")

        if not cookies:
            raise ValueError("Session auth requires cookies")

        return {
            "type": "session",
            "cookies": cookies
        }

    def _create_custom_auth(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create custom authentication configuration

        Args:
            credentials: Dict with custom headers, params, etc.

        Returns:
            Auth configuration
        """
        return {
            "type": "custom",
            "headers": credentials.get("headers", {}),
            "params": credentials.get("params", {}),
            "cookies": credentials.get("cookies", {})
        }

    def apply_auth(
        self,
        client: httpx.AsyncClient,
        auth_config: Optional[Dict[str, Any]]
    ) -> httpx.AsyncClient:
        """
        Apply authentication to HTTP client

        Args:
            client: The HTTP client to configure
            auth_config: Authentication configuration

        Returns:
            Configured HTTP client
        """
        if not auth_config:
            return client

        auth_type = auth_config.get("type")

        if auth_type == "basic":
            # For httpx, basic auth is applied per-request
            # Store it in client for later use
            client.auth = auth_config.get("auth")

        elif auth_type in ["bearer", "oauth2", "jwt", "api_key", "custom"]:
            # Add headers to client
            headers = auth_config.get("headers", {})
            client.headers.update(headers)

            # Add query params if present
            params = auth_config.get("params", {})
            if params:
                # Store params for later use in requests
                client.params = params

        elif auth_type == "session":
            # Set cookies
            cookies = auth_config.get("cookies", {})
            client.cookies.update(cookies)

        return client

    async def test_auth(
        self,
        url: str,
        auth_config: Dict[str, Any]
    ) -> bool:
        """
        Test if authentication is working

        Args:
            url: URL to test authentication against
            auth_config: Authentication configuration

        Returns:
            True if authentication works, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                client = self.apply_auth(client, auth_config)
                response = await client.get(url)

                # Consider 2xx and 3xx as success
                if 200 <= response.status_code < 400:
                    logger.info(f"Authentication test successful for {url}")
                    return True
                else:
                    logger.warning(f"Authentication test failed for {url}: status {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Authentication test error for {url}: {e}")
            return False

    def cache_auth(
        self,
        domain: str,
        auth_config: Dict[str, Any]
    ):
        """
        Cache authentication for a domain

        Args:
            domain: Domain to cache auth for
            auth_config: Authentication configuration
        """
        self.auth_cache[domain] = auth_config
        logger.info(f"Cached authentication for {domain}")

    def get_cached_auth(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get cached authentication for a domain

        Args:
            domain: Domain to get auth for

        Returns:
            Authentication configuration, or None if not cached
        """
        return self.auth_cache.get(domain)

    def clear_cache(self, domain: Optional[str] = None):
        """
        Clear authentication cache

        Args:
            domain: Specific domain to clear, or None to clear all
        """
        if domain:
            if domain in self.auth_cache:
                del self.auth_cache[domain]
                logger.info(f"Cleared authentication cache for {domain}")
        else:
            self.auth_cache.clear()
            logger.info("Cleared all authentication cache")


# Singleton instance
auth_manager = AuthManager()
