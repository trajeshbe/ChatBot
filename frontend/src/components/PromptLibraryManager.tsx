/**
 * Prompt Library Manager - CRUD UI for managing prompts and templates
 *
 * Features:
 * - List all prompts with search and filters
 * - Create new prompts
 * - Edit existing prompts
 * - Delete prompts
 * - Rate prompts
 * - Manage output templates
 * - Public/private toggle
 * - Module categorization
 */

import { useState, useEffect } from 'react'
import {
  Plus, Edit2, Trash2, Star, Search, Filter,
  Save, X, Eye, EyeOff, CheckCircle, AlertCircle,
  FileText, Code, Table, Layout, Download
} from 'lucide-react'
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
  output_schema: any
  example_input: string
  example_output: string
  is_public: boolean
  is_verified: boolean
  usage_count: number
  average_rating: number
  total_ratings: number
  created_at: string
  updated_at: string
  creator_username?: string
}

interface OutputTemplate {
  id: string
  name: string
  description: string
  template_type: string
  template_config: any
  is_public: boolean
  created_at: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function PromptLibraryManager() {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [templates, setTemplates] = useState<OutputTemplate[]>([])
  const [filteredPrompts, setFilteredPrompts] = useState<Prompt[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedModule, setSelectedModule] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [showPublicOnly, setShowPublicOnly] = useState(false)

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null)
  const [activeTab, setActiveTab] = useState<'prompts' | 'templates'>('prompts')

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt_text: '',
    prompt_type: 'general',
    category: 'general',
    module: 'chat',
    tags: '',
    expected_output_format: 'text',
    example_input: '',
    example_output: '',
    is_public: true,
  })

  // Fetch prompts
  useEffect(() => {
    fetchPrompts()
    fetchTemplates()
  }, [])

  // Filter prompts
  useEffect(() => {
    let filtered = prompts

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query) ||
        p.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // Module filter
    if (selectedModule !== 'all') {
      filtered = filtered.filter(p => p.module === selectedModule)
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(p => p.category === selectedCategory)
    }

    // Public filter
    if (showPublicOnly) {
      filtered = filtered.filter(p => p.is_public)
    }

    setFilteredPrompts(filtered)
  }, [searchQuery, selectedModule, selectedCategory, showPublicOnly, prompts])

  const fetchPrompts = async () => {
    try {
      setIsLoading(true)
      const response = await axios.get(`${API_URL}/api/v1/prompts`, {
        params: { page: 1, page_size: 100, sort_by: 'created_at', sort_order: 'desc' }
      })
      setPrompts(response.data.prompts)
      setFilteredPrompts(response.data.prompts)
    } catch (error) {
      console.error('Error fetching prompts:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/templates`, {
        params: { page: 1, page_size: 100 }
      })
      setTemplates(response.data.templates)
    } catch (error) {
      console.error('Error fetching templates:', error)
    }
  }

  const handleCreatePrompt = async () => {
    try {
      const payload = {
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
      }
      await axios.post(`${API_URL}/api/v1/prompts`, payload)
      alert('Prompt created successfully!')
      setShowCreateModal(false)
      resetForm()
      fetchPrompts()
    } catch (error) {
      console.error('Error creating prompt:', error)
      alert('Failed to create prompt')
    }
  }

  const handleUpdatePrompt = async () => {
    if (!selectedPrompt) return
    try {
      const payload = {
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
      }
      await axios.put(`${API_URL}/api/v1/prompts/${selectedPrompt.id}`, payload)
      alert('Prompt updated successfully!')
      setShowEditModal(false)
      setSelectedPrompt(null)
      resetForm()
      fetchPrompts()
    } catch (error) {
      console.error('Error updating prompt:', error)
      alert('Failed to update prompt')
    }
  }

  const handleDeletePrompt = async (promptId: string) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return
    try {
      await axios.delete(`${API_URL}/api/v1/prompts/${promptId}`)
      alert('Prompt deleted successfully!')
      fetchPrompts()
    } catch (error) {
      console.error('Error deleting prompt:', error)
      alert('Failed to delete prompt')
    }
  }

  const handleRatePrompt = async (promptId: string, rating: number) => {
    try {
      await axios.post(`${API_URL}/api/v1/prompts/${promptId}/rate`, { rating })
      fetchPrompts()
    } catch (error) {
      console.error('Error rating prompt:', error)
    }
  }

  const openEditModal = (prompt: Prompt) => {
    setSelectedPrompt(prompt)
    setFormData({
      name: prompt.name,
      description: prompt.description,
      prompt_text: prompt.prompt_text,
      prompt_type: prompt.prompt_type,
      category: prompt.category,
      module: prompt.module,
      tags: prompt.tags.join(', '),
      expected_output_format: prompt.expected_output_format,
      example_input: prompt.example_input || '',
      example_output: prompt.example_output || '',
      is_public: prompt.is_public,
    })
    setShowEditModal(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      prompt_text: '',
      prompt_type: 'general',
      category: 'general',
      module: 'chat',
      tags: '',
      expected_output_format: 'text',
      example_input: '',
      example_output: '',
      is_public: true,
    })
  }

  const getOutputFormatIcon = (format: string) => {
    switch (format) {
      case 'json': return <Code className="w-4 h-4" />
      case 'table': return <Table className="w-4 h-4" />
      case 'markdown': return <FileText className="w-4 h-4" />
      default: return <Layout className="w-4 h-4" />
    }
  }

  const getOutputFormatColor = (format: string) => {
    switch (format) {
      case 'json': return 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
      case 'table': return 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300'
      case 'markdown': return 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
      default: return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-900 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              Prompt Library Manager
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Create, edit, and manage your prompt library
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Create New Prompt
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mt-4">
          <button
            onClick={() => setActiveTab('prompts')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'prompts'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            Prompts ({prompts.length})
          </button>
          <button
            onClick={() => setActiveTab('templates')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'templates'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            Templates ({templates.length})
          </button>
        </div>
      </div>

      {/* Filters */}
      {activeTab === 'prompts' && (
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search prompts..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Module Filter */}
            <select
              value={selectedModule}
              onChange={(e) => setSelectedModule(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Modules</option>
              <option value="chat">Chat</option>
              <option value="scraping">Scraping</option>
              <option value="project_estimator">Project Estimator</option>
              <option value="general">General</option>
            </select>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Categories</option>
              <option value="general">General</option>
              <option value="data-analysis">Data Analysis</option>
              <option value="business">Business</option>
              <option value="technical">Technical</option>
            </select>

            {/* Public Filter */}
            <button
              onClick={() => setShowPublicOnly(!showPublicOnly)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                showPublicOnly
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600'
              }`}
            >
              {showPublicOnly ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
              Public Only
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'prompts' ? (
          isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredPrompts.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No prompts found</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {searchQuery ? 'Try adjusting your search or filters' : 'Create your first prompt to get started'}
              </p>
              {!searchQuery && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Prompt
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredPrompts.map((prompt) => (
                <div
                  key={prompt.id}
                  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        {prompt.name}
                        {prompt.is_verified && (
                          <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" title="Verified" />
                        )}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                        {prompt.description}
                      </p>
                    </div>
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={() => openEditModal(prompt)}
                        className="p-1.5 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                        title="Edit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeletePrompt(prompt.id)}
                        className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">
                      {prompt.module}
                    </span>
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full">
                      {prompt.category}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full flex items-center gap-1 ${getOutputFormatColor(prompt.expected_output_format)}`}>
                      {getOutputFormatIcon(prompt.expected_output_format)}
                      {prompt.expected_output_format}
                    </span>
                    {prompt.is_public && (
                      <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full">
                        Public
                      </span>
                    )}
                  </div>

                  {/* Tags */}
                  {prompt.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {prompt.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      <span>{prompt.average_rating.toFixed(1)} ({prompt.total_ratings})</span>
                    </div>
                    <div>
                      Used {prompt.usage_count} times
                    </div>
                  </div>

                  {/* Rating */}
                  <div className="flex items-center gap-1 mt-2">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => handleRatePrompt(prompt.id, rating)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                      >
                        <Star
                          className={`w-4 h-4 ${
                            rating <= Math.round(prompt.average_rating)
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-gray-300 dark:text-gray-600'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          // Templates Tab
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{template.name}</h3>
                  <Download className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{template.description}</p>
                <div className="flex gap-2">
                  <span className="text-xs px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full">
                    {template.template_type}
                  </span>
                  {template.is_public && (
                    <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full">
                      Public
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || showEditModal) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {showEditModal ? 'Edit Prompt' : 'Create New Prompt'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setShowEditModal(false)
                  setSelectedPrompt(null)
                  resetForm()
                }}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Prompt Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Entity Extraction"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of what this prompt does"
                  rows={2}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Prompt Text */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Prompt Text * <span className="text-xs text-gray-500">(Use {'{'}variable{'}'} for placeholders)</span>
                </label>
                <textarea
                  value={formData.prompt_text}
                  onChange={(e) => setFormData({ ...formData, prompt_text: e.target.value })}
                  placeholder="e.g., Extract all entities from {input_text} and format as JSON"
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>

              {/* Row: Type, Category, Module */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Type
                  </label>
                  <input
                    type="text"
                    value={formData.prompt_type}
                    onChange={(e) => setFormData({ ...formData, prompt_type: e.target.value })}
                    placeholder="e.g., entity_extraction"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="general">General</option>
                    <option value="data-analysis">Data Analysis</option>
                    <option value="business">Business</option>
                    <option value="technical">Technical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Module
                  </label>
                  <select
                    value={formData.module}
                    onChange={(e) => setFormData({ ...formData, module: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="chat">Chat</option>
                    <option value="scraping">Scraping</option>
                    <option value="project_estimator">Project Estimator</option>
                    <option value="general">General</option>
                  </select>
                </div>
              </div>

              {/* Tags & Output Format */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tags <span className="text-xs text-gray-500">(comma-separated)</span>
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    placeholder="e.g., nlp, extraction, entities"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Output Format
                  </label>
                  <select
                    value={formData.expected_output_format}
                    onChange={(e) => setFormData({ ...formData, expected_output_format: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="text">Text</option>
                    <option value="json">JSON</option>
                    <option value="markdown">Markdown</option>
                    <option value="table">Table</option>
                  </select>
                </div>
              </div>

              {/* Example Input/Output */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Example Input
                  </label>
                  <textarea
                    value={formData.example_input}
                    onChange={(e) => setFormData({ ...formData, example_input: e.target.value })}
                    placeholder="Sample input for this prompt"
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Example Output
                  </label>
                  <textarea
                    value={formData.example_output}
                    onChange={(e) => setFormData({ ...formData, example_output: e.target.value })}
                    placeholder="Expected output for the example input"
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
              </div>

              {/* Public Toggle */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_public" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Make this prompt public (visible to all users)
                </label>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setShowEditModal(false)
                  setSelectedPrompt(null)
                  resetForm()
                }}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={showEditModal ? handleUpdatePrompt : handleCreatePrompt}
                disabled={!formData.name || !formData.description || !formData.prompt_text}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                <Save className="w-5 h-5" />
                {showEditModal ? 'Update Prompt' : 'Create Prompt'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
