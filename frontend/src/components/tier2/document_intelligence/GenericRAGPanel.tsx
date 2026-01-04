import { useState } from 'react'
import axios from 'axios'
import { Search, FileText, Sparkles, TrendingUp, Clock, Settings, CheckCircle } from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import FileUpload from '../../FileUpload'
import ExportWizardButton from '../../ExportWizardButton'

type RetrievalStrategy = 'semantic' | 'keyword' | 'hybrid' | 'rerank'
type ResponseStyle = 'concise' | 'detailed' | 'bullet_points' | 'technical' | 'conversational'

interface SourceChunk {
  chunk_id: string
  document_id: string
  document_name: string
  content: string
  page_number?: number
  similarity_score: number
  rerank_score?: number
  relevance_explanation?: string
}

interface RAGQueryResponse {
  query_id: string
  answer: string
  response_style: ResponseStyle
  sources: SourceChunk[]
  num_sources_retrieved: number
  num_sources_used: number
  confidence_score: number
  quality_indicators: Record<string, any>
  retrieval_time_ms: number
  llm_time_ms: number
  total_time_ms: number
  cached_response: boolean
  tier_1_services_used: string[]
}

export default function GenericRAGPanel() {
  const [query, setQuery] = useState('')
  const [showConfig, setShowConfig] = useState(false)
  const [retrievalStrategy, setRetrievalStrategy] = useState<RetrievalStrategy>('hybrid')
  const [responseStyle, setResponseStyle] = useState<ResponseStyle>('detailed')
  const [topK, setTopK] = useState(5)
  const [temperature, setTemperature] = useState(0.3)

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RAGQueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('chat_session_id') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a question')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const requestData = {
        query: query.trim(),
        top_k: topK,
        temperature: temperature,
        response_style: responseStyle,
        session_id: sessionId,
        configuration: {
          retrieval_strategy: retrievalStrategy,
          top_k: topK,
          temperature: temperature,
          response_style: responseStyle,
          collection_name: 'default',
          document_ids: [],
          session_id: sessionId
        }
      }

      const response = await axios.post<RAGQueryResponse>(
        'http://localhost:8000/api/v1/modules/generic-rag/query',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'RAG query failed')
    } finally {
      setLoading(false)
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600 bg-green-50'
    if (score >= 0.75) return 'text-blue-600 bg-blue-50'
    if (score >= 0.5) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-8 h-8 text-purple-600" />
              Generic RAG
            </h1>
            <p className="text-gray-600 mt-2">
              Configurable Retrieval-Augmented Generation for any document collection
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <ExportWizardButton
            moduleCode="generic-rag"
            moduleName="Generic RAG"
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
            moduleName="generic_rag"
            onClose={() => setShowConfig(false)}
          />
        </div>
      )}

      {/* Document Upload Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          📚 Upload Documents
        </h3>
        <p className="text-sm text-slate-600 mb-4">
          Upload any documents for intelligent search and retrieval.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'document_intelligence',
            usecase: 'generic_rag'
          }}
        />
      </div>

      {/* Query Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6 space-y-6">
        <h2 className="text-xl font-semibold">Ask a Question</h2>

        {/* Query Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Question
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What would you like to know about your documents?"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
            rows={3}
          />
        </div>

        {/* Configuration Options */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Retrieval Strategy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Retrieval Strategy
            </label>
            <select
              value={retrievalStrategy}
              onChange={(e) => setRetrievalStrategy(e.target.value as RetrievalStrategy)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="semantic">Semantic (Vector Search)</option>
              <option value="keyword">Keyword (BM25)</option>
              <option value="hybrid">Hybrid (Combined)</option>
              <option value="rerank">Rerank (Best Quality)</option>
            </select>
          </div>

          {/* Response Style */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Response Style
            </label>
            <select
              value={responseStyle}
              onChange={(e) => setResponseStyle(e.target.value as ResponseStyle)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="concise">Concise</option>
              <option value="detailed">Detailed</option>
              <option value="bullet_points">Bullet Points</option>
              <option value="technical">Technical</option>
              <option value="conversational">Conversational</option>
            </select>
          </div>

          {/* Top K */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Top K Sources: {topK}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          onClick={handleQuery}
          disabled={loading || !query.trim()}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Querying Documents...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Ask Question
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
          {/* Answer Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-semibold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                Answer
              </h3>
              <div className="flex items-center gap-3">
                {result.cached_response && (
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Cached
                  </span>
                )}
                <span className={`px-4 py-2 rounded-lg font-bold ${getConfidenceColor(result.confidence_score)}`}>
                  {(result.confidence_score * 100).toFixed(0)}% Confident
                </span>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 mb-4">
              <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">
                {result.answer}
              </p>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-4 gap-3 p-3 bg-gray-50 rounded-lg text-sm">
              <div className="text-center">
                <p className="text-xs text-gray-600">Retrieval</p>
                <p className="text-lg font-bold text-blue-600">{result.retrieval_time_ms.toFixed(0)}ms</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600">LLM Generation</p>
                <p className="text-lg font-bold text-green-600">{result.llm_time_ms.toFixed(0)}ms</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600">Total Time</p>
                <p className="text-lg font-bold text-purple-600">{result.total_time_ms.toFixed(0)}ms</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600">Sources Used</p>
                <p className="text-lg font-bold text-gray-900">{result.num_sources_used}/{result.num_sources_retrieved}</p>
              </div>
            </div>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Sources ({result.sources.length})
              </h3>

              <div className="space-y-3">
                {result.sources.map((source, idx) => (
                  <div key={source.chunk_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900">
                          {idx + 1}. {source.document_name}
                        </h4>
                        {source.page_number && (
                          <p className="text-sm text-gray-600">Page {source.page_number}</p>
                        )}
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-sm font-semibold text-blue-600">
                          {(source.similarity_score * 100).toFixed(0)}% Match
                        </div>
                        {source.rerank_score && (
                          <div className="text-xs text-purple-600">
                            Rerank: {(source.rerank_score * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 mb-2">
                      {source.content}
                    </div>

                    {source.relevance_explanation && (
                      <div className="text-xs text-gray-600 italic">
                        Why relevant: {source.relevance_explanation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quality Indicators */}
          {Object.keys(result.quality_indicators).length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Quality Indicators
              </h3>
              <div className="grid md:grid-cols-3 gap-4">
                {Object.entries(result.quality_indicators).map(([key, value]) => (
                  <div key={key} className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <p className="text-lg font-bold text-gray-900">
                      {typeof value === 'number' ? value.toFixed(2) : String(value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tech Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4" />
              <p><strong>Query ID:</strong> {result.query_id}</p>
            </div>
            <p><strong>Response Style:</strong> {result.response_style}</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">
            Ready to Query Your Documents
          </h3>
          <p className="text-gray-600">
            Ask questions and get intelligent answers with source citations
          </p>
        </div>
      )}
    </div>
  )
}
