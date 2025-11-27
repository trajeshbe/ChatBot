import { useState, useEffect } from 'react'
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
  FileSpreadsheet,
  Database,
  Save
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
  const [globalSelectedModel, setGlobalSelectedModel] = useState<string>('gpt-4-turbo')
  const [isMapping, setIsMapping] = useState(false)
  const [mappedData, setMappedData] = useState<MappingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [availableTemplates, setAvailableTemplates] = useState<any[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')

  // Derive llm_provider from model_id
  const getLLMProvider = (modelId: string): LLMProvider => {
    if (modelId.startsWith('gpt-') || modelId.startsWith('o1-')) return 'openai'
    if (modelId.startsWith('claude-')) return 'anthropic'
    return 'ollama'
  }

  // ============================================================================
  // URL VALIDATION HELPERS
  // ============================================================================

  // Check if URL matches the template's url_pattern
  const checkUrlMatch = (url: string, pattern: string): boolean => {
    if (!url || !pattern) return true // No validation if empty

    try {
      const urlObj = new URL(url)
      const urlHost = urlObj.hostname
      const urlPath = urlObj.pathname

      // Pattern like "books.toscrape.com/*" or "screener.in/company/*"
      const patternParts = pattern.split('/')
      const patternHost = patternParts[0]
      const patternPath = patternParts.slice(1).join('/')

      // Check hostname match (exact or wildcard)
      const hostMatches = patternHost === '*' ||
                          urlHost === patternHost ||
                          urlHost.endsWith('.' + patternHost) ||
                          patternHost.endsWith('*') && urlHost.includes(patternHost.replace('*', ''))

      // Check path match (if pattern has path)
      if (patternPath) {
        const pathPattern = new RegExp('^' + patternPath.replace(/\*/g, '.*') + '$')
        return hostMatches && pathPattern.test(urlPath)
      }

      return hostMatches
    } catch {
      return false // If URL is invalid, show validation error
    }
  }

  // Generate example URL from pattern
  const getExampleUrl = (pattern: string): string => {
    if (!pattern) return ''

    // Replace wildcards with examples
    const exampleUrl = pattern
      .replace(/\*/g, 'example')
      .replace(/\/$/, '')

    return exampleUrl.startsWith('http') ? exampleUrl : `https://${exampleUrl}`
  }

  // Get current template's URL pattern
  const currentUrlPattern = selectedTemplate
    ? availableTemplates.find(t => t.name === selectedTemplate)?.url_pattern
    : null

  // Check if current URL matches the template pattern
  const urlMatches = currentUrlPattern ? checkUrlMatch(url, currentUrlPattern) : true

  // ============================================================================
  // STATE PERSISTENCE
  // ============================================================================

  // Load saved state on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUrl = localStorage.getItem('templateMapper_url')
      const savedColumns = localStorage.getItem('templateMapper_columns')
      const savedModel = localStorage.getItem('globalSelectedModel')

      if (savedUrl) setUrl(savedUrl)
      if (savedColumns) {
        try {
          setColumns(JSON.parse(savedColumns))
        } catch (e) {
          console.error('Error parsing saved columns:', e)
        }
      }
      if (savedModel) setGlobalSelectedModel(savedModel)
    }
  }, [])

  // Listen for global model changes
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'globalSelectedModel' && e.newValue) {
        setGlobalSelectedModel(e.newValue)
      }
    }
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // Load saved templates
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        // Template Mapper mode: Show ALL templates (CSS-based + AI-powered)
        // No filter_mode parameter = default "all" mode
        const response = await axios.get(`${API_URL}/api/v1/extract/saved-templates`)
        setAvailableTemplates(response.data.templates || [])
      } catch (err) {
        console.error('Error loading templates:', err)
      }
    }
    loadTemplates()
  }, [])

  // Save state to localStorage when values change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('templateMapper_url', url)
    }
  }, [url])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('templateMapper_columns', JSON.stringify(columns))
    }
  }, [columns])

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

  const handleLoadTemplate = (templateName: string) => {
    setSelectedTemplate(templateName)
    if (!templateName) return

    const template = availableTemplates.find(t => t.name === templateName)
    if (template && template.fields) {
      // Load template columns
      setColumns(template.fields)
    }
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

    const llmProvider = getLLMProvider(globalSelectedModel)

    try {
      const response = await axios.post<MappingResponse>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/smart-map-to-template`,
        {
          url,
          template_columns: columns,
          llm_provider: llmProvider,
          model_id: globalSelectedModel,
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

  const handleDownloadExcel = async () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/to-excel`,
        mappedData.data,
        {
          responseType: 'blob',
          params: {
            filename: `smart_mapped_data_${Date.now()}.xlsx`
          },
          timeout: 30000
        }
      )

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `smart_mapped_data_${Date.now()}.xlsx`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to export to Excel')
    }
  }

  const handleSaveTemplate = async () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return

    try {
      // Extract domain from URL for template name
      const urlObj = new URL(url)
      const domain = urlObj.hostname.replace('www.', '')
      const templateName = `${domain}_template_${Date.now()}`

      // Get field names from the first row of data and convert to fields array
      const fieldNames = Object.keys(mappedData.data[0])
      const fields = fieldNames.map(name => ({
        name,
        selector: 'auto',  // Use 'auto' to let AI determine the selector
        data_type: 'text',
        required: false
      }))

      const displayName = `${domain.charAt(0).toUpperCase() + domain.slice(1)} Template`
      const urlPattern = `${urlObj.hostname}/*`

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/save-template`,
        {
          template_name: templateName,
          display_name: displayName,
          description: `Template for ${domain} with ${fieldNames.length} fields`,
          url_pattern: urlPattern,
          wait_for_selector: '.main',
          fields
        },
        {
          timeout: 30000
        }
      )

      if (response.data.success) {
        alert(`✅ Template saved successfully as "${templateName}"!\n\nYou can reuse this template for similar pages.`)
      } else {
        setError('Failed to save template')
      }
    } catch (err: any) {
      // Handle error detail that might be an array or object
      let errorMsg = 'Failed to save template'
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail, null, 2)
      } else if (err.message) {
        errorMsg = err.message
      }
      setError(`Failed to save template: ${errorMsg}`)
    }
  }

  const handleSaveToDatabase = async () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return

    try {
      // Get session ID from localStorage
      const sessionId = localStorage.getItem('sessionId') || undefined

      // Extract company name from data or URL
      const urlObj = new URL(url)
      const domain = urlObj.hostname.replace('www.', '')
      const companyName = mappedData.data[0]?.['Company Name'] ||
                         mappedData.data[0]?.['company_name'] ||
                         domain

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const response = await axios.post(
        `${API_URL}/api/v1/extract/save-to-db`,
        {
          company_name: companyName,
          source_url: url,
          extraction_type: 'smart_mapper',
          data: mappedData.data,
          template_name: domain + '_mapper',
          session_id: sessionId
        },
        {
          timeout: 30000
        }
      )

      if (response.data.success) {
        alert(`✅ Data saved to database!\n\nSaved ${mappedData.data.length} record(s) from ${url}\n\nYou can now query this data using the chatbot.`)
      } else {
        setError('Failed to save data to database')
      }
    } catch (err: any) {
      // Handle error detail that might be an array or object
      let errorMsg = 'Failed to save to database'
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail, null, 2)
      } else if (err.message) {
        errorMsg = err.message
      }
      setError(`Failed to save to database: ${errorMsg}`)
    }
  }

  // Count successfully mapped vs missing fields
  const getFieldStats = () => {
    if (!mappedData || !mappedData.data || mappedData.data.length === 0) return null

    const data = mappedData.data[0]

    let successful = 0
    let missing = 0

    Object.values(data).forEach(value => {
      // Check for missing markers: "—", "— (requires additional research)", empty, or null
      if (value === '—' || value === '— (requires additional research)' || value === null || value === '' || value === undefined) {
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
        <div className="p-2 bg-primary-600 rounded-lg">
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
      <div className="bg-primary-50 dark:bg-blue-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-primary-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-700 dark:text-slate-300">
            <p className="font-semibold mb-1">How it works:</p>
            <ol className="list-decimal ml-4 space-y-1">
              <li>Enter a URL and provide your template columns (paste from Excel or enter manually)</li>
              <li>AI scrapes the webpage and intelligently maps data to your columns</li>
              <li>Missing fields are clearly marked as "— (requires additional research)"</li>
              <li>Download results in JSON or CSV format</li>
            </ol>
            <p className="mt-2 text-xs text-primary-700 dark:text-primary-300 font-semibold">
              ⚠️ This is designed for predefined column lists. For auto-column generation, use Smart Extractor instead.
            </p>
          </div>
        </div>
      </div>

      {/* URL Input */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Website URL
          </label>
          {selectedTemplate && currentUrlPattern && (
            <button
              type="button"
              onClick={() => setUrl(getExampleUrl(currentUrlPattern))}
              className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1"
              title="Use an example URL that matches this template"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Use Example URL
            </button>
          )}
        </div>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/page-to-scrape"
          className={`w-full px-4 py-2 border-2 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:border-transparent placeholder-slate-400 transition-colors ${
            url && selectedTemplate && currentUrlPattern
              ? urlMatches
                ? 'border-green-500 dark:border-green-400 focus:ring-green-500'
                : 'border-red-500 dark:border-red-400 focus:ring-red-500'
              : 'border-slate-300 dark:border-slate-600 focus:ring-purple-500'
          }`}
        />
        {selectedTemplate && currentUrlPattern && url && !urlMatches && (
          <div className="mt-2 flex items-start gap-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-800">
            <div className="text-amber-600 dark:text-amber-400 mt-0.5">⚠️</div>
            <div className="flex-1">
              <p className="text-xs font-medium text-amber-800 dark:text-amber-200">URL Pattern Mismatch</p>
              <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                This URL might not work with the selected template. Expected pattern: <span className="font-mono">{currentUrlPattern}</span>
              </p>
            </div>
          </div>
        )}
        {selectedTemplate && currentUrlPattern && url && urlMatches && (
          <div className="mt-2 flex items-center gap-2 text-xs text-green-700 dark:text-green-300">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>URL matches template pattern</span>
          </div>
        )}
      </div>

      {/* Template Selector */}
      {availableTemplates.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Load Saved Template (Optional)
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => handleLoadTemplate(e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">-- Select a template or enter columns manually --</option>
            {availableTemplates.map((template) => (
              <option key={template.name} value={template.name}>
                {template.has_css_selectors !== false ? '[CSS] ' : '[AI] '}{template.display_name} - {template.description}
              </option>
            ))}
          </select>
          {selectedTemplate && availableTemplates.find(t => t.name === selectedTemplate) && (
            <div className="mt-2 space-y-2">
              <div className="flex items-center gap-2">
                {availableTemplates.find(t => t.name === selectedTemplate)?.has_css_selectors !== false ? (
                  <span className="px-2 py-0.5 text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200 rounded">
                    CSS Selector Based
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-xs font-semibold bg-primary-100 text-blue-800 dark:bg-primary-900/30 dark:text-blue-200 rounded">
                    AI-Powered
                  </span>
                )}
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {availableTemplates.find(t => t.name === selectedTemplate)?.fields.length} columns loaded
                </span>
              </div>
              {availableTemplates.find(t => t.name === selectedTemplate)?.url_pattern && (
                <div className="flex items-start gap-2 p-2 bg-primary-50 dark:bg-blue-900/20 rounded border border-primary-200 dark:border-primary-800">
                  <div className="text-primary-600 dark:text-blue-400 mt-0.5">ℹ️</div>
                  <div className="flex-1">
                    <p className="text-xs font-medium text-blue-800 dark:text-blue-200">Compatible URL Pattern:</p>
                    <p className="text-xs font-mono text-primary-700 dark:text-primary-300 mt-1">
                      {availableTemplates.find(t => t.name === selectedTemplate)?.url_pattern}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

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

      {/* Map Button */}
      <div className="mb-6">
        <button
          onClick={handleSmartMap}
          disabled={isMapping || !url || columns.length === 0}
          className="w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold shadow-md"
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
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={handleDownloadExcel}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2 text-sm font-semibold"
                title="Download as Excel (.xlsx)"
              >
                <FileSpreadsheet className="h-4 w-4" />
                Excel
              </button>
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
              <button
                onClick={handleSaveTemplate}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 text-sm font-semibold"
                title="Save this extraction pattern as a reusable template"
              >
                <Save className="h-4 w-4" />
                Save Template
              </button>
              <button
                onClick={handleSaveToDatabase}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2 text-sm font-semibold"
                title="Save extracted data to vector database for RAG queries"
              >
                <Database className="h-4 w-4" />
                Save to DB
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
                    // Check for missing values
                    const isMissing = value === '—' || value === '— (requires additional research)' || value === null || value === '' || value === undefined
                    const displayValue = isMissing ? '—' : String(value)

                    return (
                      <tr key={idx} className="border-t border-slate-200 dark:border-slate-700">
                        <td className="px-4 py-2 text-slate-900 dark:text-white font-medium">
                          {key}
                        </td>
                        <td className={`px-4 py-2 ${isMissing ? 'text-amber-600 dark:text-amber-400 italic' : 'text-slate-600 dark:text-slate-400'}`}>
                          {displayValue}
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
