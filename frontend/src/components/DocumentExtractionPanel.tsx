import { useState, useRef } from 'react'
import { Upload, Loader2, CheckCircle, XCircle, FileText, Download } from 'lucide-react'
import axios from 'axios'
import ExtractionResults from './ExtractionResults'

interface DocumentExtractionRequest {
  document_id: string
  session_id?: string
  project_id?: string
  extract_mode: 'auto' | 'text' | 'vision' | 'hybrid'
  model_id?: string
}

interface DocumentExtractionResult {
  // Project Metadata (11 fields)
  project_name?: string
  address?: string
  project_status?: string
  storeys?: number
  gross_floor_area?: number
  site_area?: number
  zoning?: string
  heritage_designation?: string
  architect?: string
  developer?: string
  planning_consultant?: string

  // Building Information (7 fields)
  residential_units?: number
  unit_types?: string[]
  commercial_uses?: string[]
  amenities?: string[]
  parking_levels?: number
  parking_spaces?: number
  public_realm_features?: string[]

  // Metadata
  fields_extracted: number
  total_fields: number
  extraction_method?: string
  processing_time_ms?: number
}

interface DocumentExtractionResponse {
  success: boolean
  document_id: string
  data: DocumentExtractionResult
  error?: string
}

interface UploadedDocument {
  id: string
  filename: string
  file_type: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DocumentExtractionPanel() {
  const [isExtracting, setIsExtracting] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState<DocumentExtractionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null)
  const [extractMode, setExtractMode] = useState<'auto' | 'text' | 'vision' | 'hybrid'>('auto')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Get session ID from sessionStorage
  const getSessionId = (): string => {
    if (typeof window === 'undefined') return ''
    let sessionId = sessionStorage.getItem('chat_session_id')
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('chat_session_id', sessionId)
    }
    return sessionId
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['.pdf', '.docx', '.png', '.jpg', '.jpeg', '.tiff']
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!validTypes.includes(fileExt)) {
      setError(`Please upload a valid document: ${validTypes.join(', ')}`)
      return
    }

    setIsUploading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', getSessionId())

    try {
      const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setUploadedDocument({
        id: response.data.document_id,
        filename: file.name,
        file_type: fileExt.replace('.', '')
      })
    } catch (err: any) {
      console.error('Upload error:', err)
      setError(err.response?.data?.detail || 'Failed to upload document')
    } finally {
      setIsUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleExtract = async () => {
    if (!uploadedDocument) return

    setIsExtracting(true)
    setError(null)
    setResult(null)

    const requestData: DocumentExtractionRequest = {
      document_id: uploadedDocument.id,
      session_id: getSessionId(),
      extract_mode: extractMode
    }

    try {
      const response = await axios.post<DocumentExtractionResponse>(
        `${API_URL}/api/v1/modules/docu-extract/extract`,
        requestData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )

      setResult(response.data)
    } catch (err: any) {
      console.error('Extraction error:', err)
      setError(err.response?.data?.detail || 'Failed to extract document data')
    } finally {
      setIsExtracting(false)
    }
  }

  const handleExportJSON = () => {
    if (!result) return

    const dataStr = JSON.stringify(result.data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${result.data.project_name || 'document'}_extraction.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleExportCSV = () => {
    if (!result) return

    const data = result.data
    const csvRows = []

    // Header
    csvRows.push('Field,Value')

    // Project Metadata
    csvRows.push(`Project Name,${data.project_name || 'N/A'}`)
    csvRows.push(`Address,${data.address || 'N/A'}`)
    csvRows.push(`Project Status,${data.project_status || 'N/A'}`)
    csvRows.push(`Storeys,${data.storeys || 'N/A'}`)
    csvRows.push(`Gross Floor Area (m²),${data.gross_floor_area || 'N/A'}`)
    csvRows.push(`Site Area (m²),${data.site_area || 'N/A'}`)
    csvRows.push(`Zoning,${data.zoning || 'N/A'}`)
    csvRows.push(`Heritage Designation,${data.heritage_designation || 'N/A'}`)
    csvRows.push(`Architect,${data.architect || 'N/A'}`)
    csvRows.push(`Developer,${data.developer || 'N/A'}`)
    csvRows.push(`Planning Consultant,${data.planning_consultant || 'N/A'}`)

    // Building Information
    csvRows.push(`Residential Units,${data.residential_units || 'N/A'}`)
    csvRows.push(`Unit Types,"${data.unit_types?.join('; ') || 'N/A'}"`)
    csvRows.push(`Commercial Uses,"${data.commercial_uses?.join('; ') || 'N/A'}"`)
    csvRows.push(`Amenities,"${data.amenities?.join('; ') || 'N/A'}"`)
    csvRows.push(`Parking Levels,${data.parking_levels || 'N/A'}`)
    csvRows.push(`Parking Spaces,${data.parking_spaces || 'N/A'}`)
    csvRows.push(`Public Realm Features,"${data.public_realm_features?.join('; ') || 'N/A'}"`)

    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${data.project_name || 'document'}_extraction.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white">
      <div className="flex-1 flex flex-col items-center justify-start p-8 overflow-y-auto">
        <div className="w-full max-w-6xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">
              Document Intelligence Extraction
            </h1>
            <p className="text-slate-600">
              Extract 18 structured fields from planning documents and architectural drawings using AI
            </p>
          </div>

          {/* Upload Section */}
          <div className="mb-8">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isExtracting}
              className="w-full py-6 px-8 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex flex-col items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
                  <span className="text-blue-700 font-medium">Uploading document...</span>
                </>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-blue-600" />
                  <span className="text-blue-700 font-medium">Click to upload document</span>
                  <span className="text-sm text-slate-500">
                    PDF, DOCX, PNG, JPEG, TIFF supported
                  </span>
                </>
              )}
            </button>
          </div>

          {/* Uploaded Document Display */}
          {uploadedDocument && !result && (
            <div className="mb-8 space-y-4">
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                  <div>
                    <div className="font-semibold text-emerald-900">{uploadedDocument.filename}</div>
                    <div className="text-sm text-emerald-700">File type: {uploadedDocument.file_type.toUpperCase()}</div>
                  </div>
                </div>
              </div>

              {/* Extraction Mode Selector */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="text-sm font-semibold text-slate-700 mb-3">Extraction Mode</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {(['auto', 'text', 'vision', 'hybrid'] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setExtractMode(mode)}
                      className={`py-2 px-4 rounded-lg font-medium transition-colors ${
                        extractMode === mode
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      {mode.charAt(0).toUpperCase() + mode.slice(1)}
                    </button>
                  ))}
                </div>
                <div className="mt-3 text-xs text-slate-600">
                  <strong>Auto:</strong> Automatically choose best method •
                  <strong> Text:</strong> PDF/DOCX text •
                  <strong> Vision:</strong> GPT-4o Vision •
                  <strong> Hybrid:</strong> Combined
                </div>
              </div>

              {/* Extract Button */}
              <button
                onClick={handleExtract}
                disabled={isExtracting}
                className="w-full py-4 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExtracting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Extracting fields...
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5" />
                    Extract 18 Fields
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-red-900">Extraction Failed</div>
                <div className="text-sm text-red-700">{error}</div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {result && result.success && (
            <div className="space-y-6">
              {/* Success Header */}
              <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                  <div>
                    <div className="font-semibold text-emerald-900">
                      Extraction Complete
                    </div>
                    <div className="text-sm text-emerald-700">
                      {result.data.fields_extracted}/{result.data.total_fields} fields extracted •
                      Method: {result.data.extraction_method || 'auto'}
                      {result.data.processing_time_ms &&
                        ` • ${(result.data.processing_time_ms / 1000).toFixed(1)}s`
                      }
                    </div>
                  </div>
                </div>
              </div>

              {/* Extraction Results Component */}
              <ExtractionResults data={result.data} />

              {/* Export Buttons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={handleExportJSON}
                  className="py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download JSON
                </button>
                <button
                  onClick={handleExportCSV}
                  className="py-3 px-4 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download CSV
                </button>
              </div>

              {/* New Extraction Button */}
              <button
                onClick={() => {
                  setResult(null)
                  setUploadedDocument(null)
                  setError(null)
                }}
                className="w-full py-3 px-4 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors font-medium"
              >
                Extract Another Document
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
