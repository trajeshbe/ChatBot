"""
Tool Usage Statistics API Routes

Provides endpoints for retrieving tool usage statistics and analytics.
Used by the Evaluation Dashboard to display tool usage insights.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from app.tier_1.infrastructure.database import get_db
from app.tier_1.platform_services.tool_usage_tracker import tool_tracker, ToolCategory
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tool-stats", tags=["Tool Statistics"])


@router.get("/summary")
async def get_tool_statistics_summary(
    category: Optional[str] = Query(None, description="Filter by tool category"),
    tool_name: Optional[str] = Query(None, description="Filter by specific tool name"),
    days: int = Query(7, description="Number of days to include (default: 7)"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated tool usage statistics.

    Returns comprehensive statistics for all tools including:
    - Total invocations
    - Success/failure rates
    - Performance metrics (latency, P95, etc.)
    - Resource usage (tokens, cost)
    - Quality scores

    Query parameters:
    - category: Filter by tool category (document_processing, web_scraping, rag_service, llm_service, mcp_tool)
    - tool_name: Filter by specific tool (docling, playwright, gpt-4, etc.)
    - days: Number of days to include in stats (default: 7)
    - session_id: Filter by session ID
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get statistics
        stats = await tool_tracker.get_tool_statistics(
            db=db,
            category=category,
            tool_name=tool_name,
            start_date=start_date,
            end_date=end_date,
            session_id=session_id
        )

        # Group by category for easier consumption
        by_category = {}
        for stat in stats:
            cat = stat['tool_category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(stat)

        return {
            'summary': {
                'total_tools': len(stats),
                'total_invocations': sum(s['total_invocations'] for s in stats),
                'total_successful': sum(s['successful_invocations'] for s in stats),
                'total_failed': sum(s['failed_invocations'] for s in stats),
                'total_tokens_used': sum(s['total_tokens_used'] or 0 for s in stats),
                'total_cost_usd': sum(s['total_cost_usd'] or 0 for s in stats),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                }
            },
            'by_category': by_category,
            'all_tools': stats
        }

    except Exception as e:
        logger.error(f"Error getting tool statistics: {e}")
        return {
            'summary': {
                'total_tools': 0,
                'total_invocations': 0,
                'error': str(e)
            },
            'by_category': {},
            'all_tools': []
        }


@router.get("/timeline")
async def get_tool_usage_timeline(
    category: Optional[str] = Query(None, description="Filter by tool category"),
    tool_name: Optional[str] = Query(None, description="Filter by specific tool name"),
    days: int = Query(7, description="Number of days to include (default: 7)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tool usage over time (daily aggregation).

    Returns time series data suitable for charting.

    Query parameters:
    - category: Filter by tool category
    - tool_name: Filter by specific tool
    - days: Number of days to include (default: 7)
    """
    try:
        timeline = await tool_tracker.get_tool_usage_timeline(
            db=db,
            category=category,
            tool_name=tool_name,
            days=days
        )

        return {
            'timeline': timeline,
            'days': days
        }

    except Exception as e:
        logger.error(f"Error getting tool usage timeline: {e}")
        return {
            'timeline': [],
            'days': days,
            'error': str(e)
        }


@router.get("/categories")
async def get_tool_categories():
    """
    Get list of all tool categories.

    Returns the predefined tool categories for filtering.
    """
    return {
        'categories': [
            {
                'id': ToolCategory.DOCUMENT_PROCESSING,
                'name': 'Document Processing',
                'description': 'PDF, DOCX, OCR tools (Docling, Tesseract, PyPDF2, etc.)',
                'tools': [
                    'docling',
                    'tesseract_ocr',
                    'pypdf2',
                    'python_docx',
                    'python_pptx',
                    'openpyxl'
                ]
            },
            {
                'id': ToolCategory.WEB_SCRAPING,
                'name': 'Web Scraping',
                'description': 'Browser automation and content extraction',
                'tools': [
                    'playwright',
                    'ultra_smart_extractor',
                    'template_extractor',
                    'css_extractor',
                    'xpath_extractor',
                    'llm_extractor'
                ]
            },
            {
                'id': ToolCategory.RAG_SERVICE,
                'name': 'RAG Services',
                'description': 'Retrieval and ranking components',
                'tools': [
                    'vector_search',
                    'cross_encoder_reranker',
                    'query_reformulation',
                    'query_classifier',
                    'quality_metrics'
                ]
            },
            {
                'id': ToolCategory.EMBEDDING,
                'name': 'Embedding Services',
                'description': 'Text embedding generation',
                'tools': [
                    'sentence_transformers',
                    'all-MiniLM-L6-v2',
                    'bge-base-en-v1.5'
                ]
            },
            {
                'id': ToolCategory.LLM_SERVICE,
                'name': 'LLM Services',
                'description': 'Language model inference',
                'tools': [
                    'gpt-4',
                    'gpt-3.5-turbo',
                    'claude-3-opus',
                    'claude-3-sonnet',
                    'ollama/mistral',
                    'ollama/llama2'
                ]
            },
            {
                'id': ToolCategory.CACHING,
                'name': 'Caching Services',
                'description': 'Semantic caching with Redis',
                'tools': [
                    'redis_cache',
                    'semantic_cache'
                ]
            },
            {
                'id': ToolCategory.MCP_TOOL,
                'name': 'MCP Tools',
                'description': 'External MCP server tools',
                'tools': []  # Dynamically populated based on connected servers
            }
        ]
    }


@router.get("/top-tools")
async def get_top_tools(
    limit: int = Query(10, description="Number of top tools to return"),
    days: int = Query(7, description="Number of days to include"),
    sort_by: str = Query("invocations", description="Sort by: invocations, latency, cost, quality"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top N tools by various metrics.

    Query parameters:
    - limit: Number of tools to return (default: 10)
    - days: Number of days to include (default: 7)
    - sort_by: Sort criteria (invocations, latency, cost, quality)
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get all statistics
        stats = await tool_tracker.get_tool_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date
        )

        # Sort based on criteria
        if sort_by == "latency":
            stats.sort(key=lambda x: x.get('avg_latency_ms', float('inf')))
        elif sort_by == "cost":
            stats.sort(key=lambda x: x.get('total_cost_usd', 0), reverse=True)
        elif sort_by == "quality":
            stats.sort(key=lambda x: x.get('avg_quality_score', 0), reverse=True)
        else:  # invocations
            stats.sort(key=lambda x: x.get('total_invocations', 0), reverse=True)

        return {
            'top_tools': stats[:limit],
            'sort_by': sort_by,
            'days': days,
            'limit': limit
        }

    except Exception as e:
        logger.error(f"Error getting top tools: {e}")
        return {
            'top_tools': [],
            'error': str(e)
        }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'tool-stats'
    }
