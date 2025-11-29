import { useState, useEffect } from 'react'
import { FolderPlus, ChevronDown, Search, Folder } from 'lucide-react'
import axios from 'axios'
import CreateProjectModal from './CreateProjectModal'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Project {
  id: string
  name: string
  description?: string
  owner_username?: string
  department_name?: string
  team_name?: string
  status: string
  file_count: number
  total_size: number
}

interface ProjectSelectorProps {
  value?: string
  onChange: (projectId: string, project: Project | null) => void
  currentUser?: {
    id: string
    username: string
    role: string
    department_id?: string
    team_id?: string
  }
  placeholder?: string
  className?: string
  required?: boolean
}

export default function ProjectSelector({
  value,
  onChange,
  currentUser,
  placeholder = 'Select project...',
  className = '',
  required = false
}: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Load projects on mount
  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')  // Fixed: was 'token', should be 'access_token'
      const response = await axios.get(`${API_URL}/api/v1/projects`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      setProjects(response.data)
    } catch (err: any) {
      console.error('Error loading projects:', err)
      setError('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  const handleProjectCreated = (newProject: Project) => {
    setProjects([newProject, ...projects])
    onChange(newProject.id, newProject)
    setShowCreateModal(false)
  }

  // Filter projects by search query
  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.department_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.team_name?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Get selected project
  const selectedProject = projects.find(p => p.id === value)

  // Format file size
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  return (
    <>
      <div className={`relative ${className}`}>
        {/* Selected Value Display */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-left flex items-center justify-between hover:border-slate-400 dark:hover:border-slate-500 transition-colors"
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {selectedProject ? (
              <>
                <Folder className="w-4 h-4 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{selectedProject.name}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                    {selectedProject.department_name} • {selectedProject.team_name}
                  </div>
                </div>
              </>
            ) : (
              <span className="text-slate-400">{placeholder}</span>
            )}
          </div>
          <ChevronDown
            className={`w-4 h-4 text-slate-400 flex-shrink-0 transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute z-50 mt-1 w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg shadow-lg max-h-96 overflow-hidden">
            {/* Search */}
            <div className="p-2 border-b border-slate-200 dark:border-slate-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search projects..."
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            {/* Create New Project Button */}
            <button
              onClick={() => {
                setShowCreateModal(true)
                setIsOpen(false)
              }}
              className="w-full px-3 py-2.5 text-left hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 border-b border-slate-200 dark:border-slate-700"
            >
              <FolderPlus className="w-4 h-4" />
              Create New Project
            </button>

            {/* Projects List */}
            <div className="max-h-64 overflow-y-auto">
              {loading ? (
                <div className="p-4 text-center text-sm text-slate-500">
                  Loading projects...
                </div>
              ) : error ? (
                <div className="p-4 text-center text-sm text-red-600 dark:text-red-400">
                  {error}
                </div>
              ) : filteredProjects.length === 0 ? (
                <div className="p-4 text-center text-sm text-slate-500">
                  {searchQuery ? 'No matching projects' : 'No projects yet'}
                </div>
              ) : (
                filteredProjects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      onChange(project.id, project)
                      setIsOpen(false)
                    }}
                    className={`w-full px-3 py-2.5 text-left hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors border-b border-slate-100 dark:border-slate-700 last:border-b-0 ${
                      value === project.id
                        ? 'bg-primary-50 dark:bg-primary-900/20'
                        : ''
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <Folder
                        className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                          value === project.id
                            ? 'text-primary-600 dark:text-primary-400'
                            : 'text-slate-400'
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-slate-900 dark:text-white truncate">
                          {project.name}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                          {project.department_name} • {project.team_name}
                        </div>
                        {project.file_count > 0 && (
                          <div className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                            {project.file_count} file{project.file_count !== 1 ? 's' : ''} •{' '}
                            {formatSize(project.total_size)}
                          </div>
                        )}
                      </div>
                      {value === project.id && (
                        <div className="flex-shrink-0">
                          <div className="w-5 h-5 bg-primary-600 dark:bg-primary-400 rounded-full flex items-center justify-center">
                            <svg
                              className="w-3 h-3 text-white dark:text-slate-900"
                              fill="none"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {/* Click Outside to Close */}
        {isOpen && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </div>

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleProjectCreated}
        currentUser={currentUser}
      />
    </>
  )
}
