import { useState, useEffect } from 'react'
import { FileSpreadsheet, Globe, Download, Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp, AlertCircle, Database } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ExtractionJob {
  id: string
  url: string
  preset: string
  status: 'pending' | 'processing' | 'success' | 'error'
  data?: any[]
  error?: string
  timestamp: Date
  presetData?: boolean // Flag to indicate data from preset endpoint (needs Excel conversion)
}

interface CollapsibleErrorProps {
  error: string
  onDismiss?: () => void
}

const CollapsibleError: React.FC<CollapsibleErrorProps> = ({ error, onDismiss }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="mb-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
      >
        <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm font-medium">Error occurred</span>
        </div>
        <div className="flex items-center gap-2">
          {!isExpanded && (
            <span className="text-xs text-red-600 dark:text-red-400 max-w-md truncate">
              {error}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-red-600" />
          ) : (
            <ChevronDown className="w-4 h-4 text-red-600" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 py-3 border-t border-red-200 dark:border-red-800 bg-red-100 dark:bg-red-900/10">
          <p className="text-sm text-red-800 dark:text-red-200 font-mono whitespace-pre-wrap">
            {error}
          </p>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="mt-2 px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  )
}

interface CustomField {
  name: string
  selector: string
  data_type: 'text' | 'number' | 'date'
  required: boolean
}

export default function TemplateExtractor({ sessionId }: { sessionId: string }) {
  const [url, setUrl] = useState('')
  const [preset, setPreset] = useState('screener_in')
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobs, setJobs] = useState<ExtractionJob[]>([])
  const [availablePresets, setAvailablePresets] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  // Extraction mode: 'preset' or 'custom'
  const [extractionMode, setExtractionMode] = useState<'preset' | 'custom'>('preset')

  // Custom CSS fields state
  const [customFields, setCustomFields] = useState<CustomField[]>([])
  const [newFieldName, setNewFieldName] = useState('')
  const [newFieldSelector, setNewFieldSelector] = useState('')
  const [newFieldDataType, setNewFieldDataType] = useState<'text' | 'number' | 'date'>('text')
  const [newFieldRequired, setNewFieldRequired] = useState(false)

  // Save Template modal state
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [templateDescription, setTemplateDescription] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  // Save to DB modal state
  const [showSaveToDBModal, setShowSaveToDBModal] = useState(false)
  const [companyName, setCompanyName] = useState('')
  const [isSavingToDB, setIsSavingToDB] = useState(false)

  // ============================================================================
  // STATE PERSISTENCE
  // ============================================================================

  // Load saved form state on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUrl = localStorage.getItem('templateExtractor_url')
      const savedPreset = localStorage.getItem('templateExtractor_preset')

      if (savedUrl) setUrl(savedUrl)
      if (savedPreset) setPreset(savedPreset)
    }
  }, [])

  // Save form state to localStorage when values change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('templateExtractor_url', url)
    }
  }, [url])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('templateExtractor_preset', preset)
    }
  }, [preset])

  // Load jobs from sessionStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId) {
      const stored = sessionStorage.getItem(`extraction_jobs_${sessionId}`)
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          setJobs(parsed.map((j: any) => ({
            ...j,
            timestamp: new Date(j.timestamp)
          })))
        } catch (e) {
          console.error('Error loading extraction jobs:', e)
        }
      }
    }
  }, [sessionId])

  // Save jobs to sessionStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId && jobs.length > 0) {
      sessionStorage.setItem(`extraction_jobs_${sessionId}`, JSON.stringify(jobs))
    }
  }, [jobs, sessionId])

  // Load available presets (including saved templates)
  useEffect(() => {
    const loadPresets = async () => {
      try {
        // CSS Extractor mode: Only show templates with CSS selectors
        const response = await axios.get(`${API_URL}/api/v1/extract/saved-templates?filter_mode=css`)
        const allTemplates = response.data.templates || []

        // Show ONLY templates with CSS selectors (filtered by backend)
        setAvailablePresets(allTemplates)

        console.log(`Loaded ${allTemplates.length} CSS-based templates`)
      } catch (error) {
        console.error('Error loading presets:', error)
      }
    }
    loadPresets()
  }, [])

  // ============================================================================
  // CUSTOM FIELD MANAGEMENT
  // ============================================================================

  const handleAddField = () => {
    if (!newFieldName.trim() || !newFieldSelector.trim()) {
      alert('Please enter both field name and CSS selector')
      return
    }

    const newField: CustomField = {
      name: newFieldName.trim(),
      selector: newFieldSelector.trim(),
      data_type: newFieldDataType,
      required: newFieldRequired
    }

    setCustomFields(prev => [...prev, newField])

    // Clear form
    setNewFieldName('')
    setNewFieldSelector('')
    setNewFieldDataType('text')
    setNewFieldRequired(false)
  }

  const handleRemoveField = (index: number) => {
    setCustomFields(prev => prev.filter((_, i) => i !== index))
  }

  const handleExtract = async () => {
    if (!url.trim()) return

    // Validation
    if (extractionMode === 'custom' && customFields.length === 0) {
      setError('Please add at least one field with a CSS selector before extracting')
      return
    }

    setIsProcessing(true)
    setError(null)

    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const newJob: ExtractionJob = {
      id: jobId,
      url,
      preset: extractionMode === 'preset' ? preset : 'custom',
      status: 'processing',
      timestamp: new Date()
    }

    setJobs(prev => [newJob, ...prev])

    try {
      let response

      if (extractionMode === 'preset') {
        // Use preset template endpoint
        response = await axios.post(
          `${API_URL}/api/v1/extract/preset/${preset}`,
          {
            url,
            session_id: sessionId
          }
        )
      } else {
        // Custom CSS extraction - create temporary template and use it
        const tempTemplateName = `temp_${Date.now()}`
        const urlObj = new URL(url)

        // Create temporary template with custom fields
        const templatePayload = {
          template_name: tempTemplateName,
          display_name: 'Temporary Custom Template',
          description: 'User-defined custom CSS extraction',
          url_pattern: `${urlObj.hostname}/*`,
          wait_for_selector: '.main, body',
          fields: customFields.map(field => ({
            name: field.name,
            selector: field.selector,
            data_type: field.data_type,
            required: field.required
          }))
        }

        // Save temp template
        await axios.post(`${API_URL}/api/v1/extract/save-template`, templatePayload)

        // Use the temp template
        response = await axios.post(
          `${API_URL}/api/v1/extract/preset/${tempTemplateName}`,
          {
            url,
            session_id: sessionId
          }
        )
      }

      if (response.data.success && response.data.data) {
        // Update job with extracted data
        setJobs(prev =>
          prev.map(job =>
            job.id === jobId
              ? {
                  ...job,
                  status: 'success',
                  data: response.data.data,
                  presetData: true
                }
              : job
          )
        )
        setUrl('')
      } else {
        throw new Error(response.data.error || 'Extraction failed')
      }

    } catch (error: any) {
      // Handle both string errors and detailed error objects from backend
      let errorMessage: string
      const detail = error.response?.data?.detail

      if (typeof detail === 'object' && detail !== null) {
        // Backend returned a detailed error object
        errorMessage = detail.message || detail.error || 'Extraction failed'

        // Add suggestions if available
        if (detail.suggestions && Array.isArray(detail.suggestions)) {
          errorMessage += '\n\nSuggestions:\n' + detail.suggestions.map((s: string) => `• ${s}`).join('\n')
        }
      } else if (typeof detail === 'string') {
        errorMessage = detail
      } else {
        errorMessage = error.message || 'Extraction failed'
      }

      setJobs(prev =>
        prev.map(job =>
          job.id === jobId
            ? {
                ...job,
                status: 'error',
                error: errorMessage
              }
            : job
        )
      )
      setError(errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleExportPresetData = async (data: any[], filename: string) => {
    try {
      // Use the /to-excel endpoint for preset data
      const response = await axios.post(
        `${API_URL}/api/v1/extract/to-excel`,
        data,
        {
          params: { filename },
          responseType: 'blob'
        }
      )

      // Create download link
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error exporting to Excel:', error)
      alert('Failed to export to Excel')
    }
  }

  const handleSaveAsTemplate = async (job: ExtractionJob) => {
    if (!templateName.trim()) {
      alert('Please enter a template name')
      return
    }

    setIsSaving(true)
    try {
      // Convert template name to internal format (lowercase with underscores)
      const internalName = templateName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')

      // Get URL pattern from job URL
      const urlObj = new URL(job.url)
      const urlPattern = `${urlObj.hostname}/*`

      // Prepare fields - use custom fields if in custom mode, otherwise infer from data
      let templateFields

      if (extractionMode === 'custom' && customFields.length > 0) {
        // Custom mode: Use the CSS selectors defined by the user
        templateFields = customFields.map(field => ({
          name: field.name,
          selector: field.selector,
          data_type: field.data_type,
          required: field.required
        }))
      } else {
        // Preset mode: Create template from extracted data structure (AI-powered template)
        templateFields = job.data && job.data[0] ? Object.keys(job.data[0]).map(key => ({
          name: key,
          selector: '',  // Empty selector = AI-powered template
          data_type: 'text',
          required: false
        })) : []
      }

      const response = await axios.post(`${API_URL}/api/v1/extract/save-template`, {
        template_name: internalName,
        display_name: templateName,
        description: templateDescription || `Extract data from ${urlObj.hostname}`,
        url_pattern: urlPattern,
        wait_for_selector: '.main, body',  // Default selector
        fields: templateFields
      })

      alert(`✅ Template "${templateName}" saved successfully! It's now available in the preset dropdown.`)
      setShowSaveModal(false)
      setTemplateName('')
      setTemplateDescription('')

      // Reload presets to show the new template (CSS mode filter)
      try {
        const presetsResponse = await axios.get(`${API_URL}/api/v1/extract/saved-templates?filter_mode=css`)
        if (presetsResponse.data.templates) {
          setAvailablePresets(presetsResponse.data.templates)
        }
      } catch (error) {
        console.error('Error reloading presets:', error)
      }

    } catch (error: any) {
      console.error('Error saving template:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to save template'
      alert(`Failed to save template: ${errorMsg}`)
    } finally {
      setIsSaving(false)
    }
  }

  // Save extracted data to vector DB & MinIO for RAG
  const handleSaveToDB = async (job: ExtractionJob) => {
    if (!companyName.trim()) {
      alert('Please enter a company name')
      return
    }

    if (!job.data || job.data.length === 0) {
      alert('No data available to save')
      return
    }

    setIsSavingToDB(true)
    try {
      const response = await axios.post(`${API_URL}/api/v1/extract/save-to-db`, {
        company_name: companyName,
        source_url: job.url,
        extraction_type: 'css_selector',
        template_name: job.preset,
        data: job.data,
        session_id: sessionId
      })

      alert(`✅ Saved ${job.data.length} rows to vector store! Data is now available for RAG queries about ${companyName}.`)
      setShowSaveToDBModal(false)
      setCompanyName('')
    } catch (error: any) {
      console.error('Error saving to DB:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to save to database'
      alert(`Failed to save to database: ${errorMsg}`)
    } finally {
      setIsSavingToDB(false)
    }
  }

  return (
    <div className="h-full p-6 overflow-y-auto bg-slate-50 dark:bg-slate-900">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          CSS Selector Based Data Extraction
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Extract structured data from websites using pre-configured CSS selector templates (Screener.in preset available).
        </p>

        {/* Global Error (Collapsible) */}
        {error && (
          <CollapsibleError
            error={error}
            onDismiss={() => setError(null)}
          />
        )}

        {/* Extraction Form */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-md border border-slate-200 dark:border-slate-700 mb-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            Extract Data
          </h3>

          {/* Extraction Mode Toggle */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Extraction Mode
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setExtractionMode('preset')}
                className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                  extractionMode === 'preset'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                    : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500 text-slate-600 dark:text-slate-400'
                }`}
              >
                <div className="text-center">
                  <div className="font-semibold">Use Saved Template</div>
                  <div className="text-xs mt-1 opacity-80">Select from existing templates</div>
                </div>
              </button>
              <button
                onClick={() => setExtractionMode('custom')}
                className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                  extractionMode === 'custom'
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                    : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500 text-slate-600 dark:text-slate-400'
                }`}
              >
                <div className="text-center">
                  <div className="font-semibold">Define Custom Fields</div>
                  <div className="text-xs mt-1 opacity-80">Manually specify CSS selectors</div>
                </div>
              </button>
            </div>
          </div>

          {/* Template Selection (only in preset mode) */}
          {extractionMode === 'preset' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Select Preset Template
              </label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availablePresets.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.has_css_selectors !== false ? '[CSS] ' : '[AI] '}{p.display_name} - {p.description}
                </option>
              ))}
            </select>
            {availablePresets.find(p => p.name === preset) && (
              <div className="mt-2 space-y-1">
                <div className="flex items-center gap-2">
                  {availablePresets.find(p => p.name === preset)?.has_css_selectors !== false ? (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200 rounded">
                      CSS Selector Based
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200 rounded">
                      AI-Powered
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Extracts: {availablePresets.find(p => p.name === preset)?.fields.join(', ')}
                </p>
                {availablePresets.find(p => p.name === preset)?.url_pattern && (
                  <div className="flex items-start gap-2 mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                    <div className="text-blue-600 dark:text-blue-400 mt-0.5">ℹ️</div>
                    <div className="flex-1">
                      <p className="text-xs font-medium text-blue-800 dark:text-blue-200">Compatible URL Pattern:</p>
                      <p className="text-xs font-mono text-blue-700 dark:text-blue-300 mt-1">
                        {availablePresets.find(p => p.name === preset)?.url_pattern}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
            </div>
          )}

          {/* Custom Field Builder (only in custom mode) */}
          {extractionMode === 'custom' && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Custom CSS Fields ({customFields.length})
                </label>
              </div>

              {/* Add Field Form */}
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 border border-slate-200 dark:border-slate-700 mb-3">
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                      Field Name
                    </label>
                    <input
                      type="text"
                      value={newFieldName}
                      onChange={(e) => setNewFieldName(e.target.value)}
                      placeholder="e.g., Product Title"
                      className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                      CSS Selector
                    </label>
                    <input
                      type="text"
                      value={newFieldSelector}
                      onChange={(e) => setNewFieldSelector(e.target.value)}
                      placeholder="e.g., .product-title h1"
                      className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                      Data Type
                    </label>
                    <select
                      value={newFieldDataType}
                      onChange={(e) => setNewFieldDataType(e.target.value as 'text' | 'number' | 'date')}
                      className="w-full px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      <option value="text">Text</option>
                      <option value="number">Number</option>
                      <option value="date">Date</option>
                    </select>
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 px-3 py-2 text-sm">
                      <input
                        type="checkbox"
                        checked={newFieldRequired}
                        onChange={(e) => setNewFieldRequired(e.target.checked)}
                        className="rounded border-slate-300 dark:border-slate-600"
                      />
                      <span className="text-slate-700 dark:text-slate-300">Required</span>
                    </label>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleAddField}
                      className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors font-medium"
                    >
                      Add Field
                    </button>
                  </div>
                </div>
              </div>

              {/* Custom Fields List */}
              {customFields.length > 0 ? (
                <div className="space-y-2">
                  {customFields.map((field, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700"
                    >
                      <div className="flex-1 grid grid-cols-3 gap-3 text-sm">
                        <div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Field Name</div>
                          <div className="font-medium text-slate-900 dark:text-white">{field.name}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">CSS Selector</div>
                          <div className="font-mono text-xs text-slate-700 dark:text-slate-300">{field.selector}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Type</div>
                          <div className="flex gap-2">
                            <span className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded">
                              {field.data_type}
                            </span>
                            {field.required && (
                              <span className="px-2 py-0.5 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">
                                required
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveField(index)}
                        className="px-3 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500 dark:text-slate-400 text-sm">
                  No custom fields defined. Add fields using the form above.
                </div>
              )}
            </div>
          )}

          {/* URL Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              URL to Extract
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/page-to-scrape"
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleExtract}
            disabled={isProcessing || !url.trim()}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Extracting...
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-5 h-5" />
                Extract Data
              </>
            )}
          </button>
        </div>

        {/* Extraction History */}
        {jobs.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Extraction History ({jobs.length})
            </h3>
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-md border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Globe className="w-4 h-4 text-blue-600" />
                        <p className="text-sm font-medium text-slate-900 dark:text-white break-all">
                          {job.url}
                        </p>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Template: {availablePresets.find(p => p.name === job.preset)?.display_name || job.preset}
                        {' • '}
                        {job.timestamp.toLocaleString()}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {job.status === 'processing' && (
                        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                      )}
                      {job.status === 'success' && (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          {job.data && job.data.length > 0 && (
                            <>
                              <button
                                onClick={() => {
                                  setShowSaveModal(true)
                                  // Pre-fill template name based on preset
                                  const presetInfo = availablePresets.find(p => p.name === job.preset)
                                  if (presetInfo) {
                                    setTemplateName(`${presetInfo.display_name} - Custom`)
                                  }
                                }}
                                className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors flex items-center gap-1"
                                title="Save this extraction as a reusable CSS template"
                              >
                                <FileSpreadsheet className="w-3 h-3" />
                                Save Template
                              </button>
                              <button
                                onClick={() => handleExportPresetData(
                                  job.data!,
                                  `extraction_${new Date().getTime()}.xlsx`
                                )}
                                className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
                              >
                                <Download className="w-3 h-3" />
                                Export Excel
                              </button>
                              <button
                                onClick={() => {
                                  setShowSaveToDBModal(true)
                                  // Try to extract company name from URL or data
                                  const firstRow = job.data?.[0]
                                  if (firstRow && 'Company Name' in firstRow) {
                                    setCompanyName(String(firstRow['Company Name']))
                                  }
                                }}
                                className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors flex items-center gap-1"
                                title="Save extracted data to vector database for RAG queries"
                              >
                                <Database className="w-3 h-3" />
                                Save to DB
                              </button>
                            </>
                          )}
                        </>
                      )}
                      {job.status === 'error' && (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                  </div>

                  {/* Success: Show extraction info */}
                  {job.status === 'success' && job.data && job.data.length > 0 && (
                    <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                      <p className="text-sm font-medium text-green-900 dark:text-green-100 mb-2">
                        ✓ Extraction completed successfully!
                      </p>
                      <div className="text-xs text-green-800 dark:text-green-200 space-y-1">
                        <p>Extracted {job.data.length} row(s) using preset template: {job.preset}</p>
                        <p className="text-xs mt-2 text-green-700 dark:text-green-300">
                          Click "Export Excel" button above to download the results.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Error: Collapsible */}
                  {job.status === 'error' && job.error && (
                    <div className="mt-3">
                      <CollapsibleError error={job.error} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {jobs.length === 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-12 shadow-md border border-slate-200 dark:border-slate-700 text-center">
            <FileSpreadsheet className="w-16 h-16 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
            <p className="text-lg text-slate-600 dark:text-slate-400">No extraction jobs yet</p>
            <p className="text-sm text-slate-500 dark:text-slate-500 mt-1">Select a preset template and enter a URL to start extracting data</p>
          </div>
        )}

        {/* Save Template Modal */}
        {showSaveModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                Save as CSS Template
              </h3>

              <div className="space-y-4">
                {/* Template Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    placeholder="e.g., Product Data Extraction"
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    This name will appear in the preset dropdown
                  </p>
                </div>

                {/* Template Description */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    value={templateDescription}
                    onChange={(e) => setTemplateDescription(e.target.value)}
                    placeholder="Brief description of what this template extracts..."
                    rows={3}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                  />
                </div>

                {/* Info Note */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    💡 This will save the extraction structure as a reusable template. You can use it for similar pages in the future.
                  </p>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowSaveModal(false)
                    setTemplateName('')
                    setTemplateDescription('')
                  }}
                  className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  disabled={isSaving}
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Find the most recent successful job to save
                    const successJob = jobs.find(j => j.status === 'success' && j.data && j.data.length > 0)
                    if (successJob) {
                      handleSaveAsTemplate(successJob)
                    }
                  }}
                  disabled={isSaving || !templateName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
                >
                  {isSaving ? 'Saving...' : 'Save Template'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Save to DB Modal */}
        {showSaveToDBModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                Save to Vector Database
              </h3>

              <div className="space-y-4">
                {/* Company Name */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="e.g., Reliance Industries"
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Used for folder organization in MinIO and metadata tagging
                  </p>
                </div>

                {/* Info Note */}
                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
                  <p className="text-sm text-purple-700 dark:text-purple-300 mb-2">
                    <strong>💡 What happens when you save:</strong>
                  </p>
                  <ul className="text-xs text-purple-600 dark:text-purple-300 space-y-1 list-disc list-inside">
                    <li>Data is converted to text and embedded (384-dim vectors)</li>
                    <li>Stored in PostgreSQL vector store for semantic search</li>
                    <li>Raw JSON saved to MinIO at: extractions/{companyName}/</li>
                    <li>Ready for RAG queries in chat interface</li>
                  </ul>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowSaveToDBModal(false)
                    setCompanyName('')
                  }}
                  className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  disabled={isSavingToDB}
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Find the most recent successful job to save
                    const successJob = jobs.find(j => j.status === 'success' && j.data && j.data.length > 0)
                    if (successJob) {
                      handleSaveToDB(successJob)
                    }
                  }}
                  disabled={isSavingToDB || !companyName.trim()}
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
                >
                  {isSavingToDB ? 'Saving...' : 'Save to DB'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
