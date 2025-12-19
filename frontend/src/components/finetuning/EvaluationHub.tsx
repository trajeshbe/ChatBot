import React, { useState, useEffect } from 'react';
import {
  Target, TrendingUp, BarChart3, GitCompare, Play, Download,
  AlertCircle, CheckCircle, Clock, Zap, FileText, ArrowRight, Upload, XCircle,
  Eye, Send, Settings, RefreshCw, X
} from 'lucide-react';

interface EvaluationMetrics {
  accuracy?: number;
  perplexity?: number;
  rouge_1?: number;
  rouge_2?: number;
  rouge_l?: number;
  bleu_score?: number;
  f1_score?: number;
  precision?: number;
  recall?: number;
  loss?: number;
}

interface FineTunedModel {
  id: string;
  name: string;
  version: string;
  description: string;
  base_model: string;
  finetuning_method: string;
  status: 'registered' | 'deployed' | 'archived' | 'deprecated';
  eval_metrics: EvaluationMetrics | null;
  created_at: string;
  ollama_model_name?: string;
  job_id?: string;
}

interface ComparisonResult {
  model_id: string;
  model_name: string;
  response: string;
  latency_ms: number;
  tokens_used: number;
}

interface EvaluationSample {
  sample_id: number;
  input: string;
  reference: string;
  generated: string;
  scores: {
    bleu?: number;
    rouge?: {
      rouge1: number;
      rouge2: number;
      rougeL: number;
    };
    meteor?: number;
    bertscore?: {
      precision: number;
      recall: number;
      f1: number;
    };
  };
}

interface DetailedEvaluationResults {
  model_id: string;
  model_name: string;
  status: string;
  timestamp: string;
  task_type: string;
  num_samples_evaluated: number;
  metrics: Record<string, {
    mean: number;
    std: number;
    min: number;
    max: number;
    median: number;
  }>;
  sample_results: EvaluationSample[];
  example_samples: {
    best: EvaluationSample[];
    worst: EvaluationSample[];
    median: EvaluationSample[];
  };
  metric_descriptions: Record<string, string>;
}

