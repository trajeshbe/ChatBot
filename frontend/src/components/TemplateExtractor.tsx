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
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [templateSource, setTemplateSource] = useState<'preset' | 'uploaded'>('preset')
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

  // Load uploaded Excel templates
  useEffect(() => {
    const loadUploadedTemplates = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/extraction/templates`)
        setUploadedTemplates(response.data || [])
      } catch (error) {
        console.error('Error loading uploaded templates:', error)
      }
    }
    loadUploadedTemplates()
  }, [])

  const handleExtract = async () => {
    if (!url.trim()) return

    setIsProcessing(true)
    setError(null)

    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const newJob: ExtractionJob = {
      id: jobId,
      url,
      preset: templateSource === 'preset' ? preset : selectedTemplateId,
      status: 'processing',
      timestamp: new Date()
    }

    setJobs(prev => [newJob, ...prev])

    try {
      let response

      if (templateSource === 'uploaded' && selectedTemplateId) {
        // Use the new extraction jobs endpoint with template_id
        response = await axios.post(
          `${API_URL}/api/v1/extraction/jobs`,
          {
            urls: [url],
            template_id: selectedTemplateId,
            output_format: 'excel',
            delivery_method: 'download',
            session_id: sessionId
          }
        )

        // Poll for job completion
        const extractionJobId = response.data.job_id
        let attempts = 0
        const maxAttempts = 60 // 60 attempts * 2 seconds = 2 minutes max

        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 2000))

          const statusResponse = await axios.get(
            `${API_URL}/api/v1/extraction/jobs/${extractionJobId}`
          )

          const status = statusResponse.data.status

          if (status === 'completed' || status === 'completed_with_errors') {
            // Get the result
            const resultResponse = await axios.get(
              `${API_URL}/api/v1/extraction/jobs/${extractionJobId}/result`
            )

            setJobs(prev =>
              prev.map(job =>
                job.id === jobId
                  ? {
                      ...job,
                      status: 'success',
                      data: [{
                        job_id: extractionJobId,
                        records_extracted: resultResponse.data.records_extracted,
                        quality_score: resultResponse.data.quality_score,
                        download_url: resultResponse.data.download_url
                      }]
                    }
                  : job
              )
            )
            setUrl('')
            return
          } else if (status === 'failed') {
            throw new Error('Extraction job failed')
          }

          attempts++
        }

        throw new Error('Extraction job timed out')

      } else {
        // Use preset template endpoint (existing behavior)
        response = await axios.post(
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
        // Reload all templates to get the latest list
        const templatesResponse = await axios.get(`${API_URL}/api/v1/extraction/templates`)
        setUploadedTemplates(templatesResponse.data || [])

        // Select the newly uploaded template
        setSelectedTemplateId(response.data.template_id)
        setTemplateSource('uploaded')

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
    <div className="h-full p-6 overflow-y-auto bg-slate-50 dark:bg-slate-900">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Template-based Data Extraction
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Extract structured data from websites using predefined templates or your own Excel templates.
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

          {/* Template Upload Section */}
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <FileUp className="w-5 h-5 text-blue-600" />
                  Upload Excel Template
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  Upload an Excel file with column headers. The AI will extract data and populate those columns automatically.
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
                disabled={isUploadingTemplate}
              />
              <label
                htmlFor="template-upload"
                className={`flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer flex items-center justify-center gap-2 ${isUploadingTemplate ? 'opacity-50 cursor-not-allowed' : ''}`}
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
              <div className="mt-3 p-3 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Available Templates ({uploadedTemplates.length}):
                </p>
                <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1 max-h-24 overflow-y-auto">
                  {uploadedTemplates.map((template) => (
                    <div key={template.template_id} className="flex items-center gap-2">
                      <CheckCircle className="w-3 h-3 text-green-600 flex-shrink-0" />
                      <span className="flex-1">{template.name} ({template.fields_count} columns)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Template Source Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Choose Template Source
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="templateSource"
                  value="preset"
                  checked={templateSource === 'preset'}
                  onChange={() => setTemplateSource('preset')}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">Preset Templates</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="templateSource"
                  value="uploaded"
                  checked={templateSource === 'uploaded'}
                  onChange={() => setTemplateSource('uploaded')}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                  disabled={uploadedTemplates.length === 0}
                />
                <span className={`text-sm ${uploadedTemplates.length === 0 ? 'text-slate-400 dark:text-slate-600' : 'text-slate-700 dark:text-slate-300'}`}>
                  Uploaded Excel Templates {uploadedTemplates.length === 0 && '(Upload one first)'}
                </span>
              </label>
            </div>
          </div>

          {/* Template Selection based on source */}
          {templateSource === 'preset' ? (
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
                    {p.display_name} - {p.description}
                  </option>
                ))}
              </select>
              {availablePresets.find(p => p.name === preset) && (
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Extracts: {availablePresets.find(p => p.name === preset)?.fields.join(', ')}
                </p>
              )}
            </div>
          ) : (
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Select Uploaded Template
              </label>
              <select
                value={selectedTemplateId}
                onChange={(e) => setSelectedTemplateId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select a template --</option>
                {uploadedTemplates.map((template) => (
                  <option key={template.template_id} value={template.template_id}>
                    {template.name} ({template.fields_count} columns)
                  </option>
                ))}
              </select>
              {selectedTemplateId && uploadedTemplates.find(t => t.template_id === selectedTemplateId) && (
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {uploadedTemplates.find(t => t.template_id === selectedTemplateId)?.description || 'AI will intelligently map data to your Excel columns'}
                </p>
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
            disabled={isProcessing || !url.trim() || (templateSource === 'uploaded' && !selectedTemplateId)}
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
                        Template: {availablePresets.find(p => p.name === job.preset)?.display_name || uploadedTemplates.find(t => t.template_id === job.preset)?.name || job.preset}
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
                              {job.data[0].download_url ? (
                                <a
                                  href={`${API_URL}${job.data[0].download_url}`}
                                  download
                                  className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
                                >
                                  <Download className="w-3 h-3" />
                                  Download Excel
                                </a>
                              ) : (
                                <button
                                  onClick={() => handleExportToExcel(
                                    job.data!,
                                    `extraction_${new Date().getTime()}.xlsx`
                                  )}
                                  className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
                                >
                                  <Download className="w-3 h-3" />
                                  Export Excel
                                </button>
                              )}
                            </>
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
                        {job.data[0].records_extracted !== undefined ? (
                          <>Extracted {job.data[0].records_extracted} record(s) • Quality: {(job.data[0].quality_score * 100).toFixed(0)}%</>
                        ) : (
                          <>Extracted {job.data.length} row(s)</>
                        )}
                      </p>
                      {!job.data[0].download_url && (
                        <div className="text-xs font-mono text-slate-600 dark:text-slate-400 overflow-x-auto">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(job.data[0], null, 2)}
                          </pre>
                        </div>
                      )}
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
            <p className="text-sm text-slate-500 dark:text-slate-500 mt-1">Upload an Excel template or select a preset, then enter a URL to start extracting data</p>
          </div>
        )}
      </div>
    </div>
  )
}
