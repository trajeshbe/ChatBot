/**
 * Model Lifecycle Manager
 *
 * Complete MLOps lifecycle management for fine-tuned models:
 * - Evaluation: Test model performance metrics
 * - Deployment: Deploy to Ollama/vLLM
 * - Monitoring: Track usage and performance
 * - Governance: Model versioning, approval, deprecation
 */

import { useState, useEffect } from 'react'
import {
  Activity,
  Rocket,
  BarChart3,
  Shield,
  PlayCircle,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Clock,
  Archive,
  ExternalLink,
  Send,
  ThumbsUp,
  ThumbsDown,
  FileBox
} from 'lucide-react'

interface EvalMetrics {
  perplexity?: number
  bleu_score?: number
  rouge_1?: number
  rouge_2?: number
  rouge_l?: number
  accuracy?: number
  f1_score?: number
  eval_loss?: number
  evaluated_at?: string
  test_samples?: number
}

interface Model {
  id: string
  name: string
  version?: string
  status: string  // registered, approved, deployed, archived, deprecated
  base_model: string
  deployment_url?: string
  ollama_model_name?: string
  vllm_model_name?: string
  total_inferences?: number
  avg_latency_ms?: number
  last_inference_at?: string
  eval_metrics?: EvalMetrics
  deprecated_at?: string
  deprecation_reason?: string
  created_at?: string
  minio_checkpoint_path?: string  // NEW: MinIO artifact path
  finetuning_method?: string
  job_id?: string
}

interface ApprovalStatus {
  model_status: string
  approval_status?: string
  can_deploy: boolean
  approval_id?: string
  requested_at?: string
  reviewed_at?: string
  review_comments?: string
}

interface ModelLifecycleManagerProps {
  models: Model[]
  onRefresh?: () => void
}

type Tab = 'evaluation' | 'deployment' | 'monitoring' | 'governance'

