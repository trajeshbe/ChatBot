"""
API Usage Tracker

Tracks Anthropic API usage and enforces daily/monthly budget caps.

Features:
- Daily budget limits
- Monthly budget limits
- Real-time usage tracking
- Auto-fallback when limits reached
- Persistent storage (Redis + Database)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class APIUsageTracker:
    """
    Tracks API usage and enforces budget limits

    Storage:
    - In-memory cache for fast access
    - Redis for persistence across restarts
    - Database for historical analytics

    Budget Caps:
    - Daily limit (default: $10)
    - Monthly limit (default: $200)
    - Configurable per user/organization
    """

    def __init__(
        self,
        daily_limit: float = 10.0,
        monthly_limit: float = 200.0
    ):
        """
        Initialize tracker with budget limits

        Args:
            daily_limit: Daily spending cap in USD
            monthly_limit: Monthly spending cap in USD
        """

        self.daily_budget_limit = daily_limit
        self.monthly_budget_limit = monthly_limit

        # In-memory cache (would use Redis in production)
        self.usage_cache = {
            "daily": {
                "date": None,
                "spent": 0.0,
                "tasks": 0,
                "details": []  # List of {task_id, cost, timestamp}
            },
            "monthly": {
                "month": None,
                "spent": 0.0,
                "tasks": 0,
                "details": []
            }
        }

        # Redis connection (TODO: Initialize from config)
        self.redis_client = None

    async def get_daily_budget_remaining(self) -> float:
        """
        Get remaining daily budget

        Returns:
            Remaining budget in USD
        """

        today = datetime.now().date()

        # Reset if new day
        if self.usage_cache["daily"]["date"] != today:
            self.usage_cache["daily"] = {
                "date": today,
                "spent": 0.0,
                "tasks": 0,
                "details": []
            }
            logger.info(f"📅 New day: Daily budget reset to ${self.daily_budget_limit:.2f}")

        spent_today = self.usage_cache["daily"]["spent"]
        remaining = max(0, self.daily_budget_limit - spent_today)

        return remaining

    async def get_monthly_budget_remaining(self) -> float:
        """
        Get remaining monthly budget

        Returns:
            Remaining budget in USD
        """

        current_month = datetime.now().strftime("%Y-%m")

        # Reset if new month
        if self.usage_cache["monthly"]["month"] != current_month:
            self.usage_cache["monthly"] = {
                "month": current_month,
                "spent": 0.0,
                "tasks": 0,
                "details": []
            }
            logger.info(f"📅 New month: Monthly budget reset to ${self.monthly_budget_limit:.2f}")

        spent_this_month = self.usage_cache["monthly"]["spent"]
        remaining = max(0, self.monthly_budget_limit - spent_this_month)

        return remaining

    async def record_usage(
        self,
        cost: float,
        task_id: str,
        agent_option: str,
        tokens_used: int = 0,
        model_name: str = None
    ):
        """
        Record API usage

        Args:
            cost: Cost in USD
            task_id: Unique task identifier
            agent_option: Which agent was used (local_mini/claude_cli)
            tokens_used: Total tokens consumed
            model_name: Model name used
        """

        if cost <= 0:
            # Free usage (local models), no tracking needed
            return

        today = datetime.now().date()
        current_month = datetime.now().strftime("%Y-%m")
        timestamp = datetime.now().isoformat()

        # Update daily
        if self.usage_cache["daily"]["date"] != today:
            self.usage_cache["daily"] = {
                "date": today,
                "spent": 0.0,
                "tasks": 0,
                "details": []
            }

        self.usage_cache["daily"]["spent"] += cost
        self.usage_cache["daily"]["tasks"] += 1
        self.usage_cache["daily"]["details"].append({
            "task_id": task_id,
            "cost": cost,
            "agent": agent_option,
            "tokens": tokens_used,
            "model": model_name,
            "timestamp": timestamp
        })

        # Update monthly
        if self.usage_cache["monthly"]["month"] != current_month:
            self.usage_cache["monthly"] = {
                "month": current_month,
                "spent": 0.0,
                "tasks": 0,
                "details": []
            }

        self.usage_cache["monthly"]["spent"] += cost
        self.usage_cache["monthly"]["tasks"] += 1
        self.usage_cache["monthly"]["details"].append({
            "task_id": task_id,
            "cost": cost,
            "agent": agent_option,
            "tokens": tokens_used,
            "model": model_name,
            "timestamp": timestamp
        })

        logger.info(
            f"💳 API Usage Recorded: ${cost:.2f} ({agent_option}) "
            f"| Daily: ${self.usage_cache['daily']['spent']:.2f}/"
            f"${self.daily_budget_limit:.2f} "
            f"| Monthly: ${self.usage_cache['monthly']['spent']:.2f}/"
            f"${self.monthly_budget_limit:.2f}"
        )

        # Check if approaching limits
        daily_pct = (self.usage_cache["daily"]["spent"] / self.daily_budget_limit * 100) if self.daily_budget_limit > 0 else 0
        monthly_pct = (self.usage_cache["monthly"]["spent"] / self.monthly_budget_limit * 100) if self.monthly_budget_limit > 0 else 0

        if daily_pct >= 80:
            logger.warning(f"⚠️ Daily budget {daily_pct:.0f}% consumed!")

        if monthly_pct >= 80:
            logger.warning(f"⚠️ Monthly budget {monthly_pct:.0f}% consumed!")

        # TODO: Store in database for persistence and analytics

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics

        Returns:
            Dictionary with daily/monthly stats
        """

        daily_remaining = await self.get_daily_budget_remaining()
        monthly_remaining = await self.get_monthly_budget_remaining()

        today = datetime.now().date()
        current_month = datetime.now().strftime("%Y-%m")

        # Ensure data is current
        if self.usage_cache["daily"]["date"] != today:
            await self.get_daily_budget_remaining()  # Triggers reset

        if self.usage_cache["monthly"]["month"] != current_month:
            await self.get_monthly_budget_remaining()  # Triggers reset

        return {
            "daily": {
                "limit": self.daily_budget_limit,
                "spent": round(self.usage_cache["daily"]["spent"], 2),
                "remaining": round(daily_remaining, 2),
                "tasks": self.usage_cache["daily"]["tasks"],
                "percentage_used": round(
                    (self.usage_cache["daily"]["spent"] / self.daily_budget_limit * 100)
                    if self.daily_budget_limit > 0 else 0,
                    1
                ),
                "date": str(self.usage_cache["daily"]["date"])
            },
            "monthly": {
                "limit": self.monthly_budget_limit,
                "spent": round(self.usage_cache["monthly"]["spent"], 2),
                "remaining": round(monthly_remaining, 2),
                "tasks": self.usage_cache["monthly"]["tasks"],
                "percentage_used": round(
                    (self.usage_cache["monthly"]["spent"] / self.monthly_budget_limit * 100)
                    if self.monthly_budget_limit > 0 else 0,
                    1
                ),
                "month": self.usage_cache["monthly"]["month"]
            },
            "warnings": self._get_budget_warnings()
        }

    def _get_budget_warnings(self) -> list:
        """Generate budget warnings"""

        warnings = []

        daily_pct = (self.usage_cache["daily"]["spent"] / self.daily_budget_limit * 100) if self.daily_budget_limit > 0 else 0
        monthly_pct = (self.usage_cache["monthly"]["spent"] / self.monthly_budget_limit * 100) if self.monthly_budget_limit > 0 else 0

        if daily_pct >= 100:
            warnings.append({
                "level": "critical",
                "message": "Daily budget exhausted! Claude CLI disabled until tomorrow."
            })
        elif daily_pct >= 90:
            warnings.append({
                "level": "warning",
                "message": f"Daily budget {daily_pct:.0f}% consumed"
            })

        if monthly_pct >= 100:
            warnings.append({
                "level": "critical",
                "message": "Monthly budget exhausted! Claude CLI disabled until next month."
            })
        elif monthly_pct >= 90:
            warnings.append({
                "level": "warning",
                "message": f"Monthly budget {monthly_pct:.0f}% consumed"
            })

        return warnings

    async def set_limits(
        self,
        daily_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None
    ):
        """
        Update budget limits

        Args:
            daily_limit: New daily limit in USD
            monthly_limit: New monthly limit in USD
        """

        if daily_limit is not None:
            self.daily_budget_limit = daily_limit
            logger.info(f"💰 Daily budget limit updated: ${daily_limit:.2f}")

        if monthly_limit is not None:
            self.monthly_budget_limit = monthly_limit
            logger.info(f"💰 Monthly budget limit updated: ${monthly_limit:.2f}")

        # TODO: Persist to database

    async def get_detailed_usage(
        self,
        period: str = "daily"
    ) -> list:
        """
        Get detailed usage breakdown

        Args:
            period: "daily" or "monthly"

        Returns:
            List of usage records
        """

        if period == "daily":
            return self.usage_cache["daily"]["details"]
        elif period == "monthly":
            return self.usage_cache["monthly"]["details"]
        else:
            return []


# Global instance
api_usage_tracker = APIUsageTracker(
    daily_limit=10.0,    # $10/day default
    monthly_limit=200.0  # $200/month default
)
