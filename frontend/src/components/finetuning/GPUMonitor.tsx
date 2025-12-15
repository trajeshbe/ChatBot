/**
 * GPU Monitor Component
 *
 * Monitor GPU resources with:
 * - Real-time GPU utilization and memory
 * - Embedded Grafana dashboard
 * - GPU allocation status
 */

import { useState, useEffect, useRef } from 'react'
import { Cpu, Activity, Zap, HardDrive, TrendingUp, RefreshCw } from 'lucide-react'

interface GPUInfo {
  id: string
  name: string
  uuid: string
  memory_total_mb: number
  memory_used_mb: number
  memory_free_mb: number
  memory_utilization_percent: number
  gpu_utilization_percent: number
  temperature_c: number
  power_draw_w: number
  power_limit_w: number
  allocated_to_job: string | null
  allocated_to_job_name: string | null
}

interface GPUStats {
  total_gpus: number
  available_gpus: number
  allocated_gpus: number
  total_memory_gb: number
  used_memory_gb: number
  average_utilization: number
  gpus: GPUInfo[]
}

export default function GPUMonitor() {
  const [stats, setStats] = useState<GPUStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const GRAFANA_URL = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3000'

  useEffect(() => {
    loadGPUStats()

    if (autoRefresh) {
      connectWebSocket()
      return () => {
        if (wsRef.current) {
          wsRef.current.close()
        }
      }
    }
  }, [autoRefresh])

  const loadGPUStats = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/gpu/status`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Error loading GPU stats:', error)
    }
    setLoading(false)
  }

  const connectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const wsUrl = `${API_BASE.replace('http', 'ws')}/api/v1/finetuning/ws/gpu/status`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('GPU monitor WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'gpu_status') {
        setStats(data.data)
      }
    }

    ws.onerror = (error) => {
      console.error('GPU monitor WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('GPU monitor WebSocket closed')
    }

    wsRef.current = ws
  }

  const getUtilizationColor = (percent: number) => {
    if (percent < 30) return 'text-green-600 dark:text-green-400'
    if (percent < 70) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getUtilizationBgColor = (percent: number) => {
    if (percent < 30) return 'bg-green-500'
    if (percent < 70) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          GPU Monitor
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              autoRefresh
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
            }`}
          >
            {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </button>
          <button
            onClick={loadGPUStats}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">Total GPUs</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100 mt-1">
                  {stats.total_gpus}
                </p>
              </div>
              <Cpu className="w-8 h-8 text-blue-500 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 dark:text-green-300 font-medium">Available</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100 mt-1">
                  {stats.available_gpus}
                </p>
              </div>
              <Zap className="w-8 h-8 text-green-500 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700 dark:text-purple-300 font-medium">Avg Utilization</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100 mt-1">
                  {stats.average_utilization.toFixed(1)}%
                </p>
              </div>
              <Activity className="w-8 h-8 text-purple-500 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-700 dark:text-orange-300 font-medium">Memory Used</p>
                <p className="text-2xl font-bold text-orange-900 dark:text-orange-100 mt-1">
                  {stats.used_memory_gb.toFixed(1)} GB
                </p>
                <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                  / {stats.total_memory_gb.toFixed(1)} GB
                </p>
              </div>
              <HardDrive className="w-8 h-8 text-orange-500 opacity-50" />
            </div>
          </div>
        </div>
      )}

      {/* GPU Cards */}
      {loading ? (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      ) : stats && stats.gpus.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stats.gpus.map((gpu) => (
            <div
              key={gpu.id}
              className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6"
            >
              {/* GPU Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white">
                    GPU {gpu.id}
                  </h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    {gpu.name}
                  </p>
                  <p className="text-xs font-mono text-slate-400 dark:text-slate-500 mt-1">
                    {gpu.uuid.slice(0, 16)}...
                  </p>
                </div>
                {gpu.allocated_to_job ? (
                  <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs rounded-full">
                    Allocated
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                    Available
                  </span>
                )}
              </div>

              {/* GPU Utilization */}
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-600 dark:text-slate-400">GPU Utilization</span>
                    <span className={`font-semibold ${getUtilizationColor(gpu.gpu_utilization_percent)}`}>
                      {gpu.gpu_utilization_percent}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${getUtilizationBgColor(gpu.gpu_utilization_percent)}`}
                      style={{ width: `${gpu.gpu_utilization_percent}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-600 dark:text-slate-400">Memory</span>
                    <span className={`font-semibold ${getUtilizationColor(gpu.memory_utilization_percent)}`}>
                      {gpu.memory_used_mb} / {gpu.memory_total_mb} MB ({gpu.memory_utilization_percent}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${getUtilizationBgColor(gpu.memory_utilization_percent)}`}
                      style={{ width: `${gpu.memory_utilization_percent}%` }}
                    ></div>
                  </div>
                </div>

                {/* Additional Info */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Temperature</p>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {gpu.temperature_c}°C
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Power</p>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {gpu.power_draw_w}W / {gpu.power_limit_w}W
                    </p>
                  </div>
                </div>

                {gpu.allocated_to_job_name && (
                  <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Allocated to Job</p>
                    <p className="text-sm font-medium text-orange-600 dark:text-orange-400">
                      {gpu.allocated_to_job_name}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-12 text-center">
          <Cpu className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
          <p className="text-slate-500 dark:text-slate-400">No GPUs detected</p>
        </div>
      )}

      {/* Grafana Dashboard Embed */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-semibold text-slate-900 dark:text-white">
              GPU Metrics Dashboard
            </h4>
            <a
              href={`${GRAFANA_URL}/d/gpu-finetuning`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <TrendingUp className="w-4 h-4" />
              Open in Grafana
            </a>
          </div>
        </div>
        <div className="p-6">
          <iframe
            src={`${GRAFANA_URL}/d-solo/gpu-finetuning/gpu-monitoring?orgId=1&theme=light&panelId=1`}
            width="100%"
            height="400"
            frameBorder="0"
            className="rounded-lg"
          ></iframe>
        </div>
      </div>
    </div>
  )
}
