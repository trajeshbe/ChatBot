"""
Grant Thornton Agent Service

LangGraph-based agent for financial datapoint extraction.
Uses react agent pattern with search tool for dynamic retrieval.

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import Dict, Any, List, Optional, AsyncIterator
import json
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser

from app.schemas.grant_thornton_schemas import ValueSchema, ExtractedDatapoint
from .retrieval_service import search_financial_details
from .config import load_config, load_prompts

logger = logging.getLogger(__name__)


class GrantThorntonAgent:
    """
    LangGraph agent for extracting financial datapoints from annual reports.

    Uses:
    - GPT-4o-mini for extraction (configurable)
    - search_financial_details tool for dynamic retrieval
    - Structured output (ValueSchema) with validation
    - Retry logic (2 attempts per datapoint)
    """

    def __init__(self):
        self.config = load_config()
        self.prompts = load_prompts()

        # LLM for extraction
        self.llm = ChatOpenAI(
            model=self.config.llm_model_name,  # gpt-4o-mini
            temperature=0.0,  # Deterministic for financial data
            streaming=True
        )

        # Output parser for structured extraction
        self.output_parser = JsonOutputParser(pydantic_object=ValueSchema)

        # Current document MD5 (set during extraction)
        self.current_md5: Optional[str] = None

        self._initialized = False

    async def initialize(self):
        """Initialize agent components"""
        if self._initialized:
            return

        logger.info(
            f"✅ Grant Thornton agent ready\n"
            f"   - LLM: {self.config.llm_model_name}\n"
            f"   - Temperature: 0.0 (deterministic)\n"
            f"   - Retry count: {self.config.retry_count}"
        )

        self._initialized = True

    def _create_search_tool(self, md5_hash: str):
        """
        Create search tool for this extraction session.

        The tool is bound to the specific document (md5_hash).
        """
        @tool
        async def search_financial_details_tool(query: str) -> str:
            """
            Search for specific financial details in the annual report.

            Use this tool when you need to find financial data like:
            - Balance sheet items (assets, liabilities, equity)
            - P&L items (revenue, expenses, net income)
            - Cash flow items (operating, investing, financing)
            - Financial ratios and metrics

            Args:
                query: Natural language query describing what to search for

            Returns:
                Relevant excerpts from the annual report
            """
            try:
                results = await search_financial_details(
                    md5_hash=md5_hash,
                    query=query,
                    top_k=2
                )

                # Format results for LLM
                if not results:
                    return "No relevant information found. Try a different search query."

                formatted = []
                for i, chunk in enumerate(results, 1):
                    content = chunk.get('page_content', chunk.get('content', ''))
                    metadata = chunk.get('metadata', {})
                    page = metadata.get('page', 'unknown')
                    score = chunk.get('rerank_score', chunk.get('similarity', 0))

                    formatted.append(
                        f"[Result {i}] (Page {page}, Relevance: {score:.2f})\n{content}\n"
                    )

                return "\n".join(formatted)

            except Exception as e:
                logger.error(f"Error in search tool: {e}", exc_info=True)
                return f"Error searching: {str(e)}"

        return search_financial_details_tool

    def _create_system_prompt(self) -> str:
        """
        Create system prompt for financial extraction.

        Uses prompt template from config/prompts.yaml or defaults.
        """
        user_prompt = self.prompts.get('user_prompt', '')

        if not user_prompt:
            # Default prompt
            user_prompt = """You are a financial-ratio engine tasked with extracting financial data from annual reports.

Your role:
1. Search through the provided document for the requested financial metric
2. Extract the EXACT numerical value
3. Note the page number where you found it
4. Provide brief reference notes about the context

Return your answer in the following JSON format:
{
    "value": <numerical_value>,
    "page_no": <page_number>,
    "reference_notes": "<brief_context>"
}

If you cannot find the value, return:
{
    "value": 0,
    "page_no": 0,
    "reference_notes": "Not Applicable"
}

