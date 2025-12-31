import { useState, useEffect } from 'react'
import { Settings, ChevronDown, ChevronUp, CheckSquare, Square, Bot, Wrench } from 'lucide-react'

/**
 * Tool & Agent Selector Component
 *
 * Allows users to:
 * 1. Enable/disable specific tools for query execution
 * 2. Select which agent orchestrates the query
 *
 * Architecture:
 * - Tools: Individual capabilities (document_rag, ocr, vision_analysis, construction_extraction, etc.)
 * - Agents: Orchestration workflows (RAG Agent, Enhanced RAG Agent, Local Mini Agent, etc.)
 * - Hybrid Services: Internal extraction strategies used BY tools (not user-selectable)
 */

// Available tools (from tool_registry.py)
export const AVAILABLE_TOOLS = [
  {
    id: 'document_rag',
    name: 'Document RAG',
    description: 'Retrieve relevant information from uploaded documents',
    category: 'retrieval',
    icon: '📄'
  },
  {
    id: 'smart_extraction',
    name: 'Smart Web Extraction',
    description: 'Intelligent content extraction from web pages',
    category: 'web',
    icon: '🧠'
  },
  {
    id: 'web_scraper',
    name: 'General Web Scraper',
    description: 'Extract content from any website',
    category: 'web',
    icon: '🕷️'
  },
  {
    id: 'template_extraction',
    name: 'Template-Based Extraction',
    description: 'Extract structured data using templates',
    category: 'extraction',
    icon: '📋'
  },
  {
    id: 'docling_pdf',
    name: 'Advanced PDF Processing',
    description: 'Deep PDF analysis with layout understanding',
    category: 'document',
    icon: '📑'
  },
  {
    id: 'ocr',
    name: 'OCR',
    description: 'Extract text from images and scanned documents',
    category: 'document',
    icon: '🔍'
  },
  {
    id: 'vision_analysis',
    name: 'Vision LLM Analysis',
    description: 'Analyze images, diagrams, and visual content',
    category: 'vision',
    icon: '👁️'
  },
  {
    id: 'construction_extraction',
    name: 'Construction Metrics',
    description: 'Extract building metrics from architectural drawings (uses hybrid: Vision LLM + OCR + OpenCV)',
    category: 'specialized',
    icon: '🏗️'
  },
  {
    id: 'compress_text_for_llm',
    name: 'Text Compression',
    description: 'Compress long text for smaller LLM context windows',
    category: 'utility',
    icon: '🗜️'
  },
  {
    id: 'navigation_agent',
    name: 'Multi-Page Navigator',
    description: 'Navigate and extract from multi-page websites',
    category: 'web',
    icon: '🧭'
  }
]

// Available agents
export const AVAILABLE_AGENTS = [
  {
    id: 'auto',
    name: 'Auto (Multi-Strategy)',
    description: 'Automatically select best strategy (Direct LLM / RAG / Tools)',
    icon: '🤖'
  },
  {
    id: 'rag_agent',
    name: 'RAG Agent',
    description: 'Basic RAG query agent',
    icon: '📚'
  },
  {
    id: 'enhanced_rag_agent',
    name: 'Enhanced RAG Agent',
    description: 'Advanced RAG with multi-strategy selection',
    icon: '⚡'
  },
  {
    id: 'local_mini_agent',
    name: 'Local Mini Agent',
    description: 'Lightweight local agent for simple queries',
    icon: '🏃'
  },
  {
    id: 'construction_agent',
    name: 'Construction Agent',
    description: 'Specialized for construction document analysis',
    icon: '🏗️'
  }
]

interface ToolAgentSelectorProps {
  enabledTools: string[]
  onToolsChange: (tools: string[]) => void
  selectedAgent: string
  onAgentChange: (agent: string) => void
}

