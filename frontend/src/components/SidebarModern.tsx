import { useState, useEffect } from 'react'
import {
  MessageSquare,
  Upload,
  Globe,
  BarChart3,
  Calculator,
  Wrench,
  Sliders,
  History,
  Plus,
  FolderOpen,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Folder,
  FileText,
  Files,
  Sparkles,
  TrendingUp,
  ChevronDown,
  BookOpen,
  Bot,
  Building2,
  ShoppingCart,
  Users,
  Sprout,
  Mail,
  ShoppingBag,
  Ship,
  PieChart,
  Target,
  Layers,
  CheckCircle2
} from 'lucide-react'
import { ThemeToggle } from '@/theme/ThemeToggle'
import axios from 'axios'
import { generateMissingTitles, ChatSession as ChatSessionType } from '@/utils/sessionTitles'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Project {
  id: string
  name: string
  description?: string
  file_count: number
  updated_at: string
}

type TabType = 'dashboard' | 'chat' | 'upload' | 'scrape' | 'history' | 'evaluation' | 'estimator' | 'tools' | 'weights' | 'library' | 'projects' | 'files' | 'explainable' | 'agent' | 'construction' | 'document-extract'

interface Props {
  activeTab: TabType
  setActiveTab: (tab: TabType) => void
  currentUser?: string
  onNewChat?: () => void
  onProjectClick?: (projectId: string) => void
  onNewProject?: () => void
}

