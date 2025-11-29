import { useState, useEffect } from 'react'
import { X, Lock, FolderPlus, Loader2 } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Department {
  id: string
  name: string
  code: string
  description?: string
}

interface Team {
  id: string
  name: string
  code: string
  department_id: string
  department_name?: string
  member_count: number
}

interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (project: any) => void
  currentUser?: {
    id: string
    username: string
    role: string
    department_id?: string
    team_id?: string
  }
}

export default function CreateProjectModal({
  isOpen,
  onClose,
  onSuccess,
  currentUser
}: CreateProjectModalProps) {
  const [loading, setLoading] = useState(false)
  const [departments, setDepartments] = useState<Department[]>([])
  const [teams, setTeams] = useState<Team[]>([])

  // Form state
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('')
  const [selectedTeamId, setSelectedTeamId] = useState('')
  const [projectName, setProjectName] = useState('')
  const [description, setDescription] = useState('')

  // Error state
  const [error, setError] = useState<string | null>(null)

  // Load departments on mount
  useEffect(() => {
    if (isOpen) {
      loadDepartments()
    }
  }, [isOpen])

  // Load teams when department changes
  useEffect(() => {
    if (selectedDepartmentId) {
      loadTeams(selectedDepartmentId)
    } else {
      setTeams([])
      setSelectedTeamId('')
    }
  }, [selectedDepartmentId])

  // Auto-select user's department and team
  useEffect(() => {
    if (currentUser?.department_id && departments.length > 0) {
      setSelectedDepartmentId(currentUser.department_id)
    }
  }, [currentUser, departments])

  useEffect(() => {
    if (currentUser?.team_id && teams.length > 0) {
      setSelectedTeamId(currentUser.team_id)
    }
  }, [currentUser, teams])

  const loadDepartments = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_URL}/api/v1/departments`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      setDepartments(response.data)
    } catch (err: any) {
      console.error('Error loading departments:', err)
      setError('Failed to load departments')
    }
  }

  const loadTeams = async (departmentId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${API_URL}/api/v1/teams?department_id=${departmentId}`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      setTeams(response.data)
    } catch (err: any) {
      console.error('Error loading teams:', err)
      setError('Failed to load teams')
    }
  }

  const generatePathPreview = () => {
    if (!projectName || !selectedDepartmentId || !selectedTeamId) return ''

    const sanitize = (str: string) =>
      str.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')

    const dept = departments.find(d => d.id === selectedDepartmentId)
    const team = teams.find(t => t.id === selectedTeamId)
    const role = currentUser?.role || 'user'
    const username = currentUser?.username || 'username'

    return `${sanitize(role)}/${sanitize(dept?.name || 'dept')}/${sanitize(team?.name || 'team')}/${sanitize(username)}/${sanitize(projectName)}/`
  }

  const handleCreate = async () => {
    setError(null)

    // Validation
    if (!projectName.trim()) {
      setError('Project name is required')
      return
    }
    if (!selectedDepartmentId) {
      setError('Please select a department')
      return
    }
    if (!selectedTeamId) {
      setError('Please select a team')
      return
    }

    setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.post(
        `${API_URL}/api/v1/projects`,
        {
          name: projectName,
          description: description || undefined,
          department_id: selectedDepartmentId,
          team_id: selectedTeamId
        },
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )

      onSuccess(response.data)
      handleClose()
    } catch (err: any) {
      console.error('Error creating project:', err)
      setError(err.response?.data?.detail || 'Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setProjectName('')
    setDescription('')
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  const selectedDept = departments.find(d => d.id === selectedDepartmentId)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Create New Project</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Organize your files by project</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-800 dark:text-red-200">
              {error}
            </div>
          )}

          {/* Department - Auto-populated */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Department *
            </label>
            <div className="relative">
              <select
                value={selectedDepartmentId}
                onChange={(e) => setSelectedDepartmentId(e.target.value)}
                disabled={!!currentUser?.department_id}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">Select department...</option>
                {departments.map(dept => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
              {currentUser?.department_id && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                  <Lock className="w-3 h-3" />
                  <span>Auto</span>
                </div>
              )}
            </div>
            {currentUser?.department_id && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                ℹ️ Auto-populated from your user profile
              </p>
            )}
          </div>

          {/* Team - Dropdown */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Team *
            </label>
            <select
              value={selectedTeamId}
              onChange={(e) => setSelectedTeamId(e.target.value)}
              disabled={!selectedDepartmentId || loading}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white disabled:opacity-50"
              required
            >
              <option value="">Select team...</option>
              {teams.map(team => (
                <option key={team.id} value={team.id}>
                  {team.name} ({team.member_count} members)
                </option>
              ))}
            </select>
            {!selectedDepartmentId && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Select a department first
              </p>
            )}
          </div>

          {/* Project Name - User Input */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Project Name *
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g., ChatBot RAG, Customer Analytics"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400"
              required
            />
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Choose a descriptive name for your project
            </p>
          </div>

          {/* Description - Optional */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Brief description of the project..."
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 resize-none"
            />
          </div>

          {/* MinIO Path Preview */}
          {projectName && selectedDepartmentId && selectedTeamId && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">
                📁 Files will be stored at:
              </p>
              <p className="text-xs font-mono text-blue-700 dark:text-blue-300 break-all">
                {generatePathPreview()}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-200 dark:border-slate-700 flex items-center justify-end gap-3">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!projectName || !selectedDepartmentId || !selectedTeamId || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <FolderPlus className="w-4 h-4" />
                Create Project
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
