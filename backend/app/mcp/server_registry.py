"""
MCP Server Registry

Provides additional utilities for managing external MCP servers,
including server discovery, health checks, and status monitoring.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPServerRegistry:
    """
    Registry for tracking and managing external MCP servers

    This complements MCPClientManager by providing additional
    management and monitoring capabilities.
    """

    def __init__(self, client_manager):
        """
        Initialize server registry

        Args:
            client_manager: MCPClientManager instance
        """
        self.client_manager = client_manager
        self.health_checks: Dict[str, Dict[str, Any]] = {}

    def list_available_servers(self) -> List[Dict[str, Any]]:
        """List all available MCP servers"""
        servers = []

        for server_id, server in self.client_manager.servers.items():
            servers.append({
                "server_id": server_id,
                "name": server.name,
                "enabled": server.enabled,
                "connected": server.connected,
                "transport": server.transport,
                "tools_count": len(server.tools_imported),
                "tools": server.tools_imported,
                "error": server.error
            })

        return servers

    def get_server_by_id(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server information by ID"""
        return self.client_manager.get_server_status(server_id)

    def get_enabled_servers(self) -> List[Dict[str, Any]]:
        """Get only enabled servers"""
        return [
            s for s in self.list_available_servers()
            if s["enabled"]
        ]

    def get_connected_servers(self) -> List[Dict[str, Any]]:
        """Get only connected servers"""
        return [
            s for s in self.list_available_servers()
            if s["connected"]
        ]

    async def health_check(self, server_id: str) -> Dict[str, Any]:
        """
        Perform health check on an MCP server

        Args:
            server_id: ID of server to check

        Returns:
            Health check results
        """
        server = self.client_manager.servers.get(server_id)

        if not server:
            return {
                "server_id": server_id,
                "healthy": False,
                "status": "not_found",
                "timestamp": datetime.utcnow().isoformat()
            }

        health_status = {
            "server_id": server_id,
            "name": server.name,
            "enabled": server.enabled,
            "connected": server.connected,
            "healthy": server.connected and server.enabled,
            "tools_imported": len(server.tools_imported),
            "error": server.error,
            "status": "healthy" if server.connected else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store health check result
        self.health_checks[server_id] = health_status

        return health_status

    async def health_check_all(self) -> List[Dict[str, Any]]:
        """Perform health check on all servers"""
        results = []

        for server_id in self.client_manager.servers.keys():
            health = await self.health_check(server_id)
            results.append(health)

        return results

    def get_tools_by_server(self, server_id: str) -> List[str]:
        """Get list of tools provided by a specific server"""
        server = self.client_manager.servers.get(server_id)

        if not server:
            return []

        return server.tools_imported

    def get_server_statistics(self) -> Dict[str, Any]:
        """Get overall statistics for all MCP servers"""
        servers = self.list_available_servers()

        total_servers = len(servers)
        enabled_servers = len([s for s in servers if s["enabled"]])
        connected_servers = len([s for s in servers if s["connected"]])
        total_external_tools = sum(s["tools_count"] for s in servers)

        return {
            "total_servers": total_servers,
            "enabled_servers": enabled_servers,
            "connected_servers": connected_servers,
            "disconnected_servers": enabled_servers - connected_servers,
            "total_external_tools": total_external_tools,
            "servers_with_errors": len([s for s in servers if s["error"]]),
            "health_check_timestamp": datetime.utcnow().isoformat()
        }

    async def reconnect_failed_servers(self) -> Dict[str, Any]:
        """Attempt to reconnect all failed servers"""
        results = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "servers": []
        }

        for server_id, server in self.client_manager.servers.items():
            if server.enabled and not server.connected:
                results["attempted"] += 1

                success = await self.client_manager.connect_server(server_id)

                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

                results["servers"].append({
                    "server_id": server_id,
                    "success": success,
                    "error": server.error
                })

        logger.info(
            f"Reconnection attempt: {results['successful']}/{results['attempted']} successful"
        )

        return results


# Global registry instance
_mcp_server_registry: Optional[MCPServerRegistry] = None


def get_mcp_server_registry(client_manager) -> MCPServerRegistry:
    """Get or create MCP server registry instance"""
    global _mcp_server_registry

    if _mcp_server_registry is None:
        _mcp_server_registry = MCPServerRegistry(client_manager)

    return _mcp_server_registry
