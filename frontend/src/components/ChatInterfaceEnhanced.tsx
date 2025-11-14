import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText, ExternalLink, Paperclip, X, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import FileUpload from './FileUpload'
import WebScraper from './WebScraper'
import ModelSelector from './ModelSelector'
import UploadedFilesList from './UploadedFilesList'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
  model?: string
  model_name?: string
  contextInfo?: string
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

interface Props {
  activeTab: 'chat' | 'upload' | 'scrape'
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

export default function ChatInterfaceEnhanced({ activeTab }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your enterprise RAG assistant with multi-model support. I can use OpenAI, Claude, or local models. Select your preferred model above and ask me anything! You can also upload files directly in this chat.',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string>('')
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize session ID on mount
  useEffect(() => {
    setSessionId(getSessionId())
  }, [])

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

  // Upload files to backend with session ID
  const uploadAttachedFiles = async (): Promise<{ success: boolean; duplicates: string[] }> => {
    if (attachedFiles.length === 0) return { success: true, duplicates: [] }

    setUploadingFiles(true)
    const duplicates: string[] = []
    let hasErrors = false

    try {
      for (const file of attachedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('session_id', sessionId) // 🎯 Pass session ID!

        const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        // Check if file was duplicate
        if (response.data.duplicate || !response.data.success) {
          duplicates.push(file.name)
          console.log(`⚠️ Duplicate file skipped: ${file.name}`)
        } else {
          console.log(`✅ Uploaded ${file.name} to session ${sessionId}`)
        }
      }
      setAttachedFiles([]) // Clear after processing all files
      return { success: !hasErrors, duplicates }
    } catch (error) {
      console.error('Error uploading files:', error)
      hasErrors = true
      return { success: false, duplicates }
    } finally {
      setUploadingFiles(false)
    }
  }

  const handleSendMessage = async () => {
    if ((!input.trim() && attachedFiles.length === 0) || isLoading) return

    // Upload attached files first
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

      // If only files were attached without a message, show success message
      if (!input.trim()) {
        let successContent = 'Files uploaded successfully to this session! You can now ask questions about them.'

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
      const formData = new FormData()
      formData.append('query', input)
      formData.append('session_id', sessionId) // 🎯 Pass session ID!
      formData.append('use_cache', 'true')

      // Add selected model if specified
      if (selectedModel) {
        formData.append('model_id', selectedModel)
      }

      // 🆕 Pass conversation history for context continuity
      // Include last 10 messages (5 exchanges) for context window
      const recentMessages = messages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      formData.append('conversation_history', JSON.stringify(recentMessages))

      console.log(`📤 Querying with session ${sessionId} and ${recentMessages.length} context messages`)

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
        timestamp: new Date()
      }

      // Log context usage
      if (response.data.context_info) {
        console.log(`📚 Context: ${response.data.context_info}`)
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

  const handleClearSession = async () => {
    if (!confirm('Clear this session? This will:\n• Remove all messages\n• Remove document associations\n• Start a fresh conversation\n\nDocuments will remain in the system for future sessions.')) {
      return
    }

    try {
      // Clear session on backend
      await axios.post(`${API_URL}/api/v1/sessions/${sessionId}/clear`)
      console.log(`🧹 Cleared session: ${sessionId}`)

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
    return <WebScraper />
  }

  return (
    <div className="flex flex-col h-full">
      {/* Model Selector Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Model:
            </span>
            <ModelSelector
              selectedModel={selectedModel}
              onModelChange={setSelectedModel}
            />
          </div>
          <div className="flex items-center gap-4">
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {messages.length - 1} messages
            </div>
            <button
              onClick={handleClearSession}
              className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 flex items-center gap-1 px-3 py-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Clear session and start fresh"
            >
              <Trash2 className="w-4 h-4" />
              Clear Session
            </button>
          </div>
        </div>
      </div>

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

              {/* Model used and context info (for assistant messages) */}
              {message.role === 'assistant' && (message.model_name || message.contextInfo) && (
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  {message.model_name && (
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
                      {message.model_name}
                    </span>
                  )}
                  {message.contextInfo && (
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                      📚 {message.contextInfo}
                    </span>
                  )}
                </div>
              )}

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
                            {source.memory_type === 'short-term' && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
                                Session
                              </span>
                            )}
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

              <p className="text-xs text-slate-500 mt-2" suppressHydrationWarning>
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

      {/* Uploaded Files List */}
      <UploadedFilesList sessionId={sessionId} />

      {/* Input Area */}
      <div className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <div className="max-w-4xl mx-auto">
          {/* Attached Files Display */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100 px-3 py-1.5 rounded-lg text-sm"
                >
                  <FileText className="w-4 h-4" />
                  <span className="max-w-[200px] truncate">{file.name}</span>
                  <button
                    onClick={() => removeAttachedFile(index)}
                    className="hover:bg-blue-200 dark:hover:bg-blue-800 rounded p-0.5"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2">
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
              className="px-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              title="Attach files"
            >
              <Paperclip className="w-5 h-5" />
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question or attach files..."
              className="flex-1 resize-none rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              disabled={isLoading || uploadingFiles}
            />
            <button
              onClick={handleSendMessage}
              disabled={(attachedFiles.length === 0 && !input.trim()) || isLoading || uploadingFiles}
              className="px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isLoading || uploadingFiles ? (
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
