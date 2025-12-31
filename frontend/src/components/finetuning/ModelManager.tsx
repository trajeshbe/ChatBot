/**
 * Model Manager Component
 *
 * Manage fine-tuned models with:
 * - Model registry and metadata
 * - Deployment status and controls
 * - Model download/export
 */

import { useState, useEffect } from 'react'
import { Package, Download, Play, StopCircle, Trash2, Eye, CheckCircle, XCircle } from 'lucide-react'

interface Model {
  id: string
  name: string
  job_id: string
  base_model: string
  finetuning_method: string
  model_path: string
  adapter_path: string | null
  status: string  // Backend returns 'status' not 'deployment_status'
  deployment_target: string | null
  endpoint_url: string | null
  quantization: string
  final_metrics: any
  created_at: string
  user_id: string | null
  project_id: string | null
}

interface ModelManagerProps {
  onRefresh?: () => void
}

export default function ModelManager({ onRefresh }: ModelManagerProps) {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)
  const [showDeployForm, setShowDeployForm] = useState(false)
  const [deploymentTarget, setDeploymentTarget] = useState('ollama')

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models`)
      if (response.ok) {
        const data = await response.json()
        setModels(data.models || [])
      }
    } catch (error) {
      console.error('Error loading models:', error)
    }
    setLoading(false)
  }

  const deployModel = async (modelId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deployment_target: deploymentTarget,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        alert(`✅ Model deployed successfully!\n\nEndpoint: ${result.endpoint_url || 'N/A'}`)
        setShowDeployForm(false)
        await loadModels()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Deployment failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error deploying model:', error)
      alert('❌ Deployment failed. Please try again.')
    }
  }

  const undeployModel = async (modelId: string) => {
    if (!confirm('⚠️ Undeploy this model?')) return

    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/undeploy`, {
        method: 'POST',
      })

      if (response.ok) {
        alert('✅ Model undeployed successfully!')
        await loadModels()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Undeploy failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error undeploying model:', error)
      alert('❌ Undeploy failed. Please try again.')
    }
  }

  const deleteModel = async (modelId: string, name: string) => {
    if (!confirm(`⚠️ Delete model "${name}"?\n\nThis will delete the model files and cannot be undone.`)) {
      return
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        alert('✅ Model deleted successfully!')
        await loadModels()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Delete failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error deleting model:', error)
      alert('❌ Delete failed. Please try again.')
    }
  }

  const downloadModel = async (model: Model) => {
    alert(`Model download would start for: ${model.name}\n\nPath: ${model.model_path}`)
    // TODO: Implement actual download logic
  }

  const getDeploymentStatusBadge = (status: string) => {
    switch (status) {
      case 'deployed':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
            <CheckCircle className="w-3 h-3" />
            Deployed
          </span>
        )
      case 'failed':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs rounded-full">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        )
      default:
        return (
          <span className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs rounded-full">
            Not Deployed
          </span>
        )
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Fine-Tuned Models
        </h3>
        <button
          onClick={loadModels}
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          Refresh
        </button>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : models.length === 0 ? (
          <div className="col-span-full bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-12 text-center">
            <Package className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <p className="text-slate-500 dark:text-slate-400">No fine-tuned models yet</p>
          </div>
        ) : (
          models.map((model) => (
            <div
              key={model.id}
              className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-5 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Package className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  <h4 className="font-semibold text-slate-900 dark:text-white truncate">
                    {model.name}
                  </h4>
                </div>
                {getDeploymentStatusBadge(model.status)}
              </div>

              {/* Details */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Base Model</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium truncate ml-2">
                    {model.base_model.split('/').pop()}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Method</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium">
                    {model.finetuning_method.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Quantization</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium">
                    {model.quantization || 'None'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Created</span>
                  <span className="text-slate-700 dark:text-slate-300">
                    {new Date(model.created_at).toLocaleDateString()}
                  </span>
                </div>
                {model.endpoint_url && (
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Endpoint</p>
                    <p className="text-xs font-mono text-blue-600 dark:text-blue-400 truncate">
                      {model.endpoint_url}
                    </p>
                  </div>
                )}
              </div>

              {/* Final Metrics */}
              {model.final_metrics && (
                <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 mb-4">
                  <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Final Metrics
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {model.final_metrics.final_loss && (
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">Loss:</span>{' '}
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {model.final_metrics.final_loss.toFixed(4)}
                        </span>
                      </div>
                    )}
                    {model.final_metrics.perplexity && (
                      <div>
                        <span className="text-slate-500 dark:text-slate-400">Perplexity:</span>{' '}
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {model.final_metrics.perplexity.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                {model.status === 'deployed' ? (
                  <button
                    onClick={() => undeployModel(model.id)}
                    className="flex-1 px-3 py-2 bg-orange-600 text-white text-sm rounded-lg hover:bg-orange-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <StopCircle className="w-4 h-4" />
                    Undeploy
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      setSelectedModel(model)
                      setShowDeployForm(true)
                    }}
                    className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Deploy
                  </button>
                )}
                <button
                  onClick={() => downloadModel(model)}
                  className="px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                  title="Download model"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={() => deleteModel(model.id, model.name)}
                  className="px-3 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                  title="Delete model"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Deploy Modal */}
      {showDeployForm && selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Deploy Model: {selectedModel.name}
              </h3>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Deployment Target
                </label>
                <select
                  value={deploymentTarget}
                  onChange={(e) => setDeploymentTarget(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="ollama">Ollama (Local)</option>
                  <option value="vllm">vLLM (GPU Server)</option>
                  <option value="torchserve">TorchServe</option>
                  <option value="triton">NVIDIA Triton</option>
                </select>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  Choose the inference server for deployment
                </p>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowDeployForm(false)
                  setSelectedModel(null)
                }}
                className="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => deployModel(selectedModel.id)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
