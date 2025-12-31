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
  projectId?: string  // 🆕 Add project context
  onRefresh?: () => void
  forceExpand?: boolean
  onExpandChange?: (expanded: boolean) => void
}

export default function UploadedFilesList({ sessionId, projectId, onRefresh, forceExpand = false, onExpandChange }: Props) {
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
      // 🆕 Build URL with project_id filter if in project context
      let url = `${API_URL}/api/v1/sessions/${sessionId}/documents`
      if (projectId) {
        url += `?project_id=${projectId}`
        console.log(`📄 Loading documents for session ${sessionId} in project ${projectId}`)
      }

      const response = await axios.get(url)
      setDocuments(response.data.documents || [])
      console.log(`📄 Loaded ${response.data.documents?.length || 0} documents${projectId ? ` for project ${projectId}` : ''}`)
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
  }, [sessionId, projectId])  // 🆕 Reload when project changes

  // 🆕 FIXED: Only expand when explicitly forced, NOT automatically when documents load
  useEffect(() => {
    if (forceExpand) {
      setIsCollapsed(false)
    }
  }, [forceExpand])

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
    <div className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-3">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={toggleCollapse}
            className="flex items-center gap-1.5 hover:text-primary-600 transition-colors flex-1 text-left group"
          >
            <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors" />
              Documents ({documents.length})
            </h3>
            {isCollapsed ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-primary-600 transition-colors" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-slate-400 group-hover:text-primary-600 transition-colors" />
            )}
          </button>
          {!isCollapsed && (
            <button
              onClick={loadDocuments}
              disabled={loading}
              className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 disabled:opacity-50 flex items-center gap-1 transition-colors"
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
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {documents.map((doc) => (
              <div
                key={doc.id}
                className="group inline-flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700 hover:border-primary-300 dark:hover:border-primary-600 hover:bg-slate-50 dark:hover:bg-slate-750 transition-all"
              >
                <FileText className="w-3.5 h-3.5 text-primary-600 dark:text-primary-400 flex-shrink-0" />

                <div className="flex items-center gap-2">
                  <p className="text-xs font-medium text-slate-900 dark:text-white max-w-[200px] truncate">
                    {doc.filename}
                  </p>

                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 dark:text-slate-400">
                    <span>{formatFileSize(doc.file_size)}</span>

                    {doc.has_embeddings && doc.chunk_count > 0 ? (
                      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full font-medium">
                        ✓ {doc.chunk_count}
                      </span>
                    ) : doc.processing_status === 'processing' ? (
                      <span className="inline-flex items-center px-1.5 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full">
                        ⏳
                      </span>
                    ) : doc.processing_status === 'failed' ? (
                      <span className="inline-flex items-center px-1.5 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full">
                        ✗
                      </span>
                    ) : null}
                  </div>
                </div>

                <button
                  onClick={() => deleteDocument(doc.id, doc.filename)}
                  className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 dark:hover:text-red-400 p-0.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-all flex-shrink-0"
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
