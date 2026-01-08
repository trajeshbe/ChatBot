import { useState, useEffect } from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'
import { Users, Activity, Database, TrendingUp, Search, Filter, ChevronDown, ChevronUp, Key, Server, Wrench, Globe, Shield, Lock, UserPlus, Trash2, Settings } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import UserHeader from '@/components/UserHeader'
import APIKeysManager from '../components/APIKeysManager'
import OllamaModelsManager from '../components/OllamaModelsManager'
import { MCPToolsManager } from '../components/MCPToolsManager'
import { ScrapingConfigManager } from '../components/ScrapingConfigManager'
import RoleManager from '../components/admin/RoleManager'
import PermissionMatrix from '../components/admin/PermissionMatrix'
import UserRoleAssignment from '../components/admin/UserRoleAssignment'
import FineTuningManager from '../components/finetuning/FineTuningManager'
import FineTuningGovernanceUI from '../components/finetuning/FineTuningGovernanceUI'
import ExportWizardButton from '../components/ExportWizardButton'

interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
  last_login: string | null
  department_id: string | null
  department_name: string | null
  function: string | null
  team_ids: string[]
  team_names: string[]
}

interface Department {
  id: string
  name: string
  code: string
  description: string | null
  is_active: boolean
}

interface Team {
  id: string
  name: string
  code: string
  department_id: string
  department_name: string | null
  description: string | null
  is_active: boolean
}

interface Session {
  id: string
  session_id: string
  user_id: string | null
  title: string | null
  created_at: string
  last_activity: string
  is_active: boolean
  message_count: number
}

interface AuditLog {
  id: string
  user_id: string | null
  session_id: string | null
  action: string
  resource_type: string | null
  description: string | null
  ip_address: string | null
  status_code: number | null
  error_message: string | null
  latency_ms: number | null
  created_at: string
}

interface UsageMetric {
  id: string
  user_id: string | null
  date: string
  model_id: string | null
  total_queries: number
  total_tokens: number
  total_cost_usd: number
  avg_latency_ms: number
  documents_uploaded: number
  cache_hits: number
  cache_misses: number
}

interface DbDocument {
  id: string
  filename: string
  file_type: string
  file_size: number
  source_type: string
  source_url: string | null
  upload_date: string | null
  processed: boolean
  processing_error: string | null
  total_chunks: number
  chunks_with_embeddings: number
  embedding_percentage: number
  session_count: number
  session_ids: string[]
}

interface DbChunk {
  id: string
  chunk_index: number
  content: string
  content_length: number
  has_embedding: boolean
  embedding_dimensions: number | null
  meta_info: any
  created_at: string | null
}

interface DbStats {
  documents: {
    total: number
    processed: number
    failed: number
  }
  chunks: {
    total: number
    with_embeddings: number
    coverage_percentage: number
  }
  sessions: {
    total: number
    active: number
  }
  storage: {
    total_bytes: number
    total_mb: number
    total_gb: number
  }
  users: {
    total: number
  }
  audit: {
    total_logs: number
  }
}

