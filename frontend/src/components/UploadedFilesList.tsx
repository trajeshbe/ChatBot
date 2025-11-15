import { useState, useEffect } from 'react'
import { FileText, Trash2, RefreshCw, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Document {
  id: string
  filename: string
  file_size: number
  processing_status: string
  has_embeddings: boolean
  chunk_count: number
  created_at: string
  priority: number
}

interface Props {
  sessionId: string
  onRefresh?: () => void
  forceExpand?: boolean
  onExpandChange?: (expanded: boolean) => void
}

export default function UploadedFilesList({ sessionId, onRefresh, forceExpand = false, onExpandChange }: Props) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(true) // Start collapsed

  const loadDocuments = async () => {
    if (!sessionId) {
      setDocuments([])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(
        `${API_URL}/api/v1/sessions/${sessionId}/documents`
      )
      setDocuments(response.data.documents || [])
      console.log(`📄 Loaded ${response.data.documents?.length || 0} documents for session ${sessionId}`)
    } catch (error: any) {
      console.error('Error loading documents:', error)
      setError(error.response?.data?.detail || 'Failed to load documents')
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }

  const deleteDocument = async (documentId: string, filename: string) => {
    if (!confirm(`Delete "${filename}"? This will remove it from your session.`)) {
      return
    }

    try {
      await axios.delete(`${API_URL}/api/v1/documents/${documentId}`)
      console.log(`🗑️ Deleted document: ${filename}`)
      await loadDocuments() // Refresh list
      if (onRefresh) onRefresh()
    } catch (error) {
      console.error('Error deleting document:', error)
      alert('Failed to delete document')
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
    return date.toLocaleDateString()
  }

  useEffect(() => {
    loadDocuments()
  }, [sessionId])

  // Expand when forceExpand is true or when documents are loaded
  useEffect(() => {
    if (forceExpand || (documents.length > 0 && isCollapsed)) {
      setIsCollapsed(false)
    }
  }, [forceExpand, documents.length])

  // Notify parent when collapse state changes
  const toggleCollapse = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    if (onExpandChange) {
      onExpandChange(!newState)
    }
  }

  if (!sessionId) {
    return null
  }

  // Don't show the list if no documents and collapsed
  if (documents.length === 0 && isCollapsed) {
    return null
  }

  return (
    <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={toggleCollapse}
            className="flex items-center gap-1.5 hover:text-blue-600 transition-colors flex-1 text-left"
          >
            <h3 className="text-xs font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" />
              Documents ({documents.length})
            </h3>
            {isCollapsed ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
            )}
          </button>
          {!isCollapsed && (
            <button
              onClick={loadDocuments}
              disabled={loading}
              className="text-xs text-blue-600 hover:text-blue-700 disabled:opacity-50 flex items-center gap-1"
              title="Refresh list"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>

        {!isCollapsed && (
          <>
            {error && (
              <div className="mb-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded flex items-start gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-red-600 mt-0.5 flex-shrink-0" />
                <div className="text-[10px] text-red-800 dark:text-red-200">
                  {error}
                </div>
              </div>
            )}

            {documents.length === 0 && !loading && !error && (
              <div className="text-center py-4 text-xs text-slate-500">
                <FileText className="w-6 h-6 mx-auto mb-1.5 opacity-50" />
                <p>No documents yet</p>
                <p className="text-[10px] mt-0.5">Use the paperclip button</p>
              </div>
            )}

            {documents.length > 0 && (
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
              >
                <div className="flex items-start gap-2 flex-1 min-w-0">
                  <FileText className="w-3.5 h-3.5 text-blue-600 flex-shrink-0 mt-0.5" />

                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-medium text-slate-900 dark:text-white truncate">
                      {doc.filename}
                    </p>

                    <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{formatDate(doc.created_at)}</span>

                      {doc.has_embeddings && doc.chunk_count > 0 ? (
                        <>
                          <span>•</span>
                          <span className="text-green-600 dark:text-green-400">
                            ✓ {doc.chunk_count}
                          </span>
                        </>
                      ) : doc.processing_status === 'processing' ? (
                        <>
                          <span>•</span>
                          <span className="text-yellow-600 dark:text-yellow-400">
                            ⏳
                          </span>
                        </>
                      ) : doc.processing_status === 'failed' ? (
                        <>
                          <span>•</span>
                          <span className="text-red-600 dark:text-red-400">
                            ✗
                          </span>
                        </>
                      ) : null}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => deleteDocument(doc.id, doc.filename)}
                  className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors flex-shrink-0"
                  title="Delete document"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
