import { useState } from 'react'
import axios from 'axios'
import { Shield, Upload, AlertTriangle , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'

interface InsuranceRiskPanelResponse {
  results: any
  insights: string[]
  recommendations?: string[]
}

export default function InsuranceRiskPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [textInput, setTextInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<InsuranceRiskPanelResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleSubmit = async () => {
    if (!file && !textInput.trim()) {
      setError('Please upload a file or enter text')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      if (file) {
        formData.append('file', file)
      }
      if (textInput.trim()) {
        formData.append('text', textInput)
      }

      const response = await axios.post<InsuranceRiskPanelResponse>(
        'http://localhost:8000/api/v1/modules/insurance-risk/analyze',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
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
          <Shield className="w-8 h-8 text-orange-600" />
          Insurance Risk Assessment
        </h1>
        <p className="text-gray-600 mt-2">Assess insurance risk and pricing</p>
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
              moduleName="insurance_risk"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Data or Enter Text</h2>

        {/* File Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-orange-400 transition-colors mb-4">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-orange-600 hover:text-orange-700 font-medium">
              Click to upload
            </span>
            <span className="text-gray-600"> or drag and drop</span>
            <input
              type="file"
              accept=".csv,.pdf,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-500 mt-2">PDF, CSV, or TXT files</p>
        </div>

        {file && (
          <p className="mt-3 text-sm text-gray-700 mb-4">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        {/* Text Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Or enter text directly
          </label>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Enter your data or query here..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
          />
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={loading || (!file && !textInput.trim())}
          className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Processing...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
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
