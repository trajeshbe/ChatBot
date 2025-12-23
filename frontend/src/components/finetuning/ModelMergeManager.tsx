/**
 * Model Merge Manager
 *
 * Manages LoRA adapter merging workflow:
 * 1. View adapter-only models
 * 2. Request merge (LoRA + Base Model)
 * 3. Monitor merge progress
 * 4. View merged model status
 * 5. Proceed to approval & deployment
 */

import React, { useState, useEffect } from 'react';
import {
  GitMerge,
  PlayCircle,
  CheckCircle,
  XCircle,
  Clock,
  Loader,
  AlertTriangle,
  FileBox,
  ExternalLink,
  Rocket,
  Info,
  TrendingUp
} from 'lucide-react';

interface MergeStatus {
  model_id: string;
  status: string;  // adapter_only, merging, merged, merge_failed, deployed
  merged_model_path?: string;
  merge_duration_seconds?: number;
  merge_requested_at?: string;
  merge_error_message?: string;
}

interface Model {
  id: string;
  name: string;
  version?: string;
  status: string;
  base_model: string;
  finetuning_method?: string;
  minio_checkpoint_path?: string;
  merged_model_path?: string;
  merge_duration_seconds?: number;
  merge_requested_at?: string;
  merge_error_message?: string;
  job_id?: string;
}

interface ModelMergeManagerProps {
  models: Model[];
  onRefresh?: () => void;
}

