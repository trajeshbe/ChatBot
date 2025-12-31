import { useState, useEffect } from 'react'
import { Cpu, HardDrive, Activity, CheckCircle, XCircle, Server, AlertCircle, BarChart3, ChevronDown, ChevronUp, Database, Download, Trash2, Loader } from 'lucide-react'
import axios from 'axios'

interface OllamaModel {
  name: string
  model: string
  modified_at: string
  size: number
  digest: string
  details?: {
    format?: string
    family?: string
    families?: string[]
    parameter_size?: string
    quantization_level?: string
  }
}

interface RunningModel {
  name: string
  model: string
  size: number
  digest: string
  expires_at: string
  size_vram: number
}

interface ModelStats {
  total_models: number
  total_size_gb: number
  total_size_bytes: number
  models_by_family: Record<string, number>
  largest_model: {
    name: string
    size_gb: number
    size_bytes: number
  }
  smallest_model: {
    name: string
    size_gb: number
    size_bytes: number
  }
}

interface ModelDetails {
  modelfile: string
  parameters: string
  template: string
  details: {
    format?: string
    family?: string
    families?: string[]
    parameter_size?: string
    quantization_level?: string
  }
  model_info?: Record<string, any>
}

interface HealthCheckResponse {
  status: string
  ollama_available: boolean
  endpoint: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function OllamaModelsManager() {
  const [models, setModels] = useState<OllamaModel[]>([])
  const [runningModels, setRunningModels] = useState<RunningModel[]>([])
  const [stats, setStats] = useState<ModelStats | null>(null)
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Expanded model details
  const [expandedModel, setExpandedModel] = useState<string | null>(null)
  const [modelDetails, setModelDetails] = useState<Record<string, ModelDetails>>({})
  const [loadingDetails, setLoadingDetails] = useState<Record<string, boolean>>({})

  // Phase 2: Pull/Delete operations
  const [pullModelName, setPullModelName] = useState('')
  const [pulling, setPulling] = useState(false)
  const [pullProgress, setPullProgress] = useState<string>('')
  const [deleting, setDeleting] = useState<Record<string, boolean>>({})

  useEffect(() => {
    fetchAll()
    // Refresh every 30 seconds
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchAll = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all data in parallel
      const [healthRes, modelsRes, runningRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/admin/ollama/health`),
        axios.get(`${API_URL}/api/v1/admin/ollama/models`),
        axios.get(`${API_URL}/api/v1/admin/ollama/running`),
        axios.get(`${API_URL}/api/v1/admin/ollama/stats`)
      ])

      setHealth(healthRes.data)
      setModels(modelsRes.data.models || [])
      setRunningModels(runningRes.data.running_models || [])
      setStats(statsRes.data.stats || null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch Ollama data')
      console.error('Error fetching Ollama data:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchModelDetails = async (modelName: string) => {
    if (modelDetails[modelName]) {
      // Already fetched, just toggle
      setExpandedModel(expandedModel === modelName ? null : modelName)
      return
    }

    try {
      setLoadingDetails({ ...loadingDetails, [modelName]: true })
      const response = await axios.get(`${API_URL}/api/v1/admin/ollama/models/${modelName}`)
      setModelDetails({ ...modelDetails, [modelName]: response.data.details })
      setExpandedModel(modelName)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch model details')
      console.error('Error fetching model details:', err)
    } finally {
      setLoadingDetails({ ...loadingDetails, [modelName]: false })
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  }

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString()
  }

  const getModelFamily = (modelName: string): string => {
    return modelName.split(':')[0] || modelName
  }

  const getModelTag = (modelName: string): string => {
    return modelName.split(':')[1] || 'latest'
  }

  const isModelRunning = (modelName: string): boolean => {
    return runningModels.some(rm => rm.name === modelName)
  }

  // Phase 2: Pull model handler
  const handlePullModel = async () => {
    if (!pullModelName.trim()) {
      setError('Please enter a model name')
      return
    }

    try {
      setPulling(true)
      setPullProgress('Connecting to Ollama...')
      setError(null)

      const response = await fetch(`${API_URL}/api/v1/admin/ollama/pull`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_name: pullModelName.trim() }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const text = decoder.decode(value)
          const lines = text.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))

                if (data.status === 'error') {
                  // Provide helpful error messages for common issues
                  let errorMessage = data.error
                  if (data.error.includes('file does not exist') || data.error.includes('manifest')) {
                    errorMessage = `Model "${pullModelName}" not found in Ollama registry.

Common issues:
• Model name may be incorrect or doesn't exist
• Try without quantization suffix (Ollama handles this automatically)
• For 8B models, use: llama3.1:8b, mistral:7b, qwen2.5:7b
• For 3B models, use: llama3.2:3b, llama3.2
• Check https://ollama.com/library for available models

Examples:
  ✓ llama3.1:8b (correct)
  ✗ llama3.2:8b-instruct-q4_K_M (incorrect - too specific)
  ✓ mistral (correct - uses latest)
  ✓ qwen2.5:7b (correct)`
                  }
                  setError(errorMessage)
                  setPullProgress(`Error: ${data.error}`)
                  break
                } else if (data.status === 'success') {
                  setPullProgress('Model pulled successfully!')
                  setPullModelName('')
                  // Refresh model list
                  setTimeout(() => fetchAll(), 1000)
                } else {
                  setPullProgress(data.status || 'Downloading...')
                }
              } catch (e) {
                console.error('Failed to parse progress:', e)
              }
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to pull model')
      console.error('Error pulling model:', err)
    } finally {
      setPulling(false)
      setTimeout(() => setPullProgress(''), 5000)
    }
  }

  // Phase 2: Delete model handler
  const handleDeleteModel = async (modelName: string) => {
    if (!confirm(`Are you sure you want to delete model "${modelName}"? This action cannot be undone.`)) {
      return
    }

    try {
      setDeleting({ ...deleting, [modelName]: true })
      setError(null)

      const response = await axios.delete(`${API_URL}/api/v1/admin/ollama/models/${modelName}`)

      if (response.data.success) {
        // Refresh model list
        await fetchAll()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete model')
      console.error('Error deleting model:', err)
    } finally {
      setDeleting({ ...deleting, [modelName]: false })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Server className="w-6 h-6 text-purple-500" />
          <h2 className="text-2xl font-bold text-gray-900">Ollama Model Management</h2>
        </div>
        <button
          onClick={fetchAll}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
        >
          <Activity className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <p className="text-gray-600">
        Manage and monitor Ollama models. View installed models, check running models, and analyze resource usage.
      </p>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-800">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Health Status */}
      {health && (
        <div className={`rounded-lg border-2 p-4 ${
          health.ollama_available
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center gap-3">
            {health.ollama_available ? (
              <CheckCircle className="w-6 h-6 text-green-500" />
            ) : (
              <XCircle className="w-6 h-6 text-red-500" />
            )}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Ollama Service Status</h3>
              <p className="text-sm text-gray-600">
                Status: <span className={health.ollama_available ? 'text-green-700 font-medium' : 'text-red-700 font-medium'}>
                  {health.status}
                </span> | Endpoint: {health.endpoint}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-primary-500" />
              <div>
                <p className="text-sm text-gray-600">Total Models</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_models}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <HardDrive className="w-8 h-8 text-purple-500" />
              <div>
                <p className="text-sm text-gray-600">Total Size</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_size_gb} GB</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">Running Models</p>
                <p className="text-2xl font-bold text-gray-900">{runningModels.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-orange-500" />
              <div>
                <p className="text-sm text-gray-600">Model Families</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Object.keys(stats.models_by_family).length}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pull Model Section (Phase 2) */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Download className="w-5 h-5 text-primary-500" />
            Pull/Install New Model
          </h3>
        </div>
        <div className="p-6">
          <div className="flex gap-4">
            <input
              type="text"
              value={pullModelName}
              onChange={(e) => setPullModelName(e.target.value)}
              placeholder="e.g., llama3.1:8b, mistral:7b, qwen2.5:7b"
              disabled={pulling}
              onKeyPress={(e) => e.key === 'Enter' && handlePullModel()}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={handlePullModel}
              disabled={pulling || !pullModelName.trim()}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
            >
              {pulling ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  Pulling...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Pull Model
                </>
              )}
            </button>
          </div>

          {pullProgress && (
            <div className="mt-4 p-3 bg-primary-50 border border-primary-200 rounded-lg">
              <p className="text-sm text-blue-800">{pullProgress}</p>
            </div>
          )}

          <p className="mt-3 text-sm text-gray-600">
            Enter a model name from the Ollama library (e.g., llama2, mistral, qwen2.5).
            Include a tag for specific versions (e.g., llama2:7b, mistral:latest).
          </p>
        </div>
      </div>

      {/* Running Models */}
      {runningModels.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-500" />
              Running Models ({runningModels.length})
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {runningModels.map((model) => (
              <div key={model.digest} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{model.name}</h4>
                    <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                      <div>
                        <span className="text-gray-500">Model Size:</span>
                        <span className="ml-2 text-gray-700">{formatBytes(model.size)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">VRAM Usage:</span>
                        <span className="ml-2 text-gray-700">{formatBytes(model.size_vram)}</span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-gray-500">Expires At:</span>
                        <span className="ml-2 text-gray-700">{formatDate(model.expires_at)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <Activity className="w-3 h-3" />
                      Running
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Installed Models */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Server className="w-5 h-5" />
            Installed Models ({models.length})
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">
            Loading models...
          </div>
        ) : models.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No models installed. Pull models using Ollama CLI.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {models.map((model) => {
              const family = getModelFamily(model.name)
              const tag = getModelTag(model.name)
              const isRunning = isModelRunning(model.name)
              const isExpanded = expandedModel === model.name
              const details = modelDetails[model.name]

              return (
                <div key={model.digest} className="hover:bg-gray-50">
                  <div className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-semibold text-gray-900">{model.name}</h4>
                          {isRunning && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <Activity className="w-3 h-3" />
                              Running
                            </span>
                          )}
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-blue-800">
                            {family}
                          </span>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {tag}
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Size:</span>
                            <span className="ml-2 text-gray-700 font-medium">{formatBytes(model.size)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Modified:</span>
                            <span className="ml-2 text-gray-700">{formatDate(model.modified_at)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Digest:</span>
                            <span className="ml-2 text-gray-700 font-mono text-xs">{model.digest.substring(0, 12)}...</span>
                          </div>
                        </div>
                      </div>

                      <div className="ml-4 flex gap-2">
                        <button
                          onClick={() => fetchModelDetails(model.name)}
                          disabled={loadingDetails[model.name]}
                          className="px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 rounded-lg hover:bg-purple-100 flex items-center gap-1"
                        >
                          {loadingDetails[model.name] ? (
                            'Loading...'
                          ) : (
                            <>
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              Details
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => handleDeleteModel(model.name)}
                          disabled={deleting[model.name]}
                          className="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center gap-1"
                        >
                          {deleting[model.name] ? (
                            <>
                              <Loader className="w-4 h-4 animate-spin" />
                              Deleting...
                            </>
                          ) : (
                            <>
                              <Trash2 className="w-4 h-4" />
                              Delete
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && details && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          {details.details.format && (
                            <div>
                              <span className="text-sm text-gray-500">Format:</span>
                              <span className="ml-2 text-sm text-gray-700 font-medium">{details.details.format}</span>
                            </div>
                          )}
                          {details.details.parameter_size && (
                            <div>
                              <span className="text-sm text-gray-500">Parameters:</span>
                              <span className="ml-2 text-sm text-gray-700 font-medium">{details.details.parameter_size}</span>
                            </div>
                          )}
                          {details.details.quantization_level && (
                            <div>
                              <span className="text-sm text-gray-500">Quantization:</span>
                              <span className="ml-2 text-sm text-gray-700 font-medium">{details.details.quantization_level}</span>
                            </div>
                          )}
                          {details.details.families && (
                            <div>
                              <span className="text-sm text-gray-500">Family:</span>
                              <span className="ml-2 text-sm text-gray-700 font-medium">{details.details.families.join(', ')}</span>
                            </div>
                          )}
                        </div>

                        <div className="space-y-2">
                          <div>
                            <h5 className="text-sm font-semibold text-gray-700 mb-1">Parameters:</h5>
                            <pre className="text-xs bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto">
                              {details.parameters}
                            </pre>
                          </div>

                          <div>
                            <h5 className="text-sm font-semibold text-gray-700 mb-1">Template:</h5>
                            <pre className="text-xs bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto">
                              {details.template}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Model Families Breakdown */}
      {stats && Object.keys(stats.models_by_family).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Models by Family
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.models_by_family).map(([family, count]) => (
              <div key={family} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600">{family}</p>
                <p className="text-xl font-bold text-gray-900">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Notice */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
          <div>
            <h4 className="font-semibold text-green-900 mb-1">Phase 2: Full Model Management (Active)</h4>
            <ul className="text-sm text-green-800 space-y-1">
              <li>• ✓ View all installed Ollama models with metadata</li>
              <li>• ✓ Monitor running models and resource usage (VRAM)</li>
              <li>• ✓ Analyze model statistics and size breakdown</li>
              <li>• ✓ View detailed model information and configurations</li>
              <li>• ✓ <strong>Pull/Install new models</strong> from Ollama library with progress tracking</li>
              <li>• ✓ <strong>Delete installed models</strong> to free up disk space</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
