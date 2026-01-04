/**
 * Tier 2 Module Interface Template
 *
 * Reusable base component for tier 2 domain vertical modules.
 * Provides standardized UI patterns for:
 * - JSON input (structured data)
 * - File upload (CSV, TXT, JSON, PDF)
 * - Loading states
 * - Error handling
 * - Results display
 * - Empty states
 *
 * Usage: Copy this template and customize for each module
 */

import { useState, useRef } from 'react'
import axios from 'axios'
import { Upload, Loader2, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import ExportWizardButton from '../ExportWizardButton'

interface ModuleInterfaceTemplateProps {
  // Module metadata
  moduleId: string
  moduleName: string
  moduleDescription: string
  moduleIcon?: string

  // API configuration
  apiEndpoint: string

  // Input configuration
  acceptedFileTypes?: string  // e.g., ".csv,.json,.txt"
  showJsonInput?: boolean
  showFileUpload?: boolean
  jsonPlaceholder?: string

  // Custom components (optional)
  InputComponent?: React.ComponentType<any>
  ResultsComponent?: React.ComponentType<any>
}

export default function ModuleInterfaceTemplate({
  moduleId,
  moduleName,
  moduleDescription,
  moduleIcon = '🔧',
  apiEndpoint,
  acceptedFileTypes = '.csv,.json,.txt',
  showJsonInput = true,
  showFileUpload = true,
  jsonPlaceholder = 'Enter JSON input...',
  InputComponent,
  ResultsComponent
}: ModuleInterfaceTemplateProps) {
  const [jsonInput, setJsonInput] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      let response

      if (selectedFile) {
        // File upload
        const formData = new FormData()
        formData.append('file', selectedFile)
        formData.append('session_id', sessionStorage.getItem('chat_session_id') || 'default')

        response = await axios.post(apiEndpoint, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      } else if (jsonInput.trim()) {
        // JSON input
        const data = JSON.parse(jsonInput)
        response = await axios.post(apiEndpoint, data)
      } else {
        setError('Please provide either a file or JSON input')
        setLoading(false)
        return
      }

      setResult(response.data)
    } catch (err: any) {
      console.error('Module error:', err)
      setError(err.response?.data?.detail || err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setJsonInput('')
    setSelectedFile(null)
    setResult(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start mb-2">
            <h1 className="text-3xl font-bold text-slate-800">
              {moduleIcon} {moduleName}
            </h1>
            <ExportWizardButton
              moduleCode={moduleId}
              moduleName={moduleName}
              tier={2}
              variant="button"
              size="md"
            />
          </div>
          <p className="text-slate-600">{moduleDescription}</p>
          <div className="mt-2 px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium inline-block">
            Tier 2 Module • {moduleId}
          </div>
        </div>

        {/* Input Section */}
        {InputComponent ? (
          <InputComponent
            onSubmit={handleSubmit}
            loading={loading}
            setError={setError}
          />
        ) : (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Input</h2>

            {/* JSON Input */}
            {showJsonInput && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  JSON Input
                </label>
                <textarea
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  placeholder={jsonPlaceholder}
                  disabled={loading || selectedFile !== null}
                  className="w-full h-32 px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:bg-slate-50 disabled:text-slate-400 font-mono text-sm"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Enter structured JSON data following the API schema
                </p>
              </div>
            )}

            {/* File Upload */}
            {showFileUpload && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Or Upload File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={acceptedFileTypes}
                  onChange={handleFileSelect}
                  disabled={loading || jsonInput.trim() !== ''}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading || jsonInput.trim() !== ''}
                  className="w-full py-4 px-4 border-2 border-dashed border-slate-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {selectedFile ? (
                    <>
                      <FileText className="w-5 h-5 text-blue-600" />
                      <span className="text-blue-700 font-medium">{selectedFile.name}</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5 text-slate-500" />
                      <span className="text-slate-600">Click to upload ({acceptedFileTypes.replace(/\./g, '').toUpperCase()})</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleSubmit}
                disabled={loading || (!jsonInput.trim() && !selectedFile)}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Process
                  </>
                )}
              </button>

              <button
                onClick={handleReset}
                disabled={loading}
                className="px-6 py-3 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 disabled:bg-slate-100 disabled:cursor-not-allowed transition-colors font-medium"
              >
                Reset
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-red-900">Error</div>
              <div className="text-sm text-red-700">{error}</div>
            </div>
          </div>
        )}

        {/* Results Display */}
        {result && (
          ResultsComponent ? (
            <ResultsComponent result={result} />
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Results</h2>
              <pre className="bg-slate-50 p-4 rounded-lg overflow-auto max-h-96 text-sm">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )
        )}

        {/* Empty State */}
        {!result && !loading && !error && (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="text-6xl mb-4">{moduleIcon}</div>
            <h3 className="text-xl font-semibold text-slate-800 mb-2">
              Ready to process
            </h3>
            <p className="text-slate-600">
              Provide input data to get started with {moduleName}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
