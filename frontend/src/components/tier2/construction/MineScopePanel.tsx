import { useState, useRef } from 'react'
import axios from 'axios'
import { Mountain, Upload, Loader2, CheckCircle, XCircle, AlertTriangle, TrendingUp, FileText } from 'lucide-react'

// Types matching backend schemas
type MineScopeType = 'exploration' | 'development' | 'production' | 'reclamation' | 'feasibility_study' | 'environmental_assessment' | 'safety_plan' | 'equipment_specification' | 'operational_plan' | 'unknown'
type MiningSector = 'coal' | 'gold' | 'iron_ore' | 'copper' | 'lithium' | 'rare_earth' | 'nickel' | 'zinc' | 'bauxite' | 'diamond' | 'unknown'
type MiningMethod = 'underground' | 'open_pit' | 'mountaintop_removal' | 'strip_mining' | 'placer' | 'dredging' | 'in_situ_leaching' | 'unknown'

interface ScopeRequirement {
  requirement_id: string
  category: string
  description: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  mandatory: boolean
}

interface ExtractedMetrics {
  production_target?: number
  production_unit?: string
  reserves_estimated?: number
  equipment_count?: number
  workforce_size?: number
  estimated_cost?: number
  timeline_months?: number
}

interface IdentifiedRisk {
  risk_id: string
  category: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  likelihood: 'very_likely' | 'likely' | 'possible' | 'unlikely'
  mitigation_strategy?: string
}

interface ComplianceRequirement {
  requirement_id: string
  regulation: string
  description: string
  deadline?: string
  status?: string
}

interface MineScopeAnalysisRequest {
  document_id: string
  extract_requirements?: boolean
  extract_metrics?: boolean
  identify_risks?: boolean
  extract_compliance?: boolean
  classify_scope_type?: boolean
  identify_sector?: boolean
  identify_mining_method?: boolean
  use_vision?: boolean
  min_confidence?: number
  session_id?: string
}

interface MineScopeAnalysisResponse {
  analysis_id: string
  document_id: string
  scope_type?: MineScopeType
  mining_sector?: MiningSector
  mining_method?: MiningMethod
  classification_confidence?: number
  requirements: ScopeRequirement[]
  extracted_metrics?: ExtractedMetrics
  identified_risks: IdentifiedRisk[]
  compliance_requirements: ComplianceRequirement[]
  executive_summary?: string
  key_findings: string[]
  processing_time_seconds: number
  tier_1_services_used: string[]
}

interface UploadedDocument {
  id: string
  filename: string
  file_type: string
}

const PRIORITY_COLORS = {
  critical: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-500' },
  high: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-500' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-500' },
  low: { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-500' },
}

const SEVERITY_COLORS = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
}