export default function ToolAgentSelector({
  enabledTools,
  onToolsChange,
  selectedAgent,
  onAgentChange
}: ToolAgentSelectorProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [toolsExpanded, setToolsExpanded] = useState(true)
  const [agentExpanded, setAgentExpanded] = useState(true)

  // Initialize with all tools enabled by default
  useEffect(() => {
    if (enabledTools.length === 0) {
      onToolsChange(AVAILABLE_TOOLS.map(t => t.id))
    }
  }, [])

  const toggleTool = (toolId: string) => {
    if (enabledTools.includes(toolId)) {
      onToolsChange(enabledTools.filter(id => id !== toolId))
    } else {
      onToolsChange([...enabledTools, toolId])
    }
  }

  const toggleAllTools = () => {
    if (enabledTools.length === AVAILABLE_TOOLS.length) {
      onToolsChange([])
    } else {
      onToolsChange(AVAILABLE_TOOLS.map(t => t.id))
    }
  }

  // Group tools by category
  const toolsByCategory = AVAILABLE_TOOLS.reduce((acc, tool) => {
    if (!acc[tool.category]) acc[tool.category] = []
    acc[tool.category].push(tool)
    return acc
  }, {} as Record<string, typeof AVAILABLE_TOOLS>)

  const categoryLabels = {
    retrieval: 'Document Retrieval',
    web: 'Web Scraping',
    extraction: 'Data Extraction',
    document: 'Document Processing',
    vision: 'Vision Analysis',
    specialized: 'Specialized Tools',
    utility: 'Utilities'
  }

  return (
    <div className="border border-sage-200 rounded-lg bg-white shadow-sm">
      {/* Header - Compact */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center justify-between hover:bg-sage-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-sage-600" />
          <span className="text-sm font-medium text-gray-900">Tools & Agents</span>
          <span className="text-xs text-gray-500">
            ({enabledTools.length}/{AVAILABLE_TOOLS.length}, {AVAILABLE_AGENTS.find(a => a.id === selectedAgent)?.icon})
          </span>
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>

      {/* Expanded Content - Scrollable */}
      {isExpanded && (
        <div className="border-t border-gray-200 max-h-96 overflow-y-auto"
             style={{ scrollbarWidth: 'thin' }}>

          {/* Tool Selection - Compact */}
          <div className="p-3 space-y-2">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setToolsExpanded(!toolsExpanded)}
                className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 hover:text-gray-900"
              >
                <Wrench className="w-3.5 h-3.5" />
                <span>Tools ({enabledTools.length}/{AVAILABLE_TOOLS.length})</span>
                {toolsExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              <button
                onClick={toggleAllTools}
                className="text-[10px] text-sage-600 hover:text-sage-800 font-medium uppercase tracking-wide"
              >
                {enabledTools.length === AVAILABLE_TOOLS.length ? 'None' : 'All'}
              </button>
            </div>

            {toolsExpanded && (
              <div className="space-y-2 pl-1">
                {/* Tools by Category - Compact Grid */}
                {Object.entries(toolsByCategory).map(([category, tools]) => (
                  <div key={category} className="space-y-1">
                    <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                      {categoryLabels[category as keyof typeof categoryLabels]}
                    </div>
                    {tools.map(tool => (
                      <label
                        key={tool.id}
                        className="flex items-center gap-2 px-2 py-1 rounded hover:bg-sage-50 cursor-pointer group transition-colors"
                        title={tool.description}
                      >
                        <input
                          type="checkbox"
                          checked={enabledTools.includes(tool.id)}
                          onChange={() => toggleTool(tool.id)}
                          className="w-3.5 h-3.5 text-sage-600 rounded border-gray-300 focus:ring-sage-500"
                        />
                        <span className="text-sm">{tool.icon}</span>
                        <span className="text-xs font-medium text-gray-700 group-hover:text-gray-900 flex-1">
                          {tool.name}
                        </span>
                      </label>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Agent Selection - Compact */}
          <div className="p-3 space-y-2 border-t border-gray-100">
            <button
              onClick={() => setAgentExpanded(!agentExpanded)}
              className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 hover:text-gray-900"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Agent</span>
              {agentExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {agentExpanded && (
              <div className="space-y-0.5 pl-1">
                {AVAILABLE_AGENTS.map(agent => (
                  <label
                    key={agent.id}
                    className="flex items-center gap-2 px-2 py-1 rounded hover:bg-sage-50 cursor-pointer group transition-colors"
                    title={agent.description}
                  >
                    <input
                      type="radio"
                      name="agent"
                      checked={selectedAgent === agent.id}
                      onChange={() => onAgentChange(agent.id)}
                      className="w-3.5 h-3.5 text-sage-600 border-gray-300 focus:ring-sage-500"
                    />
                    <span className="text-sm">{agent.icon}</span>
                    <span className="text-xs font-medium text-gray-700 group-hover:text-gray-900">
                      {agent.name}
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Info Box - Compact */}
          <div className="bg-sage-50 border-t border-sage-100 p-2 text-[10px] text-sage-700">
            <p className="font-semibold mb-0.5">💡 Quick Guide</p>
            <p className="text-sage-600 leading-relaxed">
              <strong>Tools</strong> = capabilities • <strong>Agents</strong> = orchestration • <strong>Hybrid</strong> = internal (auto)
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
