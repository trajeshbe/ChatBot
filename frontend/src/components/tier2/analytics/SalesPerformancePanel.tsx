import { useState } from 'react'
import axios from 'axios'
import { TrendingUp, Upload, Target, Award, Users, DollarSign , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'

interface SalesMetrics {
  total_revenue: number
  total_units_sold: number
  average_order_value: number
  conversion_rate: number
  top_products: Array<{
    product: string
    revenue: number
    units: number
  }>
  top_salespeople: Array<{
    name: string
    revenue: number
    deals_closed: number
  }>
  regional_performance: Record<string, {
    revenue: number
    growth_rate: number
  }>
}

interface SalesPerformanceResponse {
  metrics: SalesMetrics
  period: string
  growth_rate: number
  performance_grade: 'A' | 'B' | 'C' | 'D' | 'F'
  insights: string[]
  recommendations: string[]
}

const GRADE_COLORS = {
  A: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-500' },
  B: { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-500' },
  C: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-500' },
  D: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-500' },
  F: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-500' },
}

export default function SalesPerformancePanel() {
  const [file, setFile] = useState<File | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SalesPerformanceResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload a CSV file with sales data')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('company', 'analytics')
    formData.append('usecase', 'sales_performance')

    try {
      const response = await axios.post<SalesPerformanceResponse>(
        'http://localhost:8000/api/v1/modules/sales-performance/analyze',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sales performance analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Target className="w-8 h-8 text-green-600" />
          Sales Performance Analytics
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze sales metrics, track performance, and identify growth opportunities
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
              moduleName="sales_performance"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Sales Data</h2>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-green-400 transition-colors">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-green-600 hover:text-green-700 font-medium">
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
          <p className="text-sm text-gray-500 mt-2">CSV file with sales transaction data</p>
        </div>

        {file && (
          <p className="mt-3 text-sm text-gray-700">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-blue-900 mb-2">Expected CSV Columns:</p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• transaction_id, date, product, revenue, units_sold</li>
            <li>• salesperson_name, region, customer_id (optional)</li>
          </ul>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !file}
          className="w-full mt-6 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Analyzing Performance...
            </>
          ) : (
            <>
              <TrendingUp className="w-5 h-5" />
              Analyze Sales
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
          {/* Performance Grade */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Overall Performance</h3>
            <div className={`p-6 rounded-lg border-l-4 ${GRADE_COLORS[result.performance_grade].border} ${GRADE_COLORS[result.performance_grade].bg}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium mb-1">Performance Grade</p>
                  <p className={`text-6xl font-bold ${GRADE_COLORS[result.performance_grade].text}`}>
                    {result.performance_grade}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium mb-1">Growth Rate</p>
                  <p className={`text-4xl font-bold ${result.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {result.growth_rate > 0 ? '+' : ''}{result.growth_rate.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Key Metrics</h3>
            <div className="grid md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  <p className="text-sm text-green-600 font-medium">Total Revenue</p>
                </div>
                <p className="text-2xl font-bold text-green-900">
                  ${result.metrics.total_revenue.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  <p className="text-sm text-blue-600 font-medium">Units Sold</p>
                </div>
                <p className="text-2xl font-bold text-blue-900">
                  {result.metrics.total_units_sold.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="w-5 h-5 text-purple-600" />
                  <p className="text-sm text-purple-600 font-medium">Avg Order Value</p>
                </div>
                <p className="text-2xl font-bold text-purple-900">
                  ${result.metrics.average_order_value.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                  <p className="text-sm text-orange-600 font-medium">Conversion Rate</p>
                </div>
                <p className="text-2xl font-bold text-orange-900">
                  {(result.metrics.conversion_rate * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          {/* Top Products */}
          {result.metrics.top_products && result.metrics.top_products.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Award className="w-5 h-5 text-yellow-600" />
                Top Products
              </h3>
              <div className="space-y-3">
                {result.metrics.top_products.map((product, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                        idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-gray-400' : 'bg-orange-400'
                      }`}>
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-semibold text-gray-900">{product.product}</p>
                        <p className="text-sm text-gray-600">{product.units.toLocaleString()} units</p>
                      </div>
                    </div>
                    <p className="text-xl font-bold text-green-600">
                      ${product.revenue.toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Salespeople */}
          {result.metrics.top_salespeople && result.metrics.top_salespeople.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                Top Performers
              </h3>
              <div className="space-y-3">
                {result.metrics.top_salespeople.map((person, idx) => (
                  <div key={idx} className="p-4 bg-blue-50 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-semibold text-gray-900">{person.name}</p>
                        <p className="text-sm text-gray-600">{person.deals_closed} deals closed</p>
                      </div>
                    </div>
                    <p className="text-xl font-bold text-blue-600">
                      ${person.revenue.toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insights */}
          {result.insights && result.insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
              <ul className="space-y-2">
                {result.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <span className="text-blue-600 font-bold">{idx + 1}.</span>
                    <span className="text-gray-900">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <span className="text-green-600 font-bold">✓</span>
                    <span className="text-gray-900">{rec}</span>
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
