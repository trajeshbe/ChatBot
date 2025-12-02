"""
MCP (Model Context Protocol) Server Service

Exposes our internal tools as an MCP server for external consumption.
External applications can discover and use our tools via the MCP protocol.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class MCPServerService:
    """
    Service for managing MCP server that exposes internal tools to external applications
    """

    def __init__(self):
        self.available_tools = {
            "document_rag": {
                "name": "document_rag",
                "description": "Query documents using RAG (Retrieval-Augmented Generation)",
                "enabled": True,
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Question to ask"},
                    "session_id": {"type": "string", "required": False, "description": "Session ID for context"},
                    "top_k": {"type": "integer", "required": False, "default": 5, "description": "Number of results"}
                },
                "handler": "execute_document_rag"
            },
            "smart_extraction": {
                "name": "smart_extraction",
                "description": "Extract structured data from web pages using AI",
                "enabled": True,
                "parameters": {
                    "url": {"type": "string", "required": True, "description": "URL to extract from"},
                    "user_instructions": {"type": "string", "required": True, "description": "What to extract"},
                    "llm_provider": {"type": "string", "required": False, "default": "openai", "description": "LLM provider"}
                },
                "handler": "execute_smart_extraction"
            },
            "web_scraper": {
                "name": "web_scraper",
                "description": "Scrape web content with compliance checking",
                "enabled": True,
                "parameters": {
                    "url": {"type": "string", "required": True, "description": "URL to scrape"},
                    "scrape_prompt": {"type": "string", "required": False, "description": "Content filtering prompt"},
                    "strategy": {"type": "string", "required": False, "description": "Scraping strategy"}
                },
                "handler": "execute_web_scraper"
            },
            "template_extraction": {
                "name": "template_extraction",
                "description": "Extract data using predefined templates",
                "enabled": True,
                "parameters": {
                    "url": {"type": "string", "required": True, "description": "URL to extract from"},
                    "template_id": {"type": "string", "required": True, "description": "Template ID to use"}
                },
                "handler": "execute_template_extraction"
            },
            "docling_pdf": {
                "name": "docling_pdf",
                "description": "Extract text and structure from PDF documents",
                "enabled": True,
                "parameters": {
                    "url": {"type": "string", "required": True, "description": "PDF URL or file path"},
                    "extract_tables": {"type": "boolean", "required": False, "default": True}
                },
                "handler": "execute_docling_pdf"
            },
            "ocr": {
                "name": "ocr",
                "description": "Extract text from images using OCR",
                "enabled": True,
                "parameters": {
                    "image_url": {"type": "string", "required": True, "description": "Image URL"},
                    "language": {"type": "string", "required": False, "default": "eng"}
                },
                "handler": "execute_ocr"
            },
            "navigation_agent": {
                "name": "navigation_agent",
                "description": "AI-powered web navigation and data extraction",
                "enabled": True,
                "parameters": {
                    "start_url": {"type": "string", "required": True, "description": "Starting URL"},
                    "goal": {"type": "string", "required": True, "description": "Navigation goal"}
                },
                "handler": "execute_navigation_agent"
            }
        }

    async def list_tools(self, db: AsyncSession, include_disabled: bool = False) -> List[Dict[str, Any]]:
        """
        List all available MCP tools

        Args:
            db: Database session
            include_disabled: Whether to include disabled tools

        Returns:
            List of tool definitions
        """
        try:
            # Get tool configurations from database
            from app.models.database_enhanced import MCPToolConfig

            query = select(MCPToolConfig)
            if not include_disabled:
                query = query.where(MCPToolConfig.enabled == True)

            result = await db.execute(query)
            db_configs = {config.tool_name: config for config in result.scalars().all()}

            tools = []
            for tool_name, tool_def in self.available_tools.items():
                # Check if tool is enabled in database (if config exists)
                if tool_name in db_configs:
                    if not include_disabled and not db_configs[tool_name].enabled:
                        continue
                    tool_def = {**tool_def, "enabled": db_configs[tool_name].enabled}
                elif not include_disabled and not tool_def.get("enabled", True):
                    continue

                tools.append({
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "enabled": tool_def.get("enabled", True),
                    "parameters": tool_def["parameters"]
                })

            return tools

        except Exception as e:
            logger.error(f"Error listing MCP tools: {e}")
            # Fallback to default tools if database not initialized
            return [
                {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "enabled": tool_def.get("enabled", True),
                    "parameters": tool_def["parameters"]
                }
                for tool_def in self.available_tools.values()
                if include_disabled or tool_def.get("enabled", True)
            ]

    async def get_tool(self, db: AsyncSession, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific tool

        Args:
            db: Database session
            tool_name: Name of the tool

        Returns:
            Tool definition or None if not found
        """
        if tool_name not in self.available_tools:
            return None

        tool_def = self.available_tools[tool_name]

        try:
            # Check database configuration
            from app.models.database_enhanced import MCPToolConfig

            query = select(MCPToolConfig).where(MCPToolConfig.tool_name == tool_name)
            result = await db.execute(query)
            db_config = result.scalar_one_or_none()

            if db_config:
                tool_def = {**tool_def, "enabled": db_config.enabled}

        except Exception as e:
            logger.warning(f"Could not load tool config from database: {e}")

        return {
            "name": tool_def["name"],
            "description": tool_def["description"],
            "enabled": tool_def.get("enabled", True),
            "parameters": tool_def["parameters"],
            "handler": tool_def["handler"]
        }

    async def toggle_tool(self, db: AsyncSession, tool_name: str, enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable a tool for MCP access

        Args:
            db: Database session
            tool_name: Name of the tool
            enabled: Whether to enable or disable

        Returns:
            Updated tool configuration
        """
        if tool_name not in self.available_tools:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

        try:
            from app.models.database_enhanced import MCPToolConfig

            # Check if config exists
            query = select(MCPToolConfig).where(MCPToolConfig.tool_name == tool_name)
            result = await db.execute(query)
            config = result.scalar_one_or_none()

            if config:
                # Update existing
                config.enabled = enabled
                config.updated_at = datetime.utcnow()
            else:
                # Create new
                config = MCPToolConfig(
                    tool_name=tool_name,
                    enabled=enabled,
                    description=self.available_tools[tool_name]["description"]
                )
                db.add(config)

            await db.commit()
            await db.refresh(config)

            logger.info(f"Tool {tool_name} {'enabled' if enabled else 'disabled'} for MCP access")

            return {
                "tool_name": config.tool_name,
                "enabled": config.enabled,
                "description": config.description,
                "updated_at": config.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error toggling tool {tool_name}: {e}")
            await db.rollback()
            raise

    async def execute_tool(
        self,
        db: AsyncSession,
        tool_name: str,
        parameters: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool via MCP

        Args:
            db: Database session
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            api_key: Optional API key for authentication

        Returns:
            Tool execution result
        """
        # Check if tool exists and is enabled
        tool = await self.get_tool(db, tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

        if not tool["enabled"]:
            raise HTTPException(status_code=403, detail=f"Tool is disabled: {tool_name}")

        # Validate API key if provided
        if api_key:
            await self._validate_api_key(db, api_key)

        # Log the execution attempt
        await self._log_tool_execution(db, tool_name, parameters, api_key)

        # Execute the tool
        handler_name = tool["handler"]
        handler = getattr(self, handler_name, None)

        if not handler:
            raise HTTPException(status_code=500, detail=f"Handler not found: {handler_name}")

        try:
            result = await handler(db, parameters)
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }

    async def _validate_api_key(self, db: AsyncSession, api_key: str) -> bool:
        """Validate API key for external MCP access"""
        try:
            from app.models.database_enhanced import MCPAPIKey

            query = select(MCPAPIKey).where(
                MCPAPIKey.key_hash == api_key,  # In production, hash the key
                MCPAPIKey.is_active == True
            )
            result = await db.execute(query)
            key_record = result.scalar_one_or_none()

            if not key_record:
                raise HTTPException(status_code=401, detail="Invalid API key")

            # Update last used
            key_record.last_used_at = datetime.utcnow()
            key_record.usage_count += 1
            await db.commit()

            return True

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            raise HTTPException(status_code=401, detail="Invalid API key")

    async def _log_tool_execution(
        self,
        db: AsyncSession,
        tool_name: str,
        parameters: Dict[str, Any],
        api_key: Optional[str]
    ):
        """Log tool execution for monitoring"""
        try:
            from app.models.database_enhanced import MCPToolExecutionLog

            log_entry = MCPToolExecutionLog(
                tool_name=tool_name,
                parameters=parameters,
                api_key_id=api_key[:8] if api_key else None,  # Store only prefix
                executed_at=datetime.utcnow()
            )
            db.add(log_entry)
            await db.commit()

        except Exception as e:
            logger.warning(f"Could not log tool execution: {e}")

    # Tool execution handlers
    async def execute_document_rag(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document RAG query"""
        from app.services.rag_service import rag_service

        result = await rag_service.query_documents(
            db=db,
            query=params["query"],
            session_id=params.get("session_id"),
            top_k=params.get("top_k", 5)
        )
        return result

    async def execute_smart_extraction(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute smart extraction"""
        from app.api.routes.extraction_routes import extract_ultra_smart_internal

        result = await extract_ultra_smart_internal(
            url=params["url"],
            user_instructions=params["user_instructions"],
            llm_provider=params.get("llm_provider", "openai"),
            db=db
        )
        return result

    async def execute_web_scraper(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web scraper"""
        from app.services.scraper_service import scraper_service

        result = await scraper_service.scrape_url(
            url=params["url"],
            scrape_prompt=params.get("scrape_prompt"),
            strategy=params.get("strategy"),
            db=db
        )
        return result

    async def execute_template_extraction(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute template extraction"""
        # Implementation would go here
        return {"message": "Template extraction not yet implemented"}

    async def execute_docling_pdf(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Docling PDF extraction"""
        # Implementation would go here
        return {"message": "Docling PDF extraction not yet implemented"}

    async def execute_ocr(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OCR"""
        # Implementation would go here
        return {"message": "OCR not yet implemented"}

    async def execute_navigation_agent(self, db: AsyncSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigation agent"""
        # Implementation would go here
        return {"message": "Navigation agent not yet implemented"}


# Singleton instance
mcp_server_service = MCPServerService()
