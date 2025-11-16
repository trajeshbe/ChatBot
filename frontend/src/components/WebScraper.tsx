import { useState } from 'react'
import { Globe, Plus, Trash2, Loader2, CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'

interface ScrapeJob {
  url: string
  prompt?: string
  status: 'pending' | 'processing' | 'success' | 'error'
  documentId?: string
  title?: string
  contentLength?: number
  error?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function WebScraper() {
  const [urls, setUrls] = useState<string[]>([''])
  const [scrapePrompt, setScrapePrompt] = useState('')
  const [jobs, setJobs] = useState<ScrapeJob[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

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

    // Initialize jobs
    const newJobs: ScrapeJob[] = validUrls.map(url => ({
      url,
      prompt: scrapePrompt,
      status: 'processing'
    }))
    setJobs(prev => [...prev, ...newJobs])

    // Process each URL
    for (let i = 0; i < validUrls.length; i++) {
      try {
        const formData = new FormData()
        formData.append('url', validUrls[i])
        if (scrapePrompt) {
          formData.append('scrape_prompt', scrapePrompt)
        }

        console.log(`Scraping URL ${i + 1}/${validUrls.length}:`, validUrls[i])

        const response = await axios.post(`${API_URL}/api/v1/scrape`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
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
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Web Scraping
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Scrape websites and add their content to the knowledge base. The content will be processed and embedded for semantic search.
        </p>

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
                  className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
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
              className="w-full resize-none rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
            <p className="text-xs text-slate-500 mt-1">
              Provide instructions to guide content extraction
            </p>
          </div>

          <button
            onClick={handleScrape}
            disabled={isProcessing || urls.every(url => !url.trim())}
            className="mt-6 w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
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
              Scrape Jobs
            </h3>
            <div className="space-y-3">
              {jobs.map((job, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Globe className="w-5 h-5 text-blue-600" />
                        <p className="font-medium text-slate-900 dark:text-white break-all">
                          {job.url}
                        </p>
                      </div>
                      {job.title && (
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                          Title: {job.title}
                        </p>
                      )}
                      {job.contentLength && (
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Content: {job.contentLength.toLocaleString()} characters
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {job.status === 'processing' && (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                          <span className="text-sm text-slate-600">Scraping...</span>
                        </>
                      )}
                      {job.status === 'success' && (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="text-sm text-green-600">Complete</span>
                        </>
                      )}
                      {job.status === 'error' && (
                        <>
                          <XCircle className="w-5 h-5 text-red-600" />
                          <span className="text-sm text-red-600">{job.error}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
