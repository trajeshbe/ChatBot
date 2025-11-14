/**
 * Evaluation Settings Component
 *
 * Provides a UI for configuring RAG evaluation metrics with:
 * - Toggleable evaluation methods
 * - Real-time configuration updates
 * - Performance optimizations (caching, async)
 * - Visual grouping by category
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Settings,
  Check,
  X,
  AlertCircle,
  Zap,
  Shield,
  Target,
  Database,
  Brain,
  TrendingUp,
  Save,
  RefreshCw,
  Info
} from 'lucide-react';

interface EvaluationMethod {
  id: string;
  name: string;
  description: string;
  category: 'framework' | 'llm' | 'metric' | 'safety' | 'retrieval';
  requires_external_lib: boolean;
}

interface EvaluationConfig {
  // Toggle switches
  enable_ragas: boolean;
  enable_llm_as_judge: boolean;
  enable_deepeval: boolean;
  enable_semantic_similarity: boolean;
  enable_bertscore: boolean;
  enable_citation_accuracy: boolean;
  enable_toxicity: boolean;
  enable_bias_detection: boolean;
  enable_hallucination: boolean;
  enable_answer_relevancy: boolean;
  enable_context_precision: boolean;
  enable_context_recall: boolean;
  enable_faithfulness: boolean;

  // Configuration parameters
  llm_judge_model: string;
  use_cache: boolean;
  async_evaluation: boolean;
  batch_size: number;
  min_score_threshold: number;
  cache_ttl_seconds: number;

  // Auto-evaluation
  auto_evaluate: boolean;
  evaluation_sampling_rate: number;
}

const defaultConfig: EvaluationConfig = {
  enable_ragas: false,
  enable_llm_as_judge: false,
  enable_deepeval: false,
  enable_semantic_similarity: false,
  enable_bertscore: false,
  enable_citation_accuracy: true,
  enable_toxicity: true,
  enable_bias_detection: true,
  enable_hallucination: true,
  enable_answer_relevancy: true,
  enable_context_precision: false,
  enable_context_recall: false,
  enable_faithfulness: true,
  llm_judge_model: 'gpt-4-turbo-preview',
  use_cache: true,
  async_evaluation: true,
  batch_size: 10,
  min_score_threshold: 0.7,
  cache_ttl_seconds: 3600,
  auto_evaluate: false,
  evaluation_sampling_rate: 1.0
};

interface EvaluationSettingsProps {
  sessionId?: string;
  onConfigChange?: (config: EvaluationConfig) => void;
}

export const EvaluationSettings: React.FC<EvaluationSettingsProps> = ({
  sessionId,
  onConfigChange
}) => {
  const [config, setConfig] = useState<EvaluationConfig>(defaultConfig);
  const [methods, setMethods] = useState<EvaluationMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchMethods();
    if (sessionId) {
      fetchConfig();
    } else {
      setLoading(false);
    }
  }, [sessionId]);

  const fetchMethods = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/evaluation/methods`);
      setMethods(response.data);
    } catch (error) {
      console.error('Failed to fetch evaluation methods:', error);
    }
  };

  const fetchConfig = async () => {
    if (!sessionId) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/api/v1/evaluation/config/${sessionId}`);
      setConfig(response.data.config);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch config:', error);
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const payload = {
        ...config,
        session_id: sessionId
      };

      await axios.post(`${API_URL}/api/v1/evaluation/config`, payload);

      setMessage({ type: 'success', text: 'Evaluation settings saved successfully!' });
      if (onConfigChange) {
        onConfigChange(config);
      }

      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      console.error('Failed to save config:', error);
      setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const resetConfig = () => {
    setConfig(defaultConfig);
    setMessage({ type: 'success', text: 'Settings reset to defaults' });
    setTimeout(() => setMessage(null), 3000);
  };

  const updateConfig = (key: keyof EvaluationConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'framework': return <Database className="w-4 h-4" />;
      case 'llm': return <Brain className="w-4 h-4" />;
      case 'metric': return <Target className="w-4 h-4" />;
      case 'safety': return <Shield className="w-4 h-4" />;
      case 'retrieval': return <TrendingUp className="w-4 h-4" />;
      default: return <Settings className="w-4 h-4" />;
    }
  };

  const getEnabledMethodsCount = () => {
    return Object.entries(config)
      .filter(([key, value]) => key.startsWith('enable_') && value === true)
      .length;
  };

  const groupedMethods = methods.reduce((acc, method) => {
    if (!acc[method.category]) {
      acc[method.category] = [];
    }
    acc[method.category].push(method);
    return acc;
  }, {} as Record<string, EvaluationMethod[]>);

  const categoryNames = {
    framework: 'Evaluation Frameworks',
    llm: 'LLM-based Evaluation',
    metric: 'Core Metrics',
    safety: 'Safety & Quality',
    retrieval: 'Retrieval Metrics'
  };

  const categoryDescriptions = {
    framework: 'Comprehensive evaluation frameworks (requires external libraries)',
    llm: 'Use powerful LLMs as judges for nuanced evaluation',
    metric: 'Fundamental quality and relevance metrics',
    safety: 'Detect harmful content, bias, and hallucinations',
    retrieval: 'Evaluate quality of context retrieval'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading evaluation settings...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 border-b cursor-pointer hover:bg-gray-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center space-x-3">
          <Settings className="w-6 h-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-800">Evaluation Settings</h2>
            <p className="text-sm text-gray-600">
              {getEnabledMethodsCount()} methods enabled •
              {config.auto_evaluate ? ' Auto-evaluation ON' : ' Manual evaluation'}
            </p>
          </div>
        </div>
        <button className="text-gray-400 hover:text-gray-600">
          {isOpen ? <X className="w-5 h-5" /> : <Settings className="w-5 h-5" />}
        </button>
      </div>

      {/* Settings Panel */}
      {isOpen && (
        <div className="p-6 space-y-6">
          {/* Message Banner */}
          {message && (
            <div
              className={`p-4 rounded-lg flex items-center space-x-2 ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {message.type === 'success' ? (
                <Check className="w-5 h-5" />
              ) : (
                <AlertCircle className="w-5 h-5" />
              )}
              <span>{message.text}</span>
            </div>
          )}

          {/* Performance Settings */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center space-x-2 mb-4">
              <Zap className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-800">Performance Optimization</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Use Cache */}
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.use_cache}
                  onChange={(e) => updateConfig('use_cache', e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium text-gray-700">Enable Caching</div>
                  <div className="text-xs text-gray-500">Cache evaluation results for faster responses</div>
                </div>
              </label>

              {/* Async Evaluation */}
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.async_evaluation}
                  onChange={(e) => updateConfig('async_evaluation', e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium text-gray-700">Async Evaluation</div>
                  <div className="text-xs text-gray-500">Run evaluations in parallel</div>
                </div>
              </label>

              {/* Auto-evaluate */}
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.auto_evaluate}
                  onChange={(e) => updateConfig('auto_evaluate', e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium text-gray-700">Auto-Evaluate</div>
                  <div className="text-xs text-gray-500">Automatically evaluate all responses</div>
                </div>
              </label>

              {/* Cache TTL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cache TTL (seconds)
                </label>
                <input
                  type="number"
                  value={config.cache_ttl_seconds}
                  onChange={(e) => updateConfig('cache_ttl_seconds', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  min="60"
                  max="86400"
                />
              </div>
            </div>

            {/* Sampling Rate */}
            {config.auto_evaluate && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Evaluation Sampling Rate: {(config.evaluation_sampling_rate * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.evaluation_sampling_rate}
                  onChange={(e) => updateConfig('evaluation_sampling_rate', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="text-xs text-gray-500 mt-1">
                  Evaluate {(config.evaluation_sampling_rate * 100).toFixed(0)}% of queries to balance performance and insights
                </div>
              </div>
            )}
          </div>

          {/* Evaluation Methods by Category */}
          <div className="space-y-6">
            {Object.entries(groupedMethods).map(([category, categoryMethods]) => (
              <div key={category} className="border rounded-lg overflow-hidden">
                <div className="bg-gray-50 p-3 flex items-center space-x-2">
                  {getCategoryIcon(category)}
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800">
                      {categoryNames[category as keyof typeof categoryNames]}
                    </h3>
                    <p className="text-xs text-gray-600">
                      {categoryDescriptions[category as keyof typeof categoryDescriptions]}
                    </p>
                  </div>
                </div>

                <div className="divide-y">
                  {categoryMethods.map((method) => {
                    const configKey = `enable_${method.id}` as keyof EvaluationConfig;
                    const isEnabled = config[configKey] as boolean;

                    return (
                      <div key={method.id} className="p-4 hover:bg-gray-50">
                        <label className="flex items-start space-x-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isEnabled}
                            onChange={(e) => updateConfig(configKey, e.target.checked)}
                            className="mt-1 w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                          />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-800">{method.name}</span>
                              {method.requires_external_lib && (
                                <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                                  Requires Library
                                </span>
                              )}
                              {isEnabled && (
                                <Check className="w-4 h-4 text-green-600" />
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{method.description}</p>
                          </div>
                        </label>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Advanced Settings */}
          <div className="border rounded-lg p-4 bg-gray-50">
            <div className="flex items-center space-x-2 mb-4">
              <Info className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-800">Advanced Settings</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* LLM Judge Model */}
              {config.enable_llm_as_judge && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    LLM Judge Model
                  </label>
                  <select
                    value={config.llm_judge_model}
                    onChange={(e) => updateConfig('llm_judge_model', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                    <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                  </select>
                </div>
              )}

              {/* Min Score Threshold */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min Score Threshold: {config.min_score_threshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={config.min_score_threshold}
                  onChange={(e) => updateConfig('min_score_threshold', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="text-xs text-gray-500 mt-1">
                  Minimum acceptable quality score
                </div>
              </div>

              {/* Batch Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Batch Size
                </label>
                <input
                  type="number"
                  value={config.batch_size}
                  onChange={(e) => updateConfig('batch_size', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="100"
                />
                <div className="text-xs text-gray-500 mt-1">
                  Number of evaluations to process in parallel
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t">
            <button
              onClick={resetConfig}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset to Defaults</span>
            </button>

            <button
              onClick={saveConfig}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center space-x-2"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Settings</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluationSettings;
