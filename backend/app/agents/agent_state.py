"""
Agent State Definitions

Defines state structures for the multi-tool AI agent.
"""

from typing import TypedDict, Sequence, List, Dict, Any, Optional
from langchain.schema import BaseMessage


class EnhancedAgentState(TypedDict):
    """
    Enhanced state for multi-tool AI agent

    This state tracks the agent's workflow through multiple phases:
    1. Intent analysis - Understanding what the user wants
    2. Tool selection - Choosing appropriate tools
    3. Tool execution - Running selected tools
    4. Result synthesis - Combining multi-tool outputs
    5. Response generation - Creating final answer
    """

    # ========================================================================
    # Input
    # ========================================================================

    query: str
    """User's natural language query"""

    session_id: Optional[str]
    """Session ID for memory hierarchy and context"""

    user_preferences: Dict[str, Any]
    """User-specific preferences (model, language, etc.)"""

    messages: Sequence[BaseMessage]
    """Conversation history as LangChain messages"""

    # ========================================================================
    # Intent Analysis Phase
    # ========================================================================

    detected_intent: str
    """
    Detected user intent

    Possible values:
    - document_qa: Answer questions from uploaded documents
    - web_extraction: Extract data from websites
    - pdf_processing: Process PDF documents
    - image_ocr: Extract text from images
    - web_navigation: Navigate websites to find information
    - multi_step: Complex workflow requiring multiple tools
    - general: General question/conversation
    """

    confidence: float
    """Confidence score for detected intent (0.0-1.0)"""

    intent_reasoning: str
    """LLM's reasoning for why this intent was detected"""

    # ========================================================================
    # Tool Selection Phase
    # ========================================================================

    selected_tools: List[str]
    """List of tool IDs selected for execution"""

    tool_params: Dict[str, Dict[str, Any]]
    """
    Parameters for each selected tool

    Format:
    {
        "tool_id": {
            "param1": value1,
            "param2": value2
        }
    }
    """

    tool_selection_reasoning: str
    """LLM's reasoning for tool selection"""

    # ========================================================================
    # Tool Execution Phase
    # ========================================================================

    tool_results: Dict[str, Any]
    """
    Results from each executed tool

    Format:
    {
        "tool_id": {
            "success": bool,
            "result": Any,
            "execution_time_ms": float
        }
    }
    """

    tool_errors: Dict[str, str]
    """Errors from failed tool executions"""

    # ========================================================================
    # Result Synthesis Phase
    # ========================================================================

    synthesized_data: Any
    """Combined/synthesized results from multiple tools"""

    synthesis_method: str
    """Method used to synthesize results (single_tool, merge, llm_synthesis)"""

    # ========================================================================
    # Response Generation Phase
    # ========================================================================

    answer: str
    """Final answer to return to the user"""

    sources: List[Dict[str, Any]]
    """Source citations and references"""

    metadata: Dict[str, Any]
    """
    Metadata about the response

    Includes:
    - tools_used: List of tool names
    - tool_timing: Execution time for each tool
    - total_time_ms: Total processing time
    - model_used: LLM model used
    - tokens_used: Token count
    """

    # ========================================================================
    # Workflow Control
    # ========================================================================

    next_action: str
    """Next action to take in the workflow"""

    retry_count: int
    """Number of retries for failed operations"""

    validation_result: str
    """Result of response validation (complete, regenerate, refine)"""


class ToolExecutionResult(TypedDict):
    """Result from executing a single tool"""

    success: bool
    """Whether the tool executed successfully"""

    result: Any
    """Tool output data"""

    execution_time_ms: float
    """Time taken to execute the tool"""

    error: Optional[str]
    """Error message if execution failed"""

    metadata: Dict[str, Any]
    """Additional metadata from tool execution"""


class IntentAnalysisResult(TypedDict):
    """Result from intent analysis"""

    intent: str
    """Detected intent type"""

    confidence: float
    """Confidence score (0.0-1.0)"""

    reasoning: str
    """LLM's reasoning for this classification"""

    suggested_tools: List[str]
    """Tools suggested for this intent"""


class ToolSelectionResult(TypedDict):
    """Result from tool selection"""

    selected_tools: List[str]
    """List of selected tool IDs"""

    tool_params: Dict[str, Dict[str, Any]]
    """Parameters for each tool"""

    reasoning: str
    """LLM's reasoning for tool selection"""

    estimated_time_ms: float
    """Estimated total execution time"""