export default function MineScopePanel() {
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null)
  const [extractRequirements, setExtractRequirements] = useState(true)
  const [extractMetrics, setExtractMetrics] = useState(true)
  const [identifyRisks, setIdentifyRisks] = useState(true)
  const [extractCompliance, setExtractCompliance] = useState(true)
  const [classifyScope, setClassifyScope] = useState(true)
  const [useVision, setUseVision] = useState(true)
  const [result, setResult] = useState<MineScopeAnalysisResponse | null>(null)
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

    const requestData: MineScopeAnalysisRequest = {
      document_id: uploadedDocument.id,
      extract_requirements: extractRequirements,
      extract_metrics: extractMetrics,
      identify_risks: identifyRisks,
      extract_compliance: extractCompliance,
      classify_scope_type: classifyScope,
      identify_sector: classifyScope,
      identify_mining_method: classifyScope,
      use_vision: useVision,
      min_confidence: 0.7,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<MineScopeAnalysisResponse>(
        'http://localhost:8000/api/v1/modules/mine-scope/analyze',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Mining scope analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Mountain className="w-8 h-8 text-amber-600" />
          MineScope - Mining Intelligence & CRU Analysis
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze mining scope documents for requirements, metrics, risks, and regulatory compliance
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload Mining Scope Document
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
          className="w-full py-6 px-8 border-2 border-dashed border-amber-300 rounded-lg hover:border-amber-500 hover:bg-amber-50 transition-colors flex flex-col items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-12 h-12 text-amber-600 animate-spin" />
              <span className="text-amber-700 font-medium">Uploading...</span>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-amber-600" />
              <span className="text-amber-700 font-medium">Click to upload mining scope document</span>
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
              <div className="grid md:grid-cols-2 gap-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={extractRequirements}
                    onChange={(e) => setExtractRequirements(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">Extract scope requirements</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={extractMetrics}
                    onChange={(e) => setExtractMetrics(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">Extract quantitative metrics</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={identifyRisks}
                    onChange={(e) => setIdentifyRisks(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">Identify risks</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={extractCompliance}
                    onChange={(e) => setExtractCompliance(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">Extract compliance requirements</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={classifyScope}
                    onChange={(e) => setClassifyScope(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">Classify scope type & sector</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useVision}
                    onChange={(e) => setUseVision(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">Use AI vision for diagrams</span>
                </label>
              </div>
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="w-full py-4 px-6 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing Mining Scope...
                </>
              ) : (
                <>
                  <Mountain className="w-5 h-5" />
                  Analyze Mining Scope
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
      {result && (
        <div className="space-y-6">
          {/* Classification */}
          {(result.scope_type || result.mining_sector || result.mining_method) && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Scope Classification</h3>
              <div className="grid md:grid-cols-3 gap-4">
                {result.scope_type && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600 mb-1">Scope Type</p>
                    <p className="font-bold text-blue-900">{result.scope_type.replace('_', ' ').toUpperCase()}</p>
                  </div>
                )}
                {result.mining_sector && (
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <p className="text-xs text-amber-600 mb-1">Mining Sector</p>
                    <p className="font-bold text-amber-900">{result.mining_sector.replace('_', ' ').toUpperCase()}</p>
                  </div>
                )}
                {result.mining_method && (
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-green-600 mb-1">Mining Method</p>
                    <p className="font-bold text-green-900">{result.mining_method.replace('_', ' ').toUpperCase()}</p>
                  </div>
                )}
              </div>
              {result.classification_confidence && (
                <p className="text-sm text-gray-600 mt-3">
                  Classification confidence: {(result.classification_confidence * 100).toFixed(0)}%
                </p>
              )}
            </div>
          )}

          {/* Executive Summary */}
          {result.executive_summary && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Executive Summary
              </h3>
              <p className="text-gray-700 leading-relaxed">{result.executive_summary}</p>
            </div>
          )}

          {/* Extracted Metrics */}
          {result.extracted_metrics && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Extracted Metrics</h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.extracted_metrics.production_target && (
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-xs text-purple-600">Production Target</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {result.extracted_metrics.production_target.toLocaleString()}
                      {result.extracted_metrics.production_unit && ` ${result.extracted_metrics.production_unit}`}
                    </p>
                  </div>
                )}
                {result.extracted_metrics.reserves_estimated && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600">Estimated Reserves</p>
                    <p className="text-2xl font-bold text-blue-900">{result.extracted_metrics.reserves_estimated.toLocaleString()}</p>
                  </div>
                )}
                {result.extracted_metrics.equipment_count && (
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-green-600">Equipment Count</p>
                    <p className="text-2xl font-bold text-green-900">{result.extracted_metrics.equipment_count}</p>
                  </div>
                )}
                {result.extracted_metrics.workforce_size && (
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <p className="text-xs text-amber-600">Workforce Size</p>
                    <p className="text-2xl font-bold text-amber-900">{result.extracted_metrics.workforce_size}</p>
                  </div>
                )}
                {result.extracted_metrics.estimated_cost && (
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-xs text-red-600">Estimated Cost</p>
                    <p className="text-2xl font-bold text-red-900">${result.extracted_metrics.estimated_cost.toLocaleString()}</p>
                  </div>
                )}
                {result.extracted_metrics.timeline_months && (
                  <div className="p-3 bg-indigo-50 rounded-lg">
                    <p className="text-xs text-indigo-600">Timeline</p>
                    <p className="text-2xl font-bold text-indigo-900">{result.extracted_metrics.timeline_months} months</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Requirements */}
          {result.requirements.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Scope Requirements ({result.requirements.length})</h3>
              <div className="space-y-3">
                {result.requirements.map((req) => {
                  const colors = PRIORITY_COLORS[req.priority]
                  return (
                    <div key={req.requirement_id} className={`p-4 rounded-lg border-l-4 ${colors.border} ${colors.bg}`}>
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <span className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs font-medium mr-2">
                            {req.category}
                          </span>
                          {req.mandatory && (
                            <span className="px-2 py-0.5 bg-red-200 text-red-800 rounded text-xs font-bold">
                              MANDATORY
                            </span>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${colors.text}`}>
                          {req.priority.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900">{req.description}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Identified Risks */}
          {result.identified_risks.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                Identified Risks ({result.identified_risks.length})
              </h3>
              <div className="space-y-3">
                {result.identified_risks.map((risk) => (
                  <div key={risk.risk_id} className="p-4 bg-orange-50 rounded-lg border-l-4 border-orange-500">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <span className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-xs font-medium mr-2">
                          {risk.category}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${SEVERITY_COLORS[risk.severity]}`}>
                          {risk.severity.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-xs text-gray-600">{risk.likelihood.replace('_', ' ')}</span>
                    </div>
                    <p className="text-sm text-gray-900 mb-2">{risk.description}</p>
                    {risk.mitigation_strategy && (
                      <div className="mt-2 p-2 bg-green-50 rounded">
                        <p className="text-xs font-semibold text-green-800">Mitigation:</p>
                        <p className="text-xs text-green-700">{risk.mitigation_strategy}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compliance Requirements */}
          {result.compliance_requirements.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Compliance Requirements ({result.compliance_requirements.length})</h3>
              <div className="space-y-2">
                {result.compliance_requirements.map((comp) => (
                  <div key={comp.requirement_id} className="p-3 bg-blue-50 rounded-lg flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-semibold text-blue-900">{comp.regulation}</p>
                      <p className="text-sm text-blue-700">{comp.description}</p>
                    </div>
                    {comp.deadline && (
                      <span className="ml-3 text-xs font-medium text-blue-600 whitespace-nowrap">
                        Due: {comp.deadline}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Findings */}
          {result.key_findings.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Key Findings
              </h3>
              <ul className="space-y-2">
                {result.key_findings.map((finding, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-900">{finding}</span>
                  </li>
                ))}
              </ul>
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
