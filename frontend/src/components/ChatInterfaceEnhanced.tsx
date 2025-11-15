import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText, ExternalLink, Paperclip, X, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import FileUpload from './FileUpload'
import WebScraper from './WebScraper'
import ModelSelector from './ModelSelector'
import UploadedFilesList from './UploadedFilesList'
import { getCurrentRAGConfig, type RAGConfig } from './RAGSettings'
import PerformanceMetrics from './PerformanceMetrics'
import EvaluationMetrics from './EvaluationMetrics'
import RAGSettingsDisplay from './RAGSettingsDisplay'
import axios from 'axios'

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
  }
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
  activeTab: 'chat' | 'upload' | 'scrape' | 'evaluation'
  ragConfig?: RAGConfig | null
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
      return parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))
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
    localStorage.setItem(`chat_messages_${sessionId}`, JSON.stringify(messages))
  } catch (error) {
    console.error('Error saving messages to localStorage:', error)
  }
}

export default function ChatInterfaceEnhanced({ activeTab, ragConfig: ragConfigProp }: Props) {
  const [sessionId, setSessionId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>(() => {
    // Initialize messages by loading from localStorage if available
    const initialSessionId = getSessionId()
    return loadMessages(initialSessionId)
  })
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [filesJustUploaded, setFilesJustUploaded] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Use prop config if available, otherwise get from localStorage
  const ragConfig = ragConfigProp || getCurrentRAGConfig()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize session ID on mount
  useEffect(() => {
    const id = getSessionId()
    setSessionId(id)
  }, [])

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      saveMessages(sessionId, messages)
      console.log(`💾 Saved ${messages.length} messages for session ${sessionId}`)
    }
  }, [messages, sessionId])

  // Load messages when sessionId changes (e.g., after clearing session)
  useEffect(() => {
    if (sessionId) {
      const loadedMessages = loadMessages(sessionId)
      // Only update if different from current messages to avoid infinite loop
      if (JSON.stringify(loadedMessages) !== JSON.stringify(messages)) {
        setMessages(loadedMessages)
        console.log(`📥 Loaded ${loadedMessages.length} messages for session ${sessionId}`)
      }
    }
  }, [sessionId]) // Only depend on sessionId, not messages

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
      setFilesJustUploaded(true) // Signal that files were just uploaded
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

      // 🆕 Add RAG configuration parameters
      formData.append('top_k', ragConfig.top_k.toString())
      formData.append('similarity_threshold', ragConfig.similarity_threshold.toString())
      formData.append('min_similarity_threshold', ragConfig.min_similarity_threshold.toString())
      formData.append('no_relevant_docs_threshold', ragConfig.no_relevant_docs_threshold.toString())

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
        timestamp: new Date(),
        // 🆕 Capture performance metrics
        latency_ms: response.data.latency_ms,
        tokens_used: response.data.tokens_used,
        num_sources: response.data.sources?.length || 0,
        cached: response.data.cached || false,
        // 🆕 Capture evaluation metrics
        quality_metrics: response.data.quality_metrics,
        // 🆕 Capture RAG settings used for this query
        rag_settings: response.data.rag_settings
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
    return <WebScraper />
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900">
      {/* Model Selector Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
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
              className="text-xs text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Clear session and start fresh"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>
          </div>
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
                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-md shadow-sm'
                  : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-md border border-slate-200 dark:border-slate-700'
              }`}
            >
              <div className={`markdown-content ${message.role === 'user' ? 'user-message-text' : ''}`}>
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>

              {/* Model used and context info (for assistant messages) */}
              {message.role === 'assistant' && (message.model_name || message.contextInfo) && (
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  {message.model_name && (
                    <span className="text-xs px-1.5 py-0.5 rounded-md bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
                      {message.model_name}
                    </span>
                  )}
                  {message.contextInfo && (
                    <span className="text-xs px-1.5 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                      📚 {message.contextInfo}
                    </span>
                  )}
                </div>
              )}

              {/* 🆕 Performance Metrics */}
              {message.role === 'assistant' && (
                <PerformanceMetrics
                  metrics={{
                    latency_ms: message.latency_ms,
                    tokens_used: message.tokens_used,
                    num_sources: message.num_sources,
                    cached: message.cached,
                    model_used: message.model,
                    model_name: message.model_name
                  }}
                />
              )}

              {/* 🆕 Evaluation Metrics */}
              {message.role === 'assistant' && message.quality_metrics && (
                <EvaluationMetrics metrics={message.quality_metrics} />
              )}

              {/* 🆕 RAG Settings Used */}
              {message.role === 'assistant' && message.rag_settings && (
                <RAGSettingsDisplay settings={message.rag_settings} />
              )}

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
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
                              <ExternalLink className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
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
                            {(source.relevance * 100).toFixed(0)}%
                          </span>
                        </div>
                        {source.source_url && (
                          <a
                            href={source.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-blue-600 hover:underline mt-1 block truncate"
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

              <p className="text-[10px] text-slate-500 dark:text-slate-500 mt-2" suppressHydrationWarning>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-semibold text-sm">
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
                  className="flex items-center gap-2 bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100 px-2.5 py-1.5 rounded-lg text-xs border border-blue-200 dark:border-blue-800"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span className="max-w-[200px] truncate">{file.name}</span>
                  <button
                    onClick={() => removeAttachedFile(index)}
                    className="hover:bg-blue-100 dark:hover:bg-blue-800 rounded p-0.5"
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

            <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 focus-within:border-blue-500 dark:focus-within:border-blue-500 transition-colors">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message RAG Bot..."
                className="w-full resize-none bg-transparent px-4 py-3 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none"
                rows={1}
                disabled={isLoading || uploadingFiles}
              />
            </div>

            <button
              onClick={handleSendMessage}
              disabled={(attachedFiles.length === 0 && !input.trim()) || isLoading || uploadingFiles}
              className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed transition-colors flex items-center"
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
    </div>
  )
}
