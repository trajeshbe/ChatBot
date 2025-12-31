import { Settings, Sliders, Target, Hash, Search, Brain } from 'lucide-react'
import { motion } from 'framer-motion'

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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mt-3 pt-3 border-t border-gray-200 dark:border-slate-700"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg">
          <Settings className="w-3.5 h-3.5 text-white" />
        </div>
        <p className="text-xs font-bold gradient-text-primary">
          RAG Configuration
        </p>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-2 gap-2">
        {/* Top K Results */}
        {settings.top_k !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="glass-card-light p-2 rounded-lg hover-glow-primary smooth-transition"
          >
            <div className="flex items-center gap-1.5">
              <div className="p-1 bg-gradient-to-br from-primary-500 to-secondary-500 rounded">
                <Hash className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-500 dark:text-gray-400">Top K</p>
                <p className="text-sm font-bold text-primary-600 dark:text-primary-400">
                  {settings.top_k}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Similarity Threshold */}
        {settings.similarity_threshold !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 }}
            className="glass-card-light p-2 rounded-lg hover-glow-primary smooth-transition"
          >
            <div className="flex items-center gap-1.5">
              <div className="p-1 bg-gradient-to-br from-secondary-500 to-primary-500 rounded">
                <Target className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-500 dark:text-gray-400">Similarity</p>
                <p className="text-sm font-bold text-secondary-600 dark:text-secondary-400">
                  {formatThreshold(settings.similarity_threshold)}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Min Similarity Threshold */}
        {settings.min_similarity_threshold !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="glass-card-light p-2 rounded-lg hover-glow-primary smooth-transition"
          >
            <div className="flex items-center gap-1.5">
              <div className="p-1 bg-gradient-to-br from-amber-500 to-orange-500 rounded">
                <Target className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-500 dark:text-gray-400">Min Sim</p>
                <p className="text-sm font-bold text-amber-600 dark:text-amber-400">
                  {formatThreshold(settings.min_similarity_threshold)}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* No Relevant Docs Threshold */}
        {settings.no_relevant_docs_threshold !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.25 }}
            className="glass-card-light p-2 rounded-lg hover-glow-primary smooth-transition"
          >
            <div className="flex items-center gap-1.5">
              <div className="p-1 bg-gradient-to-br from-orange-500 to-red-500 rounded">
                <Target className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-500 dark:text-gray-400">Relevance</p>
                <p className="text-sm font-bold text-orange-600 dark:text-orange-400">
                  {formatThreshold(settings.no_relevant_docs_threshold)}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Chunk Size */}
        {settings.chunk_size !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="glass-card-light p-2 rounded-lg hover-glow-primary smooth-transition"
          >
            <div className="flex items-center gap-1.5">
              <div className="p-1 bg-gradient-to-br from-primary-500 to-secondary-600 rounded">
                <Sliders className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-500 dark:text-gray-400">Chunk Size</p>
                <p className="text-sm font-bold text-primary-600 dark:text-primary-400">
                  {settings.chunk_size}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Chunk Overlap */}
        {settings.chunk_overlap !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.35 }}
            className="glass-card-light p-2 rounded-lg hover-glow-primary smooth-transition"
          >
            <div className="flex items-center gap-1.5">
              <div className="p-1 bg-gradient-to-br from-secondary-500 to-primary-600 rounded">
                <Sliders className="w-3 h-3 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] text-gray-500 dark:text-gray-400">Overlap</p>
                <p className="text-sm font-bold text-secondary-600 dark:text-secondary-400">
                  {settings.chunk_overlap}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Search Type and Memory Type */}
      {(settings.search_type || settings.memory_type) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-2 flex items-center gap-2"
        >
          {settings.search_type && (
            <div className="glass-card-light px-2 py-1 rounded-md flex items-center gap-1.5">
              <div className="p-0.5 bg-gradient-to-br from-primary-500 to-secondary-500 rounded">
                <Search className="w-2.5 h-2.5 text-white" />
              </div>
              <span className="text-[10px] text-gray-600 dark:text-gray-400">
                Search: <span className="font-mono font-semibold gradient-text-primary">{settings.search_type}</span>
              </span>
            </div>
          )}
          {settings.memory_type && (
            <div className="glass-card-light px-2 py-1 rounded-md flex items-center gap-1.5">
              <div className="p-0.5 bg-gradient-to-br from-secondary-500 to-primary-500 rounded">
                <Brain className="w-2.5 h-2.5 text-white" />
              </div>
              <span className="text-[10px] text-gray-600 dark:text-gray-400">
                Memory: <span className="font-mono font-semibold gradient-text-primary">{settings.memory_type}</span>
              </span>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}