export default function ModelLifecycleManager({ models, onRefresh }: ModelLifecycleManagerProps) {
  const [activeTab, setActiveTab] = useState<Tab>('evaluation')
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)
  const [loading, setLoading] = useState(false)
  const [deploymentConfig, setDeploymentConfig] = useState({
    target: 'ollama',
    model_name: ''
  })
  const [approvalStatus, setApprovalStatus] = useState<ApprovalStatus | null>(null)
  const [approvalReason, setApprovalReason] = useState('')
  const [reviewComments, setReviewComments] = useState('')

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const MINIO_CONSOLE = process.env.NEXT_PUBLIC_MINIO_CONSOLE_URL || 'http://localhost:9001'

  useEffect(() => {
    if (models.length > 0 && !selectedModel) {
      // Auto-select first completed model
      const completed = models.find(m => m.status === 'completed')
      setSelectedModel(completed || models[0])
    }
  }, [models])

  const runEvaluation = async (modelId: string) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/evaluate`, {
        method: 'POST'
      })

      if (response.ok) {
        const data = await response.json()
        alert(`Evaluation completed!\n\nPerplexity: ${data.eval_metrics.perplexity}\nBLEU: ${data.eval_metrics.bleu_score}`)
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`Evaluation failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Evaluation error:', error)
      alert('Failed to run evaluation')
    } finally {
      setLoading(false)
    }
  }

  const deployModel = async (modelId: string) => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(deploymentConfig)
      })

      if (response.ok) {
        const data = await response.json()
        alert(`Deployed to ${data.deployment_target}!\n\nModel: ${data.deployed_model_name}\nURL: ${data.deployment_url}`)
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`Deployment failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Deployment error:', error)
      alert('Failed to deploy model')
    } finally {
      setLoading(false)
    }
  }

  const deprecateModel = async (modelId: string) => {
    const reason = prompt('Reason for deprecation:')
    if (!reason) return

    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/deprecate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      })

      if (response.ok) {
        alert('Model deprecated successfully')
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`Deprecation failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Deprecation error:', error)
      alert('Failed to deprecate model')
    } finally {
      setLoading(false)
    }
  }

  const renderMetricCard = (label: string, value: any, unit: string = '', goodThreshold?: number) => {
    const numValue = typeof value === 'number' ? value : parseFloat(value)
    const isGood = goodThreshold ? numValue >= goodThreshold : true

    return (
      <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
        <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
        <p className={`text-2xl font-bold ${isGood ? 'text-green-600' : 'text-orange-600'}`}>
          {value?.toFixed ? value.toFixed(3) : value || 'N/A'}{unit}
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
      {/* Tab Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <div className="flex space-x-1 p-2">
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'evaluation'
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm font-medium">Evaluation</span>
          </button>
          <button
            onClick={() => setActiveTab('deployment')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'deployment'
                ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Rocket className="w-4 h-4" />
            <span className="text-sm font-medium">Deployment</span>
          </button>
          <button
            onClick={() => setActiveTab('monitoring')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'monitoring'
                ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">Monitoring</span>
          </button>
          <button
            onClick={() => setActiveTab('governance')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'governance'
                ? 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span className="text-sm font-medium">Governance</span>
          </button>
        </div>
      </div>

      {/* Model Selector */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Select Model
        </label>
        <select
          value={selectedModel?.id || ''}
          onChange={(e) => {
            const model = models.find(m => m.id === e.target.value)
            setSelectedModel(model || null)
            if (model) {
              setDeploymentConfig(prev => ({ ...prev, model_name: `${model.name}-deployed` }))
            }
          }}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
        >
          <option value="">Select a model...</option>
          {models.map(model => (
            <option key={model.id} value={model.id}>
              {model.name} ({model.status})
            </option>
          ))}
        </select>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {!selectedModel ? (
          <div className="text-center py-12 text-slate-500">
            Select a model to manage its lifecycle
          </div>
        ) : (
          <>
            {/* Evaluation Tab */}
            {activeTab === 'evaluation' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Model Evaluation
                  </h3>
                  <button
                    onClick={() => runEvaluation(selectedModel.id)}
                    disabled={loading}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-400"
                  >
                    <PlayCircle className="w-4 h-4" />
                    <span>{loading ? 'Running...' : 'Run Evaluation'}</span>
                  </button>
                </div>

                {selectedModel.eval_metrics ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {selectedModel.eval_metrics.perplexity && renderMetricCard('Perplexity', selectedModel.eval_metrics.perplexity, '', 0)}
                    {selectedModel.eval_metrics.bleu_score && renderMetricCard('BLEU Score', selectedModel.eval_metrics.bleu_score, '', 0.6)}
                    {selectedModel.eval_metrics.rouge_1 && renderMetricCard('ROUGE-1', selectedModel.eval_metrics.rouge_1, '', 0.6)}
                    {selectedModel.eval_metrics.rouge_2 && renderMetricCard('ROUGE-2', selectedModel.eval_metrics.rouge_2, '', 0.5)}
                    {selectedModel.eval_metrics.rouge_l && renderMetricCard('ROUGE-L', selectedModel.eval_metrics.rouge_l, '', 0.6)}
                    {selectedModel.eval_metrics.accuracy && renderMetricCard('Accuracy', selectedModel.eval_metrics.accuracy, '', 0.8)}
                    {selectedModel.eval_metrics.f1_score && renderMetricCard('F1 Score', selectedModel.eval_metrics.f1_score, '', 0.7)}
                    {selectedModel.eval_metrics.eval_loss && renderMetricCard('Eval Loss', selectedModel.eval_metrics.eval_loss, '', 0)}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <BarChart3 className="w-12 h-12 mx-auto text-slate-400 mb-3" />
                    <p className="text-slate-600 dark:text-slate-400">
                      No evaluation metrics available. Run evaluation to generate metrics.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Deployment Tab */}
            {activeTab === 'deployment' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Model Deployment
                </h3>

                {selectedModel.status === 'deployed' ? (
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                      <CheckCircle className="w-6 h-6 text-green-600" />
                      <div>
                        <p className="font-medium text-green-900 dark:text-green-100">Model is deployed</p>
                        <p className="text-sm text-green-700 dark:text-green-300">
                          {selectedModel.ollama_model_name || selectedModel.vllm_model_name}
                        </p>
                      </div>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Deployment URL:</p>
                      <p className="font-mono text-sm text-slate-900 dark:text-white">
                        {selectedModel.deployment_url}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                          Deployment Target
                        </label>
                        <select
                          value={deploymentConfig.target}
                          onChange={(e) => setDeploymentConfig({ ...deploymentConfig, target: e.target.value })}
                          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900"
                        >
                          <option value="ollama">Ollama (Local)</option>
                          <option value="vllm">vLLM (High Performance)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                          Deployed Model Name
                        </label>
                        <input
                          type="text"
                          value={deploymentConfig.model_name}
                          onChange={(e) => setDeploymentConfig({ ...deploymentConfig, model_name: e.target.value })}
                          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900"
                          placeholder="my-model-v1"
                        />
                      </div>
                    </div>

                    <button
                      onClick={() => deployModel(selectedModel.id)}
                      disabled={loading || !deploymentConfig.model_name}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-slate-400"
                    >
                      <Rocket className="w-5 h-5" />
                      <span>{loading ? 'Deploying...' : 'Deploy Model'}</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Monitoring Tab */}
            {activeTab === 'monitoring' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Performance Monitoring
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-blue-600" />
                      <p className="text-xs text-slate-500 dark:text-slate-400">Total Inferences</p>
                    </div>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {selectedModel.total_inferences?.toLocaleString() || 0}
                    </p>
                  </div>

                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Activity className="w-4 h-4 text-green-600" />
                      <p className="text-xs text-slate-500 dark:text-slate-400">Avg Latency</p>
                    </div>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {selectedModel.avg_latency_ms?.toFixed(0) || 'N/A'} ms
                    </p>
                  </div>

                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Clock className="w-4 h-4 text-purple-600" />
                      <p className="text-xs text-slate-500 dark:text-slate-400">Last Inference</p>
                    </div>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {selectedModel.last_inference_at
                        ? new Date(selectedModel.last_inference_at).toLocaleString()
                        : 'Never'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Governance Tab */}
            {activeTab === 'governance' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Model Governance
                </h3>

                <div className="space-y-4">
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-600 dark:text-slate-400">Status:</p>
                        <p className="font-medium text-slate-900 dark:text-white capitalize">
                          {selectedModel.status}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-600 dark:text-slate-400">Version:</p>
                        <p className="font-medium text-slate-900 dark:text-white">
                          {selectedModel.version || 'v1.0'}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-600 dark:text-slate-400">Created:</p>
                        <p className="font-medium text-slate-900 dark:text-white">
                          {selectedModel.created_at ? new Date(selectedModel.created_at).toLocaleDateString() : 'Unknown'}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-600 dark:text-slate-400">Base Model:</p>
                        <p className="font-medium text-slate-900 dark:text-white truncate">
                          {selectedModel.base_model}
                        </p>
                      </div>
                    </div>
                  </div>

                  {selectedModel.deprecated_at ? (
                    <div className="flex items-start space-x-3 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                      <Archive className="w-5 h-5 text-red-600 mt-0.5" />
                      <div>
                        <p className="font-medium text-red-900 dark:text-red-100">Model Deprecated</p>
                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                          {selectedModel.deprecation_reason}
                        </p>
                        <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                          Deprecated on {new Date(selectedModel.deprecated_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => deprecateModel(selectedModel.id)}
                      disabled={loading}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-slate-400"
                    >
                      <Archive className="w-5 h-5" />
                      <span>{loading ? 'Deprecating...' : 'Deprecate Model'}</span>
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
