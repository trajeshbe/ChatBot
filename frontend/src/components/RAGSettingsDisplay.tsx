import { Settings, Sliders, Target, Hash } from 'lucide-react'

interface RAGSettingsDisplayProps {
  settings?: {
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

export default function RAGSettingsDisplay({ settings }: RAGSettingsDisplayProps) {
  if (!settings) return null

  const hasData = settings.top_k !== undefined ||
                  settings.similarity_threshold !== undefined ||
                  settings.chunk_size !== undefined

  if (!hasData) return null

  // Format threshold as percentage
  const formatThreshold = (threshold: number | undefined): string => {
    if (threshold === undefined) return 'N/A'
    return `${(threshold * 100).toFixed(0)}%`
  }

  return (
    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
      <div className="flex items-center gap-1 mb-2">
        <Settings className="w-3 h-3 text-slate-500" />
        <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
          RAG Settings
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {/* Top K Results */}
        {settings.top_k !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Hash className="w-3 h-3 text-indigo-500" />
            <span className="text-slate-600 dark:text-slate-400">Top K:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {settings.top_k}
            </span>
          </div>
        )}

        {/* Similarity Threshold */}
        {settings.similarity_threshold !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Target className="w-3 h-3 text-purple-500" />
            <span className="text-slate-600 dark:text-slate-400">Similarity:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {formatThreshold(settings.similarity_threshold)}
            </span>
          </div>
        )}

        {/* Min Similarity Threshold */}
        {settings.min_similarity_threshold !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Target className="w-3 h-3 text-amber-500" />
            <span className="text-slate-600 dark:text-slate-400">Min Sim:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {formatThreshold(settings.min_similarity_threshold)}
            </span>
          </div>
        )}

        {/* No Relevant Docs Threshold */}
        {settings.no_relevant_docs_threshold !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Target className="w-3 h-3 text-orange-500" />
            <span className="text-slate-600 dark:text-slate-400">Relevance:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {formatThreshold(settings.no_relevant_docs_threshold)}
            </span>
          </div>
        )}

        {/* Chunk Size */}
        {settings.chunk_size !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Sliders className="w-3 h-3 text-cyan-500" />
            <span className="text-slate-600 dark:text-slate-400">Chunk:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {settings.chunk_size}
            </span>
          </div>
        )}

        {/* Chunk Overlap */}
        {settings.chunk_overlap !== undefined && (
          <div className="flex items-center gap-1.5 text-xs bg-slate-50 dark:bg-slate-900 px-2 py-1.5 rounded-md">
            <Sliders className="w-3 h-3 text-teal-500" />
            <span className="text-slate-600 dark:text-slate-400">Overlap:</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">
              {settings.chunk_overlap}
            </span>
          </div>
        )}
      </div>

      {/* Search Type and Memory Type */}
      {(settings.search_type || settings.memory_type) && (
        <div className="mt-2 text-[10px] text-slate-500 dark:text-slate-400 flex items-center gap-2">
          {settings.search_type && (
            <span>
              Search: <span className="font-mono">{settings.search_type}</span>
            </span>
          )}
          {settings.memory_type && (
            <span>
              Memory: <span className="font-mono">{settings.memory_type}</span>
            </span>
          )}
        </div>
      )}
    </div>
  )
}
