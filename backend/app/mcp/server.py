"""
MCP Server Implementation (Provider)

Exposes our 7 specialized tools as an MCP service for external clients:
1. document_rag - Document search with semantic similarity
2. smart_extraction - AI-powered web data extraction
3. web_scraper - Basic Playwright web scraping
4. template_extraction - Template-based extraction
5. docling_pdf - Advanced PDF processing
6. ocr - OCR text extraction
7. navigation_agent - Multi-page website navigation
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for MCP server"""
    server_name: str = "chatbot-rag-platform"
    server_version: str = "1.0.0"
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8001
    transport: str = "http"  # "http", "sse", or "stdio"
    description: str = "Enterprise RAG Chatbot Platform with 7 specialized AI tools"


class ChatbotMCPServer:
    """
    MCP Server exposing our tools as an external service

    This allows external clients (Claude Desktop, other apps) to use our tools
    via the Model Context Protocol.
    """

    def __init__(
        self,
        tool_registry,
        config: Optional[MCPServerConfig] = None
    ):
        """
        Initialize MCP server

        Args:
            tool_registry: ToolRegistry instance with registered tools
            config: Server configuration
        """
        self.tool_registry = tool_registry
        self.config = config or MCPServerConfig()
        self.enabled = self.config.enabled

        # MCP SDK will be initialized when available
        self.mcp_server = None

        logger.info(
            f"MCP Server initialized: {self.config.server_name} v{self.config.server_version}"
        )

    async def start(self):
        """Start the MCP server"""
        if not self.enabled:
            logger.info("MCP Server is disabled")
            return

        try:
            # Import MCP SDK (will be added to requirements)
            from mcp.server import Server
            from mcp.server.stdio import stdio_server

            # Create MCP server instance
            self.mcp_server = Server(self.config.server_name)

            # Register all tools from tool registry
            await self._register_tools()

            # Start server based on transport type
            if self.config.transport == "stdio":
                logger.info(f"Starting MCP Server (stdio transport)")
                await stdio_server(self.mcp_server)
            else:
                logger.info(
                    f"Starting MCP Server ({self.config.transport} transport) "
                    f"on {self.config.host}:{self.config.port}"
                )
                # HTTP/SSE transport implementation
                await self._start_http_server()

        except ImportError:
            logger.error(
                "MCP SDK not installed. Install with: pip install mcp"
            )
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}", exc_info=True)
            self.enabled = False

    async def stop(self):
        """Stop the MCP server"""
        if self.mcp_server:
            logger.info("Stopping MCP Server")
            # Cleanup logic here
            self.mcp_server = None

    async def enable(self):
        """Enable MCP server"""
        self.enabled = True
        self.config.enabled = True
        logger.info("MCP Server enabled")
        await self.start()

    async def disable(self):
        """Disable MCP server"""
        self.enabled = False
        self.config.enabled = False
        logger.info("MCP Server disabled")
        await self.stop()

    async def _register_tools(self):
        """Register all tools from tool registry with MCP"""
        if not self.mcp_server:
            return

        # Get all enabled tools from registry
        tools = self.tool_registry.get_all_tools(enabled_only=True)

        logger.info(f"Registering {len(tools)} tools with MCP server")

        for tool in tools:
            try:
                # Register tool with MCP server
                await self._register_single_tool(tool)
                logger.info(f"Registered MCP tool: {tool.tool_id}")
            except Exception as e:
                logger.error(
                    f"Failed to register tool {tool.tool_id}: {e}",
                    exc_info=True
                )

    async def _register_single_tool(self, tool):
        """Register a single tool with MCP server"""
        from mcp.types import Tool as MCPTool

        # Convert our tool to MCP tool format
        mcp_tool = MCPTool(
            name=tool.tool_id,
            description=tool.description,
            inputSchema=tool.input_schema
        )

        # Register tool handler
        @self.mcp_server.call_tool()
        async def handle_tool_call(name: str, arguments: dict) -> List[Any]:
            """Handle tool execution requests from MCP clients"""
            if name != tool.tool_id:
                return []

            try:
                # Execute tool through registry
                result = await self.tool_registry.execute_tool(
                    tool_id=name,
                    parameters=arguments
                )

                # Return result in MCP format
                return [{
                    "type": "text",
                    "text": str(result)
                }]

            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                return [{
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }]

        # Register the tool definition
        self.mcp_server.list_tools = lambda: [mcp_tool]

    async def _start_http_server(self):
        """Start HTTP/SSE transport server"""
        # HTTP transport implementation
        # This would use FastAPI or similar to expose MCP over HTTP
        from fastapi import FastAPI, Request
        from fastapi.responses import StreamingResponse
        import uvicorn

        app = FastAPI(title=self.config.server_name)

        @app.post("/mcp/v1/tools")
        async def list_tools():
            """List available tools"""
            tools = self.tool_registry.get_all_tools(enabled_only=True)
            return {
                "tools": [
                    {
                        "id": tool.tool_id,
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "tags": tool.tags
                    }
                    for tool in tools
                ]
            }

        @app.post("/mcp/v1/tools/{tool_id}/execute")
        async def execute_tool(tool_id: str, request: Request):
            """Execute a tool"""
            params = await request.json()

            try:
                result = await self.tool_registry.execute_tool(
                    tool_id=tool_id,
                    parameters=params
                )
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Start server
        config = uvicorn.Config(
            app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    def get_status(self) -> Dict[str, Any]:
        """Get MCP server status"""
        return {
            "enabled": self.enabled,
            "server_name": self.config.server_name,
            "version": self.config.server_version,
            "transport": self.config.transport,
            "host": self.config.host,
            "port": self.config.port,
            "tools_exposed": len(self.tool_registry.get_all_tools(enabled_only=True)),
            "running": self.mcp_server is not None
        }

    def get_connection_info(self) -> Dict[str, str]:
        """Get connection information for external clients"""
        if self.config.transport == "stdio":
            return {
                "transport": "stdio",
                "command": "python -m app.mcp_server",
                "description": "Run this command from the backend directory"
            }
        else:
            return {
                "transport": self.config.transport,
                "url": f"http://{self.config.host}:{self.config.port}/mcp/v1",
                "description": "Connect to this URL from MCP clients"
            }


# Global MCP server instance
_mcp_server_instance: Optional[ChatbotMCPServer] = None


async def get_mcp_server(tool_registry) -> ChatbotMCPServer:
    """Get or create MCP server instance"""
    global _mcp_server_instance

    if _mcp_server_instance is None:
        _mcp_server_instance = ChatbotMCPServer(tool_registry)

    return _mcp_server_instance


async def start_mcp_server(tool_registry):
    """Start MCP server"""
    server = await get_mcp_server(tool_registry)
    await server.start()
    return server


async def stop_mcp_server():
    """Stop MCP server"""
    global _mcp_server_instance

    if _mcp_server_instance:
        await _mcp_server_instance.stop()
        _mcp_server_instance = None
