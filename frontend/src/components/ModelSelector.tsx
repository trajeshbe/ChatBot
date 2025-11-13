import { useState, useEffect } from 'react'
import { ChevronDown, Cpu, Cloud, Zap, Check } from 'lucide-react'
import axios from 'axios'

interface Model {
  id: string
  name: string
  provider: string
  type: string
  context_length: number
  cost_per_1k_tokens: number
  requires_gpu: boolean
  description: string
  available: boolean
  recommended: boolean
}

interface ModelSelectorProps {
  selectedModel: string | null
  onModelChange: (modelId: string) => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<{ proprietary: Model[], local_gpu: Model[], local_cpu: Model[] }>({
    proprietary: [],
    local_gpu: [],
    local_cpu: []
  })
  const [defaultModel, setDefaultModel] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [gpuAvailable, setGpuAvailable] = useState(false)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/models/`)
      setModels(response.data.grouped)
      setDefaultModel(response.data.default)
      setGpuAvailable(response.data.gpu_info?.available || false)

      // Set selected model to default if not set
      if (!selectedModel && response.data.default) {
        onModelChange(response.data.default)
      }
    } catch (error) {
      console.error('Error fetching models:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSelectedModelInfo = (): Model | null => {
    const allModels = [...models.proprietary, ...models.local_gpu, ...models.local_cpu]
    return allModels.find(m => m.id === (selectedModel || defaultModel)) || null
  }

  const getModelIcon = (type: string) => {
    switch (type) {
      case 'proprietary':
        return <Cloud className="w-4 h-4" />
      case 'local-gpu':
        return <Zap className="w-4 h-4 text-green-500" />
      case 'local-cpu':
        return <Cpu className="w-4 h-4 text-blue-500" />
      default:
        return <Cpu className="w-4 h-4" />
    }
  }

  const getModelBadge = (model: Model) => {
    if (model.type === 'proprietary') {
      return (
        <span className="text-xs px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300">
          Proprietary
        </span>
      )
    } else if (model.requires_gpu) {
      return (
        <span className="text-xs px-2 py-0.5 rounded bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
          GPU
        </span>
      )
    } else {
      return (
        <span className="text-xs px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
          CPU
        </span>
      )
    }
  }

  const selectedModelInfo = getSelectedModelInfo()

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg">
        <Cpu className="w-4 h-4 animate-pulse" />
        <span className="text-sm text-slate-600 dark:text-slate-400">Loading models...</span>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Selected Model Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors w-full sm:w-auto"
      >
        {selectedModelInfo && getModelIcon(selectedModelInfo.type)}
        <div className="flex-1 text-left">
          <div className="text-sm font-medium text-slate-900 dark:text-white">
            {selectedModelInfo?.name || 'Select Model'}
          </div>
          {selectedModelInfo && (
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {selectedModelInfo.provider}
              {selectedModelInfo.cost_per_1k_tokens > 0 && (
                <span className="ml-2">
                  ${selectedModelInfo.cost_per_1k_tokens.toFixed(4)}/1K tokens
                </span>
              )}
              {selectedModelInfo.cost_per_1k_tokens === 0 && (
                <span className="ml-2 text-green-600 dark:text-green-400">Free (Local)</span>
              )}
            </div>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full mt-2 w-full sm:w-96 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          {/* Proprietary Models */}
          {models.proprietary.length > 0 && (
            <div className="p-2">
              <div className="px-2 py-1 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                <Cloud className="w-3 h-3 inline mr-1" />
                Proprietary API
              </div>
              {models.proprietary.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    onModelChange(model.id)
                    setIsOpen(false)
                  }}
                  className={`w-full text-left px-3 py-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
                    selectedModel === model.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                          {model.name}
                        </span>
                        {model.recommended && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
                            Recommended
                          </span>
                        )}
                        {selectedModel === model.id && (
                          <Check className="w-4 h-4 text-blue-600" />
                        )}
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                        {model.description}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {getModelBadge(model)}
                        <span className="text-xs text-slate-500">
                          ${model.cost_per_1k_tokens.toFixed(4)}/1K tokens
                        </span>
                        <span className="text-xs text-slate-500">
                          {model.context_length.toLocaleString()} tokens
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Local GPU Models */}
          {models.local_gpu.length > 0 && (
            <div className="p-2 border-t border-slate-200 dark:border-slate-700">
              <div className="px-2 py-1 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                <Zap className="w-3 h-3 inline mr-1" />
                Local GPU {!gpuAvailable && '(GPU Not Available)'}
              </div>
              {models.local_gpu.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    onModelChange(model.id)
                    setIsOpen(false)
                  }}
                  disabled={!gpuAvailable}
                  className={`w-full text-left px-3 py-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
                    selectedModel === model.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  } ${!gpuAvailable ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                          {model.name}
                        </span>
                        {model.recommended && gpuAvailable && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
                            Recommended
                          </span>
                        )}
                        {selectedModel === model.id && (
                          <Check className="w-4 h-4 text-blue-600" />
                        )}
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                        {model.description}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {getModelBadge(model)}
                        <span className="text-xs text-green-600 dark:text-green-400">Free (Local)</span>
                        <span className="text-xs text-slate-500">
                          Min {model.min_gpu_memory_gb}GB GPU
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Local CPU Models */}
          {models.local_cpu.length > 0 && (
            <div className="p-2 border-t border-slate-200 dark:border-slate-700">
              <div className="px-2 py-1 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                <Cpu className="w-3 h-3 inline mr-1" />
                Local CPU
              </div>
              {models.local_cpu.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    onModelChange(model.id)
                    setIsOpen(false)
                  }}
                  className={`w-full text-left px-3 py-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
                    selectedModel === model.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                          {model.name}
                        </span>
                        {model.recommended && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
                            Recommended
                          </span>
                        )}
                        {selectedModel === model.id && (
                          <Check className="w-4 h-4 text-blue-600" />
                        )}
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                        {model.description}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {getModelBadge(model)}
                        <span className="text-xs text-green-600 dark:text-green-400">Free (Local)</span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}
