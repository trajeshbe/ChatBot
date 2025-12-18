/**
 * GPU Configuration Component
 *
 * Detects available GPUs and provides hardware-aware configuration presets
 * for fine-tuning jobs. Integrates with the GPU capabilities API endpoint.
 */

import { useState, useEffect } from 'react'
import { Cpu, Zap, AlertTriangle, CheckCircle, Info } from 'lucide-react'

interface GPUInfo {
  id: string
  name: string
  memory_total_gb: number
  memory_free_gb: number
  memory_used_gb: number
  utilization_percent: number
  temperature_c: number | null
}

interface GPUPreset {
  name: string
  description: string
  icon: string
  hardware_requirements?: {
    min_gpu_memory_gb: number
    recommended_gpu: string
  }
  hyperparameters: {
    gpu_count: number
    min_gpu_memory_gb: number
    max_memory_gb: number
    batch_size?: number
    gradient_accumulation_steps?: number
    max_seq_length?: number
    lora_rank?: number
    lora_alpha?: number
    optimizer?: string
  }
}

interface GPUCapabilities {
  available: boolean
  gpu_count: number
  gpus?: GPUInfo[]
  total_memory_gb?: number
  safe_memory_gb?: number
  recommended_config: {
    gpu_count: number
    min_gpu_memory_gb: number
    max_memory_gb: number
  }
  presets: Record<string, GPUPreset>
  hardware_summary?: string
  message?: string
  error?: string
}

interface GPUConfigurationProps {
  onPresetSelect?: (preset: GPUPreset) => void
  onCustomConfig?: (config: any) => void
}

export default function GPUConfiguration({ onPresetSelect, onCustomConfig }: GPUConfigurationProps) {
  const [capabilities, setCapabilities] = useState<GPUCapabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchGPUCapabilities()
  }, [])

  const fetchGPUCapabilities = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/finetuning/gpu/capabilities`)

      if (!response.ok) {
        throw new Error(`Failed to fetch GPU capabilities: ${response.statusText}`)
      }

      const data = await response.json()
      setCapabilities(data)

      // Auto-select first available preset
      if (data.presets && Object.keys(data.presets).length > 0) {
        const firstPreset = Object.keys(data.presets)[0]
        setSelectedPreset(firstPreset)
        if (onPresetSelect) {
          onPresetSelect(data.presets[firstPreset])
        }
      }
    } catch (err: any) {
      console.error('Error fetching GPU capabilities:', err)
      setError(err.message || 'Failed to detect GPU capabilities')
    } finally {
      setLoading(false)
    }
  }

  const handlePresetClick = (presetKey: string, preset: GPUPreset) => {
    setSelectedPreset(presetKey)
    if (onPresetSelect) {
      onPresetSelect(preset)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Detecting GPU hardware...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-900">GPU Detection Failed</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={fetchGPUCapabilities}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!capabilities) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* GPU Hardware Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">GPU Hardware</h3>
          <button
            onClick={fetchGPUCapabilities}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Refresh
          </button>
        </div>

        {capabilities.available ? (
          <div className="space-y-4">
            {/* Hardware Summary */}
            <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">
                  {capabilities.hardware_summary || `${capabilities.gpu_count} GPU(s) Detected`}
                </p>
                <p className="text-xs text-green-700 mt-0.5">
                  {capabilities.safe_memory_gb?.toFixed(1)}GB safe memory available
                </p>
              </div>
            </div>

            {/* GPU Details */}
            {capabilities.gpus && capabilities.gpus.length > 0 && (
              <div className="space-y-2">
                {capabilities.gpus.map((gpu) => (
                  <div key={gpu.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <Zap className="w-4 h-4 text-yellow-600" />
                          <span className="font-medium text-gray-900">{gpu.name}</span>
                        </div>
                        <div className="mt-2 space-y-1 text-sm text-gray-600">
                          <div className="flex justify-between">
                            <span>Memory:</span>
                            <span className="font-mono">
                              {gpu.memory_free_gb.toFixed(1)}GB free / {gpu.memory_total_gb.toFixed(1)}GB total
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Utilization:</span>
                            <span className={gpu.utilization_percent > 50 ? 'text-orange-600 font-medium' : ''}>
                              {gpu.utilization_percent}%
                            </span>
                          </div>
                          {gpu.temperature_c !== null && (
                            <div className="flex justify-between">
                              <span>Temperature:</span>
                              <span className={gpu.temperature_c > 80 ? 'text-red-600 font-medium' : ''}>
                                {gpu.temperature_c}°C
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-start space-x-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <Cpu className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-900">No GPU Detected</p>
              <p className="text-xs text-yellow-700 mt-1">
                {capabilities.message || 'Training will use CPU (very slow)'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Hardware-Aware Presets */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Configuration Presets</h3>
          <div className="group relative">
            <Info className="w-4 h-4 text-gray-400 cursor-help" />
            <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-10">
              These presets are automatically configured based on your detected GPU hardware
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(capabilities.presets).map(([key, preset]) => (
            <button
              key={key}
              onClick={() => handlePresetClick(key, preset)}
              className={`
                p-4 rounded-lg border-2 text-left transition-all
                ${selectedPreset === key
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }
              `}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{preset.icon}</span>
                  <h4 className="font-semibold text-gray-900">{preset.name}</h4>
                </div>
                {selectedPreset === key && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </div>

              <p className="text-sm text-gray-600 mb-3">{preset.description}</p>

              {preset.hardware_requirements && (
                <div className="text-xs text-gray-500 mb-2">
                  <div>Min GPU: {preset.hardware_requirements.min_gpu_memory_gb}GB</div>
                  {preset.hardware_requirements.recommended_gpu && (
                    <div className="truncate">{preset.hardware_requirements.recommended_gpu}</div>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-1 mt-2">
                {preset.hyperparameters.batch_size && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                    Batch: {preset.hyperparameters.batch_size}
                  </span>
                )}
                {preset.hyperparameters.lora_rank && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                    LoRA: {preset.hyperparameters.lora_rank}
                  </span>
                )}
                {preset.hyperparameters.max_seq_length && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                    Seq: {preset.hyperparameters.max_seq_length}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>

        {Object.keys(capabilities.presets).length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">
            No presets available for current hardware configuration
          </p>
        )}
      </div>
    </div>
  )
}
