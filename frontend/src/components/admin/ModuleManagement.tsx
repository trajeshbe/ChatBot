import { useState, useEffect } from 'react'
import { Settings, ToggleLeft, ToggleRight, Shield, Lock, Layers, Filter, Search } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Module {
  id: string
  name: string
  code: string
  description: string | null
  icon: string | null
  route: string | null
  display_order: number
  is_active: boolean
  is_enabled: boolean
  is_beta: boolean
  requires_special_permission: boolean
  tier: number | null
  category: string | null
  module_type: string | null
  tier_2_dependencies: string[] | null
  created_at: string
  updated_at: string | null
}

export default function ModuleManagement() {
  const [modules, setModules] = useState<Module[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterTier, setFilterTier] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadModules()
  }, [filterTier])

  const loadModules = async () => {
    setLoading(true)
    setError(null)
    try {
      const tierParam = filterTier ? `tier/${filterTier}?enabled_only=false` : ''
      const url = tierParam
        ? `${API_BASE}/api/v1/rbac/modules/${tierParam}`
        : `${API_BASE}/api/v1/rbac/modules?active_only=false`

      const res = await fetch(url)
      if (!res.ok) throw new Error('Failed to load modules')

      const data = await res.json()
      setModules(data.items || data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load modules')
    } finally {
      setLoading(false)
    }
  }

  const toggleModuleEnabled = async (moduleId: string, currentState: boolean) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/rbac/modules/${moduleId}/management`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_enabled: !currentState })
      })

      if (!res.ok) throw new Error('Failed to update module')

      const updatedModule = await res.json()
      setModules(modules.map(m => m.id === moduleId ? updatedModule : m))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update module')
    }
  }

  const toggleModuleBeta = async (moduleId: string, currentState: boolean) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/rbac/modules/${moduleId}/management`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_beta: !currentState })
      })

      if (!res.ok) throw new Error('Failed to update module')

      const updatedModule = await res.json()
      setModules(modules.map(m => m.id === moduleId ? updatedModule : m))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update module')
    }
  }

  const toggleSpecialPermission = async (moduleId: string, currentState: boolean) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/rbac/modules/${moduleId}/management`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requires_special_permission: !currentState })
      })

      if (!res.ok) throw new Error('Failed to update module')

      const updatedModule = await res.json()
      setModules(modules.map(m => m.id === moduleId ? updatedModule : m))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update module')
    }
  }

  const filteredModules = modules.filter(module =>
    module.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    module.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (module.category && module.category.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const groupedModules = filteredModules.reduce((acc, module) => {
    const tier = module.tier || 0
    if (!acc[tier]) acc[tier] = []
    acc[tier].push(module)
    return acc
  }, {} as Record<number, Module[]>)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Module Management</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Enable/disable modules and manage access permissions
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search modules..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400"
              />
            </div>
          </div>

          {/* Tier Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={filterTier || ''}
              onChange={(e) => setFilterTier(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
            >
              <option value="">All Tiers</option>
              <option value="1">Tier 1</option>
              <option value="2">Tier 2</option>
              <option value="3">Tier 3</option>
            </select>
          </div>
        </div>
      </div>

      {/* Module Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Total Modules</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{modules.length}</p>
            </div>
            <Layers className="h-8 w-8 text-primary-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Enabled</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {modules.filter(m => m.is_enabled).length}
              </p>
            </div>
            <ToggleRight className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Beta Features</p>
              <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                {modules.filter(m => m.is_beta).length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Restricted</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {modules.filter(m => m.requires_special_permission).length}
              </p>
            </div>
            <Lock className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Modules by Tier */}
      {Object.keys(groupedModules).sort((a, b) => parseInt(a) - parseInt(b)).map(tierKey => {
        const tier = parseInt(tierKey)
        const tierModules = groupedModules[tier]
        const tierName = tier === 1 ? 'Core Platform' : tier === 2 ? 'Domain Verticals' : tier === 3 ? 'Customer Solutions' : `Tier ${tier}`

        return (
          <div key={tier} className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-primary-500" />
              {tierName} ({tierModules.length} modules)
            </h3>

            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
              <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                <thead className="bg-slate-50 dark:bg-slate-900/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Module
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Enabled
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Beta
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Restricted
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {tierModules.map((module) => (
                    <tr key={module.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-slate-900 dark:text-white">
                            {module.name}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            {module.code}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {module.category && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300">
                            {module.category}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => toggleModuleEnabled(module.id, module.is_enabled)}
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                            module.is_enabled
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/50'
                              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                          }`}
                        >
                          {module.is_enabled ? (
                            <><ToggleRight className="h-3 w-3 mr-1" /> Enabled</>
                          ) : (
                            <><ToggleLeft className="h-3 w-3 mr-1" /> Disabled</>
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => toggleModuleBeta(module.id, module.is_beta)}
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                            module.is_beta
                              ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/50'
                              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                          }`}
                        >
                          {module.is_beta ? (
                            <><Shield className="h-3 w-3 mr-1" /> Beta</>
                          ) : (
                            <>Stable</>
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => toggleSpecialPermission(module.id, module.requires_special_permission)}
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                            module.requires_special_permission
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/50'
                              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                          }`}
                        >
                          {module.requires_special_permission ? (
                            <><Lock className="h-3 w-3 mr-1" /> Restricted</>
                          ) : (
                            <>Open</>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}
