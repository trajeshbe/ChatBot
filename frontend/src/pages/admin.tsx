import { useState, useEffect } from 'react'
import Head from 'next/head'
import { Users, Activity, Database, TrendingUp, Search, Filter, ChevronDown, ChevronUp } from 'lucide-react'

interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
  last_login: string | null
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

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'users' | 'sessions' | 'audit' | 'metrics'>('users')
  const [users, setUsers] = useState<User[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [metrics, setMetrics] = useState<UsageMetric[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [sessionDetails, setSessionDetails] = useState<any>(null)
  const [expandedLog, setExpandedLog] = useState<string | null>(null)

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
      }
    } catch (error) {
      console.error('Error loading data:', error)
    }
    setLoading(false)
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

  const filteredAuditLogs = auditLogs.filter(log => {
    if (actionFilter && log.action !== actionFilter) return false
    if (userFilter && log.user_id !== userFilter) return false
    return true
  })

  return (
    <>
      <Head>
        <title>Admin Dashboard - Enterprise RAG Chatbot</title>
        <meta name="description" content="Admin dashboard for user and activity management" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
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
              <a
                href="/"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Back to Chat
              </a>
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
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Created
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            Last Login
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
                              {formatDate(user.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                              {user.last_login ? formatDate(user.last_login) : 'Never'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
            </>
          )}
        </div>
      </div>
    </>
  )
}
