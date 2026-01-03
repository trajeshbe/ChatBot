import { useState, useRef } from 'react'
import axios from 'axios'
import { FileText, Upload, Loader2, CheckCircle, XCircle, AlertTriangle, TrendingUp, Calendar, DollarSign } from 'lucide-react'

// Types matching backend schemas
type TenderType = 'open_tender' | 'rfp' | 'rfq' | 'rfei' | 'eoi' | 'sealed_bid' | 'two_stage' | 'framework_agreement'
type BidRecommendation = 'strong_bid' | 'bid_with_conditions' | 'no_bid' | 'further_analysis_required'

interface TenderSummary {
  title?: string
  issuer?: string
  scope?: string
  reference_number?: string
}

interface TenderRequirement {
  category: string
  description: string
  mandatory: boolean
  weight?: number
}

interface EvaluationCriterion {
  name: string
  description: string
  weight: number
}

interface KeyDeadline {
  type: string
  date: string
  description?: string
}

interface BidViability {
  competitive?: boolean
  resources_available?: boolean
  alignment_score?: number
}

interface TenderAnalysisRequest {
  document_id: string
  analyze_requirements?: boolean
  analyze_evaluation_criteria?: boolean
  assess_bid_viability?: boolean
  session_id?: string
  project_id?: string
}

interface TenderAnalysisResponse {
  analysis_id: string
  document_id: string
  tender_summary: TenderSummary
  tender_type: TenderType
  requirements: TenderRequirement[]
  evaluation_criteria: EvaluationCriterion[]
  key_deadlines: KeyDeadline[]
  estimated_contract_value?: number
  contract_duration_months?: number
  bid_viability: BidViability
  compliance_requirements: string[]
  bid_recommendation: BidRecommendation
  recommendation_reason: string
  win_probability: number
  confidence_level: number
  processing_time_seconds: number
  tier_1_services_used: string[]
}

interface UploadedDocument {
  id: string
  filename: string
  file_type: string
}

