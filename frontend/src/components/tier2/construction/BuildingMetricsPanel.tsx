import { useState } from 'react'
import axios from 'axios'
import { Building, Upload, AlertTriangle , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import FileUpload from '../../FileUpload'
import ExportWizardButton from '../../ExportWizardButton'

interface BuildingMetricsPanelResponse {
  results: any
  insights: string[]
  recommendations?: string[]
}

export default function BuildingMetricsPanel() {
  const [showConfig, setShowConfig] = useState(false)
  const [textInput, setTextInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BuildingMetricsPanelResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!textInput.trim()) {
      setError('Please enter a query or analysis request')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post<BuildingMetricsPanelResponse>(
        'http://localhost:8000/api/v1/modules/construction/analyze',
        { text: textInput },
        { headers: { 'Content-Type': 'application/json' } }
      )
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Building className="w-8 h-8 text-orange-600" />
          Building Metrics
        </h1>
        <p className="text-gray-600 mt-2">Construction project metrics extraction and analysis</p>
      </div>
          </div>
          <div className="flex gap-2">
            <ExportWizardButton
              moduleCode="construction"
              moduleName="Building Metrics"
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
              moduleName="building_metrics"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* File Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">📋 Upload Building Metrics Data</h2>
        <p className="text-sm text-gray-600 mb-4">
          Upload construction project documents, metrics reports, or building data for analysis.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'construction',
            usecase: 'building_metrics'
          }}
        />
      </div>

      {/* Query Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">💬 Or Enter Query</h2>

        <textarea
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Enter your query or analysis request..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 mb-4"
        />

        <button
          onClick={handleSubmit}
          disabled={loading || !textInput.trim()}
          className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Processing...
            </>
          ) : (
            <>
              <Building className="w-5 h-5" />
              Analyze
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">Error</p>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Results</h3>
            <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>

          {result.insights && result.insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Insights</h3>
              <ul className="space-y-2">
                {result.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                    <span className="text-orange-600 font-bold">{idx + 1}.</span>
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
