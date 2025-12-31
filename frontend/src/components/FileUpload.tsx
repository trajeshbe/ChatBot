import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react'
import axios from 'axios'
import ProjectSelector from './ProjectSelector'

interface Project {
  id: string
  name: string
  description?: string
  department_name?: string
  team_name?: string
}

interface UploadedFile {
  name: string
  size: number
  status: 'uploading' | 'processing' | 'success' | 'error' | 'duplicate'
  documentId?: string
  error?: string
}

interface FileUploadProps {
  currentUser?: {
    id: string
    username: string
    role: string
    department_id?: string
    team_id?: string
  }
  sessionId?: string
  projectId?: string  // ✅ Accept project ID from parent
  onUploadComplete?: () => void  // ✅ Callback after upload
  hideProjectSelector?: boolean  // ✅ Hide internal project selector when parent manages it
  compact?: boolean  // ✅ Compact mode for scaled contexts (smaller icons, less padding)
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Get or create session ID
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

export default function FileUpload({
  currentUser,
  sessionId: externalSessionId,
  projectId: externalProjectId,
  onUploadComplete,
  hideProjectSelector = false,
  compact = false
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [sessionId, setSessionId] = useState<string>('')
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)

  useEffect(() => {
    // Use external session if provided, otherwise generate one
    setSessionId(externalSessionId || getSessionId())

    // Use external project ID if provided, otherwise load from localStorage
    if (externalProjectId) {
      setSelectedProjectId(externalProjectId)
      console.log('📁 [FileUpload] Using external project ID:', externalProjectId)
    } else if (typeof window !== 'undefined') {
      const savedProjectId = localStorage.getItem('selected_project_id')
      if (savedProjectId) {
        setSelectedProjectId(savedProjectId)
        console.log('📁 [FileUpload] Loaded project ID from localStorage:', savedProjectId)
      }
    }
  }, [externalSessionId, externalProjectId])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const currentSessionId = getSessionId()

    // ✅ FIX: Use externalProjectId with priority over internal state
    const projectIdToUse = externalProjectId || selectedProjectId
    console.log(`📁 [FileUpload.onDrop] Using project ID: ${projectIdToUse} (external: ${externalProjectId}, internal: ${selectedProjectId})`)

    for (const file of acceptedFiles) {
      // Check if file is already in the list (client-side duplicate check)
      const isDuplicate = files.some(
        f => f.name === file.name && f.size === file.size && f.status !== 'error'
      )

      if (isDuplicate) {
        console.warn(`⚠️ File ${file.name} is already in the upload list`)
        // Still add it to show the duplicate status
        setFiles(prev => [...prev, {
          name: file.name,
          size: file.size,
          status: 'duplicate',
          error: 'This file is already in your current session'
        }])
        continue // Skip to next file
      }

      const uploadedFile: UploadedFile = {
        name: file.name,
        size: file.size,
        status: 'uploading'
      }

      setFiles(prev => [...prev, uploadedFile])

      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('session_id', currentSessionId) // 🎯 Pass session ID!
        if (projectIdToUse) {
          formData.append('project_id', projectIdToUse) // ✅ FIX: Use prioritized project ID!
          console.log(`📁 [FileUpload] Uploading ${file.name} to project: ${projectIdToUse}`)
        }

        const token = localStorage.getItem('access_token')
        console.log('[FileUpload] Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NULL')
        console.log('[FileUpload] Sending Authorization header:', !!token)

        const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          onUploadProgress: (progressEvent) => {
            // Update progress if needed
          }
        })

        // Check if the backend indicates success
        if (response.data.success === false) {
          // Handle duplicate file case
          if (response.data.duplicate) {
            console.warn(`⚠️ Duplicate file: ${file.name} already exists in session`)
            setFiles(prev =>
              prev.map(f =>
                f.name === file.name
                  ? {
                      ...f,
                      status: 'duplicate',
                      documentId: response.data.existing_document_id,
                      error: response.data.message || 'File already exists in this session'
                    }
                  : f
              )
            )
            return // Skip to next file
          }

          // Handle other backend errors
          console.error(`❌ Upload failed for ${file.name}: ${response.data.message}`)
          setFiles(prev =>
            prev.map(f =>
              f.name === file.name
                ? {
                    ...f,
                    status: 'error',
                    error: response.data.message || 'Upload failed'
                  }
                : f
            )
          )
          return
        }

        console.log(`✅ Uploaded ${file.name} to session ${currentSessionId}`)

        setFiles(prev =>
          prev.map(f =>
            f.name === file.name
              ? {
                  ...f,
                  status: 'success',
                  documentId: response.data.document_id
                }
              : f
          )
        )

