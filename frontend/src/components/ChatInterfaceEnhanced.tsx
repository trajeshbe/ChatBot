import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText, ExternalLink, Paperclip, X, Trash2, ChevronDown, ChevronUp, ArrowLeft, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import FileUpload from './FileUpload'
import WebScraperEnhanced from './WebScraperEnhanced'
import ModelSelector from './ModelSelector'
import UploadedFilesList from './UploadedFilesList'
import { getCurrentRAGConfig, type RAGConfig } from './RAGSettings'
import PerformanceMetrics from './PerformanceMetrics'
import EvaluationMetrics from './EvaluationMetrics'
import SettingsPanel, { MetricsSettings } from './SettingsPanel'
import PromptCommandPalette from './PromptCommandPalette'
import OutputExport from './OutputExport'
import ToolAgentSelector, { AVAILABLE_TOOLS } from './ToolAgentSelector'
import { BrainView } from './BrainView'
// import ToolUsageDisplay from './ToolUsageDisplay'  // Disabled - duplicate display
import axios from 'axios'

// Unified WeightsConfig interface - all 48 parameters for dynamic per-query control
interface WeightsConfig {
  strategy_weights: {
    rag_short_term: number;
    rag_hybrid: number;
    tool_navigation: number;
    tool_ocr: number;
    tool_docling: number;
    tool_web_scraping: number;
    rag_long_term: number;
    direct_llm: number;
  };
  scoring_formula_weights: {
    strategy_weight: number;
    confidence: number;
    source_quality_score: number;
    relevance_score: number;
    completeness_score: number;
    diversity_bonus: number;
  };
  source_quality_weights: {
    short_term: number;
    long_term: number;
    general: number;
    scraped: number;
    ocr: number;
  };
  classification_thresholds: {
    general_knowledge_skip: number;
    ai_personal_skip: number;
    ambiguous_use_rag: number;
    min_llm_classification_confidence: number;
  };
  similarity_thresholds: {
    default: number;
    proper_nouns: number;
    short_query: number;
    minimum: number;
    maximum: number;
  };
  reranking_weights: {
    semantic: number;
    keyword: number;
    recency: number;
  };
  query_preprocessing: {
    max_length_for_expansion: number;
    min_query_length: number;
    max_query_length: number;
  };
  cache: {
    similarity_threshold: number;
    ttl_seconds: number;
  };
  multi_tool_weights: {
    document_rag: number;
    navigation_agent: number;
    ocr_tool: number;
    web_scraping: number;
    docling: number;
  };
  answer_fusion: {
    best_answer_weight: number;
    second_best_weight: number;
    third_best_weight: number;
  };
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
  model?: string
  model_name?: string
  contextInfo?: string
  // Performance metrics
  latency_ms?: number
  tokens_used?: number
  num_sources?: number
  cached?: boolean
  // Evaluation metrics
  quality_metrics?: {
    quality_level?: string
    rag_score?: number
    faithfulness?: number
    answer_relevancy?: number
    context_relevancy?: number
    context_precision?: number
    evaluation_time_ms?: number
    enabled_methods?: string[]
    classification_type?: string
    classification_confidence?: number
  }
  // 🆕 Tool usage tracking (enhanced structure from backend)
  tools_used?: Array<{
    tool_id: string
    tool_name: string
    status: 'success' | 'failure'
    latency_ms: number
    order: number
  }>
  // RAG settings used for this query
  rag_settings?: {
    top_k?: number
    similarity_threshold?: number
    min_similarity_threshold?: number
    no_relevant_docs_threshold?: number
    chunk_size?: number
    chunk_overlap?: number
    search_type?: string
    memory_type?: string
  }
  // 🧠 Brain View debug context (inline per-message)
  debug_context?: any
  // User feedback
  userFeedback?: 'thumbs_up' | 'thumbs_down' | 'rated'
  userRating?: number
}

interface Source {
  id: string
  filename: string
  source_type: string
  source_url?: string
  relevance: number
  excerpt: string
  memory_type?: 'short-term' | 'long-term'
}

interface Project {
  id: string
  name: string
  description?: string
  file_count: number
}

interface Props {
  activeTab: 'chat' | 'upload' | 'scrape' | 'evaluation'
  ragConfig?: RAGConfig | null
  projectId?: string  // Link chat to project
  hideHeader?: boolean  // Hide model/project selector (for embedded views)
  onBackToProject?: () => void  // Callback to return to project view
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 🆕 MEMORY OPTIMIZATION: Message limits to prevent unbounded growth
const MAX_MESSAGES_IN_MEMORY = 100  // Keep max 100 messages in state
const MAX_MESSAGES_IN_LOCALSTORAGE = 50  // Save only last 50 to localStorage

// Generate or retrieve session ID
const getSessionId = (): string => {
  if (typeof window === 'undefined') return ''

  let sessionId = sessionStorage.getItem('chat_session_id')
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem('chat_session_id', sessionId)
    console.log('🆔 Created new session:', sessionId)
  }
  return sessionId
}

// Load messages from localStorage for a specific session
const loadMessages = (sessionId: string): Message[] => {
  if (typeof window === 'undefined' || !sessionId) {
    return [{
      role: 'assistant',
      content: 'Hello! I\'m your enterprise RAG assistant with multi-model support. I can use OpenAI, Claude, or local models. Select your preferred model above and ask me anything! You can also upload files directly in this chat.',
      timestamp: new Date()
    }]
  }

  try {
    const stored = localStorage.getItem(`chat_messages_${sessionId}`)
    if (stored) {
      const parsed = JSON.parse(stored)
      // Convert timestamp strings back to Date objects
      const messages = parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))

      // 🆕 MEMORY OPTIMIZATION: Trim to max messages if exceeded
      if (messages.length > MAX_MESSAGES_IN_MEMORY) {
        console.log(`⚠️  Trimming ${messages.length} messages to ${MAX_MESSAGES_IN_MEMORY} to prevent memory overflow`)
        return messages.slice(-MAX_MESSAGES_IN_MEMORY)
      }

      return messages
    }
  } catch (error) {
    console.error('Error loading messages from localStorage:', error)
  }

  // Return default message if no stored messages found
  return [{
    role: 'assistant',
    content: 'Hello! I\'m your enterprise RAG assistant with multi-model support. I can use OpenAI, Claude, or local models. Select your preferred model above and ask me anything! You can also upload files directly in this chat.',
    timestamp: new Date()
  }]
}

// Save messages to localStorage for a specific session
const saveMessages = (sessionId: string, messages: Message[]): void => {
  if (typeof window === 'undefined' || !sessionId) return

  try {
    // 🆕 MEMORY OPTIMIZATION: Only save last N messages to localStorage
    const messagesToSave = messages.slice(-MAX_MESSAGES_IN_LOCALSTORAGE)

    // 🆕 MEMORY OPTIMIZATION: Strip heavy metadata before saving
    const lightweightMessages = messagesToSave.map(msg => {
      const { debug_context, tools_used, quality_metrics, ...essential } = msg

      // Keep only essential data for localStorage
      return {
        ...essential,
        // Keep lightweight metadata for UI display
        latency_ms: msg.latency_ms,
        tokens_used: msg.tokens_used,
        num_sources: msg.num_sources,
        model: msg.model,
        model_name: msg.model_name
      }
    })

    localStorage.setItem(`chat_messages_${sessionId}`, JSON.stringify(lightweightMessages))

  } catch (error) {
    console.error('Error saving messages to localStorage:', error)

    // 🆕 MEMORY OPTIMIZATION: Handle QuotaExceededError
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      console.warn('⚠️  localStorage quota exceeded, saving fewer messages...')

      try {
        // Try saving only last 25 messages as fallback
        const reducedMessages = messages.slice(-25).map(msg => {
          const { debug_context, tools_used, quality_metrics, sources, ...minimal } = msg
          return {
            ...minimal,
            // Keep only timestamp and content for minimal storage
            role: msg.role,
            content: msg.content.slice(0, 500), // Truncate content to 500 chars
            timestamp: msg.timestamp
          }
        })

        localStorage.setItem(`chat_messages_${sessionId}`, JSON.stringify(reducedMessages))
        console.log('✅ Saved reduced messages after quota error')
      } catch (fallbackError) {
        console.error('❌ Failed to save even reduced messages:', fallbackError)
        // Clear old sessions to make space
        try {
          const keys = Object.keys(localStorage)
          const sessionKeys = keys.filter(k => k.startsWith('chat_messages_session-'))
          if (sessionKeys.length > 5) {
            // Remove oldest session (first 5 alphabetically)
            sessionKeys.slice(0, 5).forEach(k => localStorage.removeItem(k))
            console.log(`🧹 Cleaned up ${5} old sessions`)
          }
        } catch (cleanupError) {
          console.error('Failed to cleanup old sessions:', cleanupError)
        }
      }
    }
  }
}

