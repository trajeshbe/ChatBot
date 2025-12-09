import { useState, useEffect } from 'react'
import {
  Sparkles,
  Loader2,
  Download,
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  Info,
  ArrowRight,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Database
} from 'lucide-react'
import axios from 'axios'

// ============================================================================
// TYPES
// ============================================================================

type LLMProvider = 'ollama' | 'openai' | 'anthropic'
type OutputFormat = 'excel' | 'csv' | 'json'

interface ExtractedField {
  name: string
  display_name: string
  description: string
  type: string
  required: boolean
  extraction_strategy: string
  extraction_hint: string
}

interface AutoGenerateResponse {
  success: boolean
  template?: {
    name: string
    description: string
    template_type: string
    fields_count: number
  }
  fields?: ExtractedField[]
  template_type?: string
  confidence?: number
  message?: string
  error?: string
}

interface ExtractionResponse {
  success: boolean
  table: Array<Record<string, any>>  // Ultra-smart endpoint returns "table", not "data"
  columns: string[]
  row_count: number
  extraction_metadata: Record<string, any>
  error?: string | null
}

// ============================================================================
// COMPONENT
// ============================================================================

interface SmartExtractorProps {
  projectId?: string
}

interface Project {
  id: string
  name: string
}

export const SmartExtractor = ({ projectId }: SmartExtractorProps = {}) => {
  // State
  const [url, setUrl] = useState('')
  const [userInstructions, setUserInstructions] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)
  const [generatedTemplate, setGeneratedTemplate] = useState<AutoGenerateResponse | null>(null)
  const [extractedData, setExtractedData] = useState<ExtractionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [globalSelectedModel, setGlobalSelectedModel] = useState<string>('')
  const [projectName, setProjectName] = useState<string>('')

  // Configurable parameters
  const [maxSteps, setMaxSteps] = useState(10)

  // Fixed backend parameters (not configurable in UI)
  const outputFormat: OutputFormat = 'json'
  const maxFields = 15

  // Derive llm_provider from model_id
  const getLLMProvider = (modelId: string): LLMProvider => {
    if (modelId.startsWith('gpt-') || modelId.startsWith('o1-')) return 'openai'
    if (modelId.startsWith('claude-')) return 'anthropic'
    return 'ollama'  // Ollama models typically have format like "qwen2.5:1.5b"
  }

  // Save Template modal state
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [templateName, setTemplateName] = useState('')

  // ============================================================================
  // STATE PERSISTENCE
  // ============================================================================

  // Load saved state on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUrl = localStorage.getItem('smartExtractor_url')
      const savedInstructions = localStorage.getItem('smartExtractor_instructions')
      const savedModel = localStorage.getItem('globalSelectedModel')

      if (savedUrl) setUrl(savedUrl)
      if (savedInstructions) setUserInstructions(savedInstructions)
      // Load model from localStorage - no hardcoded fallback
      if (savedModel) {
        setGlobalSelectedModel(savedModel)
      }
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

  // Fetch project name if projectId is provided
  useEffect(() => {
    const fetchProjectName = async () => {
      if (projectId) {
        try {
          const token = localStorage.getItem('access_token')
          const response = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects`,
            { headers: token ? { Authorization: `Bearer ${token}` } : {} }
          )
          const projects: Project[] = response.data || []
          const project = projects.find(p => p.id === projectId)
          if (project) {
            setProjectName(project.name)
          }
        } catch (error) {
          console.error('Error fetching project name:', error)
        }
      }
    }
    fetchProjectName()
  }, [projectId])

  // Save state to localStorage when values change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('smartExtractor_url', url)
    }
  }, [url])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('smartExtractor_instructions', userInstructions)
    }
  }, [userInstructions])
  const [templateDescription, setTemplateDescription] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  // Save to DB modal state
  const [showSaveToDBModal, setShowSaveToDBModal] = useState(false)
  const [companyName, setCompanyName] = useState('')
  const [isSavingToDB, setIsSavingToDB] = useState(false)

  // Session ID from localStorage
  const [sessionId, setSessionId] = useState<string>('')

  // Load session ID on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('sessionId')
    if (storedSessionId) {
      setSessionId(storedSessionId)
    } else {
      // Use hyphens to match ChatInterfaceEnhanced format: session-{timestamp}-{random}
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
      localStorage.setItem('sessionId', newSessionId)
      setSessionId(newSessionId)
    }
  }, [])

  // Example prompts
  const examplePrompts = [
    "Extract product information: name, price, description, and availability",
    "Get company financial data: revenue, profit margin, growth rate, and market cap",
    "Pull article details: title, author, publish date, category, and tags",
    "Scrape job listings: job title, company, location, salary, and requirements",
    "Extract real estate listings: address, price, bedrooms, bathrooms, and square footage"
  ]

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleAutoGenerate = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    if (!userInstructions.trim()) {
      setError('Please provide instructions for what data to extract')
      return
    }

    // Validate that a model is selected
    if (!globalSelectedModel || !globalSelectedModel.trim()) {
      setError('Please select a model from the dropdown in the Chat interface first.')
      return
    }

    setIsGenerating(true)
    setError(null)
    setGeneratedTemplate(null)

    const llmProvider = getLLMProvider(globalSelectedModel)

    try {
      const response = await axios.post<AutoGenerateResponse>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/auto-generate`,
        {
          url,
          user_instructions: userInstructions,
          llm_provider: llmProvider,
          max_fields: maxFields,
          project_id: projectId || undefined
        }
      )

      if (response.data.success) {
        setGeneratedTemplate(response.data)
      } else {
        setError(response.data.error || 'Failed to generate template')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate template')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSmartExtract = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    if (!userInstructions.trim()) {
      setError('Please provide instructions for what data to extract')
      return
    }

    // Validate that a model is selected
    if (!globalSelectedModel || !globalSelectedModel.trim()) {
      setError('Please select a model from the dropdown in the Chat interface first.')
      return
    }

    setIsExtracting(true)
    setError(null)
    setExtractedData(null)

    const llmProvider = getLLMProvider(globalSelectedModel)

    // Get auth token for user context
    const token = localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    try {
      const response = await axios.post<ExtractionResponse>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/ultra-smart`,
        {
          url,
          user_instructions: userInstructions,
          llm_provider: llmProvider,
          model_id: globalSelectedModel,  // Use model from Chat UI dropdown
          output_format: outputFormat,
          max_steps: maxSteps,
          project_id: projectId || undefined
        },
        { headers }
      )

      if (response.data.success) {
        setExtractedData(response.data)
      } else {
        setError(response.data.error || 'Failed to extract data')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract data')
    } finally {
      setIsExtracting(false)
    }
  }

  const handleDownloadData = () => {
    if (!extractedData) return

    const dataStr = JSON.stringify(extractedData.table, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `extracted_data_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const useExamplePrompt = (prompt: string) => {
    setUserInstructions(prompt)
  }

  const handleSaveAsTemplate = async () => {
    if (!templateName.trim()) {
      alert('Please enter a template name')
      return
    }

    if (!extractedData || !extractedData.table || extractedData.table.length === 0) {
      alert('No extracted data available to save')
      return
    }

    setIsSaving(true)
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // Convert template name to internal format (lowercase with underscores)
      const internalName = templateName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')

      // Get URL pattern from extraction URL (use the url state variable, not extractedData.url)
      const urlObj = new URL(url)
      const urlPattern = `${urlObj.hostname}/*`

      // Prepare fields from extracted data
      const templateFields = Object.keys(extractedData.table[0]).map(key => ({
        name: key,
        selector: '',
        data_type: 'text',
        required: false
      }))

      const response = await axios.post(`${API_URL}/api/v1/extract/save-template`, {
        template_name: internalName,
        display_name: templateName,
        description: templateDescription || `Extract data from ${urlObj.hostname} using Smart Extraction pattern`,
        url_pattern: urlPattern,
        wait_for_selector: '.main',  // Default selector
        fields: templateFields
      })

      alert(`✅ Template "${templateName}" saved successfully! It's now available in CSS Selector mode.`)
      setShowSaveModal(false)
      setTemplateName('')
      setTemplateDescription('')

    } catch (error: any) {
      console.error('Error saving template:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to save template'
      alert(`Failed to save template: ${errorMsg}`)
    } finally {
      setIsSaving(false)
    }
  }

  // Save extracted data to vector DB & MinIO for RAG
  const handleSaveToDB = async () => {
    if (!companyName.trim()) {
      alert('Please enter a company name')
      return
    }

    if (!extractedData || !extractedData.table || extractedData.table.length === 0) {
      alert('No data available to save')
      return
    }

    setIsSavingToDB(true)
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // Get auth token for user context
      const token = localStorage.getItem('access_token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}

      const response = await axios.post(`${API_URL}/api/v1/extract/save-to-db`, {
        company_name: companyName,
        source_url: extractedData.url || url,
        extraction_type: 'smart',
        template_name: null,
        data: extractedData.table,
        session_id: sessionId,
        project_id: projectId || undefined  // Include project context
      }, { headers })

      alert(`✅ Saved ${extractedData.table.length} rows to vector store! Data is now available for RAG queries about ${companyName}.`)
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

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 mb-6 border border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-primary-500 to-cyan-500 rounded-lg">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Smart Extractor</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Extract data with AI - no template needed! Just describe what you want.
          </p>
        </div>
      </div>

      {/* Project Context Indicator */}
      {projectId && projectName && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-700 rounded-lg p-3 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <Database className="h-4 w-4 text-primary-600 dark:text-primary-400" />
            <span className="text-primary-700 dark:text-primary-300 font-medium">
              Project Context:
            </span>
            <span className="text-primary-900 dark:text-primary-100 font-semibold">
              {projectName}
            </span>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="bg-primary-50 dark:bg-blue-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-primary-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-700 dark:text-slate-300">
            <p className="font-semibold mb-1">How it works:</p>
            <ol className="list-decimal ml-4 space-y-1">
              <li>Enter a URL and describe what data you want to extract in plain English</li>
              <li>AI analyzes the webpage and creates an intelligent extraction template</li>
              <li>Data is extracted automatically and delivered in your preferred format</li>
            </ol>
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
          className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder-slate-400"
        />
      </div>

      {/* User Instructions */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            What data do you want to extract?
          </div>
        </label>
        <textarea
          value={userInstructions}
          onChange={(e) => setUserInstructions(e.target.value)}
          placeholder="Describe what you want to extract in natural language...&#10;&#10;Example: Extract product names, prices, ratings, and availability status"
          rows={4}
          className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none placeholder-slate-400"
        />

        {/* Example Prompts */}
        <div className="mt-3">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Try these examples:</p>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => useExamplePrompt(prompt)}
                className="text-xs px-3 py-1 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full hover:bg-primary-100 dark:hover:bg-blue-900/50 transition-colors"
              >
                {prompt.substring(0, 50)}...
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="mb-4">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
        >
          {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          Advanced Options
        </button>

        {showAdvanced && (
          <div className="mt-3 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="text-sm text-slate-600 dark:text-slate-400">
              {/* Max Steps Control */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Max Navigation Steps (for pagination)
                </label>
                <input
                  type="number"
                  value={maxSteps}
                  onChange={(e) => setMaxSteps(Math.max(1, Math.min(50, parseInt(e.target.value) || 10)))}
                  min="1"
                  max="50"
                  className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Controls how many pages the navigation agent will visit. Increase for sites with many pages. Default: 10
                </p>
              </div>

              <p className="mb-2 font-medium text-slate-700 dark:text-slate-300">Two-Step Workflow:</p>
              <p className="mb-4">
                You can either generate a template first to review it, or directly extract data in one step.
              </p>

              <button
                onClick={handleAutoGenerate}
                disabled={isGenerating || !url || !userInstructions}
                className="w-full mb-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating Template...
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4" />
                    Step 1: Generate Template Only
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={handleSmartExtract}
          disabled={isExtracting || !url || !userInstructions}
          className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold shadow-md"
        >
          {isExtracting ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Extracting Data...
            </>
          ) : (
            <>
              <Sparkles className="h-5 w-5" />
              Smart Extract
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <XCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-semibold text-red-800">Error</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Generated Template Display */}
      {generatedTemplate && generatedTemplate.success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3 mb-4">
            <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-semibold text-green-800 dark:text-green-200">Template Generated Successfully!</p>
              <p className="text-sm text-green-700 dark:text-green-300">{generatedTemplate.message}</p>
            </div>
          </div>

          {generatedTemplate.template && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 mb-4 border border-slate-200 dark:border-slate-700">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Template Details:</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Name:</span>{' '}
                  <span className="font-medium text-slate-900 dark:text-white">{generatedTemplate.template.name}</span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Type:</span>{' '}
                  <span className="font-medium text-slate-900 dark:text-white">{generatedTemplate.template.template_type}</span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Fields:</span>{' '}
                  <span className="font-medium text-slate-900 dark:text-white">{generatedTemplate.template.fields_count}</span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Confidence:</span>{' '}
                  <span className="font-medium text-slate-900 dark:text-white">
                    {((generatedTemplate.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {generatedTemplate.fields && generatedTemplate.fields.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Generated Fields:</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {generatedTemplate.fields.map((field, idx) => (
                  <div key={idx} className="border border-slate-200 dark:border-slate-700 rounded p-3">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-slate-800 dark:text-slate-200">
                          {field.display_name || field.name}
                        </p>
                        {field.description && (
                          <p className="text-xs text-slate-600 dark:text-slate-400">{field.description}</p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <span className="text-xs px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded">
                          {field.type}
                        </span>
                        {field.required && (
                          <span className="text-xs px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">
                            required
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      <span className="font-medium">Strategy:</span> {field.extraction_strategy}
                      {field.extraction_hint !== 'N/A' && (
                        <span className="ml-2">
                          <span className="font-medium">Hint:</span> {field.extraction_hint}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Extracted Data Display */}
      {extractedData && extractedData.success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-green-800 dark:text-green-200">Data Extracted Successfully!</p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Extracted {extractedData.row_count} records from {extractedData.url}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowSaveModal(true)}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
                title="Save this extraction pattern as a CSS template for faster future extractions"
              >
                <FileText className="h-4 w-4" />
                Save Template
              </button>
              <button
                onClick={handleDownloadData}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                Download JSON
              </button>
              <button
                onClick={() => {
                  setShowSaveToDBModal(true)
                  // Try to extract company name from extracted data
                  const firstRow = extractedData.table?.[0]
                  if (firstRow && 'Company Name' in firstRow) {
                    setCompanyName(String(firstRow['Company Name']))
                  } else if (firstRow && 'company_name' in firstRow) {
                    setCompanyName(String(firstRow['company_name']))
                  }
                }}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                title="Save extracted data to vector database for RAG queries"
              >
                <Database className="h-4 w-4" />
                Save to DB
              </button>
            </div>
          </div>

          {/* Data Preview */}
          {extractedData.table && extractedData.table.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 max-h-96 overflow-auto border border-slate-200 dark:border-slate-700">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Data Preview:</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-900">
                      {Object.keys(extractedData.table[0]).map((key) => (
                        <th key={key} className="px-4 py-2 text-left font-medium text-slate-700 dark:text-slate-300">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {extractedData.table.slice(0, 10).map((row, idx) => (
                      <tr key={idx} className="border-t border-slate-200 dark:border-slate-700">
                        {Object.values(row).map((value: any, colIdx) => (
                          <td key={colIdx} className="px-4 py-2 text-slate-600 dark:text-slate-400">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {extractedData.table.length > 10 && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 text-center">
                    Showing 10 of {extractedData.table.length} rows
                  </p>
                )}
              </div>
            </div>
          )}
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
                  This template will be available in CSS Selector mode
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
              <div className="bg-primary-50 dark:bg-blue-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-3">
                <p className="text-sm text-primary-700 dark:text-primary-300">
                  💡 Save this Smart Extraction pattern as a CSS template for faster extractions in the future!
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
                onClick={handleSaveAsTemplate}
                disabled={isSaving || !templateName.trim()}
                className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
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
                  Company/Entity Name *
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g., Reliance Industries, Tesla, etc."
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
                onClick={handleSaveToDB}
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
  )
}
