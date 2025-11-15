import { Target, TrendingUp, Shield, CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface EvaluationMetricsProps {
  metrics?: {
    // Backend field names (from quality_metrics_service)
    quality_level?: string
    rag_score?: number
    faithfulness?: number
    answer_relevancy?: number
    context_relevancy?: number
    context_precision?: number
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

          {/* Faithfulness */}
          {(metrics.faithfulness ?? metrics.faithfulness_score) !== undefined && (
            <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded">
              <span className="text-slate-600 dark:text-slate-400">Faithfulness</span>
              <span className={`font-mono font-medium ${getScoreColor(metrics.faithfulness ?? metrics.faithfulness_score)}`}>
                {formatScore(metrics.faithfulness ?? metrics.faithfulness_score)}
              </span>
            </div>
          )}

          {/* Context Precision */}
          {(metrics.context_precision ?? metrics.context_precision_score) !== undefined && (
            <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded">
              <span className="text-slate-600 dark:text-slate-400">Context Precision</span>
              <span className={`font-mono font-medium ${getScoreColor(metrics.context_precision ?? metrics.context_precision_score)}`}>
                {formatScore(metrics.context_precision ?? metrics.context_precision_score)}
              </span>
            </div>
          )}

          {/* Context Relevance */}
          {(metrics.context_relevancy ?? metrics.context_relevance_score) !== undefined && (
            <div className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded">
              <span className="text-slate-600 dark:text-slate-400">Context Relevance</span>
              <span className={`font-mono font-medium ${getScoreColor(metrics.context_relevancy ?? metrics.context_relevance_score)}`}>
                {formatScore(metrics.context_relevancy ?? metrics.context_relevance_score)}
              </span>
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
        </div>
      )}
    </div>
  )
}
