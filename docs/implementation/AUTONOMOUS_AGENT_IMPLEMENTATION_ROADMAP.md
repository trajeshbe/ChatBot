# 🤖 Autonomous Agent Implementation Roadmap
**Project**: Fully Autonomous General-Purpose Agent
**Started**: 2025-12-01
**Status**: Phase 1 Complete - Foundation & Prompt Engineering

---

## 🎯 Vision

Build a **FULLY AUTONOMOUS GENERAL-PURPOSE AGENT** that can:
- Handle ANY problem type (data analysis, ML, code generation, debugging, research, web scraping)
- Decide complexity and approach autonomously
- Install required packages without human intervention
- Self-correct on errors with retry logic
- Ask clarifying questions when needed
- Operate through THINK → PLAN → ACT → OBSERVE loop

**Cost**: $0 (local LLMs via Ollama)
**Privacy**: 100% (no external API calls)

---

## ✅ PHASE 1: Foundation (COMPLETE)

### 1.1 Base Agent Runtime ✅
- **Container**: `rag-agent-runtime` with Python 3.11
- **LLM**: Ollama qwen2.5-coder:7b (local, free)
- **Workspace**: `/workspace` with `/artifacts` subdirectory
- **Configuration**:
  - Max Iterations: 30
  - Timeout: 600 seconds (10 minutes)
  - Stream: false (for complete responses)

### 1.2 Tool Registry ✅
**14 Tools Implemented**:

#### Core Tools (6)
1. `read_file` - Read file contents
2. `write_file` - Create or overwrite files
3. `list_directory` - List files in directory
4. `execute_bash` - Run shell commands (with security validation)
5. `search_files` - Grep search across files
6. `get_current_time` - Timestamp for operations

#### Data Science Tools (7)
7. `analyze_dataframe` - Full EDA with correlations, missing values, distributions
8. `visualize_data` - Auto-detect chart types and create visualizations
9. `analyze_excel_workbook` - Multi-sheet analysis with formula extraction
10. `extract_pdf_content` - Docling + pdfplumber + OCR fallback
11. `extract_word_document` - Tables, metadata, formatting
12. `analyze_image_with_vision` - llama3.2-vision for image understanding
13. `extract_text_from_image` - Tesseract/EasyOCR locally

#### Autonomous Installation (1) 🆕
14. **`install_package`** - Install Python packages via pip
    - Security: Command injection prevention
    - Timeout: 120 seconds
    - Returns: success/error status
    - Example: `install_package(package="xgboost")`

### 1.3 Safe Python Executor ✅
```python
# Pre-imported libraries available in execution environment
- pandas (pd)
- numpy (np)
- matplotlib.pyplot (plt)
- pathlib.Path
- Standard library: json, os, sys, re, datetime, etc.

# Security
- Removed RestrictedPython (was blocking imports)
- Path validation for file operations
- Bash command blacklist (rm -rf, sudo, etc.)
- Resource limits via Docker
```

### 1.4 Enhanced System Prompt ✅
**Problem**: LLM was describing steps instead of calling tools
**Solution**: Strict directive prompt with few-shot examples

```python
system_prompt = """You are a TOOL-CALLING AI agent. Your ONLY job is to call tools.

⚠️ CRITICAL RULES:
1. NEVER write explanations, plans, or descriptions
2. NEVER say "we should do X" or "let's start by doing Y"
3. IMMEDIATELY call a tool in EVERY response

✅ CORRECT:
TOOL_CALL: read_file
ARGS: {"path": "sales.txt"}

❌ WRONG:
"To analyze sales.txt, we should first..."  ← NEVER DO THIS!

📚 EXAMPLES:
[Two complete few-shot examples]
"""
```

**Status**: Deployed, testing in progress

### 1.5 Documentation ✅
Created comprehensive docs:
- `/docs/architecture/FULLY_AUTONOMOUS_AGENT_ARCHITECTURE.md` - Full design
- `/docs/analysis/CLAUDE_CODE_VS_OUR_IMPLEMENTATION.md` - Best practices comparison
- `/docs/session_summaries/AUTONOMOUS_AGENT_STATUS_2025-12-01.md` - Current state
- `/docs/session_summaries/PROMPT_ENGINEERING_FIX_2025-12-01.md` - Prompt fix details

