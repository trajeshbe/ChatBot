/**
 * Scraping Configuration Manager Component
 *
 * Manages domain-specific scraping policies and compliance:
 * - Domain whitelist/blacklist configuration
 * - Robots.txt compliance settings
 * - Rate limiting per domain
 * - API integration for sites with official APIs
 * - Scraping audit logs and statistics
 */

import React, { useState, useEffect } from 'react';
import {
  Globe,
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  Plus,
  Edit2,
  Trash2,
  BarChart3,
  FileText,
  AlertCircle,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ScrapingConfig {
  id: string;
  domain: string;
  allow_scraping: boolean;
  robots_txt_compliant: boolean;
  rate_limit_requests_per_minute: number;
  rate_limit_delay_seconds: number;
  use_api: boolean;
  api_endpoint?: string;
  preferred_method: string;
  status: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

interface DomainStats {
  domain: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  blocked_requests: number;
  total_bytes_downloaded: number;
  avg_response_time_ms?: number;
  rate_limit_violations: number;
  robots_txt_violations: number;
  first_scraped_at?: string;
  last_scraped_at?: string;
}

interface AuditLog {
  id: string;
  domain: string;
  url: string;
  method?: string;
  status_code?: number;
  success: boolean;
  robots_txt_allowed?: boolean;
  rate_limit_respected?: boolean;
  created_at: string;
}

export const ScrapingConfigManager: React.FC = () => {
  const [configs, setConfigs] = useState<ScrapingConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<ScrapingConfig | null>(null);
  const [domainStats, setDomainStats] = useState<DomainStats | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'configs' | 'stats' | 'audit'>('configs');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState<Partial<ScrapingConfig>>({
    domain: '',
    allow_scraping: false,
    robots_txt_compliant: true,
    rate_limit_requests_per_minute: 10,
    rate_limit_delay_seconds: 2.0,
    use_api: false,
    preferred_method: 'auto',
    notes: ''
  });

  useEffect(() => {
    loadConfigs();
  }, [statusFilter]);

  useEffect(() => {
    if (activeView === 'audit') {
      loadAuditLogs();
    }
  }, [activeView]);

  const loadConfigs = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);

      const res = await fetch(`${API_BASE}/api/v1/admin/scraping-configs?${params}`);
      if (res.ok) {
        const data = await res.json();
        setConfigs(data);
      } else {
        throw new Error('Failed to load configurations');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadDomainStats = async (domain: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/domain-statistics/${domain}`);
      if (res.ok) {
        const stats = await res.json();
        setDomainStats(stats);
        setActiveView('stats');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    }
  };

  const loadAuditLogs = async () => {
    try {
      const params = new URLSearchParams({ limit: '100' });
      const res = await fetch(`${API_BASE}/api/v1/admin/scraping-audit-logs?${params}`);
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data.logs || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    }
  };

  const createConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/scraping-configs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        await loadConfigs();
        setShowCreateModal(false);
        resetForm();
      } else {
        throw new Error('Failed to create configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create configuration');
    }
  };

  const updateConfig = async () => {
    if (!selectedConfig) return;

    try {
      // URL-encode domain to handle domains with special characters like "https://example.com"
      const res = await fetch(`${API_BASE}/api/v1/admin/scraping-configs/${encodeURIComponent(selectedConfig.domain)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        await loadConfigs();
        setShowEditModal(false);
        setSelectedConfig(null);
        resetForm();
      } else {
        throw new Error('Failed to update configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update configuration');
    }
  };

  const deleteConfig = async (domain: string) => {
    if (!confirm(`Are you sure you want to delete configuration for ${domain}?`)) return;

    try {
      // URL-encode domain to handle domains with special characters like "https://example.com"
      const res = await fetch(`${API_BASE}/api/v1/admin/scraping-configs/${encodeURIComponent(domain)}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        await loadConfigs();
      } else {
        throw new Error('Failed to delete configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete configuration');
    }
  };

  const resetForm = () => {
    setFormData({
      domain: '',
      allow_scraping: false,
      robots_txt_compliant: true,
      rate_limit_requests_per_minute: 10,
      rate_limit_delay_seconds: 2.0,
      use_api: false,
      preferred_method: 'auto',
      notes: ''
    });
  };

  const openEditModal = (config: ScrapingConfig) => {
    setSelectedConfig(config);
    setFormData({
      allow_scraping: config.allow_scraping,
      robots_txt_compliant: config.robots_txt_compliant,
      rate_limit_requests_per_minute: config.rate_limit_requests_per_minute,
      rate_limit_delay_seconds: config.rate_limit_delay_seconds,
      use_api: config.use_api,
      api_endpoint: config.api_endpoint,
      preferred_method: config.preferred_method,
      status: config.status,
      notes: config.notes
    });
    setShowEditModal(true);
  };

  const filteredConfigs = configs.filter(config =>
    config.domain.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Scraping Configuration & Compliance
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Manage domain-specific scraping policies and track compliance
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={loadConfigs}
            className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Domain</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      {/* View Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <div className="flex space-x-8">
          <button
            onClick={() => setActiveView('configs')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeView === 'configs'
                ? 'border-primary-500 text-primary-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4" />
              <span>Configurations</span>
              <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                {configs.length}
              </span>
            </div>
          </button>
          <button
            onClick={() => setActiveView('stats')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeView === 'stats'
                ? 'border-primary-500 text-primary-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Statistics</span>
            </div>
          </button>
          <button
            onClick={() => setActiveView('audit')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeView === 'audit'
                ? 'border-primary-500 text-primary-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4" />
              <span>Audit Logs</span>
            </div>
          </button>
        </div>
      </div>

      {/* Configurations View */}
      {activeView === 'configs' && (
        <>
          {/* Filters */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search domains..."
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-800 dark:text-white"
                />
              </div>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-800 dark:text-white"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="blocked">Blocked</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>

          {/* Configurations List */}
          <div className="space-y-4">
            {filteredConfigs.map((config) => (
              <div
                key={config.id}
                className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-primary-500 dark:hover:border-primary-500 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <Globe className="w-5 h-5 text-primary-600 dark:text-blue-400" />
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        {config.domain}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        config.allow_scraping
                          ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                          : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                      }`}>
                        {config.allow_scraping ? 'Allowed' : 'Blocked'}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        config.status === 'active'
                          ? 'bg-primary-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                      }`}>
                        {config.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                      <div>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Rate Limit</p>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {config.rate_limit_requests_per_minute} req/min
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Delay</p>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {config.rate_limit_delay_seconds}s
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Method</p>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {config.preferred_method}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Robots.txt</p>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {config.robots_txt_compliant ? (
                            <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 inline" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 inline" />
                          )}
                        </p>
                      </div>
                    </div>

                    {config.notes && (
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                        {config.notes}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => loadDomainStats(config.domain)}
                      className="p-2 text-primary-600 dark:text-blue-400 hover:bg-primary-100 dark:hover:bg-blue-900 rounded-lg"
                      title="View Statistics"
                    >
                      <BarChart3 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => openEditModal(config)}
                      className="p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                      title="Edit"
                    >
                      <Edit2 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => deleteConfig(config.domain)}
                      className="p-2 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 rounded-lg"
                      title="Delete"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {filteredConfigs.length === 0 && (
              <div className="text-center py-12">
                <Globe className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-600 dark:text-slate-400">
                  {searchQuery ? 'No configurations match your search' : 'No configurations yet'}
                </p>
              </div>
            )}
          </div>
        </>
      )}

      {/* Statistics View */}
      {activeView === 'stats' && domainStats && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Statistics for {domainStats.domain}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-primary-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-primary-600 dark:text-blue-400">Total Requests</p>
                <p className="text-2xl font-bold text-primary-900 dark:text-primary-100">{domainStats.total_requests}</p>
              </div>
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm text-green-600 dark:text-green-400">Successful</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">{domainStats.successful_requests}</p>
              </div>
              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400">Failed</p>
                <p className="text-2xl font-bold text-red-900 dark:text-red-100">{domainStats.failed_requests}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                <p className="text-sm text-slate-600 dark:text-slate-400">Rate Limit Violations</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-white">{domainStats.rate_limit_violations}</p>
              </div>
              <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                <p className="text-sm text-slate-600 dark:text-slate-400">Robots.txt Violations</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-white">{domainStats.robots_txt_violations}</p>
              </div>
              <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                <p className="text-sm text-slate-600 dark:text-slate-400">Avg Response Time</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-white">
                  {domainStats.avg_response_time_ms?.toFixed(2) || 'N/A'} ms
                </p>
              </div>
              <div className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                <p className="text-sm text-slate-600 dark:text-slate-400">Total Data Downloaded</p>
                <p className="text-xl font-semibold text-slate-900 dark:text-white">
                  {(domainStats.total_bytes_downloaded / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs View */}
      {activeView === 'audit' && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 dark:bg-slate-800">
              <tr>
                <th className="px-4 py-3 text-left">Domain</th>
                <th className="px-4 py-3 text-left">URL</th>
                <th className="px-4 py-3 text-left">Method</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Compliance</th>
                <th className="px-4 py-3 text-left">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                  <td className="px-4 py-3">{log.domain}</td>
                  <td className="px-4 py-3 max-w-xs truncate" title={log.url}>{log.url}</td>
                  <td className="px-4 py-3">{log.method || 'N/A'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      log.success
                        ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                    }`}>
                      {log.status_code || 'N/A'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex space-x-2">
                      {log.robots_txt_allowed && (
                        <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" title="Robots.txt OK" />
                      )}
                      {log.rate_limit_respected && (
                        <Clock className="w-4 h-4 text-primary-600 dark:text-blue-400" title="Rate limit OK" />
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {auditLogs.length === 0 && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400">No audit logs yet</p>
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                Add Domain Configuration
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Domain
                  </label>
                  <input
                    type="text"
                    value={formData.domain}
                    onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                    placeholder="example.com"
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.allow_scraping}
                      onChange={(e) => setFormData({ ...formData, allow_scraping: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">Allow Scraping</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.robots_txt_compliant}
                      onChange={(e) => setFormData({ ...formData, robots_txt_compliant: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">Robots.txt Compliant</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.use_api}
                      onChange={(e) => setFormData({ ...formData, use_api: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">Use API</span>
                  </label>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Requests per Minute
                    </label>
                    <input
                      type="number"
                      value={formData.rate_limit_requests_per_minute}
                      onChange={(e) => setFormData({ ...formData, rate_limit_requests_per_minute: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Delay (seconds)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.rate_limit_delay_seconds}
                      onChange={(e) => setFormData({ ...formData, rate_limit_delay_seconds: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                </div>

                {formData.use_api && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      API Endpoint
                    </label>
                    <input
                      type="text"
                      value={formData.api_endpoint || ''}
                      onChange={(e) => setFormData({ ...formData, api_endpoint: e.target.value })}
                      placeholder="https://api.example.com/v1"
                      className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Notes
                  </label>
                  <textarea
                    value={formData.notes || ''}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                  />
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setShowCreateModal(false);
                      resetForm();
                    }}
                    className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={createConfig}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Create
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                Edit Configuration: {selectedConfig.domain}
              </h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.allow_scraping}
                      onChange={(e) => setFormData({ ...formData, allow_scraping: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">Allow Scraping</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.robots_txt_compliant}
                      onChange={(e) => setFormData({ ...formData, robots_txt_compliant: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">Robots.txt Compliant</span>
                  </label>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Requests per Minute
                    </label>
                    <input
                      type="number"
                      value={formData.rate_limit_requests_per_minute}
                      onChange={(e) => setFormData({ ...formData, rate_limit_requests_per_minute: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Delay (seconds)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.rate_limit_delay_seconds}
                      onChange={(e) => setFormData({ ...formData, rate_limit_delay_seconds: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Notes
                  </label>
                  <textarea
                    value={formData.notes || ''}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-900 dark:text-white"
                  />
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setShowEditModal(false);
                      setSelectedConfig(null);
                      resetForm();
                    }}
                    className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={updateConfig}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Update
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
