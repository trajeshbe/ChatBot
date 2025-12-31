# Tool & Agent Selection Implementation

**Date**: 2025-12-03
**Status**: ✅ Complete
**Components**: Frontend UI + Backend API

---

## Overview

Implemented comprehensive tool and agent selection system that allows users to:
1. **Enable/disable specific tools** for query execution (10 available tools)
2. **Select which agent orchestrates** the query (5 available agents)
3. **Understand the architecture** (Tools vs Agents vs Hybrid Services)

---

## Architecture Explained

### **1. Tools** (User-Selectable Capabilities)

Tools are **individual capabilities** that the system can use to answer queries. Think of them as specialized workers.

**10 Available Tools** (from `tool_registry.py`):

| Tool ID | Name | Description | Category |
|---------|------|-------------|----------|
| `document_rag` | Document RAG | Retrieve from uploaded documents | Retrieval |
| `smart_extraction` | Smart Web Extraction | Intelligent web content extraction | Web |
| `web_scraper` | General Web Scraper | Extract from any website | Web |
| `template_extraction` | Template-Based Extraction | Structured data extraction | Extraction |
| `docling_pdf` | Advanced PDF Processing | Deep PDF analysis | Document |
| `ocr` | OCR | Extract text from images/scans | Document |
| `vision_analysis` | Vision LLM Analysis | Analyze images, diagrams, visuals | Vision |
| **`construction_extraction`** | **Construction Metrics** | **Extract building metrics (uses hybrid!)** | **Specialized** |
| `compress_text_for_llm` | Text Compression | Compress for small LLMs | Utility |
| `navigation_agent` | Multi-Page Navigator | Navigate multi-page websites | Web |

### **2. Agents** (Orchestration Workflows)

Agents are **orchestration workflows** that decide HOW to answer a query. Think of them as managers who coordinate the tools.

**5 Available Agents**:

| Agent ID | Name | Description |
|----------|------|-------------|
| `auto` | Auto (Multi-Strategy) | Automatically select best strategy (Direct LLM / RAG / Tools) |
| `rag_agent` | RAG Agent | Basic RAG query agent |
| `enhanced_rag_agent` | Enhanced RAG Agent | Advanced RAG with multi-strategy selection |
| `local_mini_agent` | Local Mini Agent | Lightweight local agent for simple queries |
| `construction_agent` | Construction Agent | Specialized for construction document analysis |

### **3. Hybrid Services** (Internal Extraction Strategies)

Hybrid services are **NOT user-selectable**. They are internal implementation details used BY tools.

**6 Hybrid Extraction Methods**:
1. Vision LLM (llama3.2-vision:11b)
2. OCR (Tesseract/pytesseract)
3. Advanced parsing (Docling)
4. Table extraction (PyMuPDF/PyPDF2)
5. OpenCV scale detection (1:100 scales)
6. OpenCV geometric measurement (contours)

**Example**: The `construction_extraction` tool uses ALL 6 hybrid methods internally!

```
User Query → Agent (selected_agent) → Tools (enabled_tools) → Hybrid Services (automatic)
                     ↓                          ↓
              enhanced_rag_agent      construction_extraction → Vision LLM
                                                               → OCR
                                                               → Docling
                                                               → OpenCV Scale
                                                               → OpenCV Geometry
```

---

## Implementation Details

### Frontend Components

#### 1. **ToolAgentSelector.tsx** (NEW)
- Location: `frontend/src/components/ToolAgentSelector.tsx`
- Features:
  - Multi-select checkboxes for tools (grouped by category)
  - Radio buttons for agent selection
  - Collapsible panels
  - Visual icons for each tool/agent
  - Info box explaining the architecture

#### 2. **ChatInterfaceEnhanced.tsx** (UPDATED)
- Added imports:
  ```typescript
  import ToolAgentSelector, { AVAILABLE_TOOLS } from './ToolAgentSelector'
  ```

- Added state:
  ```typescript
  const [enabledTools, setEnabledTools] = useState<string[]>(AVAILABLE_TOOLS.map(t => t.id))
  const [selectedAgent, setSelectedAgent] = useState<string>('auto')
  ```

- Added UI component (after header, before messages):
  ```tsx
  <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
    <div className="max-w-3xl mx-auto">
      <ToolAgentSelector
        enabledTools={enabledTools}
        onToolsChange={setEnabledTools}
        selectedAgent={selectedAgent}
        onAgentChange={setSelectedAgent}
      />
    </div>
  </div>
  ```

- Added to query request (line 917-923):
  ```typescript
  formData.append('enabled_tools', JSON.stringify(enabledTools))
  formData.append('selected_agent', selectedAgent)

  console.log(`🔧 Tools enabled: ${enabledTools.length}/${AVAILABLE_TOOLS.length}`)
  console.log(`🤖 Agent selected: ${selectedAgent}`)
  ```

### Backend API

#### **backend/app/main.py** (UPDATED)

**1. Added parameters to `/api/v1/query` endpoint** (line 618-620):
```python
# 🆕 Tool & Agent Selection
enabled_tools: Optional[str] = Form(None),  # JSON array of enabled tool IDs
selected_agent: Optional[str] = Form('auto'),  # Selected agent
```

