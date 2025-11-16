import { useState, useEffect } from 'react'
import {
  Globe, Plus, Trash2, Loader2, CheckCircle, XCircle,
  Settings, ChevronDown, ChevronUp, Info
} from 'lucide-react'
import axios from 'axios'

interface ScrapeJob {
  url: string
  prompt?: string
  strategy?: string
  status: 'pending' | 'processing' | 'success' | 'error'
  documentId?: string
  title?: string
  contentLength?: number
  strategyUsed?: string
  error?: string
}

interface ScraperCapabilities {
  web_scraping_enabled: boolean
  playwright_enabled: boolean
  smart_scraping_enabled: boolean
  available_strategies: string[]
  default_strategy: string
  max_concurrent_requests: number
  configuration: {
    timeout: number
    max_retries: number
    min_content_length: number
    javascript_enabled: boolean
  }
}

interface ScraperConfig {
  strategy?: string
  timeout?: number
  max_retries?: number
  include_links?: boolean
  include_tables?: boolean
  include_images?: boolean
  include_metadata?: boolean
  remove_nav?: boolean
  remove_footer?: boolean
  remove_header?: boolean
  enable_javascript?: boolean
  min_content_length?: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const STRATEGY_DESCRIPTIONS: Record<string, string> = {
  auto: 'Automatically selects the best strategy based on URL',
  trafilatura: 'Best for articles and blog posts',
  beautifulsoup: 'General purpose HTML parsing',
  playwright: 'For JavaScript-heavy sites (requires Playwright)',
  hybrid: 'Tries multiple strategies for best results'
}

export default function WebScraperEnhanced() {
  const [urls, setUrls] = useState<string[]>([''])
  const [scrapePrompt, setScrapePrompt] = useState('')
  const [jobs, setJobs] = useState<ScrapeJob[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Scraper capabilities
  const [capabilities, setCapabilities] = useState<ScraperCapabilities | null>(null)
  const [loadingCapabilities, setLoadingCapabilities] = useState(true)

  // Advanced configuration
  const [config, setConfig] = useState<ScraperConfig>({
    strategy: 'auto',
    timeout: 30,
    max_retries: 3,
    include_links: true,
    include_tables: true,
    include_images: false,
    include_metadata: true,
    remove_nav: true,
    remove_footer: true,
    remove_header: true,
    enable_javascript: false,
    min_content_length: 100
  })

  // Load scraper capabilities
  useEffect(() => {
    loadCapabilities()
  }, [])

  const loadCapabilities = async () => {
    try {
      setLoadingCapabilities(true)
      const response = await axios.get(`${API_URL}/api/v1/scraper/capabilities`)
      setCapabilities(response.data)

      // Update config defaults from capabilities
      if (response.data.default_strategy) {
        setConfig(prev => ({ ...prev, strategy: response.data.default_strategy }))
      }
    } catch (error) {
      console.error('Error loading scraper capabilities:', error)
      // Fallback to basic scraper if enhanced API not available
      setCapabilities(null)
    } finally {
      setLoadingCapabilities(false)
    }
  }

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
      strategy: config.strategy,
      status: 'processing'
    }))
    setJobs(prev => [...prev, ...newJobs])

    // Check if enhanced scraper is available
    const useEnhancedScraper = capabilities?.web_scraping_enabled

    if (useEnhancedScraper) {
      // Use enhanced scraper API
      await handleEnhancedScrape(validUrls)
    } else {
      // Fallback to basic scraper
      await handleBasicScrape(validUrls)
    }

    setIsProcessing(false)
    setUrls([''])
    setScrapePrompt('')
  }

  const handleEnhancedScrape = async (validUrls: string[]) => {
    // Use bulk scrape endpoint for efficiency
    try {
      const requestBody = {
        urls: validUrls,
        scrape_prompt: scrapePrompt || undefined,
        strategy: config.strategy,
        config: {
          timeout: config.timeout,
          max_retries: config.max_retries,
          include_links: config.include_links,
          include_tables: config.include_tables,
          include_images: config.include_images,
          include_metadata: config.include_metadata,
          remove_nav: config.remove_nav,
          remove_footer: config.remove_footer,
          remove_header: config.remove_header,
          enable_javascript: config.enable_javascript,
          min_content_length: config.min_content_length
        },
        session_id: localStorage.getItem('sessionId') || undefined
      }

      const response = await axios.post(`${API_URL}/api/v1/scraper/scrape/bulk`, requestBody, {
        headers: {
          'Content-Type': 'application/json'
        }
      })

      // Update job statuses
      const results = response.data.results || []
      results.forEach((result: any) => {
        setJobs(prev =>
          prev.map(job =>
            job.url === result.url && job.status === 'processing'
              ? {
                  ...job,
                  status: result.success ? 'success' : 'error',
                  documentId: result.document_id,
                  title: result.title,
                  contentLength: result.content_length,
                  strategyUsed: result.strategy_used,
                  error: result.error
                }
              : job
          )
        )
      })
    } catch (error) {
      console.error('Enhanced scrape error:', error)
      // Mark all jobs as error
      validUrls.forEach(url => {
        setJobs(prev =>
          prev.map(job =>
            job.url === url && job.status === 'processing'
              ? {
                  ...job,
                  status: 'error',
                  error: 'Scraping failed'
                }
              : job
          )
        )
      })
    }
  }

  const handleBasicScrape = async (validUrls: string[]) => {
    // Fallback to basic scraper
    for (let i = 0; i < validUrls.length; i++) {
      try {
        const formData = new FormData()
        formData.append('url', validUrls[i])
        if (scrapePrompt) {
          formData.append('scrape_prompt', scrapePrompt)
        }

        const response = await axios.post(`${API_URL}/api/v1/scrape`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

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
      } catch (error) {
        console.error('Scrape error:', error)
        setJobs(prev =>
          prev.map(job =>
            job.url === validUrls[i] && job.status === 'processing'
              ? {
                  ...job,
                  status: 'error',
                  error: 'Scraping failed'
                }
              : job
          )
        )
      }
    }
  }

  const resetConfig = () => {
    setConfig({
      strategy: capabilities?.default_strategy || 'auto',
      timeout: capabilities?.configuration.timeout || 30,
      max_retries: capabilities?.configuration.max_retries || 3,
      include_links: true,
      include_tables: true,
      include_images: false,
      include_metadata: true,
      remove_nav: true,
      remove_footer: true,
      remove_header: true,
      enable_javascript: capabilities?.configuration.javascript_enabled || false,
      min_content_length: capabilities?.configuration.min_content_length || 100
    })
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Web Scraping
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
            Scrape websites and add their content to the knowledge base with advanced options.
          </p>

          {/* Capabilities Info */}
          {capabilities && (
            <div className="mt-3 flex items-center gap-2 text-sm">
              <Info className="w-4 h-4 text-blue-500" />
              <span className="text-slate-600 dark:text-slate-400">
                {capabilities.available_strategies.length} strategies available
                {capabilities.smart_scraping_enabled && ' • Smart scraping enabled'}
                {capabilities.playwright_enabled && ' • JavaScript rendering available'}
              </span>
            </div>
          )}
        </div>

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

          {/* Scraping Strategy */}
          {capabilities && capabilities.available_strategies.length > 0 && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Scraping Strategy
              </label>
              <select
                value={config.strategy}
                onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {capabilities.available_strategies.map(strategy => (
                  <option key={strategy} value={strategy}>
                    {strategy.charAt(0).toUpperCase() + strategy.slice(1)} - {STRATEGY_DESCRIPTIONS[strategy] || 'Custom strategy'}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Optional Scrape Prompt */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Scraping Instructions (Optional)
              {capabilities?.smart_scraping_enabled && (
                <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">
                  AI-powered filtering enabled
                </span>
              )}
            </label>
            <textarea
              value={scrapePrompt}
              onChange={(e) => setScrapePrompt(e.target.value)}
              placeholder="E.g., 'Extract only information about AI and machine learning'"
              className="w-full resize-none rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
            <p className="text-xs text-slate-500 mt-1">
              Provide instructions to guide content extraction
            </p>
          </div>

          {/* Advanced Settings */}
          {capabilities && (
            <div className="mt-6">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
              >
                <Settings className="w-4 h-4" />
                Advanced Settings
                {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showAdvanced && (
                <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-4">
                  {/* Timeout and Retries */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Timeout (seconds)
                      </label>
                      <input
                        type="number"
                        value={config.timeout}
                        onChange={(e) => setConfig({ ...config, timeout: Number(e.target.value) })}
                        min="1"
                        max="300"
                        className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Max Retries
                      </label>
                      <input
                        type="number"
                        value={config.max_retries}
                        onChange={(e) => setConfig({ ...config, max_retries: Number(e.target.value) })}
                        min="0"
                        max="10"
                        className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  {/* Content Extraction Options */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Content Extraction
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.include_links}
                          onChange={(e) => setConfig({ ...config, include_links: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Include links
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.include_tables}
                          onChange={(e) => setConfig({ ...config, include_tables: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Include tables
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.include_images}
                          onChange={(e) => setConfig({ ...config, include_images: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Include images
                      </label>
                    </div>
                  </div>

                  {/* Content Filtering */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Content Filtering
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.remove_nav}
                          onChange={(e) => setConfig({ ...config, remove_nav: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Remove navigation
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.remove_header}
                          onChange={(e) => setConfig({ ...config, remove_header: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Remove headers
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.remove_footer}
                          onChange={(e) => setConfig({ ...config, remove_footer: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Remove footers
                      </label>
                    </div>
                  </div>

                  {/* JavaScript Rendering (if available) */}
                  {capabilities.playwright_enabled && (
                    <div>
                      <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={config.enable_javascript}
                          onChange={(e) => setConfig({ ...config, enable_javascript: e.target.checked })}
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        Enable JavaScript rendering (slower)
                      </label>
                      <p className="text-xs text-slate-500 mt-1 ml-6">
                        Use Playwright for JavaScript-heavy sites
                      </p>
                    </div>
                  )}

                  {/* Min Content Length */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Minimum Content Length (characters)
                    </label>
                    <input
                      type="number"
                      value={config.min_content_length}
                      onChange={(e) => setConfig({ ...config, min_content_length: Number(e.target.value) })}
                      min="0"
                      max="10000"
                      className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Reset Button */}
                  <button
                    onClick={resetConfig}
                    className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    Reset to defaults
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Scrape Button */}
          <button
            onClick={handleScrape}
            disabled={isProcessing || urls.every(url => !url.trim()) || loadingCapabilities}
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
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                          Content: {job.contentLength.toLocaleString()} characters
                        </p>
                      )}
                      {job.strategyUsed && (
                        <p className="text-xs text-slate-500 dark:text-slate-500">
                          Strategy: {job.strategyUsed}
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