const BID_RECOMMENDATION_COLORS: Record<BidRecommendation, { bg: string; text: string; border: string }> = {
  strong_bid: { bg: 'bg-green-50', text: 'text-green-900', border: 'border-green-500' },
  bid_with_conditions: { bg: 'bg-yellow-50', text: 'text-yellow-900', border: 'border-yellow-500' },
  no_bid: { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-500' },
  further_analysis_required: { bg: 'bg-blue-50', text: 'text-blue-900', border: 'border-blue-500' },
}

export default function TenderIntelligencePanel() {
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null)
  const [analyzeRequirements, setAnalyzeRequirements] = useState(true)
  const [analyzeCriteria, setAnalyzeCriteria] = useState(true)
  const [assessViability, setAssessViability] = useState(true)
  const [result, setResult] = useState<TenderAnalysisResponse | null>(null)
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

  const handleAnalyze = async () => {
    if (!uploadedDocument) return

    setIsAnalyzing(true)
    setError(null)
    setResult(null)

    const requestData: TenderAnalysisRequest = {
      document_id: uploadedDocument.id,
      analyze_requirements: analyzeRequirements,
      analyze_evaluation_criteria: analyzeCriteria,
      assess_bid_viability: assessViability,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<TenderAnalysisResponse>(
        'http://localhost:8000/api/v1/modules/tender-intelligence/analyze',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Tender analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const recommendationColors = result ? BID_RECOMMENDATION_COLORS[result.bid_recommendation] : null

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="w-8 h-8 text-indigo-600" />
          Tender Intelligence Analyzer
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze tender/RFP documents with AI-powered requirement extraction and bid recommendations
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Tender Document
        </h2>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileUpload}
          className="hidden"
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || isAnalyzing}
          className="w-full py-6 px-8 border-2 border-dashed border-indigo-300 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors flex flex-col items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
              <span className="text-indigo-700 font-medium">Uploading...</span>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-indigo-600" />
              <span className="text-indigo-700 font-medium">Click to upload tender document</span>
              <span className="text-sm text-gray-500">PDF, DOCX, TXT supported</span>
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

            {/* Analysis Options */}
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="text-sm font-semibold text-gray-700 mb-3">Analysis Options</div>
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={analyzeRequirements}
                    onChange={(e) => setAnalyzeRequirements(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-700">Extract technical, financial, and legal requirements</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={analyzeCriteria}
                    onChange={(e) => setAnalyzeCriteria(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-700">Analyze evaluation criteria and weights</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={assessViability}
                    onChange={(e) => setAssessViability(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-700">Assess bid viability and generate recommendation</span>
                </label>
              </div>
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full py-4 px-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing Tender...
                </>
              ) : (
                <>
                  <TrendingUp className="w-5 h-5" />
                  Analyze Tender
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
            <div className="font-semibold text-red-900">Analysis Failed</div>
            <div className="text-sm text-red-700">{error}</div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && recommendationColors && (
        <div className="space-y-6">
          {/* Bid Recommendation (Prominent) */}
          <div className={`rounded-lg shadow-lg p-6 border-l-4 ${recommendationColors.border} ${recommendationColors.bg}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className={`text-2xl font-bold mb-2 ${recommendationColors.text}`}>
                  {result.bid_recommendation.replace(/_/g, ' ').toUpperCase()}
                </h3>
                <p className="text-gray-700 mb-4">{result.recommendation_reason}</p>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-indigo-600" />
                    <div>
                      <p className="text-xs text-gray-600">Win Probability</p>
                      <p className="text-lg font-bold text-gray-900">{(result.win_probability * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="text-xs text-gray-600">Confidence</p>
                      <p className="text-lg font-bold text-gray-900">{(result.confidence_level * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tender Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Tender Summary</h3>
            <div className="space-y-3">
              {result.tender_summary.title && (
                <div>
                  <p className="text-sm text-gray-600">Title</p>
                  <p className="font-semibold text-gray-900">{result.tender_summary.title}</p>
                </div>
              )}
              {result.tender_summary.issuer && (
                <div>
                  <p className="text-sm text-gray-600">Issuer</p>
                  <p className="font-semibold text-gray-900">{result.tender_summary.issuer}</p>
                </div>
              )}
              {result.tender_summary.scope && (
                <div>
                  <p className="text-sm text-gray-600">Scope</p>
                  <p className="text-gray-900">{result.tender_summary.scope}</p>
                </div>
              )}
              <div className="grid md:grid-cols-3 gap-4 pt-3 border-t">
                <div>
                  <p className="text-sm text-gray-600">Tender Type</p>
                  <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                    {result.tender_type.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                {result.estimated_contract_value && (
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-green-600" />
                    <div>
                      <p className="text-sm text-gray-600">Est. Contract Value</p>
                      <p className="font-semibold text-gray-900">${result.estimated_contract_value.toLocaleString()}</p>
                    </div>
                  </div>
                )}
                {result.contract_duration_months && (
                  <div>
                    <p className="text-sm text-gray-600">Duration</p>
                    <p className="font-semibold text-gray-900">{result.contract_duration_months} months</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Requirements */}
          {result.requirements.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Requirements ({result.requirements.length})</h3>
              <div className="space-y-3">
                {result.requirements.map((req, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                            {req.category.toUpperCase()}
                          </span>
                          {req.mandatory && (
                            <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded text-xs font-bold">
                              MANDATORY
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-900">{req.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evaluation Criteria */}
          {result.evaluation_criteria.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Evaluation Criteria ({result.evaluation_criteria.length})</h3>
              <div className="space-y-3">
                {result.evaluation_criteria.map((criterion, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">{criterion.name}</p>
                      <p className="text-sm text-gray-600">{criterion.description}</p>
                    </div>
                    <div className="ml-4 text-right">
                      <p className="text-2xl font-bold text-purple-600">{(criterion.weight * 100).toFixed(0)}%</p>
                      <p className="text-xs text-gray-500">Weight</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Deadlines */}
          {result.key_deadlines.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Key Deadlines ({result.key_deadlines.length})
              </h3>
              <div className="space-y-2">
                {result.key_deadlines.map((deadline, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">{deadline.type.replace('_', ' ').toUpperCase()}</p>
                      {deadline.description && <p className="text-sm text-gray-600">{deadline.description}</p>}
                    </div>
                    <p className="font-mono text-sm font-semibold text-amber-900">{deadline.date}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compliance Requirements */}
          {result.compliance_requirements.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Compliance Requirements</h3>
              <div className="flex flex-wrap gap-2">
                {result.compliance_requirements.map((req, idx) => (
                  <span key={idx} className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
                    {req}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tech Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Analysis ID:</strong> {result.analysis_id}</p>
            <p><strong>Processing Time:</strong> {result.processing_time_seconds.toFixed(2)}s</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  )
}
