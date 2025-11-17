import { useState } from 'react'
import {
  Zap,
  Loader2,
  Download,
  AlertCircle,
  CheckCircle,
  XCircle,
  Upload,
  Copy,
  Plus,
  Trash2,
  Info,
  FileSpreadsheet
} from 'lucide-react'
import axios from 'axios'

// ============================================================================
// TYPES
// ============================================================================

type LLMProvider = 'openai' | 'anthropic' | 'ollama'

interface MappingResponse {
  success: boolean
  url: string
  template_name: string
  data: Array<Record<string, any>>
  row_count: number
  extracted_at: string
  error?: string
}

// ============================================================================
// COMPONENT
// ============================================================================

export const SmartTemplateMapper = () => {
  // State
  const [url, setUrl] = useState('')
  const [columns, setColumns] = useState<string[]>([])
  const [columnInput, setColumnInput] = useState('')
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('openai')
  const [isMapping, setIsMapping] = useState(false)
  const [mappedData, setMappedData] = useState<MappingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleParseColumns = (text: string) => {
    // Split by common delimiters: newline, tab, comma
    const parsed = text
      .split(/[\n\t,]/)
      .map(col => col.trim())
      .filter(col => col.length > 0)

    setColumns(prev => [...new Set([...prev, ...parsed])])
    setColumnInput('')
  }

  const handlePasteColumns = async () => {
    try {
      const text = await navigator.clipboard.readText()
      handleParseColumns(text)
    } catch (err) {
      setError('Failed to read from clipboard. Please paste manually.')
    }
  }

  const handleAddColumn = () => {
    if (columnInput.trim()) {
      handleParseColumns(columnInput)
    }
  }

  const handleRemoveColumn = (index: number) => {
    setColumns(prev => prev.filter((_, i) => i !== index))
  }

  const handleClearColumns = () => {
    setColumns([])
  }

  const handleSmartMap = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    if (columns.length === 0) {
      setError('Please add at least one column')
      return
    }

    setIsMapping(true)
    setError(null)
    setMappedData(null)

    try {
      const response = await axios.post<MappingResponse>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/smart-map-to-template`,
        {
          url,
          template_columns: columns,
          llm_provider: llmProvider,
          output_format: 'json'
        },
        {
          timeout: 120000 // 2 minute timeout
        }
      )

      if (response.data.success) {
        setMappedData(response.data)
      } else {
        setError(response.data.error || 'Failed to map data to template')
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to map data to template'
      setError(errorMsg)
    } finally {
      setIsMapping(false)
    }
  }

  const handleDownloadData = () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return

    const dataStr = JSON.stringify(mappedData.data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `smart_mapped_data_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleDownloadCSV = () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return

    const data = mappedData.data[0]
    const headers = Object.keys(data)
    const values = Object.values(data)

    const csvContent = [
      headers.join(','),
      values.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `smart_mapped_data_${Date.now()}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Count successfully mapped vs missing fields
  const getFieldStats = () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return null

    const data = mappedData.data[0]
    const missingMarker = '— (requires additional research)'

    let successful = 0
    let missing = 0

    Object.values(data).forEach(value => {
      if (value === missingMarker || value === null || value === '') {
        missing++
      } else {
        successful++
      }
    })

    return { successful, missing, total: successful + missing }
  }

  const stats = getFieldStats()

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 mb-6 border border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
          <Zap className="h-6 w-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Smart Template Mapper</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Map scraped data to your custom template columns using AI
          </p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-700 dark:text-slate-300">
            <p className="font-semibold mb-1">How it works:</p>
            <ol className="list-decimal ml-4 space-y-1">
              <li>Enter a URL and provide your template columns (paste from Excel or enter manually)</li>
              <li>AI scrapes the webpage and intelligently maps data to your columns</li>
              <li>Missing fields are clearly marked as "— (requires additional research)"</li>
              <li>Download results in JSON or CSV format</li>
            </ol>
            <p className="mt-2 text-xs text-purple-700 dark:text-purple-300 font-semibold">
              ⚠️ This is designed for predefined column lists. For auto-column generation, use Smart Extractor instead.
            </p>
          </div>
        </div>
      </div>

      {/* URL Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Website URL
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/page-to-scrape"
          className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent placeholder-slate-400"
        />
      </div>

      {/* Column Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Template Columns
        </label>

        {/* Input Area */}
        <div className="flex gap-2 mb-3">
          <textarea
            value={columnInput}
            onChange={(e) => setColumnInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleAddColumn()
              }
            }}
            placeholder="Paste or type column names (separate by newline, tab, or comma)&#10;&#10;Example:&#10;Company Name&#10;Market Cap&#10;Revenue&#10;Profit Margin"
            rows={4}
            className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none placeholder-slate-400 text-sm"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={handlePasteColumns}
            className="px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors flex items-center gap-2 text-sm"
          >
            <Copy className="h-4 w-4" />
            Paste from Clipboard
          </button>

          <button
            onClick={handleAddColumn}
            disabled={!columnInput.trim()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
          >
            <Plus className="h-4 w-4" />
            Add Columns
          </button>

          {columns.length > 0 && (
            <button
              onClick={handleClearColumns}
              className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors flex items-center gap-2 text-sm ml-auto"
            >
              <Trash2 className="h-4 w-4" />
              Clear All
            </button>
          )}
        </div>

        {/* Column List */}
        {columns.length > 0 && (
          <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Template Columns ({columns.length}):
            </p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {columns.map((col, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-white dark:bg-slate-800 px-3 py-2 rounded border border-slate-200 dark:border-slate-700"
                >
                  <span className="text-sm text-slate-900 dark:text-white font-mono">{col}</span>
                  <button
                    onClick={() => handleRemoveColumn(idx)}
                    className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Settings Row */}
      <div className="grid grid-cols-1 gap-4 mb-4">
        {/* LLM Provider */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            AI Provider (OpenAI recommended for best results)
          </label>
          <select
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value as LLMProvider)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="openai">OpenAI GPT-4 (Recommended)</option>
            <option value="anthropic">Anthropic Claude</option>
            <option value="ollama">Ollama (Local)</option>
          </select>
        </div>
      </div>

      {/* Map Button */}
      <div className="mb-6">
        <button
          onClick={handleSmartMap}
          disabled={isMapping || !url || columns.length === 0}
          className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold shadow-md"
        >
          {isMapping ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Mapping Data...
            </>
          ) : (
            <>
              <Zap className="h-5 w-5" />
              Map Data to Template
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6 flex items-start gap-3">
          <XCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-semibold text-red-800 dark:text-red-200">Error</p>
            <p className="text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap">{error}</p>
          </div>
        </div>
      )}

      {/* Mapped Data Display */}
      {mappedData && mappedData.success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3 flex-1">
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-semibold text-green-800 dark:text-green-200">Data Mapped Successfully!</p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Mapped data from {mappedData.url}
                </p>
                {stats && (
                  <div className="mt-2 flex gap-4 text-sm">
                    <span className="text-green-700 dark:text-green-300">
                      ✓ {stats.successful} fields extracted
                    </span>
                    {stats.missing > 0 && (
                      <span className="text-amber-700 dark:text-amber-300">
                        ⚠ {stats.missing} fields require research
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleDownloadCSV}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 text-sm"
              >
                <FileSpreadsheet className="h-4 w-4" />
                CSV
              </button>
              <button
                onClick={handleDownloadData}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 text-sm"
              >
                <Download className="h-4 w-4" />
                JSON
              </button>
            </div>
          </div>

          {/* Data Table */}
          {mappedData.data && mappedData.data.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700 overflow-auto max-h-96">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Mapped Data:</h3>
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-slate-100 dark:bg-slate-900">
                    <th className="px-4 py-2 text-left font-medium text-slate-700 dark:text-slate-300 w-1/3">
                      Column
                    </th>
                    <th className="px-4 py-2 text-left font-medium text-slate-700 dark:text-slate-300">
                      Value
                    </th>
                    <th className="px-4 py-2 text-center font-medium text-slate-700 dark:text-slate-300 w-20">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(mappedData.data[0]).map(([key, value], idx) => {
                    const isMissing = value === '— (requires additional research)' || value === null || value === ''
                    return (
                      <tr key={idx} className="border-t border-slate-200 dark:border-slate-700">
                        <td className="px-4 py-2 text-slate-900 dark:text-white font-medium">
                          {key}
                        </td>
                        <td className={`px-4 py-2 ${isMissing ? 'text-amber-600 dark:text-amber-400 italic' : 'text-slate-600 dark:text-slate-400'}`}>
                          {String(value)}
                        </td>
                        <td className="px-4 py-2 text-center">
                          {isMissing ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-xs">
                              <AlertCircle className="h-3 w-3" />
                              Missing
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs">
                              <CheckCircle className="h-3 w-3" />
                              Found
                            </span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
