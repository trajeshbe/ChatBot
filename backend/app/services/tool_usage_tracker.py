"""
Tool Usage Tracking Service

Tracks usage statistics for all tools/services in the system:
- Document processing tools (Docling, Tesseract OCR, PyPDF2, etc.)
- Web scraping tools (Playwright, Ultra Smart Extractor, Template Extraction, etc.)
- RAG services (Embedding, Reranking, Query Reformulation, Vector Search, etc.)
- LLM services (OpenAI, Anthropic, Ollama, etc.)
- MCP tools (External MCP servers)

Provides insights into:
- Tool usage patterns
- Performance metrics per tool
- Success/failure rates
- Cost attribution
- Tool contribution to overall quality
"""

from typing import Dict, List, Optional, Any
import logging
import time
import uuid
import json
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ToolCategory:
    """Tool categories for classification"""
    DOCUMENT_PROCESSING = "document_processing"
    WEB_SCRAPING = "web_scraping"
    RAG_SERVICE = "rag_service"
    LLM_SERVICE = "llm_service"
    MCP_TOOL = "mcp_tool"
    EMBEDDING = "embedding"
    CACHING = "caching"
    ORCHESTRATION = "orchestration"


class ToolUsageTracker:
    """
    Central service for tracking tool usage across the application.

    Usage:
        async with tool_tracker.track_tool_usage(
            category=ToolCategory.DOCUMENT_PROCESSING,
            tool_name="docling",
            operation="parse_pdf",
            session_id=session_id
        ) as tracker:
            result = await process_document(file_path)
            tracker.set_output_size(len(result))
            tracker.set_quality_score(0.95)
    """

    async def track_tool_usage(
        self,
        category: str,
        tool_name: str,
        operation: str,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        tool_version: Optional[str] = None,
        input_size: Optional[int] = None
    ) -> "ToolUsageContext":
        """
        Context manager for tracking tool usage.

        Automatically records start time, end time, success/failure, and metrics.
        """
        return ToolUsageContext(
            category=category,
            tool_name=tool_name,
            operation=operation,
            db=db,
            session_id=session_id,
            user_id=user_id,
            tool_version=tool_version,
            input_size=input_size
        )

    async def record_tool_usage(
        self,
        category: str,
        tool_name: str,
        operation: str,
        latency_ms: float,
        success: bool,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        tool_version: Optional[str] = None,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        quality_score: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Record a tool usage event directly (without context manager).

        Use this for simple cases where you don't need the context manager.
        """
        try:
            query = sql_text("""
                INSERT INTO tool_usage_stats (
                    tool_category, tool_name, tool_version, session_id, user_id,
                    operation, input_size, output_size, latency_ms, success,
                    error_message, tokens_used, cost_usd, quality_score, metadata
                ) VALUES (
                    :category, :tool_name, :tool_version, :session_id, :user_id,
                    :operation, :input_size, :output_size, :latency_ms, :success,
                    :error_message, :tokens_used, :cost_usd, :quality_score, :metadata
                )
            """)

            await db.execute(query, {
                'category': category,
                'tool_name': tool_name,
                'tool_version': tool_version,
                'session_id': session_id,
                'user_id': user_id,
                'operation': operation,
                'input_size': input_size,
                'output_size': output_size,
                'latency_ms': latency_ms,
                'success': success,
                'error_message': error_message,
                'tokens_used': tokens_used,
                'cost_usd': cost_usd,
                'quality_score': quality_score,
                'metadata': json.dumps(metadata) if metadata else None
            })

            await db.commit()

            logger.debug(
                f"📊 Tool usage tracked: {category}/{tool_name} - {operation} "
                f"({latency_ms:.0f}ms, success={success})"
            )

        except Exception as e:
            logger.error(f"Error tracking tool usage: {e}")
            # Don't fail the main operation if tracking fails
            pass

    async def get_tool_statistics(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        tool_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get aggregated tool usage statistics.

        Args:
            category: Filter by tool category
            tool_name: Filter by specific tool
            start_date: Start of date range
            end_date: End of date range
            session_id: Filter by session

        Returns:
            List of tool statistics with usage counts, performance metrics, etc.
        """
        try:
            # Build dynamic query based on filters
            where_clauses = []
            params = {}

            if category:
                where_clauses.append("tool_category = :category")
                params['category'] = category

            if tool_name:
                where_clauses.append("tool_name = :tool_name")
                params['tool_name'] = tool_name

            if start_date:
                where_clauses.append("created_at >= :start_date")
                params['start_date'] = start_date

            if end_date:
                where_clauses.append("created_at <= :end_date")
                params['end_date'] = end_date

            if session_id:
                where_clauses.append("session_id = :session_id")
                params['session_id'] = session_id

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            query = sql_text(f"""
                SELECT
                    tool_category,
                    tool_name,
                    COUNT(*) as total_invocations,
                    COUNT(*) FILTER (WHERE success = TRUE) as successful_invocations,
                    COUNT(*) FILTER (WHERE success = FALSE) as failed_invocations,
                    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
                    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as median_latency_ms,
                    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as p95_latency_ms,
                    ROUND(MIN(latency_ms)::numeric, 2) as min_latency_ms,
                    ROUND(MAX(latency_ms)::numeric, 2) as max_latency_ms,
                    SUM(tokens_used) as total_tokens_used,
                    ROUND(SUM(cost_usd)::numeric, 4) as total_cost_usd,
                    ROUND(AVG(quality_score)::numeric, 3) as avg_quality_score,
                    ROUND(
                        100.0 * COUNT(*) FILTER (WHERE success = TRUE) / NULLIF(COUNT(*), 0)::numeric,
                        2
                    ) as success_rate_pct,
                    MIN(created_at) as first_used,
                    MAX(created_at) as last_used
                FROM tool_usage_stats
                WHERE {where_clause}
                GROUP BY tool_category, tool_name
                ORDER BY total_invocations DESC
            """)

            result = await db.execute(query, params)
            rows = result.fetchall()

            statistics = []
            for row in rows:
                statistics.append({
                    'tool_category': row[0],
                    'tool_name': row[1],
                    'total_invocations': row[2],
                    'successful_invocations': row[3],
                    'failed_invocations': row[4],
                    'avg_latency_ms': float(row[5]) if row[5] else None,
                    'median_latency_ms': float(row[6]) if row[6] else None,
                    'p95_latency_ms': float(row[7]) if row[7] else None,
                    'min_latency_ms': float(row[8]) if row[8] else None,
                    'max_latency_ms': float(row[9]) if row[9] else None,
                    'total_tokens_used': row[10],
                    'total_cost_usd': float(row[11]) if row[11] else None,
                    'avg_quality_score': float(row[12]) if row[12] else None,
                    'success_rate_pct': float(row[13]) if row[13] else None,
                    'first_used': row[14],
                    'last_used': row[15]
                })

            return statistics

        except Exception as e:
            logger.error(f"Error getting tool statistics: {e}")
            return []

    async def get_tool_usage_timeline(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        tool_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict]:
        """
        Get tool usage over time (daily aggregation).

        Returns time series data for charting.
        """
        try:
            where_clauses = []
            params = {'days': days}

            if category:
                where_clauses.append("tool_category = :category")
                params['category'] = category

            if tool_name:
                where_clauses.append("tool_name = :tool_name")
                params['tool_name'] = tool_name

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            query = sql_text(f"""
                SELECT
                    DATE(created_at) as date,
                    tool_category,
                    tool_name,
                    COUNT(*) as invocations,
                    COUNT(*) FILTER (WHERE success = TRUE) as successful,
                    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms
                FROM tool_usage_stats
                WHERE created_at >= CURRENT_DATE - INTERVAL ':days days'
                  AND {where_clause}
                GROUP BY DATE(created_at), tool_category, tool_name
                ORDER BY date DESC, invocations DESC
            """)

            result = await db.execute(query, params)
            rows = result.fetchall()

            timeline = []
            for row in rows:
                timeline.append({
                    'date': row[0].isoformat() if row[0] else None,
                    'tool_category': row[1],
                    'tool_name': row[2],
                    'invocations': row[3],
                    'successful': row[4],
                    'avg_latency_ms': float(row[5]) if row[5] else None
                })

            return timeline

        except Exception as e:
            logger.error(f"Error getting tool usage timeline: {e}")
            return []


class ToolUsageContext:
    """
    Context manager for tracking a single tool usage event.

    Automatically records start/end time and handles exceptions.
    """

    def __init__(
        self,
        category: str,
        tool_name: str,
        operation: str,
        db: AsyncSession,
        session_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        tool_version: Optional[str] = None,
        input_size: Optional[int] = None
    ):
        self.category = category
        self.tool_name = tool_name
        self.operation = operation
        self.db = db
        self.session_id = session_id
        self.user_id = user_id
        self.tool_version = tool_version
        self.input_size = input_size

        self.start_time = None
        self.output_size = None
        self.tokens_used = None
        self.cost_usd = None
        self.quality_score = None
        self.metadata = {}
        self.success = True
        self.error_message = None

    async def __aenter__(self):
        self.start_time = time.time()
        logger.debug(f"🔧 Tool started: {self.category}/{self.tool_name} - {self.operation}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000

        # Handle exceptions
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)[:500]  # Truncate long errors

        # Record to database
        try:
            query = sql_text("""
                INSERT INTO tool_usage_stats (
                    tool_category, tool_name, tool_version, session_id, user_id,
                    operation, input_size, output_size, latency_ms, success,
                    error_message, tokens_used, cost_usd, quality_score, metadata
                ) VALUES (
                    :category, :tool_name, :tool_version, :session_id, :user_id,
                    :operation, :input_size, :output_size, :latency_ms, :success,
                    :error_message, :tokens_used, :cost_usd, :quality_score, :metadata
                )
            """)

            await self.db.execute(query, {
                'category': self.category,
                'tool_name': self.tool_name,
                'tool_version': self.tool_version,
                'session_id': self.session_id,
                'user_id': self.user_id,
                'operation': self.operation,
                'input_size': self.input_size,
                'output_size': self.output_size,
                'latency_ms': latency_ms,
                'success': self.success,
                'error_message': self.error_message,
                'tokens_used': self.tokens_used,
                'cost_usd': self.cost_usd,
                'quality_score': self.quality_score,
                'metadata': self.metadata
            })

            await self.db.commit()

            status = "✅" if self.success else "❌"
            logger.info(
                f"{status} Tool completed: {self.category}/{self.tool_name} - {self.operation} "
                f"({latency_ms:.0f}ms, success={self.success})"
            )

        except Exception as e:
            logger.error(f"Error recording tool usage: {e}")
            # Don't propagate tracking errors

        # Don't suppress the original exception
        return False

    def set_output_size(self, size: int):
        """Set the output size for this operation"""
        self.output_size = size

    def set_tokens_used(self, tokens: int):
        """Set the number of tokens used (for LLM operations)"""
        self.tokens_used = tokens

    def set_cost(self, cost_usd: float):
        """Set the estimated cost in USD"""
        self.cost_usd = cost_usd

    def set_quality_score(self, score: float):
        """Set the quality/confidence score"""
        self.quality_score = score

    def set_metadata(self, key: str, value: Any):
        """Add custom metadata"""
        self.metadata[key] = value


# Singleton instance
_tool_usage_tracker: Optional[ToolUsageTracker] = None


def get_tool_usage_tracker() -> ToolUsageTracker:
    """Get or create global tool usage tracker instance"""
    global _tool_usage_tracker
    if _tool_usage_tracker is None:
        _tool_usage_tracker = ToolUsageTracker()
    return _tool_usage_tracker


# Convenience alias
tool_tracker = get_tool_usage_tracker()
