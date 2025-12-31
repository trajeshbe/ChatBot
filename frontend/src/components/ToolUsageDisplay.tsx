import React from 'react'
import { Wrench, CheckCircle2, XCircle, Clock } from 'lucide-react'

interface ToolUsage {
  tool_id: string
  tool_name: string
  status: 'success' | 'failure'
  latency_ms: number
  order: number
}

interface ToolUsageDisplayProps {
  tools: ToolUsage[]
}

const ToolUsageDisplay: React.FC<ToolUsageDisplayProps> = ({ tools }) => {
  if (!tools || tools.length === 0) {
    return null
  }

  return (
    <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
      <div className="flex items-center gap-2 mb-3">
        <Wrench className="w-4 h-4 text-slate-600 dark:text-slate-400" />
        <h4 className="font-semibold text-sm text-slate-700 dark:text-slate-300">
          Tools Used (in execution order)
        </h4>
      </div>

      <div className="space-y-2">
        {tools.map((tool) => (
          <div
            key={`${tool.order}-${tool.tool_id}`}
            className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
          >
            <div className="flex items-center gap-3 flex-1">
              {/* Order badge */}
              <div className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-mono text-xs font-semibold">
                {tool.order}
              </div>

              {/* Tool name and ID */}
              <div className="flex flex-col">
                <span className="font-medium text-sm text-slate-900 dark:text-slate-100">
                  {tool.tool_name}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                  {tool.tool_id}
                </span>
              </div>
            </div>

            {/* Status and timing */}
            <div className="flex items-center gap-3">
              {/* Latency */}
              <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400">
                <Clock className="w-3 h-3" />
                <span className="font-mono">{(tool.latency_ms || 0).toFixed(1)}ms</span>
              </div>

              {/* Status indicator */}
              <div className="flex items-center gap-1">
                {tool.status === 'success' ? (
                  <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="text-xs font-medium">Success</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
                    <XCircle className="w-4 h-4" />
                    <span className="text-xs font-medium">Failed</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary footer */}
      {tools.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
          <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400">
            <span>
              Total: <span className="font-semibold">{tools.length}</span> tool{tools.length !== 1 ? 's' : ''}
            </span>
            <span>
              Total time: <span className="font-mono font-semibold">
                {tools.reduce((sum, t) => sum + (t.latency_ms || 0), 0).toFixed(1)}ms
              </span>
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default ToolUsageDisplay