---

## 🔄 PHASE 2: THINK & PLAN (IN PROGRESS)

### 2.1 THINK Phase - Problem Classification
**Goal**: Analyze problem type and complexity before execution

```python
async def _think_phase(self, task: str) -> Dict:
    """
    Analyze task to determine:
    - Problem type (data_analysis, ml, code_gen, web_scraping, research, debugging)
    - Complexity (simple, moderate, complex)
    - Required tools
    - Missing packages
    - Estimated steps
    """

    thinking_prompt = f"""
    Analyze this task and return JSON:

    Task: {task}

    {{
        "type": "data_analysis" | "ml" | "code_generation" | "web_scraping" | "research" | "debugging",
        "complexity": "simple" | "moderate" | "complex",
        "required_tools": ["tool1", "tool2", ...],
        "missing_packages": ["package1", "package2", ...],
        "estimated_steps": 5,
        "reasoning": "Why this classification"
    }}
    """

    analysis = await self._call_llm(thinking_prompt)
    return parse_json(analysis)
```

**Benefits**:
- Optimized approach based on problem type
- Proactive package installation
- Better resource allocation
- Clearer execution plan

**Timeline**: Week 1 of next session

### 2.2 PLAN Phase - Strategic Planning
**Goal**: Create detailed step-by-step execution plan

```python
async def _plan_phase(self, thinking: Dict) -> Dict:
    """
    Create detailed execution plan with:
    - Ordered steps
    - Tool calls for each step
    - Fallback strategies
    - Success criteria
    """

    planning_prompt = f"""
    Create execution plan for this task:

    Type: {thinking['type']}
    Complexity: {thinking['complexity']}
    Required Tools: {thinking['required_tools']}

    Return JSON:
    {{
        "steps": [
            {{
                "step": 1,
                "action": "install_package",
                "args": {{"package": "xgboost"}},
                "purpose": "Install ML library for model training"
            }},
            {{
                "step": 2,
                "action": "read_file",
                "args": {{"path": "data.csv"}},
                "purpose": "Load training data"
            }},
            ...
        ],
        "fallback_strategy": "If X fails, try Y",
        "success_criteria": "Model R² > 0.8"
    }}
    """

    plan = await self._call_llm(planning_prompt)
    return parse_json(plan)
```

**Benefits**:
- Clear roadmap before execution
- Fallback strategies defined upfront
- Better error handling
- Measurable success criteria

**Timeline**: Week 1-2 of next session

### 2.3 Enhanced ACT Phase - Plan Execution
**Goal**: Execute plan with error recovery

```python
async def _act_with_plan(self, plan: Dict) -> Dict:
    """Execute plan step-by-step with retry logic"""

    for step in plan["steps"]:
        logger.info(f"📍 Step {step['step']}: {step['purpose']}")

        result = await self._execute_tool_with_retry(
            action=step["action"],
            args=step["args"],
            max_retries=3
        )

        if not result["success"]:
            # Try fallback strategy
            fallback = plan.get("fallback_strategy")
            if fallback:
                result = await self._execute_fallback(fallback)

        # Store result for next steps
        self.step_results.append(result)

    return {"success": True, "results": self.step_results}
```

**Timeline**: Week 2 of next session

---

## 🔧 PHASE 3: Error Recovery & Self-Correction (PLANNED)

### 3.1 Retry Logic with Analysis
```python
async def _execute_tool_with_retry(self, action: str, args: Dict, max_retries=3) -> Dict:
    """Execute tool with intelligent retry"""

    for attempt in range(max_retries):
        result = await self._execute_tool(action, args)

        if result["success"]:
            return result

        # Analyze error and adapt approach
        error_analysis = await self._analyze_error(
            tool=action,
            error=result["error"],
            attempt=attempt
        )

        # Update args based on error analysis
        args = error_analysis.get("updated_args", args)

        # Or switch to different tool
        if error_analysis.get("switch_tool"):
            action = error_analysis["new_tool"]

    return {"success": False, "error": "Max retries exceeded"}
```

