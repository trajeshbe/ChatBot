/**
 * Job Manager Component
 *
 * Create and monitor training jobs with:
 * - Three hyperparameter modes: Manual, Recommended, Auto-Tune
 * - Real-time training metrics via WebSocket
 * - Job status monitoring and control
 */

import { useState, useEffect, useRef } from 'react'
import { Play, Pause, StopCircle, Settings, Sliders, Sparkles, TrendingUp, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

interface Job {
  id: string
  name: string
  dataset_id: string
  dataset_name: string
  base_model: string
  finetuning_method: string
  status: string
  progress_percentage: number
  current_step: number
  total_steps: number
  hyperparameters: any
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

interface JobManagerProps {
  onRefresh?: () => void
}

type HyperparamMode = 'manual' | 'recommended' | 'auto-tune'

export default function JobManager({ onRefresh }: JobManagerProps) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [datasets, setDatasets] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [metrics, setMetrics] = useState<any>(null)

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    dataset_id: '',
    base_model: 'Qwen/Qwen2.5-7B-Instruct',
    finetuning_method: 'peft',
    training_objective: 'instruction',
    quantization: '4bit',
  })

  // Hyperparameter mode
  const [hyperparamMode, setHyperparamMode] = useState<HyperparamMode>('recommended')

  // Manual hyperparameters
  const [manualHyperparams, setManualHyperparams] = useState({
    learning_rate: 0.0002,
    num_epochs: 3,
    batch_size: 4,
    gradient_accumulation_steps: 4,
    warmup_steps: 100,
    lora_r: 16,
    lora_alpha: 32,
    lora_dropout: 0.05,
  })

  // Auto-tune config
  const [autoTuneConfig, setAutoTuneConfig] = useState({
    n_trials: 20,
    optimization_metric: 'loss',
    user_constraints: {} as any,
  })

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadJobs()
    loadDatasets()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`)
      if (response.ok) {
        const data = await response.json()
        setJobs(data.jobs || [])
      }
    } catch (error) {
      console.error('Error loading jobs:', error)
    }
    setLoading(false)
  }

  const loadDatasets = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`)
      if (response.ok) {
        const data = await response.json()
        setDatasets(data.datasets || [])
      }
    } catch (error) {
      console.error('Error loading datasets:', error)
    }
  }

  const connectWebSocket = (jobId: string) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const wsUrl = `${API_BASE.replace('http', 'ws')}/api/v1/finetuning/ws/jobs/${jobId}/metrics`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected for job:', jobId)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'metric') {
        setMetrics(data.data)
      } else if (data.type === 'status') {
        // Update job status
        setJobs(jobs.map(j => j.id === jobId ? { ...j, status: data.status } : j))
      } else if (data.type === 'progress') {
        // Update progress
        setJobs(jobs.map(j =>
          j.id === jobId
            ? { ...j, current_step: data.current_step, total_steps: data.total_steps, progress_percentage: data.percentage }
            : j
        ))
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
    }

    wsRef.current = ws
  }

  const createJob = async () => {
    try {
      let hyperparameters = {}

      if (hyperparamMode === 'manual') {
        hyperparameters = manualHyperparams
      } else if (hyperparamMode === 'recommended') {
        // Request recommended hyperparameters from backend
        const dataset = datasets.find(d => d.id === formData.dataset_id)
        const datasetSize = dataset?.sample_count || 1000

        const recommendResponse = await fetch(
          `${API_BASE}/api/v1/finetuning/hyperparameters/recommend`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              finetuning_method: formData.finetuning_method,
              dataset_size: datasetSize,
              available_memory_gb: 24, // TODO: Get from GPU monitor
            })
          }
        )
        if (recommendResponse.ok) {
          hyperparameters = await recommendResponse.json()
        }
      } else if (hyperparamMode === 'auto-tune') {
        // Auto-tune mode - backend will run Optuna
        hyperparameters = {
          auto_tune: true,
          ...autoTuneConfig,
        }
      }

      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          hyperparameters,
        }),
      })

      if (response.ok) {
        const result = await response.json()
        alert(`✅ Job created successfully!\n\nJob ID: ${result.id}\nStatus: ${result.status}`)
        setShowCreateForm(false)
        await loadJobs()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Job creation failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error creating job:', error)
      alert('❌ Job creation failed. Please try again.')
    }
  }

  const submitJob = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/submit`, {
        method: 'POST',
      })

      if (response.ok) {
        alert('✅ Job submitted for training!')
        await loadJobs()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Submit failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error submitting job:', error)
      alert('❌ Submit failed. Please try again.')
    }
  }

  const cancelJob = async (jobId: string) => {
    if (!confirm('⚠️ Cancel this training job?')) return

    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/cancel`, {
        method: 'POST',
      })

      if (response.ok) {
        alert('✅ Job cancelled!')
        await loadJobs()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Cancel failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error cancelling job:', error)
      alert('❌ Cancel failed. Please try again.')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'running':
        return <Play className="w-5 h-5 text-blue-500 animate-pulse" />
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />
      case 'cancelled':
        return <StopCircle className="w-5 h-5 text-gray-500" />
      default:
        return <AlertTriangle className="w-5 h-5 text-orange-500" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Create Job Button */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Training Jobs
        </h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Play className="w-4 h-4" />
          {showCreateForm ? 'Cancel' : 'Create New Job'}
        </button>
      </div>

      {/* Create Job Form */}
      {showCreateForm && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            Create Training Job
          </h4>

          <div className="space-y-4">
            {/* Basic Configuration */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Job Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  placeholder="e.g., my-model-v1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Dataset *
                </label>
                <select
                  value={formData.dataset_id}
                  onChange={(e) => setFormData({ ...formData, dataset_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="">Select Dataset</option>
                  {datasets.filter(d => d.valid).map((dataset) => (
                    <option key={dataset.id} value={dataset.id}>
                      {dataset.name} ({dataset.sample_count} samples)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Base Model *
                </label>
                <select
                  value={formData.base_model}
                  onChange={(e) => setFormData({ ...formData, base_model: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="Qwen/Qwen2.5-7B-Instruct">Qwen 2.5 7B Instruct</option>
                  <option value="meta-llama/Llama-2-7b-hf">Llama 2 7B</option>
                  <option value="mistralai/Mistral-7B-v0.1">Mistral 7B</option>
                  <option value="google/gemma-7b">Gemma 7B</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Fine-Tuning Method *
                </label>
                <select
                  value={formData.finetuning_method}
                  onChange={(e) => setFormData({ ...formData, finetuning_method: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="peft">PEFT (LoRA/QLoRA)</option>
                  <option value="sft">Supervised Fine-Tuning (SFT)</option>
                  <option value="rlhf-ppo">RLHF with PPO</option>
                  <option value="rlhf-grpo">RLHF with GRPO</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Training Objective
                </label>
                <select
                  value={formData.training_objective}
                  onChange={(e) => setFormData({ ...formData, training_objective: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="instruction">Instruction Following</option>
                  <option value="qa">Question Answering</option>
                  <option value="summarization">Summarization</option>
                  <option value="classification">Classification</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Quantization
                </label>
                <select
                  value={formData.quantization}
                  onChange={(e) => setFormData({ ...formData, quantization: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="4bit">4-bit (QLoRA)</option>
                  <option value="8bit">8-bit</option>
                  <option value="none">None (Full Precision)</option>
                </select>
              </div>
            </div>

            {/* Hyperparameter Mode Selection */}
            <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                Hyperparameter Configuration Mode
              </label>
              <div className="flex gap-3">
                <button
                  onClick={() => setHyperparamMode('manual')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                    hyperparamMode === 'manual'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'
                  }`}
                >
                  <Sliders className="w-5 h-5 mx-auto mb-1 text-blue-600 dark:text-blue-400" />
                  <p className="text-sm font-medium text-slate-900 dark:text-white">Manual</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Full control</p>
                </button>
                <button
                  onClick={() => setHyperparamMode('recommended')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                    hyperparamMode === 'recommended'
                      ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-green-400'
                  }`}
                >
                  <TrendingUp className="w-5 h-5 mx-auto mb-1 text-green-600 dark:text-green-400" />
                  <p className="text-sm font-medium text-slate-900 dark:text-white">Recommended</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Heuristic-based</p>
                </button>
                <button
                  onClick={() => setHyperparamMode('auto-tune')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                    hyperparamMode === 'auto-tune'
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-purple-400'
                  }`}
                >
                  <Sparkles className="w-5 h-5 mx-auto mb-1 text-purple-600 dark:text-purple-400" />
                  <p className="text-sm font-medium text-slate-900 dark:text-white">Auto-Tune</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Optuna optimization</p>
                </button>
              </div>
            </div>

            {/* Manual Hyperparameters */}
            {hyperparamMode === 'manual' && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-3">
                  Manual Configuration
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-blue-700 dark:text-blue-300 mb-1">
                      Learning Rate
                    </label>
                    <input
                      type="number"
                      step="0.00001"
                      value={manualHyperparams.learning_rate}
                      onChange={(e) => setManualHyperparams({ ...manualHyperparams, learning_rate: parseFloat(e.target.value) })}
                      className="w-full px-2 py-1 text-sm border border-blue-300 dark:border-blue-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-blue-700 dark:text-blue-300 mb-1">
                      Epochs
                    </label>
                    <input
                      type="number"
                      value={manualHyperparams.num_epochs}
                      onChange={(e) => setManualHyperparams({ ...manualHyperparams, num_epochs: parseInt(e.target.value) })}
                      className="w-full px-2 py-1 text-sm border border-blue-300 dark:border-blue-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-blue-700 dark:text-blue-300 mb-1">
                      Batch Size
                    </label>
                    <select
                      value={manualHyperparams.batch_size}
                      onChange={(e) => setManualHyperparams({ ...manualHyperparams, batch_size: parseInt(e.target.value) })}
                      className="w-full px-2 py-1 text-sm border border-blue-300 dark:border-blue-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="2">2</option>
                      <option value="4">4</option>
                      <option value="8">8</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-blue-700 dark:text-blue-300 mb-1">
                      LoRA Rank (r)
                    </label>
                    <select
                      value={manualHyperparams.lora_r}
                      onChange={(e) => setManualHyperparams({ ...manualHyperparams, lora_r: parseInt(e.target.value) })}
                      className="w-full px-2 py-1 text-sm border border-blue-300 dark:border-blue-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="8">8</option>
                      <option value="16">16</option>
                      <option value="32">32</option>
                      <option value="64">64</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Recommended Mode Info */}
            {hyperparamMode === 'recommended' && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                <p className="text-sm font-medium text-green-900 dark:text-green-100 mb-2">
                  Recommended Configuration
                </p>
                <p className="text-xs text-green-700 dark:text-green-300">
                  Hyperparameters will be automatically selected based on dataset size, model architecture, and available GPU memory using proven heuristics.
                </p>
              </div>
            )}

            {/* Auto-Tune Configuration */}
            {hyperparamMode === 'auto-tune' && (
              <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                <p className="text-sm font-medium text-purple-900 dark:text-purple-100 mb-3">
                  Auto-Tune Configuration (Optuna)
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-purple-700 dark:text-purple-300 mb-1">
                      Number of Trials
                    </label>
                    <input
                      type="number"
                      min="5"
                      max="100"
                      value={autoTuneConfig.n_trials}
                      onChange={(e) => setAutoTuneConfig({ ...autoTuneConfig, n_trials: parseInt(e.target.value) })}
                      className="w-full px-2 py-1 text-sm border border-purple-300 dark:border-purple-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-purple-700 dark:text-purple-300 mb-1">
                      Optimization Metric
                    </label>
                    <select
                      value={autoTuneConfig.optimization_metric}
                      onChange={(e) => setAutoTuneConfig({ ...autoTuneConfig, optimization_metric: e.target.value })}
                      className="w-full px-2 py-1 text-sm border border-purple-300 dark:border-purple-700 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    >
                      <option value="loss">Loss (minimize)</option>
                      <option value="accuracy">Accuracy (maximize)</option>
                      <option value="f1">F1 Score (maximize)</option>
                    </select>
                  </div>
                </div>
                <p className="text-xs text-purple-700 dark:text-purple-300 mt-3">
                  Optuna will automatically search for optimal hyperparameters using Bayesian optimization with TPE sampler and median pruning.
                </p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-2 justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={createJob}
                disabled={!formData.name || !formData.dataset_id}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
              >
                Create Job
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Jobs List */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="divide-y divide-slate-200 dark:divide-slate-700">
          {loading ? (
            <div className="px-6 py-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Play className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-slate-500 dark:text-slate-400">No training jobs yet</p>
            </div>
          ) : (
            jobs.map((job) => (
              <div
                key={job.id}
                className="px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {job.name}
                        </p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {job.base_model}
                          </span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            Method: {job.finetuning_method.toUpperCase()}
                          </span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            Created: {new Date(job.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {job.status === 'running' && (
                          <div className="mt-2">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full transition-all"
                                  style={{ width: `${job.progress_percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-xs text-slate-600 dark:text-slate-400">
                                {job.progress_percentage}%
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                              Step {job.current_step} / {job.total_steps}
                            </p>
                          </div>
                        )}
                        {job.error_message && (
                          <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                            ❌ {job.error_message}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {job.status === 'pending' && (
                      <button
                        onClick={() => submitJob(job.id)}
                        className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                        title="Submit job for training"
                      >
                        Submit
                      </button>
                    )}
                    {job.status === 'running' && (
                      <>
                        <button
                          onClick={() => {
                            setSelectedJob(job)
                            connectWebSocket(job.id)
                          }}
                          className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                          title="View metrics"
                        >
                          Monitor
                        </button>
                        <button
                          onClick={() => cancelJob(job.id)}
                          className="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                          title="Cancel job"
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Metrics Modal */}
      {selectedJob && metrics && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Training Metrics: {selectedJob.name}
                </h3>
                <button
                  onClick={() => {
                    setSelectedJob(null)
                    setMetrics(null)
                    if (wsRef.current) {
                      wsRef.current.close()
                    }
                  }}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6 overflow-y-auto">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Loss</p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {metrics.loss?.toFixed(4) || 'N/A'}
                  </p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Learning Rate</p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {metrics.learning_rate?.toExponential(2) || 'N/A'}
                  </p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                  <p className="text-xs text-slate-500 dark:text-slate-400">GPU Memory</p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {metrics.gpu_memory_used_gb?.toFixed(1) || 'N/A'} GB
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
