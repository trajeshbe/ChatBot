import React, { useState, useEffect } from 'react';
import { Rocket, Activity, Clock, TrendingUp, AlertCircle, CheckCircle, XCircle, Trash2 } from 'lucide-react';

interface DeployedModel {
  id: string;
  name: string;
  version: string;
  status: string;
  ollama_model_name?: string;
  vllm_model_name?: string;
  deployment_url?: string;
  base_model: string;
  finetuning_method: string;
  total_inferences?: number;
  avg_latency_ms?: number;
  last_inference_at?: string;
  created_at?: string;
  minio_path?: string;
  dataset_name?: string;
}

export default function DeploymentManager({ userRole }: { userRole: string }) {
  const [deployedModels, setDeployedModels] = useState<DeployedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [undeployingId, setUndeployingId] = useState<string | null>(null);

  useEffect(() => {
    fetchDeployedModels();
  }, []);

  const fetchDeployedModels = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/finetuning/models-public', {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Filter only deployed models
      const deployed = data.models.filter((m: DeployedModel) => m.status === 'deployed');
      setDeployedModels(deployed);
      setError(null);
    } catch (err) {
      console.error('Error fetching deployed models:', err);
      setError('Failed to load deployed models');
    } finally {
      setLoading(false);
    }
  };

  const handleUndeploy = async (modelId: string, modelName: string) => {
    if (!confirm(`Are you sure you want to undeploy "${modelName}"? This will remove it from Ollama and it will no longer be available in the chat UI.`)) {
      return;
    }

    try {
      setUndeployingId(modelId);

      const response = await fetch(
        `http://localhost:8000/api/v1/finetuning/models-public/${modelId}/undeploy`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        alert('Model undeployed successfully! It will no longer appear in the chat UI model dropdown.');
        await fetchDeployedModels(); // Refresh the list
      } else {
        const error = await response.json();
        alert(`Failed to undeploy: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error undeploying model:', error);
      alert('Failed to undeploy model');
    } finally {
      setUndeployingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusColors: { [key: string]: string } = {
      deployed: 'bg-green-100 text-green-800',
      registered: 'bg-yellow-100 text-yellow-800',
      rejected: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800'
    };

    const statusIcons: { [key: string]: React.ReactNode } = {
      deployed: <CheckCircle className="w-4 h-4 inline mr-1" />,
      registered: <Clock className="w-4 h-4 inline mr-1" />,
      rejected: <XCircle className="w-4 h-4 inline mr-1" />,
      failed: <AlertCircle className="w-4 h-4 inline mr-1" />
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {statusIcons[status]}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatLatency = (ms?: number) => {
    if (!ms) return 'N/A';
    return `${ms.toFixed(1)} ms`;
  };

  const formatInferences = (count?: number) => {
    if (!count) return '0';
    return count.toLocaleString();
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Rocket className="w-6 h-6 text-indigo-600" />
          <h2 className="text-2xl font-bold">Deployment Manager</h2>
        </div>
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading deployments...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Rocket className="w-6 h-6 text-indigo-600" />
          <h2 className="text-2xl font-bold">Deployment Manager</h2>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <AlertCircle className="w-5 h-5 inline mr-2" />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Rocket className="w-6 h-6 text-indigo-600" />
          <h2 className="text-2xl font-bold">Deployment Manager</h2>
        </div>
        <div className="text-sm text-gray-600">
          <Activity className="w-4 h-4 inline mr-1" />
          {deployedModels.length} Active Deployment{deployedModels.length !== 1 ? 's' : ''}
        </div>
      </div>

      {deployedModels.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Rocket className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Deployments</h3>
          <p className="text-gray-600">Deploy a fine-tuned model to see it here</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {deployedModels.map((model) => (
            <div
              key={model.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{model.name}</h3>
                  <p className="text-sm text-gray-600">
                    Version {model.version} • {model.finetuning_method}
                  </p>
                </div>
                {getStatusBadge(model.status)}
              </div>

              {/* Base Model */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Base Model</p>
                <p className="text-sm font-medium text-gray-900">{model.base_model}</p>
              </div>

              {/* Training Dataset */}
              {model.dataset_name && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-gray-500 mb-1">Training Dataset</p>
                  <p className="text-sm font-medium text-blue-900">{model.dataset_name}</p>
                </div>
              )}

              {/* Deployment Info */}
              <div className="space-y-3 mb-4">
                {model.ollama_model_name && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Ollama Model:</span>
                    <span className="text-sm font-medium text-gray-900 bg-indigo-50 px-3 py-1 rounded-full">
                      {model.ollama_model_name}
                    </span>
                  </div>
                )}

                {model.vllm_model_name && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">vLLM Model:</span>
                    <span className="text-sm font-medium text-gray-900 bg-purple-50 px-3 py-1 rounded-full">
                      {model.vllm_model_name}
                    </span>
                  </div>
                )}

                {model.deployment_url && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Endpoint:</span>
                    <a
                      href={model.deployment_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-indigo-600 hover:text-indigo-800 truncate max-w-xs"
                    >
                      {model.deployment_url}
                    </a>
                  </div>
                )}

                {/* MinIO Artifacts Link */}
                {model.minio_path && (
                  <div className="pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        📦 Model Artifacts{model.dataset_name ? ` (${model.dataset_name})` : ''}
                      </span>
                      <a
                        href={`http://localhost:9001/browser/${model.minio_path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        View in MinIO
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
                    <p className="text-xs text-gray-500">Inferences</p>
                  </div>
                  <p className="text-lg font-bold text-gray-900">
                    {formatInferences(model.total_inferences)}
                  </p>
                </div>

                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <Activity className="w-4 h-4 text-blue-600 mr-1" />
                    <p className="text-xs text-gray-500">Avg Latency</p>
                  </div>
                  <p className="text-lg font-bold text-gray-900">
                    {formatLatency(model.avg_latency_ms)}
                  </p>
                </div>

                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <Clock className="w-4 h-4 text-purple-600 mr-1" />
                    <p className="text-xs text-gray-500">Last Used</p>
                  </div>
                  <p className="text-xs font-medium text-gray-900">
                    {model.last_inference_at
                      ? new Date(model.last_inference_at).toLocaleDateString()
                      : 'Never'
                    }
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <button
                  onClick={() => handleUndeploy(model.id, model.name)}
                  disabled={undeployingId === model.id}
                  className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
                >
                  {undeployingId === model.id ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Undeploying...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      Undeploy Model
                    </>
                  )}
                </button>
              </div>

              {/* Deployed At */}
              <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
                Deployed: {formatDate(model.created_at)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
