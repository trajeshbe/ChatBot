import { useState, useEffect } from 'react'
import { FileText, Trash2, RefreshCw, AlertCircle } from 'lucide-react'
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
}

export default function UploadedFilesList({ sessionId, onRefresh }: Props) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  if (!sessionId) {
    return null
  }

  return (
    <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Uploaded Documents ({documents.length})
          </h3>
          <button
            onClick={loadDocuments}
            disabled={loading}
            className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50 flex items-center gap-1"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {error && (
          <div className="mb-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5" />
            <div className="text-sm text-red-800 dark:text-red-200">
              {error}
            </div>
          </div>
        )}

        {documents.length === 0 && !loading && !error && (
          <div className="text-center py-6 text-sm text-slate-500">
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No documents uploaded yet</p>
            <p className="text-xs mt-1">Use the paperclip button to attach files</p>
          </div>
        )}

        {documents.length > 0 && (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
              >
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <FileText className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {doc.filename}
                    </p>

                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{formatDate(doc.created_at)}</span>

                      {doc.has_embeddings && doc.chunk_count > 0 ? (
                        <>
                          <span>•</span>
                          <span className="text-green-600 dark:text-green-400 flex items-center gap-1">
                            ✓ {doc.chunk_count} chunks
                          </span>
                        </>
                      ) : doc.processing_status === 'processing' ? (
                        <>
                          <span>•</span>
                          <span className="text-yellow-600 dark:text-yellow-400">
                            ⏳ Processing...
                          </span>
                        </>
                      ) : doc.processing_status === 'failed' ? (
                        <>
                          <span>•</span>
                          <span className="text-red-600 dark:text-red-400">
                            ✗ Failed
                          </span>
                        </>
                      ) : (
                        <>
                          <span>•</span>
                          <span className="text-orange-600 dark:text-orange-400">
                            ⚠ Not embedded
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => deleteDocument(doc.id, doc.filename)}
                  className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors flex-shrink-0"
                  title="Delete document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
