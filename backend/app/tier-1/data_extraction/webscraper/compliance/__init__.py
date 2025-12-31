"""
Compliance Module for Web Scraping

This module provides comprehensive compliance tools for ethical and legal web scraping,
including robots.txt checking, rate limiting, proxy rotation, user agent management,
and authentication support.
"""

from .robots_txt_checker import RobotsTxtChecker, robots_txt_checker
from .rate_limiter import RateLimiter, rate_limiter
from .user_agent_rotator import UserAgentRotator, user_agent_rotator
from .proxy_manager import ProxyManager, proxy_manager
from .auth_manager import AuthManager, AuthType, auth_manager
from .compliance_engine import (
    ComplianceEngine,
    ComplianceLevel,
    compliance_engine,
    strict_compliance,
    balanced_compliance,
    aggressive_compliance
)

__all__ = [
    # Classes
    "RobotsTxtChecker",
    "RateLimiter",
    "UserAgentRotator",
    "ProxyManager",
    "AuthManager",
    "AuthType",
    "ComplianceEngine",
    "ComplianceLevel",

    # Singleton instances
    "robots_txt_checker",
    "rate_limiter",
    "user_agent_rotator",
    "proxy_manager",
    "auth_manager",
    "compliance_engine",
    "strict_compliance",
    "balanced_compliance",
    "aggressive_compliance",
]
