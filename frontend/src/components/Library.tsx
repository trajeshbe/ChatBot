import { useState, useEffect } from 'react'
import {
  FolderOpen,
  File,
  FileText,
  Image as ImageIcon,
  FileCode,
  Download,
  Trash2,
  Search,
  Filter,
  Eye,
  X,
  Loader2,
  AlertCircle
} from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Project {
  id: string
  name: string
  department_name?: string
  team_name?: string
  file_count: number
  total_size: number
}

interface FileItem {
  id: string
  filename: string
  file_type: string
  file_size: number
  upload_date: string
  processed: boolean
  processing_status: string
  project_name?: string
  uploaded_by_username?: string
  department_name?: string
  team_name?: string
  minio_path?: string
  chunk_count: number
  has_embeddings: boolean
}

interface LibraryProps {
  currentUser?: {
    id: string
    username: string
    role: string
  }
}

export default function Library({ currentUser }: LibraryProps) {
  // Projects state
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [loadingProjects, setLoadingProjects] = useState(false)

  // Files state
  const [files, setFiles] = useState<FileItem[]>([])
  const [loadingFiles, setLoadingFiles] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [fileTypeFilter, setFileTypeFilter] = useState('all')

  // Preview state
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [previewContent, setPreviewContent] = useState<string | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)

  // Error state
  const [error, setError] = useState<string | null>(null)

  // Load projects on mount
  useEffect(() => {
    loadProjects()
  }, [])

  // Load files when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadFiles(selectedProjectId)
    } else {
      setFiles([])
      setSelectedFile(null)
    }
  }, [selectedProjectId, searchQuery, fileTypeFilter])

  const loadProjects = async () => {
    setLoadingProjects(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')  // Fixed: was 'token', should be 'access_token'
      const response = await axios.get(`${API_URL}/api/v1/projects`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      setProjects(response.data)

      // Auto-select first project if available
      if (response.data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(response.data[0].id)
      }
    } catch (err: any) {
      console.error('Error loading projects:', err)
      setError('Failed to load projects')
    } finally {
      setLoadingProjects(false)
    }
  }

  const loadFiles = async (projectId: string) => {
    setLoadingFiles(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (fileTypeFilter !== 'all') params.append('file_type', fileTypeFilter)

      const response = await axios.get(
        `${API_URL}/api/v1/library/projects/${projectId}/files?${params.toString()}`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      setFiles(response.data)
    } catch (err: any) {
      console.error('Error loading files:', err)
      setError('Failed to load files')
    } finally {
      setLoadingFiles(false)
    }
  }

  const handleDownload = async (file: FileItem) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${API_URL}/api/v1/library/files/${file.id}/download-url`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )

      // Open download URL in new tab
      window.open(response.data.download_url, '_blank')
    } catch (err: any) {
      console.error('Error downloading file:', err)
      alert('Failed to download file')
    }
  }

  const handleDelete = async (file: FileItem) => {
    if (!confirm(`Are you sure you want to delete "${file.filename}"?`)) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      await axios.delete(`${API_URL}/api/v1/library/files/${file.id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      // Refresh file list
      if (selectedProjectId) {
        loadFiles(selectedProjectId)
      }

      // Clear preview if deleted file was selected
      if (selectedFile?.id === file.id) {
        setSelectedFile(null)
        setPreviewContent(null)
      }

      // Refresh projects to update file count
      loadProjects()
    } catch (err: any) {
      console.error('Error deleting file:', err)
      alert(err.response?.data?.detail || 'Failed to delete file')
    }
  }

  const handlePreview = async (file: FileItem) => {
    setSelectedFile(file)
    setLoadingPreview(true)
    setPreviewContent(null)

    // For now, just show file metadata
    // In future, could fetch actual content for text files
    setLoadingPreview(false)
  }

  // Get file icon
  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return ImageIcon
    if (fileType.includes('pdf')) return FileText
    if (fileType.includes('text') || fileType.includes('markdown')) return FileText
    if (fileType.includes('code') || fileType.includes('json')) return FileCode
    return File
  }

  // Format file size
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="flex h-full bg-slate-50 dark:bg-slate-900">
      {/* Projects Panel (Left) */}
      <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col">
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            Projects
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loadingProjects ? (
            <div className="p-4 text-center text-slate-500">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
              Loading...
            </div>
          ) : projects.length === 0 ? (
            <div className="p-4 text-center text-sm text-slate-500">
              No projects yet
            </div>
          ) : (
            projects.map((project) => (
              <button
                key={project.id}
                onClick={() => setSelectedProjectId(project.id)}
                className={`w-full px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-700 border-b border-slate-100 dark:border-slate-700 transition-colors ${
                  selectedProjectId === project.id
                    ? 'bg-primary-50 dark:bg-primary-900/20 border-l-4 border-l-primary-600'
                    : ''
                }`}
              >
                <div className="font-medium text-sm text-slate-900 dark:text-white truncate">
                  {project.name}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                  {project.department_name} • {project.team_name}
                </div>
                <div className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  {project.file_count} file{project.file_count !== 1 ? 's' : ''} •{' '}
                  {formatSize(project.total_size)}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Files Panel (Center) */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Search and Filter Bar */}
        <div className="p-4 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search files..."
                className="w-full pl-9 pr-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <select
              value={fileTypeFilter}
              onChange={(e) => setFileTypeFilter(e.target.value)}
              className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Types</option>
              <option value="application/pdf">PDF</option>
              <option value="text/plain">Text</option>
              <option value="application/json">JSON</option>
              <option value="text/markdown">Markdown</option>
            </select>
          </div>
        </div>

        {/* Files List */}
        <div className="flex-1 overflow-y-auto">
          {!selectedProjectId ? (
            <div className="flex items-center justify-center h-full text-slate-500">
              <div className="text-center">
                <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Select a project to view files</p>
              </div>
            </div>
          ) : loadingFiles ? (
            <div className="p-8 text-center text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" />
              Loading files...
            </div>
          ) : files.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <File className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No files in this project</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-200 dark:divide-slate-700">
              {files.map((file) => {
                const FileIcon = getFileIcon(file.file_type)
                return (
                  <div
                    key={file.id}
                    className={`p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors cursor-pointer ${
                      selectedFile?.id === file.id
                        ? 'bg-primary-50 dark:bg-primary-900/20'
                        : ''
                    }`}
                    onClick={() => handlePreview(file)}
                  >
                    <div className="flex items-start gap-3">
                      <FileIcon className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-slate-900 dark:text-white truncate">
                          {file.filename}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {formatSize(file.file_size)} • {formatDate(file.upload_date)}
                        </div>
                        <div className="flex items-center gap-3 mt-2">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              file.processing_status === 'completed'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                : file.processing_status === 'failed'
                                ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                            }`}
                          >
                            {file.processing_status}
                          </span>
                          {file.chunk_count > 0 && (
                            <span className="text-xs text-slate-500">
                              {file.chunk_count} chunks
                            </span>
                          )}
                          {file.has_embeddings && (
                            <span className="text-xs text-green-600 dark:text-green-400">
                              ✓ Indexed
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDownload(file)
                          }}
                          className="p-2 hover:bg-slate-200 dark:hover:bg-slate-600 rounded transition-colors"
                          title="Download"
                        >
                          <Download className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(file)
                          }}
                          className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Preview Panel (Right) */}
      {selectedFile && (
        <div className="w-96 bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 flex flex-col">
          {/* Preview Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Preview
            </h3>
            <button
              onClick={() => setSelectedFile(null)}
              className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {/* Preview Content */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              {/* File Info */}
              <div>
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  File Information
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Name:</span>
                    <span className="ml-2 text-slate-900 dark:text-white font-medium">
                      {selectedFile.filename}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Type:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {selectedFile.file_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Size:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {formatSize(selectedFile.file_size)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Uploaded:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {formatDate(selectedFile.upload_date)}
                    </span>
                  </div>
                  {selectedFile.uploaded_by_username && (
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Uploaded by:</span>
                      <span className="ml-2 text-slate-900 dark:text-white">
                        {selectedFile.uploaded_by_username}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Organization */}
              <div>
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Organization
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Project:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {selectedFile.project_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Department:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {selectedFile.department_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Team:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {selectedFile.team_name}
                    </span>
                  </div>
                </div>
              </div>

              {/* Processing Status */}
              <div>
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Processing Status
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Status:</span>
                    <span
                      className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        selectedFile.processing_status === 'completed'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : selectedFile.processing_status === 'failed'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                      }`}
                    >
                      {selectedFile.processing_status}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Chunks:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {selectedFile.chunk_count}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Indexed:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">
                      {selectedFile.has_embeddings ? '✓ Yes' : '✗ No'}
                    </span>
                  </div>
                </div>
              </div>

              {/* MinIO Path */}
              {selectedFile.minio_path && (
                <div>
                  <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Storage Path
                  </h4>
                  <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded text-xs font-mono text-slate-600 dark:text-slate-400 break-all">
                    {selectedFile.minio_path}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => handleDownload(selectedFile)}
                  className="flex-1 px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2 text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
                <button
                  onClick={() => handleDelete(selectedFile)}
                  className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2 text-sm font-medium"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-2">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