**Timeline**: Week 2-3 of next session

### 3.2 Fallback Strategies
```python
FALLBACK_STRATEGIES = {
    "pandas_read_error": ["try_polars", "try_manual_parsing"],
    "matplotlib_error": ["try_plotly", "try_seaborn"],
    "package_install_error": ["try_conda", "skip_and_continue"],
    "llm_timeout": ["retry_with_smaller_context", "split_into_subtasks"]
}
```

### 3.3 Self-Correction Patterns
- **Import Error** → Auto-install missing package
- **File Not Found** → List directory and suggest closest match
- **Memory Error** → Process data in chunks
- **Timeout** → Split task into smaller subtasks

**Timeline**: Week 3 of next session

---

## 💬 PHASE 4: Interactive Clarification (PLANNED)

### 4.1 Ask User Question Tool
```python
async def _ask_user_question(
    self,
    question: str,
    options: List[str] = None,
    timeout: int = 300
) -> str:
    """
    Ask user for clarification during execution.

    Args:
        question: The question to ask
        options: Multiple choice options (or None for free text)
        timeout: Seconds to wait for answer

    Returns:
        User's answer as string
    """

    # Save question to database with task_id
    question_id = await db.save_agent_question(
        task_id=self.task_id,
        question=question,
        options=options,
        created_at=datetime.now()
    )

    # Poll for answer (non-blocking for agent)
    answer = await wait_for_user_response(
        question_id=question_id,
        timeout=timeout
    )

    if answer is None:
        # Timeout - make best guess
        logger.warning(f"⏰ No user response, proceeding with default")
        return "continue_with_best_guess"

    return answer
```

### 4.2 UI Integration
**Frontend Modal**:
```typescript
<AgentQuestionModal
  question="Should I use linear regression or random forest for this prediction?"
  options={[
    "Linear Regression (simpler, faster)",
    "Random Forest (more accurate, slower)",
    "Let agent decide based on data"
  ]}
  onAnswer={(answer) => sendAnswerToAgent(answer)}
  timeout={300}  // 5 minutes
/>
```

**When to Ask**:
- Ambiguous requirements ("visualizations" - what type?)
- Multiple valid approaches (ML model selection)
- Before destructive operations ("delete old files?")
- Parameter tuning ("how many clusters?")

**Timeline**: Week 4 of next session

---

## 🚀 PHASE 5: Advanced Capabilities (FUTURE)

### 5.1 Expand Tool Registry to 50+

**Tier 1: System Tools** (existing + 3 new)
- file operations (read, write, list) ✅
- bash execution ✅
- install_package ✅
- `create_virtual_env` (isolated environments) 🆕
- `docker_exec` (run commands in containers) 🆕
- `monitor_resources` (CPU, memory, disk) 🆕

**Tier 2: Code Execution** (existing + 5 new)
- execute_python ✅
- `execute_javascript` (Node.js) 🆕
- `execute_r` (R scripts) 🆕
- `execute_sql` (database queries) 🆕
- `compile_and_run` (C/C++/Go) 🆕
- `debug_code` (auto-debugging with pdb) 🆕

**Tier 3: Data Processing** (existing + 3 new)
- analyze_dataframe ✅
- visualize_data ✅
- analyze_excel_workbook ✅
- `clean_data` (auto data cleaning) 🆕
- `merge_datasets` (smart joins) 🆕
- `time_series_analysis` (forecasting) 🆕

**Tier 4: Document Processing** (existing + 2 new)
- extract_pdf_content ✅
- extract_word_document ✅
- `extract_ppt_content` (PowerPoint) 🆕
- `convert_document` (format conversion) 🆕

**Tier 5: Vision & OCR** (existing + 2 new)
- analyze_image_with_vision ✅
- extract_text_from_image ✅
- `detect_objects` (YOLO/Detectron2) 🆕
- `generate_image` (DALL-E/Stable Diffusion) 🆕

