import React, { useState, useEffect } from 'react';
import {
  Play, Pause, StopCircle, Trash2, Copy, Edit, BarChart3,
  Filter, Search, Calendar, Users, Zap, Clock, CheckCircle,
  XCircle, AlertTriangle, RefreshCw, Download, Upload, Settings
} from 'lucide-react';
import JobManager from './JobManager';

/**
 * TrainingJobsManagerEnhanced - Enterprise Job Management
 *
 * Features:
 * - Comprehensive job grid with sorting/filtering
 * - Bulk operations (cancel, delete, clone)
 * - Job comparison and analytics
 * - Integration with sandbox and GPU pool
 * - Real-time status updates
 * - Simple/Advanced modes for PMs and ML Engineers
 */

interface Job {
  id: string;
  name: string;
  dataset_id: string;
  dataset_name: string;
  base_model: string;
  finetuning_method: string;
  training_objective: string;
  quantization: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_epoch: number | null;
  current_step: number | null;
  total_steps: number | null;
  train_loss: number | null;
  eval_loss: number | null;
  hyperparameters: any;
  gpu_type: string | null;
  gpu_count: number | null;
  training_time_seconds: number | null;
  created_at: string;
  created_by: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  celery_task_id: string | null;
}

interface TrainingJobsManagerProps {
  userRole: string;
}

