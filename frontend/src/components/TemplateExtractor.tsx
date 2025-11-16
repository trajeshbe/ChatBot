import { useState, useEffect, useRef } from 'react'
import { FileSpreadsheet, Globe, Download, Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp, AlertCircle, Upload, FileUp } from 'lucide-react'
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
}

interface UploadedTemplate {
  template_id: string
  name: string
  description?: string
  fields_count: number
  created_at: string
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

export default function TemplateExtractor({ sessionId }: { sessionId: string }) {
  const [url, setUrl] = useState('')
  const [preset, setPreset] = useState('screener_in')
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobs, setJobs] = useState<ExtractionJob[]>([])
  const [availablePresets, setAvailablePresets] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isUploadingTemplate, setIsUploadingTemplate] = useState(false)
  const [uploadedTemplates, setUploadedTemplates] = useState<UploadedTemplate[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  // Load available presets
  useEffect(() => {
    const loadPresets = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/extract/presets`)
        setAvailablePresets(response.data.presets || [])
      } catch (error) {
        console.error('Error loading presets:', error)
      }
    }
    loadPresets()
  }, [])

  const handleExtract = async () => {
    if (!url.trim()) return

    setIsProcessing(true)
    setError(null)

    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const newJob: ExtractionJob = {
      id: jobId,
      url,
      preset,
      status: 'processing',
      timestamp: new Date()
    }

    setJobs(prev => [newJob, ...prev])

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/extract/preset/${preset}`,
        {
          url,
          session_id: sessionId
        }
      )

      if (response.data.success) {
        setJobs(prev =>
          prev.map(job =>
            job.id === jobId
              ? {
                  ...job,
                  status: 'success',
                  data: response.data.data
                }
              : job
          )
        )
        setUrl('')
      } else {
        throw new Error(response.data.error || 'Extraction failed')
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Extraction failed'
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

  const handleExportToExcel = async (data: any[], filename: string) => {
    try {
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
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Error exporting to Excel:', error)
      alert('Failed to export to Excel')
    }
  }

  const handleTemplateUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Please upload an Excel file (.xlsx or .xls)')
      return
    }

    setIsUploadingTemplate(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('template_name', file.name)

      const response = await axios.post(
        `${API_URL}/api/v1/extraction/templates/upload-excel`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      if (response.data) {
        setUploadedTemplates(prev => [response.data, ...prev])
        alert(`Template "${response.data.name}" uploaded successfully with ${response.data.fields_count} columns!`)
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload template'
      setError(errorMessage)
      console.error('Error uploading template:', error)
    } finally {
      setIsUploadingTemplate(false)
    }
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Template-based Data Extraction
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Extract structured data from websites using predefined templates. Perfect for scraping financial data, product catalogs, and more.
        </p>

        {/* Global Error (Collapsible) */}
        {error && (
          <CollapsibleError
            error={error}
            onDismiss={() => setError(null)}
          />
        )}

        {/* Extraction Form */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            Extract Data
          </h3>

          {/* Template Upload Section */}
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <FileUp className="w-5 h-5 text-blue-600" />
                  Upload Excel Template
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  Upload an Excel file with column headers. The system will extract data and populate those columns automatically.
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleTemplateUpload}
                className="hidden"
                id="template-upload"
              />
              <label
                htmlFor="template-upload"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploadingTemplate ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Choose Excel File
                  </>
                )}
              </label>
            </div>
            {uploadedTemplates.length > 0 && (
              <div className="mt-3 p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Uploaded Templates ({uploadedTemplates.length}):
                </p>
                <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                  {uploadedTemplates.slice(0, 3).map((template) => (
                    <li key={template.template_id} className="flex items-center gap-2">
                      <CheckCircle className="w-3 h-3 text-green-600" />
                      {template.name} ({template.fields_count} columns)
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Preset Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Or Use a Preset Template
            </label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availablePresets.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.display_name} - {p.description}
                </option>
              ))}
            </select>
            {availablePresets.find(p => p.name === preset) && (
              <p className="text-xs text-slate-500 mt-1">
                Extracts: {availablePresets.find(p => p.name === preset)?.fields.join(', ')}
              </p>
            )}
          </div>

          {/* URL Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              URL to Extract
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.screener.in/company/BHARTIARTL/consolidated/"
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleExtract}
            disabled={isProcessing || !url.trim()}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
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
                  className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Globe className="w-4 h-4 text-blue-600" />
                        <p className="text-sm font-medium text-slate-900 dark:text-white break-all">
                          {job.url}
                        </p>
                      </div>
                      <p className="text-xs text-slate-500">
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
                          {job.data && (
                            <button
                              onClick={() => handleExportToExcel(
                                job.data!,
                                `extraction_${new Date().getTime()}.xlsx`
                              )}
                              className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors flex items-center gap-1"
                            >
                              <Download className="w-3 h-3" />
                              Export Excel
                            </button>
                          )}
                        </>
                      )}
                      {job.status === 'error' && (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                  </div>

                  {/* Success: Show extracted data preview */}
                  {job.status === 'success' && job.data && job.data.length > 0 && (
                    <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700">
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Extracted {job.data.length} row(s)
                      </p>
                      <div className="text-xs font-mono text-slate-600 dark:text-slate-400 overflow-x-auto">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(job.data[0], null, 2)}
                        </pre>
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
          <div className="text-center py-12 text-slate-500">
            <FileSpreadsheet className="w-16 h-16 mx-auto mb-3 opacity-50" />
            <p className="text-lg">No extraction jobs yet</p>
            <p className="text-sm mt-1">Enter a URL above to start extracting data</p>
          </div>
        )}
      </div>
    </div>
  )
}