export default function ChatInterfaceEnhanced({ activeTab, ragConfig: ragConfigProp, projectId, hideHeader = false, onBackToProject }: Props) {
  const [sessionId, setSessionId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: 'Hello! I\'m your enterprise RAG assistant with multi-model support. I can use OpenAI, Claude, or local models. Select your preferred model above and ask me anything! You can also upload files directly in this chat.',
    timestamp: new Date()
  }])
  const [isHydrated, setIsHydrated] = useState(false)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPromptPalette, setShowPromptPalette] = useState(false)
  const [promptSearchQuery, setPromptSearchQuery] = useState('')
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [filesJustUploaded, setFilesJustUploaded] = useState(false)
  const [expandedMetrics, setExpandedMetrics] = useState<Record<number, boolean>>({})
  const [expandedBrainView, setExpandedBrainView] = useState<Record<number, boolean>>({})
  const [metricsSettings, setMetricsSettings] = useState<MetricsSettings>({
    enableEvaluation: false,  // Default - will be loaded from localStorage if available
    showPerformanceMetrics: true,
    showToolsUsed: true,
  })
  // 🆕 Unified configuration state - ALL 48 parameters for dynamic per-query control
  const [unifiedConfig, setUnifiedConfig] = useState<WeightsConfig | null>(null)
  // 🆕 Project management state
  const [availableProjects, setAvailableProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projectId || null)
  // Export functionality state
  const [exportingMessageIndex, setExportingMessageIndex] = useState<number | null>(null)
  // 🆕 Tool & Agent Selection State
  const [enabledTools, setEnabledTools] = useState<string[]>(AVAILABLE_TOOLS.map(t => t.id)) // All tools enabled by default
  const [selectedAgent, setSelectedAgent] = useState<string>('auto') // Default to auto (multi-strategy)
  // 🧠 Brain View State - Load from localStorage to persist across navigations
  const [brainViewOpen, setBrainViewOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('brainViewOpen')
      return saved === 'true' // Default to false if not set
    }
    return false
  })
  const [currentDebugContext, setCurrentDebugContext] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const previousProjectIdRef = useRef<string | null>(null)  // 🐛 FIX: Track previous project to detect switches

  // 🆕 Fetch unified configuration on mount
  useEffect(() => {
    const fetchUnifiedConfig = async () => {
      try {
        // 🆕 PRIORITY 1: Check localStorage for user's session config
        if (typeof window !== 'undefined') {
          const savedConfig = localStorage.getItem('userWeightsConfig')
          if (savedConfig) {
            try {
              const parsedConfig = JSON.parse(savedConfig)
              setUnifiedConfig(parsedConfig)
              console.log('✅ Loaded USER SESSION config from localStorage with', Object.keys(parsedConfig).length, 'parameter groups')
              return // Use session config, don't fetch from API
            } catch (parseError) {
              console.error('Failed to parse saved config, fetching from API:', parseError)
            }
          }
        }

        // PRIORITY 2: Fetch default config from backend if no session config
        const response = await axios.get(`${API_URL}/api/v1/config/weights`)
        if (response.data.success && response.data.data) {
          setUnifiedConfig(response.data.data)
          console.log('✅ Loaded DEFAULT config from API with', Object.keys(response.data.data).length, 'parameter groups')
        }
      } catch (error) {
        console.warn('⚠️ Could not load unified config, using defaults:', error)
      }
    }
    fetchUnifiedConfig()

    // 🆕 FIX: Listen for tab visibility changes to reload config
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('🔄 Tab became visible, reloading config from localStorage...')
        fetchUnifiedConfig()
      }
    }

    // 🆕 FIX: Listen for custom storage event when WeightsConfigManager saves
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'userWeightsConfig' && e.newValue) {
        try {
          const parsedConfig = JSON.parse(e.newValue)
          setUnifiedConfig(parsedConfig)
          console.log('🔄 Config updated from storage event with', Object.keys(parsedConfig).length, 'parameter groups')
        } catch (parseError) {
          console.error('Failed to parse storage event config:', parseError)
        }
      }
    }

    // 🆕 FIX: Listen for custom event when WeightsConfigManager saves (same-tab updates)
    const handleConfigUpdate = (e: CustomEvent) => {
      if (e.detail) {
        setUnifiedConfig(e.detail)
        console.log('🔄 Config updated from custom event with', Object.keys(e.detail).length, 'parameter groups')
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('storage', handleStorageChange as EventListener)
    window.addEventListener('weightsConfigUpdated', handleConfigUpdate as EventListener)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('storage', handleStorageChange as EventListener)
      window.removeEventListener('weightsConfigUpdated', handleConfigUpdate as EventListener)
    }
  }, [])

  // 🆕 Load metrics settings from localStorage (syncs with SettingsPanel in sidebar)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedSettings = localStorage.getItem('metricsSettings')
      if (savedSettings) {
        try {
          const parsed = JSON.parse(savedSettings)
          setMetricsSettings(parsed)
          console.log('✅ Loaded metrics settings from localStorage:', parsed)
        } catch (e) {
          console.error('Failed to load metrics settings:', e)
        }
      }

      // Listen for storage changes (when SettingsPanel updates settings)
      const handleMetricsChange = (e: StorageEvent) => {
        if (e.key === 'metricsSettings' && e.newValue) {
          try {
            const parsed = JSON.parse(e.newValue)
            setMetricsSettings(parsed)
            console.log('🔄 Metrics settings updated from storage:', parsed)
          } catch (error) {
            console.error('Failed to parse metrics settings:', error)
          }
        }
      }

      window.addEventListener('storage', handleMetricsChange as EventListener)
      return () => {
        window.removeEventListener('storage', handleMetricsChange as EventListener)
      }
    }
  }, [])

  // 🆕 Load model based on context (global or project-specific)
  useEffect(() => {
    if (typeof window !== 'undefined' && isHydrated) {
      const currentProjectId = selectedProjectId || projectId
      const previousProjectId = previousProjectIdRef.current

      // 🐛 FIX: Detect project switch
      const projectChanged = currentProjectId !== previousProjectId
      previousProjectIdRef.current = currentProjectId

      let modelToUse: string | null = null

      if (currentProjectId) {
        // Project context - use project's preferred model
        const storageKey = `model_project_${currentProjectId}`
        const projectModel = localStorage.getItem(storageKey)

        if (projectModel) {
          modelToUse = projectModel
          console.log(`📥 ${projectChanged ? 'Project switched! ' : ''}Loaded model for project ${currentProjectId}:`, projectModel)
        } else {
          // Project has no model set, use global default
          const globalModel = localStorage.getItem('globalDefaultModel')
          modelToUse = globalModel
          console.log(`📥 Project has no saved model, using global default:`, globalModel)
        }
      } else {
        // Global context - use global default
        const globalModel = localStorage.getItem('globalDefaultModel')
        modelToUse = globalModel
        console.log(`📥 Loaded global default model:`, globalModel)
      }

      if (modelToUse && modelToUse !== selectedModel) {
        console.log(`🔄 Updating model from "${selectedModel}" to "${modelToUse}"`)
        setSelectedModel(modelToUse)
      }
    }
  }, [selectedProjectId, projectId, isHydrated])

  // 🆕 Save selected model to appropriate context (global or project-specific)
  // 🐛 FIX: Only depend on selectedModel to avoid overwriting on project switch
  useEffect(() => {
    if (typeof window !== 'undefined' && selectedModel && isHydrated) {
      // Use current project context (at time of model selection)
      const currentProjectId = selectedProjectId || projectId

      if (currentProjectId) {
        // Save to project preferences
        const storageKey = `model_project_${currentProjectId}`
        localStorage.setItem(storageKey, selectedModel)
        console.log(`💾 Saved model for project ${currentProjectId}:`, selectedModel)
      } else {
        // Save as global default
        localStorage.setItem('globalDefaultModel', selectedModel)
        console.log(`💾 Saved global default model:`, selectedModel)
      }

      // ALWAYS save to globalSelectedModel for cross-component access
      // This allows SmartExtractor, SmartTemplateMapper, etc. to access the selected model
      localStorage.setItem('globalSelectedModel', selectedModel)
      console.log(`💾 Saved globalSelectedModel for all components:`, selectedModel)
    }
  }, [selectedModel, isHydrated])  // 🐛 FIX: Removed selectedProjectId and projectId from dependencies

  // Helper function to get current RAG config - always fresh
  const getCurrentConfig = (): RAGConfig => {
    return ragConfigProp || getCurrentRAGConfig()
  }

  // Toggle metrics expansion for a specific message
  const toggleMetricsExpansion = (index: number) => {
    setExpandedMetrics(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  // Toggle Brain View expansion for a specific message
  const toggleBrainViewExpansion = (index: number) => {
    setExpandedBrainView(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize session ID and load messages on mount (client-side only)
  useEffect(() => {
    // If projectId prop is provided (from ProjectDetail), use project-specific session
    let id: string
    if (projectId) {
      const storageKey = `session_project_${projectId}`
      id = localStorage.getItem(storageKey) || `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem(storageKey, id)
      setSelectedProjectId(projectId) // Set selected project to match prop
      console.log(`📁 Initializing with project session: ${id} for project ${projectId}`)
    } else {
      // Global session (no project)
      id = localStorage.getItem('session_global') || getSessionId()
      localStorage.setItem('session_global', id)
      console.log(`🌐 Initializing with global session: ${id}`)
    }

    setSessionId(id)

    // Load messages from localStorage after hydration
    if (id) {
      const loadedMessages = loadMessages(id)
      setMessages(loadedMessages)
      console.log(`📥 Loaded ${loadedMessages.length} messages for session ${id}`)
    }

    setIsHydrated(true)
  }, [])

  // Save messages to localStorage whenever they change (only after hydration)
  // Use ref to track last saved session to prevent cross-contamination
  const lastSavedSessionRef = useRef<string | null>(null)

  // 🆕 MEMORY OPTIMIZATION: Debounced save to reduce localStorage writes
  useEffect(() => {
    if (isHydrated && sessionId && messages.length > 0) {
      // Only save if we're saving to the same session we loaded from
      if (!lastSavedSessionRef.current || lastSavedSessionRef.current === sessionId) {
        // Debounce: Wait 1 second after last message before saving
        const timeoutId = setTimeout(() => {
          saveMessages(sessionId, messages)
          lastSavedSessionRef.current = sessionId
          console.log(`💾 Debounced save: ${messages.length} messages for session ${sessionId}`)
        }, 1000)

        // Cleanup: Cancel previous timeout if messages change again
        return () => clearTimeout(timeoutId)
      }
    }
  }, [messages, sessionId, isHydrated])

  // 🆕 MEMORY OPTIMIZATION: Memory usage monitoring (development only)
  useEffect(() => {
    if (typeof window === 'undefined' || process.env.NODE_ENV !== 'development') return

    const checkMemory = () => {
      // Chrome-specific memory API
      if ('memory' in performance) {
        const memory = (performance as any).memory
        const usedMB = (memory.usedJSHeapSize / 1024 / 1024).toFixed(2)
        const totalMB = (memory.totalJSHeapSize / 1024 / 1024).toFixed(2)
        const limitMB = (memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)

        console.log(`💾 Memory Usage: ${usedMB} MB / ${totalMB} MB (Limit: ${limitMB} MB)`)
        console.log(`   Messages in memory: ${messages.length}`)
        console.log(`   localStorage keys: ${Object.keys(localStorage).filter(k => k.startsWith('chat_messages_')).length}`)

        // Warn if memory usage is high
        if (memory.usedJSHeapSize / memory.jsHeapSizeLimit > 0.9) {
          console.warn('⚠️  Memory usage is high (>90%)! Consider clearing old sessions.')
        }
      }
    }

    // Check memory every 30 seconds in development
    const interval = setInterval(checkMemory, 30000)

    // Initial check after 5 seconds
    const initialTimeout = setTimeout(checkMemory, 5000)

    return () => {
      clearInterval(interval)
      clearTimeout(initialTimeout)
    }
  }, [messages.length])

  // Listen for new chat event from parent
  useEffect(() => {
    const handleNewChat = (event: CustomEvent) => {
      const newSessionId = event.detail?.sessionId
      if (newSessionId) {
        console.log('🆕 Starting new chat session:', newSessionId)
        setSessionId(newSessionId)
        setMessages([{
          role: 'assistant',
          content: 'Hello! I\'m your enterprise RAG assistant. How can I help you today?',
          timestamp: new Date()
        }])
        setAttachedFiles([])
        setInput('')
      }
    }

    window.addEventListener('new-chat', handleNewChat as EventListener)
    return () => window.removeEventListener('new-chat', handleNewChat as EventListener)
  }, [])

  // 🐛 FIX: Reload session when selectedProjectId changes (from dropdown)
  useEffect(() => {
    if (!isHydrated || projectId) return // Skip if not hydrated yet, or if using fixed projectId prop

    const currentProjectId = selectedProjectId || null
    let sessionKey: string
    let newSessionId: string

    if (currentProjectId) {
      // Project-specific session
      sessionKey = `session_project_${currentProjectId}`
      newSessionId = localStorage.getItem(sessionKey) || `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem(sessionKey, newSessionId)
      console.log(`📁 Project changed! Loading session for project ${currentProjectId}:`, newSessionId)
    } else {
      // Global session
      sessionKey = 'session_global'
      newSessionId = localStorage.getItem(sessionKey) || getSessionId()
      localStorage.setItem(sessionKey, newSessionId)
      console.log(`🌐 Switched to global session:`, newSessionId)
    }

    // Only update if session actually changed
    if (newSessionId !== sessionId) {
      setSessionId(newSessionId)

      // Load messages for this session
      const loadedMessages = loadMessages(newSessionId)
      setMessages(loadedMessages)
      console.log(`📥 Loaded ${loadedMessages.length} messages for session ${newSessionId}`)

      // Clear input and attachments
      setInput('')
      setAttachedFiles([])
    }
  }, [selectedProjectId, isHydrated, projectId])

  // Listen for session-changed event (when loading from history)
  useEffect(() => {
    const handleSessionChanged = async (event: CustomEvent) => {
      const loadSessionId = event.detail?.sessionId
      if (loadSessionId) {
        console.log('📂 Loading session from history:', loadSessionId)
        setSessionId(loadSessionId)

        // Fetch messages from backend
        try {
          const response = await fetch(`${API_URL}/api/v1/sessions/${loadSessionId}/messages`)
          if (response.ok) {
            const data = await response.json()
            const loadedMessages = data.messages.map((msg: any) => ({
              role: msg.role,
              content: msg.content,
              timestamp: new Date(msg.created_at),
              sources: msg.sources,
              modelUsed: msg.model_used,
              tokensUsed: msg.tokens_used,
              latencyMs: msg.latency_ms
            }))

            if (loadedMessages.length > 0) {
              setMessages(loadedMessages)
              console.log(`✅ Loaded ${loadedMessages.length} messages from backend`)
            } else {
              // No messages in backend, try localStorage
              const localMessages = loadMessages(loadSessionId)
              setMessages(localMessages)
              console.log(`📦 Loaded ${localMessages.length} messages from localStorage`)
            }

            // 🆕 Update UI context to match session's project and model
            if (data.project_id) {
              console.log('📁 Setting project context from session:', data.project_id)
              setSelectedProjectId(data.project_id)
              // Save to localStorage for sync with FileUpload
              localStorage.setItem('selected_project_id', data.project_id)
            } else {
              console.log('🌐 Session has no project, clearing project context')
              setSelectedProjectId(null)
              localStorage.removeItem('selected_project_id')
            }

            if (data.most_used_model) {
              console.log('🤖 Setting model context from session:', data.most_used_model)
              setSelectedModel(data.most_used_model)
              // Note: Model will be saved to appropriate context by existing useEffect (lines 390-406)
            }
          } else {
            // Fallback to localStorage
            const localMessages = loadMessages(loadSessionId)
            setMessages(localMessages)
            console.log(`📦 Backend failed, loaded ${localMessages.length} messages from localStorage`)
          }
        } catch (error) {
          console.error('Error loading session messages:', error)
          // Fallback to localStorage
          const localMessages = loadMessages(loadSessionId)
          setMessages(localMessages)
        }

        setAttachedFiles([])
        setInput('')
      }
    }

    window.addEventListener('session-changed', handleSessionChanged as EventListener)
    return () => window.removeEventListener('session-changed', handleSessionChanged as EventListener)
  }, [])

  // 🆕 Load available projects on mount
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const token = localStorage.getItem('access_token')
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const response = await axios.get(`${API_URL}/api/v1/projects`, { headers })
        setAvailableProjects(response.data || [])
        console.log('📁 Loaded projects:', response.data.length)
      } catch (error) {
        console.error('Failed to load projects:', error)
      }
    }
    loadProjects()
  }, [])

  // 🆕 Handle project switching - create separate sessions per project
  useEffect(() => {
    if (!isHydrated) return // Wait for initial hydration
    if (projectId) return // If embedded in ProjectDetail, don't switch sessions

    // Get or create session for this project
    const getProjectSession = (projId: string | null): string => {
      const storageKey = projId ? `session_project_${projId}` : 'session_global'
      let projSessionId = localStorage.getItem(storageKey)

      if (!projSessionId) {
        // Create new session for this project
        projSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        localStorage.setItem(storageKey, projSessionId)
        console.log(`🆕 Created new session for ${projId ? `project ${projId}` : 'global'}: ${projSessionId}`)
      } else {
        console.log(`📂 Loaded existing session for ${projId ? `project ${projId}` : 'global'}: ${projSessionId}`)
      }

      return projSessionId
    }

    // Switch to project-specific session
    const newSessionId = getProjectSession(selectedProjectId)

    if (newSessionId !== sessionId) {
      console.log(`🔄 Switching session from ${sessionId} to ${newSessionId}`)

      // CRITICAL: Save current messages to OLD session before switching
      if (sessionId && messages.length > 0) {
        saveMessages(sessionId, messages)
        console.log(`💾 Saved ${messages.length} messages to old session ${sessionId}`)
      }

      // Switch to new session
      setSessionId(newSessionId)
      lastSavedSessionRef.current = newSessionId // Update ref to prevent cross-contamination

      // Load messages for this project's session
      const loadedMessages = loadMessages(newSessionId)
      setMessages(loadedMessages)
      console.log(`📥 Loaded ${loadedMessages.length} messages for ${selectedProjectId ? 'project' : 'global'} session`)

      // Clear any attached files when switching projects
      setAttachedFiles([])
      setInput('')
    }
  }, [selectedProjectId, isHydrated])

  // Handle file attachment
  const handleFileAttach = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setAttachedFiles(prev => [...prev, ...files])
    // Reset input to allow re-uploading same file
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeAttachedFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Handle feedback (thumbs up/down)
  const handleFeedback = async (messageIndex: number, type: 'thumbs_up' | 'thumbs_down') => {
    try {
      const message = messages[messageIndex]

      await axios.post(`${API_URL}/api/v1/evaluation/feedback`, {
        session_id: sessionId,
        thumbs_up: type === 'thumbs_up',
        feedback_type: 'inline',
        feedback_text: type === 'thumbs_up' ? 'User found this helpful' : 'User found this unhelpful'
      })

      // Update message to show feedback was recorded
      const updatedMessages = [...messages]
      updatedMessages[messageIndex] = {
        ...message,
        userFeedback: type
      }
      setMessages(updatedMessages)

      console.log(`✅ Feedback recorded: ${type}`)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  // Handle star rating
  const handleRating = async (messageIndex: number, rating: number) => {
    try {
      const message = messages[messageIndex]

      await axios.post(`${API_URL}/api/v1/evaluation/feedback`, {
        session_id: sessionId,
        rating: rating,
        accuracy_rating: rating,
        helpfulness_rating: rating,
        clarity_rating: rating,
        feedback_type: 'inline'
      })

      // Update message to show rating was recorded
      const updatedMessages = [...messages]
      updatedMessages[messageIndex] = {
        ...message,
        userFeedback: 'rated',
        userRating: rating
      }
      setMessages(updatedMessages)

      console.log(`✅ Rating recorded: ${rating} stars`)
    } catch (error) {
      console.error('Failed to submit rating:', error)
    }
  }

  // Poll document status until processing is complete
  const waitForDocumentProcessing = async (
    documentIds: string[],
    maxWaitSeconds = 30
  ): Promise<boolean> => {
    const startTime = Date.now()
    const pollIntervalMs = 1000 // Check every 1 second

    console.log(`⏳ Waiting for ${documentIds.length} documents to finish processing...`)

    while ((Date.now() - startTime) / 1000 < maxWaitSeconds) {
      try {
        // Check status of all uploaded documents
        const statusChecks = await Promise.all(
          documentIds.map(docId =>
            axios.get(`${API_URL}/api/v1/documents/${docId}/status`)
          )
        )

        const allCompleted = statusChecks.every(response =>
          response.data.processing_status === 'completed'
        )

        if (allCompleted) {
          console.log(`✅ All ${documentIds.length} documents processing complete!`)
          return true
        }

        // Check if any failed
        const anyFailed = statusChecks.some(response =>
          response.data.processing_status === 'failed'
        )

        if (anyFailed) {
          console.error(`❌ Some documents failed to process`)
          return false
        }

        // Still processing, wait and try again
        console.log(`⏳ Still processing... (${Math.floor((Date.now() - startTime) / 1000)}s elapsed)`)
        await new Promise(resolve => setTimeout(resolve, pollIntervalMs))

      } catch (error) {
        console.error('Error checking document status:', error)
        // Continue polling even if status check fails
        await new Promise(resolve => setTimeout(resolve, pollIntervalMs))
      }
    }

    console.warn(`⚠️  Timeout waiting for document processing after ${maxWaitSeconds}s`)
    return false
  }

  // Upload files to backend with session ID
  const uploadAttachedFiles = async (): Promise<{
    success: boolean
    duplicates: string[]
    documentIds: string[]  // 🆕 Return document IDs
  }> => {
    if (attachedFiles.length === 0) return { success: true, duplicates: [], documentIds: [] }

    setUploadingFiles(true)
    const duplicates: string[] = []
    const documentIds: string[] = []  // 🆕 Track uploaded document IDs
    let hasErrors = false

    try {
      for (const file of attachedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('session_id', sessionId) // 🎯 Pass session ID!

        // 🔧 FIX: Only send project_id if we have a valid value (not empty string)
        const globalProject = availableProjects.find(p => p.name.toLowerCase() === 'global')
        const activeProjectId = selectedProjectId || projectId || globalProject?.id || null
        if (activeProjectId) {
          formData.append('project_id', activeProjectId) // 🎯 Pass project ID if available!
          console.log(`📤 Uploading file with project_id: ${activeProjectId}`)
        } else {
          console.log(`📤 Uploading file without project_id - backend will use session's project or Global`)
        }


        const token = localStorage.getItem('access_token')
        console.log('[ChatInterface] Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NULL')

        const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          }
        })

        // Check if file was duplicate
        if (response.data.duplicate || !response.data.success) {
          duplicates.push(file.name)
          console.log(`⚠️ Duplicate file skipped: ${file.name}`)
        } else {
          // 🆕 Collect document ID for status polling
          if (response.data.document_id) {
            documentIds.push(response.data.document_id)
          }
          console.log(`✅ Uploaded ${file.name} to session ${sessionId}`)
        }
      }
      setAttachedFiles([]) // Clear after processing all files
      setFilesJustUploaded(true) // Signal that files were just uploaded
      return { success: !hasErrors, duplicates, documentIds }  // 🆕 Return IDs
    } catch (error) {
      console.error('Error uploading files:', error)
      hasErrors = true
      return { success: false, duplicates, documentIds }
    } finally {
      setUploadingFiles(false)
    }
  }

  const handleSendMessage = async () => {
    if ((!input.trim() && attachedFiles.length === 0) || isLoading) return

    // 🎯 SMART UPLOAD SYNC: Upload files AND wait for processing
    if (attachedFiles.length > 0) {
      const uploadResult = await uploadAttachedFiles()

      if (!uploadResult.success) {
        const errorMessage: Message = {
          role: 'assistant',
          content: 'Sorry, there was an error uploading your files. Please try again.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
        return
      }

      // 🆕 WAIT FOR PROCESSING TO COMPLETE before sending query
      if (uploadResult.documentIds.length > 0 && input.trim()) {
        // Show "processing" indicator to user
        setIsLoading(true)

        const processingComplete = await waitForDocumentProcessing(
          uploadResult.documentIds,
          30 // Wait up to 30 seconds
        )

        setIsLoading(false)

        if (!processingComplete) {
          const warningMessage: Message = {
            role: 'assistant',
            content: 'Warning: Document processing is taking longer than expected. Your query may not have access to all document content yet. You can try asking again in a few moments.',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, warningMessage])
          // Continue with query anyway - backend has its own 30s wait
        } else {
          console.log('✅ Documents ready, proceeding with query')
        }
      }

      // If only files were attached without a message, show success message
      if (!input.trim()) {
        let successContent = 'Files uploaded and processed successfully! You can now ask questions about them.'

        // Add note about duplicates if any
        if (uploadResult.duplicates.length > 0) {
          successContent += `\n\n**Note:** The following files were already uploaded to this session and were skipped:\n${uploadResult.duplicates.map(f => `- ${f}`).join('\n')}`
        }

        const successMessage: Message = {
          role: 'assistant',
          content: successContent,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
        return
      }
    }

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // 🆕 Get fresh RAG config to ensure we use latest slider values
      const currentRagConfig = getCurrentConfig()

      const formData = new FormData()
      formData.append('query', input)
      formData.append('session_id', sessionId) // 🎯 Pass session ID!

      // 🔧 FIX: Only send project_id if we have a valid value (not empty string)
      const globalProject = availableProjects.find(p => p.name.toLowerCase() === 'global')
      const activeProjectId = selectedProjectId || projectId || globalProject?.id || null
      if (activeProjectId) {
        formData.append('project_id', activeProjectId) // 🎯 Pass project ID if available!
        console.log(`📤 Querying with project_id: ${activeProjectId}`)
      } else {
        console.log(`📤 Querying without project_id - backend will use session's project or Global`)
      }

      formData.append('use_cache', 'true')

      // Add selected model if specified
      if (selectedModel) {
        console.log('🎯 Using selected model for query:', selectedModel)
        formData.append('model_id', selectedModel)
      } else {
        console.log('⚠️ No model selected, backend will use default')
      }

      // 🆕 UNIFIED CONFIG: Pass ALL 48 parameters as single JSON for dynamic per-query control
      // 🆕 FIX: Always try to load from localStorage BEFORE sending query
      let configToSend = unifiedConfig
      if (!configToSend && typeof window !== 'undefined') {
        const savedConfig = localStorage.getItem('userWeightsConfig')
        if (savedConfig) {
          try {
            configToSend = JSON.parse(savedConfig)
            console.log('📦 Loaded config from localStorage for this query (unifiedConfig state was null)')
          } catch (e) {
            console.error('Failed to parse localStorage config:', e)
          }
        }
      }

      if (configToSend) {
        formData.append('unified_config', JSON.stringify(configToSend))
        console.log('📦 Passing unified config with strategy weights:', configToSend.strategy_weights)
        console.log('   → Top K:', configToSend.rag_settings?.top_k || 'N/A')
        console.log('   → Semantic Weight:', configToSend.reranking_weights?.semantic || 'N/A')
        console.log('   → Keyword Weight:', configToSend.reranking_weights?.keyword || 'N/A')
      } else {
        // Fallback: Pass individual RAG config parameters if unified config not loaded yet
        console.warn('⚠️ Unified config not loaded, falling back to individual parameters')
        formData.append('top_k', currentRagConfig.top_k.toString())
        formData.append('similarity_threshold', currentRagConfig.similarity_threshold.toString())
        formData.append('min_similarity_threshold', currentRagConfig.min_similarity_threshold.toString())
        formData.append('no_relevant_docs_threshold', currentRagConfig.no_relevant_docs_threshold.toString())
        formData.append('semantic_weight', currentRagConfig.semantic_weight.toString())
        formData.append('keyword_weight', currentRagConfig.keyword_weight.toString())
      }

      // 🆕 Add metrics settings - enable evaluation flag
      formData.append('enable_evaluation', metricsSettings.enableEvaluation.toString())

      // 🆕 Pass conversation history for context continuity
      // Include last 10 messages (5 exchanges) for context window
      const recentMessages = messages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      formData.append('conversation_history', JSON.stringify(recentMessages))

      // 🆕 Add enabled tools and selected agent
      formData.append('enabled_tools', JSON.stringify(enabledTools))
      formData.append('selected_agent', selectedAgent)

      console.log(`📤 Querying with session ${sessionId} and ${recentMessages.length} context messages`)
      console.log(`🔧 Tools enabled: ${enabledTools.length}/${AVAILABLE_TOOLS.length}`)
      console.log(`🤖 Agent selected: ${selectedAgent}`)

      const response = await axios.post(`${API_URL}/api/v1/query`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        model: response.data.model,
        model_name: response.data.model_name,
        contextInfo: response.data.context_info,
        timestamp: new Date(),
        // 🆕 Capture performance metrics
        latency_ms: response.data.latency_ms,
        tokens_used: response.data.tokens_used,
        num_sources: response.data.sources?.length || 0,
        cached: response.data.cached || false,
        // 🆕 Capture evaluation metrics
        quality_metrics: response.data.quality_metrics,
        // 🆕 Capture RAG settings used for this query
        rag_settings: response.data.rag_settings,
        // 🆕 Capture tool usage tracking
        tools_used: response.data.tools_used,
        // 🧠 Capture debug context for inline Brain View
        debug_context: response.data.debug_context
      }

      // 🧠 Update Brain View with debug context (if enabled and present)
      if (response.data.debug_context) {
        setCurrentDebugContext(response.data.debug_context)
        console.log('🧠 Brain View: Received debug context', response.data.debug_context)
      }

      // Log context usage
      if (response.data.context_info) {
        console.log(`📚 Context: ${response.data.context_info}`)
      }

      // Log quality metrics if available
      if (response.data.quality_metrics) {
        console.log(`📊 Quality Metrics:`, response.data.quality_metrics)
      }

      // Log RAG settings if available
      if (response.data.rag_settings) {
        console.log(`⚙️ RAG Settings:`, response.data.rag_settings)
      }

      // 🆕 Log tool usage if available
      if (response.data.tools_used && response.data.tools_used.length > 0) {
        console.log(`🔧 Tools Used (${response.data.tools_used.length}):`, response.data.tools_used)
        console.log(`🔧 First tool structure:`, JSON.stringify(response.data.tools_used[0], null, 2))
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      // Don't send if prompt palette is open
      if (!showPromptPalette) {
        handleSendMessage()
      }
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInput(value)

    // Detect slash command
    if (value.startsWith('/')) {
      setShowPromptPalette(true)
      // Extract search query after "/"
      const query = value.slice(1)
      setPromptSearchQuery(query)
    } else {
      setShowPromptPalette(false)
      setPromptSearchQuery('')
    }
  }

  const handleSelectPrompt = (promptText: string) => {
    setInput(promptText)
    setShowPromptPalette(false)
    setPromptSearchQuery('')
  }

  const handleClosePalette = () => {
    setShowPromptPalette(false)
    setPromptSearchQuery('')
  }

  const handleClearSession = async () => {
    if (!confirm('Clear this session? This will:\n• Remove all messages\n• Remove document associations\n• Start a fresh conversation\n\nDocuments will remain in the system for future sessions.')) {
      return
    }

    try {
      // Clear session on backend
      await axios.post(`${API_URL}/api/v1/sessions/${sessionId}/clear`)
      console.log(`🧹 Cleared session: ${sessionId}`)

      // Clear messages from localStorage for this session
      localStorage.removeItem(`chat_messages_${sessionId}`)

      // Generate new session ID
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('chat_session_id', newSessionId)
      setSessionId(newSessionId)
      console.log('🆕 New session started:', newSessionId)

      // Reset frontend state
      setMessages([{
        role: 'assistant',
        content: 'Session cleared! Starting fresh. You can upload new files or ask me anything.',
        timestamp: new Date()
      }])
      setAttachedFiles([])
    } catch (error) {
      console.error('Error clearing session:', error)
      alert('Failed to clear session. Please try again.')
    }
  }

  if (activeTab === 'upload') {
    return <FileUpload />
  }

  if (activeTab === 'scrape') {
    // Use simple WebScraper with session management
    const WebScraperComponent = require('./WebScraper').default
    return <WebScraperComponent sessionId={sessionId} />
  }

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 overflow-hidden">
      {/* Sleek Modern Header - Model & Project Controls */}
      {!hideHeader && (
      <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="max-w-5xl mx-auto px-4 py-2.5">
          <div className="flex items-center justify-between gap-4">
            {/* Left Section: Model & Project Controls */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* Model Selector - Compact */}
              <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg px-3 py-1.5 border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Model
                </span>
                <div className="border-l border-slate-300 dark:border-slate-600 h-4" />
                <ModelSelector
                  selectedModel={selectedModel}
                  onModelChange={setSelectedModel}
                />
              </div>

              {/* Project Selector - Sleek Dropdown (only show if not in project context) */}
              {!projectId && (
                <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg px-3 py-1.5 border border-slate-200 dark:border-slate-700 flex-1 max-w-xs">
                  <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Project
                  </span>
                  <div className="border-l border-slate-300 dark:border-slate-600 h-4" />
                  <select
                    value={selectedProjectId || ''}
                    onChange={(e) => {
                      const projectId = e.target.value || null
                      setSelectedProjectId(projectId)
                      // Save to localStorage for FileUpload sync
                      if (projectId) {
                        localStorage.setItem('selected_project_id', projectId)
                      } else {
                        localStorage.removeItem('selected_project_id')
                      }
                      console.log('📁 Selected project ID saved to localStorage:', projectId)
                    }}
                    className="flex-1 min-w-0 bg-transparent text-xs text-slate-700 dark:text-slate-300 font-medium focus:outline-none cursor-pointer"
                  >
                    {/* Show Global project from database if exists, otherwise show hardcoded fallback */}
                    {(() => {
                      const globalProject = availableProjects.find(p => p.name.toLowerCase() === 'global')
                      if (globalProject) {
                        return (
                          <option value={globalProject.id}>
                            Global ({globalProject.file_count})
                          </option>
                        )
                      } else {
                        return <option value="">Global (All Projects)</option>
                      }
                    })()}
                    {/* Show all other non-global projects */}
                    {availableProjects
                      .filter(project => project.name.toLowerCase() !== 'global')
                      .map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name} ({project.file_count})
                        </option>
                      ))}
                  </select>
                </div>
              )}
            </div>

            {/* Right Section: Context Badge & Actions */}
            <div className="flex items-center gap-2">
              {/* Context Badge */}
              <div className="flex items-center gap-2 text-xs">
                {selectedProjectId ? (
                  <span className="px-2.5 py-1 rounded-md bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium border border-primary-200 dark:border-primary-800 flex items-center gap-1.5">
                    <span className="text-primary-600 dark:text-primary-400">📁</span>
                    {availableProjects.find(p => p.id === selectedProjectId)?.name || 'Project'}
                  </span>
                ) : projectId ? null : (
                  <span className="px-2.5 py-1 rounded-md bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-medium border border-slate-200 dark:border-slate-700 flex items-center gap-1.5">
                    <span>🌐</span>
                    Global
                  </span>
                )}
                <span className="text-slate-400 dark:text-slate-600">•</span>
                <span className="text-slate-500 dark:text-slate-400">
                  {messages.length - 1} msg{messages.length - 1 !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Back to Project Button (only show when in project context) */}
              {projectId && onBackToProject && (
                <button
                  onClick={onBackToProject}
                  className="text-xs text-slate-600 hover:text-primary-600 dark:text-slate-400 dark:hover:text-primary-400 flex items-center gap-1.5 px-2.5 py-1 rounded-md hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all border border-transparent hover:border-primary-200 dark:hover:border-primary-800"
                  title="Back to project"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span className="font-medium">Back</span>
                </button>
              )}

              {/* Clear Session Button */}
              <button
                onClick={handleClearSession}
                className="text-xs text-slate-600 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 flex items-center gap-1.5 px-2.5 py-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 transition-all border border-transparent hover:border-red-200 dark:hover:border-red-800"
                title="Clear session and start fresh"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span className="font-medium">Clear</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* 🆕 Tool & Agent Selector - Collapsible Panel */}
      <div className="border-b border-sage-100 bg-sage-50/30 px-4 py-2">
        <div className="max-w-md mx-auto">
          <ToolAgentSelector
            enabledTools={enabledTools}
            onToolsChange={setEnabledTools}
            selectedAgent={selectedAgent}
            onAgentChange={setSelectedAgent}
          />
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message, index) => (
          <div
            key={index}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-semibold text-sm">
                AI
              </div>
            )}
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-br-md shadow-sm'
                  : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-md border border-slate-200 dark:border-slate-700'
              }`}
            >
              <div className={`markdown-content ${message.role === 'user' ? 'user-message-text' : ''}`}>
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>

              {/* Model used and context info (for assistant messages) */}
              {message.role === 'assistant' && (message.model_name || message.model || message.contextInfo) && (
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  {(message.model_name || message.model) && (
                    <span className="text-xs px-2 py-1 rounded-md bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/30 dark:to-blue-900/30 text-purple-700 dark:text-purple-300 font-medium border border-purple-200 dark:border-purple-800 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M13 7H7v6h6V7z"/>
                        <path fillRule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clipRule="evenodd"/>
                      </svg>
                      {message.model_name || message.model}
                    </span>
                  )}
                  {message.contextInfo && (
                    <span className="text-xs px-1.5 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                      📚 {message.contextInfo}
                    </span>
                  )}
                </div>
              )}

              {/* 🆕 Inline Eval Metrics - Quick at-a-glance view (respects user settings) */}
              {message.role === 'assistant' && (metricsSettings.showPerformanceMetrics || metricsSettings.enableEvaluation) && (message.quality_metrics || message.num_sources !== undefined || message.latency_ms) && (
                <div className="mt-2 flex items-center gap-2 flex-wrap text-[10px]">
                  {/* Quality Score - only if evaluation metrics enabled */}
                  {metricsSettings.enableEvaluation && message.quality_metrics?.rag_score !== null && message.quality_metrics?.rag_score !== undefined && (
                    <span className={`px-2 py-0.5 rounded-full font-medium ${
                      message.quality_metrics.rag_score >= 0.7 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                      message.quality_metrics.rag_score >= 0.4 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' :
                      'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                    }`}>
                      ✨ Quality: {(message.quality_metrics.rag_score * 100).toFixed(0)}%
                    </span>
                  )}

                  {/* Number of Sources - only if performance metrics enabled */}
                  {metricsSettings.showPerformanceMetrics && message.num_sources !== undefined && (
                    <span className="px-2 py-0.5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
                      📄 {message.num_sources} source{message.num_sources !== 1 ? 's' : ''}
                    </span>
                  )}

                  {/* Latency - only if performance metrics enabled */}
                  {metricsSettings.showPerformanceMetrics && message.latency_ms && (
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      ⚡ {message.latency_ms.toFixed(0)}ms
                    </span>
                  )}

                  {/* Classification - only if evaluation metrics enabled */}
                  {metricsSettings.enableEvaluation && message.quality_metrics?.classification_type && message.quality_metrics.classification_type !== 'None' && (
                    <span className="px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                      🏷️ {message.quality_metrics.classification_type}
                    </span>
                  )}

                  {/* 🆕 Tools Used - shows which tools/steps were used and in what order */}
                  {metricsSettings.showToolsUsed && message.tools_used && message.tools_used.length > 0 && (
                    <span
                      className="px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 cursor-help"
                      title={`Tool execution order:\n${message.tools_used.map((t, i) => `${i + 1}. ${t.tool_name || t.tool_id || 'Unknown Tool'}${t.details ? ` - ${t.details}` : ''}`).join('\n')}`}
                    >
                      🔧 {message.tools_used.length} tool{message.tools_used.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )}

              {/* Collapsible Metrics & Sources Section */}
              {message.role === 'assistant' && (message.latency_ms || message.sources?.length || message.quality_metrics) && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                  <button
                    onClick={() => toggleMetricsExpansion(index)}
                    className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors w-full"
                  >
                    {expandedMetrics[index] ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                    <span>
                      {expandedMetrics[index] ? 'Hide' : 'Show'} Metrics & Sources
                      {!expandedMetrics[index] && message.sources && message.sources.length > 0 && (
                        <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700">
                          {message.sources.length}
                        </span>
                      )}
                    </span>
                  </button>

                  {expandedMetrics[index] && (
                    <div className="mt-3 space-y-3">
                      {/* Performance Metrics with RAG Settings - conditionally shown */}
                      {metricsSettings.showPerformanceMetrics && (
                        <PerformanceMetrics
                          metrics={{
                            latency_ms: message.latency_ms,
                            tokens_used: message.tokens_used,
                            num_sources: message.num_sources,
                            cached: message.cached,
                            model_used: message.model,
                            model_name: message.model_name
                          }}
                          ragSettings={message.rag_settings}
                        />
                      )}

                      {/* Evaluation Metrics - shown only if enabled and present */}
                      {metricsSettings.enableEvaluation && message.quality_metrics && (
                        <EvaluationMetrics metrics={message.quality_metrics} />
                      )}

                      {/* 🆕 Detailed Tool Usage - shows execution order and timing */}
                      {metricsSettings.showToolsUsed && message.tools_used && message.tools_used.length > 0 && (
                        <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                          <p className="text-xs font-semibold mb-2 text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                            <span className="text-indigo-500">🔧</span>
                            Tool Execution Order:
                          </p>
                          <div className="space-y-1">
                            {message.tools_used.map((tool, idx) => (
                              <div
                                key={tool.tool_id || idx}
                                className="text-xs bg-indigo-50 dark:bg-indigo-950/20 p-2 rounded-lg border border-indigo-200 dark:border-indigo-800/30 flex items-start gap-2"
                              >
                                <span className="text-[10px] font-mono font-semibold text-indigo-600 dark:text-indigo-400 min-w-[20px]">
                                  {tool.order || (idx + 1)}.
                                </span>
                                <div className="flex-1">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-indigo-900 dark:text-indigo-100">
                                      {tool.tool_name || tool.tool?.replace(/_/g, ' ') || 'Unknown Tool'}
                                    </span>
                                    <div className="flex items-center gap-2">
                                      <span className="text-[10px] text-slate-500 dark:text-slate-400">
                                        {(tool.latency_ms || tool.timestamp_ms || 0).toFixed(0)}ms
                                      </span>
                                      {tool.status && (
                                        <span className={`text-[10px] font-semibold ${
                                          tool.status === 'success'
                                            ? 'text-green-600 dark:text-green-400'
                                            : 'text-red-600 dark:text-red-400'
                                        }`}>
                                          {tool.status === 'success' ? '✅' : '❌'}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  {tool.details && (
                                    <p className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5 italic">
                                      {tool.details}
                                    </p>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}


              {/* 🧠 Brain View - Inline Debug Context (No Component Import Issues) */}
              {message.role === 'assistant' && message.debug_context && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                  <button
                    onClick={() => toggleBrainViewExpansion(index)}
                    className="flex items-center gap-2 text-xs font-medium text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-200 transition-colors w-full"
                  >
                    {expandedBrainView[index] ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                    <span className="flex items-center gap-1.5">
                      🧠 {expandedBrainView[index] ? 'Hide' : 'Show'} Brain View
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30">
                        Debug Info
                      </span>
                    </span>
                  </button>

                  {expandedBrainView[index] && (
                    <div className="mt-3 space-y-3 text-xs">
                      {/* Routing Decision */}
                      {message.debug_context.routing_decision && (
                        <div className="bg-blue-50 dark:bg-blue-950/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                          <p className="font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                            🎯 Routing Decision
                          </p>
                          <div className="space-y-1 text-blue-800 dark:text-blue-200">
                            <div><strong>Strategy:</strong> {message.debug_context.routing_decision.strategy}</div>
                            <div><strong>Reason:</strong> {message.debug_context.routing_decision.reason}</div>
                            <div><strong>Confidence:</strong> {(message.debug_context.routing_decision.classification_confidence * 100).toFixed(0)}%</div>
                          </div>
                        </div>
                      )}

                      {/* Conversation History */}
                      {message.debug_context.conversation_history && (
                        <div className="bg-green-50 dark:bg-green-950/20 p-3 rounded-lg border border-green-200 dark:border-green-800">
                          <p className="font-semibold text-green-900 dark:text-green-100 mb-2 flex items-center gap-2">
                            💬 Conversation History
                          </p>
                          <div className="space-y-1 text-green-800 dark:text-green-200">
                            <div><strong>Messages Used:</strong> {message.debug_context.conversation_history.messages_used}</div>
                            <div className="text-[10px]">{message.debug_context.conversation_history.note}</div>
                          </div>
                        </div>
                      )}

                      {/* Tools Executed */}
                      {message.debug_context.tools_executed && (
                        <div className="bg-indigo-50 dark:bg-indigo-950/20 p-3 rounded-lg border border-indigo-200 dark:border-indigo-800">
                          <p className="font-semibold text-indigo-900 dark:text-indigo-100 mb-2 flex items-center gap-2">
                            🔧 Tools Executed
                          </p>
                          <div className="space-y-2">
                            {message.debug_context.tools_executed.query_time_tools?.map((tool: any, idx: number) => (
                              <div key={idx} className="text-indigo-800 dark:text-indigo-200 flex justify-between">
                                <span>{tool.tool_name}</span>
                                <span className="text-[10px]">{tool.latency_ms?.toFixed(0) || 0}ms</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Documents Retrieved */}
                      {message.debug_context.documents_retrieved && (
                        <div className="bg-amber-50 dark:bg-amber-950/20 p-3 rounded-lg border border-amber-200 dark:border-amber-800">
                          <p className="font-semibold text-amber-900 dark:text-amber-100 mb-2 flex items-center gap-2">
                            📄 Documents Retrieved
                          </p>
                          <div className="text-amber-800 dark:text-amber-200">
                            <div><strong>Total Chunks:</strong> {message.debug_context.documents_retrieved.total_chunks}</div>
                            {message.debug_context.documents_retrieved.chunks?.slice(0, 3).map((chunk: any, idx: number) => (
                              <div key={idx} className="text-[10px] mt-1">
                                {chunk.filename} (score: {chunk.similarity_score?.toFixed(3)})
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Performance Metrics */}
                      {message.debug_context.performance_metrics && (
                        <div className="bg-purple-50 dark:bg-purple-950/20 p-3 rounded-lg border border-purple-200 dark:border-purple-800">
                          <p className="font-semibold text-purple-900 dark:text-purple-100 mb-2 flex items-center gap-2">
                            ⚡ Performance
                          </p>
                          <div className="space-y-1 text-purple-800 dark:text-purple-200">
                            <div><strong>Total Latency:</strong> {message.debug_context.performance_metrics.total_latency_ms?.toFixed(0) || 0}ms</div>
                            <div><strong>LLM Time:</strong> {message.debug_context.performance_metrics.breakdown?.llm_generation?.toFixed(0) || 0}ms</div>
                            <div><strong>Model:</strong> {message.debug_context.performance_metrics.model_used}</div>
                            {message.debug_context.performance_metrics.tokens_used > 0 && (
                              <div><strong>Tokens:</strong> {message.debug_context.performance_metrics.tokens_used}</div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                          <p className="text-xs font-semibold mb-2 text-slate-600 dark:text-slate-400">
                            Sources:
                          </p>
                          <div className="space-y-2">
                            {message.sources.map((source, idx) => (
                              <div
                                key={idx}
                                className="text-xs bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700"
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex items-center gap-1.5">
                                    {source.source_type === 'scrape' ? (
                                      <ExternalLink className="w-3.5 h-3.5 text-primary-500 flex-shrink-0" />
                                    ) : (
                                      <FileText className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                                    )}
                                    <span className="font-medium text-slate-900 dark:text-white text-xs">
                                      {source.filename}
                                    </span>
                                    {source.memory_type === 'short-term' && (
                                      <span className="text-[10px] px-1 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                                        Session
                                      </span>
                                    )}
                                  </div>
                                  <span className="text-[10px] text-slate-500">
                                    {source.relevance !== undefined && source.relevance !== null && !isNaN(source.relevance)
                                      ? `${(source.relevance * 100).toFixed(0)}%`
                                      : 'N/A'}
                                  </span>
                                </div>
                                {source.source_url && (
                                  <a
                                    href={source.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[10px] text-primary-600 hover:underline mt-1 block truncate"
                                  >
                                    {source.source_url}
                                  </a>
                                )}
                                <p className="text-[10px] text-slate-600 dark:text-slate-400 mt-1.5 italic line-clamp-2">
                                  "{source.excerpt}"
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* User Feedback Section (Thumbs Up/Down & Star Ratings) - Compact */}
              {message.role === 'assistant' && (
                <div className="mt-2 flex items-center gap-3 text-xs">
                  {/* Thumbs Up/Down */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleFeedback(index, 'thumbs_up')}
                      disabled={(message as any).userFeedback === 'thumbs_up'}
                      className={`p-1 rounded transition-all ${
                        (message as any).userFeedback === 'thumbs_up'
                          ? 'bg-emerald-100 dark:bg-emerald-900/40'
                          : 'hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                      title="Helpful"
                    >
                      <span className="text-sm">👍</span>
                    </button>
                    <button
                      onClick={() => handleFeedback(index, 'thumbs_down')}
                      disabled={(message as any).userFeedback === 'thumbs_down'}
                      className={`p-1 rounded transition-all ${
                        (message as any).userFeedback === 'thumbs_down'
                          ? 'bg-red-100 dark:bg-red-900/40'
                          : 'hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                      title="Not helpful"
                    >
                      <span className="text-sm">👎</span>
                    </button>
                  </div>

                  {/* Star Ratings */}
                  <div className="flex items-center gap-0.5 pl-2 border-l border-slate-200 dark:border-slate-700">
                    <div className="flex gap-0.5">
                      {[1, 2, 3, 4, 5].map(star => (
                        <button
                          key={star}
                          onClick={() => handleRating(index, star)}
                          disabled={(message as any).userFeedback === 'rated'}
                          className="transition-transform hover:scale-110"
                          title={`${star} star${star > 1 ? 's' : ''}`}
                        >
                          <span className={`text-xs ${
                            (message as any).userRating && star <= (message as any).userRating
                              ? 'text-yellow-400'
                              : 'text-slate-300 dark:text-slate-600 hover:text-yellow-400'
                          }`}>
                            ★
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Show if feedback submitted - compact */}
                  {(message as any).userFeedback && (
                    <span className="ml-auto text-[10px] text-emerald-600 dark:text-emerald-400">
                      ✓ Thanks
                    </span>
                  )}
                </div>
              )}

              {/* Export Button */}
              {message.role === 'assistant' && (
                <button
                  onClick={() => setExportingMessageIndex(index)}
                  className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 transition-colors"
                >
                  <Download className="w-3 h-3" />
                  Export Response
                </button>
              )}

              <p className="text-[10px] text-slate-500 dark:text-slate-500 mt-2" suppressHydrationWarning>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white font-semibold text-sm">
                U
              </div>
            )}
          </div>
        ))}
        </div>

        {isLoading && (
          <div className="max-w-3xl mx-auto flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-semibold text-sm">
              AI
            </div>
            <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-bl-md px-4 py-3">
              <Loader2 className="w-5 h-5 animate-spin text-emerald-600 dark:text-emerald-400" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Uploaded Files List */}
      <UploadedFilesList
        sessionId={sessionId}
        projectId={selectedProjectId || undefined}  // 🆕 Pass project context
        forceExpand={filesJustUploaded}
        onExpandChange={(expanded) => {
          if (!expanded) setFilesJustUploaded(false)
        }}
      />

      {/* Input Area */}
      <div className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          {/* Attached Files Display */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 bg-primary-50 dark:bg-blue-900/20 text-primary-900 dark:text-primary-100 px-2.5 py-1.5 rounded-lg text-xs border border-primary-200 dark:border-primary-800"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span className="max-w-[200px] truncate">{file.name}</span>
                  <button
                    onClick={() => removeAttachedFile(index)}
                    className="hover:bg-primary-100 dark:hover:bg-primary-800 rounded p-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2 items-end">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              multiple
              accept=".pdf,.txt,.doc,.docx,.json,.md"
              className="hidden"
            />

            {/* File attachment button */}
            <button
              onClick={handleFileAttach}
              disabled={isLoading || uploadingFiles}
              className="p-3 text-slate-600 dark:text-slate-400 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              title="Attach files"
            >
              <Paperclip className="w-5 h-5" />
            </button>

            <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 focus-within:border-primary-500 dark:focus-within:border-primary-500 transition-colors relative">
              {/* Prompt Command Palette */}
              <PromptCommandPalette
                isOpen={showPromptPalette}
                onClose={handleClosePalette}
                onSelectPrompt={handleSelectPrompt}
                searchQuery={promptSearchQuery}
                module="chat"
              />

              <textarea
                value={input}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                placeholder="Type / for prompts or message Enterprise AI..."
                className="w-full resize-none bg-transparent px-4 py-3 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none"
                rows={1}
                disabled={isLoading || uploadingFiles}
              />
            </div>

            <button
              onClick={handleSendMessage}
              disabled={(attachedFiles.length === 0 && !input.trim()) || isLoading || uploadingFiles}
              className="p-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {isLoading || uploadingFiles ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Export Modal */}
      {exportingMessageIndex !== null && messages[exportingMessageIndex] && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <OutputExport
            content={messages[exportingMessageIndex].content}
            messageId={`msg-${exportingMessageIndex}`}
            onClose={() => setExportingMessageIndex(null)}
          />
        </div>
      )}

      {/* 🧠 Brain View - Now inline with each message (removed global component to avoid caching issues) */}
    </div>
  )
}
