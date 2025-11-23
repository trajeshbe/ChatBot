"""
Enhanced RAG Agent with Multi-Tool Support

Extends the basic RAGAgent with intelligent tool selection and execution.
Phase 3 implementation - LLM-based tool selection with function calling.
"""

from typing import Dict, Any, Optional, List
import logging
import time
import asyncio
import json

from app.agents.rag_agent import RAGAgent
from app.agents.agent_state import EnhancedAgentState
from app.agents.tool_registry import tool_registry
from langchain.schema import HumanMessage
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedRAGAgent(RAGAgent):
    """
    Enhanced RAG Agent with multi-tool support

    Extends the basic RAGAgent to support:
    - Intelligent tool selection
    - Multi-tool workflows
    - Parallel tool execution (future)
    - MCP server integration (future)

    Phase 1: Simplified implementation for proof of concept
    """

    def __init__(self):
        """Initialize enhanced agent with tool registry and LLM client"""
        super().__init__()
        self.tool_registry = tool_registry
        self.openai_client = None
        self.use_llm_selection = True  # Flag to enable/disable LLM-based selection
        logger.info("EnhancedRAGAgent initialized with tool registry")

    async def _ensure_openai_client(self):
        """Ensure OpenAI client is initialized for function calling"""
        if self.openai_client is None and settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized for tool selection")
        return self.openai_client

    async def run(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent workflow with multi-tool support

        Phase 1 Implementation:
        1. Simple keyword-based tool selection
        2. Single tool execution
        3. Direct response generation

        Future phases will add:
        - LLM-based tool selection
        - Parallel multi-tool execution
        - Result synthesis

        Args:
            query: User's question
            session_id: Optional session ID for context
            user_preferences: Optional user preferences (includes threshold parameters)

        Returns:
            Response with answer, sources, and metadata
        """
        start_time = time.time()

        # Extract threshold parameters from user_preferences
        user_preferences = user_preferences or {}
        top_k = user_preferences.get('top_k')
        similarity_threshold = user_preferences.get('similarity_threshold')
        min_similarity_threshold = user_preferences.get('min_similarity_threshold')
        no_relevant_docs_threshold = user_preferences.get('no_relevant_docs_threshold')

        logger.info(
            f"Agent run with thresholds from UI: "
            f"top_k={top_k}, similarity={similarity_threshold}, "
            f"min_similarity={min_similarity_threshold}, no_relevant={no_relevant_docs_threshold}"
        )

        # Initialize state
        state: EnhancedAgentState = {
            "query": query,
            "session_id": session_id,
            "user_preferences": user_preferences,
            "messages": [HumanMessage(content=query)],
            "detected_intent": "",
            "confidence": 0.0,
            "intent_reasoning": "",
            "selected_tools": [],
            "tool_params": {},
            "tool_selection_reasoning": "",
            "tool_results": {},
            "tool_errors": {},
            "synthesized_data": None,
            "synthesis_method": "",
            "answer": "",
            "sources": [],
            "metadata": {},
            "next_action": "",
            "retry_count": 0,
            "validation_result": "complete"
        }

        try:
            # Phase 3: LLM-based tool selection (with fallback to simple selection)
            logger.info(f"Processing query: {query}")

            # Try LLM-based selection if OpenAI is available
            if self.use_llm_selection and await self._ensure_openai_client():
                try:
                    # LLM-based intent analysis and tool selection
                    selection_result = await self._select_tools_llm(
                        query, session_id, top_k=top_k
                    )

                    state["detected_intent"] = selection_result["intent"]
                    state["confidence"] = selection_result["confidence"]
                    state["intent_reasoning"] = selection_result["reasoning"]
                    state["selected_tools"] = selection_result["tools"]
                    state["tool_params"] = selection_result["tool_params"]
                    state["tool_selection_reasoning"] = selection_result["tool_selection_reasoning"]

                    logger.info(f"LLM selected tools: {selection_result['tools']} (confidence: {selection_result['confidence']:.2f})")

                except Exception as e:
                    logger.warning(f"LLM-based selection failed, falling back to simple selection: {e}")
                    # Fallback to simple keyword-based selection
                    tool_id, tool_params = self._select_tool_simple(
                        query, session_id, top_k=top_k
                    )
                    state["selected_tools"] = [tool_id]
                    state["tool_params"] = {tool_id: tool_params}
                    state["detected_intent"] = self._infer_intent_from_tool(tool_id)
            else:
                # Use simple keyword-based selection
                logger.info("Using simple keyword-based tool selection")
                tool_id, tool_params = self._select_tool_simple(
                    query, session_id, top_k=top_k
                )
                state["selected_tools"] = [tool_id]
                state["tool_params"] = {tool_id: tool_params}
                state["detected_intent"] = self._infer_intent_from_tool(tool_id)

            logger.info(f"Selected tools: {state['selected_tools']}")

            # Phase 4: Parallel tool execution with timeout
            if len(state["selected_tools"]) > 1:
                # Execute multiple tools in parallel
                logger.info(f"Executing {len(state['selected_tools'])} tools in parallel")
                tool_results = await self._execute_tools_parallel(
                    state["selected_tools"],
                    state["tool_params"],
                    timeout=60.0  # 60 second timeout per tool
                )
                state["tool_results"] = tool_results
            else:
                # Execute single tool
                tool_id = state["selected_tools"][0]
                tool_params = state["tool_params"][tool_id]
                logger.info(f"Executing single tool: {tool_id}")

                tool_result = await self._execute_tool(tool_id, tool_params)
                state["tool_results"][tool_id] = tool_result

            # Generate response
            response = await self._generate_response(state)

            # Calculate timing
            total_time_ms = (time.time() - start_time) * 1000

            # Build comprehensive tool usage metadata
            tool_timing = {}
            tool_execution_summary = {}

            for tool_id, tool_result in state["tool_results"].items():
                tool_timing[tool_id] = tool_result.get("execution_time_ms", 0)
                tool_execution_summary[tool_id] = {
                    "success": tool_result.get("success", False),
                    "execution_time_ms": tool_result.get("execution_time_ms", 0),
                    "error": tool_result.get("error") if not tool_result.get("success", False) else None
                }

            response["metadata"]["tool_usage"] = {
                "tools_used": state["selected_tools"],
                "tool_timing": tool_timing,
                "tool_execution_summary": tool_execution_summary,
                "tool_selection_method": "llm_based" if (self.use_llm_selection and "confidence" in state) else "keyword_based",
                "selection_confidence": state.get("confidence", 0.0),
                "intent_detected": state.get("detected_intent", "unknown"),
                "tool_selection_reasoning": state.get("tool_selection_reasoning", ""),
                "total_time_ms": total_time_ms,
                "multi_tool_used": len(state["selected_tools"]) > 1
            }

            logger.info(f"Query processed successfully in {total_time_ms:.2f}ms using {len(state['selected_tools'])} tool(s)")

            return response

        except Exception as e:
            logger.error(f"Error in enhanced agent: {e}", exc_info=True)

            # Fallback to basic RAG
            logger.info("Falling back to basic RAG")
            return await self._fallback_to_basic_rag(query, session_id)

    def _select_tool_simple(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Simple keyword-based tool selection (Phase 1)

        Future phases will use LLM function calling for smarter selection.

        Args:
            query: User's question
            session_id: Optional session ID
            top_k: Number of results to retrieve (from UI or None for default)

        Returns:
            Tuple of (tool_id, tool_parameters)
        """
        query_lower = query.lower()

        # ============================================================
        # PRIORITY 1: Check for NAVIGATION keywords FIRST
        # (before generic scraping/URL detection)
        # ============================================================
        if any(word in query_lower for word in [
            "navigate", "navigation", "pagination", "paginate",
            "next page", "all pages", "multiple pages", "go through"
        ]):
            # Check if URL exists
            import re
            url_match = re.search(r'https?://[^\s]+', query)

            if url_match:
                url = url_match.group(0)

                # Use navigation_agent for multi-page extraction
                return "navigation_agent", {
                    "start_url": url,
                    "navigation_instructions": query.replace(url, "").strip() or "Navigate and extract all data",
                    "max_pages": 10  # Default max pages
                }

        # ============================================================
        # PRIORITY 2: Check for web scraping keywords
        # ============================================================
        if any(word in query_lower for word in [
            "scrape", "extract from", "get data from", "fetch from",
            "http://", "https://", ".com", ".org", ".net"
        ]):
            # Check if it's a URL
            if "http" in query or ".com" in query or ".org" in query:
                # Extract URL (simple regex)
                import re
                url_match = re.search(r'https?://[^\s]+', query)

                if url_match:
                    url = url_match.group(0)

                    # Determine user instructions
                    user_instructions = query.replace(url, "").strip()
                    if not user_instructions or len(user_instructions) < 10:
                        user_instructions = "Extract all relevant information from this page"

                    return "smart_extraction", {
                        "url": url,
                        "user_instructions": user_instructions
                    }

        # Check for general web scraping (without specific URL in query)
        if any(word in query_lower for word in ["scrape", "get from web", "download page"]):
            # This would need clarification, default to RAG
            pass

        # Default: Use document RAG with UI-provided top_k (or None to use RAG service default)
        params = {
            "query": query,
            "session_id": session_id
        }

        # Only add top_k if provided (let RAG service use its defaults otherwise)
        if top_k is not None:
            params["top_k"] = top_k

        return "document_rag", params

    async def _select_tools_llm(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        LLM-based tool selection using OpenAI function calling (Phase 3)

        Uses GPT-4 to analyze the query and intelligently select the best tool(s)
        based on available tools and their descriptions.

        Args:
            query: User's question
            session_id: Optional session ID
            top_k: Number of results to retrieve (from UI or None for default)

        Returns:
            Dictionary with:
                - intent: Detected user intent
                - confidence: Confidence score (0-1)
                - reasoning: Explanation of intent detection
                - tools: List of selected tool IDs
                - tool_params: Parameters for each tool
                - tool_selection_reasoning: Why these tools were selected
        """
        # Get available tools in OpenAI function format
        available_tools = self.tool_registry.get_tools_for_llm()

        # System prompt for intent analysis and tool selection
        system_prompt = """You are an intelligent tool selection assistant.  Your job is to analyze user queries and select the most appropriate tool(s) to answer their question.

Available tools and their purposes:
- document_rag: Search and answer questions from uploaded documents
- smart_extraction: Extract structured data from web pages using AI
- web_scraper: Basic web page scraping (HTML and text)
- template_extraction: Extract data using predefined templates
- docling_pdf: Advanced PDF processing and extraction
- ocr: Extract text from images
- navigation_agent: Navigate multiple web pages to collect data

Guidelines:
1. For questions about uploaded documents → use document_rag
2. For extracting data from URLs → use smart_extraction or navigation_agent
3. For PDF files → use docling_pdf
4. For images with text → use ocr
5. For template-based extraction → use template_extraction
6. Choose the SIMPLEST tool that can accomplish the task
7. You may select multiple tools if the query requires it (rare)

Analyze the query carefully and select the best tool(s)."""

        user_prompt = f"""User Query: "{query}"

Analyze this query and determine:
1. What is the user trying to accomplish?
2. Which tool(s) would best accomplish this?
3. What parameters does each tool need?

Respond by calling the appropriate tool function(s)."""

        # Call OpenAI with function calling
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=available_tools,
                tool_choice="auto",  # Let GPT decide which tool to use
                temperature=0.3  # Lower temperature for more consistent tool selection
            )

            message = response.choices[0].message

            # Check if tools were called
            if not message.tool_calls:
                # No tool selected, default to document RAG
                logger.warning("LLM did not select any tool, defaulting to document_rag")

                # Build default params (only include top_k if provided)
                default_params = {
                    "query": query,
                    "session_id": session_id
                }
                if top_k is not None:
                    default_params["top_k"] = top_k

                return {
                    "intent": "general_query",
                    "confidence": 0.5,
                    "reasoning": "LLM did not make a specific tool selection",
                    "tools": ["document_rag"],
                    "tool_params": {
                        "document_rag": default_params
                    },
                    "tool_selection_reasoning": "Default selection due to no LLM tool call"
                }

            # Parse tool calls
            selected_tools = []
            tool_params = {}

            for tool_call in message.tool_calls:
                tool_id = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                selected_tools.append(tool_id)
                tool_params[tool_id] = arguments

                logger.info(f"LLM selected tool: {tool_id} with params: {arguments}")

            # Infer intent from first selected tool
            intent = self._infer_intent_from_tool(selected_tools[0])

            # Extract reasoning from the LLM response
            reasoning = f"LLM selected {len(selected_tools)} tool(s) based on query analysis"

            return {
                "intent": intent,
                "confidence": 0.9,  # High confidence when LLM makes a selection
                "reasoning": reasoning,
                "tools": selected_tools,
                "tool_params": tool_params,
                "tool_selection_reasoning": f"GPT-4 analyzed the query and selected: {', '.join(selected_tools)}"
            }

        except Exception as e:
            logger.error(f"LLM-based tool selection failed: {e}")
            raise

    async def _execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single tool

        Args:
            tool_id: Tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result with timing
        """
        start_time = time.time()

        try:
            result = await self.tool_registry.execute_tool(tool_id, parameters)

            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time_ms,
                "error": None
            }

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            logger.error(f"Tool execution failed: {e}")

            return {
                "success": False,
                "result": None,
                "execution_time_ms": execution_time_ms,
                "error": str(e)
            }

    async def _execute_tools_parallel(
        self,
        tool_ids: List[str],
        tool_params: Dict[str, Dict[str, Any]],
        timeout: float = 60.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple tools in parallel with timeout (Phase 4)

        Uses asyncio.gather() to run tools concurrently, with individual
        timeouts for each tool to prevent hanging.

        Args:
            tool_ids: List of tool IDs to execute
            tool_params: Parameters for each tool
            timeout: Timeout in seconds for each tool (default: 60s)

        Returns:
            Dictionary mapping tool_id to execution result
        """
        async def execute_with_timeout(tool_id: str) -> tuple[str, Dict[str, Any]]:
            """Execute single tool with timeout"""
            try:
                # Execute tool with timeout
                result = await asyncio.wait_for(
                    self._execute_tool(tool_id, tool_params[tool_id]),
                    timeout=timeout
                )
                return (tool_id, result)

            except asyncio.TimeoutError:
                logger.error(f"Tool {tool_id} timed out after {timeout}s")
                return (tool_id, {
                    "success": False,
                    "result": None,
                    "execution_time_ms": timeout * 1000,
                    "error": f"Timeout after {timeout}s"
                })

            except Exception as e:
                logger.error(f"Tool {tool_id} execution failed: {e}", exc_info=True)
                return (tool_id, {
                    "success": False,
                    "result": None,
                    "execution_time_ms": 0,
                    "error": str(e)
                })

        # Create tasks for all tools
        tasks = [execute_with_timeout(tool_id) for tool_id in tool_ids]

        # Execute all tasks in parallel
        logger.info(f"Executing {len(tasks)} tools in parallel with {timeout}s timeout")
        start_time = time.time()

        # Gather results (continue even if some fail)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = (time.time() - start_time) * 1000
        logger.info(f"Parallel execution completed in {total_time:.2f}ms")

        # Build result dictionary
        tool_results = {}
        for result in results:
            if isinstance(result, Exception):
                # Handle unexpected exceptions
                logger.error(f"Unexpected exception in parallel execution: {result}")
                continue

            tool_id, tool_result = result
            tool_results[tool_id] = tool_result

            # Log result status
            if tool_result["success"]:
                logger.info(
                    f"Tool {tool_id} succeeded in {tool_result['execution_time_ms']:.2f}ms"
                )
            else:
                logger.warning(
                    f"Tool {tool_id} failed: {tool_result['error']}"
                )

        return tool_results

    def _format_tool_results_as_context(
        self,
        query: str,
        tool_id: str,
        tool_result: Dict[str, Any]
    ) -> str:
        """
        Format tool results as context for RAG service

        Instead of synthesizing ourselves, we format tool results and let
        RAG service generate the answer using the user's chosen model.

        Args:
            query: Original user query
            tool_id: Tool that was used
            tool_result: Result from the tool

        Returns:
            Formatted context string for RAG service
        """
        result_data = tool_result["result"]

        if tool_id == "smart_extraction":
            table_data = result_data.get("table", [])
            row_count = result_data.get("row_count", 0)
            url = result_data.get("url", "")

            if row_count == 0:
                context = f"I extracted data from {url} but found no results."
            else:
                # Show sample data
                sample_rows = table_data[:10]
                context = f"Data extracted from {url} ({row_count} records total):\n\n"
                for i, row in enumerate(sample_rows, 1):
                    context += f"{i}. {row}\n"
                if row_count > 10:
                    context += f"\n... and {row_count - 10} more records"

        elif tool_id == "web_scraper":
            text = result_data.get("text", "")
            url = result_data.get("url", "unknown")
            context = f"Content from {url}:\n\n{text[:2000]}"  # First 2000 chars

        elif tool_id == "document_rag":
            # For document RAG, just return the sources as context
            sources = result_data.get("sources", [])
            if sources:
                context = "Relevant information from documents:\n\n"
                for i, source in enumerate(sources[:5], 1):
                    content = source.get("content", "")[:500]
                    context += f"Document {i}: {content}\n\n"
            else:
                context = "No relevant documents found."

        else:
            context = str(result_data)

        return context

    async def _generate_response(self, state: EnhancedAgentState) -> Dict[str, Any]:
        """
        Generate final response using RAG service with user's chosen model

        Architecture:
        1. GPT-4 selects tools (function calling)
        2. If no tool → RAG service directly
        3. If tools chosen → format results as context → RAG service

        Args:
            state: Agent state with tool results

        Returns:
            Response generated by RAG service using user's chosen model
        """
        # Get the tool result
        tool_id = state["selected_tools"][0]
        tool_result = state["tool_results"][tool_id]

        if not tool_result["success"]:
            return {
                "answer": f"I encountered an error: {tool_result['error']}",
                "sources": [],
                "metadata": {
                    "error": tool_result["error"],
                    "tool_used": tool_id
                }
            }

        result_data = tool_result["result"]

        # Special handling for document_rag - it already has answer from RAG service
        if tool_id == "document_rag":
            # Document RAG already used the user's chosen model via RAG service
            # Just return the result as-is, including quality_metrics
            sources = result_data.get("sources", [])
            answer = result_data.get("answer", "I don't have any information about that in my documents.")

            response = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    **result_data.get("metadata", {}),
                    "synthesis_method": "rag_service"
                }
            }

            # ✅ Pass through quality_metrics if present
            if "quality_metrics" in result_data:
                response["quality_metrics"] = result_data["quality_metrics"]

            return response

        # For other tools (smart_extraction, web_scraper, etc.):
        # Format tool results as context and let RAG service generate natural answer

        # Format tool results as context
        context = self._format_tool_results_as_context(
            state["query"],
            tool_id,
            tool_result
        )

        # Get user's chosen model from preferences
        model_id = state["user_preferences"].get("model_id")

        # Call RAG service to generate natural language answer using user's model
        from app.services.rag_service import rag_service

        try:
            # Create a synthetic query that includes the context
            synthesis_query = f"""Based on the following information, {state["query"]}

Context:
{context}"""

            # Call RAG service with user's chosen model and threshold parameters
            rag_response = await rag_service.query(
                query_text=synthesis_query,
                conversation_history=None,
                use_cache=False,  # Don't cache synthesis queries
                model_id=model_id,  # Use user's chosen model
                db=state["user_preferences"].get("db"),
                # Pass through threshold parameters from UI
                top_k=state["user_preferences"].get("top_k"),
                similarity_threshold=state["user_preferences"].get("similarity_threshold"),
                min_similarity_threshold=state["user_preferences"].get("min_similarity_threshold"),
                no_relevant_docs_threshold=state["user_preferences"].get("no_relevant_docs_threshold")
            )

            # Extract answer from RAG service response
            answer = rag_response.get("answer", context)

        except Exception as e:
            logger.warning(f"RAG service synthesis failed, using context directly: {e}")
            # Fallback to returning formatted context
            answer = context

        # Build sources based on tool type
        if tool_id == "smart_extraction":
            table_data = result_data.get("table", [])
            row_count = result_data.get("row_count", 0)

            return {
                "answer": answer,
                "sources": [{
                    "type": "web_extraction",
                    "url": state["tool_params"][tool_id].get("url", ""),
                    "data": table_data,
                    "extraction_metadata": result_data.get("extraction_metadata", {})
                }],
                "metadata": {
                    "extraction_method": result_data.get("extraction_metadata", {}).get("extraction_method", ""),
                    "row_count": row_count,
                    "synthesis_method": "rag_service"
                }
            }

        elif tool_id == "web_scraper":
            text = result_data.get("text", "")

            return {
                "answer": answer,
                "sources": [{
                    "type": "web_scrape",
                    "html_length": len(result_data.get("html", "")),
                    "text_length": len(text)
                }],
                "metadata": {
                    **result_data.get("metadata", {}),
                    "synthesis_method": "rag_service"
                }
            }

        else:
            # Generic response
            return {
                "answer": answer,
                "sources": [],
                "metadata": {
                    "synthesis_method": "rag_service"
                }
            }

    def _infer_intent_from_tool(self, tool_id: str) -> str:
        """Infer intent from selected tool"""
        intent_map = {
            "document_rag": "document_qa",
            "smart_extraction": "web_extraction",
            "web_scraper": "web_scraping",
            "template_extraction": "template_extraction",
            "docling_pdf": "pdf_processing",
            "ocr": "image_ocr",
            "navigation_agent": "web_navigation"
        }

        return intent_map.get(tool_id, "general")

    async def _fallback_to_basic_rag(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback to basic RAG if enhanced agent fails

        Args:
            query: User query
            session_id: Optional session ID

        Returns:
            Basic RAG response
        """
        try:
            # Use parent class run method
            result = await super().run(query)

            # Add fallback metadata
            if "metadata" not in result:
                result["metadata"] = {}

            result["metadata"]["fallback"] = True
            result["metadata"]["fallback_reason"] = "enhanced_agent_error"

            return result

        except Exception as e:
            logger.error(f"Fallback also failed: {e}")

            return {
                "answer": "I apologize, but I encountered an error processing your request.",
                "sources": [],
                "metadata": {
                    "error": str(e),
                    "fallback": True
                }
            }


# Global instance
enhanced_rag_agent = EnhancedRAGAgent()
