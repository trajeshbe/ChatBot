/**
 * Merge & Deploy to Ollama - One-Click Workflow
 *
 * Combines the following steps into a single button:
 * 1. Approve model (if pending)
 * 2. Merge LoRA adapter with base model (5-15 min)
 * 3. Deploy to Ollama
 * 4. Make available in chat UI
 *
 * Shows progress for each step with real-time updates
 */

import React, { useState, useEffect } from 'react';
import {
  Rocket,
  GitMerge,
  CheckCircle,
  Loader,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Zap
} from 'lucide-react';

interface Model {
  id: string;
  name: string;
  version?: string;
  status: string;
  base_model: string;
  minio_checkpoint_path?: string;
  merged_model_path?: string;
  ollama_model_name?: string;
}

interface MergeAndDeployButtonProps {
  model: Model;
  onComplete?: () => void;
  onError?: (error: string) => void;
  compact?: boolean;
}

type WorkflowStep = 'idle' | 'approving' | 'merging' | 'deploying' | 'completed' | 'error';

interface StepStatus {
  approve: 'pending' | 'running' | 'completed' | 'skipped' | 'error';
  merge: 'pending' | 'running' | 'completed' | 'error';
  deploy: 'pending' | 'running' | 'completed' | 'error';
}

export default function MergeAndDeployButton({
  model,
  onComplete,
  onError,
  compact = false
}: MergeAndDeployButtonProps) {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('idle');
  const [stepStatus, setStepStatus] = useState<StepStatus>({
    approve: 'pending',
    merge: 'pending',
    deploy: 'pending'
  });
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [mergeTaskId, setMergeTaskId] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<string>('');

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Determine if we can start the workflow
  const canStart = () => {
    const validStatuses = ['registered', 'approved', 'adapter_only', 'merged'];
    return validStatuses.includes(model.status);
  };

  // Check if merge is needed
  const needsMerge = () => {
    return !['merged', 'deployed'].includes(model.status);
  };

  // Check if approval is needed
  const needsApproval = () => {
    return model.status === 'registered';
  };

  // Step 1: Approve model
  const approveModel = async () => {
    if (!needsApproval()) {
      setStepStatus(prev => ({ ...prev, approve: 'skipped' }));
      return true;
    }

    try {
      setCurrentStep('approving');
      setStepStatus(prev => ({ ...prev, approve: 'running' }));
      setProgress(10);

      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${API_BASE}/api/v1/finetuning/models-public/${model.id}/approve`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            notes: 'Auto-approved for merge and deployment'
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Approval failed');
      }

      setStepStatus(prev => ({ ...prev, approve: 'completed' }));
      setProgress(20);
      return true;
    } catch (err: any) {
      setStepStatus(prev => ({ ...prev, approve: 'error' }));
      const errorMsg = err.message || 'Unknown error';
      const detailedError = err.message === 'Failed to fetch'
        ? `Network error - check if backend is running at ${API_BASE}. Try refreshing the page.`
        : errorMsg;
      setError(`Approval failed: ${detailedError}`);
      setCurrentStep('error');
      if (onError) onError(detailedError);
      return false;
    }
  };

  // Step 2: Merge LoRA adapter with base model
  const mergeModel = async () => {
    if (!needsMerge()) {
      setStepStatus(prev => ({ ...prev, merge: 'skipped' }));
      return true;
    }

    try {
      setCurrentStep('merging');
      setStepStatus(prev => ({ ...prev, merge: 'running' }));
      setProgress(30);
      setEstimatedTime('5-15 minutes');

      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${API_BASE}/api/v1/finetuning/models/${model.id}/merge`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            base_model_name: model.base_model,
            force_cpu: false
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Merge request failed');
      }

      const data = await response.json();
      setMergeTaskId(data.task_id);

      // Start polling for merge status
      return await pollMergeStatus();
    } catch (err: any) {
      setStepStatus(prev => ({ ...prev, merge: 'error' }));
      setError(`Merge failed: ${err.message}`);
      setCurrentStep('error');
      if (onError) onError(err.message);
      return false;
    }
  };

  // Poll merge status
  const pollMergeStatus = (): Promise<boolean> => {
    return new Promise((resolve) => {
      let attempts = 0;
      const maxAttempts = 180; // 15 minutes max (polling every 5 seconds)

      const interval = setInterval(async () => {
        attempts++;

        try {
          // Use public endpoint to avoid CORS issues during polling
          const response = await fetch(
            `${API_BASE}/api/v1/finetuning/models-public/${model.id}/merge-status`
          );

          if (!response.ok) {
            throw new Error('Failed to get merge status');
          }

          const data = await response.json();

          // Update progress (30-70% during merge)
          const mergeProgress = Math.min(70, 30 + (attempts * 0.5));
          setProgress(mergeProgress);

          if (data.status === 'merged') {
            clearInterval(interval);
            setPollingInterval(null);
            setStepStatus(prev => ({ ...prev, merge: 'completed' }));
            setProgress(75);
            setEstimatedTime('');
            resolve(true);
          } else if (data.status === 'merge_failed') {
            clearInterval(interval);
            setPollingInterval(null);
            setStepStatus(prev => ({ ...prev, merge: 'error' }));
            setError(`Merge failed: ${data.merge_error_message || 'Unknown error'}`);
            setCurrentStep('error');
            if (onError) onError(data.merge_error_message);
            resolve(false);
          } else if (attempts >= maxAttempts) {
            clearInterval(interval);
            setPollingInterval(null);
            setStepStatus(prev => ({ ...prev, merge: 'error' }));
            setError('Merge timeout: took longer than 15 minutes');
            setCurrentStep('error');
            if (onError) onError('Merge timeout');
            resolve(false);
          }
        } catch (err: any) {
          clearInterval(interval);
          setPollingInterval(null);
          setStepStatus(prev => ({ ...prev, merge: 'error' }));
          setError(`Merge polling failed: ${err.message}`);
          setCurrentStep('error');
          if (onError) onError(err.message);
          resolve(false);
        }
      }, 5000); // Poll every 5 seconds

      setPollingInterval(interval);
    });
  };

  // Step 3: Deploy to Ollama
  const deployToOllama = async () => {
    try {
      setCurrentStep('deploying');
      setStepStatus(prev => ({ ...prev, deploy: 'running' }));
      setProgress(80);

      const ollamaModelName = `${model.name.toLowerCase().replace(/[^a-z0-9-]/g, '-')}-v${model.version || '1'}`;

      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${API_BASE}/api/v1/finetuning/models-public/${model.id}/deploy`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            deployment_target: 'ollama',
            deployment_config: {
              model_name: ollamaModelName,
              temperature: 0.7,
              top_p: 0.9,
              top_k: 40
            }
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Deployment failed');
      }

      const data = await response.json();
      setStepStatus(prev => ({ ...prev, deploy: 'completed' }));
      setProgress(100);
      setCurrentStep('completed');

      // Success notification
      if (onComplete) onComplete();

      return true;
    } catch (err: any) {
      setStepStatus(prev => ({ ...prev, deploy: 'error' }));
      setError(`Deployment failed: ${err.message}`);
      setCurrentStep('error');
      if (onError) onError(err.message);
      return false;
    }
  };

  // Execute full workflow
  const executeWorkflow = async () => {
    setError(null);
    setProgress(0);
    setStepStatus({
      approve: 'pending',
      merge: 'pending',
      deploy: 'pending'
    });

    // Step 1: Approve (if needed)
    const approveSuccess = await approveModel();
    if (!approveSuccess) return;

    // Step 2: Merge (if needed)
    const mergeSuccess = await mergeModel();
    if (!mergeSuccess) return;

    // Step 3: Deploy
    await deployToOllama();
  };

  // Render step indicator
  const renderStepIndicator = (
    stepName: string,
    status: 'pending' | 'running' | 'completed' | 'skipped' | 'error',
    icon: React.ReactNode
  ) => {
    const getColor = () => {
      switch (status) {
        case 'completed': return 'text-green-600 dark:text-green-400';
        case 'running': return 'text-blue-600 dark:text-blue-400';
        case 'error': return 'text-red-600 dark:text-red-400';
        case 'skipped': return 'text-gray-400 dark:text-gray-600';
        default: return 'text-gray-400 dark:text-gray-600';
      }
    };

    const getIcon = () => {
      switch (status) {
        case 'completed': return <CheckCircle className="w-4 h-4" />;
        case 'running': return <Loader className="w-4 h-4 animate-spin" />;
        case 'error': return <XCircle className="w-4 h-4" />;
        case 'skipped': return <CheckCircle className="w-4 h-4 opacity-30" />;
        default: return icon;
      }
    };

    return (
      <div className={`flex items-center gap-2 ${getColor()}`}>
        {getIcon()}
        <span className="text-sm font-medium">{stepName}</span>
        {status === 'skipped' && <span className="text-xs opacity-50">(skipped)</span>}
      </div>
    );
  };

  // Compact button view
  if (compact) {
    return (
      <button
        onClick={executeWorkflow}
        disabled={currentStep !== 'idle' || !canStart()}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:cursor-not-allowed"
      >
        {currentStep === 'idle' ? (
          <>
            <Zap className="w-4 h-4" />
            <span>Merge & Deploy to Ollama</span>
          </>
        ) : currentStep === 'completed' ? (
          <>
            <CheckCircle className="w-4 h-4" />
            <span>Deployed!</span>
          </>
        ) : currentStep === 'error' ? (
          <>
            <XCircle className="w-4 h-4" />
            <span>Failed</span>
          </>
        ) : (
          <>
            <Loader className="w-4 h-4 animate-spin" />
            <span>Processing... {progress}%</span>
          </>
        )}
      </button>
    );
  }

  // Full card view with progress
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
            <Rocket className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Merge & Deploy to Ollama
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              One-click deployment workflow
            </p>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      {currentStep !== 'idle' && (
        <div className="space-y-3">
          {renderStepIndicator('1. Approve Model', stepStatus.approve, <CheckCircle className="w-4 h-4" />)}
          {renderStepIndicator('2. Merge LoRA Adapter', stepStatus.merge, <GitMerge className="w-4 h-4" />)}
          {renderStepIndicator('3. Deploy to Ollama', stepStatus.deploy, <Rocket className="w-4 h-4" />)}

          {/* Progress Bar */}
          <div className="pt-2">
            <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
              <span>Overall Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Estimated Time */}
          {estimatedTime && (
            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
              <Clock className="w-4 h-4" />
              <span>Estimated time: {estimatedTime}</span>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={executeWorkflow}
        disabled={currentStep !== 'idle' && currentStep !== 'error' && currentStep !== 'completed' || !canStart()}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:cursor-not-allowed"
      >
        {currentStep === 'idle' ? (
          <>
            <Zap className="w-5 h-5" />
            <span>Start Merge & Deploy</span>
          </>
        ) : currentStep === 'completed' ? (
          <>
            <CheckCircle className="w-5 h-5" />
            <span>✅ Successfully Deployed!</span>
          </>
        ) : currentStep === 'error' ? (
          <>
            <XCircle className="w-5 h-5" />
            <span>Retry Workflow</span>
          </>
        ) : (
          <>
            <Loader className="w-5 h-5 animate-spin" />
            <span>Processing... {progress}%</span>
          </>
        )}
      </button>

      {/* Success Message */}
      {currentStep === 'completed' && (
        <div className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-green-700 dark:text-green-300">
            <p className="font-medium">Model deployed successfully!</p>
            <p className="mt-1">Your model is now available in the Chat UI. Go to Chat and select it from the model dropdown.</p>
          </div>
        </div>
      )}
    </div>
  );
}
