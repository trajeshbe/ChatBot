"""
MCP Admin API Routes

Provides RESTful API endpoints for managing MCP (Model Context Protocol) integration:
- Provider: Manage our MCP server that exposes tools to external clients
- Consumer: Manage connections to external MCP servers
- Monitoring: Health checks, statistics, and server status
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP Management"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class MCPServerStatus(BaseModel):
    """MCP Server (Provider) status"""
    enabled: bool
    server_name: str
    version: str
    transport: str
    host: str
    port: int
    tools_exposed: int
    running: bool


class ExternalMCPServerStatus(BaseModel):
    """External MCP server (Consumer) status"""
    server_id: str
    name: str
    enabled: bool
    connected: bool
    transport: str
    tools_imported: int
    tools: List[str]
    error: Optional[str] = None


class MCPStatistics(BaseModel):
    """Overall MCP statistics"""
    total_servers: int
    enabled_servers: int
    connected_servers: int
    disconnected_servers: int
    total_external_tools: int
    servers_with_errors: int
    health_check_timestamp: str


class HealthCheckResult(BaseModel):
    """Health check result for a server"""
    server_id: str
    name: str
    healthy: bool
    enabled: bool
    connected: bool
    tools_imported: int
    error: Optional[str] = None
    status: str
    timestamp: str


class EnableServerRequest(BaseModel):
    """Request to enable/disable a server"""
    enabled: bool = Field(description="True to enable, False to disable")


class ReconnectResult(BaseModel):
    """Result of reconnection attempt"""
    attempted: int
    successful: int
    failed: int
    servers: List[Dict[str, Any]]


# ============================================================================
# Global MCP instances (initialized at startup)
# ============================================================================

_mcp_server_instance = None
_mcp_client_manager_instance = None
_mcp_server_registry_instance = None


def initialize_mcp_instances(mcp_server, mcp_client, mcp_registry):
    """
    Initialize global MCP instances

    This should be called during application startup to inject dependencies.
    """
    global _mcp_server_instance, _mcp_client_manager_instance, _mcp_server_registry_instance
    _mcp_server_instance = mcp_server
    _mcp_client_manager_instance = mcp_client
    _mcp_server_registry_instance = mcp_registry


def get_mcp_server():
    """Get MCP Server instance"""
    if _mcp_server_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP Server not initialized"
        )
    return _mcp_server_instance


def get_mcp_client():
    """Get MCP Client Manager instance"""
    if _mcp_client_manager_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP Client Manager not initialized"
        )
    return _mcp_client_manager_instance


def get_mcp_registry():
    """Get MCP Server Registry instance"""
    if _mcp_server_registry_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP Server Registry not initialized"
        )
    return _mcp_server_registry_instance


# ============================================================================
# Provider Endpoints (Our MCP Server)
# ============================================================================

@router.get(
    "/provider/status",
    response_model=MCPServerStatus,
    summary="Get MCP Server (Provider) status",
    description="Returns the status of our MCP server that exposes tools to external clients"
)
async def get_provider_status():
    """Get MCP Server (Provider) status"""
    try:
        mcp_server = get_mcp_server()
        status_info = mcp_server.get_status()

        return MCPServerStatus(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider status: {str(e)}"
        )


@router.post(
    "/provider/enable",
    response_model=MCPServerStatus,
    summary="Enable MCP Server (Provider)",
    description="Enable our MCP server to start exposing tools to external clients"
)
async def enable_provider():
    """Enable MCP Server (Provider)"""
    try:
        mcp_server = get_mcp_server()
        await mcp_server.enable()

        status_info = mcp_server.get_status()
        logger.info(f"MCP Server (Provider) enabled: {status_info}")

        return MCPServerStatus(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable provider: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable provider: {str(e)}"
        )


@router.post(
    "/provider/disable",
    response_model=MCPServerStatus,
    summary="Disable MCP Server (Provider)",
    description="Disable our MCP server to stop exposing tools to external clients"
)
async def disable_provider():
    """Disable MCP Server (Provider)"""
    try:
        mcp_server = get_mcp_server()
        await mcp_server.disable()

        status_info = mcp_server.get_status()
        logger.info(f"MCP Server (Provider) disabled: {status_info}")

        return MCPServerStatus(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable provider: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable provider: {str(e)}"
        )


@router.get(
    "/provider/connection-info",
    summary="Get connection info for external clients",
    description="Get connection information that external MCP clients can use to connect to our server"
)
async def get_provider_connection_info() -> Dict[str, str]:
    """Get connection information for external clients"""
    try:
        mcp_server = get_mcp_server()
        connection_info = mcp_server.get_connection_info()

        return connection_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection info: {str(e)}"
        )


# ============================================================================
# Consumer Endpoints (External MCP Servers)
# ============================================================================

@router.get(
    "/consumer/servers",
    response_model=List[ExternalMCPServerStatus],
    summary="List all external MCP servers",
    description="Returns list of all configured external MCP servers (connected and disconnected)"
)
async def list_external_servers():
    """List all external MCP servers"""
    try:
        client_manager = get_mcp_client()
        servers_status = client_manager.get_all_servers_status()

        return [ExternalMCPServerStatus(**server) for server in servers_status]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list external servers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list external servers: {str(e)}"
        )


@router.get(
    "/consumer/servers/{server_id}",
    response_model=ExternalMCPServerStatus,
    summary="Get specific external server status",
    description="Returns status of a specific external MCP server"
)
async def get_external_server_status(server_id: str):
    """Get specific external server status"""
    try:
        client_manager = get_mcp_client()
        server_status = client_manager.get_server_status(server_id)

        if not server_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server not found: {server_id}"
            )

        return ExternalMCPServerStatus(**server_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server status: {str(e)}"
        )


@router.post(
    "/consumer/servers/{server_id}/enable",
    response_model=ExternalMCPServerStatus,
    summary="Enable external MCP server",
    description="Enable and connect to an external MCP server"
)
async def enable_external_server(server_id: str):
    """Enable external MCP server"""
    try:
        client_manager = get_mcp_client()
        await client_manager.enable_server(server_id)

        server_status = client_manager.get_server_status(server_id)
        logger.info(f"External server enabled: {server_id}")

        if not server_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server not found: {server_id}"
            )

        return ExternalMCPServerStatus(**server_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable server {server_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable server: {str(e)}"
        )


@router.post(
    "/consumer/servers/{server_id}/disable",
    response_model=ExternalMCPServerStatus,
    summary="Disable external MCP server",
    description="Disable and disconnect from an external MCP server"
)
async def disable_external_server(server_id: str):
    """Disable external MCP server"""
    try:
        client_manager = get_mcp_client()
        await client_manager.disable_server(server_id)

        server_status = client_manager.get_server_status(server_id)
        logger.info(f"External server disabled: {server_id}")

        if not server_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server not found: {server_id}"
            )

        return ExternalMCPServerStatus(**server_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable server {server_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable server: {str(e)}"
        )


@router.get(
    "/consumer/servers/{server_id}/tools",
    summary="List tools from external server",
    description="Returns list of tools imported from a specific external MCP server"
)
async def list_server_tools(server_id: str) -> List[str]:
    """List tools from external server"""
    try:
        registry = get_mcp_registry()
        tools = registry.get_tools_by_server(server_id)

        return tools

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tools for {server_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


# ============================================================================
# Monitoring Endpoints
# ============================================================================

@router.get(
    "/health",
    summary="Overall MCP health check",
    description="Returns overall health status of MCP integration (provider + all consumers)"
)
async def get_overall_health() -> Dict[str, Any]:
    """Overall MCP health check"""
    try:
        mcp_server = get_mcp_server()
        registry = get_mcp_registry()

        # Provider status
        provider_status = mcp_server.get_status()

        # Consumer health checks
        consumer_health = await registry.health_check_all()

        return {
            "provider": provider_status,
            "consumers": consumer_health,
            "overall_healthy": provider_status["enabled"] and all(
                h["healthy"] for h in consumer_health if h.get("enabled", False)
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get overall health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overall health: {str(e)}"
        )


@router.get(
    "/health/{server_id}",
    response_model=HealthCheckResult,
    summary="Health check for specific external server",
    description="Perform health check on a specific external MCP server"
)
async def health_check_server(server_id: str):
    """Health check for specific external server"""
    try:
        registry = get_mcp_registry()
        health_result = await registry.health_check(server_id)

        if health_result.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server not found: {server_id}"
            )

        return HealthCheckResult(**health_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to health check {server_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to health check server: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=MCPStatistics,
    summary="Get MCP statistics",
    description="Returns overall statistics for all MCP servers (provider + consumers)"
)
async def get_statistics():
    """Get MCP statistics"""
    try:
        registry = get_mcp_registry()
        stats = registry.get_server_statistics()

        return MCPStatistics(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post(
    "/consumer/reconnect-failed",
    response_model=ReconnectResult,
    summary="Reconnect failed servers",
    description="Attempt to reconnect all failed external MCP servers"
)
async def reconnect_failed_servers():
    """Reconnect failed servers"""
    try:
        registry = get_mcp_registry()
        result = await registry.reconnect_failed_servers()

        return ReconnectResult(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reconnect servers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reconnect servers: {str(e)}"
        )
