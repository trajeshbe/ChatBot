import { useState } from 'react'
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
  ChevronUp
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

export const SmartExtractor = () => {
  // State
  const [url, setUrl] = useState('')
  const [userInstructions, setUserInstructions] = useState('')
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('ollama')
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('excel')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)
  const [generatedTemplate, setGeneratedTemplate] = useState<AutoGenerateResponse | null>(null)
  const [extractedData, setExtractedData] = useState<ExtractionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [maxFields, setMaxFields] = useState(15)

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

    setIsGenerating(true)
    setError(null)
    setGeneratedTemplate(null)

    try {
      const response = await axios.post<AutoGenerateResponse>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/auto-generate`,
        {
          url,
          user_instructions: userInstructions,
          llm_provider: llmProvider,
          max_fields: maxFields
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

    setIsExtracting(true)
    setError(null)
    setExtractedData(null)

    try {
      const response = await axios.post<ExtractionResponse>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/extract/smart-extract`,
        {
          url,
          user_instructions: userInstructions,
          llm_provider: llmProvider,
          output_format: outputFormat
        }
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

    const dataStr = JSON.stringify(extractedData.data, null, 2)
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

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 mb-6 border border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Smart Extractor</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Extract data with AI - no template needed! Just describe what you want.
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
          className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent placeholder-slate-400"
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
          className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none placeholder-slate-400"
        />

        {/* Example Prompts */}
        <div className="mt-3">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Try these examples:</p>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => useExamplePrompt(prompt)}
                className="text-xs px-3 py-1 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors"
              >
                {prompt.substring(0, 50)}...
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Settings Row */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        {/* LLM Provider */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            AI Provider
          </label>
          <select
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value as LLMProvider)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="ollama">Ollama (Local)</option>
            <option value="openai">OpenAI GPT-4</option>
            <option value="anthropic">Anthropic Claude</option>
          </select>
        </div>

        {/* Output Format */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Output Format
          </label>
          <select
            value={outputFormat}
            onChange={(e) => setOutputFormat(e.target.value as OutputFormat)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="excel">Excel (.xlsx)</option>
            <option value="csv">CSV (.csv)</option>
            <option value="json">JSON (.json)</option>
          </select>
        </div>

        {/* Max Fields */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Max Fields
          </label>
          <input
            type="number"
            value={maxFields}
            onChange={(e) => setMaxFields(parseInt(e.target.value))}
            min={1}
            max={30}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
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
              <p className="mb-2 font-medium text-slate-700 dark:text-slate-300">Two-Step Workflow:</p>
              <p className="mb-4">
                You can either generate a template first to review it, or directly extract data in one step.
              </p>

              <button
                onClick={handleAutoGenerate}
                disabled={isGenerating || !url || !userInstructions}
                className="w-full mb-2 px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
          className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold shadow-md"
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
                        <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
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
            <button
              onClick={handleDownloadData}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Download JSON
            </button>
          </div>

          {/* Data Preview */}
          {extractedData.data && extractedData.data.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 max-h-96 overflow-auto border border-slate-200 dark:border-slate-700">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Data Preview:</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-900">
                      {Object.keys(extractedData.data[0]).map((key) => (
                        <th key={key} className="px-4 py-2 text-left font-medium text-slate-700 dark:text-slate-300">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {extractedData.data.slice(0, 10).map((row, idx) => (
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
                {extractedData.data.length > 10 && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 text-center">
                    Showing 10 of {extractedData.data.length} rows
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
