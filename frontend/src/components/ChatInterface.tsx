import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import FileUpload from './FileUpload'
import WebScraper from './WebScraper'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
}

interface Source {
  id: string
  filename: string
  source_type: string
  source_url?: string
  relevance: number
  excerpt: string
}

interface Props {
  activeTab: 'chat' | 'upload' | 'scrape'
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ChatInterface({ activeTab }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your enterprise RAG assistant. I can help you find information from uploaded documents and scraped websites. How can I assist you today?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const formData = new FormData()
      formData.append('query', input)
      formData.append('use_cache', 'true')

      const response = await axios.post(`${API_URL}/api/v1/query`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
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
      handleSendMessage()
    }
  }

  if (activeTab === 'upload') {
    return <FileUpload />
  }

  if (activeTab === 'scrape') {
    return <WebScraper />
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-md'
              }`}
            >
              <div className="markdown-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-sm font-semibold mb-2 text-slate-700 dark:text-slate-300">
                    Sources:
                  </p>
                  <div className="space-y-2">
                    {message.sources.map((source, idx) => (
                      <div
                        key={idx}
                        className="text-sm bg-slate-50 dark:bg-slate-900 p-3 rounded border border-slate-200 dark:border-slate-700"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            {source.source_type === 'scrape' ? (
                              <ExternalLink className="w-4 h-4 text-blue-500" />
                            ) : (
                              <FileText className="w-4 h-4 text-green-500" />
                            )}
                            <span className="font-medium text-slate-900 dark:text-white">
                              {source.filename}
                            </span>
                          </div>
                          <span className="text-xs text-slate-500">
                            {(source.relevance * 100).toFixed(0)}% match
                          </span>
                        </div>
                        {source.source_url && (
                          <a
                            href={source.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline mt-1 block"
                          >
                            {source.source_url}
                          </a>
                        )}
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 italic">
                          "{source.excerpt}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-xs text-slate-500 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-md">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              className="flex-1 resize-none rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!input.trim() || isLoading}
              className="px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Send
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
