import { useState } from 'react'
import axios from 'axios'
import { Settings } from 'lucide-react'
import POCConfigManager from './POCConfigManager'

interface Source {
  document_id: string
  document_name: string
  page: number | null
  score: number
  snippet: string
}

interface QueryResponse {
  answer: string
  confidence: number
  confidence_level: string
  confidence_description: string
  sources: Source[]
  pipeline_used: string
  query_type: string
  processing_time_ms: number
}

interface PipelineResult {
  pipeline: string
  answer: string
  confidence: number
  confidence_level: string
  num_sources: number
  processing_time_ms: number
}

export default function CRUMiningIntelligence() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [comparisonResults, setComparisonResults] = useState<PipelineResult[]>([])
  const [showComparison, setShowComparison] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)

  // Sample queries
  const sampleQueries = [
    "What is the estimated capex for the Gold Valley project?",
    "What are the key environmental risks?",
    "Compare iron ore grades across all drilling sites",
    "Find documents mentioning feasibility studies"
  ]

  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a query')
      return
    }

    setLoading(true)
    setError(null)
    setShowComparison(false)

    try {
      const response = await axios.post<QueryResponse>(
        'http://localhost:8000/api/v1/cru/query',
        {
          query: query,
          top_k: 5
        }
      )

      setResult(response.data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process query')
      console.error('Query error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!query.trim()) {
      setError('Please enter a query')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/cru/compare-pipelines',
        {
          query: query,
          top_k: 5
        }
      )

      setComparisonResults(response.data.results)
      setShowComparison(true)
      setResult(null)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to compare pipelines')
      console.error('Comparison error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-emerald-500'
    if (confidence >= 0.75) return 'bg-blue-500'
    if (confidence >= 0.5) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getConfidenceBadgeColor = (level: string) => {
    const colors: Record<string, string> = {
      'very_high': 'bg-emerald-100 text-emerald-800',
      'high': 'bg-blue-100 text-blue-800',
      'medium': 'bg-yellow-100 text-yellow-800',
      'low': 'bg-red-100 text-red-800'
    }
    return colors[level] || 'bg-gray-100 text-gray-800'
  }

  const getPipelineBadgeColor = (pipeline: string) => {
    const colors: Record<string, string> = {
      'pgvector': 'bg-purple-100 text-purple-800',
      'elasticsearch': 'bg-orange-100 text-orange-800',
      'hybrid': 'bg-indigo-100 text-indigo-800'
    }
    return colors[pipeline] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">
              ⛏️ CRU Mining Intelligence
            </h1>
            <p className="text-slate-600">
              Multi-pipeline RAG for mining document analysis
            </p>
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
              moduleName="cru_mining"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

        {/* Pipeline badges */}
        <div className="mb-6">
          <div className="flex gap-2 mt-2">
            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
              pgvector (Semantic)
            </span>
            <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">
              Elasticsearch (Keyword)
            </span>
            <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">
              Hybrid (RRF Fusion)
            </span>
          </div>
        </div>

        {/* Query Input */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-slate-800 mb-4">
            Ask a Question
          </h2>

          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What is the estimated capex for the Gold Valley project?"
            className="w-full h-24 px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none mb-3"
          />

          {/* Sample Queries */}
          <div className="mb-4">
            <p className="text-xs font-medium text-slate-600 mb-2">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {sampleQueries.map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuery(sample)}
                  className="px-3 py-1 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleQuery}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex-1"
            >
              {loading ? '⏳ Processing...' : '🔍 Search (Auto-Route)'}
            </button>

            <button
              onClick={handleCompare}
              disabled={loading}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex-1"
            >
              {loading ? '⏳ Comparing...' : '⚖️ Compare Pipelines'}
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              ❌ {error}
            </div>
          )}
        </div>

        {/* Single Query Result */}
        {result && !showComparison && (
          <div className="space-y-4">
            {/* Answer Card */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-xl font-semibold text-slate-800">Answer</h2>
                <div className="flex flex-col items-end gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getConfidenceBadgeColor(result.confidence_level)}`}>
                    {result.confidence_level.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPipelineBadgeColor(result.pipeline_used)}`}>
                    {result.pipeline_used}
                  </span>
                </div>
              </div>

              <div className="bg-slate-50 rounded-lg p-4 mb-4">
                <p className="text-slate-800 leading-relaxed">{result.answer}</p>
              </div>

              {/* Confidence Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-slate-600">Confidence Score</span>
                  <span className="font-semibold text-slate-800">
                    {(result.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-2 ${getConfidenceColor(result.confidence)} transition-all`}
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
                <p className="text-xs text-slate-600 mt-1">{result.confidence_description}</p>
              </div>

              {/* Metadata */}
              <div className="flex gap-4 text-sm text-slate-600 border-t border-slate-200 pt-3">
                <div>
                  <span className="font-medium">Query Type:</span> {result.query_type}
                </div>
                <div>
                  <span className="font-medium">Processing Time:</span> {result.processing_time_ms}ms
                </div>
                <div>
                  <span className="font-medium">Sources:</span> {result.sources.length}
                </div>
              </div>
            </div>

            {/* Sources */}
            {result.sources.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="text-xl font-semibold text-slate-800 mb-4">
                  📚 Sources ({result.sources.length})
                </h2>

                <div className="space-y-3">
                  {result.sources.map((source, idx) => (
                    <div key={idx} className="border border-slate-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="font-semibold text-slate-800">
                            {idx + 1}. {source.document_name}
                          </h3>
                          {source.page && (
                            <p className="text-sm text-slate-600">Page {source.page}</p>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-semibold text-blue-600">
                            Score: {source.score.toFixed(3)}
                          </div>
                        </div>
                      </div>

                      <div className="bg-slate-50 rounded p-3 text-sm text-slate-700">
                        {source.snippet}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Pipeline Comparison Results */}
        {showComparison && comparisonResults.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-slate-800 mb-6">
              ⚖️ Pipeline Comparison Results
            </h2>

            <div className="grid grid-cols-3 gap-4">
              {comparisonResults.map((pipelineResult, idx) => (
                <div key={idx} className="border-2 border-slate-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPipelineBadgeColor(pipelineResult.pipeline)}`}>
                      {pipelineResult.pipeline}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceBadgeColor(pipelineResult.confidence_level)}`}>
                      {pipelineResult.confidence_level}
                    </span>
                  </div>

                  {/* Confidence */}
                  <div className="mb-4">
                    <div className="text-2xl font-bold text-slate-800 mb-1">
                      {(pipelineResult.confidence * 100).toFixed(0)}%
                    </div>
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-2 ${getConfidenceColor(pipelineResult.confidence)}`}
                        style={{ width: `${pipelineResult.confidence * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Answer */}
                  <div className="bg-slate-50 rounded p-3 mb-3">
                    <p className="text-sm text-slate-700 line-clamp-4">
                      {pipelineResult.answer}
                    </p>
                  </div>

                  {/* Metadata */}
                  <div className="text-xs text-slate-600 space-y-1">
                    <div>Sources: {pipelineResult.num_sources}</div>
                    <div>Time: {pipelineResult.processing_time_ms}ms</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Winner Highlight */}
            <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🏆</span>
                <div>
                  <p className="font-semibold text-emerald-800">Best Pipeline:</p>
                  <p className="text-sm text-emerald-700">
                    {comparisonResults.reduce((best, current) =>
                      current.confidence > best.confidence ? current : best
                    ).pipeline} with {(Math.max(...comparisonResults.map(r => r.confidence)) * 100).toFixed(0)}% confidence
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!result && !showComparison && !loading && (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="text-6xl mb-4">⛏️</div>
            <h3 className="text-xl font-semibold text-slate-800 mb-2">
              Ready to explore mining documents
            </h3>
            <p className="text-slate-600 mb-4">
              Ask questions about mining projects, feasibility studies, geological surveys, and more
            </p>
            <div className="text-sm text-slate-500">
              <p className="mb-1"><strong>Semantic queries:</strong> "What are the key environmental risks?"</p>
              <p className="mb-1"><strong>Keyword queries:</strong> "Find Gold Valley documents"</p>
              <p><strong>Hybrid queries:</strong> "Capex for Gold Valley 2024"</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