        // ✅ Call onUploadComplete callback if provided
        if (onUploadComplete) {
          onUploadComplete()
        }
      } catch (error: any) {
        console.error('Upload error:', error)

        // Extract error message from backend response
        const errorMessage = error.response?.data?.detail
          || error.response?.data?.message
          || error.message
          || 'Upload failed. Please try again.'

        setFiles(prev =>
          prev.map(f =>
            f.name === file.name
              ? {
                  ...f,
                  status: 'error',
                  error: errorMessage
                }
              : f
          )
        )
      }
    }
  }, [files, selectedProjectId, externalProjectId])  // ✅ FIX: Add project IDs to dependencies!

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/json': ['.json'],
      'text/markdown': ['.md']
    }
  })

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className={`h-full ${compact ? 'p-2' : 'p-6'} overflow-y-auto`}>
      <div className={compact ? '' : 'max-w-4xl mx-auto'}>
        {/* Hide header and description in compact mode */}
        {!compact && (
          <>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Upload Documents
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Upload documents to be processed and added to the knowledge base. Supported formats: PDF, TXT, DOC, DOCX, JSON, MD
            </p>
          </>
        )}

        {/* Project Selector - Hide when parent component manages project selection */}
        {!hideProjectSelector && !compact && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Project (Optional)
            </label>
            <ProjectSelector
              value={selectedProjectId}
              onChange={(projectId, project) => {
                setSelectedProjectId(projectId)
                setSelectedProject(project)
                // Save to localStorage for ChatInterface sync
                if (projectId) {
                  localStorage.setItem('selected_project_id', projectId)
                } else {
                  localStorage.removeItem('selected_project_id')
                }
                console.log('📁 [FileUpload] Selected project ID saved to localStorage:', projectId)
              }}
              currentUser={currentUser}
              placeholder="Select a project or upload without a project"
            />
            {selectedProject && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                Files will be organized in:{' '}
                <span className="font-mono text-primary-600 dark:text-primary-400">
                  {selectedProject.department_name}/{selectedProject.team_name}/
                  {currentUser?.username || 'username'}/{selectedProject.name}/
                </span>
              </p>
            )}
          </div>
        )}

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg ${compact ? 'p-3' : 'p-12'} text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-600 bg-primary-50 dark:bg-blue-900/20'
              : 'border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-primary-500'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className={`${compact ? 'w-6 h-6' : 'w-16 h-16'} mx-auto text-slate-400 ${compact ? 'mb-1' : 'mb-4'}`} />
          {isDragActive ? (
            <p className={`${compact ? 'text-xs' : 'text-lg'} text-primary-600 dark:text-blue-400`}>
              Drop the files here...
            </p>
          ) : (
            <>
              <p className={`${compact ? 'text-xs' : 'text-lg'} text-slate-700 dark:text-slate-300 ${compact ? 'mb-0' : 'mb-2'}`}>
                {compact ? 'Drag & drop or click' : 'Drag & drop files here, or click to select files'}
              </p>
              {!compact && (
                <p className="text-sm text-slate-500">
                  Documents will be processed with Docling and embedded into pgvector
                </p>
              )}
            </>
          )}
        </div>

        {/* Uploaded Files List */}
        {files.length > 0 && (
          <div className={compact ? 'mt-2' : 'mt-8'}>
            {!compact && (
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Uploaded Files
              </h3>
            )}
            <div className={compact ? 'space-y-1' : 'space-y-3'}>
              {files.map((file, index) => (
                <div
                  key={index}
                  className={`bg-white dark:bg-slate-800 rounded ${compact ? 'p-1.5' : 'p-4'} shadow-sm border border-slate-200 dark:border-slate-700`}
                >
                  <div className="flex items-center justify-between">
                    <div className={`flex items-center ${compact ? 'gap-1.5' : 'gap-3'} flex-1`}>
                      <FileText className={`${compact ? 'w-4 h-4' : 'w-8 h-8'} text-primary-600`} />
                      <div className="flex-1">
                        <p className={`${compact ? 'text-xs' : 'font-medium'} text-slate-900 dark:text-white ${compact ? 'truncate' : ''}`}>
                          {file.name}
                        </p>
                        {!compact && (
                          <p className="text-sm text-slate-500">
                            {formatFileSize(file.size)}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className={`flex items-center ${compact ? 'gap-1' : 'gap-2'}`}>
                      {file.status === 'uploading' && (
                        <>
                          <Loader2 className={`${compact ? 'w-3 h-3' : 'w-5 h-5'} animate-spin text-primary-600`} />
                          {!compact && <span className="text-sm text-slate-600">Uploading...</span>}
                        </>
                      )}
                      {file.status === 'processing' && (
                        <>
                          <Loader2 className={`${compact ? 'w-3 h-3' : 'w-5 h-5'} animate-spin text-primary-600`} />
                          {!compact && <span className="text-sm text-slate-600">Processing...</span>}
                        </>
                      )}
                      {file.status === 'success' && (
                        <>
                          <CheckCircle className={`${compact ? 'w-3 h-3' : 'w-5 h-5'} text-green-600`} />
                          {!compact && <span className="text-sm text-green-600">Processed</span>}
                        </>
                      )}
                      {file.status === 'duplicate' && (
                        <>
                          <AlertCircle className={`${compact ? 'w-3 h-3' : 'w-5 h-5'} text-amber-600`} />
                          {!compact && <span className="text-sm text-amber-600">{file.error || 'Already uploaded'}</span>}
                        </>
                      )}
                      {file.status === 'error' && (
                        <>
                          <XCircle className={`${compact ? 'w-3 h-3' : 'w-5 h-5'} text-red-600`} />
                          {!compact && <span className="text-sm text-red-600">{file.error}</span>}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
