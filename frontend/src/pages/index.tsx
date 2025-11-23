import { useState, useEffect } from 'react'
import Head from 'next/head'
import ChatInterface from '@/components/ChatInterfaceEnhanced'
import Sidebar from '@/components/Sidebar'
import EvaluationDashboard from '@/components/EvaluationDashboard'
import DataExtractionHub from '@/components/DataExtractionHub'
import ProjectEstimator from '@/components/ProjectEstimator'
import ToolUsageDashboard from '@/components/ToolUsageDashboard'
import type { RAGConfig } from '@/components/RAGSettings'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'scrape' | 'extract' | 'evaluation' | 'estimator' | 'tools'>('chat')
  const [sessionId, setSessionId] = useState<string>('')
  const [currentUser, setCurrentUser] = useState<string>('Anonymous')
  const [ragConfig, setRagConfig] = useState<RAGConfig | null>(null)

  useEffect(() => {
    // Get session ID from sessionStorage
    if (typeof window !== 'undefined') {
      const storedSessionId = sessionStorage.getItem('chat_session_id')
      if (storedSessionId) {
        setSessionId(storedSessionId)
      }

      // Get username (from localStorage or default to Anonymous)
      const storedUsername = localStorage.getItem('username') || 'Anonymous'
      setCurrentUser(storedUsername)
    }
  }, [])

  const handleRAGSettingsChange = (settings: RAGConfig) => {
    setRagConfig(settings)
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
        {/* Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          currentUser={currentUser}
          onRAGSettingsChange={handleRAGSettingsChange}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'evaluation' ? (
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
          ) : activeTab === 'tools' ? (
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
          ) : activeTab === 'estimator' ? (
            <div className="flex-1 overflow-y-auto">
              <ProjectEstimator sessionId={sessionId} />
            </div>
          ) : activeTab === 'extract' ? (
            <div className="flex-1 overflow-y-auto">
              <DataExtractionHub sessionId={sessionId} />
            </div>
          ) : (
            <div className="flex-1 overflow-hidden">
              <ChatInterface activeTab={activeTab} ragConfig={ragConfig} />
            </div>
          )}
        </div>
      </main>
    </>
  )
}
