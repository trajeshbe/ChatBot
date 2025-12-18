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
import ProjectSelector from '../ProjectSelector'
import GPUConfiguration from './GPUConfiguration'
import HyperparameterConfiguration from './HyperparameterConfiguration'

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

  // Project selection
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [currentUser, setCurrentUser] = useState<any>(null)

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null)

  // Job details view
  const [jobDetailsView, setJobDetailsView] = useState<any | null>(null)

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

  // GPU and Hyperparameter configuration from new components
  const [selectedGPUPreset, setSelectedGPUPreset] = useState<any>(null)
  const [hyperparameterConfig, setHyperparameterConfig] = useState<any>({})

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadJobs()
    loadDatasets()
    // Load current user
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setCurrentUser(JSON.parse(userStr))
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
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
      const token = localStorage.getItem('access_token')
      if (!token) {
        console.error('No authentication token found. Please log in.')
        alert('⚠️ Authentication required. Please log in to access fine-tuning features.')
        return
      }

      const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      if (response.status === 401) {
        console.error('Unauthorized: Invalid or expired token')
        alert('⚠️ Session expired. Please log in again.')
        return
      }

      if (response.ok) {
        const data = await response.json()
        console.log('Datasets loaded:', data.datasets?.length || 0)
        setDatasets(data.datasets || [])
      } else {
        console.error(`Failed to load datasets: ${response.status} ${response.statusText}`)
      }
    } catch (error) {
      console.error('Error loading datasets:', error)
      alert('❌ Error loading datasets. Check console for details.')
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
      // Validate required fields before submitting
      if (!formData.name || formData.name.trim() === '') {
        alert('❌ Job name is required')
        return
      }

      if (!formData.dataset_id) {
        alert('❌ Please select a dataset')
        return
      }

      if (!formData.base_model) {
        alert('❌ Please select a base model')
        return
      }

      const token = localStorage.getItem('access_token')

      // Default hyperparameters based on method
      const getDefaultHyperparameters = (method: string) => {
        if (method === 'peft') {
          return {
            learning_rate: 0.0002,
            num_epochs: 3,
            batch_size: 4,
            gradient_accumulation_steps: 4,
            warmup_steps: 100,
            lora_r: 16,
            lora_alpha: 32,
            lora_dropout: 0.05
          }
        } else if (method === 'sft') {
          return {
            learning_rate: 0.0001,
            num_epochs: 3,
            batch_size: 4,
            gradient_accumulation_steps: 4,
            warmup_steps: 100
          }
        } else {
          // rlhf-ppo or rlhf-grpo
          return {
            learning_rate: 0.00005,
            num_epochs: 2,
            batch_size: 4,
            gradient_accumulation_steps: 4,
            warmup_steps: 50,
            ppo_epochs: 4
          }
        }
      }

      // Start with default hyperparameters for the selected method
      let hyperparameters = getDefaultHyperparameters(formData.finetuning_method)

      if (hyperparamMode === 'manual') {
        // Use hyperparameters from the new HyperparameterConfiguration component
        hyperparameters = Object.keys(hyperparameterConfig).length > 0
          ? hyperparameterConfig
          : manualHyperparams // Fallback to legacy if component hasn't loaded
      } else if (hyperparamMode === 'recommended') {
        // Try to get recommended hyperparameters from backend
        try {
          const dataset = datasets.find(d => d.id === formData.dataset_id)
          const datasetSize = dataset?.sample_count || 1000

          const recommendResponse = await fetch(
            `${API_BASE}/api/v1/finetuning/hyperparameters/recommend`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {})
              },
              body: JSON.stringify({
                finetuning_method: formData.finetuning_method,
                dataset_size: datasetSize,
                available_memory_gb: 24, // TODO: Get from GPU monitor
              })
            }
          )
          if (recommendResponse.ok) {
            const recommended = await recommendResponse.json()
            hyperparameters = recommended
            console.log('✅ Using recommended hyperparameters:', recommended)
          } else if (recommendResponse.status === 404) {
            console.warn('⚠️  Hyperparameter recommendation endpoint not found, using defaults')
          } else {
            console.warn('⚠️  Failed to get recommended hyperparameters, using defaults')
          }
        } catch (error) {
          console.warn('⚠️  Error fetching recommended hyperparameters, using defaults:', error)
        }
      } else if (hyperparamMode === 'auto-tune') {
        // Auto-tune mode - backend will run Optuna
        hyperparameters = {
          auto_tune: true,
          ...autoTuneConfig,
        }
      }

      console.log('Creating job with hyperparameters:', hyperparameters)

      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
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
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/submit`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {}
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
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {}
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
                  {datasets.map((dataset) => (
                    <option key={dataset.id} value={dataset.id}>
                      {dataset.name} ({dataset.num_samples !== null && dataset.num_samples !== undefined ? dataset.num_samples : 'pending'} samples)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Project Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Project (Optional)
              </label>
              <ProjectSelector
                value={selectedProjectId}
                onChange={(projectId) => setSelectedProjectId(projectId)}
                currentUser={currentUser}
                placeholder="Select project or leave blank for global..."
              />
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Datasets and checkpoints will be organized by project
              </p>
            </div>

            {/* Model Configuration */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Base Model *
                </label>
                <select
                  value={formData.base_model}
                  onChange={(e) => setFormData({ ...formData, base_model: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                >
                  <option value="Qwen/Qwen2.5-1.5B-Instruct">Qwen 2.5 1.5B Instruct (Lightweight)</option>
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

            {/* GPU Configuration (for all modes) */}
            <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
              <GPUConfiguration
                onPresetSelect={(preset) => {
                  setSelectedGPUPreset(preset)
                  console.log('GPU preset selected:', preset)
                }}
                onCustomConfig={(config) => {
                  console.log('Custom GPU config:', config)
                }}
              />
            </div>

            {/* Manual Hyperparameters */}
            {hyperparamMode === 'manual' && (
              <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
                <HyperparameterConfiguration
                  finetuningMethod={formData.finetuning_method.toUpperCase()}
                  onConfigChange={(config) => {
                    setHyperparameterConfig(config)
                    console.log('Hyperparameter config updated:', config)
                  }}
                  onPresetSelect={(presetKey, preset) => {
                    console.log('Hyperparameter preset selected:', presetKey, preset)
                  }}
                />
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
                    {/* View Details button - available for all statuses */}
                    <button
                      onClick={() => setJobDetailsView(job)}
                      className="px-3 py-1.5 bg-slate-600 text-white text-sm rounded hover:bg-slate-700 transition-colors"
                      title="View job details"
                    >
                      Details
                    </button>

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

      {/* Job Details Modal */}
      {jobDetailsView && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Job Details: {jobDetailsView.name}
                </h3>
                <button
                  onClick={() => setJobDetailsView(null)}
                  className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* Job Info */}
              <div className="space-y-6">
                {/* Status & Basic Info */}
                <div>
                  <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-3">Status</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                      <p className="text-xs text-slate-500 dark:text-slate-400">Current Status</p>
                      <p className="text-lg font-bold text-slate-900 dark:text-white capitalize">
                        {jobDetailsView.status}
                      </p>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                      <p className="text-xs text-slate-500 dark:text-slate-400">Progress</p>
                      <p className="text-lg font-bold text-slate-900 dark:text-white">
                        {jobDetailsView.progress_percentage || 0}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Model Configuration */}
                <div>
                  <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-3">Model Configuration</h4>
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Base Model:</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">{jobDetailsView.base_model}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Method:</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">{jobDetailsView.finetuning_method.toUpperCase()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Objective:</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">{jobDetailsView.training_objective}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Quantization:</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">{jobDetailsView.quantization || 'None'}</span>
                    </div>
                  </div>
                </div>

                {/* Hyperparameters */}
                <div>
                  <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-3">Hyperparameters</h4>
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                    <pre className="text-xs text-slate-700 dark:text-slate-300 overflow-x-auto">
                      {JSON.stringify(jobDetailsView.hyperparameters, null, 2)}
                    </pre>
                  </div>
                </div>

                {/* Training Progress (if running or completed) */}
                {(jobDetailsView.status === 'running' || jobDetailsView.status === 'completed') && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-3">Training Progress</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {jobDetailsView.current_epoch !== null && (
                        <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                          <p className="text-xs text-slate-500 dark:text-slate-400">Current Epoch</p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white">
                            {jobDetailsView.current_epoch}
                          </p>
                        </div>
                      )}
                      {jobDetailsView.current_step !== null && (
                        <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                          <p className="text-xs text-slate-500 dark:text-slate-400">Steps</p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white">
                            {jobDetailsView.current_step} / {jobDetailsView.total_steps}
                          </p>
                        </div>
                      )}
                      {jobDetailsView.train_loss !== null && (
                        <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                          <p className="text-xs text-slate-500 dark:text-slate-400">Training Loss</p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white">
                            {jobDetailsView.train_loss?.toFixed(4)}
                          </p>
                        </div>
                      )}
                      {jobDetailsView.eval_loss !== null && (
                        <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4">
                          <p className="text-xs text-slate-500 dark:text-slate-400">Eval Loss</p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white">
                            {jobDetailsView.eval_loss?.toFixed(4)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Error Message (if failed) */}
                {jobDetailsView.error_message && (
                  <div>
                    <h4 className="text-sm font-medium text-red-600 dark:text-red-400 mb-3">Error Message</h4>
                    <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                      <p className="text-sm text-red-700 dark:text-red-300">
                        {jobDetailsView.error_message}
                      </p>
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                <div>
                  <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-3">Timestamps</h4>
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Created:</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        {new Date(jobDetailsView.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Last Updated:</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        {new Date(jobDetailsView.updated_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end">
              <button
                onClick={() => setJobDetailsView(null)}
                className="px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
