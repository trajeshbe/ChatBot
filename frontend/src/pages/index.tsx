import { useState } from 'react'
import Head from 'next/head'
import ChatInterface from '@/components/ChatInterfaceEnhanced'
import Sidebar from '@/components/Sidebar'
import { FileText, Globe } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'scrape'>('chat')

  return (
    <>
      <Head>
        <title>Enterprise RAG Chatbot</title>
        <meta name="description" content="Enterprise-grade RAG chatbot with document processing and web scraping" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        {/* Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700">
            <div className="px-6 py-4">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Enterprise RAG Chatbot
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                Powered by vLLM, pgvector, and advanced RAG architecture
              </p>
            </div>
          </header>

          {/* Chat Interface */}
          <div className="flex-1 overflow-hidden">
            <ChatInterface activeTab={activeTab} />
          </div>
        </div>
      </main>
    </>
  )
}