Important:
- ALWAYS use the search_financial_details tool to find information
- Extract ONLY numerical values (remove currency symbols, commas, etc.)
- Be precise with page numbers
- If a value appears in multiple places, use the most authoritative source (audited statements)
"""

        return user_prompt

    async def extract_datapoint(
        self,
        md5_hash: str,
        datapoint: ExtractedDatapoint,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> ExtractedDatapoint:
        """
        Extract a single financial datapoint using the agent.

        Args:
            md5_hash: MD5 hash of the PDF
            datapoint: Datapoint to extract (with field_name, definition)
            initial_context: Optional initial context chunks (Stage 1)

        Returns:
            Updated datapoint with extracted value, page_no, reference_notes
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"🔍 Extracting: {datapoint.field_name}")

        # Create search tool bound to this document
        search_tool = self._create_search_tool(md5_hash)

        # Build extraction prompt
        extraction_query = f"""Extract the following financial metric from the annual report:

**Field Name:** {datapoint.field_name}
**Definition:** {datapoint.definition}
{f"**Typical Location:** {datapoint.typical_location}" if datapoint.typical_location else ""}

Use the search_financial_details tool to find this information in the document.
Return the result in JSON format with value, page_no, and reference_notes.
"""

        # Add initial context if provided (Stage 1)
        if initial_context:
            context_str = "\n\n".join([
                f"[Context {i+1}] (Page {chunk.get('metadata', {}).get('page', 'unknown')})\n{chunk.get('page_content', chunk.get('content', ''))}"
                for i, chunk in enumerate(initial_context)
            ])
            extraction_query += f"\n\n**Initial Context (from financial statements):**\n{context_str}"

        try:
            # Create messages
            messages = [
                SystemMessage(content=self._create_system_prompt()),
                HumanMessage(content=extraction_query)
            ]

            # Bind tools to LLM
            llm_with_tools = self.llm.bind_tools([search_tool])

            # Invoke with tool calling
            response = await llm_with_tools.ainvoke(messages)

            # Handle tool calls (if any)
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"Agent called {len(response.tool_calls)} tools")

                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get('name', '')
                    tool_args = tool_call.get('args', {})

                    if tool_name == 'search_financial_details_tool':
                        search_query = tool_args.get('query', '')
                        logger.info(f"   Tool query: '{search_query}'")

                        # Execute search
                        tool_result = await search_tool.ainvoke(tool_args)

                        # Add tool result to messages
                        from langchain_core.messages import ToolMessage
                        messages.append(response)
                        messages.append(ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call.get('id', '')
                        ))

                # Get final response with tool results
                final_response = await self.llm.ainvoke(messages)
                response_text = final_response.content
            else:
                # No tool calls, use direct response
                response_text = response.content

            # Parse JSON output
            try:
                # Extract JSON from response (may be wrapped in markdown)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)

                    # Validate and update datapoint
                    value_schema = ValueSchema(**result)
                    datapoint.value = value_schema.value
                    datapoint.page_no = value_schema.page_no
                    datapoint.reference_notes = value_schema.reference_notes
                    datapoint.extraction_status = "success"

                    logger.info(
                        f"✅ Extracted {datapoint.field_name}: "
                        f"value={value_schema.value}, page={value_schema.page_no}"
                    )
                else:
                    raise ValueError("No JSON found in response")

            except Exception as parse_error:
                logger.error(f"Error parsing response: {parse_error}")
                logger.debug(f"Response text: {response_text}")

                # Mark as failed but keep trying
                datapoint.extraction_status = "parse_error"
                datapoint.reference_notes = f"Parse error: {str(parse_error)}"

        except Exception as e:
            logger.error(f"Error extracting {datapoint.field_name}: {e}", exc_info=True)
            datapoint.extraction_status = "error"
            datapoint.reference_notes = f"Error: {str(e)}"

        return datapoint

    async def extract_datapoint_with_retry(
        self,
        md5_hash: str,
        datapoint: ExtractedDatapoint,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> ExtractedDatapoint:
        """
        Extract datapoint with retry logic.

        Args:
            md5_hash: MD5 hash of the PDF
            datapoint: Datapoint to extract
            initial_context: Optional initial context

        Returns:
            Updated datapoint (may have failed after retries)
        """
        max_retries = self.config.retry_count

        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(f"🔄 Retry {attempt}/{max_retries - 1} for {datapoint.field_name}")

            result = await self.extract_datapoint(
                md5_hash=md5_hash,
                datapoint=datapoint,
                initial_context=initial_context
            )

            if result.extraction_status == "success":
                return result

            # Update retry count
            result.retry_count = attempt + 1

            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s...
                await asyncio.sleep(wait_time)

        # All retries failed
        logger.warning(
            f"❌ Failed to extract {datapoint.field_name} after {max_retries} attempts"
        )
        result.extraction_status = "failed"

        return result


# Singleton instance
_agent = None


async def get_agent() -> GrantThorntonAgent:
    """
    Get or create Grant Thornton agent singleton.

    Returns:
        Initialized GrantThorntonAgent
    """
    global _agent

    if _agent is None:
        _agent = GrantThorntonAgent()
        await _agent.initialize()

    return _agent
