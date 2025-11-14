import { Activity, Zap, Database, Clock, CheckCircle } from 'lucide-react'

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
}

export default function PerformanceMetrics({ metrics }: PerformanceMetricsProps) {
  if (!metrics) return null

  const hasData = metrics.latency_ms !== undefined ||
                  metrics.tokens_used !== undefined ||
                  metrics.num_sources !== undefined

  if (!hasData) return null

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
    </div>
  )
}
