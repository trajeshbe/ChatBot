import { useState } from 'react'
import axios from 'axios'
import { FileText, Upload, Network, CheckCircle, AlertCircle, Settings, Download, Table, FileDown } from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import ExportWizardButton from '../../ExportWizardButton'

interface Entity {
  text: string
  type: string
  normalized?: string
  confidence: number
  metadata?: Record<string, any>
}

interface Relation {
  subject: Entity
  relation: string
  object: Entity
  context: string
  source_page?: number
  attributes?: Record<string, any>
  confidence: number
  extraction_method: string
  temporal_info?: Record<string, any>
}

interface RelationExtractionResponse {
  extraction_id: string
  document_id: string
  relations: Relation[]
  graph: {
    nodes: Entity[]
    edges: Relation[]
    num_entities: number
    num_relations: number
  }
  total_relations_found: number
  relations_after_filtering: number
  extraction_time_seconds: number
  extraction_mode: string
  tier_1_services_used: string[]
  avg_confidence: number
  high_confidence_count: number
  created_at: string
}

export default function RelationExtractorPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [showConfig, setShowConfig] = useState(false)
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
    formData.append('company', 'document_intelligence')
    formData.append('usecase', 'relation_extraction')

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

  const exportToFormat = async (format: 'excel' | 'markdown' | 'pdf') => {
    if (!result) return

    try {
      // Prepare export data
      const exportContent = format === 'markdown'
        ? generateMarkdownExport()
        : format === 'excel'
        ? generateExcelData()
        : generateMarkdownExport() // PDF will use markdown as base

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      const filename = `relation_extraction_${timestamp}.${format === 'excel' ? 'xlsx' : format === 'pdf' ? 'pdf' : 'md'}`

      if (format === 'markdown') {
        // Download as .md file directly
        const blob = new Blob([exportContent], { type: 'text/markdown' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } else {
        // Use backend export API for Excel and PDF
        const response = await axios.post('http://localhost:8000/api/v1/export', {
          content: exportContent,
          filename,
          template_type: format,
          template_config: {}
        }, {
          responseType: 'blob'
        })

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export failed:', error)
      setError('Export failed. Please try again.')
    }
  }

  const generateMarkdownExport = () => {
    if (!result) return ''

    return `# Relation Extraction Results

## Summary
- **Entities Found**: ${result.graph.num_entities}
- **Relations Found**: ${result.total_relations_found}
- **Processing Time**: ${result.extraction_time_seconds.toFixed(2)}s
- **Average Confidence**: ${(result.avg_confidence * 100).toFixed(1)}%
- **Extraction Mode**: ${result.extraction_mode}
- **Document ID**: ${result.document_id}

## Entities (${result.graph.nodes.length})

${result.graph.nodes.map(entity => `- **${entity.text}** (${entity.type}) - ${(entity.confidence * 100).toFixed(0)}% confidence`).join('\n')}

## Relationships (${result.relations.length})

${result.relations.map((rel, idx) => `
### ${idx + 1}. ${rel.subject.text} → ${rel.relation} → ${rel.object.text}

- **Confidence**: ${(rel.confidence * 100).toFixed(0)}%
- **Context**: "${rel.context}"
- **Extraction Method**: ${rel.extraction_method}
`).join('\n')}

## Technical Details

- **Document ID**: ${result.document_id}
- **Extraction ID**: ${result.extraction_id}
- **Tier 1 Services Used**: ${result.tier_1_services_used.join(', ')}
- **Created At**: ${new Date(result.created_at).toLocaleString()}

---
*Generated by Relation Extractor Module*
`
  }

  const generateExcelData = () => {
    if (!result) return ''

    // Create CSV-like structure for Excel export
    let csv = 'Entity Extraction Results\n\n'
    csv += 'Entities\n'
    csv += 'Text,Type,Confidence\n'
    result.graph.nodes.forEach(entity => {
      csv += `"${entity.text}","${entity.type}",${entity.confidence}\n`
    })

    csv += '\n\nRelationships\n'
    csv += 'Subject,Relation,Object,Confidence,Context\n'
    result.relations.forEach(rel => {
      csv += `"${rel.subject.text}","${rel.relation}","${rel.object.text}",${rel.confidence},"${rel.context}"\n`
    })

    return csv
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Network className="w-8 h-8 text-purple-600" />
          Relation Extractor - Entity Relationships
        </h1>
        <p className="text-gray-600 mt-2">
          Extract entities and their relationships from documents using LLM-powered analysis
        </p>
      </div>
          </div>
          <div className="flex gap-2">
            <ExportWizardButton
              moduleCode="relation-extractor"
              moduleName="Relation Extractor"
              tier={2}
              variant="button"
              size="md"
            />
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Configure
            </button>
          </div>
        </div>

        {/* Configuration Panel */}
        {showConfig && (
          <div className="mb-6">
            <POCConfigManager
              moduleName="relation-extractor"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

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
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Extraction Summary</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => exportToFormat('markdown')}
                  className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm flex items-center gap-2 transition-colors"
                  title="Export as Markdown"
                >
                  <FileDown className="w-4 h-4" />
                  Markdown
                </button>
                <button
                  onClick={() => exportToFormat('excel')}
                  className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm flex items-center gap-2 transition-colors"
                  title="Export as Excel"
                >
                  <Table className="w-4 h-4" />
                  Excel
                </button>
                <button
                  onClick={() => exportToFormat('pdf')}
                  className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm flex items-center gap-2 transition-colors"
                  title="Export as PDF"
                >
                  <Download className="w-4 h-4" />
                  PDF
                </button>
              </div>
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Entities Found</p>
                <p className="text-3xl font-bold text-blue-900">{result.graph.num_entities}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">Relations Found</p>
                <p className="text-3xl font-bold text-purple-900">{result.total_relations_found}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Processing Time</p>
                <p className="text-3xl font-bold text-gray-900">{result.extraction_time_seconds.toFixed(2)}s</p>
              </div>
            </div>
          </div>

          {/* Entities */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Entities ({result.graph.nodes.length})</h3>
            <div className="flex flex-wrap gap-2">
              {result.graph.nodes.map((entity, idx) => (
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
                  <div className="flex items-center gap-3 mb-2">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded font-medium text-sm">
                      {relation.subject.text}
                    </span>
                    <span className="text-gray-600 text-sm font-medium">
                      → {relation.relation} →
                    </span>
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded font-medium text-sm">
                      {relation.object.text}
                    </span>
                    <span className="ml-auto text-xs text-gray-500">
                      {(relation.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  {relation.context && (
                    <p className="text-sm text-gray-600 italic mt-2">"{relation.context}"</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Tech Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Document ID:</strong> {result.document_id}</p>
            <p><strong>Extraction Mode:</strong> {result.extraction_mode}</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
            <p><strong>Avg Confidence:</strong> {(result.avg_confidence * 100).toFixed(1)}%</p>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}
