import { useState, useEffect } from 'react'
import { Settings, ChevronDown, ChevronUp, Info, RotateCcw } from 'lucide-react'

interface RAGSettingsProps {
  onSettingsChange?: (settings: RAGConfig) => void
  compact?: boolean
}

export interface RAGConfig {
  top_k: number
  similarity_threshold: number
  min_similarity_threshold: number
  no_relevant_docs_threshold: number
  chunk_size: number
  chunk_overlap: number
  semantic_weight: number  // 🆕 Hybrid search semantic weight
  keyword_weight: number   // 🆕 Hybrid search keyword weight (auto-calculated)
}

// Default values from backend config
const DEFAULT_CONFIG: RAGConfig = {
  top_k: 5,
  similarity_threshold: 0.50,  // Updated to match backend
  min_similarity_threshold: 0.40,  // Updated to match backend
  no_relevant_docs_threshold: 0.35,  // Updated to match backend
  chunk_size: 800,
  chunk_overlap: 150,
  semantic_weight: 0.8,  // 🆕 80% semantic (vector similarity)
  keyword_weight: 0.2    // 🆕 20% keyword (lexical matching)
}

export default function RAGSettings({ onSettingsChange, compact = false }: RAGSettingsProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [config, setConfig] = useState<RAGConfig>(DEFAULT_CONFIG)

  // Load config from localStorage on mount
  useEffect(() => {
    const savedConfig = localStorage.getItem('rag_config')
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig)
        setConfig({ ...DEFAULT_CONFIG, ...parsed })
      } catch (error) {
        console.error('Failed to parse saved RAG config:', error)
      }
    }
  }, [])

  // Save config to localStorage and notify parent
  const updateConfig = (key: keyof RAGConfig, value: number) => {
    let newConfig = { ...config, [key]: value }

    // 🆕 Auto-update keyword_weight when semantic_weight changes (must sum to 1.0)
    if (key === 'semantic_weight') {
      newConfig.keyword_weight = 1.0 - value
    }

    setConfig(newConfig)
    localStorage.setItem('rag_config', JSON.stringify(newConfig))
    if (onSettingsChange) {
      onSettingsChange(newConfig)
    }
  }

  const resetToDefaults = () => {
    setConfig(DEFAULT_CONFIG)
    localStorage.setItem('rag_config', JSON.stringify(DEFAULT_CONFIG))
    if (onSettingsChange) {
      onSettingsChange(DEFAULT_CONFIG)
    }
  }

  const settingsItems = [
    {
      key: 'top_k' as keyof RAGConfig,
      label: 'Top K Results',
      description: 'Number of document chunks to retrieve',
      min: 1,
      max: 50,
      step: 1,
      value: config.top_k,
      format: (v: number) => v.toString()
    },
    {
      key: 'semantic_weight' as keyof RAGConfig,
      label: '🆕 Semantic Weight (Vector)',
      description: 'Balance between semantic (vector) and keyword (lexical) search. Higher = more semantic.',
      min: 0.0,
      max: 1.0,
      step: 0.05,
      value: config.semantic_weight,
      format: (v: number) => `${(v * 100).toFixed(0)}% semantic / ${((1-v) * 100).toFixed(0)}% keyword`
    },
    {
      key: 'similarity_threshold' as keyof RAGConfig,
      label: 'Similarity Threshold',
      description: 'Minimum similarity score for chunk retrieval (higher = stricter)',
      min: 0.0,
      max: 1.0,
      step: 0.05,
      value: config.similarity_threshold,
      format: (v: number) => `${(v * 100).toFixed(0)}%`
    },
    {
      key: 'min_similarity_threshold' as keyof RAGConfig,
      label: 'Min Similarity Threshold',
      description: 'Fallback minimum threshold for retrieval',
      min: 0.0,
      max: 1.0,
      step: 0.05,
      value: config.min_similarity_threshold,
      format: (v: number) => `${(v * 100).toFixed(0)}%`
    },
    {
      key: 'no_relevant_docs_threshold' as keyof RAGConfig,
      label: 'Relevance Threshold',
      description: 'Threshold to determine if documents are relevant to query',
      min: 0.0,
      max: 1.0,
      step: 0.05,
      value: config.no_relevant_docs_threshold,
      format: (v: number) => `${(v * 100).toFixed(0)}%`
    },
    {
      key: 'chunk_size' as keyof RAGConfig,
      label: 'Chunk Size',
      description: 'Size of text chunks in characters',
      min: 200,
      max: 2000,
      step: 100,
      value: config.chunk_size,
      format: (v: number) => `${v} chars`
    },
    {
      key: 'chunk_overlap' as keyof RAGConfig,
      label: 'Chunk Overlap',
      description: 'Overlap between consecutive chunks',
      min: 0,
      max: 500,
      step: 50,
      value: config.chunk_overlap,
      format: (v: number) => `${v} chars`
    }
  ]

  // Compact mode for sidebar (always show key settings)
  if (compact) {
    const keySettings = settingsItems.filter(item =>
      ['top_k', 'semantic_weight', 'similarity_threshold'].includes(item.key)
    )

    return (
      <div className="space-y-3">
        {keySettings.map((item) => (
          <div key={item.key} className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-medium text-slate-600 dark:text-slate-400">
                {item.label}
              </label>
              <span className="text-[10px] font-mono text-blue-600 dark:text-blue-400">
                {item.format(item.value)}
              </span>
            </div>
            <input
              type="range"
              min={item.min}
              max={item.max}
              step={item.step}
              value={item.value}
              onChange={(e) => updateConfig(item.key, parseFloat(e.target.value))}
              className="w-full h-1 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>
        ))}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-[10px] text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1 w-full justify-center py-1"
        >
          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {isExpanded ? 'Less' : 'More'}
        </button>

        {isExpanded && (
          <div className="space-y-3 pt-2 border-t border-slate-200 dark:border-slate-700">
            {settingsItems.filter(item => !['top_k', 'semantic_weight', 'similarity_threshold'].includes(item.key)).map((item) => (
              <div key={item.key} className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-medium text-slate-600 dark:text-slate-400">
                    {item.label}
                  </label>
                  <span className="text-[10px] font-mono text-blue-600 dark:text-blue-400">
                    {item.format(item.value)}
                  </span>
                </div>
                <input
                  type="range"
                  min={item.min}
                  max={item.max}
                  step={item.step}
                  value={item.value}
                  onChange={(e) => updateConfig(item.key, parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
            ))}
            <button
              onClick={resetToDefaults}
              className="text-[10px] text-slate-600 hover:text-slate-700 dark:text-slate-400 flex items-center gap-1 w-full justify-center py-1"
            >
              <RotateCcw className="w-3 h-3" />
              Reset All
            </button>
          </div>
        )}
      </div>
    )
  }

  // Full mode for main chat interface
  return (
    <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <div className="px-4 py-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors w-full"
        >
          <Settings className="w-4 h-4" />
          <span>RAG Settings</span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 ml-auto" />
          ) : (
            <ChevronDown className="w-4 h-4 ml-auto" />
          )}
        </button>

        {isExpanded && (
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1">
                <Info className="w-3 h-3" />
                Adjust retrieval and generation parameters
              </p>
              <button
                onClick={resetToDefaults}
                className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                Reset
              </button>
            </div>

            <div className="space-y-4">
              {settingsItems.map((item) => (
                <div key={item.key} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {item.label}
                    </label>
                    <span className="text-xs font-mono text-blue-600 dark:text-blue-400">
                      {item.format(item.value)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={item.min}
                    max={item.max}
                    step={item.step}
                    value={item.value}
                    onChange={(e) => updateConfig(item.key, parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 italic">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Export function to get current config
export function getCurrentRAGConfig(): RAGConfig {
  if (typeof window === 'undefined') return DEFAULT_CONFIG

  const savedConfig = localStorage.getItem('rag_config')
  if (savedConfig) {
    try {
      return { ...DEFAULT_CONFIG, ...JSON.parse(savedConfig) }
    } catch {
      return DEFAULT_CONFIG
    }
  }
  return DEFAULT_CONFIG
}
