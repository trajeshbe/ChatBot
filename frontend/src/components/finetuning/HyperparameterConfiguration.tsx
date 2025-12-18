/**
 * Hyperparameter Configuration Component
 *
 * Dynamically generates sliders, dropdowns, and controls based on YAML configuration.
 * Supports presets, validation rules, and method-specific parameter filtering.
 */

import { useState, useEffect } from 'react'
import { Sliders, Info, AlertTriangle, CheckCircle, RotateCcw } from 'lucide-react'

interface HyperparameterConfig {
  type: 'integer' | 'float' | 'string' | 'boolean'
  default: any
  min?: number
  max?: number
  step?: number
  description: string
  tooltip?: string
  ui_type: 'slider' | 'dropdown' | 'checkbox' | 'text'
  display_format?: 'scientific' | 'percentage' | 'decimal'
  options?: string[]
  applicable_to?: string[]
  validation?: {
    warning_threshold?: number
    error_threshold?: number
    requires?: string[]
  }
}

interface HyperparameterPreset {
  name: string
  description: string
  icon?: string
  hardware_requirements?: {
    min_gpu_memory_gb: number
    recommended_gpu: string
  }
  hyperparameters: Record<string, any>
}

interface HyperparameterConfigResponse {
  hyperparameters: Record<string, HyperparameterConfig>
  presets: Record<string, HyperparameterPreset>
  validation?: Record<string, any>
  version: string
  updated?: string
}

interface HyperparameterConfigurationProps {
  finetuningMethod: string
  onConfigChange?: (config: Record<string, any>) => void
  onPresetSelect?: (presetKey: string, preset: HyperparameterPreset) => void
}

