import { Target, TrendingUp, Shield, CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface ClaimAnalysis {
  claim: string
  supported: boolean
  overlap_score: number
  supporting_chunks?: Array<{
    content: string
    filename: string
    overlap: number
  }>
}

interface FaithfulnessDetails {
  total_claims: number
  supported_claims: number
  claims_analysis: ClaimAnalysis[]
}

interface ChunkBreakdown {
  filename: string
  similarity: number
  semantic_score: number
  keyword_score: number
  memory_type: string
  excerpt: string
}

interface ContextRelevancyDetails {
  chunks_count: number
  avg_similarity: number
  min_similarity: number
  max_similarity: number
  chunks_breakdown: ChunkBreakdown[]
}

interface RankingDetail {
  rank: number
  filename: string
  similarity: number
  ideal_rank: number
}

interface ContextPrecisionDetails {
  is_perfectly_sorted: boolean
  total_chunks: number
  correctly_ranked: number
  ranking_details: RankingDetail[]
}

interface EvaluationMetricsProps {
  metrics?: {
    // Backend field names (from quality_metrics_service)
    quality_level?: string
    rag_score?: number
    faithfulness?: number
    answer_relevancy?: number
    context_relevancy?: number
    context_precision?: number
    // Detailed analysis
    faithfulness_details?: FaithfulnessDetails
    context_relevancy_details?: ContextRelevancyDetails
    context_precision_details?: ContextPrecisionDetails
    // Alternative field names (for compatibility)
    faithfulness_score?: number
    relevance_score?: number
    coherence_score?: number
    context_precision_score?: number
    context_relevance_score?: number
    answer_relevance_score?: number
    overall_score?: number
    // Additional evaluation metadata
    evaluation_time_ms?: number
    enabled_methods?: string[]
    // New fields for classification info
    note?: string
    classification_type?: string
    classification_confidence?: number
    num_chunks_used?: number
    num_documents_searched?: number
  }
}

export default function EvaluationMetrics({ metrics }: EvaluationMetricsProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!metrics) return null

  const hasData = metrics.quality_level !== undefined ||
                  metrics.rag_score !== undefined ||
                  metrics.relevance_score !== undefined ||
                  metrics.overall_score !== undefined

  if (!hasData) return null

  // Format score as percentage
  const formatScore = (score: number | undefined): string => {
    if (score === undefined) return 'N/A'
    return `${(score * 100).toFixed(0)}%`
  }

  // Get quality badge color based on quality level
  const getQualityColor = (level: string | undefined): { bg: string; text: string; icon: any } => {
    switch (level?.toLowerCase()) {
      case 'excellent':
        return {
          bg: 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-700',
          text: 'text-emerald-700 dark:text-emerald-300',
          icon: CheckCircle
        }
      case 'good':
        return {
          bg: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700',
          text: 'text-blue-700 dark:text-blue-300',
          icon: TrendingUp
        }
      case 'fair':
        return {
          bg: 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-700',
          text: 'text-yellow-700 dark:text-yellow-300',
          icon: AlertTriangle
        }
      case 'poor':
        return {
          bg: 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700',
          text: 'text-red-700 dark:text-red-300',
          icon: XCircle
        }
      default:
        return {
          bg: 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700',
          text: 'text-slate-700 dark:text-slate-300',
          icon: Target
        }
    }
  }

  // Get score color based on value
  const getScoreColor = (score: number | undefined): string => {
    if (score === undefined) return 'text-slate-500'
    if (score >= 0.8) return 'text-emerald-600 dark:text-emerald-400'
    if (score >= 0.6) return 'text-blue-600 dark:text-blue-400'
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const qualityColor = getQualityColor(metrics.quality_level)
  const QualityIcon = qualityColor.icon

  // Determine primary score to display
  const primaryScore = metrics.overall_score ?? metrics.rag_score
  const primaryScoreLabel = metrics.overall_score !== undefined ? 'Overall' : 'RAG'

  return (
    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1">
          <Target className="w-3 h-3 text-slate-500" />
          <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
            Evaluation Metrics
          </p>
        </div>
        {/* Toggle button for expanded view */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
        >
          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Compact view - always visible */}
      <div className="grid grid-cols-2 gap-2">
        {/* Quality Level Badge */}
        {metrics.quality_level && (
          <div className={`flex items-center gap-1.5 text-xs border px-2 py-1.5 rounded-md ${qualityColor.bg} ${qualityColor.text}`}>
            <QualityIcon className="w-3 h-3" />
            <span className="font-medium capitalize">{metrics.quality_level}</span>
          </div>
        )}

        {/* Primary Score */}
        {primaryScore !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Shield className="w-3 h-3 text-purple-500" />
            <span className="text-slate-600 dark:text-slate-400">{primaryScoreLabel}:</span>
            <span className={`font-mono font-medium ${getScoreColor(primaryScore)}`}>
              {formatScore(primaryScore)}
            </span>
          </div>
        )}
      </div>

      {/* Expanded view - detailed scores */}
      {isExpanded && (
        <div className="mt-2 space-y-1.5">
          {/* Answer Relevance */}
          {(metrics.answer_relevancy ?? metrics.answer_relevance_score ?? metrics.relevance_score) !== undefined && (
            <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded">
              <span className="text-slate-600 dark:text-slate-400">Answer Relevance</span>
              <span className={`font-mono font-medium ${getScoreColor(metrics.answer_relevancy ?? metrics.answer_relevance_score ?? metrics.relevance_score)}`}>
                {formatScore(metrics.answer_relevancy ?? metrics.answer_relevance_score ?? metrics.relevance_score)}
              </span>
            </div>
          )}

          {/* Faithfulness with Tooltip */}
          {(metrics.faithfulness ?? metrics.faithfulness_score) !== undefined && (
            <div className="relative group">
              <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded cursor-help">
                <span className="text-slate-600 dark:text-slate-400">Faithfulness</span>
                <span className={`font-mono font-medium ${getScoreColor(metrics.faithfulness ?? metrics.faithfulness_score)}`}>
                  {formatScore(metrics.faithfulness ?? metrics.faithfulness_score)}
                </span>
              </div>

              {/* Tooltip for Faithfulness */}
              {metrics.faithfulness_details && (
                <div className="hidden group-hover:block absolute z-50 left-0 mt-1 w-96 p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl">
                  <div className="text-xs space-y-2">
                    <div className="font-semibold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 pb-1">
                      Faithfulness Analysis
                    </div>
                    <div className="text-[10px] text-slate-600 dark:text-slate-400">
                      {metrics.faithfulness_details.supported_claims} of {metrics.faithfulness_details.total_claims} claims verified from context
                    </div>

                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {metrics.faithfulness_details.claims_analysis.slice(0, 5).map((claim, i) => (
                        <div key={i} className="text-[10px] border-l-2 pl-2 py-1" style={{ borderColor: claim.supported ? '#10b981' : '#ef4444' }}>
                          <div className="flex items-start gap-1">
                            <span className="mt-0.5">{claim.supported ? '✅' : '❌'}</span>
                            <div className="flex-1">
                              <div className="text-slate-700 dark:text-slate-300 font-medium mb-1">
                                "{claim.claim.slice(0, 100)}{claim.claim.length > 100 ? '...' : ''}"
                              </div>
                              {claim.supported && claim.supporting_chunks && claim.supporting_chunks.length > 0 && (
                                <div className="mt-1 space-y-1">
                                  {claim.supporting_chunks.slice(0, 1).map((chunk, j) => (
                                    <div key={j} className="bg-slate-100 dark:bg-slate-900 p-1.5 rounded text-slate-600 dark:text-slate-400">
                                      <div className="font-semibold text-blue-600 dark:text-blue-400 mb-0.5">
                                        {chunk.filename} ({(chunk.overlap * 100).toFixed(0)}% overlap)
                                      </div>
                                      <div className="italic">"{chunk.content.slice(0, 120)}..."</div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                      {metrics.faithfulness_details.claims_analysis.length > 5 && (
                        <div className="text-[10px] text-slate-500 dark:text-slate-400 italic text-center">
                          +{metrics.faithfulness_details.claims_analysis.length - 5} more claims...
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Context Precision with Tooltip */}
          {(metrics.context_precision ?? metrics.context_precision_score) !== undefined && (
            <div className="relative group">
              <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded cursor-help">
                <span className="text-slate-600 dark:text-slate-400">Context Precision</span>
                <span className={`font-mono font-medium ${getScoreColor(metrics.context_precision ?? metrics.context_precision_score)}`}>
                  {formatScore(metrics.context_precision ?? metrics.context_precision_score)}
                </span>
              </div>

              {/* Tooltip for Context Precision */}
              {metrics.context_precision_details && (
                <div className="hidden group-hover:block absolute z-50 left-0 mt-1 w-80 p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl">
                  <div className="text-xs space-y-2">
                    <div className="font-semibold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 pb-1">
                      Context Precision Analysis
                    </div>
                    <div className="text-[10px] text-slate-600 dark:text-slate-400">
                      {metrics.context_precision_details.correctly_ranked} of {metrics.context_precision_details.total_chunks} chunks correctly ranked
                      {metrics.context_precision_details.is_perfectly_sorted && " ✨ Perfect!"}
                    </div>

                    <div className="max-h-48 overflow-y-auto space-y-1">
                      {metrics.context_precision_details.ranking_details.map((detail, i) => (
                        <div key={i} className="flex items-center justify-between text-[10px] bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-slate-500">#{detail.rank}</span>
                            <span className="text-slate-700 dark:text-slate-300">{detail.filename}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`font-mono ${getScoreColor(detail.similarity)}`}>
                              {(detail.similarity * 100).toFixed(0)}%
                            </span>
                            {detail.rank !== detail.ideal_rank && (
                              <span className="text-yellow-600 dark:text-yellow-400" title="Should be ranked differently">
                                ⚠️
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Context Relevance with Tooltip */}
          {(metrics.context_relevancy ?? metrics.context_relevance_score) !== undefined && (
            <div className="relative group">
              <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded cursor-help">
                <span className="text-slate-600 dark:text-slate-400">Context Relevance</span>
                <span className={`font-mono font-medium ${getScoreColor(metrics.context_relevancy ?? metrics.context_relevance_score)}`}>
                  {formatScore(metrics.context_relevancy ?? metrics.context_relevance_score)}
                </span>
              </div>

              {/* Tooltip for Context Relevance */}
              {metrics.context_relevancy_details && (
                <div className="hidden group-hover:block absolute z-50 left-0 mt-1 w-96 p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl">
                  <div className="text-xs space-y-2">
                    <div className="font-semibold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 pb-1">
                      Context Relevance Analysis
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[10px]">
                      <div className="bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">
                        <div className="text-slate-500">Avg</div>
                        <div className="font-mono font-semibold">{(metrics.context_relevancy_details.avg_similarity * 100).toFixed(0)}%</div>
                      </div>
                      <div className="bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">
                        <div className="text-slate-500">Min</div>
                        <div className="font-mono font-semibold">{(metrics.context_relevancy_details.min_similarity * 100).toFixed(0)}%</div>
                      </div>
                      <div className="bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">
                        <div className="text-slate-500">Max</div>
                        <div className="font-mono font-semibold">{(metrics.context_relevancy_details.max_similarity * 100).toFixed(0)}%</div>
                      </div>
                    </div>

                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {metrics.context_relevancy_details.chunks_breakdown.map((chunk, i) => (
                        <div key={i} className="text-[10px] bg-slate-100 dark:bg-slate-900 p-2 rounded">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-blue-600 dark:text-blue-400">{chunk.filename}</span>
                            <span className={`font-mono ${getScoreColor(chunk.similarity)}`}>
                              {(chunk.similarity * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex gap-2 text-[9px] text-slate-500 dark:text-slate-400 mb-1">
                            <span>Semantic: {(chunk.semantic_score * 100).toFixed(0)}%</span>
                            <span>Keyword: {(chunk.keyword_score * 100).toFixed(0)}%</span>
                            <span className="capitalize">{chunk.memory_type}</span>
                          </div>
                          <div className="text-slate-600 dark:text-slate-400 italic">
                            "{chunk.excerpt}"
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Evaluation Time */}
          {metrics.evaluation_time_ms !== undefined && (
            <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800">
              <span>Evaluation Time</span>
              <span className="font-mono">{metrics.evaluation_time_ms.toFixed(0)}ms</span>
            </div>
          )}

          {/* Enabled Methods */}
          {metrics.enabled_methods && metrics.enabled_methods.length > 0 && (
            <div className="text-[10px] text-slate-500 dark:text-slate-400 pt-1">
              <span>Methods: </span>
              <span className="font-mono">{metrics.enabled_methods.join(', ')}</span>
            </div>
          )}

          {/* Classification Info */}
          {metrics.classification_type && (
            <div className="text-[10px] bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 px-2 py-1.5 rounded border border-purple-200 dark:border-purple-700">
              <div className="flex items-center justify-between">
                <span>Query Type: <span className="font-semibold capitalize">{metrics.classification_type.replace('_', ' ')}</span></span>
                {metrics.classification_confidence !== undefined && (
                  <span className="font-mono">{(metrics.classification_confidence * 100).toFixed(0)}% confidence</span>
                )}
              </div>
            </div>
          )}

          {/* Note/Context */}
          {metrics.note && (
            <div className="text-[10px] text-slate-600 dark:text-slate-400 italic bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded">
              {metrics.note}
            </div>
          )}

          {/* Chunks Used */}
          {metrics.num_chunks_used !== undefined && (
            <div className="text-[10px] text-slate-500 dark:text-slate-400">
              <span>Chunks Used: </span>
              <span className="font-mono font-semibold">{metrics.num_chunks_used}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
