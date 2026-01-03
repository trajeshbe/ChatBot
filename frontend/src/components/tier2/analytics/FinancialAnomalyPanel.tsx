import { useState } from 'react'
import axios from 'axios'
import { AlertOctagon, Upload, Shield, TrendingDown, DollarSign } from 'lucide-react'

interface AnomalyDetectionResponse {
  anomalies_detected: number
  anomaly_rate: number
  anomalies: Array<{
    transaction_id: string
    amount: number
    anomaly_score: number
    severity: 'low' | 'medium' | 'high' | 'critical'
    reasons: string[]
    recommended_action: string
  }>
  patterns: string[]
  risk_summary: {
    total_flagged_amount: number
    high_risk_count: number
    suspicious_patterns: string[]
  }
}

const SEVERITY_COLORS = {
  low: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-500' },
  medium: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-500' },
  high: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-500' },
  critical: { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-500' },
}

export default function FinancialAnomalyPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnomalyDetectionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload a CSV file with transaction data')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post<AnomalyDetectionResponse>(
        'http://localhost:8000/api/v1/modules/financial-anomaly/detect',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Anomaly detection failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <AlertOctagon className="w-8 h-8 text-purple-600" />
          Financial Anomaly Detection
        </h1>
        <p className="text-gray-600 mt-2">
          Detect fraudulent transactions and suspicious financial patterns
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Transaction Data</h2>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-400 transition-colors">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-purple-600 hover:text-purple-700 font-medium">
              Click to upload
            </span>
            <span className="text-gray-600"> or drag and drop</span>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-500 mt-2">CSV file with transaction data</p>
        </div>

        {file && (
          <p className="mt-3 text-sm text-gray-700">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-blue-900 mb-2">Expected CSV Columns:</p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• transaction_id, amount, timestamp, merchant_id</li>
            <li>• customer_id, transaction_type, location (optional)</li>
          </ul>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !file}
          className="w-full mt-6 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Detecting Anomalies...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              Detect Anomalies
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="font-medium text-red-900">Error</p>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Detection Summary</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-red-600 font-medium mb-1">Anomalies Detected</p>
                <p className="text-3xl font-bold text-red-900">{result.anomalies_detected}</p>
                <p className="text-sm text-red-700 mt-1">
                  {(result.anomaly_rate * 100).toFixed(2)}% of transactions
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-orange-600 font-medium mb-1">High Risk Count</p>
                <p className="text-3xl font-bold text-orange-900">
                  {result.risk_summary.high_risk_count}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600 font-medium mb-1">Total Flagged Amount</p>
                <p className="text-3xl font-bold text-purple-900">
                  ${result.risk_summary.total_flagged_amount.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <AlertOctagon className="w-5 h-5 text-red-600" />
              Flagged Transactions ({result.anomalies.length})
            </h3>
            <div className="space-y-3">
              {result.anomalies.map((anomaly, idx) => {
                const severityColors = SEVERITY_COLORS[anomaly.severity]
                return (
                  <div key={idx} className={`p-4 rounded-lg border-l-4 ${severityColors.border} ${severityColors.bg}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-semibold text-gray-900">ID: {anomaly.transaction_id}</p>
                        <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-bold ${severityColors.text}`}>
                          {anomaly.severity.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-gray-900">
                          ${anomaly.amount.toLocaleString()}
                        </p>
                        <p className="text-sm text-gray-600">
                          Score: {anomaly.anomaly_score.toFixed(2)}
                        </p>
                      </div>
                    </div>

                    {anomaly.reasons.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-semibold text-gray-700 mb-1">Reasons:</p>
                        <ul className="space-y-1">
                          {anomaly.reasons.map((reason, i) => (
                            <li key={i} className="text-sm text-gray-700">• {reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="mt-3 p-2 bg-blue-50 rounded">
                      <p className="text-xs font-semibold text-blue-900 mb-1">Recommended Action:</p>
                      <p className="text-sm text-blue-800">{anomaly.recommended_action}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {result.risk_summary.suspicious_patterns.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Suspicious Patterns Detected</h3>
              <div className="flex flex-wrap gap-2">
                {result.risk_summary.suspicious_patterns.map((pattern, idx) => (
                  <span key={idx} className="px-4 py-2 bg-red-100 text-red-800 rounded-lg text-sm font-medium">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
