import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react'
import axios from 'axios'

interface UploadedFile {
  name: string
  size: number
  status: 'uploading' | 'processing' | 'success' | 'error' | 'duplicate'
  documentId?: string
  error?: string
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

export default function FileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [sessionId, setSessionId] = useState<string>('')

  useEffect(() => {
    setSessionId(getSessionId())
  }, [])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const currentSessionId = getSessionId()

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

        const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
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
  }, [files])

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
    <div className="h-full p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Upload Documents
        </h2>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Upload documents to be processed and added to the knowledge base. Supported formats: PDF, TXT, DOC, DOCX, JSON, MD
        </p>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-blue-500'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-16 h-16 mx-auto text-slate-400 mb-4" />
          {isDragActive ? (
            <p className="text-lg text-blue-600 dark:text-blue-400">
              Drop the files here...
            </p>
          ) : (
            <>
              <p className="text-lg text-slate-700 dark:text-slate-300 mb-2">
                Drag & drop files here, or click to select files
              </p>
              <p className="text-sm text-slate-500">
                Documents will be processed with Docling and embedded into pgvector
              </p>
            </>
          )}
        </div>

        {/* Uploaded Files List */}
        {files.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Uploaded Files
            </h3>
            <div className="space-y-3">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <FileText className="w-8 h-8 text-blue-600" />
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 dark:text-white">
                          {file.name}
                        </p>
                        <p className="text-sm text-slate-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {file.status === 'uploading' && (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                          <span className="text-sm text-slate-600">Uploading...</span>
                        </>
                      )}
                      {file.status === 'processing' && (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                          <span className="text-sm text-slate-600">Processing...</span>
                        </>
                      )}
                      {file.status === 'success' && (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="text-sm text-green-600">Processed</span>
                        </>
                      )}
                      {file.status === 'duplicate' && (
                        <>
                          <AlertCircle className="w-5 h-5 text-amber-600" />
                          <span className="text-sm text-amber-600">{file.error || 'Already uploaded'}</span>
                        </>
                      )}
                      {file.status === 'error' && (
                        <>
                          <XCircle className="w-5 h-5 text-red-600" />
                          <span className="text-sm text-red-600">{file.error}</span>
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
