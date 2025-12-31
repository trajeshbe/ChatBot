import { useState, useEffect } from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'
import ChatInterface from '@/components/ChatInterfaceEnhanced'
import SidebarModern from '@/components/SidebarModern'
import UserHeader from '@/components/UserHeader'
import ChatHistory from '@/components/ChatHistory'
import EvaluationDashboard from '@/components/EvaluationDashboard'
import UnifiedWebScraper from '@/components/UnifiedWebScraper'
import ProjectEstimator from '@/components/ProjectEstimator'
import ToolUsageDashboard from '@/components/ToolUsageDashboard'
import WeightsConfigManager from '@/components/WeightsConfigManager'
import SettingsPanel from '@/components/SettingsPanel'
import ProjectsView from '@/components/ProjectsView'
import ProjectDetail from '@/components/ProjectDetail'
import Library from '@/components/Library'
import PromptLibraryManager from '@/components/PromptLibraryManager'
import AgentTaskMonitor from '@/components/AgentTaskMonitor'
import ConstructionExtraction from '@/components/ConstructionExtraction'
import { useAuth } from '@/contexts/AuthContext'
import type { RAGConfig } from '@/components/RAGSettings'

export default function Home() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat' | 'upload' | 'scrape' | 'history' | 'evaluation' | 'estimator' | 'tools' | 'weights' | 'library' | 'projects' | 'files' | 'explainable' | 'agent' | 'construction'>('chat')
  const [sessionId, setSessionId] = useState<string>('')
  const [currentUser, setCurrentUser] = useState<string>('Anonymous')
  const [ragConfig, setRagConfig] = useState<RAGConfig | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    // Get session ID from sessionStorage
    if (typeof window !== 'undefined') {
      const storedSessionId = sessionStorage.getItem('chat_session_id')
      if (storedSessionId) {
        setSessionId(storedSessionId)
      }

      // Get username from auth context or localStorage
      if (user) {
        setCurrentUser(user.username)
      } else {
        const storedUsername = localStorage.getItem('username') || 'Anonymous'
        setCurrentUser(storedUsername)
      }
    }
  }, [user])

  const handleRAGSettingsChange = (settings: RAGConfig) => {
    setRagConfig(settings)
  }

  const handleNewChat = () => {
    console.log('🆕 [index.tsx] handleNewChat clicked')
    // Clear session and start fresh
    if (typeof window !== 'undefined') {
      // Generate new session ID
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      console.log('🆕 [index.tsx] Generated new session ID:', newSessionId)
      sessionStorage.setItem('chat_session_id', newSessionId)
      setSessionId(newSessionId)

      // Navigate to chat tab
      console.log('🆕 [index.tsx] Switching to chat tab')
      setActiveTab('chat')

      // Trigger chat interface to reload
      console.log('🆕 [index.tsx] Dispatching new-chat event')
      window.dispatchEvent(new CustomEvent('new-chat', { detail: { sessionId: newSessionId } }))
      console.log('🆕 [index.tsx] New chat setup complete')
    }
  }

  const handleProjectClick = (projectId: string) => {
    console.log('📁 [index.tsx] Project clicked:', projectId)
    setSelectedProjectId(projectId)
    setActiveTab('projects') // Ensure we're on projects tab
  }

  const handleNewProject = () => {
    console.log('📁 [index.tsx] New project clicked')
    setSelectedProjectId(null) // Clear selected project to show projects list
    setActiveTab('projects')
  }

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return (
    <>
      <Head>
        <title>Enterprise RAG Chatbot</title>
        <meta name="description" content="Enterprise-grade RAG chatbot with document processing and web scraping" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="flex h-screen bg-white dark:bg-slate-900">
        {/* Modern Sidebar */}
        <SidebarModern
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          currentUser={currentUser}
          onNewChat={handleNewChat}
          onProjectClick={handleProjectClick}
          onNewProject={handleNewProject}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* User Header */}
          <UserHeader />

          {/* 🆕 FIX: Keep ChatInterface mounted but hidden to preserve state during tab switches */}
          <div className={`flex-1 flex flex-col overflow-hidden ${activeTab === 'chat' || activeTab === 'upload' ? '' : 'hidden'}`}>
            <ChatInterface
              key="main-chat-interface"  // Stable key prevents React from unmounting
              activeTab={activeTab}
              ragConfig={ragConfig}
              projectId={selectedProjectId}
            />
          </div>

          {/* Show other tabs on top when active */}
          {activeTab === 'history' && (
            <div className="flex-1 overflow-hidden">
              <ChatHistory
                onSessionSelect={(sessionId) => {
                  // Switch to chat tab when session is selected
                  setActiveTab('chat');
                  // Session ID is already set in sessionStorage by ChatHistory
                  // Trigger a refresh of the chat interface
                  window.dispatchEvent(new CustomEvent('session-changed', { detail: { sessionId } }));
                }}
              />
            </div>
          )}

          {activeTab === 'evaluation' && (
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
              <div className="max-w-7xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    Evaluation Metrics
                  </h1>
                  <p className="text-slate-600 dark:text-slate-400">
                    Real-time analytics and performance insights for your RAG system
                  </p>
                </div>
                <EvaluationDashboard />
              </div>
            </div>
          )}

          {activeTab === 'tools' && (
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
              <div className="max-w-7xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    🔧 Tool Usage Analytics
                  </h1>
                  <p className="text-slate-600 dark:text-slate-400">
                    Comprehensive statistics for all tools, services, and agents
                  </p>
                </div>
                <ToolUsageDashboard />
              </div>
            </div>
          )}

          {activeTab === 'estimator' && (
            <div className="flex-1 overflow-y-auto">
              <ProjectEstimator sessionId={sessionId} />
            </div>
          )}

          {activeTab === 'construction' && (
            <div className="flex-1 overflow-y-auto">
              <ConstructionExtraction />
            </div>
          )}

          {activeTab === 'scrape' && (
            <div className="flex-1 flex flex-col overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
              <UnifiedWebScraper />
            </div>
          )}

          {activeTab === 'weights' && (
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
              <div className="max-w-7xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    Weights Configuration
                  </h1>
                  <p className="text-slate-600 dark:text-slate-400">
                    Configure RAG system weights for multi-strategy evaluation, scoring, and classification
                  </p>
                </div>
                <WeightsConfigManager />
              </div>
            </div>
          )}

          {activeTab === 'explainable' && (
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
              <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    Explainable RAG
                  </h1>
                  <p className="text-slate-600 dark:text-slate-400">
                    Control which metrics and performance data are displayed in your chat responses
                  </p>
                  {/* Help Banner */}
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                          Settings Apply to New Queries Only
                        </h3>
                        <p className="text-sm text-blue-800 dark:text-blue-200">
                          Changes to these settings will only affect <strong>new chat responses</strong>. Existing messages in your chat history will not be updated. To see the updated metrics, send a new query.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <SettingsPanel onSettingsChange={(settings) => console.log('Settings changed:', settings)} />
              </div>
            </div>
          )}

          {activeTab === 'projects' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {selectedProjectId ? (
                <ProjectDetail
                  projectId={selectedProjectId}
                  onBack={() => setSelectedProjectId(null)}
                  onNewChat={(projectId) => {
                    // TODO: implement new chat in project
                    console.log('🆕 New chat in project:', projectId)
                    handleNewChat()
                    // In future: associate session with project
                  }}
                />
              ) : (
                <ProjectsView
                  currentUser={user}
                  onProjectClick={(projectId) => setSelectedProjectId(projectId)}
                />
              )}
            </div>
          )}

          {activeTab === 'files' && (
            <div className="flex-1 overflow-hidden">
              <Library currentUser={user?.username || 'Anonymous'} />
            </div>
          )}

          {/* Prompt Library Manager */}
          {activeTab === 'library' && (
            <div className="flex-1 overflow-hidden">
              <PromptLibraryManager />
            </div>
          )}

          {/* Agent Task Monitor */}
          {activeTab === 'agent' && (
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
              <div className="max-w-7xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    🤖 Agent Task Monitor
                  </h1>
                  <p className="text-slate-600 dark:text-slate-400">
                    Create and monitor autonomous agent tasks with LLM-driven tool execution
                  </p>
                </div>
                <AgentTaskMonitor sessionId={sessionId} />
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
