import { useState } from 'react'
import axios from 'axios'
import { FileText, Upload, Network, CheckCircle, AlertCircle } from 'lucide-react'

interface Entity {
  text: string
  type: string
  start_pos: number
  end_pos: number
}

interface Relation {
  subject: string
  predicate: string
  object: string
  confidence: number
}

interface RelationExtractionResponse {
  extraction_id: string
  document_id: string
  document_name: string
  entities: Entity[]
  relations: Relation[]
  entity_count: number
  relation_count: number
  processing_time_seconds: number
  tier_1_services_used: string[]
}

export default function RelationExtractorPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [documentId, setDocumentId] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RelationExtractionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0]
    if (!uploadedFile) return

    setFile(uploadedFile)
    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', uploadedFile)
    formData.append('session_id', sessionId)

    try {
      const response = await axios.post('http://localhost:8000/api/v1/upload', formData)
      setDocumentId(response.data.document_id)
    } catch (err: any) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleExtract = async () => {
    if (!documentId) {
      setError('Please upload a document first')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post<RelationExtractionResponse>(
        'http://localhost:8000/api/v1/modules/relation-extractor/extract',
        {
          document_id: documentId,
          session_id: sessionId
        }
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Extraction failed')
    } finally {
      setLoading(false)
    }
  }

  const getEntityColor = (type: string) => {
    const colors: Record<string, string> = {
      PERSON: 'bg-blue-100 text-blue-800',
      ORG: 'bg-green-100 text-green-800',
      ORGANIZATION: 'bg-green-100 text-green-800',
      LOCATION: 'bg-purple-100 text-purple-800',
      DATE: 'bg-yellow-100 text-yellow-800',
      MONEY: 'bg-red-100 text-red-800',
      PRODUCT: 'bg-indigo-100 text-indigo-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Network className="w-8 h-8 text-purple-600" />
          Relation Extractor - Entity Relationships
        </h1>
        <p className="text-gray-600 mt-2">
          Extract entities and their relationships from documents using LLM-powered analysis
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Document
        </h2>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors">
          <input
            type="file"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
            accept=".pdf,.docx,.txt"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">Click to upload</p>
            <p className="text-sm text-gray-500">PDF, DOCX, TXT</p>
          </label>
        </div>

        {uploading && (
          <div className="mt-4 text-center text-sm text-gray-600">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600 mx-auto mb-2"></div>
            Uploading...
          </div>
        )}

        {file && documentId && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-green-900">{file.name}</p>
              <p className="text-xs text-green-700">Ready for extraction</p>
            </div>
          </div>
        )}

        <button
          onClick={handleExtract}
          disabled={loading || !documentId}
          className="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Extracting Relationships...
            </>
          ) : (
            <>
              <Network className="w-5 h-5" />
              Extract Entities & Relations
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Error</p>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Extraction Summary</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Entities Found</p>
                <p className="text-3xl font-bold text-blue-900">{result.entity_count}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">Relations Found</p>
                <p className="text-3xl font-bold text-purple-900">{result.relation_count}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Processing Time</p>
                <p className="text-3xl font-bold text-gray-900">{result.processing_time_seconds.toFixed(2)}s</p>
              </div>
            </div>
          </div>

          {/* Entities */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Entities ({result.entities.length})</h3>
            <div className="flex flex-wrap gap-2">
              {result.entities.map((entity, idx) => (
                <span
                  key={idx}
                  className={`px-3 py-1 rounded-full text-sm font-medium ${getEntityColor(entity.type)}`}
                >
                  {entity.text} <span className="text-xs opacity-75">({entity.type})</span>
                </span>
              ))}
            </div>
          </div>

          {/* Relations */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Relationships ({result.relations.length})</h3>
            <div className="space-y-3">
              {result.relations.map((relation, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded font-medium text-sm">
                      {relation.subject}
                    </span>
                    <span className="text-gray-600 text-sm font-medium">
                      → {relation.predicate} →
                    </span>
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded font-medium text-sm">
                      {relation.object}
                    </span>
                    <span className="ml-auto text-xs text-gray-500">
                      {(relation.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tech Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Document:</strong> {result.document_name}</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  )
}