**Tier 6: Web & Network** (5 new)
- `fetch_url` (HTTP GET/POST) 🆕
- `scrape_website` (Playwright) 🆕
- `parse_html` (BeautifulSoup) 🆕
- `download_file` (wget/curl) 🆕
- `api_call` (REST API client) 🆕

**Tier 7: Git Operations** (5 new)
- `git_clone` (clone repository) 🆕
- `git_diff` (show changes) 🆕
- `git_commit` (commit changes) 🆕
- `git_push` (push to remote) 🆕
- `git_search` (search code history) 🆕

**Tier 8: Meta-Tools** (3 new)
- `ask_user_question` (interactive clarification) 🆕
- `create_subtask` (delegate to sub-agent) 🆕
- `search_documentation` (RAG for docs) 🆕

**Timeline**: Phased rollout over 4 weeks

### 5.2 Increase Iterations to 50
- Match Claude Code's capacity
- Better handling of complex multi-step tasks
- More room for error recovery

### 5.3 Adaptive Prompts
```python
def build_adaptive_prompt(task: str, context: Dict) -> str:
    """Build context-aware prompt based on task type"""

    base_prompt = "You are a TOOL-CALLING AI agent..."

    # Task-specific instructions
    if "visualization" in task.lower():
        base_prompt += """
        VISUALIZATION DETECTED:
        - Use seaborn for professional plots
        - Always add titles and labels
        - Save to /workspace/artifacts/
        - Use color palettes (not defaults)
        """

    if "machine learning" in task.lower():
        base_prompt += """
        ML TASK DETECTED:
        - Install scikit-learn if needed
        - Split data train/test (80/20)
        - Print model metrics (accuracy, R², etc.)
        - Create residual plots for regression
        """

    if "web scraping" in task.lower():
        base_prompt += """
        WEB SCRAPING DETECTED:
        - Check robots.txt first
        - Rate limit requests (1 req/sec)
        - Handle pagination automatically
        - Extract structured data to JSON/CSV
        """

    # Add file context
    if context.get("files"):
        files_list = "\n".join(f"- {f['name']}" for f in context["files"])
        base_prompt += f"\n\nAVAILABLE FILES:\n{files_list}"

    return base_prompt
```

**Timeline**: Week 4-5 of next session

### 5.4 Multi-Agent Orchestration
- **Supervisor Agent**: Breaks complex tasks into subtasks
- **Worker Agents**: Specialized agents for specific domains
- **Reviewer Agent**: Quality checks and validation

```python
class SupervisorAgent:
    async def delegate_task(self, task: str):
        """Break task into subtasks and delegate"""

        # Analyze task complexity
        analysis = await self.analyze_complexity(task)

        if analysis["complexity"] == "simple":
            # Execute directly
            return await self.single_agent_execution(task)

        # Complex - create subtasks
        subtasks = await self.create_subtasks(task)

        # Delegate to specialized agents
        results = await asyncio.gather(*[
            self.spawn_worker_agent(subtask)
            for subtask in subtasks
        ])

        # Merge results
        final_result = await self.merge_results(results)

        # Quality review
        validated = await self.spawn_reviewer_agent(final_result)

        return validated
```

**Timeline**: Month 2

---

## 📊 Success Metrics

### Current State (Phase 1 Complete)
| Metric | Current | Target (MVP) | Target (Full) |
|--------|---------|--------------|---------------|
| **Tool Count** | 14 | 25 | 50+ |
| **Max Iterations** | 30 | 50 | 100 |
| **Autonomous Package Install** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Problem Classification** | ❌ No | ✅ Yes | ✅ Yes |
| **Strategic Planning** | ❌ No | ✅ Yes | ✅ Yes |
| **Error Recovery** | ❌ No | ⚠️ Basic | ✅ Advanced |
| **Interactive Clarification** | ❌ No | ✅ Yes | ✅ Yes |
| **Self-Correction** | ❌ No | ⚠️ Basic | ✅ Advanced |
| **Multi-Agent** | ❌ No | ❌ No | ✅ Yes |
| **Cost per Task** | $0 | $0 | $0 |
| **Task Success Rate** | ~70% | >85% | >95% |
| **Avg Completion Time** | ~60s | <45s | <30s |