export default function HyperparameterConfiguration({
  finetuningMethod,
  onConfigChange,
  onPresetSelect
}: HyperparameterConfigurationProps) {
  const [config, setConfig] = useState<HyperparameterConfigResponse | null>(null)
  const [values, setValues] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)
  const [validationWarnings, setValidationWarnings] = useState<Record<string, string>>({})

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchConfiguration()
  }, [])

  useEffect(() => {
    if (config) {
      loadDefaults()
    }
  }, [finetuningMethod, config])

  useEffect(() => {
    if (onConfigChange) {
      onConfigChange(values)
    }
    validateConfiguration()
  }, [values])

  const fetchConfiguration = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/finetuning/hyperparameters/config`)

      if (!response.ok) {
        throw new Error(`Failed to fetch hyperparameter configuration: ${response.statusText}`)
      }

      const data = await response.json()
      setConfig(data)
    } catch (err: any) {
      console.error('Error fetching hyperparameter configuration:', err)
      setError(err.message || 'Failed to load hyperparameter configuration')
    } finally {
      setLoading(false)
    }
  }

  const loadDefaults = async () => {
    if (!config) return

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/finetuning/hyperparameters/defaults?finetuning_method=${finetuningMethod}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch defaults')
      }

      const data = await response.json()
      setValues(data.defaults || {})
    } catch (err: any) {
      console.error('Error loading defaults:', err)
      // Fallback to config defaults
      const defaults: Record<string, any> = {}
      Object.entries(config.hyperparameters).forEach(([key, param]) => {
        if (!param.applicable_to || param.applicable_to.includes(finetuningMethod)) {
          defaults[key] = param.default
        }
      })
      setValues(defaults)
    }
  }

  const validateConfiguration = () => {
    if (!config) return

    const warnings: Record<string, string> = {}

    Object.entries(values).forEach(([key, value]) => {
      const param = config.hyperparameters[key]
      if (!param?.validation) return

      // Check warning threshold
      if (param.validation.warning_threshold !== undefined) {
        if (typeof value === 'number' && value > param.validation.warning_threshold) {
          warnings[key] = `Value exceeds recommended threshold of ${param.validation.warning_threshold}`
        }
      }

      // Check error threshold
      if (param.validation.error_threshold !== undefined) {
        if (typeof value === 'number' && value > param.validation.error_threshold) {
          warnings[key] = `⚠️ Value exceeds maximum safe threshold of ${param.validation.error_threshold}`
        }
      }
    })

    setValidationWarnings(warnings)
  }

  const handleValueChange = (key: string, value: any) => {
    setValues(prev => ({ ...prev, [key]: value }))
  }

  const handlePresetClick = (presetKey: string, preset: HyperparameterPreset) => {
    setSelectedPreset(presetKey)
    setValues({ ...values, ...preset.hyperparameters })

    if (onPresetSelect) {
      onPresetSelect(presetKey, preset)
    }
  }

  const handleResetToDefaults = () => {
    setSelectedPreset(null)
    loadDefaults()
  }

  const formatValue = (value: number, format?: string): string => {
    if (format === 'scientific') {
      return value.toExponential(1)
    } else if (format === 'percentage') {
      return `${(value * 100).toFixed(1)}%`
    } else if (format === 'decimal') {
      return value.toFixed(4)
    }
    return String(value)
  }

  const renderControl = (key: string, param: HyperparameterConfig) => {
    const value = values[key] ?? param.default

    switch (param.ui_type) {
      case 'slider':
        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">{param.description}</label>
              <span className="text-sm font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
                {formatValue(value, param.display_format)}
              </span>
            </div>

            <input
              type="range"
              min={param.min}
              max={param.max}
              step={param.step}
              value={value}
              onChange={(e) => handleValueChange(key, param.type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
            />

            <div className="flex justify-between text-xs text-gray-500">
              <span>{formatValue(param.min!, param.display_format)}</span>
              <span>{formatValue(param.max!, param.display_format)}</span>
            </div>

            {param.tooltip && (
              <p className="text-xs text-gray-500 flex items-start gap-1">
                <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <span>{param.tooltip}</span>
              </p>
            )}

            {validationWarnings[key] && (
              <div className="flex items-start gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                <AlertTriangle className="w-3 h-3 text-yellow-600 mt-0.5 flex-shrink-0" />
                <span className="text-yellow-800">{validationWarnings[key]}</span>
              </div>
            )}
          </div>
        )

      case 'dropdown':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">{param.description}</label>
            <select
              value={value}
              onChange={(e) => handleValueChange(key, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {param.options?.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {param.tooltip && (
              <p className="text-xs text-gray-500">{param.tooltip}</p>
            )}
          </div>
        )

      case 'checkbox':
        return (
          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleValueChange(key, e.target.checked)}
              className="mt-1 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <div className="flex-1">
              <label className="text-sm font-medium text-gray-700">{param.description}</label>
              {param.tooltip && (
                <p className="text-xs text-gray-500 mt-1">{param.tooltip}</p>
              )}
            </div>
          </div>
        )

      case 'text':
        return (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">{param.description}</label>
            <input
              type="text"
              value={value}
              onChange={(e) => handleValueChange(key, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {param.tooltip && (
              <p className="text-xs text-gray-500">{param.tooltip}</p>
            )}
          </div>
        )

      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Loading hyperparameter configuration...</span>
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
            <h3 className="font-medium text-red-900">Configuration Load Failed</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={fetchConfiguration}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!config) {
    return null
  }

  // Filter parameters applicable to current method
  const applicableParams = Object.entries(config.hyperparameters).filter(([key, param]) => {
    return !param.applicable_to || param.applicable_to.includes(finetuningMethod)
  })

  return (
    <div className="space-y-6">
      {/* Presets Section */}
      {Object.keys(config.presets).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Sliders className="w-5 h-5 text-gray-700" />
              <h3 className="text-lg font-semibold text-gray-900">Hyperparameter Presets</h3>
            </div>
            {selectedPreset && (
              <button
                onClick={handleResetToDefaults}
                className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Reset to Defaults</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(config.presets).map(([key, preset]) => (
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
                    {preset.icon && <span className="text-2xl">{preset.icon}</span>}
                    <h4 className="font-semibold text-gray-900">{preset.name}</h4>
                  </div>
                  {selectedPreset === key && (
                    <CheckCircle className="w-5 h-5 text-blue-600" />
                  )}
                </div>
                <p className="text-sm text-gray-600">{preset.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Hyperparameter Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Sliders className="w-5 h-5 text-gray-700" />
          <h3 className="text-lg font-semibold text-gray-900">
            Hyperparameters ({finetuningMethod})
          </h3>
        </div>

        <div className="space-y-6">
          {applicableParams.map(([key, param]) => (
            <div key={key} className="pb-4 border-b border-gray-200 last:border-b-0 last:pb-0">
              {renderControl(key, param)}
            </div>
          ))}
        </div>

        {applicableParams.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">
            No hyperparameters available for {finetuningMethod} method
          </p>
        )}
      </div>

      {/* Configuration Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium">Configuration Version: {config.version}</p>
            {config.updated && (
              <p className="text-blue-700 mt-1">Last updated: {config.updated}</p>
            )}
            <p className="text-blue-700 mt-2">
              Adjust hyperparameters using the sliders above, or select a preset for optimized defaults.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
