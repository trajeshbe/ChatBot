/**
 * Prompt Command Palette - Modern slash command UI for prompt library
 *
 * Features:
 * - Triggers on "/" character
 * - Keyboard navigation (arrow keys, enter, escape)
 * - Fuzzy search
 * - Shows prompt details and examples
 * - Inserts prompt with variable placeholders
 */

import { useState, useEffect, useRef } from 'react'
import { FileText, Star, TrendingUp, Clock, Tag, Layers } from 'lucide-react'
import axios from 'axios'

interface Prompt {
  id: string
  name: string
  description: string
  prompt_text: string
  prompt_type: string
  category: string
  module: string
  tags: string[]
  expected_output_format: string
  example_input: string
  example_output: string
  usage_count: number
  average_rating: number
  total_ratings: number
  is_public: boolean
  is_verified: boolean
}

interface Props {
  isOpen: boolean
  onClose: () => void
  onSelectPrompt: (promptText: string) => void
  searchQuery: string
  module?: string  // Filter by current module (chat, scraping, etc.)
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function PromptCommandPalette({ isOpen, onClose, onSelectPrompt, searchQuery, module }: Props) {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [filteredPrompts, setFilteredPrompts] = useState<Prompt[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const paletteRef = useRef<HTMLDivElement>(null)

  // Fetch prompts
  useEffect(() => {
    if (isOpen) {
      fetchPrompts()
    }
  }, [isOpen, module])

  // Filter prompts based on search query
  useEffect(() => {
    if (!searchQuery) {
      setFilteredPrompts(prompts)
      return
    }

    const query = searchQuery.toLowerCase()
    const filtered = prompts.filter(prompt =>
      prompt.name.toLowerCase().includes(query) ||
      prompt.description.toLowerCase().includes(query) ||
      prompt.prompt_type.toLowerCase().includes(query) ||
      prompt.category.toLowerCase().includes(query) ||
      prompt.tags.some(tag => tag.toLowerCase().includes(query))
    )
    setFilteredPrompts(filtered)
    setSelectedIndex(0)
  }, [searchQuery, prompts])

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => Math.min(prev + 1, filteredPrompts.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => Math.max(prev - 1, 0))
          break
        case 'Enter':
          e.preventDefault()
          if (filteredPrompts[selectedIndex]) {
            handleSelectPrompt(filteredPrompts[selectedIndex])
          }
          break
        case 'Escape':
          e.preventDefault()
          onClose()
          break
        case 'Tab':
          e.preventDefault()
          setShowDetails(!showDetails)
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, selectedIndex, filteredPrompts, showDetails])

  // Scroll selected item into view
  useEffect(() => {
    const selectedElement = paletteRef.current?.querySelector(`[data-index="${selectedIndex}"]`)
    selectedElement?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [selectedIndex])

  const fetchPrompts = async () => {
    try {
      setIsLoading(true)
      const params: any = {
        page: 1,
        page_size: 50,
        sort_by: 'usage_count',
        sort_order: 'desc'
      }

      if (module) {
        params.module = module
      }

      const response = await axios.get(`${API_URL}/api/v1/prompts`, { params })
      setPrompts(response.data.prompts)
      setFilteredPrompts(response.data.prompts)
    } catch (error) {
      console.error('Error fetching prompts:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectPrompt = (prompt: Prompt) => {
    onSelectPrompt(prompt.prompt_text)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div
      className="absolute bottom-full left-0 right-0 mb-2 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 max-h-96 overflow-hidden z-50"
      ref={paletteRef}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Prompt Library
            </h3>
            {module && (
              <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">
                {module}
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {filteredPrompts.length} prompts • ↑↓ Navigate • ↵ Select • Tab Details • Esc Close
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex max-h-80">
        {/* Prompts List */}
        <div className={`flex-1 overflow-y-auto ${showDetails ? 'w-1/2' : 'w-full'}`}>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredPrompts.length === 0 ? (
            <div className="text-center py-8 px-4 text-gray-500 dark:text-gray-400">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No prompts found</p>
              <p className="text-xs mt-1">Try a different search or create a new prompt</p>
            </div>
          ) : (
            <div className="py-1">
              {filteredPrompts.map((prompt, index) => (
                <button
                  key={prompt.id}
                  data-index={index}
                  onClick={() => handleSelectPrompt(prompt)}
                  className={`w-full text-left px-4 py-3 transition-colors ${
                    index === selectedIndex
                      ? 'bg-blue-50 dark:bg-blue-900/30 border-l-4 border-blue-600'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {prompt.name}
                        </h4>
                        {prompt.is_verified && (
                          <span className="flex-shrink-0 text-blue-600 dark:text-blue-400" title="Verified">
                            ✓
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">
                        {prompt.description}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
                        <span className="flex items-center gap-1">
                          <Tag className="w-3 h-3" />
                          {prompt.prompt_type}
                        </span>
                        <span className="flex items-center gap-1">
                          <Layers className="w-3 h-3" />
                          {prompt.category}
                        </span>
                        {prompt.usage_count > 0 && (
                          <span className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" />
                            {prompt.usage_count}
                          </span>
                        )}
                        {prompt.total_ratings > 0 && (
                          <span className="flex items-center gap-1">
                            <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                            {prompt.average_rating.toFixed(1)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        prompt.expected_output_format === 'json' ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300' :
                        prompt.expected_output_format === 'markdown' ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' :
                        prompt.expected_output_format === 'table' ? 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300' :
                        'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}>
                        {prompt.expected_output_format}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Prompt Details Panel (shown when Tab is pressed) */}
        {showDetails && filteredPrompts[selectedIndex] && (
          <div className="w-1/2 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-y-auto p-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Prompt Details
            </h4>

            {/* Prompt Text */}
            <div className="mb-4">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Prompt Text:</p>
              <div className="text-xs text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                {filteredPrompts[selectedIndex].prompt_text}
              </div>
            </div>

            {/* Example Input */}
            {filteredPrompts[selectedIndex].example_input && (
              <div className="mb-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Example Input:</p>
                <div className="text-xs text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 max-h-20 overflow-y-auto">
                  {filteredPrompts[selectedIndex].example_input}
                </div>
              </div>
            )}

            {/* Example Output */}
            {filteredPrompts[selectedIndex].example_output && (
              <div className="mb-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Example Output:</p>
                <div className="text-xs text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 font-mono max-h-20 overflow-y-auto">
                  {filteredPrompts[selectedIndex].example_output}
                </div>
              </div>
            )}

            {/* Tags */}
            {filteredPrompts[selectedIndex].tags.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Tags:</p>
                <div className="flex flex-wrap gap-1">
                  {filteredPrompts[selectedIndex].tags.map(tag => (
                    <span key={tag} className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          💡 Tip: Variables in curly braces {'{'}like {'{'}this{'}'}{'}'}  will be replaced with your input
        </p>
      </div>
    </div>
  )
}