### Test Results
✅ **Pandas Visualization** - PASSED (8 iterations, 64s)
🔄 **XGBoost ML Model** - IN PROGRESS (testing autonomous package install)
⏳ **Prompt Engineering Fix** - DEPLOYED (validating behavior change)

---

## 🗓️ Timeline Summary

### Week 1 (Current Session)
- ✅ Phase 1: Foundation complete
- ✅ Enhanced system prompt
- 🔄 Testing improved prompt behavior
- ⏳ Validate autonomous package installation

### Week 2-3 (Next Session)
- 🎯 Phase 2: THINK/PLAN phases
- 🎯 Phase 3: Error recovery
- 🎯 Test with 10+ diverse tasks

### Week 4-5
- 🎯 Phase 4: Interactive clarification
- 🎯 Phase 5: Expand tool registry to 25+
- 🎯 Phase 5: Adaptive prompts
- 🎯 Increase iterations to 50

### Month 2
- 🎯 Phase 5: Expand to 50+ tools
- 🎯 Phase 5: Multi-agent orchestration
- 🎯 Phase 5: Advanced self-correction
- 🎯 Comprehensive testing & benchmarking

---

## 💡 Key Design Decisions

### Why Local LLMs (Ollama)?
- **Zero cost** vs $1.50/task (Claude Code)
- **Data privacy** - No external API calls
- **No rate limits** - Run unlimited tasks
- **Offline capable** - Works without internet

**Trade-off**: Slightly lower quality than GPT-4/Claude-3, but improving fast

### Why THINK → PLAN → ACT → OBSERVE?
- **Think**: Understand problem deeply before acting
- **Plan**: Strategy prevents wasted iterations
- **Act**: Execute with error recovery
- **Observe**: Validate and learn from results

**Inspired by**: ReAct pattern, Claude Code architecture, Chain-of-Thought reasoning

### Why 14 Tools (Not 50+ Yet)?
- **Start small**: Validate core functionality first
- **Data science focus**: Our specialty vs general-purpose
- **Incremental growth**: Add tools as needs emerge

**Future**: Will reach 50+ tools in Phase 5

---

## 🔗 Related Documentation

### Architecture
- `/docs/architecture/FULLY_AUTONOMOUS_AGENT_ARCHITECTURE.md` - Complete design
- `/docs/architecture/MEMORY_HIERARCHY_GUIDE.md` - RAG integration

### Analysis
- `/docs/analysis/CLAUDE_CODE_VS_OUR_IMPLEMENTATION.md` - Best practices
- `/docs/analysis/WEB_SCRAPER_ANALYSIS.md` - Web scraping capabilities

### Session Summaries
- `/docs/session_summaries/AUTONOMOUS_AGENT_STATUS_2025-12-01.md` - Current state
- `/docs/session_summaries/PROMPT_ENGINEERING_FIX_2025-12-01.md` - Prompt improvements

### Testing
- `scripts/testing/test_agent_task_debug.sh` - Debug agent execution
- `scripts/testing/test_autonomous_agent.sh` - Test autonomous capabilities

---

## 🚦 Status Dashboard

### Phase Completion
```
Phase 1: Foundation              ████████████████████ 100%
Phase 2: THINK/PLAN              ████░░░░░░░░░░░░░░░░  20%
Phase 3: Error Recovery          ██░░░░░░░░░░░░░░░░░░  10%
Phase 4: Interactive Clarify     ░░░░░░░░░░░░░░░░░░░░   0%
Phase 5: Advanced Features       ░░░░░░░░░░░░░░░░░░░░   0%
```

### Current Focus
🎯 **Validating Phase 1** - Testing improved prompt and autonomous package installation

### Next Milestone
📍 **Phase 2 Start** - Implement THINK and PLAN phases (Week 2)

---

**Last Updated**: 2025-12-01
**Next Review**: After autonomous XGBoost test completion
