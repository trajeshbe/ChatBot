"""
Task Complexity Analyzer

Classifies user queries by complexity to route to appropriate execution strategy:
- Simple: Direct LLM/RAG
- Medium: Mini coding agent (quick scripts)
- Complex: Full autonomous agent (multi-step workflows)
"""

from typing import Dict, Any, Tuple
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"  # Direct LLM/RAG response
    MEDIUM = "medium"  # Quick coding agent (single file, simple script)
    COMPLEX = "complex"  # Full autonomous workflow (multi-file, iterative)


class TaskType(str, Enum):
    """Task types that may trigger agent execution"""
    CONVERSATIONAL = "conversational"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    VISION_TASK = "vision_task"
    DOCUMENT_PROCESSING = "document_processing"
    WEB_AUTOMATION = "web_automation"
    RESEARCH = "research"


class TaskComplexityAnalyzer:
    """
    Analyzes query complexity to determine execution strategy

    Uses keyword-based + LLM-based classification
    """

    def __init__(self):
        """Initialize complexity analyzer"""

        # Keywords that indicate medium complexity (coding needed)
        self.medium_keywords = [
            "create a script",
            "write code",
            "generate python",
            "build a function",
            "parse this data",
            "calculate",
            "transform data",
            "analyze this file",
            "plot",
            "visualize",
            "chart"
        ]

        # Keywords that indicate complex tasks (multi-step workflows)
        self.complex_keywords = [
            "exploratory data analysis",
            "eda",
            "comprehensive analysis",
            "end-to-end",
            "full pipeline",
            "research",
            "investigate",
            "build an application",
            "create a dashboard",
            "multi-step",
            "workflow",
            "automate this process"
        ]

        # Vision task indicators
        self.vision_keywords = [
            "image",
            "photo",
            "picture",
            "screenshot",
            "diagram",
            "chart",
            "graph",
            "ocr",
            "extract text from image",
            "visual"
        ]

    def analyze(
        self,
        query: str,
        conversation_history: list = None,
        uploaded_files: list = None
    ) -> Tuple[TaskComplexity, TaskType, Dict[str, Any]]:
        """
        Analyze query to determine complexity and type

        Args:
            query: User's query text
            conversation_history: Recent conversation messages
            uploaded_files: List of files uploaded in session

        Returns:
            Tuple of (complexity_level, task_type, metadata)
        """
        query_lower = query.lower()

        # Check for complex task indicators FIRST
        if self._is_complex_task(query_lower, uploaded_files):
            task_type = self._determine_task_type(query_lower, uploaded_files)

            return (
                TaskComplexity.COMPLEX,
                task_type,
                {
                    "reason": "Complex multi-step workflow detected",
                    "indicators": self._get_matched_keywords(query_lower, self.complex_keywords),
                    "recommended_agent": "full_autonomous",
                    "estimated_steps": self._estimate_steps(query_lower)
                }
            )

        # Check for medium complexity (coding needed)
        if self._is_medium_task(query_lower, uploaded_files):
            task_type = self._determine_task_type(query_lower, uploaded_files)

            return (
                TaskComplexity.MEDIUM,
                task_type,
                {
                    "reason": "Code generation or data processing required",
                    "indicators": self._get_matched_keywords(query_lower, self.medium_keywords),
                    "recommended_agent": "mini_coding",
                    "estimated_steps": 1
                }
            )

        # Default: Simple conversational task
        return (
            TaskComplexity.SIMPLE,
            TaskType.CONVERSATIONAL,
            {
                "reason": "Simple question-answer task",
                "recommended_agent": "rag_llm",
                "estimated_steps": 0
            }
        )

    def _is_complex_task(self, query_lower: str, uploaded_files: list = None) -> bool:
        """Check if task is complex (multi-step workflow)"""

        # Keyword-based check
        if any(keyword in query_lower for keyword in self.complex_keywords):
            return True

        # Multiple files + analysis = likely complex
        if uploaded_files and len(uploaded_files) > 2:
            if any(word in query_lower for word in ["analyze", "compare", "merge", "combine"]):
                return True

        # Long detailed prompt = likely complex
        if len(query_lower.split()) > 50:
            if any(word in query_lower for word in ["step", "first", "then", "finally", "pipeline"]):
                return True

        return False

    def _is_medium_task(self, query_lower: str, uploaded_files: list = None) -> bool:
        """Check if task needs code generation (medium complexity)"""

        # Keyword-based check
        if any(keyword in query_lower for keyword in self.medium_keywords):
            return True

        # Data file + processing request
        if uploaded_files:
            for file in uploaded_files:
                if any(ext in file.get('filename', '').lower() for ext in ['.csv', '.xlsx', '.json', '.xml']):
                    if any(word in query_lower for word in ["process", "parse", "extract", "calculate", "transform"]):
                        return True

        return False

    def _determine_task_type(self, query_lower: str, uploaded_files: list = None) -> TaskType:
        """Determine the type of task"""

        # Vision task
        if any(keyword in query_lower for keyword in self.vision_keywords):
            return TaskType.VISION_TASK

        # Data analysis (CSV, Excel, JSON)
        if uploaded_files:
            data_files = [f for f in uploaded_files if any(ext in f.get('filename', '').lower()
                          for ext in ['.csv', '.xlsx', '.json', '.parquet'])]
            if data_files and any(word in query_lower for word in ["analyze", "eda", "statistics", "plot"]):
                return TaskType.DATA_ANALYSIS

        # Code generation
        if any(word in query_lower for word in ["script", "code", "function", "class", "module"]):
            return TaskType.CODE_GENERATION

        # Web automation
        if any(word in query_lower for word in ["scrape", "automate", "navigate", "browser"]):
            return TaskType.WEB_AUTOMATION

        # Document processing
        if uploaded_files:
            doc_files = [f for f in uploaded_files if any(ext in f.get('filename', '').lower()
                        for ext in ['.pdf', '.docx', '.txt', '.md'])]
            if doc_files:
                return TaskType.DOCUMENT_PROCESSING

        # Research
        if any(word in query_lower for word in ["research", "investigate", "find information about"]):
            return TaskType.RESEARCH

        return TaskType.CONVERSATIONAL

    def _get_matched_keywords(self, query_lower: str, keyword_list: list) -> list:
        """Get list of matched keywords"""
        return [kw for kw in keyword_list if kw in query_lower]

    def _estimate_steps(self, query_lower: str) -> int:
        """Estimate number of steps needed"""

        # Count explicit steps
        step_indicators = len(re.findall(r'\b(step|stage|phase|first|second|third|then|next|finally)\b', query_lower))

        if step_indicators > 5:
            return 10  # Complex multi-step
        elif step_indicators > 2:
            return 5  # Medium multi-step
        else:
            return 3  # Default for complex tasks


# Global instance
task_complexity_analyzer = TaskComplexityAnalyzer()
