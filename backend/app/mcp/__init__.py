"""
MCP (Model Context Protocol) Integration

This module provides bidirectional MCP integration:
1. MCP Server: Expose our 7 tools as an MCP service
2. MCP Client: Consume external MCP servers

Architecture:
- server.py: MCP server implementation (provider)
- client.py: MCP client manager (consumer)
- server_registry.py: Track and manage external MCP servers
- tool_adapters.py: Adapt tools to/from MCP format
- transport.py: HTTP/SSE/stdio transports
"""

from app.mcp.server import ChatbotMCPServer
from app.mcp.client import MCPClientManager
from app.mcp.server_registry import MCPServerRegistry

__all__ = [
    "ChatbotMCPServer",
    "MCPClientManager",
    "MCPServerRegistry",
]
