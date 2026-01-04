import { useState } from 'react'
import axios from 'axios'
import { FileText, Upload, CheckCircle, XCircle, AlertTriangle, TrendingUp, Calculator , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'

interface POMatchRequest {
  po_document_id?: string
  invoice_document_id?: string
  use_document_extraction: boolean
  variance_tolerance_percent: number
  auto_approve_threshold_percent: number
  session_id?: string
}

interface Discrepancy {
  discrepancy_type: string
  description: string
  po_value?: any
  invoice_value?: any
  variance_amount?: number
  variance_percent?: number
  severity: string
  recommended_action: string
}

interface MatchResult {
  po_number: string
  invoice_number: string
  match_status: 'exact_match' | 'partial_match' | 'no_match' | 'under_review'
  match_confidence: number
  total_variance_amount: number
  total_variance_percent: number
  discrepancies: Discrepancy[]
  matched_line_items: number
  total_line_items: number
  requires_approval: boolean
}

interface POMatchResponse {
  match_id: string
  po_number: string
  invoice_number: string
  match_status: string
  match_confidence: number
  po_summary: any
  invoice_summary: any
  match_result: MatchResult
  processing_time_seconds: number
  tier_1_services_used: string[]
}

export default function ProcurementMatcherPanel() {
  const [poFile, setPoFile] = useState<File | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null)
  const [poDocId, setPoDocId] = useState<string>('')
  const [invoiceDocId, setInvoiceDocId] = useState<string>('')
  const [varianceTolerance, setVarianceTolerance] = useState(5.0)
  const [autoApproveThreshold, setAutoApproveThreshold] = useState(2.0)
  const [loading, setLoading] = useState(false)
  const [uploadingPO, setUploadingPO] = useState(false)
  const [uploadingInvoice, setUploadingInvoice] = useState(false)
  const [result, setResult] = useState<POMatchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const handlePOUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setPoFile(file)
    setUploadingPO(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    formData.append('company', 'procurement')
    formData.append('usecase', 'rfp_matching')

    try {
      const response = await axios.post('http://localhost:8000/api/v1/upload', formData)
      setPoDocId(response.data.document_id)
    } catch (err: any) {
      setError(`PO upload failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setUploadingPO(false)
    }
  }

  const handleInvoiceUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setInvoiceFile(file)
    setUploadingInvoice(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    formData.append('company', 'procurement')
    formData.append('usecase', 'rfp_matching')

    try {
      const response = await axios.post('http://localhost:8000/api/v1/upload', formData)
      setInvoiceDocId(response.data.document_id)
    } catch (err: any) {
      setError(`Invoice upload failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setUploadingInvoice(false)
    }
  }

  const handleMatch = async () => {
    if (!poDocId || !invoiceDocId) {
      setError('Please upload both PO and Invoice documents')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const requestData: POMatchRequest = {
        po_document_id: poDocId,
        invoice_document_id: invoiceDocId,
        use_document_extraction: true,
        variance_tolerance_percent: varianceTolerance,
        auto_approve_threshold_percent: autoApproveThreshold,
        session_id: sessionId
      }

      const response = await axios.post<POMatchResponse>(
        'http://localhost:8000/api/v1/modules/matcher/match',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Matching failed')
      console.error('Match error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'exact_match': return 'bg-green-100 text-green-800'
      case 'partial_match': return 'bg-yellow-100 text-yellow-800'
      case 'under_review': return 'bg-orange-100 text-orange-800'
      case 'no_match': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50'
      case 'high': return 'border-orange-500 bg-orange-50'
      case 'medium': return 'border-yellow-500 bg-yellow-50'
      case 'low': return 'border-blue-500 bg-blue-50'
      default: return 'border-gray-500 bg-gray-50'
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Calculator className="w-8 h-8 text-blue-600" />
          Procurement Matcher - PO/Invoice Reconciliation
        </h1>
        <p className="text-gray-600 mt-2">
          Automated PO-to-Invoice matching with variance analysis using LLM extraction
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
              moduleName="procurement_matcher"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Upload Section */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* PO Upload */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Purchase Order
          </h2>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              onChange={handlePOUpload}
              className="hidden"
              id="po-upload"
              accept=".pdf,.docx"
            />
            <label htmlFor="po-upload" className="cursor-pointer">
              <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 mb-1">Upload Purchase Order</p>
              <p className="text-sm text-gray-500">PDF or DOCX</p>
            </label>
          </div>

          {uploadingPO && (
            <div className="mt-4 text-center text-sm text-gray-600">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
              Uploading...
            </div>
          )}

          {poFile && poDocId && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">{poFile.name}</p>
                <p className="text-xs text-green-700">Document ID: {poDocId.substring(0, 8)}...</p>
              </div>
            </div>
          )}
        </div>

        {/* Invoice Upload */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-green-600" />
            Invoice
          </h2>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-500 transition-colors">
            <input
              type="file"
              onChange={handleInvoiceUpload}
              className="hidden"
              id="invoice-upload"
              accept=".pdf,.docx"
            />
            <label htmlFor="invoice-upload" className="cursor-pointer">
              <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 mb-1">Upload Invoice</p>
              <p className="text-sm text-gray-500">PDF or DOCX</p>
            </label>
          </div>

          {uploadingInvoice && (
            <div className="mt-4 text-center text-sm text-gray-600">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600 mx-auto mb-2"></div>
              Uploading...
            </div>
          )}

          {invoiceFile && invoiceDocId && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">{invoiceFile.name}</p>
                <p className="text-xs text-green-700">Document ID: {invoiceDocId.substring(0, 8)}...</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Matching Configuration</h2>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Variance Tolerance (%)
            </label>
            <input
              type="number"
              value={varianceTolerance}
              onChange={(e) => setVarianceTolerance(parseFloat(e.target.value))}
              min="0"
              max="100"
              step="0.5"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Maximum acceptable variance for auto-approval</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Auto-Approve Threshold (%)
            </label>
            <input
              type="number"
              value={autoApproveThreshold}
              onChange={(e) => setAutoApproveThreshold(parseFloat(e.target.value))}
              min="0"
              max="100"
              step="0.5"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Threshold for automatic approval without review</p>
          </div>
        </div>

        <button
          onClick={handleMatch}
          disabled={loading || !poDocId || !invoiceDocId}
          className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Matching Documents...
            </>
          ) : (
            <>
              <TrendingUp className="w-5 h-5" />
              Match PO to Invoice
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Error</p>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Match Status */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl font-bold">Match Result</h3>
              <span className={`px-4 py-2 rounded-full font-semibold ${getStatusColor(result.match_status)}`}>
                {result.match_status.replace('_', ' ').toUpperCase()}
              </span>
            </div>

            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">PO Number</p>
                <p className="text-lg font-bold text-gray-900">{result.po_number}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Invoice Number</p>
                <p className="text-lg font-bold text-gray-900">{result.invoice_number}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Confidence</p>
                <p className="text-lg font-bold text-blue-600">{(result.match_confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Variance</p>
                <p className="text-lg font-bold text-orange-600">
                  {result.match_result.total_variance_percent.toFixed(2)}%
                </p>
              </div>
            </div>

            {/* Summary Comparison */}
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <h4 className="font-semibold text-blue-900 mb-2">Purchase Order</h4>
                <div className="space-y-1 text-sm">
                  <p><strong>Vendor:</strong> {result.po_summary.vendor}</p>
                  <p><strong>Total:</strong> {result.po_summary.currency} {result.po_summary.total_amount.toLocaleString()}</p>
                  <p><strong>Line Items:</strong> {result.po_summary.line_items}</p>
                </div>
              </div>
              <div className="border border-green-200 rounded-lg p-4 bg-green-50">
                <h4 className="font-semibold text-green-900 mb-2">Invoice</h4>
                <div className="space-y-1 text-sm">
                  <p><strong>Vendor:</strong> {result.invoice_summary.vendor}</p>
                  <p><strong>Total:</strong> {result.invoice_summary.currency} {result.invoice_summary.total_amount.toLocaleString()}</p>
                  <p><strong>Line Items:</strong> {result.invoice_summary.line_items}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Discrepancies */}
          {result.match_result.discrepancies.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                Discrepancies ({result.match_result.discrepancies.length})
              </h3>

              <div className="space-y-3">
                {result.match_result.discrepancies.map((disc, idx) => (
                  <div key={idx} className={`border-l-4 p-4 rounded ${getSeverityColor(disc.severity)}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${
                            disc.severity === 'critical' ? 'bg-red-200 text-red-800' :
                            disc.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                            disc.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-blue-200 text-blue-800'
                          }`}>
                            {disc.severity}
                          </span>
                          <span className="text-xs text-gray-600 uppercase">{disc.discrepancy_type.replace('_', ' ')}</span>
                        </div>
                        <p className="text-gray-900 font-medium mb-2">{disc.description}</p>
                        {disc.variance_percent && (
                          <p className="text-sm text-gray-700">Variance: {disc.variance_percent.toFixed(2)}%</p>
                        )}
                        <p className="text-sm text-blue-700 mt-2">
                          <strong>Recommended Action:</strong> {disc.recommended_action}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Approval Status */}
          <div className={`p-6 rounded-lg ${result.match_result.requires_approval ? 'bg-orange-50 border border-orange-200' : 'bg-green-50 border border-green-200'}`}>
            <div className="flex items-center gap-3">
              {result.match_result.requires_approval ? (
                <>
                  <AlertTriangle className="w-6 h-6 text-orange-600" />
                  <div>
                    <p className="font-semibold text-orange-900">Manual Review Required</p>
                    <p className="text-sm text-orange-700">Variance exceeds auto-approval threshold</p>
                  </div>
                </>
              ) : (
                <>
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <div>
                    <p className="font-semibold text-green-900">Approved for Payment</p>
                    <p className="text-sm text-green-700">Variance within acceptable limits</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Processing Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Processing Time:</strong> {result.processing_time_seconds.toFixed(2)}s</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
            <p className="mt-2 text-xs">
              ✓ Uses existing pgvector embeddings and LLMService for document extraction
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
