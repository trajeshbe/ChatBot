import { useState, useRef } from 'react'
import axios from 'axios'
import { FileText, Upload, Loader2, CheckCircle, XCircle, Layers, Info , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'

// Types matching backend schemas
type PlanningDocumentType =
  | 'architectural'
  | 'structural'
  | 'electrical'
  | 'mechanical'
  | 'plumbing'
  | 'civil'
  | 'landscape'
  | 'interior'
  | 'fire_safety'
  | 'bim_model'
  | 'site_plan'
  | 'floor_plan'
  | 'elevation'
  | 'section'
  | 'detail'
  | 'schedule'
  | 'specification'
  | 'unknown'

type PlanningDocumentPurpose =
  | 'concept'
  | 'schematic_design'
  | 'design_development'
  | 'construction_documents'
  | 'as_built'
  | 'permit_submission'
  | 'bid'
  | 'shop_drawings'
  | 'rfi'
  | 'change_order'
  | 'closeout'
  | 'unknown'

interface DrawingClassification {
  document_type: PlanningDocumentType
  purpose: PlanningDocumentPurpose
  confidence: number
}

interface ExtractedMetadata {
  drawing_number?: string
  drawing_title?: string
  revision?: string
  scale?: string
  date?: string
  architect_firm?: string
  project_number?: string
  sheet_number?: string
}

interface QualityIndicators {
  has_title_block: boolean
  has_scale: boolean
  has_north_arrow: boolean
  drawing_quality: 'excellent' | 'good' | 'fair' | 'poor'
}

interface PlanningClassificationRequest {
  document_id: string
  use_vision?: boolean
  use_text?: boolean
  extract_metadata?: boolean
  min_confidence?: number
  session_id?: string
}

interface PlanningClassificationResponse {
  classification_id: string
  document_id: string
  primary_classification: DrawingClassification
  alternative_classifications: DrawingClassification[]
  extracted_metadata?: ExtractedMetadata
  quality_indicators?: QualityIndicators
  classification_method: string
  processing_time_ms: number
  tier_1_services_used: string[]
}

interface UploadedDocument {
  id: string
  filename: string
  file_type: string
}

const TYPE_COLORS: Record<string, string> = {
  architectural: 'bg-blue-100 text-blue-800',
  structural: 'bg-green-100 text-green-800',
  electrical: 'bg-yellow-100 text-yellow-800',
  mechanical: 'bg-purple-100 text-purple-800',
  plumbing: 'bg-cyan-100 text-cyan-800',
  civil: 'bg-orange-100 text-orange-800',
  landscape: 'bg-emerald-100 text-emerald-800',
  fire_safety: 'bg-red-100 text-red-800',
  unknown: 'bg-gray-100 text-gray-800',
}

const PURPOSE_COLORS: Record<string, string> = {
  concept: 'bg-indigo-100 text-indigo-800',
  schematic_design: 'bg-violet-100 text-violet-800',
  design_development: 'bg-fuchsia-100 text-fuchsia-800',
  construction_documents: 'bg-rose-100 text-rose-800',
  as_built: 'bg-amber-100 text-amber-800',
  permit_submission: 'bg-lime-100 text-lime-800',
  unknown: 'bg-gray-100 text-gray-800',
}

export default function PlanningClassifierPanel() {
  const [isUploading, setIsUploading] = useState(false)
  const [showConfig, setShowConfig] = useState(false)
  const [isClassifying, setIsClassifying] = useState(false)
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null)
  const [useVision, setUseVision] = useState(true)
  const [useText, setUseText] = useState(true)
  const [extractMetadata, setExtractMetadata] = useState(true)
  const [minConfidence, setMinConfidence] = useState(0.7)
  const [result, setResult] = useState<PlanningClassificationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    formData.append('company', 'construction')
    formData.append('usecase', 'planning_classifier')

    try {
      const response = await axios.post('http://localhost:8000/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setUploadedDocument({
        id: response.data.document_id,
        filename: file.name,
        file_type: file.name.substring(file.name.lastIndexOf('.') + 1)
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'File upload failed')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleClassify = async () => {
    if (!uploadedDocument) return

    setIsClassifying(true)
    setError(null)
    setResult(null)

    const requestData: PlanningClassificationRequest = {
      document_id: uploadedDocument.id,
      use_vision: useVision,
      use_text: useText,
      extract_metadata: extractMetadata,
      min_confidence: minConfidence,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<PlanningClassificationResponse>(
        'http://localhost:8000/api/v1/modules/planning-classifier/classify',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Classification failed')
    } finally {
      setIsClassifying(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-orange-600'
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Layers className="w-8 h-8 text-blue-600" />
          Planning Document Classifier
        </h1>
        <p className="text-gray-600 mt-2">
          Classify construction planning documents by type and purpose using AI vision and text analysis
        </p>
      </div>
          </div>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Configure
          </button>
        </div>

        {/* Configuration Panel */}
        {showConfig && (
          <div className="mb-6">
            <POCConfigManager
              moduleName="planning_classifier"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Planning Document
        </h2>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.dwg"
          onChange={handleFileUpload}
          className="hidden"
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || isClassifying}
          className="w-full py-6 px-8 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex flex-col items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
              <span className="text-blue-700 font-medium">Uploading...</span>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-blue-600" />
              <span className="text-blue-700 font-medium">Click to upload planning document</span>
              <span className="text-sm text-gray-500">PDF, PNG, JPEG, DWG supported</span>
            </>
          )}
        </button>

        {uploadedDocument && !result && (
          <div className="mt-4 space-y-4">
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <div>
                  <div className="font-semibold text-emerald-900">{uploadedDocument.filename}</div>
                  <div className="text-sm text-emerald-700">File type: {uploadedDocument.file_type.toUpperCase()}</div>
                </div>
              </div>
            </div>

            {/* Classification Options */}
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="text-sm font-semibold text-gray-700 mb-3">Classification Options</div>
              <div className="space-y-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useVision}
                    onChange={(e) => setUseVision(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Use AI Vision analysis (GPT-4o Vision)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useText}
                    onChange={(e) => setUseText(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Use text content analysis</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={extractMetadata}
                    onChange={(e) => setExtractMetadata(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Extract metadata (drawing number, revision, etc.)</span>
                </label>
                <div>
                  <label className="block text-sm text-gray-700 mb-1">
                    Minimum Confidence: {(minConfidence * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={minConfidence}
                    onChange={(e) => setMinConfidence(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>
            </div>

            {/* Classify Button */}
            <button
              onClick={handleClassify}
              disabled={isClassifying}
              className="w-full py-4 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isClassifying ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Classifying Document...
                </>
              ) : (
                <>
                  <Layers className="w-5 h-5" />
                  Classify Planning Document
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-red-900">Classification Failed</div>
            <div className="text-sm text-red-700">{error}</div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Primary Classification */}
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-blue-500">
            <h3 className="text-xl font-semibold mb-4">Primary Classification</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-2">Document Type</p>
                <span className={`inline-block px-4 py-2 rounded-lg text-lg font-bold ${TYPE_COLORS[result.primary_classification.document_type] || TYPE_COLORS.unknown}`}>
                  {result.primary_classification.document_type.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Purpose/Phase</p>
                <span className={`inline-block px-4 py-2 rounded-lg text-lg font-bold ${PURPOSE_COLORS[result.primary_classification.purpose] || PURPOSE_COLORS.unknown}`}>
                  {result.primary_classification.purpose.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <Info className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-600">Confidence:</span>
              <span className={`text-lg font-bold ${getConfidenceColor(result.primary_classification.confidence)}`}>
                {(result.primary_classification.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Alternative Classifications */}
          {result.alternative_classifications && result.alternative_classifications.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Alternative Classifications</h3>
              <div className="space-y-3">
                {result.alternative_classifications.map((alt, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-4">
                      <span className={`px-3 py-1 rounded text-sm font-medium ${TYPE_COLORS[alt.document_type] || TYPE_COLORS.unknown}`}>
                        {alt.document_type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className={`px-3 py-1 rounded text-sm font-medium ${PURPOSE_COLORS[alt.purpose] || PURPOSE_COLORS.unknown}`}>
                        {alt.purpose.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <span className={`font-semibold ${getConfidenceColor(alt.confidence)}`}>
                      {(alt.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted Metadata */}
          {result.extracted_metadata && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Extracted Metadata</h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.extracted_metadata.drawing_number && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600">Drawing Number</p>
                    <p className="font-semibold text-blue-900">{result.extracted_metadata.drawing_number}</p>
                  </div>
                )}
                {result.extracted_metadata.drawing_title && (
                  <div className="p-3 bg-purple-50 rounded-lg col-span-2">
                    <p className="text-xs text-purple-600">Drawing Title</p>
                    <p className="font-semibold text-purple-900">{result.extracted_metadata.drawing_title}</p>
                  </div>
                )}
                {result.extracted_metadata.revision && (
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-green-600">Revision</p>
                    <p className="font-semibold text-green-900">{result.extracted_metadata.revision}</p>
                  </div>
                )}
                {result.extracted_metadata.scale && (
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <p className="text-xs text-amber-600">Scale</p>
                    <p className="font-semibold text-amber-900">{result.extracted_metadata.scale}</p>
                  </div>
                )}
                {result.extracted_metadata.date && (
                  <div className="p-3 bg-pink-50 rounded-lg">
                    <p className="text-xs text-pink-600">Date</p>
                    <p className="font-semibold text-pink-900">{result.extracted_metadata.date}</p>
                  </div>
                )}
                {result.extracted_metadata.architect_firm && (
                  <div className="p-3 bg-indigo-50 rounded-lg col-span-2">
                    <p className="text-xs text-indigo-600">Architect Firm</p>
                    <p className="font-semibold text-indigo-900">{result.extracted_metadata.architect_firm}</p>
                  </div>
                )}
                {result.extracted_metadata.project_number && (
                  <div className="p-3 bg-cyan-50 rounded-lg">
                    <p className="text-xs text-cyan-600">Project Number</p>
                    <p className="font-semibold text-cyan-900">{result.extracted_metadata.project_number}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Quality Indicators */}
          {result.quality_indicators && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Quality Indicators</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  {result.quality_indicators.has_title_block ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                  <span className="text-gray-700">Title Block Detected</span>
                </div>
                <div className="flex items-center gap-3">
                  {result.quality_indicators.has_scale ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                  <span className="text-gray-700">Scale Information</span>
                </div>
                <div className="flex items-center gap-3">
                  {result.quality_indicators.has_north_arrow ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                  <span className="text-gray-700">North Arrow (Site Plans)</span>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Drawing Quality</p>
                  <span className={`inline-block mt-1 px-3 py-1 rounded font-medium text-sm ${
                    result.quality_indicators.drawing_quality === 'excellent' ? 'bg-green-100 text-green-800' :
                    result.quality_indicators.drawing_quality === 'good' ? 'bg-blue-100 text-blue-800' :
                    result.quality_indicators.drawing_quality === 'fair' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-orange-100 text-orange-800'
                  }`}>
                    {result.quality_indicators.drawing_quality.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Technical Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Classification ID:</strong> {result.classification_id}</p>
            <p><strong>Method:</strong> {result.classification_method}</p>
            <p><strong>Processing Time:</strong> {result.processing_time_ms}ms</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  )
}