export default function SidebarModern({ activeTab, setActiveTab, currentUser, onNewChat, onProjectClick, onNewProject }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showRecentChats, setShowRecentChats] = useState(true)
  const [projects, setProjects] = useState<Project[]>([])
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [recentChats, setRecentChats] = useState<ChatSessionType[]>([])
  const [loadingChats, setLoadingChats] = useState(false)
  const [metricsExpanded, setMetricsExpanded] = useState(false)  // Track metrics submenu state
  const [verticalsExpanded, setVerticalsExpanded] = useState(false)  // Track domain verticals submenu
  const [customersExpanded, setCustomersExpanded] = useState(false)  // Track customer solutions submenu

  // 🆕 Consolidated Metrics & Evaluation submenu items (defined early for useEffect)
  const metricsSubItems = [
    { id: 'tools' as const, icon: Wrench, label: 'Usage Metrics' },
    { id: 'evaluation' as const, icon: BarChart3, label: 'Evaluation' },
    { id: 'weights' as const, icon: Sliders, label: 'RAG Settings' },
    { id: 'explainable' as const, icon: Sparkles, label: 'Explainability' },
  ]

  // Load user's projects
  useEffect(() => {
    loadProjects()
    loadRecentChats()
  }, [])

  // 🆕 Auto-expand metrics submenu when one of its tabs is active
  useEffect(() => {
    const metricsTabIds = metricsSubItems.map(item => item.id)
    if (metricsTabIds.includes(activeTab)) {
      setMetricsExpanded(true)
    }
  }, [activeTab])

  const loadProjects = async () => {
    setLoadingProjects(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_URL}/api/v1/projects`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      setProjects(response.data.slice(0, 5)) // Show top 5 recent projects
    } catch (err) {
      console.error('Error loading projects:', err)
    } finally {
      setLoadingProjects(false)
    }
  }

  const loadRecentChats = async () => {
    setLoadingChats(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setLoadingChats(false)
        return
      }

      const response = await axios.get(`${API_URL}/api/v1/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.data.sessions) {
        // Auto-generate titles for sessions without titles (using shared utility)
        const sessionsWithTitles = await generateMissingTitles(response.data.sessions, token)

        // Sort by last_activity descending and take top 4
        const sorted = sessionsWithTitles.sort((a, b) =>
          new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()
        )
        setRecentChats(sorted.slice(0, 4))
        console.log(`📥 Loaded ${sorted.slice(0, 4).length} recent chats with titles`)
      }
    } catch (err) {
      console.error('Error loading recent chats:', err)
    } finally {
      setLoadingChats(false)
    }
  }

  const handleChatClick = (sessionId: string) => {
    // Set the session ID in sessionStorage
    sessionStorage.setItem('chat_session_id', sessionId)

    // Switch to chat tab and trigger session load
    setActiveTab('chat')
    window.dispatchEvent(new CustomEvent('session-changed', { detail: { sessionId } }))
  }

  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  // Main navigation items (inspired by Claude.ai)
  const mainNavItems = [
    { id: 'chat' as const, icon: MessageSquare, label: 'Chats' },
    { id: 'files' as const, icon: Files, label: 'Files' },
    // 'Projects' removed - use Projects section in sidebar instead
  ]

  // Platform Tools (Tier 1)
  const secondaryNavItems = [
    { id: 'upload' as const, icon: Upload, label: 'Upload Files' },
    { id: 'scrape' as const, icon: Globe, label: 'Web Scraping' },
    { id: 'estimator' as const, icon: Calculator, label: 'Project Estimator' },
    { id: 'library' as const, icon: BookOpen, label: 'Prompt Library' },
    { id: 'agent' as const, icon: Bot, label: 'Agent Tasks' },
  ]

  // Domain Verticals (Tier 2) - Industry-specific modules
  const domainVerticals = [
    {
      id: 'document-intelligence',
      icon: FileText,
      label: 'Document Intelligence',
      badge: '3/3',
      modules: [
        { id: 'document-extract' as const, label: '18-Field Extraction', status: 'live' },
        { id: 'relation-extractor' as const, label: 'Relation Extractor', status: 'live' },
        { id: 'generic-rag' as const, label: 'Generic RAG', status: 'live' }
      ]
    },
    {
      id: 'construction',
      icon: Building2,
      label: 'Construction',
      badge: '4/4',
      modules: [
        { id: 'construction' as const, label: 'Building Metrics', status: 'live' },
        { id: 'planning-classifier' as const, label: 'Planning Classifier', status: 'live' },
        { id: 'mine-scope' as const, label: 'Mine Scope Analysis', status: 'live' },
        { id: 'estimator-au' as const, label: 'AU Cost Estimator', status: 'live' }
      ]
    },
    {
      id: 'procurement',
      icon: ShoppingCart,
      label: 'Procurement',
      badge: '4/4',
      modules: [
        { id: 'matcher' as const, label: 'PO-Invoice Matcher', status: 'live' },
        { id: 'vendor-recommendation' as const, label: 'Vendor Recommendation', status: 'live' },
        { id: 'tender-intelligence' as const, label: 'Tender Intelligence', status: 'live' },
        { id: 'spend-smart' as const, label: 'Spend Analytics', status: 'live' }
      ]
    },
    {
      id: 'hr-talent',
      icon: Users,
      label: 'HR & Talent',
      badge: '3/3',
      modules: [
        { id: 'talent-search' as const, label: 'Talent Search', status: 'live' },
        { id: 'taxonomy-skillmatch' as const, label: 'Skill Taxonomy', status: 'live' },
        { id: 'talent-pulse' as const, label: 'Employee Engagement', status: 'live' }
      ]
    },
    {
      id: 'agriculture',
      icon: Sprout,
      label: 'Agriculture',
      badge: '2/2',
      modules: [
        { id: 'agri-taxonomy' as const, label: 'Crop Taxonomy', status: 'live' },
        { id: 'agronomy-decision' as const, label: 'Agronomy Decisions', status: 'live' }
      ]
    },
    {
      id: 'marketing',
      icon: Mail,
      label: 'Marketing',
      badge: '2/2',
      modules: [
        { id: 'sentiment-social' as const, label: 'Social Sentiment', status: 'live' },
        { id: 'campaign-optimizer' as const, label: 'Campaign Optimizer', status: 'live' }
      ]
    },
    {
      id: 'ecommerce',
      icon: ShoppingBag,
      label: 'E-commerce',
      badge: '1/1',
      modules: [
        { id: 'product-recommendation' as const, label: 'Product Recommendations', status: 'live' }
      ]
    },
    {
      id: 'maritime',
      icon: Ship,
      label: 'Maritime',
      badge: '1/1',
      modules: [
        { id: 'maritime-logistics' as const, label: 'Logistics Optimizer', status: 'live' }
      ]
    },
    {
      id: 'analytics',
      icon: PieChart,
      label: 'Analytics',
      badge: '4/4',
      modules: [
        { id: 'predictive-analytics' as const, label: 'Predictive Analytics', status: 'live' },
        { id: 'customer-churn' as const, label: 'Churn Predictor', status: 'live' },
        { id: 'sales-performance' as const, label: 'Sales Performance', status: 'live' },
        { id: 'financial-anomaly' as const, label: 'Financial Anomaly', status: 'live' }
      ]
    },
    {
      id: 'industry-verticals',
      icon: Building2,
      label: 'Industry Verticals',
      badge: '5/5',
      modules: [
        { id: 'healthcare-diagnostics' as const, label: 'Healthcare Diagnostics', status: 'live' },
        { id: 'legal-document' as const, label: 'Legal Document Analyzer', status: 'live' },
        { id: 'real-estate-valuation' as const, label: 'Real Estate Valuation', status: 'live' },
        { id: 'insurance-risk' as const, label: 'Insurance Risk Assessor', status: 'live' },
        { id: 'educational-content' as const, label: 'Educational Content', status: 'live' }
      ]
    },
    {
      id: 'advanced-capabilities',
      icon: Sparkles,
      label: 'Advanced Capabilities',
      badge: '2/2',
      modules: [
        { id: 'multilingual-translator' as const, label: 'Multilingual Translator', status: 'live' },
        { id: 'code-analysis' as const, label: 'Code Analysis & Review', status: 'live' }
      ]
    }
  ]

  // Customer Solutions (Tier 3) - Customer-specific POCs
  const customerSolutions = [
    { id: 'british-council', label: 'British Council POC', status: 'live' },
    { id: 'cru', label: 'CRU POC', status: 'live' },
    { id: 'grant-thornton', label: 'Grant Thornton POC', status: 'live' },
    { id: 'gt-motive', label: 'GT Motive POC', status: 'live' },
    { id: 'solera', label: 'Solera POC', status: 'live' },
    { id: 'construction-monitor', label: 'Construction Monitor POC', status: 'live' }
  ]

  return (
    <div
      className={`
        ${isCollapsed ? 'w-16' : 'w-64'}
        bg-white dark:bg-slate-900
        border-r border-slate-200 dark:border-slate-800
        flex flex-col
        transition-all duration-300 ease-in-out
        relative
      `}
    >
      {/* Header Section */}
      <div className="p-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-slate-900 dark:text-white text-sm">Enterprise AI</span>
            </div>
          )}

          {/* Collapse Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-600 dark:text-slate-400"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* New Chat Button - Claude.ai style with circular icon */}
      {onNewChat && (
        <div className="p-3 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => {
              console.log('🆕 [SidebarModern] New Chat button clicked')
              onNewChat()
            }}
            className={`
              ${isCollapsed ? 'w-10 h-10 p-0 justify-center' : 'w-full px-3 py-2.5'}
              flex items-center gap-2.5 rounded-lg
              bg-primary-600 hover:bg-primary-700
              text-white font-medium
              transition-all duration-200
              shadow-sm hover:shadow-md
              group
            `}
            title={isCollapsed ? 'New Chat' : ''}
          >
            <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center">
              <Plus className="w-3.5 h-3.5" />
            </div>
            {!isCollapsed && <span className="text-sm">New chat</span>}
          </button>
        </div>
      )}

      {/* Main Navigation */}
      <nav className="flex-1 overflow-y-auto">
        <div className={`${isCollapsed ? 'p-2' : 'p-3'} space-y-0.5`}>
          {/* Regular main nav items */}
          {mainNavItems.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`
                  ${isCollapsed ? 'w-10 h-10 p-0 justify-center' : 'w-full px-3 py-2'}
                  flex items-center gap-3 rounded-lg
                  transition-all duration-150
                  ${isActive
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }
                `}
                title={isCollapsed ? item.label : ''}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {!isCollapsed && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            )
          })}

          {/* 🆕 Consolidated Metrics & Evaluation Menu */}
          {!isCollapsed && (
            <div>
              <button
                onClick={() => setMetricsExpanded(!metricsExpanded)}
                className={`
                  w-full px-3 py-2 flex items-center justify-between gap-3 rounded-lg
                  transition-all duration-150
                  ${metricsSubItems.some(item => item.id === activeTab)
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm font-medium">Metrics & Evaluation</span>
                </div>
                <ChevronDown
                  className={`w-3.5 h-3.5 transition-transform duration-200 ${metricsExpanded ? 'rotate-180' : ''}`}
                />
              </button>

              {/* Submenu Items */}
              {metricsExpanded && (
                <div className="mt-0.5 ml-3 pl-3 border-l border-slate-200 dark:border-slate-700 space-y-0.5">
                  {metricsSubItems.map((item) => {
                    const Icon = item.icon
                    const isActive = activeTab === item.id

                    return (
                      <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className={`
                          w-full px-3 py-1.5 flex items-center gap-2.5 rounded-lg
                          transition-all duration-150 text-sm
                          ${isActive
                            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                          }
                        `}
                      >
                        <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>{item.label}</span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Collapsed version - show icon only */}
          {isCollapsed && (
            <button
              onClick={() => {
                setIsCollapsed(false)
                setMetricsExpanded(true)
              }}
              className={`
                w-10 h-10 p-0 justify-center flex items-center gap-3 rounded-lg
                transition-all duration-150
                ${metricsSubItems.some(item => item.id === activeTab)
                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                }
              `}
              title="Metrics & Evaluation"
            >
              <TrendingUp className="w-4 h-4 flex-shrink-0" />
            </button>
          )}

          {/* 🆕 Domain Verticals (Tier 2) Section */}
          {!isCollapsed && (
            <div className="mt-4">
              <button
                onClick={() => setVerticalsExpanded(!verticalsExpanded)}
                className={`
                  w-full px-3 py-2 flex items-center justify-between gap-3 rounded-lg
                  transition-all duration-150
                  ${['document-extract', 'construction'].includes(activeTab)
                    ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  <Layers className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm font-medium">Domain Verticals</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded font-semibold">TIER 2</span>
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-200 ${verticalsExpanded ? 'rotate-180' : ''}`}
                  />
                </div>
              </button>

              {/* Domain Verticals Submenu */}
              {verticalsExpanded && (
                <div className="mt-0.5 ml-3 pl-3 border-l border-slate-200 dark:border-slate-700 space-y-0.5">
                  {domainVerticals.map((vertical) => {
                    const Icon = vertical.icon
                    const hasModules = vertical.modules && vertical.modules.length > 0
                    const isVerticalActive = vertical.modules?.some((m: any) => m.id === activeTab)

                    return (
                      <div key={vertical.id}>
                        {hasModules ? (
                          <>
                            <div className={`px-2 py-1.5 flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-400 ${isVerticalActive ? 'text-emerald-700 dark:text-emerald-300' : ''}`}>
                              <div className="flex items-center gap-2">
                                <Icon className="w-3.5 h-3.5" />
                                <span>{vertical.label}</span>
                              </div>
                              <span className="text-[9px] px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded">{vertical.badge}</span>
                            </div>
                            <div className="ml-5 space-y-0.5">
                              {vertical.modules.map((module: any) => {
                                const isActive = activeTab === module.id
                                const isLive = module.status === 'live'

                                return (
                                  <button
                                    key={module.id}
                                    onClick={() => isLive && setActiveTab(module.id)}
                                    disabled={!isLive}
                                    className={`
                                      w-full px-2 py-1 flex items-center justify-between gap-2 rounded-lg
                                      transition-all duration-150 text-xs
                                      ${isActive
                                        ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 font-medium'
                                        : isLive
                                          ? 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                                          : 'text-slate-400 dark:text-slate-600 cursor-not-allowed'
                                      }
                                    `}
                                  >
                                    <span>{module.label}</span>
                                    {isLive ? (
                                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                                    ) : (
                                      <span className="text-[8px] px-1 py-0.5 bg-slate-200 dark:bg-slate-700 text-slate-500 rounded">SOON</span>
                                    )}
                                  </button>
                                )
                              })}
                            </div>
                          </>
                        ) : (
                          <div className={`px-2 py-1.5 flex items-center justify-between text-xs font-medium text-slate-400 dark:text-slate-600`}>
                            <div className="flex items-center gap-2">
                              <Icon className="w-3.5 h-3.5" />
                              <span>{vertical.label}</span>
                            </div>
                            <span className="text-[9px] px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded">{vertical.badge}</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* 🆕 Customer Solutions (Tier 3) Section */}
          {!isCollapsed && (
            <div className="mt-2">
              <button
                onClick={() => setCustomersExpanded(!customersExpanded)}
                className="w-full px-3 py-2 flex items-center justify-between gap-3 rounded-lg transition-all duration-150 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              >
                <div className="flex items-center gap-3">
                  <Target className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm font-medium">Customer Solutions</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-1.5 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded font-semibold">TIER 3</span>
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-200 ${customersExpanded ? 'rotate-180' : ''}`}
                  />
                </div>
              </button>

              {/* Customer Solutions Submenu */}
              {customersExpanded && (
                <div className="mt-0.5 ml-3 pl-3 border-l border-slate-200 dark:border-slate-700 space-y-0.5">
                  {customerSolutions.map((customer: any) => {
                    const isActive = activeTab === customer.id
                    const isLive = customer.status === 'live'

                    return (
                      <button
                        key={customer.id}
                        onClick={() => isLive && setActiveTab(customer.id)}
                        disabled={!isLive}
                        className={`
                          w-full px-2 py-1 flex items-center justify-between gap-2 rounded-lg
                          transition-all duration-150 text-xs
                          ${isActive
                            ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 font-medium'
                            : isLive
                              ? 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                              : 'text-slate-400 dark:text-slate-600 cursor-not-allowed'
                          }
                        `}
                      >
                        <span>{customer.label}</span>
                        {isLive ? (
                          <CheckCircle2 className="w-3 h-3 text-purple-600" />
                        ) : (
                          <span className="text-[8px] px-1 py-0.5 bg-slate-200 dark:bg-slate-700 text-slate-500 rounded">SOON</span>
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Projects Section - Only show when expanded */}
        {!isCollapsed && (
          <div className="mt-4 px-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Projects
              </h3>
              <button
                onClick={() => {
                  if (onNewProject) {
                    onNewProject()
                  } else {
                    setActiveTab('projects')
                  }
                }}
                className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
              >
                View all
              </button>
            </div>
            <button
              onClick={() => {
                if (onNewProject) {
                  onNewProject()
                } else {
                  setActiveTab('projects')
                }
              }}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-slate-600 dark:text-slate-400 mb-2"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="text-xs font-medium">New project</span>
            </button>
            <div className="space-y-0.5">
              {loadingProjects ? (
                <div className="text-xs text-slate-400 dark:text-slate-500 px-2 py-1.5">Loading...</div>
              ) : projects.length > 0 ? (
                projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      if (onProjectClick) {
                        onProjectClick(project.id)
                      }
                    }}
                    className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      <Folder className="w-3.5 h-3.5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate group-hover:text-primary-600 dark:group-hover:text-primary-400">
                          {project.name}
                        </div>
                        {project.file_count > 0 && (
                          <div className="text-[10px] text-slate-500 dark:text-slate-500">
                            {project.file_count} file{project.file_count !== 1 ? 's' : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-xs text-slate-400 dark:text-slate-500 px-2 py-1.5">No projects yet</div>
              )}
            </div>
          </div>
        )}

        {/* Recent Chats Section - Only show when expanded */}
        {!isCollapsed && showRecentChats && (
          <div className="mt-4 px-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Recent Chats
              </h3>
            </div>
            <div className="space-y-0.5">
              {loadingChats ? (
                <div className="text-xs text-slate-400 dark:text-slate-500 px-2 py-1.5">
                  Loading recent chats...
                </div>
              ) : recentChats.length > 0 ? (
                recentChats.map((chat) => (
                  <button
                    key={chat.session_id}
                    onClick={() => handleChatClick(chat.session_id)}
                    className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group"
                  >
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate group-hover:text-primary-600 dark:group-hover:text-primary-400">
                      {chat.title || 'Untitled Chat'}
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="text-[10px] text-slate-500 dark:text-slate-500">
                        {formatRelativeTime(chat.last_activity)}
                      </div>
                      {chat.message_count && (
                        <div className="text-[10px] text-slate-400 dark:text-slate-600">
                          {chat.message_count} msg{chat.message_count !== 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-xs text-slate-400 dark:text-slate-500 px-2 py-1.5">
                  No recent chats yet
                </div>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Secondary Navigation / Footer - Only show when expanded */}
      {!isCollapsed && (
        <div className="border-t border-slate-200 dark:border-slate-800">
          <div className="p-3 space-y-0.5">
            {secondaryNavItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`
                    w-full px-2 py-1.5 flex items-center gap-2.5 rounded-lg
                    transition-colors text-xs
                    ${isActive
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                    }
                  `}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              )
            })}

            {/* Admin Link */}
            <a
              href="/admin"
              className="w-full px-2 py-1.5 flex items-center gap-2.5 rounded-lg transition-colors text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="font-medium">Admin</span>
            </a>
          </div>

          {/* Theme Toggle */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Theme</span>
              <ThemeToggle />
            </div>
          </div>
        </div>
      )}

      {/* Collapsed State - Show minimal icons */}
      {isCollapsed && (
        <div className="border-t border-slate-200 dark:border-slate-800 p-2">
          <div className="flex flex-col items-center gap-2">
            <button
              onClick={() => setActiveTab('weights')}
              className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              title="Settings"
            >
              <Sliders className="w-4 h-4 text-slate-600 dark:text-slate-400" />
            </button>
            <div className="w-8 border-t border-slate-200 dark:border-slate-700" />
            <ThemeToggle />
          </div>
        </div>
      )}
    </div>
  )
}