export default function AdminPage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<'users' | 'sessions' | 'audit' | 'metrics' | 'database' | 'apikeys' | 'ollama' | 'mcptools' | 'scraping' | 'rbac' | 'finetuning'>('users')
  const [rbacSubTab, setRbacSubTab] = useState<'roles' | 'permissions' | 'users'>('roles')
  const [users, setUsers] = useState<User[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [metrics, setMetrics] = useState<UsageMetric[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [sessionDetails, setSessionDetails] = useState<any>(null)
  const [expandedLog, setExpandedLog] = useState<string | null>(null)

  // Redirect to login if not authenticated or not admin
  useEffect(() => {
    if (!isLoading && (!isAuthenticated || (user && user.role.toLowerCase() !== 'admin'))) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, user, router])

  // Database console state
  const [dbDocuments, setDbDocuments] = useState<DbDocument[]>([])
  const [dbStats, setDbStats] = useState<DbStats | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<DbDocument | null>(null)
  const [documentChunks, setDocumentChunks] = useState<DbChunk[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedChunk, setExpandedChunk] = useState<string | null>(null)

  // User creation form
  const [showUserForm, setShowUserForm] = useState(false)
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'user'
  })
  const [creatingUser, setCreatingUser] = useState(false)

  // Edit user modal
  const [showEditUserModal, setShowEditUserModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [departments, setDepartments] = useState<Department[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string>('')
  const [selectedTeamIds, setSelectedTeamIds] = useState<string[]>([])
  const [selectedFunction, setSelectedFunction] = useState<string>('')
  const [updatingUser, setUpdatingUser] = useState(false)

  // Filters
  const [actionFilter, setActionFilter] = useState<string>('')
  const [userFilter, setUserFilter] = useState<string>('')

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'users') {
        const res = await fetch(`${API_BASE}/api/v1/admin/users`)
        const data = await res.json()
        setUsers(data)
      } else if (activeTab === 'sessions') {
        const res = await fetch(`${API_BASE}/api/v1/admin/sessions?limit=50`)
        const data = await res.json()
        setSessions(data)
      } else if (activeTab === 'audit') {
        const res = await fetch(`${API_BASE}/api/v1/admin/audit-logs?limit=100`)
        const data = await res.json()
        setAuditLogs(data)
      } else if (activeTab === 'metrics') {
        const res = await fetch(`${API_BASE}/api/v1/admin/usage-metrics?days=7`)
        const data = await res.json()
        setMetrics(data)
      } else if (activeTab === 'database') {
        // Load DB stats
        const statsRes = await fetch(`${API_BASE}/api/v1/admin/db-console/stats`)
        const statsData = await statsRes.json()
        setDbStats(statsData)

        // Load documents
        const docsRes = await fetch(`${API_BASE}/api/v1/admin/db-console/documents?limit=50`)
        const docsData = await docsRes.json()
        setDbDocuments(docsData.documents || [])
      }
    } catch (error) {
      console.error('Error loading data:', error)
    }
    setLoading(false)
  }

  const loadDocumentChunks = async (documentId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/db-console/document/${documentId}/chunks?limit=100`)
      const data = await res.json()
      setDocumentChunks(data.chunks || [])
    } catch (error) {
      console.error('Error loading document chunks:', error)
    }
  }

  const searchDocuments = async () => {
    setLoading(true)
    try {
      const url = searchQuery
        ? `${API_BASE}/api/v1/admin/db-console/documents?search=${encodeURIComponent(searchQuery)}&limit=50`
        : `${API_BASE}/api/v1/admin/db-console/documents?limit=50`
      const res = await fetch(url)
      const data = await res.json()
      setDbDocuments(data.documents || [])
    } catch (error) {
      console.error('Error searching documents:', error)
    }
    setLoading(false)
  }

  const deleteDocument = async (documentId: string, filename: string) => {
    if (!confirm(
      `⚠️ Delete document and all embeddings?\n\n` +
      `Document: ${filename}\n` +
      `This will permanently delete:\n` +
      `• The document record\n` +
      `• All chunks\n` +
      `• All embeddings\n\n` +
      `This action cannot be undone.`
    )) {
      return
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/documents/${documentId}`, {
        method: 'DELETE'
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Failed to delete document')
      }

      const result = await res.json()
      alert(
        `✅ Document deleted successfully!\n\n` +
        `Filename: ${result.filename}\n` +
        `Chunks deleted: ${result.chunks_deleted}\n` +
        `Embeddings removed: ${result.embeddings_deleted}`
      )

      // Refresh the documents list
      await searchDocuments()

      // Clear selection if deleted document was selected
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null)
        setDocumentChunks([])
      }
    } catch (error: any) {
      console.error('Error deleting document:', error)
      alert(`❌ Failed to delete document:\n${error.message}`)
    }
  }

  const loadSessionDetails = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`)
      const data = await res.json()
      setSessionDetails(data)
      setSelectedSession(sessionId)
    } catch (error) {
      console.error('Error loading session details:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreatingUser(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newUser)
      })

      if (res.ok) {
        const createdUser = await res.json()
        setUsers([createdUser, ...users])
        setShowUserForm(false)
        setNewUser({
          username: '',
          email: '',
          full_name: '',
          password: '',
          role: 'user'
        })
        alert('User created successfully!')
      } else {
        const error = await res.json()
        alert(`Error creating user: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error creating user:', error)
      alert('Error creating user. Please try again.')
    }
    setCreatingUser(false)
  }

  const loadDepartments = async () => {
    try {
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      const res = await fetch(`${API_BASE}/api/v1/departments`, { headers })
      const data = await res.json()
      if (Array.isArray(data)) {
        setDepartments(data)
      } else {
        console.error('Departments response is not an array:', data)
        setDepartments([])
      }
    } catch (error) {
      console.error('Error loading departments:', error)
      setDepartments([])
    }
  }

  const loadTeams = async (departmentId?: string) => {
    try {
      const headers: HeadersInit = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      const url = departmentId
        ? `${API_BASE}/api/v1/teams?department_id=${departmentId}`
        : `${API_BASE}/api/v1/teams`
      const res = await fetch(url, { headers })
      const data = await res.json()
      if (Array.isArray(data)) {
        setTeams(data)
      } else {
        console.error('Teams response is not an array:', data)
        setTeams([])
      }
    } catch (error) {
      console.error('Error loading teams:', error)
      setTeams([])
    }
  }

  const handleEditUser = (user: User) => {
    setEditingUser(user)
    setSelectedDepartmentId(user.department_id || '')
    setSelectedTeamIds(user.team_ids || [])
    setSelectedFunction(user.function || '')
    setShowEditUserModal(true)
    // Load departments and teams
    loadDepartments()
    if (user.department_id) {
      loadTeams(user.department_id)
    }
  }

  const handleUpdateUser = async () => {
    if (!editingUser) return

    setUpdatingUser(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/users/${editingUser.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          department_id: selectedDepartmentId || null,
          function: selectedFunction || null,
          team_ids: selectedTeamIds
        })
      })

      if (res.ok) {
        const updatedUser = await res.json()
        setUsers(users.map(u => u.id === updatedUser.id ? updatedUser : u))
        setShowEditUserModal(false)
        setEditingUser(null)
        alert('User updated successfully!')
      } else {
        const error = await res.json()
        alert(`Error updating user: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error updating user:', error)
      alert('Error updating user. Please try again.')
    }
    setUpdatingUser(false)
  }

  const handleDepartmentChange = (deptId: string) => {
    setSelectedDepartmentId(deptId)
    setSelectedTeamIds([]) // Clear team selection when department changes
    if (deptId) {
      loadTeams(deptId)
    } else {
      setTeams([])
    }
  }

  const filteredAuditLogs = auditLogs.filter(log => {
    if (actionFilter && log.action !== actionFilter) return false
    if (userFilter && log.user_id !== userFilter) return false
    return true
  })

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated or not admin
  if (!isAuthenticated || (user && user.role.toLowerCase() !== 'admin')) {
    return null
  }

  return (
    <>
      <Head>
        <title>Admin Dashboard - Enterprise RAG Chatbot</title>
        <meta name="description" content="Admin dashboard for user and activity management" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        {/* User Header */}
        <UserHeader />

        {/* Header */}
        <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Admin Dashboard
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  Manage users, monitor activity, and track usage
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ExportWizardButton />
                <a
                  href="/"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Back to Chat
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
          <div className="px-6">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab('users')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'users'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4" />
                  <span>Users</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('sessions')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'sessions'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4" />
                  <span>Sessions</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('audit')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'audit'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Database className="w-4 h-4" />
                  <span>Audit Logs</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('metrics')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'metrics'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4" />
                  <span>Usage Metrics</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('database')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'database'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Database className="w-4 h-4" />
                  <span>Database</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('apikeys')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'apikeys'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Key className="w-4 h-4" />
                  <span>API Keys</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('ollama')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'ollama'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Server className="w-4 h-4" />
                  <span>Ollama Models</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('mcptools')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'mcptools'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Wrench className="w-4 h-4" />
                  <span>MCP & Tools</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('scraping')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'scraping'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Globe className="w-4 h-4" />
                  <span>Scraping Config</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('rbac')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'rbac'
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4" />
                  <span>RBAC</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('finetuning')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'finetuning'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Settings className="w-4 h-4" />
                  <span>Fine-Tuning</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Users Tab */}
              {activeTab === 'users' && (
                <div className="space-y-4">
                  {/* User Creation Form */}
                  {showUserForm && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                        Create New User
                      </h3>
                      <form onSubmit={handleCreateUser} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                              Username *
                            </label>
                            <input
                              type="text"
                              value={newUser.username}
                              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                              required
                              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                              Email *
                            </label>
                            <input
                              type="email"
                              value={newUser.email}
                              onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                              required
                              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                              Full Name
                            </label>
                            <input
                              type="text"
                              value={newUser.full_name}
                              onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                              Password *
                            </label>
                            <input
                              type="password"
                              value={newUser.password}
                              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                              required
                              minLength={8}
                              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                              Role *
                            </label>
                            <select
                              value={newUser.role}
                              onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                              required
                              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="user">User</option>
                              <option value="admin">Admin</option>
                              <option value="viewer">Viewer</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex gap-2 justify-end">
                          <button
                            type="button"
                            onClick={() => setShowUserForm(false)}
                            className="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={creatingUser}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                          >
                            {creatingUser ? 'Creating...' : 'Create User'}
                          </button>
                        </div>
                      </form>
                    </div>
                  )}

                  <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <div className="flex items-center justify-between">
                        <div>
                          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                            User Management
                          </h2>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                            Total users: {users.length}
                          </p>
                        </div>
                        <button
                          onClick={() => setShowUserForm(!showUserForm)}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                        >
                          <Users className="w-4 h-4" />
                          {showUserForm ? 'Cancel' : 'Add User'}
                        </button>
                      </div>
                    </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-slate-50 dark:bg-slate-900">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Username
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Email
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Role
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Department
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Teams
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Function
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                        {users.map((user) => (
                          <tr key={user.id} className="hover:bg-slate-50 dark:hover:bg-slate-750">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-white">
                              {user.username}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                              {user.email}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.role === 'admin'
                                  ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                                  : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                              }`}>
                                {user.role}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                              {user.department_name || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                              {user.team_names && user.team_names.length > 0
                                ? user.team_names.join(', ')
                                : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                              {user.function || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.is_active
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              }`}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                              <button
                                onClick={() => handleEditUser(user)}
                                className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                              >
                                Edit
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  </div>
                </div>
              )}

              {/* Edit User Modal */}
              {showEditUserModal && editingUser && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                  <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Edit User: {editingUser.username}
                      </h3>
                    </div>
                    <div className="px-6 py-4 space-y-4">
                      {/* Department */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Department
                        </label>
                        <select
                          value={selectedDepartmentId}
                          onChange={(e) => handleDepartmentChange(e.target.value)}
                          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">No Department</option>
                          {departments.map((dept) => (
                            <option key={dept.id} value={dept.id}>
                              {dept.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Function */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Function
                        </label>
                        <select
                          value={selectedFunction}
                          onChange={(e) => setSelectedFunction(e.target.value)}
                          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select Function</option>
                          <option value="Software Engineer">Software Engineer</option>
                          <option value="Senior Software Engineer">Senior Software Engineer</option>
                          <option value="Tech Lead">Tech Lead</option>
                          <option value="Engineering Manager">Engineering Manager</option>
                          <option value="Data Analyst">Data Analyst</option>
                          <option value="Data Scientist">Data Scientist</option>
                          <option value="Data Engineer">Data Engineer</option>
                          <option value="Product Manager">Product Manager</option>
                          <option value="Project Manager">Project Manager</option>
                          <option value="Business Analyst">Business Analyst</option>
                          <option value="QA Engineer">QA Engineer</option>
                          <option value="DevOps Engineer">DevOps Engineer</option>
                          <option value="System Administrator">System Administrator</option>
                          <option value="Database Administrator">Database Administrator</option>
                          <option value="UI/UX Designer">UI/UX Designer</option>
                          <option value="Solution Architect">Solution Architect</option>
                          <option value="Technical Architect">Technical Architect</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>

                      {/* Teams (Multi-select) */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                          Teams (Hold Ctrl/Cmd to select multiple)
                        </label>
                        <select
                          multiple
                          value={selectedTeamIds}
                          onChange={(e) => {
                            const options = Array.from(e.target.selectedOptions, option => option.value)
                            setSelectedTeamIds(options)
                          }}
                          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px]"
                          disabled={!selectedDepartmentId}
                        >
                          {teams.map((team) => (
                            <option key={team.id} value={team.id}>
                              {team.name}
                            </option>
                          ))}
                        </select>
                        {!selectedDepartmentId && (
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            Select a department first to see available teams
                          </p>
                        )}
                      </div>

                      {/* Current Selection Display */}
                      {selectedTeamIds.length > 0 && (
                        <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-lg">
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Selected Teams ({selectedTeamIds.length}):
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {selectedTeamIds.map(teamId => {
                              const team = teams.find(t => t.id === teamId)
                              return team ? (
                                <span key={teamId} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                                  {team.name}
                                </span>
                              ) : null
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-2">
                      <button
                        onClick={() => {
                          setShowEditUserModal(false)
                          setEditingUser(null)
                        }}
                        className="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleUpdateUser}
                        disabled={updatingUser}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                      >
                        {updatingUser ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Sessions Tab */}
              {activeTab === 'sessions' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Sessions List */}
                  <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Chat Sessions
                      </h2>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                        Total sessions: {sessions.length}
                      </p>
                    </div>
                    <div className="max-h-[700px] overflow-y-auto">
                      {sessions.map((session) => (
                        <div
                          key={session.id}
                          onClick={() => loadSessionDetails(session.session_id)}
                          className={`px-6 py-4 border-b border-slate-200 dark:border-slate-700 cursor-pointer transition-colors ${
                            selectedSession === session.session_id
                              ? 'bg-blue-50 dark:bg-blue-900/20'
                              : 'hover:bg-slate-50 dark:hover:bg-slate-750'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                                {session.title || `Session ${session.session_id.slice(0, 8)}...`}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                {session.message_count} messages • Last activity: {new Date(session.last_activity).toLocaleDateString()}
                              </p>
                            </div>
                            <div>
                              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                session.is_active
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                              }`}>
                                {session.is_active ? 'Active' : 'Closed'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Session Details */}
                  <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Session Details
                      </h2>
                    </div>
                    <div className="p-6">
                      {sessionDetails ? (
                        <div className="space-y-4">
                          <div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                              Session ID
                            </p>
                            <p className="text-sm font-mono text-slate-900 dark:text-white mt-1">
                              {sessionDetails.session_id}
                            </p>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                                Created
                              </p>
                              <p className="text-sm text-slate-900 dark:text-white mt-1">
                                {formatDate(sessionDetails.created_at)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                                Messages
                              </p>
                              <p className="text-sm text-slate-900 dark:text-white mt-1">
                                {sessionDetails.message_count}
                              </p>
                            </div>
                          </div>

                          <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
                            <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
                              Conversation
                            </p>
                            <div className="space-y-3 max-h-[500px] overflow-y-auto">
                              {sessionDetails.messages && sessionDetails.messages.map((msg: any, idx: number) => (
                                <div
                                  key={idx}
                                  className={`p-3 rounded-lg ${
                                    msg.role === 'user'
                                      ? 'bg-blue-50 dark:bg-blue-900/20'
                                      : 'bg-gray-50 dark:bg-slate-750'
                                  }`}
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase">
                                      {msg.role}
                                    </span>
                                    <span className="text-xs text-slate-500 dark:text-slate-400">
                                      {new Date(msg.created_at).toLocaleTimeString()}
                                    </span>
                                  </div>
                                  <p className="text-sm text-slate-900 dark:text-white whitespace-pre-wrap">
                                    {msg.content}
                                  </p>
                                  {msg.model_name && (
                                    <div className="mt-2 flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
                                      <span>Model: {msg.model_name}</span>
                                      {msg.total_tokens && <span>• {msg.total_tokens} tokens</span>}
                                      {msg.latency_ms && <span>• {Math.round(msg.latency_ms)}ms</span>}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="text-slate-500 dark:text-slate-400 text-center py-8">
                          Select a session to view details
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Audit Logs Tab */}
              {activeTab === 'audit' && (
                <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                  <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                          Audit Logs
                        </h2>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                          Total logs: {auditLogs.length}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <select
                          value={actionFilter}
                          onChange={(e) => setActionFilter(e.target.value)}
                          className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                        >
                          <option value="">All Actions</option>
                          <option value="query">Query</option>
                          <option value="upload">Upload</option>
                          <option value="scrape">Scrape</option>
                          <option value="login">Login</option>
                        </select>
                      </div>
                    </div>
                  </div>
                  <div className="max-h-[700px] overflow-y-auto">
                    {filteredAuditLogs.map((log) => (
                      <div
                        key={log.id}
                        className="px-6 py-4 border-b border-slate-200 dark:border-slate-700"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                log.action === 'query'
                                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                  : log.action === 'upload'
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : log.action === 'scrape'
                                  ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                              }`}>
                                {log.action}
                              </span>
                              <span className="text-xs text-slate-500 dark:text-slate-400">
                                {formatDate(log.created_at)}
                              </span>
                              {log.ip_address && (
                                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                                  {log.ip_address}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-slate-900 dark:text-white mt-2">
                              {log.description || 'No description'}
                            </p>
                            {log.latency_ms && (
                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Latency: {Math.round(log.latency_ms)}ms
                              </p>
                            )}
                            {log.error_message && (
                              <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                                Error: {log.error_message}
                              </p>
                            )}
                          </div>
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${
                            log.status_code && log.status_code < 400
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {log.status_code || 'N/A'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Usage Metrics Tab */}
              {activeTab === 'metrics' && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                      <p className="text-sm text-slate-600 dark:text-slate-400">Total Queries</p>
                      <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                        {metrics.reduce((sum, m) => sum + m.total_queries, 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                      <p className="text-sm text-slate-600 dark:text-slate-400">Total Tokens</p>
                      <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                        {metrics.reduce((sum, m) => sum + m.total_tokens, 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                      <p className="text-sm text-slate-600 dark:text-slate-400">Total Cost</p>
                      <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                        ${metrics.reduce((sum, m) => sum + m.total_cost_usd, 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                      <p className="text-sm text-slate-600 dark:text-slate-400">Avg Latency</p>
                      <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                        {metrics.length > 0
                          ? Math.round(metrics.reduce((sum, m) => sum + m.avg_latency_ms, 0) / metrics.length)
                          : 0}ms
                      </p>
                    </div>
                  </div>

                  {/* Detailed Metrics */}
                  <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Daily Metrics
                      </h2>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-50 dark:bg-slate-900">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Date
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Model
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Queries
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Tokens
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Cost
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Docs Uploaded
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                              Cache Hit Rate
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                          {metrics.map((metric) => {
                            const cacheHitRate =
                              metric.cache_hits + metric.cache_misses > 0
                                ? (metric.cache_hits / (metric.cache_hits + metric.cache_misses)) * 100
                                : 0
                            return (
                              <tr key={metric.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white">
                                  {new Date(metric.date).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                                  {metric.model_id || 'N/A'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white">
                                  {metric.total_queries.toLocaleString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white">
                                  {metric.total_tokens.toLocaleString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white">
                                  ${metric.total_cost_usd.toFixed(4)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white">
                                  {metric.documents_uploaded}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-white">
                                  {cacheHitRate.toFixed(1)}%
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* API Keys Tab */}
              {activeTab === 'apikeys' && (
                <div>
                  <APIKeysManager />
                </div>
              )}

              {/* Ollama Models Tab */}
              {activeTab === 'ollama' && (
                <div>
                  <OllamaModelsManager />
                </div>
              )}

              {/* MCP & Tools Tab */}
              {activeTab === 'mcptools' && (
                <div>
                  <MCPToolsManager />
                </div>
              )}

              {/* Scraping Configuration Tab */}
              {activeTab === 'scraping' && (
                <div>
                  <ScrapingConfigManager />
                </div>
              )}

              {/* RBAC Tab */}
              {activeTab === 'rbac' && (
                <div className="space-y-6">
                  {/* RBAC Sub-Navigation */}
                  <div className="border-b border-slate-200 dark:border-slate-700">
                    <div className="flex space-x-8">
                      <button
                        onClick={() => setRbacSubTab('roles')}
                        className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                          rbacSubTab === 'roles'
                            ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                            : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <Shield className="w-4 h-4" />
                          <span>Roles</span>
                        </div>
                      </button>
                      <button
                        onClick={() => setRbacSubTab('permissions')}
                        className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                          rbacSubTab === 'permissions'
                            ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                            : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <Lock className="w-4 h-4" />
                          <span>Permissions</span>
                        </div>
                      </button>
                      <button
                        onClick={() => setRbacSubTab('users')}
                        className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                          rbacSubTab === 'users'
                            ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                            : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <UserPlus className="w-4 h-4" />
                          <span>User Roles</span>
                        </div>
                      </button>
                    </div>
                  </div>

                  {/* RBAC Content */}
                  {rbacSubTab === 'roles' && <RoleManager />}
                  {rbacSubTab === 'permissions' && <PermissionMatrix />}
                  {rbacSubTab === 'users' && <UserRoleAssignment />}
                </div>
              )}

              {/* Fine-Tuning Tab */}
              {activeTab === 'finetuning' && (
                <div className="h-[calc(100vh-200px)]">
                  <FineTuningGovernanceUI />
                </div>
              )}

              {/* Database Tab */}
              {activeTab === 'database' && (
                <div className="space-y-6">
                  {/* Database Stats Cards */}
                  {dbStats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                        <p className="text-sm text-slate-600 dark:text-slate-400">Documents</p>
                        <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                          {dbStats.documents.total}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {dbStats.documents.processed} processed, {dbStats.documents.failed} failed
                        </p>
                      </div>
                      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                        <p className="text-sm text-slate-600 dark:text-slate-400">Chunks</p>
                        <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                          {dbStats.chunks.total}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {dbStats.chunks.coverage_percentage.toFixed(1)}% with embeddings
                        </p>
                      </div>
                      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                        <p className="text-sm text-slate-600 dark:text-slate-400">Storage</p>
                        <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                          {dbStats.storage.total_mb.toFixed(1)} MB
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {dbStats.storage.total_gb.toFixed(3)} GB total
                        </p>
                      </div>
                      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                        <p className="text-sm text-slate-600 dark:text-slate-400">Sessions</p>
                        <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2">
                          {dbStats.sessions.total}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {dbStats.sessions.active} active
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Documents List */}
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                          Documents & Embeddings
                        </h2>
                        <div className="mt-3 flex items-center space-x-2">
                          <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
                            placeholder="Search by filename..."
                            className="flex-1 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <button
                            onClick={searchDocuments}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                          >
                            <Search className="w-4 h-4" />
                            Search
                          </button>
                        </div>
                      </div>
                      <div className="max-h-[700px] overflow-y-auto">
                        {dbDocuments.map((doc) => (
                          <div
                            key={doc.id}
                            className={`px-6 py-4 border-b border-slate-200 dark:border-slate-700 transition-colors ${
                              selectedDocument?.id === doc.id
                                ? 'bg-blue-50 dark:bg-blue-900/20'
                                : 'hover:bg-slate-50 dark:hover:bg-slate-750'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div
                                className="flex-1 min-w-0 cursor-pointer"
                                onClick={() => {
                                  setSelectedDocument(doc)
                                  loadDocumentChunks(doc.id)
                                }}
                              >
                                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                                  {doc.filename}
                                </p>
                                <div className="flex items-center space-x-3 mt-1">
                                  <span className="text-xs text-slate-500 dark:text-slate-400">
                                    {doc.file_type}
                                  </span>
                                  <span className="text-xs text-slate-500 dark:text-slate-400">
                                    {(doc.file_size / 1024).toFixed(1)} KB
                                  </span>
                                  <span className={`text-xs font-semibold ${
                                    doc.processed
                                      ? 'text-green-600 dark:text-green-400'
                                      : 'text-yellow-600 dark:text-yellow-400'
                                  }`}>
                                    {doc.processed ? 'Processed' : 'Processing'}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-3 mt-2">
                                  <span className="text-xs text-slate-600 dark:text-slate-400">
                                    Chunks: {doc.total_chunks}
                                  </span>
                                  <span className="text-xs text-slate-600 dark:text-slate-400">
                                    Embeddings: {doc.chunks_with_embeddings} ({doc.embedding_percentage.toFixed(1)}%)
                                  </span>
                                </div>
                                {doc.session_count > 0 && (
                                  <div className="mt-2">
                                    <span className="text-xs text-blue-600 dark:text-blue-400">
                                      In {doc.session_count} session(s)
                                    </span>
                                  </div>
                                )}
                                {doc.processing_error && (
                                  <p className="text-xs text-red-600 dark:text-red-400 mt-1 truncate">
                                    Error: {doc.processing_error}
                                  </p>
                                )}
                              </div>
                              <div className="flex items-center gap-2 ml-3">
                                <div className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                  doc.embedding_percentage >= 100
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                    : doc.embedding_percentage > 0
                                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                }`}>
                                  {doc.embedding_percentage.toFixed(0)}%
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    deleteDocument(doc.id, doc.filename)
                                  }}
                                  className="p-2 text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                  title="Delete document and all embeddings"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                        {dbDocuments.length === 0 && (
                          <p className="text-slate-500 dark:text-slate-400 text-center py-8">
                            No documents found
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Document Chunks Detail */}
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                          Document Chunks
                        </h2>
                        {selectedDocument && (
                          <div className="mt-2">
                            <p className="text-sm text-slate-600 dark:text-slate-400 font-mono">
                              {selectedDocument.filename}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                              Document ID: {selectedDocument.id}
                            </p>
                            {selectedDocument.session_ids.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs text-slate-600 dark:text-slate-400">Associated Sessions:</p>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {selectedDocument.session_ids.map((sessionId, idx) => (
                                    <span
                                      key={idx}
                                      className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded"
                                    >
                                      {sessionId}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="p-6 max-h-[700px] overflow-y-auto">
                        {selectedDocument ? (
                          <div className="space-y-3">
                            {documentChunks.map((chunk) => (
                              <div
                                key={chunk.id}
                                className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
                              >
                                <div
                                  onClick={() => setExpandedChunk(expandedChunk === chunk.id ? null : chunk.id)}
                                  className="px-4 py-3 bg-slate-50 dark:bg-slate-900 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                      <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                        Chunk {chunk.chunk_index}
                                      </span>
                                      <span className="text-xs text-slate-500 dark:text-slate-400">
                                        {chunk.content_length} chars
                                      </span>
                                      {chunk.has_embedding ? (
                                        <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded-full">
                                          {chunk.embedding_dimensions}D embedding
                                        </span>
                                      ) : (
                                        <span className="text-xs bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 px-2 py-1 rounded-full">
                                          No embedding
                                        </span>
                                      )}
                                    </div>
                                    {expandedChunk === chunk.id ? (
                                      <ChevronUp className="w-4 h-4 text-slate-500" />
                                    ) : (
                                      <ChevronDown className="w-4 h-4 text-slate-500" />
                                    )}
                                  </div>
                                </div>
                                {expandedChunk === chunk.id && (
                                  <div className="px-4 py-3 bg-white dark:bg-slate-800">
                                    <p className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono">
                                      {chunk.content}
                                    </p>
                                    {chunk.meta_info && (
                                      <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Metadata:</p>
                                        <pre className="text-xs text-slate-600 dark:text-slate-400 overflow-x-auto">
                                          {JSON.stringify(chunk.meta_info, null, 2)}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                            {documentChunks.length === 0 && (
                              <p className="text-slate-500 dark:text-slate-400 text-center py-8">
                                No chunks found for this document
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className="text-slate-500 dark:text-slate-400 text-center py-8">
                            Select a document to view its chunks
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}
