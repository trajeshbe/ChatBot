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
  Building2
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

interface Props {
  activeTab: 'dashboard' | 'chat' | 'upload' | 'scrape' | 'history' | 'evaluation' | 'estimator' | 'tools' | 'weights' | 'library' | 'projects' | 'files' | 'explainable' | 'agent' | 'construction'
  setActiveTab: (tab: 'dashboard' | 'chat' | 'upload' | 'scrape' | 'history' | 'evaluation' | 'estimator' | 'tools' | 'weights' | 'library' | 'projects' | 'files' | 'explainable' | 'agent' | 'construction') => void
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
  const [metricsExpanded, setMetricsExpanded] = useState(false)  // 🆕 Track metrics submenu state

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

  // Secondary navigation - Tools & Features
  const secondaryNavItems = [
    { id: 'upload' as const, icon: Upload, label: 'Upload Files' },
    { id: 'scrape' as const, icon: Globe, label: 'Web Scraping' },
    { id: 'estimator' as const, icon: Calculator, label: 'Project Estimator' },
    { id: 'construction' as const, icon: Building2, label: 'Construction Metrics' },
    { id: 'library' as const, icon: BookOpen, label: 'Prompt Library' },
    { id: 'agent' as const, icon: Bot, label: 'Agent Tasks' },
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
