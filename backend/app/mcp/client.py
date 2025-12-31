"""
MCP Client Implementation (Consumer)

Connects to external MCP servers and imports their tools into our tool registry.

Supported MCP Servers:
- GitHub (issues, PRs, repos)
- Slack (channels, messages)
- Filesystem (read/write files)
- PostgreSQL (database queries)
- Custom servers
"""

import logging
import asyncio
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExternalMCPServer:
    """Configuration for an external MCP server"""
    server_id: str
    name: str
    enabled: bool = True
    transport: str = "stdio"  # stdio, http, sse
    command: Optional[str] = None  # For stdio transport
    url: Optional[str] = None  # For HTTP/SSE transport
    env: Dict[str, str] = field(default_factory=dict)
    tools_imported: List[str] = field(default_factory=list)
    connected: bool = False
    error: Optional[str] = None


class MCPClientManager:
    """
    Manager for external MCP server connections

    Responsibilities:
    1. Load external server configurations from YAML
    2. Connect to external MCP servers
    3. Discover tools from external servers
    4. Register external tools in our tool registry
    5. Execute tools on remote servers
    """

    def __init__(
        self,
        tool_registry,
        config_path: Optional[str] = None
    ):
        """
        Initialize MCP Client Manager

        Args:
            tool_registry: ToolRegistry instance to register external tools
            config_path: Path to mcp_servers.yaml config file
        """
        self.tool_registry = tool_registry
        self.config_path = config_path or "config/mcp_servers.yaml"

        # Track connected servers
        self.servers: Dict[str, ExternalMCPServer] = {}

        # MCP client instances (will be initialized per server)
        self.mcp_clients: Dict[str, Any] = {}

        logger.info(f"MCP Client Manager initialized with config: {self.config_path}")

    async def load_servers_from_config(self):
        """Load external MCP server configurations from YAML"""
        try:
            config_file = Path(self.config_path)

            if not config_file.exists():
                logger.warning(f"MCP config file not found: {self.config_path}")
                logger.info("Creating default config file")
                await self._create_default_config()
                return

            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'servers' not in config:
                logger.warning("No servers defined in MCP config")
                return

            # Parse server configurations
            for server_config in config['servers']:
                server_id = server_config.get('id')
                if not server_id:
                    continue

                server = ExternalMCPServer(
                    server_id=server_id,
                    name=server_config.get('name', server_id),
                    enabled=server_config.get('enabled', True),
                    transport=server_config.get('transport', 'stdio'),
                    command=server_config.get('command'),
                    url=server_config.get('url'),
                    env=server_config.get('env', {})
                )

                self.servers[server_id] = server
                logger.info(f"Loaded MCP server config: {server.name} ({server_id})")

        except Exception as e:
            logger.error(f"Failed to load MCP server config: {e}", exc_info=True)

    async def connect_all_servers(self):
        """Connect to all enabled external MCP servers"""
        enabled_servers = [s for s in self.servers.values() if s.enabled]

        logger.info(f"Connecting to {len(enabled_servers)} external MCP servers")

        # Connect to servers in parallel
        tasks = [
            self.connect_server(server.server_id)
            for server in enabled_servers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        connected_count = sum(
            1 for r in results if isinstance(r, bool) and r
        )
        logger.info(
            f"Connected to {connected_count}/{len(enabled_servers)} MCP servers"
        )

    async def connect_server(self, server_id: str) -> bool:
        """
        Connect to a specific external MCP server

        Args:
            server_id: ID of the server to connect to

        Returns:
            True if connection successful, False otherwise
        """
        server = self.servers.get(server_id)
        if not server:
            logger.error(f"Server not found: {server_id}")
            return False

        if not server.enabled:
            logger.info(f"Server {server_id} is disabled, skipping")
            return False

        try:
            logger.info(f"Connecting to MCP server: {server.name} ({server_id})")

            # Import MCP client SDK
            from mcp.client import Client
            from mcp.client.stdio import stdio_client

            # Create MCP client based on transport
            if server.transport == "stdio":
                if not server.command:
                    raise ValueError(f"No command specified for stdio server: {server_id}")

                # Create stdio client
                client_context = stdio_client(
                    server.command.split(),
                    env=server.env
                )

                async with client_context as (read, write):
                    client = Client(read, write)
                    await client.initialize()

                    # Discover tools from server
                    tools = await client.list_tools()

                    # Register tools in our registry
                    for tool in tools:
                        await self._register_external_tool(server_id, tool, client)
                        server.tools_imported.append(tool['name'])

                    server.connected = True
                    self.mcp_clients[server_id] = client

                    logger.info(
                        f"Connected to {server.name}: imported {len(tools)} tools"
                    )

            elif server.transport in ["http", "sse"]:
                # HTTP/SSE client implementation
                logger.warning(f"HTTP/SSE transport not yet implemented for {server_id}")
                return False

            return True

        except ImportError:
            error_msg = "MCP SDK not installed. Install with: pip install mcp"
            logger.error(error_msg)
            server.error = error_msg
            return False

        except Exception as e:
            error_msg = f"Failed to connect to {server_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            server.error = error_msg
            server.connected = False
            return False

    async def disconnect_server(self, server_id: str):
        """Disconnect from an external MCP server"""
        server = self.servers.get(server_id)
        if not server:
            return

        # Remove imported tools from registry
        for tool_id in server.tools_imported:
            # Tool ID format: mcp_{server_id}_{tool_name}
            full_tool_id = f"mcp_{server_id}_{tool_id}"
            if full_tool_id in self.tool_registry.tools:
                del self.tool_registry.tools[full_tool_id]

        # Close client connection
        if server_id in self.mcp_clients:
            del self.mcp_clients[server_id]

        server.connected = False
        server.tools_imported = []
        logger.info(f"Disconnected from MCP server: {server.name}")

    async def enable_server(self, server_id: str):
        """Enable an external MCP server"""
        server = self.servers.get(server_id)
        if not server:
            logger.error(f"Server not found: {server_id}")
            return

        server.enabled = True
        await self.connect_server(server_id)
        logger.info(f"Enabled MCP server: {server.name}")

    async def disable_server(self, server_id: str):
        """Disable an external MCP server"""
        server = self.servers.get(server_id)
        if not server:
            logger.error(f"Server not found: {server_id}")
            return

        server.enabled = False
        await self.disconnect_server(server_id)
        logger.info(f"Disabled MCP server: {server.name}")

    async def _register_external_tool(
        self,
        server_id: str,
        tool_definition: Dict[str, Any],
        client: Any
    ):
        """Register an external tool from MCP server in our tool registry"""
        tool_name = tool_definition['name']
        tool_id = f"mcp_{server_id}_{tool_name}"

        # Create wrapper function that calls external MCP server
        async def execute_external_tool(**params):
            """Execute tool on external MCP server"""
            try:
                result = await client.call_tool(tool_name, params)
                return result
            except Exception as e:
                logger.error(f"External tool execution failed: {e}")
                return {"error": str(e)}

        # Register in tool registry
        self.tool_registry.register(
            tool_id=tool_id,
            name=f"{tool_definition.get('description', tool_name)} (MCP: {server_id})",
            description=tool_definition.get('description', f"External tool: {tool_name}"),
            function=execute_external_tool,
            input_schema=tool_definition.get('inputSchema', {}),
            tags=["mcp", "external", server_id],
            source="mcp",
            enabled=True
        )

        logger.info(f"Registered external MCP tool: {tool_id}")

    async def _create_default_config(self):
        """Create a default mcp_servers.yaml configuration file"""
        default_config = {
            "servers": [
                {
                    "id": "github",
                    "name": "GitHub MCP Server",
                    "enabled": False,
                    "transport": "stdio",
                    "command": "npx @modelcontextprotocol/server-github",
                    "env": {
                        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
                    }
                },
                {
                    "id": "slack",
                    "name": "Slack MCP Server",
                    "enabled": False,
                    "transport": "stdio",
                    "command": "npx @modelcontextprotocol/server-slack",
                    "env": {
                        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
                        "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
                    }
                },
                {
                    "id": "filesystem",
                    "name": "Filesystem MCP Server",
                    "enabled": False,
                    "transport": "stdio",
                    "command": "npx @modelcontextprotocol/server-filesystem /allowed/path"
                },
                {
                    "id": "postgres",
                    "name": "PostgreSQL MCP Server",
                    "enabled": False,
                    "transport": "stdio",
                    "command": "npx @modelcontextprotocol/server-postgres",
                    "env": {
                        "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
                    }
                }
            ]
        }

        # Create config directory
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        # Write default config
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created default MCP server config: {self.config_path}")

    def get_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific MCP server"""
        server = self.servers.get(server_id)
        if not server:
            return None

        return {
            "server_id": server.server_id,
            "name": server.name,
            "enabled": server.enabled,
            "connected": server.connected,
            "transport": server.transport,
            "tools_imported": len(server.tools_imported),
            "tools": server.tools_imported,
            "error": server.error
        }

    def get_all_servers_status(self) -> List[Dict[str, Any]]:
        """Get status of all MCP servers"""
        return [
            self.get_server_status(server_id)
            for server_id in self.servers.keys()
        ]


# Global MCP client manager instance
_mcp_client_manager: Optional[MCPClientManager] = None


async def get_mcp_client_manager(tool_registry) -> MCPClientManager:
    """Get or create MCP client manager instance"""
    global _mcp_client_manager

    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager(tool_registry)
        await _mcp_client_manager.load_servers_from_config()
        await _mcp_client_manager.connect_all_servers()

    return _mcp_client_manager


async def initialize_mcp_client(tool_registry):
    """Initialize MCP client and connect to all enabled servers"""
    manager = await get_mcp_client_manager(tool_registry)
    return manager
