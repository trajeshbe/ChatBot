/**
 * Fine-Tuning Manager Component
 *
 * Main component for managing model fine-tuning with tabs for:
 * - Datasets
 * - Training Jobs
 * - Fine-Tuned Models
 * - GPU Monitor
 */

import { useState, useEffect } from 'react'
import { Database, Play, Cpu, Package, Upload, Eye, Trash2, Settings, Activity, TrendingUp, Zap } from 'lucide-react'
import DatasetManager from './DatasetManager'
import JobManager from './JobManager'
import ModelManager from './ModelManager'
import GPUMonitor from './GPUMonitor'

type FineTuningTab = 'datasets' | 'jobs' | 'models' | 'gpu'

interface FineTuningStats {
  total_datasets: number
  total_jobs: number
  running_jobs: number
  completed_jobs: number
  total_models: number
  deployed_models: number
  gpu_available: number
  gpu_in_use: number
}

export default function FineTuningManager() {
  const [activeTab, setActiveTab] = useState<FineTuningTab>('datasets')
  const [stats, setStats] = useState<FineTuningStats | null>(null)
  const [loading, setLoading] = useState(true)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/stats`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Error loading fine-tuning stats:', error)
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Settings className="w-6 h-6" />
              Model Fine-Tuning
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Train and deploy custom fine-tuned models
            </p>
          </div>
          <button
            onClick={loadStats}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">Datasets</p>
                  <p className="text-2xl font-bold text-blue-900 dark:text-blue-100 mt-1">
                    {stats.total_datasets}
                  </p>
                </div>
                <Database className="w-8 h-8 text-blue-500 opacity-50" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-700 dark:text-green-300 font-medium">Running Jobs</p>
                  <p className="text-2xl font-bold text-green-900 dark:text-green-100 mt-1">
                    {stats.running_jobs}
                    <span className="text-sm text-green-600 dark:text-green-400 ml-1">
                      / {stats.total_jobs}
                    </span>
                  </p>
                </div>
                <Play className="w-8 h-8 text-green-500 opacity-50" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-700 dark:text-purple-300 font-medium">Models</p>
                  <p className="text-2xl font-bold text-purple-900 dark:text-purple-100 mt-1">
                    {stats.total_models}
                    <span className="text-sm text-purple-600 dark:text-purple-400 ml-1">
                      ({stats.deployed_models} deployed)
                    </span>
                  </p>
                </div>
                <Package className="w-8 h-8 text-purple-500 opacity-50" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-700 dark:text-orange-300 font-medium">GPUs</p>
                  <p className="text-2xl font-bold text-orange-900 dark:text-orange-100 mt-1">
                    {stats.gpu_in_use}
                    <span className="text-sm text-orange-600 dark:text-orange-400 ml-1">
                      / {stats.gpu_available}
                    </span>
                  </p>
                </div>
                <Cpu className="w-8 h-8 text-orange-500 opacity-50" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="border-b border-slate-200 dark:border-slate-700">
          <div className="px-6">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab('datasets')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'datasets'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Database className="w-4 h-4" />
                  <span>Datasets</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('jobs')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'jobs'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Play className="w-4 h-4" />
                  <span>Training Jobs</span>
                  {stats && stats.running_jobs > 0 && (
                    <span className="px-2 py-0.5 bg-green-500 text-white text-xs rounded-full">
                      {stats.running_jobs}
                    </span>
                  )}
                </div>
              </button>
              <button
                onClick={() => setActiveTab('models')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'models'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Package className="w-4 h-4" />
                  <span>Models</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('gpu')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'gpu'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4" />
                  <span>GPU Monitor</span>
                  {stats && stats.gpu_in_use > 0 && (
                    <span className="px-2 py-0.5 bg-orange-500 text-white text-xs rounded-full">
                      {stats.gpu_in_use}
                    </span>
                  )}
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {activeTab === 'datasets' && <DatasetManager onRefresh={loadStats} />}
              {activeTab === 'jobs' && <JobManager onRefresh={loadStats} />}
              {activeTab === 'models' && <ModelManager onRefresh={loadStats} />}
              {activeTab === 'gpu' && <GPUMonitor />}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
