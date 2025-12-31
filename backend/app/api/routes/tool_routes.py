"""
Tool Discovery API Routes

Provides endpoints for discovering and exploring available AI agent tools.
Exposes built-in tools and dynamically imported MCP tools for frontend visibility.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from collections import Counter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tools", tags=["Tool Discovery"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ToolInfo(BaseModel):
    """Detailed information about a tool"""
    tool_id: str = Field(description="Unique identifier for the tool")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="Detailed description for LLM and users")
    input_schema: Dict[str, Any] = Field(description="JSON schema for tool parameters")
    tags: List[str] = Field(description="Categorization tags")
    source: str = Field(description="Source of tool: built-in, mcp, custom")
    enabled: bool = Field(description="Whether tool is currently enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolSummary(BaseModel):
    """Summary information about a tool"""
    tool_id: str
    name: str
    description: str
    tags: List[str]
    source: str
    enabled: bool


class ToolListResponse(BaseModel):
    """Response for tool listing endpoint"""
    total: int = Field(description="Total number of tools")
    enabled: int = Field(description="Number of enabled tools")
    disabled: int = Field(description="Number of disabled tools")
    tools: List[ToolSummary] = Field(description="List of tools")
    filters_applied: Dict[str, Any] = Field(description="Filters that were applied")


class ToolCategory(BaseModel):
    """Tool category/tag information"""
    tag: str = Field(description="Category/tag name")
    tool_count: int = Field(description="Number of tools in this category")
    sample_tools: List[str] = Field(description="Sample tool IDs (up to 5)")


class ToolStatistics(BaseModel):
    """Overall tool statistics"""
    total_tools: int
    enabled_tools: int
    disabled_tools: int
    builtin_tools: int
    mcp_tools: int
    custom_tools: int
    total_tags: int
    top_tags: List[Dict[str, Any]]


class EnableToolRequest(BaseModel):
    """Request to enable/disable a tool"""
    enabled: bool = Field(description="True to enable, False to disable")


# ============================================================================
# Helper Functions
# ============================================================================

def get_tool_registry():
    """Get the global tool registry instance"""
    try:
        from app.agents.tool_registry import tool_registry
        return tool_registry
    except ImportError as e:
        logger.error(f"Failed to import tool registry: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tool registry not available"
        )


# ============================================================================
# Tool Discovery Endpoints
# ============================================================================

@router.get(
    "",
    response_model=ToolListResponse,
    summary="List all available tools",
    description="""
    Returns a list of all available tools (built-in + MCP imported).
    Supports filtering by source, tags, and enabled status.
    """
)
async def list_tools(
    enabled_only: bool = Query(False, description="Only return enabled tools"),
    source: Optional[str] = Query(None, description="Filter by source (built-in, mcp, custom)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in name/description")
):
    """List all available tools with optional filtering"""
    try:
        registry = get_tool_registry()

        # Get all tools (apply enabled filter)
        all_tools = registry.get_all_tools(enabled_only=enabled_only)

        # Apply source filter
        if source:
            all_tools = [t for t in all_tools if t.source == source]

        # Apply tag filter
        if tag:
            all_tools = [t for t in all_tools if tag in t.tags]

        # Apply search filter
        if search:
            search_lower = search.lower()
            all_tools = [
                t for t in all_tools
                if search_lower in t.name.lower() or search_lower in t.description.lower()
            ]

        # Convert to summaries
        tool_summaries = [
            ToolSummary(
                tool_id=t.tool_id,
                name=t.name,
                description=t.description,
                tags=t.tags,
                source=t.source,
                enabled=t.enabled
            )
            for t in all_tools
        ]

        # Count enabled/disabled
        enabled_count = sum(1 for t in all_tools if t.enabled)
        disabled_count = len(all_tools) - enabled_count

        return ToolListResponse(
            total=len(all_tools),
            enabled=enabled_count,
            disabled=disabled_count,
            tools=tool_summaries,
            filters_applied={
                "enabled_only": enabled_only,
                "source": source,
                "tag": tag,
                "search": search
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get(
    "/{tool_id}",
    response_model=ToolInfo,
    summary="Get detailed information about a specific tool",
    description="Returns complete information about a tool including schema and metadata"
)
async def get_tool(tool_id: str):
    """Get detailed information about a specific tool"""
    try:
        registry = get_tool_registry()
        tool = registry.get_tool(tool_id)

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {tool_id}"
            )

        return ToolInfo(
            tool_id=tool.tool_id,
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            tags=tool.tags,
            source=tool.source,
            enabled=tool.enabled,
            metadata=tool.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool: {str(e)}"
        )


@router.get(
    "/{tool_id}/schema",
    summary="Get tool input schema",
    description="Returns the JSON schema for tool parameters (useful for form generation)"
)
async def get_tool_schema(tool_id: str) -> Dict[str, Any]:
    """Get tool input schema"""
    try:
        registry = get_tool_registry()
        tool = registry.get_tool(tool_id)

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {tool_id}"
            )

        return {
            "tool_id": tool.tool_id,
            "name": tool.name,
            "input_schema": tool.input_schema,
            "openai_format": tool.to_openai_function()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schema for {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool schema: {str(e)}"
        )


# ============================================================================
# Tool Categories / Tags
# ============================================================================

@router.get(
    "/categories/list",
    response_model=List[ToolCategory],
    summary="List all tool categories",
    description="Returns all available tool categories/tags with tool counts"
)
async def list_categories(
    enabled_only: bool = Query(True, description="Only count enabled tools")
):
    """List all tool categories/tags"""
    try:
        registry = get_tool_registry()
        all_tools = registry.get_all_tools(enabled_only=enabled_only)

        # Count tools per tag
        tag_counts = Counter()
        tag_tool_samples = {}

        for tool in all_tools:
            for tag in tool.tags:
                tag_counts[tag] += 1
                if tag not in tag_tool_samples:
                    tag_tool_samples[tag] = []
                if len(tag_tool_samples[tag]) < 5:
                    tag_tool_samples[tag].append(tool.tool_id)

        # Build category list
        categories = [
            ToolCategory(
                tag=tag,
                tool_count=count,
                sample_tools=tag_tool_samples[tag]
            )
            for tag, count in tag_counts.most_common()
        ]

        return categories

    except Exception as e:
        logger.error(f"Failed to list categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {str(e)}"
        )


@router.get(
    "/categories/{category}",
    response_model=List[ToolSummary],
    summary="List tools in a category",
    description="Returns all tools tagged with the specified category"
)
async def list_tools_by_category(
    category: str,
    enabled_only: bool = Query(True, description="Only return enabled tools")
):
    """List tools in a specific category"""
    try:
        registry = get_tool_registry()
        tools = registry.get_tools_by_tag(category, enabled_only=enabled_only)

        if not tools:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No tools found in category: {category}"
            )

        return [
            ToolSummary(
                tool_id=t.tool_id,
                name=t.name,
                description=t.description,
                tags=t.tags,
                source=t.source,
                enabled=t.enabled
            )
            for t in tools
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tools for category {category}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools by category: {str(e)}"
        )


# ============================================================================
# Tool Statistics
# ============================================================================

@router.get(
    "/statistics",
    response_model=ToolStatistics,
    summary="Get tool statistics",
    description="Returns overall statistics about available tools"
)
async def get_tool_statistics():
    """Get overall tool statistics"""
    try:
        registry = get_tool_registry()

        all_tools = registry.get_all_tools(enabled_only=False)
        enabled_tools = [t for t in all_tools if t.enabled]

        # Count by source
        builtin_count = sum(1 for t in all_tools if t.source == "built-in")
        mcp_count = sum(1 for t in all_tools if t.source == "mcp")
        custom_count = sum(1 for t in all_tools if t.source == "custom")

        # Get top tags
        tag_counts = Counter()
        for tool in all_tools:
            for tag in tool.tags:
                tag_counts[tag] += 1

        top_tags = [
            {"tag": tag, "count": count}
            for tag, count in tag_counts.most_common(10)
        ]

        return ToolStatistics(
            total_tools=len(all_tools),
            enabled_tools=len(enabled_tools),
            disabled_tools=len(all_tools) - len(enabled_tools),
            builtin_tools=builtin_count,
            mcp_tools=mcp_count,
            custom_tools=custom_count,
            total_tags=len(tag_counts),
            top_tags=top_tags
        )

    except Exception as e:
        logger.error(f"Failed to get tool statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool statistics: {str(e)}"
        )


# ============================================================================
# Tool Management (Enable/Disable)
# ============================================================================

@router.post(
    "/{tool_id}/enable",
    response_model=ToolInfo,
    summary="Enable a tool",
    description="Enable a tool to make it available to the AI agent"
)
async def enable_tool(tool_id: str):
    """Enable a tool"""
    try:
        registry = get_tool_registry()

        tool = registry.get_tool(tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {tool_id}"
            )

        registry.enable_tool(tool_id)

        # Get updated tool info
        updated_tool = registry.get_tool(tool_id)

        logger.info(f"Tool enabled: {tool_id}")

        return ToolInfo(
            tool_id=updated_tool.tool_id,
            name=updated_tool.name,
            description=updated_tool.description,
            input_schema=updated_tool.input_schema,
            tags=updated_tool.tags,
            source=updated_tool.source,
            enabled=updated_tool.enabled,
            metadata=updated_tool.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable tool: {str(e)}"
        )


@router.post(
    "/{tool_id}/disable",
    response_model=ToolInfo,
    summary="Disable a tool",
    description="Disable a tool to make it unavailable to the AI agent"
)
async def disable_tool(tool_id: str):
    """Disable a tool"""
    try:
        registry = get_tool_registry()

        tool = registry.get_tool(tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {tool_id}"
            )

        registry.disable_tool(tool_id)

        # Get updated tool info
        updated_tool = registry.get_tool(tool_id)

        logger.info(f"Tool disabled: {tool_id}")

        return ToolInfo(
            tool_id=updated_tool.tool_id,
            name=updated_tool.name,
            description=updated_tool.description,
            input_schema=updated_tool.input_schema,
            tags=updated_tool.tags,
            source=updated_tool.source,
            enabled=updated_tool.enabled,
            metadata=updated_tool.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable tool: {str(e)}"
        )


# ============================================================================
# LLM-Formatted Tools (For AI Agent)
# ============================================================================

@router.get(
    "/llm/format",
    summary="Get tools in LLM format",
    description="""
    Returns all tools formatted for LLM function calling (OpenAI format).
    This endpoint is used by the AI agent to select appropriate tools.
    """
)
async def get_tools_for_llm(
    enabled_only: bool = Query(True, description="Only return enabled tools")
) -> List[Dict[str, Any]]:
    """Get tools formatted for LLM function calling"""
    try:
        registry = get_tool_registry()
        tools_for_llm = registry.get_tools_for_llm(enabled_only=enabled_only)

        return tools_for_llm

    except Exception as e:
        logger.error(f"Failed to get tools for LLM: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tools for LLM: {str(e)}"
        )
