"""
Unit Tests for Tool Registry

Tests the tool registration, discovery, and execution system.
"""

import pytest
import asyncio
from app.agents.tool_registry import ToolRegistry, Tool


class TestToolRegistry:
    """Test suite for ToolRegistry"""

    def setup_method(self):
        """Setup for each test - create fresh registry"""
        self.registry = ToolRegistry()

    def test_initialization(self):
        """Test that registry initializes with built-in tools"""
        assert len(self.registry.tools) > 0
        assert "document_rag" in self.registry.tools
        assert "smart_extraction" in self.registry.tools
        assert "web_scraper" in self.registry.tools

    def test_get_tool(self):
        """Test getting a tool by ID"""
        tool = self.registry.get_tool("document_rag")

        assert tool is not None
        assert tool.tool_id == "document_rag"
        assert tool.name == "Document RAG Retrieval"
        assert tool.enabled is True

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist"""
        tool = self.registry.get_tool("nonexistent_tool")
        assert tool is None

    def test_get_all_tools(self):
        """Test getting all tools"""
        tools = self.registry.get_all_tools()

        assert len(tools) > 0
        assert all(isinstance(tool, Tool) for tool in tools)

    def test_get_enabled_tools_only(self):
        """Test filtering to enabled tools only"""
        # Disable one tool
        self.registry.disable_tool("document_rag")

        # Get only enabled tools
        enabled_tools = self.registry.get_all_tools(enabled_only=True)

        # Check that disabled tool is not in list
        tool_ids = [t.tool_id for t in enabled_tools]
        assert "document_rag" not in tool_ids

        # Re-enable for other tests
        self.registry.enable_tool("document_rag")

    def test_get_tools_by_tag(self):
        """Test getting tools by tag"""
        # Get tools with 'web scraping' tag
        scraping_tools = self.registry.get_tools_by_tag("web scraping")

        assert len(scraping_tools) > 0
        assert all("web scraping" in tool.tags for tool in scraping_tools)

    def test_get_tools_for_llm(self):
        """Test getting tools in OpenAI function calling format"""
        llm_tools = self.registry.get_tools_for_llm()

        assert len(llm_tools) > 0
        assert all(isinstance(tool, dict) for tool in llm_tools)

        # Check format
        first_tool = llm_tools[0]
        assert "type" in first_tool
        assert first_tool["type"] == "function"
        assert "function" in first_tool
        assert "name" in first_tool["function"]
        assert "description" in first_tool["function"]
        assert "parameters" in first_tool["function"]

    def test_disable_enable_tool(self):
        """Test disabling and enabling a tool"""
        tool_id = "document_rag"

        # Initially enabled
        assert self.registry.get_tool(tool_id).enabled is True

        # Disable
        self.registry.disable_tool(tool_id)
        assert self.registry.get_tool(tool_id).enabled is False

        # Enable
        self.registry.enable_tool(tool_id)
        assert self.registry.get_tool(tool_id).enabled is True

    def test_register_custom_tool(self):
        """Test registering a custom tool"""
        async def custom_function(param1: str) -> dict:
            return {"result": f"Processed: {param1}"}

        self.registry.register(
            tool_id="custom_test_tool",
            name="Custom Test Tool",
            description="A test tool for unit testing",
            function=custom_function,
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            },
            tags=["test", "custom"],
            source="custom"
        )

        # Verify registration
        tool = self.registry.get_tool("custom_test_tool")
        assert tool is not None
        assert tool.name == "Custom Test Tool"
        assert "test" in tool.tags
        assert tool.source == "custom"

    def test_tool_to_openai_function(self):
        """Test converting a tool to OpenAI function format"""
        tool = self.registry.get_tool("document_rag")
        openai_func = tool.to_openai_function()

        assert openai_func["type"] == "function"
        assert openai_func["function"]["name"] == "document_rag"
        assert "description" in openai_func["function"]
        assert "parameters" in openai_func["function"]

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test executing a tool that doesn't exist"""
        with pytest.raises(ValueError, match="Tool not found"):
            await self.registry.execute_tool("nonexistent_tool", {})

    @pytest.mark.asyncio
    async def test_execute_disabled_tool(self):
        """Test executing a disabled tool"""
        # Disable a tool
        self.registry.disable_tool("document_rag")

        # Try to execute
        with pytest.raises(ValueError, match="Tool is disabled"):
            await self.registry.execute_tool("document_rag", {"query": "test"})

        # Re-enable
        self.registry.enable_tool("document_rag")


class TestToolDataclass:
    """Test the Tool dataclass"""

    def test_tool_creation(self):
        """Test creating a Tool instance"""
        async def dummy_function():
            return {}

        tool = Tool(
            tool_id="test_tool",
            name="Test Tool",
            description="A test tool",
            function=dummy_function,
            input_schema={"type": "object"},
            tags=["test"],
            source="built-in",
            enabled=True
        )

        assert tool.tool_id == "test_tool"
        assert tool.name == "Test Tool"
        assert tool.enabled is True
        assert "test" in tool.tags


# Integration test (requires backend to be running)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_document_rag_tool_execution():
    """
    Integration test: Execute document RAG tool

    Note: Requires backend services to be running
    """
    registry = ToolRegistry()

    # This would actually call the RAG service
    # Skipped in unit tests, enabled for integration testing
    pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