export default function ModelMergeManager({ models, onRefresh }: ModelMergeManagerProps) {
  const [mergeStatuses, setMergeStatuses] = useState<Map<string, MergeStatus>>(new Map());
  const [mergingModels, setMergingModels] = useState<Set<string>>(new Set());
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const MINIO_CONSOLE = process.env.NEXT_PUBLIC_MINIO_CONSOLE_URL || 'http://localhost:9001';

  // Filter models that can be merged (adapter_only, merging, merged, merge_failed)
  const mergeableModels = models.filter(m =>
    ['adapter_only', 'merging', 'merged', 'merge_failed', 'registered'].includes(m.status)
  );

  useEffect(() => {
    // Poll merge status for models in 'merging' state
    const mergingIds = mergeableModels
      .filter(m => m.status === 'merging')
      .map(m => m.id);

    if (mergingIds.length > 0) {
      const interval = setInterval(() => {
        mergingIds.forEach(id => fetchMergeStatus(id));
      }, 5000); // Poll every 5 seconds

      setPollingInterval(interval);
      return () => clearInterval(interval);
    } else if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  }, [mergeableModels]);

  const fetchMergeStatus = async (modelId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/merge-status`, {
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data: MergeStatus = await response.json();
        setMergeStatuses(prev => new Map(prev).set(modelId, data));

        // If merge completed or failed, refresh models list
        if (data.status === 'merged' || data.status === 'merge_failed') {
          if (onRefresh) onRefresh();
        }
      }
    } catch (error) {
      console.error('Error fetching merge status:', error);
    }
  };

  const requestMerge = async (modelId: string, modelName: string, baseModel: string) => {
    if (!confirm(`Merge LoRA adapter with base model?\n\nModel: ${modelName}\nBase: ${baseModel}\n\nThis will take 5-15 minutes.`)) {
      return;
    }

    try {
      setMergingModels(prev => new Set(prev).add(modelId));

      const response = await fetch(`${API_BASE}/api/v1/finetuning/models/${modelId}/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_model_name: baseModel,
          force_cpu: false
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`✅ Merge started!\n\nTask ID: ${data.task_id}\nEstimated time: 5-15 minutes\n\nStatus will update automatically.`);

        // Start polling for this model
        setTimeout(() => fetchMergeStatus(modelId), 2000);
        if (onRefresh) onRefresh();
      } else {
        const error = await response.json();
        alert(`❌ Merge failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error requesting merge:', error);
      alert('Failed to start merge');
    } finally {
      setMergingModels(prev => {
        const updated = new Set(prev);
        updated.delete(modelId);
        return updated;
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
      adapter_only: {
        color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        icon: <FileBox className="w-4 h-4 inline mr-1" />,
        label: 'Adapter Only'
      },
      merging: {
        color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        icon: <Loader className="w-4 h-4 inline mr-1 animate-spin" />,
        label: 'Merging...'
      },
      merged: {
        color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        icon: <CheckCircle className="w-4 h-4 inline mr-1" />,
        label: 'Merged'
      },
      merge_failed: {
        color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        icon: <XCircle className="w-4 h-4 inline mr-1" />,
        label: 'Merge Failed'
      },
      registered: {
        color: 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200',
        icon: <Clock className="w-4 h-4 inline mr-1" />,
        label: 'Registered'
      }
    };

    const config = configs[status] || configs.registered;

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        {config.icon}
        {config.label}
      </span>
    );
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const canMerge = (model: Model) => {
    return ['adapter_only', 'registered', 'merge_failed'].includes(model.status);
  };

  const canDeploy = (model: Model) => {
    return model.status === 'merged';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <GitMerge className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Model Merge Manager</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Merge LoRA adapters with base models for deployment
            </p>
          </div>
        </div>
        <div className="text-sm text-slate-600 dark:text-slate-400">
          <TrendingUp className="w-4 h-4 inline mr-1" />
          {mergeableModels.length} Model{mergeableModels.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">Merge Workflow</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-700 dark:text-blue-300">
              <li>Request merge to combine LoRA adapter with base model</li>
              <li>Wait 5-15 minutes for merge to complete</li>
              <li>Once merged, request approval for deployment</li>
              <li>Admin approves, then deploy to Ollama</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Models Grid */}
      {mergeableModels.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
          <GitMerge className="w-16 h-16 mx-auto text-slate-400 dark:text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">No Models to Merge</h3>
          <p className="text-slate-600 dark:text-slate-400">
            Complete a fine-tuning job to see models here
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {mergeableModels.map((model) => {
            const mergeStatus = mergeStatuses.get(model.id);
            const currentStatus = mergeStatus?.status || model.status;

            return (
              <div
                key={model.id}
                className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                      {model.name}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {model.version || 'v1.0'} • {model.finetuning_method || 'LoRA'}
                    </p>
                  </div>
                  {getStatusBadge(currentStatus)}
                </div>

                {/* Base Model */}
                <div className="mb-4 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Base Model</p>
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {model.base_model}
                  </p>
                </div>

                {/* Adapter Checkpoint */}
                {model.minio_checkpoint_path && (
                  <div className="mb-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">LoRA Adapter</p>
                        <p className="text-sm font-medium text-indigo-900 dark:text-indigo-200 truncate">
                          {model.minio_checkpoint_path.split('/').pop()}
                        </p>
                      </div>
                      <a
                        href={`${MINIO_CONSOLE}/browser/${model.minio_checkpoint_path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 ml-2"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                )}

                {/* Merge Info */}
                {currentStatus === 'merging' && (
                  <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                    <div className="flex items-center gap-2 mb-2">
                      <Loader className="w-4 h-4 text-yellow-600 dark:text-yellow-400 animate-spin" />
                      <p className="text-sm font-medium text-yellow-900 dark:text-yellow-200">
                        Merge in progress...
                      </p>
                    </div>
                    <p className="text-xs text-yellow-700 dark:text-yellow-300">
                      Started: {formatTimestamp(model.merge_requested_at || mergeStatus?.merge_requested_at)}
                    </p>
                    <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                      Estimated completion: 5-15 minutes
                    </p>
                  </div>
                )}

                {currentStatus === 'merged' && (
                  <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <p className="text-sm font-medium text-green-900 dark:text-green-200">
                        Merge completed successfully
                      </p>
                    </div>
                    <div className="space-y-1 text-xs text-green-700 dark:text-green-300">
                      <p>Duration: {formatDuration(model.merge_duration_seconds || mergeStatus?.merge_duration_seconds)}</p>
                      <p className="truncate">Path: {model.merged_model_path || mergeStatus?.merged_model_path || 'N/A'}</p>
                    </div>
                  </div>
                )}

                {currentStatus === 'merge_failed' && (
                  <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                    <div className="flex items-center gap-2 mb-2">
                      <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                      <p className="text-sm font-medium text-red-900 dark:text-red-200">
                        Merge failed
                      </p>
                    </div>
                    <p className="text-xs text-red-700 dark:text-red-300">
                      {model.merge_error_message || mergeStatus?.merge_error_message || 'Unknown error'}
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="space-y-2 pt-4 border-t border-slate-200 dark:border-slate-700">
                  {canMerge(model) && (
                    <button
                      onClick={() => requestMerge(model.id, model.name, model.base_model)}
                      disabled={mergingModels.has(model.id)}
                      className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
                    >
                      {mergingModels.has(model.id) ? (
                        <>
                          <Loader className="w-4 h-4 animate-spin" />
                          Starting Merge...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="w-4 h-4" />
                          Request Merge
                        </>
                      )}
                    </button>
                  )}

                  {canDeploy(model) && (
                    <div className="flex items-center justify-center gap-2 text-sm text-green-700 dark:text-green-300">
                      <CheckCircle className="w-4 h-4" />
                      Ready for approval & deployment
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
