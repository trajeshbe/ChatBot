/**
 * Training Pipeline Visualizer
 *
 * Visual representation of the training pipeline with hover tooltips showing:
 * - Preprocessing logs (auto-detection, column mapping, dataset statistics)
 * - Training progress (epochs, steps, loss)
 * - Real-time stage updates
 */

import { useState, useEffect } from 'react'
import { CheckCircle, Clock, Loader, XCircle, ChevronRight, Database, Settings, Zap, FileCheck } from 'lucide-react'

interface PipelineStage {
  id: string
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  icon: any
  details?: string[]
}

interface PreprocessingHighlight {
  type: string
  message: string
  data?: any
}

interface TrainingPipelineVisualizerProps {
  jobId: string
  jobStatus: string
  onRefresh?: () => void
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function TrainingPipelineVisualizer({ jobId, jobStatus, onRefresh }: TrainingPipelineVisualizerProps) {
  const [logs, setLogs] = useState<any>(null)
  const [hoveredStage, setHoveredStage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Define pipeline stages
  const stages: PipelineStage[] = [
    {
      id: 'queued',
      name: 'Queued',
      status: ['pending', 'queued'].includes(jobStatus) ? 'in_progress' : 'completed',
      icon: Clock,
      details: ['Job submitted to queue', 'Waiting for GPU allocation']
    },
    {
      id: 'preprocessing',
      name: 'Preprocessing',
      status: jobStatus === 'running' ? 'in_progress' : jobStatus === 'completed' ? 'completed' : 'pending',
      icon: Database,
      details: logs?.preprocessing_highlights?.length > 0
        ? logs.preprocessing_highlights.map((h: PreprocessingHighlight) => h.message)
        : ['Dataset download', 'Auto-detect format', 'Column mapping', 'Create train/val split']
    },
    {
      id: 'training',
      name: 'Training',
      status: jobStatus === 'running' ? 'in_progress' : jobStatus === 'completed' ? 'completed' : 'pending',
      icon: Zap,
      details: ['Load base model', 'Apply LoRA adapters', 'Training epochs', 'Save checkpoints']
    },
    {
      id: 'evaluation',
      name: 'Evaluation',
      status: jobStatus === 'completed' ? 'completed' : 'pending',
      icon: FileCheck,
      details: ['Validation metrics', 'TensorBoard logs', 'Save final model']
    }
  ]

  // Fetch logs on mount and when job status changes
  useEffect(() => {
    if (jobId && jobStatus !== 'pending') {
      fetchLogs()
    }
  }, [jobId, jobStatus])

  // Auto-refresh logs for running jobs
  useEffect(() => {
    if (jobStatus === 'running') {
      const interval = setInterval(fetchLogs, 5000) // Refresh every 5 seconds
      return () => clearInterval(interval)
    }
  }, [jobStatus])

  const fetchLogs = async () => {
    if (loading) return

    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/logs?lines=50`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      if (response.ok) {
        const data = await response.json()
        setLogs(data)
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStageIcon = (stage: PipelineStage) => {
    const IconComponent = stage.icon

    if (stage.status === 'completed') {
      return <CheckCircle className="w-6 h-6 text-green-500" />
    } else if (stage.status === 'in_progress') {
      return <Loader className="w-6 h-6 text-blue-500 animate-spin" />
    } else if (stage.status === 'failed') {
      return <XCircle className="w-6 h-6 text-red-500" />
    } else {
      return <IconComponent className="w-6 h-6 text-slate-400" />
    }
  }

  const getStageColor = (stage: PipelineStage) => {
    if (stage.status === 'completed') return 'border-green-500 bg-green-50 dark:bg-green-900/20'
    if (stage.status === 'in_progress') return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
    if (stage.status === 'failed') return 'border-red-500 bg-red-50 dark:bg-red-900/20'
    return 'border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800'
  }

  return (
    <div className="space-y-4">
      {/* Pipeline Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
          Training Pipeline
        </h4>
        {loading && (
          <Loader className="w-4 h-4 text-blue-500 animate-spin" />
        )}
      </div>

      {/* Pipeline Stages */}
      <div className="relative">
        <div className="flex items-center gap-2">
          {stages.map((stage, index) => (
            <div key={stage.id} className="flex items-center flex-1">
              {/* Stage Card */}
              <div
                className={`relative flex-1 border-2 rounded-lg p-3 transition-all cursor-pointer ${getStageColor(stage)} ${
                  hoveredStage === stage.id ? 'shadow-lg scale-105' : ''
                }`}
                onMouseEnter={() => setHoveredStage(stage.id)}
                onMouseLeave={() => setHoveredStage(null)}
              >
                <div className="flex items-center gap-2">
                  {getStageIcon(stage)}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {stage.name}
                    </p>
                    {stage.status === 'in_progress' && (
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                        In progress...
                      </p>
                    )}
                  </div>
                </div>

                {/* Hover Tooltip */}
                {hoveredStage === stage.id && stage.details && stage.details.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl z-10 max-h-64 overflow-y-auto">
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                      {stage.name} Details:
                    </p>
                    <div className="space-y-1">
                      {stage.details.map((detail, idx) => (
                        <div
                          key={idx}
                          className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2"
                        >
                          {stage.id === 'preprocessing' && logs?.preprocessing_highlights?.[idx] ? (
                            <>
                              {getHighlightIcon(logs.preprocessing_highlights[idx].type)}
                              <span className="flex-1 font-mono text-xs">{detail}</span>
                            </>
                          ) : (
                            <>
                              <span className="text-slate-400">•</span>
                              <span className="flex-1">{detail}</span>
                            </>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Show live logs preview for active stage */}
                    {stage.status === 'in_progress' && logs?.logs && (
                      <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                          Live Logs:
                        </p>
                        <div className="space-y-1 max-h-32 overflow-y-auto">
                          {logs.logs
                            .filter((log: any) =>
                              stage.id === 'preprocessing'
                                ? log.source === 'celery'
                                : log.source === 'training'
                            )
                            .slice(-5)
                            .map((log: any, idx: number) => (
                              <div key={idx} className="text-xs font-mono text-slate-600 dark:text-slate-400">
                                {log.line.substring(0, 100)}
                                {log.line.length > 100 && '...'}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Arrow between stages */}
              {index < stages.length - 1 && (
                <ChevronRight className="w-5 h-5 text-slate-400 mx-1 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="mt-4 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{
              width: `${(stages.filter(s => s.status === 'completed').length / stages.length) * 100}%`
            }}
          />
        </div>
      </div>

      {/* Preprocessing Highlights Summary (Always Visible) */}
      {logs?.preprocessing_highlights && logs.preprocessing_highlights.length > 0 && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
          <p className="text-sm font-semibold text-green-900 dark:text-green-100 mb-2">
            ✅ Preprocessing Complete
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {logs.preprocessing_highlights
              .filter((h: PreprocessingHighlight) =>
                ['samples_loaded', 'objective_detected', 'train_saved', 'validation_saved'].includes(h.type)
              )
              .map((highlight: PreprocessingHighlight, idx: number) => (
                <div key={idx} className="text-green-700 dark:text-green-300 font-mono">
                  {highlight.message.replace(/.*?(📊|📝|✅)/, '$1')}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to get icon for preprocessing highlights
function getHighlightIcon(type: string) {
  const icons: Record<string, string> = {
    dataset_download: '📦',
    preprocessing_start: '🔄',
    samples_loaded: '📊',
    objective_detected: '📝',
    auto_detection: '🔍',
    column_mapping: '✅',
    fallback_mapping: '✅',
    train_saved: '✅',
    validation_saved: '✅'
  }
  return <span className="text-base">{icons[type] || '•'}</span>
}
