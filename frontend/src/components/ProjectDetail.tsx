import { useState, useEffect } from 'react'
import { ArrowLeft, Plus, FileText, MessageSquare, Upload, Folder, Calendar, Trash2, X } from 'lucide-react'
import axios from 'axios'
import ChatInterface from './ChatInterfaceEnhanced'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Project {
  id: string
  name: string
  description?: string
  file_count: number
  created_at: string
  updated_at: string
}

interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  upload_date: string
}

interface Chat {
  id: string
  session_id: string
  title: string
  message_count: number
  last_activity: string
}

interface ProjectDetailProps {
  projectId: string
  onBack: () => void
  onNewChat?: (projectId: string) => void
}

export default function ProjectDetail({ projectId, onBack, onNewChat }: ProjectDetailProps) {
  const [project, setProject] = useState<Project | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'all' | 'files' | 'chats'>('all')
  const [isInChatMode, setIsInChatMode] = useState(false) // Track if we're chatting within project

  useEffect(() => {
    loadProjectData()
  }, [projectId])

  const loadProjectData = async () => {
    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}

      // Load project details
      const projectResponse = await axios.get(`${API_URL}/api/v1/projects/${projectId}`, { headers })
      setProject(projectResponse.data)

      // Load documents in this project
      const docsResponse = await axios.get(`${API_URL}/api/v1/documents?project_id=${projectId}`, { headers })
      setDocuments(docsResponse.data || [])

      // Load chats in this project
      const chatsResponse = await axios.get(`${API_URL}/api/v1/sessions?project_id=${projectId}`, { headers })
      const sessions = chatsResponse.data?.sessions || []
      setChats(sessions.map((session: any) => ({
        id: session.id,
        session_id: session.session_id,
        title: session.title || 'Untitled Chat',
        message_count: session.message_count || 0,
        last_activity: session.last_activity
      })))
      console.log(`📚 Loaded ${sessions.length} chats for project ${projectId}`)

    } catch (err: any) {
      console.error('Error loading project data:', err)
      setError('Failed to load project data')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading project...</p>
        </div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error || 'Project not found'}</p>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const allItems = [
    ...documents.map(doc => ({ type: 'file' as const, data: doc, date: doc.upload_date })),
    ...chats.map(chat => ({ type: 'chat' as const, data: chat, date: chat.last_activity }))
  ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

  const filteredItems = activeView === 'all'
    ? allItems
    : activeView === 'files'
      ? allItems.filter(item => item.type === 'file')
      : allItems.filter(item => item.type === 'chat')

  // If in chat mode, show chat interface
  if (isInChatMode && project) {
    return (
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatInterface
          activeTab="chat"
          projectId={projectId}
          onBackToProject={() => {
            setIsInChatMode(false)
            loadProjectData()
          }}
        />
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 px-8 py-6">
        <div className="max-w-5xl mx-auto">
          {/* Back button */}
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Projects</span>
          </button>

          {/* Project header */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                <Folder className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">{project.name}</h1>
                {project.description && (
                  <p className="text-slate-600 dark:text-slate-400">{project.description}</p>
                )}
                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Created {formatDate(project.created_at)}
                  </span>
                  <span>{documents.length} files</span>
                  <span>{chats.length} chats</span>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  // TODO: Open file upload for this project
                  console.log('Upload to project:', projectId)
                }}
                className="flex items-center gap-2 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span className="font-medium">Add files</span>
              </button>
              <button
                onClick={() => {
                  console.log('🆕 Starting new chat in project:', projectId)
                  // Create new session for this project
                  const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

                  // ✅ FIX: Store in localStorage with project-specific key (where ChatInterface looks for it)
                  const sessionKey = `session_project_${projectId}`
                  localStorage.setItem(sessionKey, newSessionId)
                  console.log(`🆕 Generated new session ID for project ${projectId}:`, newSessionId)

                  // Save project_id to localStorage for ChatInterface sync
                  localStorage.setItem('selected_project_id', projectId)

                  // Dispatch event to trigger ChatInterface to reset with new session
                  window.dispatchEvent(new CustomEvent('new-chat', { detail: { sessionId: newSessionId, projectId } }))
                  console.log('🆕 Dispatched new-chat event for project chat')

                  // ✅ FIX: Set chat mode AFTER storing session (so ChatInterface finds it)
                  setIsInChatMode(true)
                }}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium shadow-sm"
              >
                <Plus className="w-4 h-4" />
                <span>New chat in {project.name}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="border-b border-slate-200 dark:border-slate-800 px-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex gap-6">
            {[
              { id: 'all' as const, label: 'All', count: allItems.length },
              { id: 'files' as const, label: 'Files', count: documents.length },
              { id: 'chats' as const, label: 'Chats', count: chats.length }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id)}
                className={`px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeView === tab.id
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-5xl mx-auto">
          {filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                {activeView === 'files' ? (
                  <FileText className="w-8 h-8 text-slate-400" />
                ) : activeView === 'chats' ? (
                  <MessageSquare className="w-8 h-8 text-slate-400" />
                ) : (
                  <Folder className="w-8 h-8 text-slate-400" />
                )}
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                No {activeView === 'all' ? 'items' : activeView} yet
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                {activeView === 'files'
                  ? 'Upload files to get started'
                  : activeView === 'chats'
                    ? 'Start a new chat in this project'
                    : 'Add files or start a chat to get started'}
              </p>
              {activeView === 'files' && (
                <button
                  onClick={() => console.log('Upload to project')}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                >
                  Add files
                </button>
              )}
              {activeView === 'chats' && (
                <button
                  onClick={() => {
                    console.log('🆕 Starting new chat in project (from empty state):', projectId)
                    // Create new session for this project
                    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

                    // ✅ FIX: Store in localStorage with project-specific key (where ChatInterface looks for it)
                    const sessionKey = `session_project_${projectId}`
                    localStorage.setItem(sessionKey, newSessionId)
                    console.log(`🆕 Generated new session ID for project ${projectId}:`, newSessionId)

                    // Save project_id to localStorage for ChatInterface sync
                    localStorage.setItem('selected_project_id', projectId)

                    // Dispatch event to trigger ChatInterface to reset with new session
                    window.dispatchEvent(new CustomEvent('new-chat', { detail: { sessionId: newSessionId, projectId } }))
                    console.log('🆕 Dispatched new-chat event for project chat')

                    // ✅ FIX: Set chat mode AFTER storing session (so ChatInterface finds it)
                    setIsInChatMode(true)
                  }}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                >
                  New chat
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredItems.map((item, index) => (
                <div
                  key={`${item.type}-${index}`}
                  className="group p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-sm transition-all cursor-pointer"
                  onClick={() => {
                    if (item.type === 'chat') {
                      // Load this chat session
                      console.log('📖 Loading chat session:', item.data.session_id)

                      // Store the session ID in localStorage for this project
                      const sessionKey = `session_project_${projectId}`
                      localStorage.setItem(sessionKey, item.data.session_id)

                      // Save project context
                      localStorage.setItem('selected_project_id', projectId)

                      // Dispatch event to load this session
                      window.dispatchEvent(new CustomEvent('session-changed', {
                        detail: { sessionId: item.data.session_id, projectId }
                      }))

                      // Enter chat mode
                      setIsInChatMode(true)
                    }
                  }}
                >
                  {item.type === 'file' ? (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-slate-900 dark:text-white truncate">
                            {item.data.filename}
                          </h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">
                            {formatSize(item.data.file_size)} &bull; {formatDate(item.data.upload_date)}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          console.log('Delete file:', item.data.id)
                        }}
                        className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                      >
                        <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                          <MessageSquare className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-slate-900 dark:text-white truncate">
                            {item.data.title || 'Untitled Chat'}
                          </h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">
                            {item.data.message_count} messages &bull; {formatDate(item.data.last_activity)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
