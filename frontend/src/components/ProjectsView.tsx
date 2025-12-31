import { useState, useEffect } from 'react'
import { Search, Plus, ChevronDown, Folder, Calendar, Activity, Edit3, Clock, MoreVertical, Trash2, Archive } from 'lucide-react'
import axios from 'axios'
import CreateProjectModal from './CreateProjectModal'
import EditProjectModal from './EditProjectModal'

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
  created_at: string
  updated_at: string
}

interface ProjectsViewProps {
  currentUser?: {
    id: string
    username: string
    role: string
    department_id?: string
    team_id?: string
  }
  onProjectClick?: (projectId: string) => void
}

type SortOption = 'activity' | 'edited' | 'created'

export default function ProjectsView({ currentUser, onProjectClick }: ProjectsViewProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('activity')
  const [showSortDropdown, setShowSortDropdown] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [projectToEdit, setProjectToEdit] = useState<Project | null>(null)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('access_token')
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
    setShowCreateModal(false)
  }

  const handleEditProject = (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    if (project) {
      setProjectToEdit(project)
      setShowEditModal(true)
    }
    setOpenMenuId(null)
  }

  const handleProjectUpdated = (updatedProject: Project) => {
    setProjects(projects.map(p => p.id === updatedProject.id ? updatedProject : p))
    setShowEditModal(false)
    setProjectToEdit(null)
  }

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      await axios.delete(`${API_URL}/api/v1/projects/${projectId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      setProjects(projects.filter(p => p.id !== projectId))
      setOpenMenuId(null)
    } catch (err: any) {
      console.error('Error deleting project:', err)
      alert('Failed to delete project')
    }
  }

  const handleArchiveProject = async (projectId: string) => {
    console.log('Archive project:', projectId)
    setOpenMenuId(null)
    // TODO: Implement archive functionality
  }

  // Filter projects by search query
  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.department_name?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Sort projects
  const sortedProjects = [...filteredProjects].sort((a, b) => {
    switch (sortBy) {
      case 'activity':
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      case 'edited':
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      case 'created':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      default:
        return 0
    }
  })

  // Format date to "X days ago"
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now.getTime() - date.getTime()
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInDays === 0) return 'Today'
    if (diffInDays === 1) return 'Yesterday'
    if (diffInDays < 7) return `${diffInDays} days ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
    return `${Math.floor(diffInDays / 30)} months ago`
  }

  // Format file size
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  const sortOptions = [
    { value: 'activity' as SortOption, label: 'Recent activity', icon: Activity },
    { value: 'edited' as SortOption, label: 'Last edited', icon: Edit3 },
    { value: 'created' as SortOption, label: 'Date created', icon: Calendar },
  ]

  return (
    <div className="flex-1 flex flex-col bg-slate-50 dark:bg-slate-900 overflow-hidden">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Projects</h1>

            {/* New Project Button */}
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-100 transition-colors font-medium shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>New project</span>
            </button>
          </div>

          {/* Search and Sort */}
          <div className="flex items-center gap-4">
            {/* Search Bar */}
            <div className="flex-1 max-w-md relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search projects..."
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow"
              />
            </div>

            {/* Sort Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowSortDropdown(!showSortDropdown)}
                className="flex items-center gap-2 px-4 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <span className="text-sm font-medium">Sort by</span>
                <span className="text-sm text-slate-500">
                  {sortOptions.find(opt => opt.value === sortBy)?.label}
                </span>
                <ChevronDown className="w-4 h-4 text-slate-400" />
              </button>

              {/* Sort Dropdown Menu */}
              {showSortDropdown && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowSortDropdown(false)}
                  />
                  <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-20 overflow-hidden">
                    {sortOptions.map((option) => {
                      const Icon = option.icon
                      return (
                        <button
                          key={option.value}
                          onClick={() => {
                            setSortBy(option.value)
                            setShowSortDropdown(false)
                          }}
                          className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors ${
                            sortBy === option.value
                              ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                              : 'text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          <span className="text-sm font-medium">{option.label}</span>
                          {sortBy === option.value && (
                            <div className="ml-auto w-2 h-2 rounded-full bg-primary-600 dark:bg-primary-400" />
                          )}
                        </button>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                <p className="text-slate-600 dark:text-slate-400">Loading projects...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                <button
                  onClick={loadProjects}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : sortedProjects.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center max-w-md">
                <Folder className="w-16 h-16 text-slate-300 dark:text-slate-700 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  {searchQuery ? 'No matching projects' : 'No projects yet'}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  {searchQuery
                    ? 'Try adjusting your search terms'
                    : 'Create your first project to get started organizing your work'}
                </p>
                {!searchQuery && (
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
                  >
                    <Plus className="w-4 h-4" />
                    Create Project
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sortedProjects.map((project) => (
                <div
                  key={project.id}
                  className="group bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-5 hover:shadow-lg hover:border-primary-300 dark:hover:border-primary-700 transition-all duration-200 cursor-pointer"
                  onClick={() => {
                    if (onProjectClick) {
                      onProjectClick(project.id)
                    }
                  }}
                >
                  {/* Project Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0">
                        <Folder className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                          {project.name}
                        </h3>
                      </div>
                    </div>

                    {/* Three-dot menu */}
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuId(openMenuId === project.id ? null : project.id)
                        }}
                        className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors opacity-0 group-hover:opacity-100"
                        title="More actions"
                      >
                        <MoreVertical className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                      </button>

                      {/* Dropdown menu */}
                      {openMenuId === project.id && (
                        <>
                          <div
                            className="fixed inset-0 z-10"
                            onClick={() => setOpenMenuId(null)}
                          />
                          <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-20 overflow-hidden">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleEditProject(project.id)
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
                            >
                              <Edit3 className="w-4 h-4" />
                              <span className="text-sm font-medium">Edit project</span>
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleArchiveProject(project.id)
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
                            >
                              <Archive className="w-4 h-4" />
                              <span className="text-sm font-medium">Archive</span>
                            </button>
                            <div className="border-t border-slate-200 dark:border-slate-700" />
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteProject(project.id)
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-red-600 dark:text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                              <span className="text-sm font-medium">Delete project</span>
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Project Description */}
                  {project.description && (
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-2">
                      {project.description}
                    </p>
                  )}

                  {/* Project Metadata */}
                  <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-500">
                    {project.file_count > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{project.file_count}</span>
                        <span>file{project.file_count !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                    {project.total_size > 0 && (
                      <div className="flex items-center gap-1">
                        <span>{formatSize(project.total_size)}</span>
                      </div>
                    )}
                  </div>

                  {/* Footer - Updated timestamp */}
                  <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-500">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Updated {formatTimeAgo(project.updated_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleProjectCreated}
        currentUser={currentUser}
      />

      {/* Edit Project Modal */}
      <EditProjectModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setProjectToEdit(null)
        }}
        onSuccess={handleProjectUpdated}
        project={projectToEdit}
      />
    </div>
  )
}
