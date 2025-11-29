import { useState, useEffect } from 'react'
import { X, Edit3, Loader2 } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Project {
  id: string
  name: string
  description?: string
  department_name?: string
  team_name?: string
}

interface EditProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (project: any) => void
  project: Project | null
}

export default function EditProjectModal({
  isOpen,
  onClose,
  onSuccess,
  project
}: EditProjectModalProps) {
  const [loading, setLoading] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Populate form when project changes
  useEffect(() => {
    if (project) {
      setProjectName(project.name)
      setDescription(project.description || '')
    }
  }, [project])

  const handleUpdate = async () => {
    setError(null)

    // Validation
    if (!projectName.trim()) {
      setError('Project name is required')
      return
    }

    setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.put(
        `${API_URL}/api/v1/projects/${project?.id}`,
        {
          name: projectName,
          description: description || undefined
        },
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )

      onSuccess(response.data)
      handleClose()
    } catch (err: any) {
      console.error('Error updating project:', err)
      setError(err.response?.data?.detail || 'Failed to update project')
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

  if (!isOpen || !project) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-lg w-full">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
              <Edit3 className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Edit Project</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Update project details</p>
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

          {/* Department & Team (Read-only) */}
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Organization</p>
            <p className="text-sm text-slate-900 dark:text-white">
              {project.department_name} • {project.team_name}
            </p>
          </div>

          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Project Name *
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g., ChatBot RAG, Customer Analytics"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Brief description of the project..."
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
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
            onClick={handleUpdate}
            disabled={!projectName || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Edit3 className="w-4 h-4" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
