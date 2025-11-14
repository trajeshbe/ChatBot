import { useState, useEffect } from 'react'
import Head from 'next/head'
import ChatInterface from '@/components/ChatInterfaceEnhanced'
import Sidebar from '@/components/Sidebar'
import { FileText, Globe, User } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'scrape'>('chat')
  const [sessionId, setSessionId] = useState<string>('')
  const [currentUser, setCurrentUser] = useState<string>('Anonymous')

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
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Chat Interface */}
          <div className="flex-1 overflow-hidden">
            <ChatInterface activeTab={activeTab} />
          </div>
        </div>
      </main>
    </>
  )
}
