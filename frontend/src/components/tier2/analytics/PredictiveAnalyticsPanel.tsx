import { useState } from 'react'
import axios from 'axios'
import { TrendingUp, Upload, BarChart3, LineChart , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'

interface PredictionResult {
  metric: string
  predicted_value: number
  confidence_interval: {
    lower: number
    upper: number
  }
  trend: 'increasing' | 'decreasing' | 'stable'
  factors: string[]
}

interface PredictiveAnalyticsResponse {
  predictions: PredictionResult[]
  forecast_period: string
  overall_trend: string
  key_insights: string[]
  recommendations: string[]
  model_accuracy?: number
}

export default function PredictiveAnalyticsPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [metric, setMetric] = useState('revenue')
  const [forecastPeriod, setForecastPeriod] = useState('30')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PredictiveAnalyticsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload a CSV file with historical data')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('metric', metric)
    formData.append('forecast_period', forecastPeriod)

    try {
      const response = await axios.post<PredictiveAnalyticsResponse>(
        'http://localhost:8000/api/v1/modules/predictive-analytics/forecast',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Predictive analytics failed')
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
          <TrendingUp className="w-8 h-8 text-blue-600" />
          Predictive Analytics & Forecasting
        </h1>
        <p className="text-gray-600 mt-2">
          Predict future trends and metrics using machine learning
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
              moduleName="predictive_analytics"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Historical Data</h2>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-blue-600 hover:text-blue-700 font-medium">
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
          <p className="text-sm text-gray-500 mt-2">CSV file with time-series data</p>
        </div>

        {file && (
          <p className="mt-3 text-sm text-gray-700">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        <div className="mt-6 grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Metric to Forecast
            </label>
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="revenue">Revenue</option>
              <option value="sales">Sales Volume</option>
              <option value="users">User Growth</option>
              <option value="churn">Churn Rate</option>
              <option value="costs">Operational Costs</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Forecast Period (days)
            </label>
            <select
              value={forecastPeriod}
              onChange={(e) => setForecastPeriod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="7">7 days</option>
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
              <option value="180">6 months</option>
              <option value="365">1 year</option>
            </select>
          </div>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-blue-900 mb-2">Expected CSV Format:</p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• date, metric_value (required)</li>
            <li>• Additional features: category, region, etc. (optional)</li>
          </ul>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !file}
          className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Generating Forecast...
            </>
          ) : (
            <>
              <LineChart className="w-5 h-5" />
              Generate Forecast
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
            <h3 className="text-xl font-semibold mb-4">Forecast Summary</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600 font-medium mb-1">Forecast Period</p>
                <p className="text-2xl font-bold text-blue-900">{result.forecast_period}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600 font-medium mb-1">Overall Trend</p>
                <p className="text-2xl font-bold text-green-900">{result.overall_trend}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              Predictions
            </h3>
            <div className="space-y-4">
              {result.predictions.map((pred, idx) => (
                <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-semibold text-gray-900">{pred.metric}</p>
                      <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-bold ${
                        pred.trend === 'increasing' ? 'bg-green-100 text-green-800' :
                        pred.trend === 'decreasing' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {pred.trend.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">
                      {pred.predicted_value.toLocaleString()}
                    </p>
                  </div>

                  <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                    <p className="text-xs font-semibold text-gray-700 mb-1">Confidence Interval:</p>
                    <p className="text-sm text-gray-700">
                      {pred.confidence_interval.lower.toLocaleString()} - {pred.confidence_interval.upper.toLocaleString()}
                    </p>
                  </div>

                  {pred.factors.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs font-semibold text-gray-700 mb-1">Key Factors:</p>
                      <div className="flex flex-wrap gap-2">
                        {pred.factors.map((factor, i) => (
                          <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {result.key_insights && result.key_insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
              <ul className="space-y-2">
                {result.key_insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <span className="text-blue-600 font-bold">{idx + 1}.</span>
                    <span className="text-gray-900">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

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