**2. Parse parameters** (line 720-729):
```python
# 🆕 Parse enabled tools and selected agent
enabled_tools_list = []
if enabled_tools:
    try:
        enabled_tools_list = json.loads(enabled_tools)
        logger.info(f"🔧 Enabled tools ({len(enabled_tools_list)}): {enabled_tools_list}")
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Failed to parse enabled_tools JSON: {e}")

logger.info(f"🤖 Selected agent: {selected_agent}")
```

**3. Pass to agent** (line 752-754):
```python
"enabled_tools": enabled_tools_list,  # List of enabled tool IDs
"selected_agent": selected_agent  # Agent orchestration type
```

---

## Usage Examples

### **Example 1**: Only use document RAG, no web tools
1. Open chat UI
2. Click "Tools & Agents" to expand
3. Under "Available Tools":
   - Deselect all
   - Enable only "Document RAG"
4. Agent: Keep "Auto (Multi-Strategy)"
5. Ask your question

### **Example 2**: Use construction agent with all specialized tools
1. Expand "Tools & Agents"
2. Tools: Enable "Construction Metrics", "Vision Analysis", "OCR", "Advanced PDF"
3. Agent: Select "Construction Agent"
4. Upload architectural drawings
5. Ask: "Extract GFA and building height from these drawings"

### **Example 3**: Web scraping only
1. Expand "Tools & Agents"
2. Tools: Enable only "Smart Web Extraction", "General Web Scraper"
3. Agent: Keep "Auto"
4. Ask: "Scrape the latest news from example.com"

---

## Next Steps: Add to Unified Config UI

Currently implemented: **Per-query** tool/agent selection in chat UI
Recommended: **Global defaults** in Unified Config UI (WeightsConfigManager)

### How to Add to Unified Config UI

1. **Update `backend/app/config/weights_config.yaml`**:
   ```yaml
   # Add new section:
   tool_and_agent_defaults:
     enabled_tools:
       - document_rag
       - smart_extraction
       - ocr
       - vision_analysis
       - construction_extraction
       - docling_pdf
       # ... list all tools you want enabled by default
     selected_agent: auto  # Default agent
   ```

2. **Update `frontend/src/components/WeightsConfigManager.tsx`**:
   - Add state for `enabledToolsDefaults` and `selectedAgentDefault`
   - Add a new collapsible section "Tool & Agent Defaults"
   - Use the same ToolAgentSelector component (reusable!)
   - Save to `userWeightsConfig` in localStorage

3. **Update backend to use defaults**:
   - If `enabled_tools` is None in query, use defaults from unified_config
   - If `selected_agent` is 'auto', use default from unified_config

### Proposed Unified Config Structure

```typescript
interface WeightsConfig {
  // ... existing 48 parameters ...

  // 🆕 NEW: Tool & Agent Defaults
  tool_and_agent_defaults: {
    enabled_tools: string[];  // List of tool IDs
    selected_agent: string;   // Default agent
  };
}
```

---

## Benefits

✅ **User Control**: Fine-grained control over which tools are used
✅ **Transparency**: Users see what capabilities are available
✅ **Performance**: Disable unused tools to reduce overhead
✅ **Flexibility**: Per-query overrides + global defaults
✅ **Education**: Info box explains architecture

---

## Testing

### 1. Frontend Test
```bash
# Open browser to http://localhost:3001
# Log into chat
# Click "Tools & Agents" to expand
# Verify:
# - 10 tools listed, all checked by default
# - 5 agents listed, "Auto" selected
# - Can expand/collapse panels
# - Can enable/disable tools
# - Can select different agents
```

### 2. Backend Test
```bash
# Check backend logs after sending a query:
docker-compose logs backend | grep -E "Enabled tools|Selected agent"

# Should see:
# 🔧 Enabled tools (10): ['document_rag', 'smart_extraction', ...]
# 🤖 Selected agent: auto
```

### 3. Integration Test
```bash
# Test with construction metrics:
# 1. Upload architectural drawings
# 2. Enable only: construction_extraction, vision_analysis, ocr
# 3. Select agent: construction_agent
# 4. Query: "Extract GFA and building metrics"
# 5. Verify response uses construction_extraction tool
```

---

## Files Modified

### Frontend
- ✅ `frontend/src/components/ToolAgentSelector.tsx` (NEW)
- ✅ `frontend/src/components/ChatInterfaceEnhanced.tsx` (UPDATED)

### Backend
- ✅ `backend/app/main.py` (UPDATED)

### Documentation
- ✅ `docs/TOOL_AGENT_SELECTION_IMPLEMENTATION.md` (NEW - this file)

---

## Related Issues Fixed

1. ✅ **Deepseeker-coder model appearing in chat** - Fixed by excluding coder models from default selection
   - File: `backend/app/services/llm_service.py` (line 488-501)
   - Now filters out models with 'coder', 'code-', '-code' keywords

2. ✅ **Tool selection option missing** - Implemented comprehensive tool/agent selector UI

3. ✅ **Construction metrics using hybrid services** - Confirmed working, construction_extraction tool uses all 6 hybrid methods internally

---

## Future Enhancements

1. **Unified Config Integration**: Add tool/agent defaults to global config
2. **Tool Dependencies**: Show which tools depend on others
3. **Tool Performance**: Show avg latency per tool
4. **Agent Recommendations**: Suggest best agent based on query type
5. **Tool Usage Analytics**: Track which tools are most effective

---

**End of Document**
