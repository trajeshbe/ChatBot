"""
Agent Container Entry Point

Runs autonomously inside Docker container with:
- Layer 1: Orchestration (session, tools, safety)
- Layer 2: Agentic Loop (THINK → PLAN → ACT → OBSERVE)
- Layer 3: Execution (Python, bash, file ops)

Entry point receives task config and executes autonomously.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Layer 1: Orchestration Layer

    Manages:
    - Session state
    - Tool registry
    - Safety checks
    - Context management
    """

    def __init__(self, task_id: str, session_id: str, workspace: Path):
        self.task_id = task_id
        self.session_id = session_id
        self.workspace = workspace

        # Create workspace directories
        self.input_dir = workspace / "input"
        self.output_dir = workspace / "output"
        self.artifacts_dir = workspace / "artifacts"
        self.temp_dir = workspace / "temp"

        for dir_path in [self.input_dir, self.output_dir, self.artifacts_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Session state (must be created before enhanced tools)
        self.session_state = {
            "task_id": task_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "initialized",
            "artifacts": [],
            "tool_calls": []
        }

        # Initialize enhanced tools (Month 1 & 2)
        sys.path.insert(0, '/app')
        from agent_tools_enhanced import EnhancedAgentTools
        self.enhanced_tools = EnhancedAgentTools(
            workspace=self.workspace,
            artifacts_dir=self.artifacts_dir,
            session_state=self.session_state
        )

        # Tool registry
        self.available_tools = self._register_tools()

        # Safety limits
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            '.py', '.txt', '.json', '.csv', '.md', '.yaml', '.yml',
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.xlsx', '.xls', '.docx', '.pptx'
        }

        logger.info(f"🎭 Orchestrator initialized for task {task_id}")

    def _register_tools(self) -> Dict[str, Any]:
        """Register available tools"""
        tools = {
            # ================================================================
            # TIER 1: CORE SYSTEM TOOLS (Basic Operations)
            # ================================================================
            "execute_python": {
                "description": "Execute Python code. Args: code (string)",
                "function": self._execute_python
            },
            "execute_bash": {
                "description": "Execute bash command. Args: command (string)",
                "function": self._execute_bash
            },
            "read_file": {
                "description": "Read file contents. Args: path (string, e.g. 'sales2.txt' or 'data/file.csv')",
                "function": self._read_file
            },
            "write_file": {
                "description": "Write file contents. Args: path (string), content (string)",
                "function": self._write_file
            },
            "list_directory": {
                "description": "List directory contents. Args: path (string, default '.')",
                "function": self._list_directory
            },
            "install_package": {
                "description": "Install Python package. Args: package (string, e.g. 'pandas' or 'matplotlib')",
                "function": self._install_package
            },

            # ================================================================
            # TIER 2: DATA PROCESSING TOOLS (Month 1 - Data Science)
            # ================================================================
            "analyze_dataframe": {
                "description": "Comprehensive EDA on CSV/Excel data with summary statistics, correlations, missing values, and automated visualizations",
                "function": self.enhanced_tools.analyze_dataframe
            },
            "visualize_data": {
                "description": "Create charts and visualizations (scatter, line, bar, box, histogram) from data files with auto-detection",
                "function": self.enhanced_tools.visualize_data
            },

            # ================================================================
            # TIER 3: DOCUMENT EXTRACTION TOOLS (Month 1 - Documents)
            # ================================================================
            "extract_pdf_content": {
                "description": "Extract text and tables from PDF using multi-strategy approach (docling → pdfplumber → OCR). Exports to text and CSV files",
                "function": self.enhanced_tools.extract_pdf_content
            },
            "analyze_excel_workbook": {
                "description": "Deep Excel analysis with multi-sheet support, formula extraction, and summary statistics. Exports each sheet to CSV",
                "function": self.enhanced_tools.analyze_excel_workbook
            },
            "extract_word_document": {
                "description": "Extract text, tables, and metadata from Word documents (.docx). Exports tables to CSV",
                "function": self.enhanced_tools.extract_word_document
            },

            # ================================================================
            # TIER 4: VISION & OCR TOOLS (Month 2 - Vision)
            # ================================================================
            "analyze_image_with_vision": {
                "description": "Use llama3.2-vision model to understand and analyze images, charts, diagrams, and complex visual layouts",
                "function": self.enhanced_tools.analyze_image_with_vision
            },
            "extract_text_from_image": {
                "description": "OCR text extraction from images using tesseract (fast, clean text) or easyocr (handwriting). Exports to text file",
                "function": self.enhanced_tools.extract_text_from_image
            }
        }

        logger.info(f"📚 Registered {len(tools)} tools (6 core + 7 enhanced + install_package)")
        return tools

    def validate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Safety check for tool calls"""

        # Check if tool exists
        if tool_name not in self.available_tools:
            logger.warning(f"⚠️ Unknown tool: {tool_name}")
            return False

        # Specific validations
        if tool_name == "execute_bash":
            # Block dangerous commands
            code = args.get("command", "")
            dangerous_commands = ["rm -rf /", "dd if=", "mkfs", "format", "> /dev/"]
            if any(cmd in code for cmd in dangerous_commands):
                logger.error(f"🚨 Blocked dangerous bash command: {code}")
                return False

        if tool_name in ["read_file", "write_file"]:
            # Validate file path is within workspace
            file_path = Path(args.get("path", ""))
            try:
                file_path.resolve().relative_to(self.workspace.resolve())
            except ValueError:
                logger.error(f"🚨 File access outside workspace: {file_path}")
                return False

        return True

    async def _execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code with output capture"""
        try:
            import io
            import sys

            # Capture stdout
            stdout_buffer = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout_buffer

            # Create safe execution environment with common libraries pre-imported
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            from pathlib import Path

            exec_globals = {
                '__builtins__': __builtins__,
                'pd': pd,
                'np': np,
                'plt': plt,
                'Path': Path,
                'print': print,  # Explicitly include print function
            }

            # Execute code
            exec(code, exec_globals)

            # Restore stdout
            sys.stdout = old_stdout
            output = stdout_buffer.getvalue()

            return {
                "success": True,
                "result": output if output else "Code executed successfully",
                "output": output
            }
        except Exception as e:
            # Restore stdout if error
            if 'old_stdout' in locals():
                sys.stdout = old_stdout
            logger.error(f"Python execution error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _install_package(self, package: str) -> Dict[str, Any]:
        """
        Install Python package using pip.

        Args:
            package: Package name (e.g., 'scikit-learn', 'seaborn==0.12.0')

        Returns:
            dict with success status and output
        """
        try:
            import subprocess

            # Security: validate package name format
            if not package or any(char in package for char in [';', '&', '|', '`', '$', '(', ')']):
                return {"success": False, "error": "Invalid package name"}

            logger.info(f"📦 Installing package: {package}")

            # Run pip install with timeout
            result = subprocess.run(
                ["pip", "install", "--no-cache-dir", package],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes for package installation
                cwd=str(self.workspace)
            )

            if result.returncode == 0:
                logger.info(f"✅ Package installed successfully: {package}")
                return {
                    "success": True,
                    "package": package,
                    "output": result.stdout,
                    "message": f"Successfully installed {package}"
                }
            else:
                logger.error(f"❌ Package installation failed: {result.stderr}")
                return {
                    "success": False,
                    "package": package,
                    "error": result.stderr
                }

        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Package installation timeout: {package}")
            return {"success": False, "error": f"Installation timeout after 120s"}
        except Exception as e:
            logger.error(f"❌ Package installation error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _execute_bash(self, command: str) -> Dict[str, Any]:
        """Execute bash command"""
        try:
            import subprocess

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace)
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            logger.error(f"Bash execution error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents"""
        try:
            file_path = self.workspace / path

            if not file_path.exists():
                return {"success": False, "error": "File not found"}

            if file_path.stat().st_size > self.max_file_size:
                return {"success": False, "error": "File too large"}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {"success": True, "content": content}
        except Exception as e:
            logger.error(f"File read error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file contents"""
        try:
            file_path = self.workspace / path

            # Validate extension
            if file_path.suffix not in self.allowed_extensions:
                return {"success": False, "error": f"File extension {file_path.suffix} not allowed"}

            # Write file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Track as artifact
            self.session_state["artifacts"].append({
                "path": str(file_path.relative_to(self.workspace)),
                "size": file_path.stat().st_size,
                "created_at": datetime.utcnow().isoformat()
            })

            return {"success": True, "path": str(file_path)}
        except Exception as e:
            logger.error(f"File write error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List directory contents"""
        try:
            dir_path = self.workspace / path

            if not dir_path.exists() or not dir_path.is_dir():
                return {"success": False, "error": "Directory not found"}

            files = []
            for item in dir_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })

            return {"success": True, "files": files}
        except Exception as e:
            logger.error(f"Directory list error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _install_package(self, package: str) -> Dict[str, Any]:
        """Install Python package"""
        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            logger.error(f"Package install error: {str(e)}")
            return {"success": False, "error": str(e)}


class AgenticLoop:
    """
    Layer 2: Agentic Loop

    Implements: THINK → PLAN → ACT → OBSERVE
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        llm_client: Any,
        max_iterations: int = 20
    ):
        self.orchestrator = orchestrator
        self.llm_client = llm_client
        self.max_iterations = max_iterations

        self.conversation_history = []
        self.iteration = 0

        logger.info(f"🔄 Agentic loop initialized (max {max_iterations} iterations)")

    async def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agentic loop

        Returns task completion result with artifacts
        """

        logger.info(f"🚀 Starting task: {task[:100]}...")

        # Initialize with task
        self.conversation_history.append({
            "role": "user",
            "content": task
        })

        task_complete = False
        final_answer = None

        while self.iteration < self.max_iterations and not task_complete:
            self.iteration += 1

            logger.info(f"📍 Iteration {self.iteration}/{self.max_iterations}")

            # THINK & PLAN: Call LLM
            response = await self._call_llm()

            # CRITICAL: Add LLM response to conversation BEFORE processing action
            # This maintains proper conversation structure (user → assistant → user → assistant...)
            if response and response.strip():
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

            # Parse response for tool calls or final answer
            action = self._parse_response(response)

            if action["type"] == "final_answer":
                # SAFETY CHECK: Reject FINAL_ANSWER if insufficient tools were used (prevents hallucination)
                tool_calls = self.orchestrator.session_state["tool_calls"]
                tools_used = len(tool_calls)
                tool_names = [call["tool"] for call in tool_calls]

                # For visualization/analysis tasks, require execute_python
                task_lower = task.lower()
                if any(word in task_lower for word in ["visualiz", "chart", "plot", "graph", "analyze", "analysis"]):
                    if "execute_python" not in tool_names:
                        logger.warning(f"⚠️ Task requires visualization/analysis but execute_python was not called!")
                        self.conversation_history.append({
                            "role": "system",
                            "content": f"ERROR: This task requires creating visualizations or analysis. You MUST call execute_python to write and run code that creates charts/visualizations and saves them to /workspace/artifacts/. Tools called so far: {tool_names}. You need to call execute_python next."
                        })
                        continue

                # General check: require at least one tool for any task
                if tools_used == 0:
                    logger.warning(f"⚠️ LLM tried to finish without using tools!")
                    self.conversation_history.append({
                        "role": "system",
                        "content": "ERROR: You MUST use tools to complete this task. You cannot provide a final answer without using tools first."
                    })
                    continue

                # Task complete (only if appropriate tools were used)
                final_answer = action["content"]
                task_complete = True
                logger.info(f"✅ Task completed with final answer (after {tools_used} tool calls: {tool_names})")

            elif action["type"] == "tool_call":
                # ACT: Execute tool
                tool_name = action["tool"]
                tool_args = action["args"]

                logger.info(f"🔧 Executing tool: {tool_name}")

                # Validate and execute
                if self.orchestrator.validate_tool_call(tool_name, tool_args):
                    tool_function = self.orchestrator.available_tools[tool_name]["function"]
                    tool_result = await tool_function(**tool_args)

                    # Track tool call
                    self.orchestrator.session_state["tool_calls"].append({
                        "iteration": self.iteration,
                        "tool": tool_name,
                        "args": tool_args,
                        "result": tool_result,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    # OBSERVE: Add result to conversation
                    # Tool results should be "user" role (feedback TO the assistant)
                    # Convert tool result to JSON-safe string
                    try:
                        result_str = json.dumps(tool_result, default=str)
                    except Exception:
                        # Fallback: use string representation
                        result_str = str(tool_result)

                    self.conversation_history.append({
                        "role": "user",  # FIXED: Tool results are user messages (feedback)
                        "content": f"Tool Result:\nTool: {tool_name}\nResult: {result_str}"
                    })
                else:
                    logger.error(f"⚠️ Tool call validation failed: {tool_name}")
                    self.conversation_history.append({
                        "role": "system",
                        "content": f"Tool call blocked for safety: {tool_name}"
                    })

            else:
                # Thinking/reasoning step or empty response
                if action["content"] and action["content"].strip():
                    logger.info(f"💭 LLM thinking...")
                    # Response already added to conversation history above
                else:
                    logger.warning("⚠️ LLM sent empty content, skipping...")

        # Build final result
        result = {
            "success": task_complete,
            "final_answer": final_answer,
            "iterations": self.iteration,
            "artifacts": self.orchestrator.session_state["artifacts"],
            "tool_calls": len(self.orchestrator.session_state["tool_calls"]),
            "conversation_history": self.conversation_history
        }

        if not task_complete:
            result["reason"] = "Max iterations reached"
            logger.warning(f"⚠️ Max iterations ({self.max_iterations}) reached without completion")

        return result

    def _compress_history(self, messages: list, max_messages: int = 6) -> list:
        """
        Compress conversation history to prevent context overflow.
        Keeps first message (task) + recent messages + summary of middle messages.
        """
        if len(messages) <= max_messages:
            return messages

        # Strategy: Keep first (task) + summarize middle + keep last 3 (recent context)
        first_message = messages[0]
        recent_messages = messages[-3:]
        middle_messages = messages[1:-3]

        # Create summary of middle messages
        middle_summary = []
        tool_calls_summary = []
        for msg in middle_messages:
            content = msg.get("content", "")
            if "Tool:" in content:
                # Extract tool name
                tool_name = content.split("Tool:")[1].split(",")[0].strip()
                tool_calls_summary.append(tool_name)

        # Build compressed history
        compressed = [first_message]

        if tool_calls_summary:
            compressed.append({
                "role": "system",
                "content": f"[Summary: Used tools: {', '.join(set(tool_calls_summary))}]"
            })

        compressed.extend(recent_messages)

        logger.info(f"📜 History compressed: {len(messages)} → {len(compressed)} messages")
        return compressed

    async def _call_llm(self) -> str:
        """Call LLM with conversation history"""
        try:
            import ollama

            # Get Ollama configuration from environment
            ollama_host = os.getenv('OLLAMA_HOST', 'http://rag-ollama:11434')
            model = os.getenv('AGENT_LLM_MODEL', 'llama3.2-vision:11b')

            # IMPORTANT: Compress conversation history to prevent context overflow
            # For small models like qwen2.5:1.5b (context ~32K tokens), keep history manageable
            compressed_history = self._compress_history(
                messages=self.conversation_history,
                max_messages=6  # Keep task + summary + 3 recent messages
            )

            # Build system prompt with available tools
            available_tools_desc = "\n".join([
                f"- {name}: {tool.get('description', 'No description')}"
                for name, tool in self.orchestrator.available_tools.items()
            ])

            system_prompt = f"""You are a TOOL-CALLING AI agent. Your ONLY job is to call tools to complete tasks.

⚠️ CRITICAL RULES:
1. NEVER write explanations, plans, or descriptions
2. NEVER say "we should do X" or "let's start by doing Y"
3. IMMEDIATELY call a tool in EVERY response
4. If no more tools needed → use FINAL_ANSWER

🔧 AUTONOMOUS CAPABILITIES:
- Install ANY Python package: use `install_package` tool
- Execute ANY Python code: use `execute_python` tool
- Read/write files, run bash commands, analyze data

📋 Available Tools:
{available_tools_desc}

🎯 RESPONSE FORMAT (STRICT):

✅ CORRECT - Immediately call tool:
TOOL_CALL: read_file
ARGS: {{"path": "sales.txt"}}

❌ WRONG - Do NOT explain or describe:
"To analyze sales.txt, we should first read the file using read_file..."  ← NEVER DO THIS!

📚 EXAMPLES:

Example 1 - Data Analysis:
User: "Analyze sales.txt and create chart"

Your Response (Step 1):
TOOL_CALL: read_file
ARGS: {{"path": "sales.txt"}}

Your Response (Step 2 - after seeing data):
TOOL_CALL: execute_python
ARGS: {{"code": "import pandas as pd\\nimport matplotlib.pyplot as plt\\ndf = pd.read_csv('sales.txt', sep='\\\\t')\\nplt.bar(df['Product'], df['Revenue'])\\nplt.savefig('/workspace/artifacts/chart.png')\\nprint('Done')"}}

Your Response (Step 3):
FINAL_ANSWER: Chart created at /workspace/artifacts/chart.png showing revenue by product

Example 2 - ML Task (needs package):
User: "Build XGBoost model on data.csv"

Your Response (Step 1):
TOOL_CALL: install_package
ARGS: {{"package": "xgboost"}}

Your Response (Step 2):
TOOL_CALL: read_file
ARGS: {{"path": "data.csv"}}

Your Response (Step 3):
TOOL_CALL: execute_python
ARGS: {{"code": "import pandas as pd\\nimport xgboost as xgb\\ndf = pd.read_csv('data.csv')\\nX = df.drop('target', axis=1)\\ny = df['target']\\nmodel = xgb.XGBRegressor()\\nmodel.fit(X, y)\\nprint(f'Model R2: {{model.score(X, y):.3f}}')"}}

Your Response (Step 4):
FINAL_ANSWER: XGBoost model trained with R² score displayed in output

🚀 START NOW - Call your first tool immediately!"""

            # Build messages for LLM
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(compressed_history)  # Use compressed history to prevent context overflow

            # Connect to Ollama
            client = ollama.Client(host=ollama_host)

            # Call LLM (IMPORTANT: stream=False to get complete response)
            logger.info(f"🤖 Calling LLM: {model}")
            response = client.chat(model=model, messages=messages, stream=False)

            llm_response = response['message']['content']
            logger.info(f"💬 LLM responded ({len(llm_response)} chars): {llm_response[:200]}...")

            return llm_response

        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            # Fallback: provide a sensible default response
            return f"FINAL_ANSWER: I encountered an error: {str(e)}. The task could not be completed."

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for actions"""

        # Check for final answer
        if "FINAL_ANSWER:" in response:
            return {
                "type": "final_answer",
                "content": response.split("FINAL_ANSWER:")[1].strip()
            }

        # Check for tool call
        if "TOOL_CALL:" in response:
            try:
                # Parse tool name and arguments from LLM response
                lines = response.split('\n')

                # Extract tool name
                tool_line = [l for l in lines if l.strip().startswith('TOOL_CALL:')]
                if not tool_line:
                    logger.warning("⚠️ TOOL_CALL found but couldn't parse tool name")
                    return {"type": "thinking", "content": response}

                tool_name = tool_line[0].replace('TOOL_CALL:', '').strip()

                # Extract arguments
                args_line = [l for l in lines if l.strip().startswith('ARGS:')]
                if not args_line:
                    logger.warning("⚠️ TOOL_CALL found but no ARGS provided")
                    # Try with empty args
                    return {
                        "type": "tool_call",
                        "tool": tool_name,
                        "args": {}
                    }

                args_json = args_line[0].replace('ARGS:', '').strip()

                # Parse JSON arguments
                try:
                    args = json.loads(args_json)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse tool arguments JSON: {e}")
                    logger.error(f"   Raw args: {args_json}")
                    return {"type": "thinking", "content": response}

                logger.info(f"✅ Parsed tool call: {tool_name} with args: {args}")

                return {
                    "type": "tool_call",
                    "tool": tool_name,
                    "args": args
                }

            except Exception as e:
                logger.error(f"❌ Error parsing tool call: {e}")
                return {"type": "thinking", "content": response}

        # Default: thinking/reasoning step
        return {
            "type": "thinking",
            "content": response
        }


async def main():
    """Main entry point"""

    logger.info("=" * 80)
    logger.info("🤖 AGENT CONTAINER STARTING")
    logger.info("=" * 80)

    # Parse input (try stdin first, then fall back to env vars)
    task_config = {}

    # Try to read from stdin if available
    try:
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                task_config = json.loads(stdin_data)
    except Exception as e:
        logger.warning(f"Could not read from stdin: {str(e)}, using env vars")

    # Get values from config or env vars (env vars as fallback)
    task_id = task_config.get("task_id") or os.getenv("TASK_ID", "default")
    session_id = task_config.get("session_id") or os.getenv("SESSION_ID", "default")

    # Get task - try base64 encoded first (newer method), then plain text (legacy)
    task = task_config.get("task")
    logger.info(f"DEBUG: task from config: {repr(task)}")
    if not task:
        import base64
        task_b64 = os.getenv("TASK_B64")
        logger.info(f"DEBUG: TASK_B64 env var: {repr(task_b64)}")
        if task_b64:
            try:
                task = base64.b64decode(task_b64.encode('utf-8')).decode('utf-8')
                logger.info("✅ Decoded base64 task description")
            except Exception as e:
                logger.warning(f"Failed to decode TASK_B64: {e}, falling back to TASK env var")
                task = os.getenv("TASK", "No task specified")
        else:
            logger.warning("⚠️  TASK_B64 not found, using default")
            task = os.getenv("TASK", "No task specified")

    max_iterations = task_config.get("max_iterations") or int(os.getenv("AGENT_MAX_ITERATIONS", "20"))

    workspace = Path(os.getenv("AGENT_WORKSPACE", "/workspace"))

    logger.info(f"📋 Task ID: {task_id}")
    logger.info(f"🔖 Session ID: {session_id}")
    logger.info(f"📁 Workspace: {workspace}")
    logger.info(f"🔄 Max Iterations: {max_iterations}")
    logger.info(f"📝 Task: {task[:200]}...")

    # Layer 1: Initialize orchestrator
    orchestrator = AgentOrchestrator(
        task_id=task_id,
        session_id=session_id,
        workspace=workspace
    )

    # Layer 2: Initialize agentic loop
    # TODO: Initialize actual LLM client based on agent type
    llm_client = None  # Placeholder

    agentic_loop = AgenticLoop(
        orchestrator=orchestrator,
        llm_client=llm_client,
        max_iterations=max_iterations
    )

    # Execute task
    try:
        result = await agentic_loop.run(
            task=task,
            context=task_config.get("context", {})
        )

        # Save result to output
        output_file = orchestrator.output_dir / "result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info("=" * 80)
        logger.info(f"✅ TASK COMPLETED: {result['success']}")
        logger.info(f"📊 Iterations: {result['iterations']}")
        logger.info(f"📁 Artifacts: {len(result['artifacts'])}")
        logger.info("=" * 80)

        # Exit with success
        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
