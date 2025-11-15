import { Activity, Zap, Database, Clock, CheckCircle, Hash, Target, Sliders } from 'lucide-react'

interface PerformanceMetricsProps {
  metrics?: {
    latency_ms?: number
    tokens_used?: number
    num_sources?: number
    cached?: boolean
    model_used?: string
    model_name?: string
    context_info?: string
  }
  ragSettings?: {
    top_k?: number
    similarity_threshold?: number
    min_similarity_threshold?: number
    no_relevant_docs_threshold?: number
    chunk_size?: number
    chunk_overlap?: number
    search_type?: string
    memory_type?: string
  }
}

export default function PerformanceMetrics({ metrics, ragSettings }: PerformanceMetricsProps) {
  if (!metrics) return null

  const hasData = metrics.latency_ms !== undefined ||
                  metrics.tokens_used !== undefined ||
                  metrics.num_sources !== undefined

  if (!hasData) return null

  // Format threshold as percentage
  const formatThreshold = (threshold: number | undefined): string => {
    if (threshold === undefined) return 'N/A'
    return `${(threshold * 100).toFixed(0)}%`
  }

  const formatLatency = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatTokens = (tokens: number): string => {
    if (tokens < 1000) return tokens.toString()
    return `${(tokens / 1000).toFixed(1)}K`
  }

  return (
    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
      <div className="flex items-center gap-1 mb-2">
        <Activity className="w-3 h-3 text-slate-500" />
        <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
          Performance
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {/* Latency */}
        {metrics.latency_ms !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Clock className="w-3 h-3 text-blue-500" />
            <span className="text-slate-600 dark:text-slate-400">Latency:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {formatLatency(metrics.latency_ms)}
            </span>
          </div>
        )}

        {/* Tokens Used */}
        {metrics.tokens_used !== undefined && metrics.tokens_used > 0 && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Zap className="w-3 h-3 text-yellow-500" />
            <span className="text-slate-600 dark:text-slate-400">Tokens:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {formatTokens(metrics.tokens_used)}
            </span>
          </div>
        )}

        {/* Sources Count */}
        {metrics.num_sources !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Database className="w-3 h-3 text-emerald-500" />
            <span className="text-slate-600 dark:text-slate-400">Sources:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {metrics.num_sources}
            </span>
          </div>
        )}

        {/* Cache Hit */}
        {metrics.cached && (
          <div className="flex items-center gap-1.5 text-xs bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 px-2 py-1.5 rounded-md">
            <CheckCircle className="w-3 h-3" />
            <span className="font-medium">Cached</span>
          </div>
        )}
      </div>

      {/* Model Used */}
      {(metrics.model_name || metrics.model_used) && (
        <div className="mt-2 text-[10px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
          <span>Model:</span>
          <span className="font-mono">
            {metrics.model_name || metrics.model_used}
          </span>
        </div>
      )}

      {/* RAG Settings */}
      {ragSettings && (
        <div className="mt-3 pt-2 border-t border-slate-200 dark:border-slate-700">
          <p className="text-[10px] font-semibold mb-2 text-slate-600 dark:text-slate-400">
            RAG Configuration
          </p>
          <div className="grid grid-cols-2 gap-2">
            {/* Top K */}
            {ragSettings.top_k !== undefined && (
              <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
                <Hash className="w-3 h-3 text-indigo-500" />
                <span className="text-slate-600 dark:text-slate-400">Top K:</span>
                <span className="font-mono font-medium text-slate-900 dark:text-white">
                  {ragSettings.top_k}
                </span>
              </div>
            )}

            {/* Similarity Threshold */}
            {ragSettings.similarity_threshold !== undefined && (
              <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
                <Target className="w-3 h-3 text-purple-500" />
                <span className="text-slate-600 dark:text-slate-400">Similarity:</span>
                <span className="font-mono font-medium text-slate-900 dark:text-white">
                  {formatThreshold(ragSettings.similarity_threshold)}
                </span>
              </div>
            )}

            {/* Min Similarity Threshold */}
            {ragSettings.min_similarity_threshold !== undefined && (
              <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
                <Target className="w-3 h-3 text-amber-500" />
                <span className="text-slate-600 dark:text-slate-400">Min Sim:</span>
                <span className="font-mono font-medium text-slate-900 dark:text-white">
                  {formatThreshold(ragSettings.min_similarity_threshold)}
                </span>
              </div>
            )}

            {/* No Relevant Docs Threshold */}
            {ragSettings.no_relevant_docs_threshold !== undefined && (
              <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
                <Target className="w-3 h-3 text-orange-500" />
                <span className="text-slate-600 dark:text-slate-400">Relevance:</span>
                <span className="font-mono font-medium text-slate-900 dark:text-white">
                  {formatThreshold(ragSettings.no_relevant_docs_threshold)}
                </span>
              </div>
            )}

            {/* Chunk Size */}
            {ragSettings.chunk_size !== undefined && (
              <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
                <Sliders className="w-3 h-3 text-cyan-500" />
                <span className="text-slate-600 dark:text-slate-400">Chunk:</span>
                <span className="font-mono font-medium text-slate-900 dark:text-white">
                  {ragSettings.chunk_size}
                </span>
              </div>
            )}

            {/* Chunk Overlap */}
            {ragSettings.chunk_overlap !== undefined && (
              <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
                <Sliders className="w-3 h-3 text-teal-500" />
                <span className="text-slate-600 dark:text-slate-400">Overlap:</span>
                <span className="font-mono font-medium text-slate-900 dark:text-white">
                  {ragSettings.chunk_overlap}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
