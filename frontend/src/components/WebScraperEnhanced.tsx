import { useState, useEffect } from 'react'
import {
  Globe,
  Plus,
  Trash2,
  Loader2,
  CheckCircle,
  XCircle,
  Settings,
  Download,
  AlertCircle,
  RefreshCw,
  FileText,
  Lock,
  Zap,
  BarChart3,
  Mail,
  Webhook,
  Database,
  Clock,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react'
import axios from 'axios'

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

type ComplianceLevel = 'strict' | 'balanced' | 'aggressive'
type LLMProvider = 'ollama' | 'openai' | 'anthropic'
type ScrapingStrategy = 'auto' | 'trafilatura' | 'beautifulsoup' | 'playwright' | 'hybrid'
type AuthType = 'none' | 'basic' | 'bearer' | 'api_key' | 'oauth2' | 'jwt' | 'session' | 'custom'
type OutputFormat = 'excel' | 'csv' | 'json' | 'xml' | 'parquet'
type DeliveryMethod = 'download' | 'email' | 'webhook' | 'storage'
type JobStatus = 'pending' | 'running' | 'completed' | 'failed'
type ScraperMode = 'basic' | 'template' | 'monitor'

interface ScrapeJob {
  url: string
  prompt?: string
  status: 'pending' | 'processing' | 'success' | 'error'
  documentId?: string
  title?: string
  contentLength?: number
  scrapingTime?: number
  strategyUsed?: string
  error?: string
}

interface ExtractionJob {
  job_id: string
  status: JobStatus
  current_step?: string
  progress_percentage?: number
  urls_total?: number
  urls_processed?: number
  successful_scrapes?: number
  failed_scrapes?: number
  records_extracted?: number
  quality_score?: number
  output_file_path?: string
  delivery_success?: boolean
  errors?: string[]
  warnings?: string[]
  started_at?: string
  completed_at?: string
  total_duration_seconds?: number
  output_format?: OutputFormat
  delivery_method?: DeliveryMethod
}

interface AdvancedConfig {
  timeout: number
  max_retries: number
  include_links: boolean
  include_tables: boolean
  include_images: boolean
  include_metadata: boolean
  remove_nav: boolean
  remove_footer: boolean
  remove_header: boolean
  remove_ads: boolean
  enable_javascript: boolean
  wait_for_selector: string
  wait_timeout: number
  min_content_length: number
}

interface AuthConfig {
  auth_type: AuthType
  credentials: Record<string, string>
}

interface DeliveryConfig {
  email_to?: string[]
  webhook_url?: string
  storage_provider?: string
  storage_bucket?: string
  storage_path?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const STRATEGY_DESCRIPTIONS: Record<string, string> = {
  auto: 'Automatically selects the best strategy based on URL',
  trafilatura: 'Best for articles and blog posts',
  beautifulsoup: 'General purpose HTML parsing',
  playwright: 'For JavaScript-heavy sites (requires Playwright)',
  hybrid: 'Tries multiple strategies for best results'
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function WebScraperEnhanced() {
  const [mode, setMode] = useState<ScraperMode>('basic')

  return (
    <div className="h-full flex flex-col bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
          Enterprise Web Scraper
        </h2>
        <p className="text-slate-600 dark:text-slate-400 text-sm">
          Advanced web scraping with compliance controls, LLM integration, and structured extraction
        </p>
      </div>

      {/* Mode Tabs */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6">
        <div className="flex gap-1">
          <TabButton
            active={mode === 'basic'}
            onClick={() => setMode('basic')}
            icon={<Globe className="w-4 h-4" />}
            label="Basic Scraping"
          />
          <TabButton
            active={mode === 'template'}
            onClick={() => setMode('template')}
            icon={<FileText className="w-4 h-4" />}
            label="Template Extraction"
          />
          <TabButton
            active={mode === 'monitor'}
            onClick={() => setMode('monitor')}
            icon={<BarChart3 className="w-4 h-4" />}
            label="Job Monitor"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {mode === 'basic' && <BasicScrapingTab />}
        {mode === 'template' && <TemplateExtractionTab />}
        {mode === 'monitor' && <JobMonitorTab />}
      </div>
    </div>
  )
}

// ============================================================================
// TAB BUTTON COMPONENT
// ============================================================================

interface TabButtonProps {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}

function TabButton({ active, onClick, icon, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-4 py-3 border-b-2 transition-colors
        ${
          active
            ? 'border-blue-600 text-blue-600 dark:border-blue-500 dark:text-blue-500'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
        }
      `}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  )
}

// ============================================================================
// BASIC SCRAPING TAB
// ============================================================================

function BasicScrapingTab() {
  const [sessionId] = useState(() => localStorage.getItem('sessionId') || undefined)

  // Initialize state from localStorage with defaults
  const [urls, setUrls] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('webScraper_basic_urls')
      return saved ? JSON.parse(saved) : ['']
    } catch {
      return ['']
    }
  })

  const [scrapePrompt, setScrapePrompt] = useState(() => {
    return localStorage.getItem('webScraper_basic_prompt') || ''
  })

  const [jobs, setJobs] = useState<ScrapeJob[]>(() => {
    try {
      const saved = localStorage.getItem('webScraper_basic_jobs')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  const [isProcessing, setIsProcessing] = useState(false)

  // Phase 1 Settings
  const [complianceLevel, setComplianceLevel] = useState<ComplianceLevel>(() => {
    const saved = localStorage.getItem('webScraper_basic_complianceLevel')
    return (saved as ComplianceLevel) || 'balanced'
  })

  const [enableSmartScraping, setEnableSmartScraping] = useState(() => {
    const saved = localStorage.getItem('webScraper_basic_enableSmartScraping')
    return saved !== null ? saved === 'true' : true
  })

  const [llmProvider, setLLMProvider] = useState<LLMProvider>(() => {
    const saved = localStorage.getItem('webScraper_basic_llmProvider')
    return (saved as LLMProvider) || 'ollama'
  })

  const [showAuthConfig, setShowAuthConfig] = useState(false)

  const [authConfig, setAuthConfig] = useState<AuthConfig>(() => {
    try {
      const saved = localStorage.getItem('webScraper_basic_authConfig')
      return saved ? JSON.parse(saved) : { auth_type: 'none', credentials: {} }
    } catch {
      return { auth_type: 'none', credentials: {} }
    }
  })

  // Phase 2 Settings
  const [strategy, setStrategy] = useState<ScrapingStrategy>(() => {
    const saved = localStorage.getItem('webScraper_basic_strategy')
    return (saved as ScrapingStrategy) || 'auto'
  })

  const [showAdvanced, setShowAdvanced] = useState(false)

  const [advancedConfig, setAdvancedConfig] = useState<AdvancedConfig>(() => {
    try {
      const saved = localStorage.getItem('webScraper_basic_advancedConfig')
      return saved ? JSON.parse(saved) : {
        timeout: 30.0,
        max_retries: 3,
        include_links: true,
        include_tables: true,
        include_images: false,
        include_metadata: true,
        remove_nav: true,
        remove_footer: true,
        remove_header: true,
        remove_ads: true,
        enable_javascript: false,
        wait_for_selector: '',
        wait_timeout: 10.0,
        min_content_length: 100
      }
    } catch {
      return {
        timeout: 30.0,
        max_retries: 3,
        include_links: true,
        include_tables: true,
        include_images: false,
        include_metadata: true,
        remove_nav: true,
        remove_footer: true,
        remove_header: true,
        remove_ads: true,
        enable_javascript: false,
        wait_for_selector: '',
        wait_timeout: 10.0,
        min_content_length: 100
      }
    }
  })

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('webScraper_basic_urls', JSON.stringify(urls))
  }, [urls])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_prompt', scrapePrompt)
  }, [scrapePrompt])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_jobs', JSON.stringify(jobs))
  }, [jobs])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_complianceLevel', complianceLevel)
  }, [complianceLevel])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_enableSmartScraping', String(enableSmartScraping))
  }, [enableSmartScraping])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_llmProvider', llmProvider)
  }, [llmProvider])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_authConfig', JSON.stringify(authConfig))
  }, [authConfig])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_strategy', strategy)
  }, [strategy])

  useEffect(() => {
    localStorage.setItem('webScraper_basic_advancedConfig', JSON.stringify(advancedConfig))
  }, [advancedConfig])

  const addUrlField = () => setUrls([...urls, ''])
  const removeUrlField = (index: number) => setUrls(urls.filter((_, i) => i !== index))
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

    // Prepare request payload
    const payload: any = {
      urls: validUrls,
      compliance_level: complianceLevel,
      scrape_prompt: scrapePrompt || undefined,
      llm_provider: enableSmartScraping ? llmProvider : undefined,
      strategy,
      config: showAdvanced ? advancedConfig : undefined,
      session_id: sessionId
    }

    // Add auth if configured
    if (authConfig.auth_type !== 'none') {
      payload.auth_config = authConfig
    }

    try {
      // Use bulk scrape endpoint
      const response = await axios.post(`${API_URL}/api/v1/scraper/scrape/bulk`, payload)

      // Update jobs with results
      if (response.data.results) {
        response.data.results.forEach((result: any, index: number) => {
          setJobs(prev =>
            prev.map(job =>
              job.url === validUrls[index] && job.status === 'processing'
                ? {
                    ...job,
                    status: result.success ? 'success' : 'error',
                    documentId: result.document_id,
                    title: result.title,
                    contentLength: result.content_length,
                    scrapingTime: result.scraping_time_ms,
                    strategyUsed: result.strategy_used,
                    error: result.error
                  }
                : job
            )
          )
        })
      }
    } catch (error: any) {
      console.error('Scrape error:', error)
      // Mark all processing jobs as error
      setJobs(prev =>
        prev.map(job =>
          job.status === 'processing'
            ? { ...job, status: 'error', error: error.response?.data?.detail || 'Scraping failed' }
            : job
        )
      )
    }

    setIsProcessing(false)
    setUrls([''])
    setScrapePrompt('')
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* URLs Input */}
        <ConfigSection title="Target URLs" icon={<Globe className="w-5 h-5" />}>
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
                  <button onClick={() => removeUrlField(index)} className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button onClick={addUrlField} className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors">
            <Plus className="w-4 h-4" />
            Add Another URL
          </button>
        </ConfigSection>

        {/* Phase 1: Compliance & LLM Settings */}
        <ConfigSection
          title="Phase 1: Compliance & Smart Scraping"
          icon={<Lock className="w-5 h-5" />}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Compliance Level */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Compliance Level
              </label>
              <select
                value={complianceLevel}
                onChange={(e) => setComplianceLevel(e.target.value as ComplianceLevel)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="strict">Strict (Max Compliance)</option>
                <option value="balanced">Balanced (Recommended)</option>
                <option value="aggressive">Aggressive (Fast)</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">
                {complianceLevel === 'strict' && 'Respects robots.txt, 2s delay, 10 req/min'}
                {complianceLevel === 'balanced' && 'Respects robots.txt, 1s delay, 30 req/min'}
                {complianceLevel === 'aggressive' && 'Minimal delays, 0.1s delay, 120 req/min'}
              </p>
            </div>

            {/* LLM Provider */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                <input
                  type="checkbox"
                  checked={enableSmartScraping}
                  onChange={(e) => setEnableSmartScraping(e.target.checked)}
                  className="rounded"
                />
                Enable LLM Smart Scraping
              </label>
              {enableSmartScraping && (
                <select
                  value={llmProvider}
                  onChange={(e) => setLLMProvider(e.target.value as LLMProvider)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ollama">Ollama (Local)</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic Claude</option>
                </select>
              )}
            </div>
          </div>

          {/* Scrape Prompt */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Scraping Instructions (Optional)
              {enableSmartScraping && (
                <span className="ml-2 text-xs text-blue-600 dark:text-blue-400">
                  AI-powered filtering enabled
                </span>
              )}
            </label>
            <textarea
              value={scrapePrompt}
              onChange={(e) => setScrapePrompt(e.target.value)}
              placeholder="E.g., 'Extract only product pricing and specifications, ignore reviews'"
              className="w-full resize-none rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          {/* Authentication */}
          <div className="mt-4">
            <button
              onClick={() => setShowAuthConfig(!showAuthConfig)}
              className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              <Lock className="w-4 h-4" />
              {showAuthConfig ? 'Hide' : 'Configure'} Authentication
              {showAuthConfig ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showAuthConfig && (
              <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Authentication Type
                  </label>
                  <select
                    value={authConfig.auth_type}
                    onChange={(e) =>
                      setAuthConfig({ ...authConfig, auth_type: e.target.value as AuthType })
                    }
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="none">None</option>
                    <option value="basic">Basic Auth</option>
                    <option value="bearer">Bearer Token</option>
                    <option value="api_key">API Key</option>
                    <option value="oauth2">OAuth2</option>
                    <option value="jwt">JWT</option>
                    <option value="session">Session Cookie</option>
                    <option value="custom">Custom Headers</option>
                  </select>
                </div>

                {authConfig.auth_type === 'basic' && (
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Username"
                      className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onChange={(e) =>
                        setAuthConfig({
                          ...authConfig,
                          credentials: { ...authConfig.credentials, username: e.target.value }
                        })
                      }
                    />
                    <input
                      type="password"
                      placeholder="Password"
                      className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onChange={(e) =>
                        setAuthConfig({
                          ...authConfig,
                          credentials: { ...authConfig.credentials, password: e.target.value }
                        })
                      }
                    />
                  </div>
                )}

                {authConfig.auth_type === 'bearer' && (
                  <input
                    type="text"
                    placeholder="Bearer Token"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onChange={(e) =>
                      setAuthConfig({
                        ...authConfig,
                        credentials: { token: e.target.value }
                      })
                    }
                  />
                )}

                {authConfig.auth_type === 'api_key' && (
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Header Name (e.g., X-API-Key)"
                      className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onChange={(e) =>
                        setAuthConfig({
                          ...authConfig,
                          credentials: { ...authConfig.credentials, header: e.target.value }
                        })
                      }
                    />
                    <input
                      type="text"
                      placeholder="API Key Value"
                      className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onChange={(e) =>
                        setAuthConfig({
                          ...authConfig,
                          credentials: { ...authConfig.credentials, key: e.target.value }
                        })
                      }
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </ConfigSection>

        {/* Phase 2: Scraping Strategy & Advanced Config */}
        <ConfigSection
          title="Phase 2: Scraping Strategy & Configuration"
          icon={<Settings className="w-5 h-5" />}
        >
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Scraping Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as ScrapingStrategy)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(STRATEGY_DESCRIPTIONS).map(([key, desc]) => (
                <option key={key} value={key}>
                  {key.charAt(0).toUpperCase() + key.slice(1)} - {desc}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            <Settings className="w-4 h-4" />
            {showAdvanced ? 'Hide' : 'Show'} Advanced Configuration
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showAdvanced && (
            <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-4">
              {/* Performance */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={advancedConfig.timeout}
                    onChange={(e) =>
                      setAdvancedConfig({ ...advancedConfig, timeout: parseFloat(e.target.value) })
                    }
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Max Retries
                  </label>
                  <input
                    type="number"
                    value={advancedConfig.max_retries}
                    onChange={(e) =>
                      setAdvancedConfig({
                        ...advancedConfig,
                        max_retries: parseInt(e.target.value)
                      })
                    }
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Min Content Length
                  </label>
                  <input
                    type="number"
                    value={advancedConfig.min_content_length}
                    onChange={(e) =>
                      setAdvancedConfig({
                        ...advancedConfig,
                        min_content_length: parseInt(e.target.value)
                      })
                    }
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                  />
                </div>
              </div>

              {/* Content Options */}
              <div>
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Include Content</p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: 'include_links', label: 'Links' },
                    { key: 'include_tables', label: 'Tables' },
                    { key: 'include_images', label: 'Images' },
                    { key: 'include_metadata', label: 'Metadata' }
                  ].map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                      <input
                        type="checkbox"
                        checked={advancedConfig[key as keyof AdvancedConfig] as boolean}
                        onChange={(e) =>
                          setAdvancedConfig({ ...advancedConfig, [key]: e.target.checked })
                        }
                        className="rounded"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              {/* Filtering */}
              <div>
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Remove Elements</p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: 'remove_nav', label: 'Navigation' },
                    { key: 'remove_footer', label: 'Footer' },
                    { key: 'remove_header', label: 'Header' },
                    { key: 'remove_ads', label: 'Advertisements' }
                  ].map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                      <input
                        type="checkbox"
                        checked={advancedConfig[key as keyof AdvancedConfig] as boolean}
                        onChange={(e) =>
                          setAdvancedConfig({ ...advancedConfig, [key]: e.target.checked })
                        }
                        className="rounded"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              {/* JavaScript Rendering */}
              <div>
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={advancedConfig.enable_javascript}
                    onChange={(e) =>
                      setAdvancedConfig({ ...advancedConfig, enable_javascript: e.target.checked })
                    }
                    className="rounded"
                  />
                  Enable JavaScript Rendering (Playwright)
                </label>

                {advancedConfig.enable_javascript && (
                  <div className="mt-2 grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Wait for selector (optional)"
                      value={advancedConfig.wait_for_selector}
                      onChange={(e) =>
                        setAdvancedConfig({ ...advancedConfig, wait_for_selector: e.target.value })
                      }
                      className="rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Wait timeout (s)"
                      value={advancedConfig.wait_timeout}
                      onChange={(e) =>
                        setAdvancedConfig({
                          ...advancedConfig,
                          wait_timeout: parseFloat(e.target.value)
                        })
                      }
                      className="rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </ConfigSection>

        {/* Scrape Button */}
        <button
          onClick={handleScrape}
          disabled={isProcessing || urls.every(url => !url.trim())}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Scraping {urls.filter(u => u.trim()).length} URLs...
            </>
          ) : (
            <>
              <Zap className="w-5 h-5" />
              Start Enterprise Scraping
            </>
          )}
        </button>

        {/* Jobs List */}
        {jobs.length > 0 && (
          <ConfigSection title="Scrape Results" icon={<BarChart3 className="w-5 h-5" />}>
            <div className="space-y-3">
              {jobs.map((job, index) => (
                <JobResultCard key={index} job={job} />
              ))}
            </div>
          </ConfigSection>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// TEMPLATE EXTRACTION TAB
// ============================================================================

function TemplateExtractionTab() {
  const [sessionId] = useState(() => localStorage.getItem('sessionId') || undefined)

  // Initialize state from localStorage with defaults
  const [urls, setUrls] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('webScraper_template_urls')
      return saved ? JSON.parse(saved) : ['']
    } catch {
      return ['']
    }
  })

  const [outputFormat, setOutputFormat] = useState<OutputFormat>(() => {
    const saved = localStorage.getItem('webScraper_template_outputFormat')
    return (saved as OutputFormat) || 'excel'
  })

  const [deliveryMethod, setDeliveryMethod] = useState<DeliveryMethod>(() => {
    const saved = localStorage.getItem('webScraper_template_deliveryMethod')
    return (saved as DeliveryMethod) || 'download'
  })

  const [deliveryConfig, setDeliveryConfig] = useState<DeliveryConfig>(() => {
    try {
      const saved = localStorage.getItem('webScraper_template_deliveryConfig')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  })

  const [complianceLevel, setComplianceLevel] = useState<ComplianceLevel>(() => {
    const saved = localStorage.getItem('webScraper_template_complianceLevel')
    return (saved as ComplianceLevel) || 'balanced'
  })

  const [maxConcurrent, setMaxConcurrent] = useState(() => {
    const saved = localStorage.getItem('webScraper_template_maxConcurrent')
    return saved ? parseInt(saved) : 5
  })

  const [isCreating, setIsCreating] = useState(false)

  const [createdJobId, setCreatedJobId] = useState<string | null>(() => {
    return localStorage.getItem('webScraper_template_createdJobId') || null
  })

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('webScraper_template_urls', JSON.stringify(urls))
  }, [urls])

  useEffect(() => {
    localStorage.setItem('webScraper_template_outputFormat', outputFormat)
  }, [outputFormat])

  useEffect(() => {
    localStorage.setItem('webScraper_template_deliveryMethod', deliveryMethod)
  }, [deliveryMethod])

  useEffect(() => {
    localStorage.setItem('webScraper_template_deliveryConfig', JSON.stringify(deliveryConfig))
  }, [deliveryConfig])

  useEffect(() => {
    localStorage.setItem('webScraper_template_complianceLevel', complianceLevel)
  }, [complianceLevel])

  useEffect(() => {
    localStorage.setItem('webScraper_template_maxConcurrent', String(maxConcurrent))
  }, [maxConcurrent])

  useEffect(() => {
    if (createdJobId) {
      localStorage.setItem('webScraper_template_createdJobId', createdJobId)
    }
  }, [createdJobId])

  // Template management state
  const [templates, setTemplates] = useState<any[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [showTemplateUpload, setShowTemplateUpload] = useState(false)
  const [templateJson, setTemplateJson] = useState('')
  const [showExcelUpload, setShowExcelUpload] = useState(false)
  const [excelFile, setExcelFile] = useState<File | null>(null)
  const [isUploadingExcel, setIsUploadingExcel] = useState(false)

  // Fetch templates on mount
  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/extraction/templates`)
      setTemplates(response.data || [])
    } catch (error) {
      console.error('Failed to fetch templates:', error)
    }
  }

  const handleUploadTemplate = async () => {
    try {
      const template = JSON.parse(templateJson)
      await axios.post(`${API_URL}/api/v1/extraction/templates`, template)
      alert('Template uploaded successfully!')
      setTemplateJson('')
      setShowTemplateUpload(false)
      fetchTemplates()
    } catch (error: any) {
      console.error('Template upload error:', error)
      alert(error.response?.data?.detail || 'Failed to upload template. Please check the JSON format.')
    }
  }

  const handleUploadExcelTemplate = async () => {
    if (!excelFile) {
      alert('Please select an Excel file first')
      return
    }

    setIsUploadingExcel(true)

    try {
      const formData = new FormData()
      formData.append('file', excelFile)

      const response = await axios.post(
        `${API_URL}/api/v1/extraction/templates/upload-excel`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      alert(`Excel template uploaded successfully! Template ID: ${response.data.template_id}`)
      setExcelFile(null)
      setShowExcelUpload(false)
      fetchTemplates()
    } catch (error: any) {
      console.error('Excel upload error:', error)
      alert(error.response?.data?.detail || 'Failed to upload Excel file')
    }

    setIsUploadingExcel(false)
  }

  const handleExcelFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        setExcelFile(file)
      } else {
        alert('Please select a valid Excel file (.xlsx or .xls)')
        e.target.value = ''
      }
    }
  }

  const handleDeleteTemplate = async (templateId: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return

    try {
      await axios.delete(`${API_URL}/api/v1/extraction/templates/${templateId}`)
      fetchTemplates()
    } catch (error) {
      console.error('Template delete error:', error)
      alert('Failed to delete template')
    }
  }

  const addUrlField = () => setUrls([...urls, ''])
  const removeUrlField = (index: number) => setUrls(urls.filter((_, i) => i !== index))
  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls]
    newUrls[index] = value
    setUrls(newUrls)
  }

  const handleBulkUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      const newUrls = text.split('\n').filter(url => url.trim())
      setUrls(newUrls)
    }
    reader.readAsText(file)
  }

  const handleCreateJob = async () => {
    const validUrls = urls.filter(url => url.trim() !== '')
    if (validUrls.length === 0) return

    setIsCreating(true)

    const payload = {
      urls: validUrls,
      template_id: selectedTemplateId || undefined,
      output_format: outputFormat,
      delivery_method: deliveryMethod,
      delivery_config: deliveryMethod !== 'download' ? deliveryConfig : undefined,
      scrape_config: {
        compliance_level: complianceLevel,
        max_concurrent_requests: maxConcurrent
      },
      session_id: sessionId
    }

    try {
      const response = await axios.post(`${API_URL}/api/v1/extraction/jobs`, payload)
      setCreatedJobId(response.data.job_id)
      setUrls([''])
    } catch (error) {
      console.error('Job creation error:', error)
      alert('Failed to create extraction job')
    }

    setIsCreating(false)
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Info Banner */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-1">
                Phase 3: Template-Based Extraction
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Create extraction jobs with structured output formats and automated delivery.
                Supports up to 100 URLs per job with LangGraph workflow orchestration.
              </p>
            </div>
          </div>
        </div>

        {/* Template Management */}
        <ConfigSection title="Extraction Template (Optional)" icon={<FileText className="w-5 h-5" />}>
          <div className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Use extraction templates to define structured data fields and extraction rules.
              Templates support CSS selectors, XPath, JSON paths, and LLM-based extraction.
            </p>

            {/* Template Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Select Template
              </label>
              <select
                value={selectedTemplateId || ''}
                onChange={(e) => setSelectedTemplateId(e.target.value || null)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No Template (Basic Extraction)</option>
                {templates.map(t => (
                  <option key={t.template_id} value={t.template_id}>
                    {t.name} ({t.fields_count} fields)
                  </option>
                ))}
              </select>
            </div>

            {/* Template Upload Section */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowExcelUpload(!showExcelUpload)
                  if (!showExcelUpload) setShowTemplateUpload(false)
                }}
                className="flex items-center gap-2 px-4 py-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
              >
                <FileText className="w-4 h-4" />
                {showExcelUpload ? 'Hide' : 'Upload Excel Template'}
              </button>

              <button
                onClick={() => {
                  setShowTemplateUpload(!showTemplateUpload)
                  if (!showTemplateUpload) setShowExcelUpload(false)
                }}
                className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                {showTemplateUpload ? 'Hide' : 'Upload JSON Template'}
              </button>
            </div>

            {/* Excel Upload Section */}
            {showExcelUpload && (
              <div className="mt-3 space-y-3 p-4 bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800">
                <div>
                  <h4 className="text-sm font-semibold text-green-900 dark:text-green-100 mb-2">
                    Upload Excel Template
                  </h4>
                  <p className="text-xs text-green-800 dark:text-green-200 mb-3">
                    Upload an Excel file (.xlsx or .xls) with column headers. The system will intelligently map
                    scraped data to these columns using LLM-powered extraction.
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300 mb-3 font-mono bg-green-100 dark:bg-green-900/30 p-2 rounded">
                    Example: Create an Excel file with columns like: "Product Name", "Price", "Description", "Rating"
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Select Excel File
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleExcelFileChange}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  {excelFile && (
                    <p className="text-xs text-green-600 dark:text-green-400 mt-2">
                      Selected: {excelFile.name} ({(excelFile.size / 1024).toFixed(2)} KB)
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleUploadExcelTemplate}
                    disabled={!excelFile || isUploadingExcel}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {isUploadingExcel ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <FileText className="w-4 h-4" />
                        Upload Excel Template
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setShowExcelUpload(false)
                      setExcelFile(null)
                    }}
                    className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* JSON Template Upload Section */}
            {showTemplateUpload && (
              <div className="mt-3 space-y-3 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Template JSON
                    </label>
                    <textarea
                      value={templateJson}
                      onChange={(e) => setTemplateJson(e.target.value)}
                      placeholder={`{
  "name": "Product Template",
  "description": "Extract product data",
  "fields": [
    {"name": "title", "type": "string", "required": true},
    {"name": "price", "type": "number", "required": true}
  ],
  "css_selectors": {
    "title": "h1.product-title",
    "price": "span.price"
  }
}`}
                      rows={12}
                      className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleUploadTemplate}
                      disabled={!templateJson.trim()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                    >
                      Upload Template
                    </button>
                    <button
                      onClick={() => {
                        setShowTemplateUpload(false)
                        setTemplateJson('')
                      }}
                      className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

            {/* Existing Templates List */}
            {templates.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Available Templates ({templates.length})
                </h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {templates.map(t => (
                    <div
                      key={t.template_id}
                      className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg"
                    >
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">{t.name}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {t.fields_count} fields • {t.description || 'No description'}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteTemplate(t.template_id)}
                        className="px-2 py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ConfigSection>

        {/* URLs Input */}
        <ConfigSection title="Target URLs (Max 100)" icon={<Globe className="w-5 h-5" />}>
          <div className="space-y-3 mb-4">
            {urls.slice(0, 5).map((url, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => updateUrl(index, e.target.value)}
                  placeholder="https://example.com/data"
                  className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {urls.length > 1 && (
                  <button onClick={() => removeUrlField(index)} className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
            {urls.length > 5 && (
              <p className="text-sm text-slate-500">...and {urls.length - 5} more URLs</p>
            )}
          </div>

          <div className="flex gap-3">
            <button onClick={addUrlField} className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors">
              <Plus className="w-4 h-4" />
              Add URL
            </button>

            <label className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors cursor-pointer">
              <FileText className="w-4 h-4" />
              Import from File
              <input
                type="file"
                accept=".txt,.csv"
                onChange={handleBulkUpload}
                className="hidden"
              />
            </label>
          </div>
        </ConfigSection>

        {/* Output Configuration */}
        <ConfigSection title="Output Configuration" icon={<Download className="w-5 h-5" />}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Output Format
              </label>
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value as OutputFormat)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="excel">Excel (.xlsx)</option>
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
                <option value="xml">XML</option>
                <option value="parquet">Parquet</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Delivery Method
              </label>
              <select
                value={deliveryMethod}
                onChange={(e) => setDeliveryMethod(e.target.value as DeliveryMethod)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="download">Download</option>
                <option value="email">Email</option>
                <option value="webhook">Webhook</option>
                <option value="storage">Cloud Storage</option>
              </select>
            </div>
          </div>

          {/* Delivery Configuration */}
          {deliveryMethod === 'email' && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Email Recipients (comma-separated)
              </label>
              <input
                type="text"
                placeholder="user1@example.com, user2@example.com"
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) =>
                  setDeliveryConfig({
                    ...deliveryConfig,
                    email_to: e.target.value.split(',').map(s => s.trim())
                  })
                }
              />
            </div>
          )}

          {deliveryMethod === 'webhook' && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Webhook URL
              </label>
              <input
                type="url"
                placeholder="https://webhook.site/your-unique-url"
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) => setDeliveryConfig({ ...deliveryConfig, webhook_url: e.target.value })}
              />
            </div>
          )}

          {deliveryMethod === 'storage' && (
            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Provider
                  </label>
                  <select
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                    onChange={(e) =>
                      setDeliveryConfig({ ...deliveryConfig, storage_provider: e.target.value })
                    }
                  >
                    <option value="s3">AWS S3</option>
                    <option value="minio">MinIO</option>
                    <option value="gcs">Google Cloud Storage</option>
                    <option value="azure">Azure Blob</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Bucket
                  </label>
                  <input
                    type="text"
                    placeholder="my-bucket"
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                    onChange={(e) =>
                      setDeliveryConfig({ ...deliveryConfig, storage_bucket: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Path
                  </label>
                  <input
                    type="text"
                    placeholder="/results/"
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm"
                    onChange={(e) =>
                      setDeliveryConfig({ ...deliveryConfig, storage_path: e.target.value })
                    }
                  />
                </div>
              </div>
            </div>
          )}
        </ConfigSection>

        {/* Scrape Configuration */}
        <ConfigSection title="Scrape Configuration" icon={<Settings className="w-5 h-5" />}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Compliance Level
              </label>
              <select
                value={complianceLevel}
                onChange={(e) => setComplianceLevel(e.target.value as ComplianceLevel)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="strict">Strict</option>
                <option value="balanced">Balanced</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Max Concurrent Requests
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={maxConcurrent}
                onChange={(e) => setMaxConcurrent(parseInt(e.target.value))}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </ConfigSection>

        {/* Create Job Button */}
        <button
          onClick={handleCreateJob}
          disabled={isCreating || urls.every(url => !url.trim())}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {isCreating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Creating Extraction Job...
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              Create Extraction Job ({urls.filter(u => u.trim()).length} URLs)
            </>
          )}
        </button>

        {/* Success Message */}
        {createdJobId && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                  Job Created Successfully
                </h3>
                <p className="text-sm text-green-800 dark:text-green-200 mb-2">
                  Job ID: <code className="bg-green-100 dark:bg-green-900 px-2 py-1 rounded text-xs">{createdJobId}</code>
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Switch to the Job Monitor tab to track progress.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// JOB MONITOR TAB
// ============================================================================

function JobMonitorTab() {
  // Initialize state from localStorage with defaults
  const [jobs, setJobs] = useState<ExtractionJob[]>(() => {
    try {
      const saved = localStorage.getItem('webScraper_monitor_jobs')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  const [isLoading, setIsLoading] = useState(false)

  const [selectedJob, setSelectedJob] = useState<ExtractionJob | null>(() => {
    try {
      const saved = localStorage.getItem('webScraper_monitor_selectedJob')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const [autoRefresh, setAutoRefresh] = useState(() => {
    const saved = localStorage.getItem('webScraper_monitor_autoRefresh')
    return saved !== null ? saved === 'true' : true
  })

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('webScraper_monitor_jobs', JSON.stringify(jobs))
  }, [jobs])

  useEffect(() => {
    if (selectedJob) {
      localStorage.setItem('webScraper_monitor_selectedJob', JSON.stringify(selectedJob))
    } else {
      localStorage.removeItem('webScraper_monitor_selectedJob')
    }
  }, [selectedJob])

  useEffect(() => {
    localStorage.setItem('webScraper_monitor_autoRefresh', String(autoRefresh))
  }, [autoRefresh])

  const fetchJobs = async () => {
    setIsLoading(true)
    try {
      const response = await axios.get(`${API_URL}/api/v1/extraction/jobs`)
      console.log('Jobs response:', response.data)

      // The API returns { jobs: ExtractionJobResponse[], total: number }
      // ExtractionJobResponse has: job_id, status, created_at, urls_count, output_format, delivery_method
      // We need to map it to our ExtractionJob interface
      const mappedJobs = (response.data.jobs || []).map((job: any) => ({
        job_id: job.job_id,
        status: job.status as JobStatus,
        urls_total: job.urls_count || 0,
        urls_processed: 0, // Not available in list response
        progress_percentage: job.status === 'completed' ? 100 : job.status === 'running' ? 50 : 0,
        output_format: job.output_format as OutputFormat,
        delivery_method: job.delivery_method as DeliveryMethod
      }))

      setJobs(mappedJobs)
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
    }
    setIsLoading(false)
  }

  const fetchJobDetails = async (jobId: string) => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/extraction/jobs/${jobId}`)
      setSelectedJob(response.data)
    } catch (error) {
      console.error('Failed to fetch job details:', error)
    }
  }

  const handleDownload = async (jobId: string) => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/extraction/jobs/${jobId}/download`, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `extraction_${jobId}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Download failed:', error)
      alert('Failed to download results')
    }
  }

  const handleRetry = async (jobId: string) => {
    if (!confirm('Retry this job with the same configuration?')) return

    try {
      const response = await axios.post(`${API_URL}/api/v1/extraction/jobs/${jobId}/retry`)
      alert(`Retry job created successfully! New Job ID: ${response.data.new_job_id}`)
      // Refresh jobs list
      fetchJobs()
      // Select the new job
      if (response.data.new_job_id) {
        setTimeout(() => fetchJobDetails(response.data.new_job_id), 1000)
      }
    } catch (error: any) {
      console.error('Retry failed:', error)
      alert(error.response?.data?.detail || 'Failed to retry job')
    }
  }

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return

    try {
      await axios.delete(`${API_URL}/api/v1/extraction/jobs/${jobId}`)
      setJobs(jobs.filter(j => j.job_id !== jobId))
      if (selectedJob?.job_id === jobId) {
        setSelectedJob(null)
      }
    } catch (error) {
      console.error('Delete failed:', error)
      alert('Failed to delete job')
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchJobs()
      if (selectedJob && (selectedJob.status === 'running' || selectedJob.status === 'pending')) {
        fetchJobDetails(selectedJob.job_id)
      }
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [autoRefresh, selectedJob])

  return (
    <div className="h-full flex">
      {/* Jobs List */}
      <div className="w-1/3 border-r border-slate-200 dark:border-slate-700 overflow-y-auto p-4 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900 dark:text-white">Extraction Jobs</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`p-2 rounded transition-colors ${
                autoRefresh
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-600'
                  : 'text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
              title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
            >
              <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={fetchJobs}
              className="p-2 rounded text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {jobs.length === 0 && !isLoading && (
            <p className="text-sm text-slate-500 text-center py-8">No extraction jobs found</p>
          )}

          {jobs.map((job) => (
            <button
              key={job.job_id}
              onClick={() => fetchJobDetails(job.job_id)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedJob?.job_id === job.job_id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono text-slate-500">
                  {job.job_id.substring(0, 8)}...
                </span>
                <StatusBadge status={job.status} />
              </div>
              {job.urls_total !== undefined && job.urls_total > 0 && (
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {job.urls_processed !== undefined ? `${job.urls_processed} / ` : ''}{job.urls_total} URLs
                </p>
              )}
              {job.progress_percentage !== undefined && job.status === 'running' && (
                <div className="mt-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                  <div
                    className="bg-blue-600 h-1.5 rounded-full transition-all"
                    style={{ width: `${job.progress_percentage}%` }}
                  />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Job Details */}
      <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
        {!selectedJob ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="text-center">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-slate-400" />
              <p>Select a job to view details</p>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
                  Job Details
                </h2>
                <p className="text-sm font-mono text-slate-500">{selectedJob.job_id}</p>
              </div>
              <StatusBadge status={selectedJob.status} large />
            </div>

            {/* Progress */}
            {selectedJob.status === 'running' && selectedJob.progress_percentage !== undefined && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    {selectedJob.current_step?.replace(/_/g, ' ').toUpperCase() || 'PROCESSING'}
                  </span>
                  <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    {selectedJob.progress_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${selectedJob.progress_percentage}%` }}
                  />
                </div>
              </div>
            )}

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="URLs Total"
                value={selectedJob.urls_total || 0}
                icon={<Globe className="w-5 h-5" />}
              />
              <MetricCard
                label="Processed"
                value={selectedJob.urls_processed || 0}
                icon={<CheckCircle className="w-5 h-5" />}
                color="green"
              />
              <MetricCard
                label="Failed"
                value={selectedJob.failed_scrapes || 0}
                icon={<XCircle className="w-5 h-5" />}
                color="red"
              />
              <MetricCard
                label="Records"
                value={selectedJob.records_extracted || 0}
                icon={<Database className="w-5 h-5" />}
                color="blue"
              />
            </div>

            {/* Quality Score */}
            {selectedJob.quality_score !== undefined && (
              <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Quality Score
                  </span>
                  <span className="text-2xl font-bold text-green-600">
                    {(selectedJob.quality_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${selectedJob.quality_score * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Timing & Output Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Timing */}
              {selectedJob.started_at && (
                <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Timing
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Started:</span>
                      <span className="font-mono text-xs">
                        {new Date(selectedJob.started_at).toLocaleString()}
                      </span>
                    </div>
                    {selectedJob.completed_at && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-400">Completed:</span>
                          <span className="font-mono text-xs">
                            {new Date(selectedJob.completed_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-400">Duration:</span>
                          <span className="font-mono">
                            {selectedJob.total_duration_seconds?.toFixed(2)}s
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Output */}
              {selectedJob.output_format && (
                <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Output
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Format:</span>
                      <span className="font-mono uppercase text-xs">{selectedJob.output_format}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Delivery:</span>
                      <span className="font-mono capitalize text-xs">{selectedJob.delivery_method}</span>
                    </div>
                    {selectedJob.delivery_success !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Delivered:</span>
                        <span
                          className={
                            selectedJob.delivery_success ? 'text-green-600' : 'text-red-600'
                          }
                        >
                          {selectedJob.delivery_success ? 'Yes' : 'No'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Errors & Warnings */}
            {((selectedJob.errors && selectedJob.errors.length > 0) ||
              (selectedJob.warnings && selectedJob.warnings.length > 0)) && (
              <div className="space-y-3">
                {selectedJob.errors && selectedJob.errors.length > 0 && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <h3 className="font-semibold text-red-900 dark:text-red-100 mb-2 flex items-center gap-2">
                      <XCircle className="w-5 h-5" />
                      Errors ({selectedJob.errors.length})
                    </h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-red-800 dark:text-red-200">
                      {selectedJob.errors.slice(0, 5).map((error, i) => (
                        <li key={i} className="truncate">{error}</li>
                      ))}
                      {selectedJob.errors.length > 5 && (
                        <li className="text-xs">...and {selectedJob.errors.length - 5} more</li>
                      )}
                    </ul>
                  </div>
                )}

                {selectedJob.warnings && selectedJob.warnings.length > 0 && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <h3 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Warnings ({selectedJob.warnings.length})
                    </h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800 dark:text-yellow-200">
                      {selectedJob.warnings.slice(0, 5).map((warning, i) => (
                        <li key={i} className="truncate">{warning}</li>
                      ))}
                      {selectedJob.warnings.length > 5 && (
                        <li className="text-xs">...and {selectedJob.warnings.length - 5} more</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              {selectedJob.status === 'completed' && (
                <button
                  onClick={() => handleDownload(selectedJob.job_id)}
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                >
                  <Download className="w-5 h-5" />
                  Download Results
                </button>
              )}
              {selectedJob.status === 'failed' && (
                <button
                  onClick={() => handleRetry(selectedJob.job_id)}
                  className="flex-1 px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-5 h-5" />
                  Retry Job
                </button>
              )}
              {(selectedJob.status === 'completed' || selectedJob.status === 'failed') && (
                <button
                  onClick={() => handleDelete(selectedJob.job_id)}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
                >
                  <Trash2 className="w-5 h-5" />
                  Delete
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================

function ConfigSection({
  title,
  icon,
  children
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  )
}

function JobResultCard({ job }: { job: ScrapeJob }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm border border-slate-200 dark:border-slate-700">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-4 h-4 text-blue-600" />
            <p className="text-sm font-medium text-slate-900 dark:text-white break-all">{job.url}</p>
          </div>
          {job.title && (
            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Title: {job.title}</p>
          )}
          <div className="flex gap-4 text-xs text-slate-500">
            {job.contentLength && <span>{job.contentLength.toLocaleString()} chars</span>}
            {job.scrapingTime && <span>{job.scrapingTime.toFixed(0)}ms</span>}
            {job.strategyUsed && <span>Strategy: {job.strategyUsed}</span>}
          </div>
        </div>

        <div className="flex items-center gap-2 ml-4">
          {job.status === 'processing' && (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              <span className="text-xs text-blue-600">Scraping...</span>
            </>
          )}
          {job.status === 'success' && (
            <>
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-xs text-green-600">Complete</span>
            </>
          )}
          {job.status === 'error' && (
            <>
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="text-xs text-red-600">{job.error}</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status, large }: { status: JobStatus; large?: boolean }) {
  const configs = {
    pending: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200', icon: Clock },
    running: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', icon: Loader2 },
    completed: { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', icon: CheckCircle },
    failed: { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', icon: XCircle }
  }

  const config = configs[status]
  const Icon = config.icon

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${large ? 'px-3 py-1.5' : 'px-2 py-1'} rounded-full ${
        large ? 'text-sm' : 'text-xs'
      } font-medium ${config.color}`}
    >
      <Icon
        className={`${large ? 'w-4 h-4' : 'w-3 h-3'} ${status === 'running' ? 'animate-spin' : ''}`}
      />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function MetricCard({
  label,
  value,
  icon,
  color = 'slate'
}: {
  label: string
  value: number
  icon: React.ReactNode
  color?: string
}) {
  const colorClasses = {
    slate: 'text-slate-600',
    green: 'text-green-600',
    red: 'text-red-600',
    blue: 'text-blue-600'
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
      <div className={`${colorClasses[color as keyof typeof colorClasses]} mb-2`}>{icon}</div>
      <p className="text-2xl font-bold text-slate-900 dark:text-white">{value.toLocaleString()}</p>
      <p className="text-xs text-slate-600 dark:text-slate-400">{label}</p>
    </div>
  )
}
