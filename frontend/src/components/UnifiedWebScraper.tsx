import { useState, useEffect } from 'react'
import { Globe, Sparkles, FileSpreadsheet, Zap, Folder, Loader2 } from 'lucide-react'
import axios from 'axios'
import WebScraper from './WebScraper'
import { SmartExtractor } from './SmartExtractor'
import { SmartTemplateMapper } from './SmartTemplateMapper'
import TemplateExtractor from './TemplateExtractor'

type TabType = 'basic' | 'smart' | 'mapper' | 'template'

interface Project {
  id: string
  name: string
  description?: string
  status?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function UnifiedWebScraper() {
  const [activeTab, setActiveTab] = useState<TabType>('basic')
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [projects, setProjects] = useState<Project[]>([])
  const [loadingProjects, setLoadingProjects] = useState(false)

  // Load projects on mount
  useEffect(() => {
    const fetchProjects = async () => {
      setLoadingProjects(true)
      try {
        const token = localStorage.getItem('access_token')
        const response = await axios.get(`${API_URL}/api/v1/projects`, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined
        })
        const fetchedProjects = response.data || []
        setProjects(fetchedProjects)

        // Auto-select Global project or first active project as default
        const activeProjects = fetchedProjects.filter((p: Project) => p.status === 'active')
        if (activeProjects.length > 0 && !selectedProjectId) {
          // Try to find Global project first
          const globalProject = activeProjects.find((p: Project) =>
            p.name.toLowerCase() === 'global'
          )
          setSelectedProjectId(globalProject?.id || activeProjects[0].id)
        }
      } catch (error) {
        console.error('Error fetching projects:', error)
        // Silently fail - projects are optional
      } finally {
        setLoadingProjects(false)
      }
    }

    fetchProjects()
  }, [])

  const tabs = [
    {
      id: 'basic' as TabType,
      label: 'Basic Scraping',
      icon: Globe,
      description: 'Simple web scraping - save pages to knowledge base'
    },
    {
      id: 'smart' as TabType,
      label: 'Smart Extraction',
      icon: Sparkles,
      description: 'AI extracts data without templates - just describe what you want'
    },
    {
      id: 'mapper' as TabType,
      label: 'Template Mapper',
      icon: Zap,
      description: 'AI maps data to your custom Excel columns'
    },
    {
      id: 'template' as TabType,
      label: 'CSS Selector Based',
      icon: FileSpreadsheet,
      description: 'Preset templates with CSS selectors (fast & reliable)'
    }
  ]

  return (
    <div className="w-full max-w-6xl mx-auto px-4">
      {/* Compact Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
          Web Scraping & Data Extraction
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Extract data from websites using various methods
        </p>
      </div>

      {/* Compact Project Context Dropdown */}
      <div className="bg-gradient-to-r from-white to-gray-50 dark:from-slate-800 dark:to-slate-800/50 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-slate-700 mb-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 min-w-0">
            <Folder className="w-4 h-4 text-primary-600 flex-shrink-0" />
            <span className="text-sm font-medium text-slate-900 dark:text-white">
              Project Context
            </span>
          </div>

          {loadingProjects ? (
            <div className="flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-xs">Loading...</span>
            </div>
          ) : (
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="max-w-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-1.5 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {projects.filter(p => p.status === 'active').map(project => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedProjectId && (
          <p className="text-xs text-primary-600 dark:text-primary-400 mt-2 flex items-center gap-1">
            <span>✓</span>
            <span>Content will be organized under selected project</span>
          </p>
        )}
      </div>

      {/* Modern Pill-Style Tabs */}
      <div className="mb-6">
        <div className="inline-flex bg-gray-100 dark:bg-slate-800 rounded-xl p-1 gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg transition-all font-medium text-sm
                  ${
                    isActive
                      ? 'bg-white dark:bg-slate-700 text-primary-600 dark:text-primary-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }
                `}
                title={tab.description}
              >
                <Icon className="w-4 h-4" />
                <span className="whitespace-nowrap">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'basic' && (
          <div>
            <WebScraper projectId={selectedProjectId} />
          </div>
        )}

        {activeTab === 'smart' && (
          <div>
            <SmartExtractor projectId={selectedProjectId} />
          </div>
        )}

        {activeTab === 'mapper' && (
          <div>
            <SmartTemplateMapper projectId={selectedProjectId} />
          </div>
        )}

        {activeTab === 'template' && (
          <div>
            <TemplateExtractor sessionId="" projectId={selectedProjectId} />
          </div>
        )}
      </div>

      {/* Compact Info Footer */}
      <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 border border-blue-200 dark:border-blue-800/50 rounded-xl">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3 text-sm">
          💡 Quick Guide: Which method to use?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="flex items-start gap-2">
            <Globe className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
            <div className="text-blue-800 dark:text-blue-200">
              <strong className="font-semibold">Basic:</strong> Save entire pages to knowledge base
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Sparkles className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-purple-600 dark:text-purple-400" />
            <div className="text-blue-800 dark:text-blue-200">
              <strong className="font-semibold">Smart:</strong> AI extracts data based on instructions
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Zap className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
            <div className="text-blue-800 dark:text-blue-200">
              <strong className="font-semibold">Mapper:</strong> AI maps data to your Excel columns
            </div>
          </div>
          <div className="flex items-start gap-2">
            <FileSpreadsheet className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400" />
            <div className="text-blue-800 dark:text-blue-200">
              <strong className="font-semibold">CSS:</strong> Fastest - uses preset selectors
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
