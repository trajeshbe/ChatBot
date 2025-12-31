import { useState, useEffect } from 'react'
import { Globe, Plus, Trash2, Loader2, CheckCircle, XCircle, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'
import axios from 'axios'

interface ScrapeJob {
  id: string
  url: string
  prompt?: string
  status: 'pending' | 'processing' | 'success' | 'error'
  documentId?: string
  title?: string
  contentLength?: number
  error?: string
  timestamp: Date
  projectId?: string
}

interface CollapsibleErrorProps {
  error: string
}

const CollapsibleError: React.FC<CollapsibleErrorProps> = ({ error }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="mb-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
      >
        <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm font-medium">Scraping error</span>
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
        </div>
      )}
    </div>
  )
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface WebScraperProps {
  sessionId?: string
  projectId?: string
}

export default function WebScraper({ sessionId, projectId }: WebScraperProps) {
  const [urls, setUrls] = useState<string[]>([''])
  const [scrapePrompt, setScrapePrompt] = useState('')
  const [jobs, setJobs] = useState<ScrapeJob[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  // Load jobs from sessionStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId) {
      const stored = sessionStorage.getItem(`scrape_jobs_${sessionId}`)
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          setJobs(parsed.map((j: any) => ({
            ...j,
            timestamp: new Date(j.timestamp)
          })))
        } catch (e) {
          console.error('Error loading scrape jobs:', e)
        }
      }
    }
  }, [sessionId])

  // Save jobs to sessionStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId && jobs.length > 0) {
      sessionStorage.setItem(`scrape_jobs_${sessionId}`, JSON.stringify(jobs))
    }
  }, [jobs, sessionId])

  const addUrlField = () => {
    setUrls([...urls, ''])
  }

  const removeUrlField = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index))
  }

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls]
    newUrls[index] = value
    setUrls(newUrls)
  }

  const handleScrape = async () => {
    const validUrls = urls.filter(url => url.trim() !== '')
    if (validUrls.length === 0) return

    setIsProcessing(true)

    // Initialize jobs with unique IDs and timestamps
    const newJobs: ScrapeJob[] = validUrls.map(url => ({
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      url,
      prompt: scrapePrompt,
      status: 'processing',
      timestamp: new Date(),
      projectId: projectId || undefined
    }))
    setJobs(prev => [...newJobs, ...prev])

    // Process each URL
    for (let i = 0; i < validUrls.length; i++) {
      try {
        const requestData = {
          url: validUrls[i],
          scrape_prompt: scrapePrompt || undefined,
          session_id: sessionId || undefined,
          project_id: projectId || undefined
        }

        // Filter out undefined values
        const cleanedData = Object.fromEntries(
          Object.entries(requestData).filter(([_, v]) => v !== undefined)
        )

        console.log(`Scraping URL ${i + 1}/${validUrls.length}:`, validUrls[i])
        console.log('Request data:', cleanedData)

        // Get auth token for user context
        const token = localStorage.getItem('access_token')

        const response = await axios.post(`${API_URL}/api/v1/scraper/scrape`, cleanedData, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        })

        console.log('Scrape response:', response.data)

        setJobs(prev =>
          prev.map(job =>
            job.url === validUrls[i] && job.status === 'processing'
              ? {
                  ...job,
                  status: 'success',
                  documentId: response.data.document_id,
                  title: response.data.title,
                  contentLength: response.data.content_length
                }
              : job
          )
        )
      } catch (error: any) {
        console.error('Scrape error:', error)
        const errorMessage = error.response?.data?.detail || error.message || 'Scraping failed'
        setJobs(prev =>
          prev.map(job =>
            job.url === validUrls[i] && job.status === 'processing'
              ? {
                  ...job,
                  status: 'error',
                  error: errorMessage
                }
              : job
          )
        )
      }
    }

    setIsProcessing(false)
    setUrls([''])
    setScrapePrompt('')
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        {/* URL Input Section */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            URLs to Scrape
          </h3>

          <div className="space-y-3 mb-4">
            {urls.map((url, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => updateUrl(index, e.target.value)}
                  placeholder="https://example.com/article"
                  className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                {urls.length > 1 && (
                  <button
                    onClick={() => removeUrlField(index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={addUrlField}
            className="flex items-center gap-2 px-4 py-2 text-primary-600 hover:bg-primary-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Another URL
          </button>

          {/* Optional Scrape Prompt */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Scraping Instructions (Optional)
            </label>
            <textarea
              value={scrapePrompt}
              onChange={(e) => setScrapePrompt(e.target.value)}
              placeholder="E.g., 'Extract only the main article content, ignore navigation and ads'"
              className="w-full resize-none rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
            />
            <p className="text-xs text-slate-500 mt-1">
              Provide instructions to guide content extraction
            </p>
          </div>

          <button
            onClick={handleScrape}
            disabled={isProcessing || urls.every(url => !url.trim())}
            className="mt-6 w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Scraping...
              </>
            ) : (
              <>
                <Globe className="w-5 h-5" />
                Start Scraping
              </>
            )}
          </button>
        </div>

        {/* Scrape Jobs List */}
        {jobs.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Scrape History ({jobs.length})
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
                        <Globe className="w-4 h-4 text-primary-600" />
                        <p className="text-sm font-medium text-slate-900 dark:text-white break-all">
                          {job.url}
                        </p>
                      </div>
                      <p className="text-xs text-slate-500">
                        {job.timestamp.toLocaleString()}
                      </p>
                      {job.title && (
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                          <strong>Title:</strong> {job.title}
                        </p>
                      )}
                      {job.contentLength && (
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          <strong>Content:</strong> {job.contentLength.toLocaleString()} characters
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {job.status === 'processing' && (
                        <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
                      )}
                      {job.status === 'success' && (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      )}
                      {job.status === 'error' && (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                  </div>

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
      </div>
    </div>
  )
}
