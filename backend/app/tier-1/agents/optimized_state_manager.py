"""
Optimized State Manager for Context Window Optimization

Manages workflow state with intelligent caching and pruning to minimize
context window usage for smaller LLMs while preserving critical information.

Key Features:
- Agent-specific state views (only what each agent needs)
- Redis caching for intermediate results
- Full state reconstruction for document generation
- TTL-based cache expiry
- Token budget enforcement

Usage:
    state_manager = OptimizedStateManager(workflow_id="proj_123")

    # Get compact state for specific agent
    compact_state = await state_manager.get_compact_state("agent_1")

    # Store intermediate result
    await state_manager.store_result("agent_1", result_data)

    # Get full state for final doc generation
    full_state = await state_manager.get_full_state()
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import timedelta
import redis.asyncio as redis

from app.core.config import settings
from app.utils.text_compression import compress_text, count_tokens

logger = logging.getLogger(__name__)


class OptimizedStateManager:
    """
    Manages workflow state with intelligent pruning and caching.
    """

    # Define what each agent needs to see (token budget per agent)
    AGENT_STATE_REQUIREMENTS = {
        "agent_1_analyst": {
            "inputs": ["user_prompt", "sample_brds"],
            "outputs": ["requirements", "complexity_assessment"],
            "max_tokens": 3500,
            "compress_inputs": True
        },
        "agent_1_1_eda": {
            "inputs": ["user_prompt", "requirements"],
            "outputs": ["eda_report"],
            "max_tokens": 2000,
            "compress_inputs": True
        },
        "agent_2_team_planner": {
            "inputs": ["requirements_summary", "complexity_summary", "eda_summary"],
            "outputs": ["team_structure", "resource_plan"],
            "max_tokens": 1500,
            "compress_inputs": True
        },
        "agent_3_task_breakdown": {
            "inputs": ["requirements_summary", "team_structure"],
            "outputs": ["task_list", "dependencies"],
            "max_tokens": 2000,
            "compress_inputs": True
        },
        "agent_4_cost_estimator": {
            "inputs": ["team_structure", "task_list", "complexity_summary"],
            "outputs": ["cost_breakdown", "timeline"],
            "max_tokens": 1500,
            "compress_inputs": True
        },
        "agent_5_risk_analyzer": {
            "inputs": ["requirements_summary", "team_structure", "timeline"],
            "outputs": ["risk_assessment", "mitigation_strategies"],
            "max_tokens": 1500,
            "compress_inputs": True
        },
        "agent_6_doc_generator": {
            "inputs": ["all"],  # Needs everything for final documents
            "outputs": ["brd_document", "excel_file"],
            "max_tokens": 6000,
            "compress_inputs": False  # No compression for doc generation
        }
    }

    def __init__(self, workflow_id: str):
        """
        Initialize state manager.

        Args:
            workflow_id: Unique workflow identifier
        """
        self.workflow_id = workflow_id
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = 3600  # 1 hour
        self.state_cache: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize Redis connection."""
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("✅ OptimizedStateManager connected to Redis")
            except Exception as e:
                logger.warning(f"⚠️  Redis unavailable, using in-memory cache: {e}")
                self.redis_client = None

    async def get_compact_state(
        self,
        agent_name: str,
        model_context_window: int = 8000
    ) -> Dict[str, Any]:
        """
        Get compact state view for specific agent.

        Returns only the data this agent needs, compressed to fit
        within its token budget.

        Args:
            agent_name: Name of the agent requesting state
            model_context_window: Context window size of the LLM

        Returns:
            Compact state dictionary
        """
        await self.initialize()

        # Get agent requirements
        agent_config = self.AGENT_STATE_REQUIREMENTS.get(agent_name, {})
        max_tokens = agent_config.get("max_tokens", 2000)
        compress_inputs = agent_config.get("compress_inputs", True)
        required_inputs = agent_config.get("inputs", [])

        logger.info(f"📦 Getting compact state for {agent_name} (max {max_tokens} tokens)")

        # Get full state from cache
        full_state = await self._get_cached_state()

        # Build compact state with only required fields
        compact_state = {}
        current_tokens = 0

        for field in required_inputs:
            if field == "all":
                # Agent 6 needs everything (but still within budget)
                compact_state = full_state.copy()
                break

            if field in full_state:
                value = full_state[field]

                # Compress if needed
                if compress_inputs and isinstance(value, str):
                    field_tokens = count_tokens(value)

                    # If this field alone exceeds 30% of budget, compress it
                    max_field_tokens = int(max_tokens * 0.3)

                    if field_tokens > max_field_tokens:
                        logger.info(f"   Compressing '{field}': {field_tokens} → {max_field_tokens} tokens")
                        value = compress_text(value, max_field_tokens, method="extractive")
                        field_tokens = count_tokens(value)

                compact_state[field] = value
                current_tokens += count_tokens(str(value))

                # Check if we're approaching budget
                if current_tokens > max_tokens * 0.9:
                    logger.warning(f"⚠️  Approaching token budget for {agent_name}: {current_tokens}/{max_tokens}")
                    break

        # Add summary fields (compressed versions of large outputs)
        if "requirements" in full_state and "requirements_summary" not in compact_state:
            requirements = full_state["requirements"]
            if isinstance(requirements, str):
                summary = compress_text(requirements, 200, method="extractive")
                compact_state["requirements_summary"] = summary

        if "eda_report" in full_state and "eda_summary" not in compact_state:
            eda = full_state["eda_report"]
            if isinstance(eda, str):
                summary = compress_text(eda, 150, method="extractive")
                compact_state["eda_summary"] = summary

        if "complexity_assessment" in full_state and "complexity_summary" not in compact_state:
            complexity = full_state["complexity_assessment"]
            if isinstance(complexity, str):
                summary = compress_text(complexity, 100, method="extractive")
                compact_state["complexity_summary"] = summary

        logger.info(f"✅ Compact state for {agent_name}: {current_tokens} tokens, {len(compact_state)} fields")

        return compact_state

    async def store_result(
        self,
        agent_name: str,
        result_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Store agent result in state cache.

        Args:
            agent_name: Name of the agent
            result_data: Data to store
            ttl: Time-to-live in seconds (optional)
        """
        await self.initialize()

        logger.info(f"💾 Storing result for {agent_name}")

        # Update local cache
        self.state_cache[agent_name] = result_data

        # Also update full state cache
        full_state = await self._get_cached_state()
        full_state.update(result_data)

        # Store in Redis
        if self.redis_client:
            try:
                cache_key = f"workflow_state:{self.workflow_id}"
                await self.redis_client.setex(
                    cache_key,
                    ttl or self.cache_ttl,
                    json.dumps(full_state)
                )
                logger.info(f"✅ Stored state in Redis (TTL: {ttl or self.cache_ttl}s)")
            except Exception as e:
                logger.warning(f"⚠️  Failed to store in Redis: {e}")

    async def get_full_state(self) -> Dict[str, Any]:
        """
        Get full workflow state (for Agent 6 doc generation).

        Returns:
            Complete state dictionary with all agent outputs
        """
        await self.initialize()

        logger.info("📦 Getting full workflow state")

        full_state = await self._get_cached_state()

        total_tokens = sum(count_tokens(str(v)) for v in full_state.values())
        logger.info(f"✅ Full state: {total_tokens} tokens, {len(full_state)} fields")

        return full_state

    async def _get_cached_state(self) -> Dict[str, Any]:
        """
        Get state from cache (Redis or memory).

        Returns:
            Cached state dictionary
        """
        # Try Redis first
        if self.redis_client:
            try:
                cache_key = f"workflow_state:{self.workflow_id}"
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"⚠️  Redis get failed: {e}")

        # Fallback to memory cache
        return self.state_cache.copy()

    async def clear_cache(self):
        """Clear workflow state cache."""
        await self.initialize()

        logger.info(f"🗑️  Clearing cache for workflow {self.workflow_id}")

        # Clear Redis
        if self.redis_client:
            try:
                cache_key = f"workflow_state:{self.workflow_id}"
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"⚠️  Redis delete failed: {e}")

        # Clear memory
        self.state_cache.clear()

        logger.info("✅ Cache cleared")

    async def get_state_summary(self) -> Dict[str, Any]:
        """
        Get summary of current workflow state.

        Returns:
            Summary with token counts and field info
        """
        await self.initialize()

        full_state = await self._get_cached_state()

        summary = {
            "workflow_id": self.workflow_id,
            "total_fields": len(full_state),
            "fields": {},
            "total_tokens": 0
        }

        for key, value in full_state.items():
            tokens = count_tokens(str(value))
            summary["fields"][key] = {
                "type": type(value).__name__,
                "tokens": tokens,
                "size_bytes": len(str(value))
            }
            summary["total_tokens"] += tokens

        return summary

    @staticmethod
    def estimate_tokens_for_agent(agent_name: str) -> int:
        """
        Estimate token budget for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Estimated token count
        """
        config = OptimizedStateManager.AGENT_STATE_REQUIREMENTS.get(agent_name, {})
        return config.get("max_tokens", 2000)


async def get_state_manager(workflow_id: str) -> OptimizedStateManager:
    """
    Factory function to get initialized state manager.

    Args:
        workflow_id: Unique workflow identifier

    Returns:
        Initialized OptimizedStateManager instance
    """
    manager = OptimizedStateManager(workflow_id)
    await manager.initialize()
    return manager
