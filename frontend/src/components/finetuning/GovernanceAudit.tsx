import React, { useState, useEffect } from 'react';
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  GitBranch,
  FileText,
  Download,
  Filter,
  ChevronDown,
  ChevronUp,
  AlertCircle
} from 'lucide-react';

interface PendingModel {
  id: string;
  name: string;
  version: string;
  base_model: string;
  finetuning_method: string;
  created_at: string;
  eval_metrics?: Record<string, number>;
}

interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  description: string;
  ip_address: string | null;
  created_at: string;
  details?: any;
}

interface ModelLineage {
  model: {
    id: string;
    name: string;
    version: string;
    status: string;
    base_model: string;
    finetuning_method: string;
    created_at: string;
    eval_metrics?: Record<string, number>;
  };
  training_job: any | null;
  dataset: any | null;
  deployment: any | null;
  approval_history: Array<{
    action: string;
    by: string;
    at: string;
    notes?: string;
    reason?: string;
  }>;
}

export default function GovernanceAudit({ userRole }: { userRole: string }) {
  const [pendingModels, setPendingModels] = useState<PendingModel[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [lineage, setLineage] = useState<ModelLineage | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const [approvalNote, setApprovalNote] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');

  const fetchPendingApprovals = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/finetuning/models-public?status=registered', {
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        const data = await response.json();
        setPendingModels(data.models || []);
      }
    } catch (error) {
      console.error('Error fetching pending approvals:', error);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const url = actionFilter
        ? `http://localhost:8000/api/v1/finetuning/audit/logs-public?action=${actionFilter}&limit=50`
        : 'http://localhost:8000/api/v1/finetuning/audit/logs-public?limit=50';

      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  const fetchLineage = async (modelId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/finetuning/models-public/${modelId}/lineage`,
        { headers: { 'Content-Type': 'application/json' } }
      );
      if (response.ok) {
        const data = await response.json();
        setLineage(data);
      }
    } catch (error) {
      console.error('Error fetching lineage:', error);
    }
  };

  const approveModel = async (modelId: string) => {
    if (!approvalNote) {
      alert('Please provide approval notes');
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/finetuning/models-public/${modelId}/approve`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ approval_notes: approvalNote })
        }
      );

      if (response.ok) {
        alert('Model approved successfully!');
        setApprovalNote('');
        await fetchPendingApprovals();
        await fetchAuditLogs();
      } else {
        const error = await response.json();
        alert(`Failed to approve: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error approving model:', error);
      alert('Failed to approve model');
    }
  };

  const rejectModel = async (modelId: string) => {
    if (!rejectionReason) {
      alert('Please provide rejection reason');
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/finetuning/models-public/${modelId}/reject`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ rejection_reason: rejectionReason })
        }
      );

      if (response.ok) {
        alert('Model rejected');
        setRejectionReason('');
        await fetchPendingApprovals();
        await fetchAuditLogs();
      } else {
        const error = await response.json();
        alert(`Failed to reject: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error rejecting model:', error);
      alert('Failed to reject model');
    }
  };

  const downloadComplianceReport = async (modelId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/finetuning/models-public/${modelId}/lineage`,
        { headers: { 'Content-Type': 'application/json' } }
      );

      if (response.ok) {
        const data = await response.json();

        // Generate compliance report as JSON
        const report = {
          report_type: 'Model Compliance Report',
          generated_at: new Date().toISOString(),
          model: data.model,
          training_provenance: data.training_job,
          data_source: data.dataset,
          deployment_info: data.deployment,
          approval_chain: data.approval_history
        };

        // Download as JSON file
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${data.model.name}-${data.model.version}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchPendingApprovals(), fetchAuditLogs()]);
      setLoading(false);
    };
    loadData();
  }, []);

  useEffect(() => {
    fetchAuditLogs();
  }, [actionFilter]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Shield className="w-6 h-6 text-indigo-600" />
        <h2 className="text-2xl font-bold">Governance & Audit</h2>
      </div>

      {/* Pending Approvals */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-orange-600" />
            <h3 className="text-lg font-semibold">Pending Model Approvals</h3>
            <span className="ml-2 bg-orange-100 text-orange-800 px-2 py-1 rounded text-sm font-semibold">
              {pendingModels.length}
            </span>
          </div>
        </div>
        <div className="p-6">
          {pendingModels.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No models pending approval</p>
          ) : (
            <div className="space-y-4">
              {pendingModels.map((model) => (
                <div key={model.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-semibold text-lg">{model.name}</h4>
                      <p className="text-sm text-gray-600">v{model.version} • {model.base_model}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Registered: {new Date(model.created_at).toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedModel(model.id);
                        fetchLineage(model.id);
                      }}
                      className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      <GitBranch className="w-4 h-4" />
                      View Lineage
                    </button>
                  </div>

                  {/* Evaluation Metrics */}
                  {model.eval_metrics && (
                    <div className="bg-gray-50 rounded p-3 mb-4">
                      <p className="text-xs font-semibold text-gray-700 mb-2">Evaluation Metrics</p>
                      <div className="grid grid-cols-3 gap-2">
                        {Object.entries(model.eval_metrics).slice(0, 6).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="text-gray-600">{key}:</span>{' '}
                            <span className="font-semibold">
                              {typeof value === 'number' && value < 1
                                ? `${(value * 100).toFixed(1)}%`
                                : typeof value === 'number'
                                ? value.toFixed(2)
                                : value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Approval Actions */}
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Approval Notes (required)
                      </label>
                      <textarea
                        value={approvalNote}
                        onChange={(e) => setApprovalNote(e.target.value)}
                        className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                        rows={2}
                        placeholder="Provide approval notes or feedback..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => approveModel(model.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => {
                          const reason = prompt('Rejection reason:');
                          if (reason) {
                            setRejectionReason(reason);
                            rejectModel(model.id);
                          }
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Model Lineage Viewer */}
      {lineage && (
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-semibold">Model Lineage: {lineage.model.name}</h3>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => downloadComplianceReport(lineage.model.id)}
                className="flex items-center gap-2 px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
              >
                <Download className="w-4 h-4" />
                Download Report
              </button>
              <button
                onClick={() => setLineage(null)}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
          <div className="p-6">
            {/* Lineage Flow Diagram */}
            <div className="flex items-center justify-between mb-6">
              {/* Dataset */}
              <div className="flex-1 text-center">
                <div className={`mx-auto w-24 h-24 rounded-lg flex items-center justify-center ${
                  lineage.dataset ? 'bg-blue-100 border-2 border-blue-500' : 'bg-gray-100 border-2 border-gray-300'
                }`}>
                  <FileText className={`w-12 h-12 ${lineage.dataset ? 'text-blue-600' : 'text-gray-400'}`} />
                </div>
                <p className="mt-2 font-semibold text-sm">Dataset</p>
                {lineage.dataset && (
                  <p className="text-xs text-gray-600">{lineage.dataset.name}</p>
                )}
              </div>

              <div className="flex-shrink-0 text-gray-400">→</div>

              {/* Training Job */}
              <div className="flex-1 text-center">
                <div className={`mx-auto w-24 h-24 rounded-lg flex items-center justify-center ${
                  lineage.training_job ? 'bg-green-100 border-2 border-green-500' : 'bg-gray-100 border-2 border-gray-300'
                }`}>
                  <Clock className={`w-12 h-12 ${lineage.training_job ? 'text-green-600' : 'text-gray-400'}`} />
                </div>
                <p className="mt-2 font-semibold text-sm">Training</p>
                {lineage.training_job && (
                  <p className="text-xs text-gray-600">{lineage.training_job.name}</p>
                )}
              </div>

              <div className="flex-shrink-0 text-gray-400">→</div>

              {/* Model */}
              <div className="flex-1 text-center">
                <div className="mx-auto w-24 h-24 rounded-lg bg-purple-100 border-2 border-purple-500 flex items-center justify-center">
                  <Shield className="w-12 h-12 text-purple-600" />
                </div>
                <p className="mt-2 font-semibold text-sm">Model</p>
                <p className="text-xs text-gray-600">v{lineage.model.version}</p>
              </div>

              <div className="flex-shrink-0 text-gray-400">→</div>

              {/* Deployment */}
              <div className="flex-1 text-center">
                <div className={`mx-auto w-24 h-24 rounded-lg flex items-center justify-center ${
                  lineage.deployment ? 'bg-orange-100 border-2 border-orange-500' : 'bg-gray-100 border-2 border-gray-300'
                }`}>
                  <CheckCircle className={`w-12 h-12 ${lineage.deployment ? 'text-orange-600' : 'text-gray-400'}`} />
                </div>
                <p className="mt-2 font-semibold text-sm">Deployment</p>
                {lineage.deployment && (
                  <p className="text-xs text-gray-600">{lineage.deployment.deployment_target}</p>
                )}
              </div>
            </div>

            {/* Detailed Information */}
            <div className="grid grid-cols-2 gap-4 mt-6">
              {lineage.dataset && (
                <div className="bg-blue-50 rounded p-4">
                  <h4 className="font-semibold text-sm mb-2">Dataset Details</h4>
                  <div className="space-y-1 text-xs">
                    <p><strong>Format:</strong> {lineage.dataset.format_type}</p>
                    <p><strong>Rows:</strong> {lineage.dataset.rows_count}</p>
                    <p><strong>Valid:</strong> {lineage.dataset.is_valid ? '✅ Yes' : '❌ No'}</p>
                    <p><strong>Uploaded:</strong> {new Date(lineage.dataset.uploaded_at).toLocaleDateString()}</p>
                  </div>
                </div>
              )}

              {lineage.training_job && (
                <div className="bg-green-50 rounded p-4">
                  <h4 className="font-semibold text-sm mb-2">Training Job Details</h4>
                  <div className="space-y-1 text-xs">
                    <p><strong>Status:</strong> {lineage.training_job.status}</p>
                    <p><strong>GPU:</strong> {lineage.training_job.gpu_allocated || 'N/A'}</p>
                    <p><strong>Steps:</strong> {lineage.training_job.current_step}/{lineage.training_job.total_steps}</p>
                    {lineage.training_job.completed_at && (
                      <p><strong>Completed:</strong> {new Date(lineage.training_job.completed_at).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Approval History */}
            {lineage.approval_history.length > 0 && (
              <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded p-4">
                <h4 className="font-semibold text-sm mb-2">Approval History</h4>
                <div className="space-y-2">
                  {lineage.approval_history.map((approval, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs">
                      {approval.action === 'approved' ? (
                        <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        <p className="font-semibold">
                          {approval.action.charAt(0).toUpperCase() + approval.action.slice(1)} by {approval.by}
                        </p>
                        <p className="text-gray-600">{new Date(approval.at).toLocaleString()}</p>
                        {approval.notes && <p className="text-gray-700 mt-1">Notes: {approval.notes}</p>}
                        {approval.reason && <p className="text-gray-700 mt-1">Reason: {approval.reason}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Trail */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold">Audit Trail</h3>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value="">All Actions</option>
                <option value="create">Create</option>
                <option value="update">Update</option>
                <option value="delete">Delete</option>
                <option value="approve">Approve</option>
                <option value="reject">Reject</option>
                <option value="deploy">Deploy</option>
              </select>
            </div>
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {auditLogs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No audit logs found</p>
          ) : (
            auditLogs.map((log) => (
              <div key={log.id} className="px-6 py-4 hover:bg-gray-50">
                <div
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <ActionIcon action={log.action} />
                      <span className="font-semibold text-sm">{log.description}</span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-600">
                      <span>{new Date(log.created_at).toLocaleString()}</span>
                      <span>•</span>
                      <span className="bg-gray-100 px-2 py-0.5 rounded">{log.action}</span>
                      <span className="bg-gray-100 px-2 py-0.5 rounded">{log.resource_type}</span>
                    </div>
                  </div>
                  {expandedLog === log.id ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>

                {expandedLog === log.id && log.details && (
                  <div className="mt-3 bg-gray-50 rounded p-3">
                    <pre className="text-xs text-gray-700 overflow-x-auto">
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// Helper component for action icons
function ActionIcon({ action }: { action: string }) {
  switch (action.toLowerCase()) {
    case 'approve':
      return <CheckCircle className="w-4 h-4 text-green-600" />;
    case 'reject':
      return <XCircle className="w-4 h-4 text-red-600" />;
    case 'create':
      return <FileText className="w-4 h-4 text-blue-600" />;
    case 'delete':
      return <XCircle className="w-4 h-4 text-red-600" />;
    case 'deploy':
      return <CheckCircle className="w-4 h-4 text-purple-600" />;
    default:
      return <AlertCircle className="w-4 h-4 text-gray-600" />;
  }
}
