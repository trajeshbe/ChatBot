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

    def __init__(
        self,
        task_id: str,
        task_name: str,  # 🆕 NEW: Human-readable task name
        session_id: str,
        workspace: Path,
        username: str = "unknown",  # 🆕 NEW: For MinIO paths
        project_name: str = "global-project"  # 🆕 NEW: For MinIO paths
    ):
        self.task_id = task_id
        self.task_name = task_name
        self.session_id = session_id
        self.workspace = workspace
        self.username = username
        self.project_name = project_name

        # Create workspace directories
        self.input_dir = workspace / "input"
        self.output_dir = workspace / "output"
        self.artifacts_dir = workspace / "artifacts"
        self.logs_dir = workspace / "logs"  # 🆕 NEW: For logs
        self.temp_dir = workspace / "temp"

        for dir_path in [self.input_dir, self.output_dir, self.artifacts_dir, self.logs_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 🆕 Setup logging to file
        log_file = self.logs_dir / "agent.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

        # Session state (must be created before enhanced tools)
        self.session_state = {
            "task_id": task_id,
            "task_name": task_name,
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

            # For read_file: Allow reading from task workspace OR parent /workspace/ (for input files)
            # For write_file: Only allow writing to task workspace
            if tool_name == "read_file":
                parent_workspace = self.workspace.parent  # /workspace/
                try:
                    # Try task workspace first
                    file_path.resolve().relative_to(self.workspace.resolve())
                except ValueError:
                    # Try parent workspace
                    try:
                        file_path.resolve().relative_to(parent_workspace.resolve())
                        logger.info(f"✅ Allowing read from parent workspace: {file_path}")
                    except ValueError:
                        logger.error(f"🚨 File access outside allowed directories: {file_path}")
                        return False
            else:  # write_file
                try:
                    file_path.resolve().relative_to(self.workspace.resolve())
                except ValueError:
                    logger.error(f"🚨 Write access outside task workspace: {file_path}")
                    return False

        return True

    async def _execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code with output capture"""
        try:
            import io
            import sys
            import os

            # Change to task-specific workspace directory so relative paths work correctly
            original_cwd = os.getcwd()
            os.chdir(str(self.workspace))
            logger.info(f"📂 Changed working directory to: {self.workspace}")

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

            # Restore stdout and working directory
            sys.stdout = old_stdout
            os.chdir(original_cwd)
            output = stdout_buffer.getvalue()

            return {
                "success": True,
                "result": output if output else "Code executed successfully",
                "output": output
            }
        except Exception as e:
            # Restore stdout and working directory if error
            if 'old_stdout' in locals():
                sys.stdout = old_stdout
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
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
            # Try task workspace first
            file_path = self.workspace / path

            # If not found in task workspace, try parent /workspace/ (for input files)
            if not file_path.exists():
                parent_path = self.workspace.parent / path
                if parent_path.exists():
                    file_path = parent_path
                    logger.info(f"📖 Reading from parent workspace: {file_path}")
                else:
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

        # Scan workspace for any files created by Python code (not tracked by write_file tool)
        # Check both artifacts directory AND workspace root for generated files
        scan_dirs = [
            self.orchestrator.artifacts_dir,  # /workspace/artifacts/
            self.orchestrator.workspace       # /workspace/ (root)
        ]

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue

            # For workspace root, only check files directly in root (not subdirectories)
            files_to_check = []
            if scan_dir == self.orchestrator.workspace:
                # Workspace root: only direct files, skip directories
                files_to_check = [f for f in scan_dir.iterdir() if f.is_file()]
            else:
                # Artifacts dir: all files
                files_to_check = [f for f in scan_dir.iterdir() if f.is_file()]

            for artifact_file in files_to_check:
                # Check if already tracked
                artifact_path = str(artifact_file.relative_to(self.orchestrator.workspace))
                already_tracked = any(
                    a.get("path") == artifact_path
                    for a in self.orchestrator.session_state["artifacts"]
                )

                # Skip input files (sales2.txt, etc.)
                if artifact_file.name in ['sales2.txt', 'sales.txt', 'sales.csv', 'sales2.csv']:
                    continue

                if not already_tracked:
                    logger.info(f"📎 Found untracked artifact: {artifact_path}")
                    self.orchestrator.session_state["artifacts"].append({
                        "path": artifact_path,
                        "size": artifact_file.stat().st_size,
                        "created_at": datetime.utcnow().isoformat()
                    })

        # 🆕 Auto-complete detection: Check every 4 iterations if artifacts created
        # This handles local models (llama, qwen, deepseek) that don't reliably call FINAL_ANSWER
        # Check at iterations 4, 8, 12, 16, etc. to give agent multiple chances
        if not task_complete and len(self.orchestrator.session_state["artifacts"]) > 0:
            # Check every 4 iterations (4, 8, 12, 16, 20, etc.)
            if self.iteration >= 4 and self.iteration % 4 == 0:
                # Check if any artifact looks like requested output
                output_extensions = ['.html', '.png', '.jpg', '.jpeg', '.svg', '.pdf',
                                   '.csv', '.json', '.txt', '.xlsx', '.docx']
                for artifact in self.orchestrator.session_state["artifacts"]:
                    artifact_path = artifact.get("path", "")
                    if any(artifact_path.endswith(ext) for ext in output_extensions):
                        logger.info(f"✅ Auto-completing: Detected output file '{artifact_path}' after {self.iteration} iterations (checkpoint every 4 iterations)")
                        final_answer = f"Task completed. Created output file: {artifact_path}"
                        task_complete = True
                        break

        # 🆕 FINAL ARTIFACT SCAN - Scan workspace one more time AFTER loop completes
        # This catches files created in the last iteration (when FINAL_ANSWER is called)
        # Add to session_state["artifacts"] so it's included in the result dict below
        logger.info("🔍 Running final artifact scan after loop completion...")
        final_scan_dirs = [
            self.orchestrator.artifacts_dir,  # /workspace/artifacts/
            self.orchestrator.workspace       # /workspace/ (root)
        ]

        for scan_dir in final_scan_dirs:
            if not scan_dir.exists():
                continue

            files_to_check = []
            if scan_dir == self.orchestrator.workspace:
                # Workspace root: only direct files, skip directories
                files_to_check = [f for f in scan_dir.iterdir() if f.is_file()]
            else:
                # Artifacts dir: all files
                files_to_check = [f for f in scan_dir.iterdir() if f.is_file()]

            for artifact_file in files_to_check:
                artifact_path = str(artifact_file.relative_to(self.orchestrator.workspace))

                # Skip input files
                if artifact_file.name in ['sales2.txt', 'sales.txt', 'sales.csv', 'sales2.csv']:
                    continue

                # Check if already tracked
                already_tracked = any(
                    a.get("path") == artifact_path
                    for a in self.orchestrator.session_state["artifacts"]
                )

                if not already_tracked:
                    logger.info(f"📎 Final scan found artifact: {artifact_path}")
                    self.orchestrator.session_state["artifacts"].append({
                        "path": artifact_path,
                        "size": artifact_file.stat().st_size,
                        "created_at": datetime.utcnow().isoformat()
                    })

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
        """Call LLM with conversation history (OpenAI primary, Ollama fallback)"""
        # Get model from environment
        model = os.getenv('AGENT_LLM_MODEL', 'llama3.2-vision:11b')

        # Detect if OpenAI model
        openai_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4-vision-preview']
        is_openai = model.startswith('gpt-') or model in openai_models

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
ARGS: {{"code": "import pandas as pd\\nimport matplotlib.pyplot as plt\\nimport os\\n# Process data and create chart\\nos.makedirs('artifacts', exist_ok=True)\\nplt.bar(df['Product'], df['Revenue'])\\n# Save with RELATIVE path\\nplt.savefig('artifacts/chart.png')\\nprint('Done')"}}

Your Response (Step 3):
FINAL_ANSWER: Chart created at artifacts/chart.png showing revenue by product

Example 2 - CSV Analysis with read_file content (IMPORTANT):
User: "Analyze sales2.txt and create a plotly bar chart"

Your Response (Step 1):
TOOL_CALL: read_file
ARGS: {{"path": "sales2.txt"}}

Your Response (Step 2 - after getting file content):
TOOL_CALL: install_package
ARGS: {{"package": "plotly"}}

Your Response (Step 3 - use content from read_file):
TOOL_CALL: execute_python
ARGS: {{"code": "import pandas as pd\\nimport plotly.express as px\\nfrom io import StringIO\\nimport os\\n# Use the CONTENT from read_file (already in memory)\\n# The read_file tool returned the content, use it via StringIO\\ncontent = '''<file content from read_file result>'''\\ndf = pd.read_csv(StringIO(content), delimiter='\\\\t')\\nos.makedirs('artifacts', exist_ok=True)\\nfig = px.bar(df, x='product', y='revenue', title='Revenue by Product')\\nfig.write_html('artifacts/revenue_chart.html')\\nprint('Chart saved')"}}

Your Response (Step 4):
FINAL_ANSWER: Interactive Plotly chart saved to artifacts/revenue_chart.html

Example 3 - Plotly Interactive Chart (IMPORTANT):
User: "Create a plotly chart and save as HTML"

Your Response (Step 1):
TOOL_CALL: install_package
ARGS: {{"package": "plotly"}}

Your Response (Step 2):
TOOL_CALL: execute_python
ARGS: {{"code": "import plotly.express as px\\nimport pandas as pd\\nimport os\\n# Process data and create chart\\nos.makedirs('artifacts', exist_ok=True)\\nfig = px.bar(df, x='Product', y='Revenue', title='Sales Report')\\n# Save with RELATIVE path\\nfig.write_html('artifacts/chart.html')\\nprint('Chart saved')"}}

Your Response (Step 3):
FINAL_ANSWER: Interactive Plotly chart saved to artifacts/chart.html

⚠️ CRITICAL RULES:
- ALWAYS save output files with RELATIVE paths: 'artifacts/chart.html' NOT '/workspace/artifacts/chart.html'
- Create artifacts directory if needed: os.makedirs('artifacts', exist_ok=True)
- For Plotly: Use fig.write_html('artifacts/filename.html') - NEVER use Dash or app.run_server()
- NEVER use absolute paths like /workspace/artifacts/ when saving files
- NEVER try to run interactive servers (Dash, Flask, Streamlit)
- When you use read_file, the content is returned in the tool result - USE IT! Don't try to read the file again with pd.read_csv(filename)
- ALWAYS use StringIO for CSV content: df = pd.read_csv(StringIO(content), delimiter='\\t')

🚀 START NOW - Call your first tool immediately!"""

        # Build messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(compressed_history)  # Use compressed history to prevent context overflow

        # Try OpenAI first if it's an OpenAI model
        if is_openai:
            try:
                from openai import OpenAI

                # Get OpenAI API key from environment
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    logger.warning(f"⚠️ OPENAI_API_KEY not set, falling back to Ollama")
                    raise ValueError("OPENAI_API_KEY not configured")

                logger.info(f"🤖 Calling OpenAI LLM: {model}")

                # Create OpenAI client
                client = OpenAI(api_key=openai_api_key)

                # Call OpenAI API
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )

                llm_response = response.choices[0].message.content
                logger.info(f"💬 OpenAI responded ({len(llm_response)} chars): {llm_response[:200]}...")

                return llm_response

            except Exception as e:
                logger.warning(f"⚠️ OpenAI call failed: {e}, falling back to Ollama")
                # Fall through to Ollama fallback below

        # Use Ollama (either selected directly or as fallback)
        try:
            import ollama

            # Get Ollama configuration from environment
            ollama_host = os.getenv('OLLAMA_HOST', 'http://rag-ollama:11434')

            # If OpenAI failed, use default Ollama model
            if is_openai:
                fallback_model = "qwen2.5-coder:7b"
                logger.info(f"🔄 Using Ollama fallback model: {fallback_model}")
            else:
                fallback_model = model
                logger.info(f"🤖 Calling Ollama LLM: {fallback_model}")

            # Connect to Ollama
            client = ollama.Client(host=ollama_host)

            # Call LLM (IMPORTANT: stream=False to get complete response)
            response = client.chat(model=fallback_model, messages=messages, stream=False)

            llm_response = response['message']['content']
            logger.info(f"💬 Ollama responded ({len(llm_response)} chars): {llm_response[:200]}...")

            return llm_response

        except Exception as e:
            logger.error(f"❌ LLM call failed (both OpenAI and Ollama): {e}")
            # Final fallback: provide a sensible default response
            return f"FINAL_ANSWER: I encountered an error: {str(e)}. The task could not be completed."

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for actions"""

        # Check for tool call FIRST (priority over FINAL_ANSWER)
        # This prevents premature completion when LLM includes both in same message
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

                # Clean up markdown code fences and other formatting issues
                # LLMs sometimes include ```json or ``` at the end
                args_json = args_json.rstrip('`').strip()
                if args_json.startswith('```json'):
                    args_json = args_json[7:].strip()
                elif args_json.startswith('```'):
                    args_json = args_json[3:].strip()

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

        # Check for final answer (AFTER tool call check)
        if "FINAL_ANSWER:" in response:
            return {
                "type": "final_answer",
                "content": response.split("FINAL_ANSWER:")[1].strip()
            }

        # Default: thinking/reasoning step
        return {
            "type": "thinking",
            "content": response
        }


async def upload_to_minio(orchestrator: AgentOrchestrator, task_id: str, result: Dict[str, Any]):
    """
    Upload all task files to MinIO for persistence.

    Structure:
        projects/{project}/{user}/agent-tasks/{task_name}/{task_id}/
            ├── input/
            ├── artifacts/
            ├── logs/
            └── metadata.json
    """
    try:
        from minio import Minio
        import re

        # Get MinIO config from env
        minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        bucket_name = os.getenv("MINIO_BUCKET", "documents")  # Changed from chatbot-bucket to documents

        # Initialize MinIO client
        minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False
        )

        # Sanitize path components
        def sanitize(s: str) -> str:
            s = s.lower().strip()
            s = re.sub(r'\s+', '-', s)
            s = re.sub(r'[^a-z0-9\-_.]', '', s)
            return s.strip('-')

        # Get base path from database (includes organizational structure)
        # Query database for minio_base_path
        import asyncpg
        from sqlalchemy import text

        # Get database connection details from env
        db_host = os.getenv("POSTGRES_HOST", "postgres")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "ragchatbot")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

        # Fetch minio_base_path from database
        base_path = None
        try:
            conn = await asyncpg.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            base_path = await conn.fetchval(
                "SELECT minio_base_path FROM agent_tasks WHERE task_id = $1",
                task_id
            )
            await conn.close()
        except Exception as e:
            logger.warning(f"Failed to fetch minio_base_path from database: {e}")

        # Fallback to old structure if database query fails
        if not base_path:
            project_sanitized = sanitize(orchestrator.project_name)
            username_sanitized = sanitize(orchestrator.username)
            task_name_sanitized = sanitize(orchestrator.task_name)
            base_path = f"projects/{project_sanitized}/{username_sanitized}/agent-tasks/{task_name_sanitized}/{task_id}/"
            logger.warning(f"Using fallback base_path: {base_path}")

        logger.info(f"📤 Uploading to MinIO: {base_path}")

        # Upload input files
        for input_file in orchestrator.input_dir.iterdir():
            if input_file.is_file():
                minio_path = f"{base_path}input/{input_file.name}"
                minio_client.fput_object(bucket_name, minio_path, str(input_file))
                logger.info(f"  ✅ Uploaded input: {input_file.name}")

        # Upload artifacts from both artifacts directory AND workspace root
        # This handles files created anywhere in the workspace
        artifact_files = []

        # From artifacts directory
        if orchestrator.artifacts_dir.exists():
            artifact_files.extend([f for f in orchestrator.artifacts_dir.iterdir() if f.is_file()])

        # From workspace root (skip input files and subdirectories)
        skip_files = {'sales2.txt', 'sales.txt', 'sales.csv', 'sales2.csv'}
        if orchestrator.workspace.exists():
            workspace_files = [
                f for f in orchestrator.workspace.iterdir()
                if f.is_file() and f.name not in skip_files
            ]
            artifact_files.extend(workspace_files)

        # Upload all collected artifacts
        for artifact_file in artifact_files:
            minio_path = f"{base_path}artifacts/{artifact_file.name}"
            try:
                minio_client.fput_object(bucket_name, minio_path, str(artifact_file))
                logger.info(f"  ✅ Uploaded artifact: {artifact_file.name}")
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to upload {artifact_file.name}: {e}")

        # Upload logs
        for log_file in orchestrator.logs_dir.iterdir():
            if log_file.is_file():
                minio_path = f"{base_path}logs/{log_file.name}"
                minio_client.fput_object(bucket_name, minio_path, str(log_file))
                logger.info(f"  ✅ Uploaded log: {log_file.name}")

        # Create and upload metadata.json
        metadata = {
            "task_id": task_id,
            "task_name": orchestrator.task_name,
            "username": orchestrator.username,
            "project_name": orchestrator.project_name,
            "session_id": orchestrator.session_id,
            "created_at": orchestrator.session_state.get("created_at"),
            "completed_at": datetime.utcnow().isoformat(),
            "success": result.get("success"),
            "iterations": result.get("iterations"),
            "artifacts_count": len(result.get("artifacts", [])),
            "tool_calls_count": result.get("tool_calls", 0)
        }

        metadata_file = orchestrator.workspace / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        minio_path = f"{base_path}metadata.json"
        minio_client.fput_object(bucket_name, minio_path, str(metadata_file))
        logger.info(f"  ✅ Uploaded metadata.json")

        logger.info(f"✅ MinIO upload complete: {base_path}")

    except Exception as e:
        logger.error(f"❌ MinIO upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise


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
    task_name = task_config.get("task_name") or os.getenv("TASK_NAME", "agent_task")  # 🆕 NEW
    session_id = task_config.get("session_id") or os.getenv("SESSION_ID", "default")
    username = task_config.get("username") or os.getenv("USERNAME", "unknown")  # 🆕 NEW
    project_name = task_config.get("project_name") or os.getenv("PROJECT_NAME", "global-project")  # 🆕 NEW

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

    # 🆕 Use task_name for workspace path (user's request)
    base_workspace = Path(os.getenv("AGENT_WORKSPACE", "/workspace"))
    workspace = base_workspace / task_name  # Use task_name instead of task_id

    logger.info(f"📋 Task ID: {task_id}")
    logger.info(f"🏷️  Task Name: {task_name}")
    logger.info(f"👤 Username: {username}")
    logger.info(f"📁 Project: {project_name}")
    logger.info(f"🔖 Session ID: {session_id}")
    logger.info(f"📂 Workspace: {workspace}")
    logger.info(f"🔄 Max Iterations: {max_iterations}")
    logger.info(f"📝 Task: {task[:200]}...")

    # Layer 1: Initialize orchestrator
    orchestrator = AgentOrchestrator(
        task_id=task_id,
        task_name=task_name,  # 🆕 NEW
        session_id=session_id,
        workspace=workspace,
        username=username,  # 🆕 NEW
        project_name=project_name  # 🆕 NEW
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
        logger.info(f"📁 Artifacts: {len(result.get('artifacts', []))}")
        logger.info("=" * 80)

        # 🆕 Upload all files to MinIO before returning result
        try:
            await upload_to_minio(orchestrator, task_id, result)
            logger.info("✅ Successfully uploaded all files to MinIO")
        except Exception as e:
            logger.error(f"❌ Failed to upload to MinIO: {e}")
            # Continue anyway - don't fail the task if MinIO upload fails

        # CRITICAL: Print result to stdout so docker exec can capture it
        # The agent_service.py expects JSON output on stdout to parse the result
        print("=" * 80)
        print("AGENT_RESULT_JSON_START")
        print(json.dumps(result, default=str, indent=2))
        print("AGENT_RESULT_JSON_END")
        print("=" * 80)

        # Exit with success (always exit 0, let backend determine success/failure from JSON)
        # This matches ChatGPT behavior where tasks complete with whatever progress was made
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