export default function TrainingJobsManagerEnhanced({ userRole }: TrainingJobsManagerProps) {
  const [view, setView] = useState<'grid' | 'create'>('grid');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [methodFilter, setMethodFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'created_at' | 'status' | 'progress'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [jobDetailsView, setJobDetailsView] = useState<Job | null>(null);

  // Fetch jobs
  const fetchJobs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await fetch('http://localhost:8000/api/v1/finetuning/jobs', {
        headers
      });

      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  // Filter and sort jobs
  useEffect(() => {
    let filtered = [...jobs];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(job =>
        job.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.base_model.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(job => job.status === statusFilter);
    }

    // Method filter
    if (methodFilter !== 'all') {
      filtered = filtered.filter(job => job.finetuning_method === methodFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal: any = a[sortBy];
      let bVal: any = b[sortBy];

      if (sortBy === 'created_at' && aVal && bVal) {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    setFilteredJobs(filtered);
  }, [jobs, searchTerm, statusFilter, methodFilter, sortBy, sortOrder]);

  // Bulk actions
  const handleBulkCancel = async () => {
    if (!confirm(`Cancel ${selectedJobs.size} job(s)?`)) return;

    for (const jobId of selectedJobs) {
      try {
        const token = localStorage.getItem('access_token');
        const headers = token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : {};

        await fetch(`http://localhost:8000/api/v1/finetuning/jobs/${jobId}/cancel`, {
          method: 'POST',
          headers,
          body: JSON.stringify({})
        });
      } catch (error) {
        console.error(`Error cancelling job ${jobId}:`, error);
      }
    }

    setSelectedJobs(new Set());
    await fetchJobs();
  };

  // Clone job
  const handleClone = (job: Job) => {
    // TODO: Implement job cloning
    alert(`Cloning job: ${job.name} (To be implemented)`);
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    const badges = {
      pending: { icon: Clock, color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', label: 'Pending' },
      queued: { icon: Clock, color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', label: 'Queued' },
      running: { icon: Zap, color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', label: 'Running' },
      completed: { icon: CheckCircle, color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', label: 'Completed' },
      failed: { icon: XCircle, color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', label: 'Failed' },
      cancelled: { icon: StopCircle, color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', label: 'Cancelled' },
    };

    const badge = badges[status as keyof typeof badges] || badges.pending;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3 h-3" />
        {badge.label}
      </span>
    );
  };

  // Format duration
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (view === 'create') {
    return (
      <div className="p-6">
        <div className="mb-4">
          <button
            onClick={() => setView('grid')}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            ← Back to Jobs
          </button>
        </div>
        <JobManager onRefresh={() => {
          setView('grid');
          fetchJobs();
        }} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Training Jobs</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Manage fine-tuning jobs with Simple/Advanced modes
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchJobs}
            disabled={loading}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Refresh jobs"
          >
            <RefreshCw className={`w-5 h-5 text-gray-600 dark:text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setView('create')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Create New Job
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>

          {/* Method Filter */}
          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="all">All Methods</option>
            <option value="peft">PEFT (LoRA/QLoRA)</option>
            <option value="sft">SFT</option>
            <option value="rlhf-ppo">RLHF-PPO</option>
            <option value="rlhf-grpo">RLHF-GRPO</option>
          </select>

          {/* Sort */}
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [by, order] = e.target.value.split('-');
              setSortBy(by as any);
              setSortOrder(order as any);
            }}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="status-asc">Status A-Z</option>
            <option value="progress-desc">Progress High-Low</option>
          </select>
        </div>

        {/* Bulk Actions */}
        {selectedJobs.size > 0 && (
          <div className="mt-4 flex items-center gap-3 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {selectedJobs.size} job(s) selected
            </span>
            <button
              onClick={handleBulkCancel}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
            >
              Cancel Selected
            </button>
            <button
              onClick={() => setSelectedJobs(new Set())}
              className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white text-sm rounded-lg transition-colors"
            >
              Clear Selection
            </button>
          </div>
        )}
      </div>

      {/* Jobs Grid */}
      {loading && jobs.length === 0 ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Zap className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            {jobs.length === 0 ? 'No training jobs yet. Create your first job!' : 'No jobs match your filters'}
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={filteredJobs.length > 0 && selectedJobs.size === filteredJobs.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedJobs(new Set(filteredJobs.map(j => j.id)));
                        } else {
                          setSelectedJobs(new Set());
                        }
                      }}
                      className="rounded border-gray-300 dark:border-gray-600"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Job Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Method</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Progress</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Loss</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Duration</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Created</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredJobs.map(job => (
                  <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedJobs.has(job.id)}
                        onChange={(e) => {
                          const newSelected = new Set(selectedJobs);
                          if (e.target.checked) {
                            newSelected.add(job.id);
                          } else {
                            newSelected.delete(job.id);
                          }
                          setSelectedJobs(newSelected);
                        }}
                        className="rounded border-gray-300 dark:border-gray-600"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">{job.name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">{job.base_model}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(job.status)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-900 dark:text-white uppercase">{job.finetuning_method}</span>
                    </td>
                    <td className="px-4 py-3">
                      {job.status === 'running' ? (
                        <div className="w-24">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs text-gray-600 dark:text-gray-400">{Math.round(job.progress)}%</span>
                          </div>
                          <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-600 transition-all duration-300"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500 dark:text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {job.train_loss !== null && job.train_loss !== undefined ? (
                        <span className="text-sm font-mono text-gray-900 dark:text-white">{job.train_loss.toFixed(4)}</span>
                      ) : (
                        <span className="text-sm text-gray-500 dark:text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-900 dark:text-white">{formatDuration(job.training_time_seconds)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {new Date(job.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        {job.status === 'running' && (
                          <button
                            onClick={() => {/* TODO: Cancel job */}}
                            className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
                            title="Cancel job"
                          >
                            <StopCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                          </button>
                        )}
                        <button
                          onClick={() => handleClone(job)}
                          className="p-1.5 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-colors"
                          title="Clone job"
                        >
                          <Copy className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </button>
                        <button
                          onClick={() => setJobDetailsView(job)}
                          className="p-1.5 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded transition-colors"
                          title="View details"
                        >
                          <BarChart3 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Stats Footer */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Jobs', value: jobs.length, color: 'bg-gray-100 dark:bg-gray-700' },
          { label: 'Running', value: jobs.filter(j => j.status === 'running').length, color: 'bg-blue-100 dark:bg-blue-900/30' },
          { label: 'Completed', value: jobs.filter(j => j.status === 'completed').length, color: 'bg-green-100 dark:bg-green-900/30' },
          { label: 'Failed', value: jobs.filter(j => j.status === 'failed').length, color: 'bg-red-100 dark:bg-red-900/30' },
        ].map((stat, idx) => (
          <div key={idx} className={`p-4 rounded-lg ${stat.color}`}>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">{stat.label}</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Job Details Modal */}
      {jobDetailsView && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Job Details: {jobDetailsView.name}
                </h3>
                <button
                  onClick={() => setJobDetailsView(null)}
                  className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Status & Progress */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">Status</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Status</p>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(jobDetailsView.status)}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Progress</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {Math.round(jobDetailsView.progress || 0)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Model Configuration */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">Model Configuration</h4>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Base Model:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">{jobDetailsView.base_model}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Method:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white uppercase">{jobDetailsView.finetuning_method}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Objective:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white capitalize">{jobDetailsView.training_objective}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Quantization:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">{jobDetailsView.quantization}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Dataset:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">{jobDetailsView.dataset_name || 'N/A'}</span>
                    </div>
                    {jobDetailsView.gpu_type && (
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">GPU:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">{jobDetailsView.gpu_type} x{jobDetailsView.gpu_count}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Hyperparameters */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">Hyperparameters</h4>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto font-mono">
                    {JSON.stringify(jobDetailsView.hyperparameters, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Training Progress (Running/Completed only) */}
              {(jobDetailsView.status === 'running' || jobDetailsView.status === 'completed') && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">Training Progress</h4>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {jobDetailsView.current_epoch !== null && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Current Epoch:</span>
                          <span className="ml-2 font-medium text-gray-900 dark:text-white">{jobDetailsView.current_epoch}</span>
                        </div>
                      )}
                      {jobDetailsView.current_step !== null && jobDetailsView.total_steps !== null && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Steps:</span>
                          <span className="ml-2 font-medium text-gray-900 dark:text-white">
                            {jobDetailsView.current_step} / {jobDetailsView.total_steps}
                          </span>
                        </div>
                      )}
                      {jobDetailsView.train_loss !== null && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Training Loss:</span>
                          <span className="ml-2 font-medium font-mono text-gray-900 dark:text-white">{jobDetailsView.train_loss.toFixed(4)}</span>
                        </div>
                      )}
                      {jobDetailsView.eval_loss !== null && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Eval Loss:</span>
                          <span className="ml-2 font-medium font-mono text-gray-900 dark:text-white">{jobDetailsView.eval_loss.toFixed(4)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message (Failed only) */}
              {jobDetailsView.status === 'failed' && jobDetailsView.error_message && (
                <div>
                  <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-3 uppercase tracking-wide">Error Message</h4>
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <p className="text-sm text-red-800 dark:text-red-300 font-mono whitespace-pre-wrap">
                      {jobDetailsView.error_message}
                    </p>
                  </div>
                </div>
              )}

              {/* Timestamps */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wide">Timestamps</h4>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Created:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {new Date(jobDetailsView.created_at).toLocaleString()}
                    </span>
                  </div>
                  {jobDetailsView.started_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Started:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {new Date(jobDetailsView.started_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {jobDetailsView.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Completed:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {new Date(jobDetailsView.completed_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {jobDetailsView.training_time_seconds !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Duration:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {formatDuration(jobDetailsView.training_time_seconds)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Created By:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{jobDetailsView.created_by || 'Unknown'}</span>
                  </div>
                  {jobDetailsView.celery_task_id && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Task ID:</span>
                      <span className="font-medium font-mono text-xs text-gray-900 dark:text-white">{jobDetailsView.celery_task_id}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={() => setJobDetailsView(null)}
                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
