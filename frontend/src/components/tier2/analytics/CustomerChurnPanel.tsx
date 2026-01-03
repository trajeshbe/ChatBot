import { useState } from 'react'
import axios from 'axios'
import { UserX, Upload, AlertTriangle, TrendingUp, Users, Calendar } from 'lucide-react'

interface ChurnData {
  customer_id: string
  tenure_months?: number
  monthly_charges?: number
  total_charges?: number
  contract_type?: string
  payment_method?: string
  internet_service?: string
  support_tickets?: number
  recent_activity_days?: number
}

interface ChurnPrediction {
  customer_id: string
  churn_probability: number
  churn_risk_level: 'low' | 'medium' | 'high' | 'critical'
  risk_factors: string[]
  retention_recommendations: string[]
}

interface ChurnAnalysisResponse {
  predictions: ChurnPrediction[]
  overall_churn_rate: number
  high_risk_customers: number
  key_risk_factors: string[]
  retention_strategies: string[]
  model_accuracy?: number
}

const RISK_COLORS = {
  low: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-500' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-500' },
  high: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-500' },
  critical: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-500' },
}

export default function CustomerChurnPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ChurnAnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload a CSV file with customer data')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post<ChurnAnalysisResponse>(
        'http://localhost:8000/api/v1/modules/customer-churn/analyze',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Customer churn analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <UserX className="w-8 h-8 text-red-600" />
          Customer Churn Prediction
        </h1>
        <p className="text-gray-600 mt-2">
          Predict customer churn probability and identify retention strategies
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Customer Data</h2>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-red-400 transition-colors">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-red-600 hover:text-red-700 font-medium">
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
          <p className="text-sm text-gray-500 mt-2">CSV file with customer data</p>
        </div>

        {file && (
          <p className="mt-3 text-sm text-gray-700">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-blue-900 mb-2">Expected CSV Columns:</p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• customer_id, tenure_months, monthly_charges, total_charges</li>
            <li>• contract_type, payment_method, internet_service</li>
            <li>• support_tickets, recent_activity_days (optional)</li>
          </ul>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !file}
          className="w-full mt-6 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Analyzing Churn Risk...
            </>
          ) : (
            <>
              <UserX className="w-5 h-5" />
              Predict Churn
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="font-medium text-red-900">Error</p>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Overall Metrics */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Overall Metrics</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-red-600 font-medium mb-1">Predicted Churn Rate</p>
                <p className="text-3xl font-bold text-red-900">
                  {(result.overall_churn_rate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-orange-600 font-medium mb-1">High Risk Customers</p>
                <p className="text-3xl font-bold text-orange-900">{result.high_risk_customers}</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600 font-medium mb-1">Total Analyzed</p>
                <p className="text-3xl font-bold text-blue-900">{result.predictions.length}</p>
              </div>
            </div>
          </div>

          {/* High Risk Customers */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              High Risk Customers
            </h3>
            <div className="space-y-3">
              {result.predictions
                .filter(p => p.churn_risk_level === 'high' || p.churn_risk_level === 'critical')
                .slice(0, 10)
                .map((pred, idx) => {
                  const riskColors = RISK_COLORS[pred.churn_risk_level]
                  return (
                    <div key={idx} className={`p-4 rounded-lg border-l-4 ${riskColors.border} ${riskColors.bg}`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold text-gray-900">{pred.customer_id}</p>
                          <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-bold ${riskColors.text}`}>
                            {pred.churn_risk_level.toUpperCase()} RISK
                          </span>
                        </div>
                        <p className="text-2xl font-bold text-gray-900">
                          {(pred.churn_probability * 100).toFixed(0)}%
                        </p>
                      </div>

                      {pred.risk_factors.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Risk Factors:</p>
                          <ul className="space-y-1">
                            {pred.risk_factors.map((factor, i) => (
                              <li key={i} className="text-sm text-gray-700">• {factor}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {pred.retention_recommendations.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Retention Strategies:</p>
                          <ul className="space-y-1">
                            {pred.retention_recommendations.map((rec, i) => (
                              <li key={i} className="text-sm text-green-700">✓ {rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )
                })}
            </div>
          </div>

          {/* Key Risk Factors */}
          {result.key_risk_factors && result.key_risk_factors.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Key Risk Factors Across All Customers</h3>
              <div className="flex flex-wrap gap-2">
                {result.key_risk_factors.map((factor, idx) => (
                  <span key={idx} className="px-4 py-2 bg-red-100 text-red-800 rounded-lg text-sm font-medium">
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Retention Strategies */}
          {result.retention_strategies && result.retention_strategies.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Recommended Retention Strategies
              </h3>
              <ul className="space-y-2">
                {result.retention_strategies.map((strategy, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <span className="text-green-600 font-bold">{idx + 1}.</span>
                    <span className="text-gray-900">{strategy}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
