import { useState, useEffect } from 'react'
import { Settings, ChevronDown, ChevronUp, Info, RotateCcw } from 'lucide-react'

interface RAGSettingsProps {
  onSettingsChange?: (settings: RAGConfig) => void
}

export interface RAGConfig {
  top_k: number
  similarity_threshold: number
  min_similarity_threshold: number
  no_relevant_docs_threshold: number
  chunk_size: number
  chunk_overlap: number
}

// Default values from backend config
const DEFAULT_CONFIG: RAGConfig = {
  top_k: 5,
  similarity_threshold: 0.70,
  min_similarity_threshold: 0.55,
  no_relevant_docs_threshold: 0.65,
  chunk_size: 800,
  chunk_overlap: 150
}

export default function RAGSettings({ onSettingsChange }: RAGSettingsProps) {
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
    const newConfig = { ...config, [key]: value }
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
      max: 20,
      step: 1,
      value: config.top_k,
      format: (v: number) => v.toString()
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