export default function EvaluationHub({ userRole }: { userRole: string }) {
  const [models, setModels] = useState<FineTunedModel[]>([]);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [compareMode, setCompareMode] = useState(false);
  const [testPrompt, setTestPrompt] = useState('');
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluatingModel, setEvaluatingModel] = useState<string | null>(null);
  const [deployingModel, setDeployingModel] = useState<string | null>(null);

  // Detailed evaluation viewer state
  const [viewingEvaluation, setViewingEvaluation] = useState<string | null>(null);
  const [evaluationResults, setEvaluationResults] = useState<DetailedEvaluationResults | null>(null);
  const [selectedSampleView, setSelectedSampleView] = useState<'all' | 'best' | 'worst' | 'median'>('all');

  // Manual testing state
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [manualTestInput, setManualTestInput] = useState('');
  const [manualTestOutput, setManualTestOutput] = useState('');
  const [testingInProgress, setTestingInProgress] = useState(false);
  const [testSettings, setTestSettings] = useState({
    temperature: 0.7,
    max_length: 512
  });

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/finetuning/models-public', {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setModels(data.models || []);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const triggerEvaluation = async (modelId: string, numSamples: number = 100) => {
    setEvaluatingModel(modelId);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/finetuning/models-public/${modelId}/evaluate?num_samples=${numSamples}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        setEvaluationResults(result);
        setViewingEvaluation(modelId);
        alert(`✅ Evaluation completed! ${result.num_samples_evaluated} samples evaluated.`);
        await fetchModels(); // Refresh models to update eval_metrics
      } else {
        const error = await response.json();
        alert(`Failed to evaluate: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error triggering evaluation:', error);
      alert('Error triggering evaluation');
    } finally {
      setEvaluatingModel(null);
    }
  };

  const viewEvaluationResults = async (modelId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/finetuning/models-public/${modelId}/evaluation-results`);

      if (response.ok) {
        const result = await response.json();
        if (result.has_evaluation) {
          setEvaluationResults(result);
          setViewingEvaluation(modelId);
        } else {
          alert('No evaluation results available. Please run evaluation first.');
        }
      }
    } catch (error) {
      console.error('Error loading evaluation results:', error);
      alert('Error loading evaluation results');
    }
  };

  const testModelManually = async (modelId: string) => {
    if (!manualTestInput.trim()) {
      alert('Please enter test input');
      return;
    }

    setTestingInProgress(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/finetuning/models-public/${modelId}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input: manualTestInput,
          temperature: testSettings.temperature,
          max_length: testSettings.max_length
        })
      });

      if (response.ok) {
        const result = await response.json();
        setManualTestOutput(result.generated);
        alert(`✅ Generated response! Total inferences: ${result.total_inferences}`);
      } else {
        const error = await response.json();
        alert(`Test failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error testing model:', error);
      alert('Error testing model');
    } finally {
      setTestingInProgress(false);
    }
  };

  const deployToOllama = async (modelId: string) => {
    const model = models.find(m => m.id === modelId);
    if (!confirm(`Deploy "${model?.name}" to Ollama? This will make it available for inference in the chat UI.`)) {
      return;
    }

    setDeployingModel(modelId);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/finetuning/models-public/${modelId}/deploy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          deployment_target: 'ollama',
          deployment_config: {
            temperature: 0.7,
            top_p: 0.9,
            top_k: 40
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Model deployed to Ollama successfully!\n\nOllama Model: ${result.ollama_model_name || 'N/A'}\n\nYou can now use it in the chat interface.`);
        await fetchModels(); // Refresh to show deployed status
      } else {
        const error = await response.json();
        alert(`Failed to deploy: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error deploying model:', error);
      alert('Error deploying model to Ollama');
    } finally {
      setDeployingModel(null);
    }
  };

  const undeployFromOllama = async (modelId: string) => {
    const model = models.find(m => m.id === modelId);
    if (!confirm(`Undeploy "${model?.name}" from Ollama?\n\nThis will remove it from the chat interface.`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/finetuning/models-public/${modelId}/undeploy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        alert('✅ Model undeployed from Ollama successfully!');
        await fetchModels();
      } else {
        alert('Failed to undeploy model');
      }
    } catch (error) {
      console.error('Error undeploying model:', error);
      alert('Error undeploying model');
    }
  };

  const toggleModelSelection = (modelId: string) => {
    const newSelection = new Set(selectedModels);
    if (newSelection.has(modelId)) {
      newSelection.delete(modelId);
    } else {
      if (newSelection.size >= 3) {
        alert('Maximum 3 models can be compared at once');
        return;
      }
      newSelection.add(modelId);
    }
    setSelectedModels(newSelection);
  };

  const compareModels = async () => {
    if (selectedModels.size < 2) {
      alert('Please select at least 2 models to compare');
      return;
    }

    if (!testPrompt.trim()) {
      alert('Please enter a test prompt');
      return;
    }

    setLoading(true);
    setCompareMode(true);

    try {
      const results: ComparisonResult[] = [];

      for (const modelId of selectedModels) {
        const model = models.find(m => m.id === modelId);
        if (!model) continue;

        const response = await fetch('http://localhost:8000/api/v1/finetuning/models/inference', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model_id: modelId,
            prompt: testPrompt
          })
        });

        if (response.ok) {
          const data = await response.json();
          results.push({
            model_id: modelId,
            model_name: model.name,
            response: data.response || 'No response generated',
            latency_ms: data.latency_ms || 0,
            tokens_used: data.tokens_used || 0
          });
        }
      }

      setComparisonResults(results);
    } catch (error) {
      console.error('Error comparing models:', error);
      alert('Error comparing models');
    } finally {
      setLoading(false);
    }
  };

  const getMetricColor = (metric: string, value: number): string => {
    // Higher is better for these metrics
    const higherIsBetter = ['accuracy', 'rouge_1', 'rouge_2', 'rouge_l', 'bleu_score', 'f1_score', 'precision', 'recall'];
    // Lower is better for these metrics
    const lowerIsBetter = ['perplexity', 'loss'];

    if (higherIsBetter.includes(metric)) {
      if (value >= 0.8) return 'text-green-600';
      if (value >= 0.6) return 'text-yellow-600';
      return 'text-red-600';
    } else if (lowerIsBetter.includes(metric)) {
      if (value <= 2.0) return 'text-green-600';
      if (value <= 5.0) return 'text-yellow-600';
      return 'text-red-600';
    }

    return 'text-gray-900';
  };

  const formatMetricValue = (value: number): string => {
    if (value < 1) {
      return (value * 100).toFixed(1) + '%';
    }
    return value.toFixed(3);
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { color: string; icon: React.ReactNode }> = {
      deployed: { color: 'bg-green-100 text-green-800', icon: <CheckCircle className="w-4 h-4" /> },
      registered: { color: 'bg-blue-100 text-blue-800', icon: <Clock className="w-4 h-4" /> },
      approved: { color: 'bg-purple-100 text-purple-800', icon: <CheckCircle className="w-4 h-4" /> },
      archived: { color: 'bg-gray-100 text-gray-800', icon: <FileText className="w-4 h-4" /> },
      deprecated: { color: 'bg-red-100 text-red-800', icon: <AlertCircle className="w-4 h-4" /> },
    };

    const badge = badges[status] || badges.registered;

    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${badge.color}`}>
        {badge.icon}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getSamplesToDisplay = (): EvaluationSample[] => {
    if (!evaluationResults) return [];

    switch (selectedSampleView) {
      case 'best':
        return evaluationResults.example_samples?.best || [];
      case 'worst':
        return evaluationResults.example_samples?.worst || [];
      case 'median':
        return evaluationResults.example_samples?.median || [];
      case 'all':
      default:
        return evaluationResults.sample_results || [];
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-6 h-6 text-indigo-600" />
          <h2 className="text-2xl font-bold">Evaluation Hub</h2>
        </div>
        {selectedModels.size >= 2 && (
          <button
            onClick={compareModels}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            <GitCompare className="w-4 h-4" />
            Compare Selected Models ({selectedModels.size})
          </button>
        )}
      </div>

      {/* Detailed Evaluation Results Modal */}
      {viewingEvaluation && evaluationResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center z-50 overflow-y-auto p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full my-8">
            {/* Modal Header */}
            <div className="border-b border-gray-200 p-6 flex items-center justify-between sticky top-0 bg-white rounded-t-lg">
              <div>
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <BarChart3 className="w-6 h-6 text-indigo-600" />
                  Evaluation Results: {evaluationResults.model_name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {evaluationResults.num_samples_evaluated} samples evaluated • {evaluationResults.task_type}
                </p>
              </div>
              <button
                onClick={() => {
                  setViewingEvaluation(null);
                  setEvaluationResults(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              {/* Metrics Summary Grid */}
              <div>
                <h4 className="text-lg font-semibold mb-4">Evaluation Metrics</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(evaluationResults.metrics || {}).map(([metric, stats]) => (
                    <div key={metric} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <h5 className="font-bold text-gray-900 mb-2">{metric.toUpperCase().replace('_', ' ')}</h5>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Mean:</span>
                          <span className="font-mono font-semibold">{stats.mean.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Std Dev:</span>
                          <span className="font-mono">{stats.std.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Median:</span>
                          <span className="font-mono">{stats.median.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>Range:</span>
                          <span>{stats.min.toFixed(2)} - {stats.max.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sample View Tabs */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold">Evaluation Samples</h4>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSelectedSampleView('all')}
                      className={`px-3 py-1 text-sm rounded ${selectedSampleView === 'all' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                    >
                      All ({evaluationResults.sample_results?.length || 0})
                    </button>
                    <button
                      onClick={() => setSelectedSampleView('best')}
                      className={`px-3 py-1 text-sm rounded ${selectedSampleView === 'best' ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                    >
                      Best
                    </button>
                    <button
                      onClick={() => setSelectedSampleView('worst')}
                      className={`px-3 py-1 text-sm rounded ${selectedSampleView === 'worst' ? 'bg-red-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                    >
                      Worst
                    </button>
                    <button
                      onClick={() => setSelectedSampleView('median')}
                      className={`px-3 py-1 text-sm rounded ${selectedSampleView === 'median' ? 'bg-yellow-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                    >
                      Median
                    </button>
                  </div>
                </div>

                {/* Sample Cards */}
                <div className="space-y-4 max-h-[500px] overflow-y-auto">
                  {getSamplesToDisplay().map((sample) => (
                    <div key={sample.sample_id} className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-600">Sample #{sample.sample_id}</span>
                        <div className="flex gap-3 text-sm">
                          {sample.scores.bleu !== undefined && (
                            <span className="font-semibold text-blue-600">
                              BLEU: {sample.scores.bleu.toFixed(3)}
                            </span>
                          )}
                          {sample.scores.rouge && (
                            <span className="font-semibold text-green-600">
                              ROUGE-1: {sample.scores.rouge.rouge1.toFixed(3)}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div>
                          <div className="text-xs font-semibold text-gray-700 mb-1">INPUT:</div>
                          <div className="p-3 bg-blue-50 rounded text-sm text-gray-800">{sample.input}</div>
                        </div>

                        <div>
                          <div className="text-xs font-semibold text-gray-700 mb-1">REFERENCE:</div>
                          <div className="p-3 bg-gray-100 rounded text-sm text-gray-800">{sample.reference}</div>
                        </div>

                        <div>
                          <div className="text-xs font-semibold text-gray-700 mb-1">GENERATED:</div>
                          <div className="p-3 bg-green-50 rounded text-sm text-gray-800">{sample.generated}</div>
                        </div>

                        <div className="flex gap-4 text-xs text-gray-600 pt-2 border-t border-gray-200">
                          {Object.entries(sample.scores).map(([metric, score]) => (
                            <div key={metric}>
                              <strong className="text-gray-700">{metric}:</strong>{' '}
                              {typeof score === 'object' ? JSON.stringify(score) : score.toFixed(3)}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Manual Testing Section */}
              {testingModel === viewingEvaluation && (
                <div className="border-t border-gray-200 pt-6">
                  <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Send className="w-5 h-5 text-indigo-600" />
                    Manual Testing
                  </h4>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Test Input
                      </label>
                      <textarea
                        value={manualTestInput}
                        onChange={(e) => setManualTestInput(e.target.value)}
                        placeholder="Enter your test input..."
                        rows={4}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      />
                    </div>

                    <div className="flex gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Temperature
                        </label>
                        <input
                          type="number"
                          value={testSettings.temperature}
                          onChange={(e) => setTestSettings({...testSettings, temperature: parseFloat(e.target.value)})}
                          min="0"
                          max="2"
                          step="0.1"
                          className="p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Max Length
                        </label>
                        <input
                          type="number"
                          value={testSettings.max_length}
                          onChange={(e) => setTestSettings({...testSettings, max_length: parseInt(e.target.value)})}
                          min="128"
                          max="2048"
                          step="128"
                          className="p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>

                    <button
                      onClick={() => testModelManually(viewingEvaluation)}
                      disabled={testingInProgress || !manualTestInput.trim()}
                      className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                    >
                      <Send className="w-4 h-4" />
                      {testingInProgress ? 'Generating...' : 'Test Model'}
                    </button>

                    {manualTestOutput && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Generated Output
                        </label>
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                          <p className="whitespace-pre-wrap text-sm text-gray-800">{manualTestOutput}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Test Prompt Input */}
      {selectedModels.size >= 2 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Test Prompt for Comparison
          </label>
          <textarea
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            placeholder="Enter a prompt to test all selected models..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            rows={3}
          />
        </div>
      )}

      {/* Comparison Results */}
      {compareMode && comparisonResults.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <GitCompare className="w-5 h-5" />
            Side-by-Side Comparison
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {comparisonResults.map((result) => (
              <div key={result.model_id} className="border border-gray-200 rounded-lg p-4">
                <div className="mb-3">
                  <h4 className="font-semibold text-gray-900">{result.model_name}</h4>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {result.latency_ms}ms
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      {result.tokens_used} tokens
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 p-3 rounded text-sm text-gray-800 whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {result.response}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => {
              setCompareMode(false);
              setComparisonResults([]);
              setTestPrompt('');
            }}
            className="mt-4 text-sm text-indigo-600 hover:text-indigo-700"
          >
            Clear comparison
          </button>
        </div>
      )}

      {/* Models Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Fine-Tuned Models
          </h3>
          <span className="text-sm text-gray-600">
            {models.length} model{models.length !== 1 ? 's' : ''}
          </span>
        </div>

        {models.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Target className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-lg font-medium mb-1">No Models Found</p>
            <p className="text-sm">Complete a fine-tuning job to see models here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Select
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Base Model
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Method
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Evaluation Metrics
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {models.map((model) => (
                  <tr key={model.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedModels.has(model.id)}
                        onChange={() => toggleModelSelection(model.id)}
                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-gray-900">{model.name}</div>
                        <div className="text-sm text-gray-500">{model.version}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {model.base_model}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded">
                        {model.finetuning_method?.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(model.status)}
                    </td>
                    <td className="px-4 py-3">
                      {model.eval_metrics ? (
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(model.eval_metrics).slice(0, 3).map(([key, value]) => (
                            <div key={key} className="text-sm">
                              <span className="text-gray-600">{key}:</span>{' '}
                              <span className={`font-medium ${getMetricColor(key, value as number)}`}>
                                {formatMetricValue(value as number)}
                              </span>
                            </div>
                          ))}
                          {Object.keys(model.eval_metrics).length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{Object.keys(model.eval_metrics).length - 3} more
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400 italic">Not evaluated</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        {!model.eval_metrics && (
                          <button
                            onClick={() => triggerEvaluation(model.id)}
                            disabled={evaluatingModel === model.id}
                            className="flex items-center gap-1 px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            <Play className="w-3 h-3" />
                            {evaluatingModel === model.id ? 'Evaluating...' : 'Evaluate'}
                          </button>
                        )}
                        {(model.status === 'registered' || model.status === 'approved') && (
                          <button
                            onClick={() => deployToOllama(model.id)}
                            disabled={deployingModel === model.id}
                            className="flex items-center gap-1 px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                            title="Deploy to Ollama"
                          >
                            <Upload className="w-3 h-3" />
                            {deployingModel === model.id ? 'Deploying...' : 'Deploy to Ollama'}
                          </button>
                        )}
                        {model.status === 'deployed' && model.ollama_model_name && (
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                              {model.ollama_model_name}
                            </span>
                            <button
                              onClick={() => undeployFromOllama(model.id)}
                              className="flex items-center gap-1 px-2 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                              title="Undeploy from Ollama"
                            >
                              <XCircle className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                        <button
                          onClick={() => alert(`View details for ${model.name}`)}
                          className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          <ArrowRight className="w-3 h-3" />
                          Details
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Metrics Legend */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Evaluation Metrics Guide
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-sm text-blue-800">
          <div>
            <span className="font-medium">Accuracy:</span> Classification correctness (%)
          </div>
          <div>
            <span className="font-medium">Perplexity:</span> Language model confidence (lower is better)
          </div>
          <div>
            <span className="font-medium">ROUGE:</span> Text overlap with reference (%)
          </div>
          <div>
            <span className="font-medium">BLEU:</span> Translation/generation quality (%)
          </div>
          <div>
            <span className="font-medium">F1 Score:</span> Balanced precision & recall (%)
          </div>
          <div>
            <span className="font-medium">Loss:</span> Training error (lower is better)
          </div>
        </div>
      </div>
    </div>
  );
}
