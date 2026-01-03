/**
 * POC Configuration Manager
 *
 * Universal configuration UI for all Tier 2 Domain Verticals and Tier 3 Customer Solutions.
 * Provides 6 tabs for managing LLMs, prompts, parameters, thresholds, scoring, and advanced settings.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface POCConfigManagerProps {
  moduleName: string;
  userId?: string;
  onClose?: () => void;
}

interface ModuleConfig {
  llm?: any;
  prompts?: {
    system?: Record<string, string>;
    user?: Record<string, string>;
  };
  parameters?: Record<string, any>;
  thresholds?: Record<string, number>;
  scoring?: {
    weights?: Record<string, number>;
    factors?: Record<string, number>;
  };
  retrieval?: {
    top_k?: number;
    rerank_top_k?: number;
    min_score?: number;
  };
  features?: Record<string, boolean>;
  extra?: Record<string, any>;
}

export const POCConfigManager: React.FC<POCConfigManagerProps> = ({
  moduleName,
  userId,
  onClose
}) => {
  const [config, setConfig] = useState<ModuleConfig>({});
  const [originalConfig, setOriginalConfig] = useState<ModuleConfig>({});
  const [activeTab, setActiveTab] = useState<string>('prompts');
  const [hasChanges, setHasChanges] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load configuration on mount
  useEffect(() => {
    loadConfig();
  }, [moduleName, userId]);

  // Track changes
  useEffect(() => {
    const changed = JSON.stringify(config) !== JSON.stringify(originalConfig);
    setHasChanges(changed);
  }, [config, originalConfig]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(
        `/api/v1/module-config/modules/${moduleName}`,
        {
          params: {
            user_id: userId,
            include_overrides: true,
            include_metadata: false
          }
        }
      );

      const loadedConfig = response.data.config || {};
      setConfig(loadedConfig);
      setOriginalConfig(JSON.parse(JSON.stringify(loadedConfig)));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load configuration');
      console.error('Failed to load config:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveChanges = async () => {
    try {
      setSaving(true);
      setError(null);

      await axios.put(`/api/v1/module-config/modules/${moduleName}`, {
        updates: config,
        change_reason: 'Updated via UI'
      });

      setOriginalConfig(JSON.parse(JSON.stringify(config)));
      setHasChanges(false);
      setSuccessMessage('Configuration saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
      console.error('Failed to save config:', err);
    } finally {
      setSaving(false);
    }
  };

  const resetChanges = () => {
    setConfig(JSON.parse(JSON.stringify(originalConfig)));
    setHasChanges(false);
  };

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      const newConfig = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let current: any = newConfig;

      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
          current[keys[i]] = {};
        }
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return newConfig;
    });
  };

  const tabs = [
    { id: 'prompts', label: '📝 Prompts', icon: '📝' },
    { id: 'models', label: '🤖 Models', icon: '🤖' },
    { id: 'parameters', label: '⚙️ Parameters', icon: '⚙️' },
    { id: 'thresholds', label: '🎯 Thresholds', icon: '🎯' },
    { id: 'scoring', label: '📊 Scoring', icon: '📊' },
    { id: 'advanced', label: '🔍 Advanced', icon: '🔍' }
  ];

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full m-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Module Configuration: {moduleName}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Configure prompts, models, and parameters dynamically
            </p>
          </div>
          <div className="flex gap-2">
            {hasChanges && (
              <>
                <button
                  onClick={resetChanges}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Reset
                </button>
                <button
                  onClick={saveChanges}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
        {successMessage && (
          <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMessage}
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 font-medium text-sm whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'prompts' && (
            <PromptsTab config={config} updateConfig={updateConfig} />
          )}
          {activeTab === 'models' && (
            <ModelsTab config={config} updateConfig={updateConfig} />
          )}
          {activeTab === 'parameters' && (
            <ParametersTab config={config} updateConfig={updateConfig} />
          )}
          {activeTab === 'thresholds' && (
            <ThresholdsTab config={config} updateConfig={updateConfig} />
          )}
          {activeTab === 'scoring' && (
            <ScoringTab config={config} updateConfig={updateConfig} />
          )}
          {activeTab === 'advanced' && (
            <AdvancedTab config={config} updateConfig={updateConfig} />
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50 flex justify-between items-center">
          <span className="text-sm text-gray-500">
            {hasChanges ? '⚠️ Unsaved changes' : '✓ All changes saved'}
          </span>
          <div className="flex gap-2">
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Tab Components
const PromptsTab: React.FC<{ config: ModuleConfig; updateConfig: (path: string, value: any) => void }> = ({
  config,
  updateConfig
}) => {
  const systemPrompts = config.prompts?.system || {};
  const userPrompts = config.prompts?.user || {};

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">System Prompts</h3>
        {Object.entries(systemPrompts).map(([key, value]) => (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </label>
            <textarea
              value={value}
              onChange={(e) => updateConfig(`prompts.system.${key}`, e.target.value)}
              rows={6}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              placeholder="Enter system prompt..."
            />
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">User Prompt Templates</h3>
        {Object.entries(userPrompts).map(([key, value]) => (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </label>
            <textarea
              value={value}
              onChange={(e) => updateConfig(`prompts.user.${key}`, e.target.value)}
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              placeholder="Enter user prompt template... Use {variable_name} for placeholders"
            />
          </div>
        ))}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-700">
          💡 <strong>Tip:</strong> Use <code className="bg-blue-100 px-1 rounded">{'{ variable_name }'}</code> for dynamic content in prompts
        </p>
      </div>
    </div>
  );
};

const ModelsTab: React.FC<{ config: ModuleConfig; updateConfig: (path: string, value: any) => void }> = ({
  config,
  updateConfig
}) => {
  const llmConfig = config.llm || {};
  const availableModels = [
    'gpt-4o-mini',
    'gpt-4',
    'gpt-4-turbo',
    'claude-3-5-sonnet-20241022',
    'claude-3-opus',
    'claude-3-sonnet',
    'mistral-large',
    'llama3.1'
  ];

  return (
    <div className="space-y-6">
      {Object.entries(llmConfig).map(([stage, stageConfig]: [string, any]) => (
        <div key={stage} className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">
            {stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
              <select
                value={stageConfig.model || 'gpt-4o-mini'}
                onChange={(e) => updateConfig(`llm.${stage}.model`, e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {availableModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature: {stageConfig.temperature !== undefined ? stageConfig.temperature : 0.2}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={stageConfig.temperature !== undefined ? stageConfig.temperature : 0.2}
                onChange={(e) => updateConfig(`llm.${stage}.temperature`, parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">Lower = more deterministic, Higher = more creative</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
              <input
                type="number"
                min="1"
                max="128000"
                value={stageConfig.max_tokens || 1000}
                onChange={(e) => updateConfig(`llm.${stage}.max_tokens`, parseInt(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

const ParametersTab: React.FC<{ config: ModuleConfig; updateConfig: (path: string, value: any) => void }> = ({
  config,
  updateConfig
}) => {
  const parameters = config.parameters || {};
  const retrieval = config.retrieval || {};

  return (
    <div className="space-y-6">
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Retrieval Parameters</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Top K Results</label>
            <input
              type="number"
              min="1"
              max="100"
              value={retrieval.top_k || 10}
              onChange={(e) => updateConfig('retrieval.top_k', parseInt(e.target.value))}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Rerank Top K</label>
            <input
              type="number"
              min="1"
              max="50"
              value={retrieval.rerank_top_k || 5}
              onChange={(e) => updateConfig('retrieval.rerank_top_k', parseInt(e.target.value))}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Custom Parameters</h3>
        <div className="space-y-4">
          {Object.entries(parameters).map(([key, value]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </label>
              <input
                type={typeof value === 'number' ? 'number' : 'text'}
                value={value as any}
                onChange={(e) => updateConfig(`parameters.${key}`, typeof value === 'number' ? parseFloat(e.target.value) : e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const ThresholdsTab: React.FC<{ config: ModuleConfig; updateConfig: (path: string, value: any) => void }> = ({
  config,
  updateConfig
}) => {
  const thresholds = config.thresholds || {};

  return (
    <div className="space-y-6">
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Confidence Thresholds</h3>

        <div className="space-y-4">
          {Object.entries(thresholds).map(([key, value]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: {value}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={value}
                onChange={(e) => updateConfig(`thresholds.${key}`, parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0.0</span>
                <span>1.0</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const ScoringTab: React.FC<{ config: ModuleConfig; updateConfig: (path: string, value: any) => void }> = ({
  config,
  updateConfig
}) => {
  const scoring = config.scoring || {};
  const weights = scoring.weights || {};
  const factors = scoring.factors || {};

  return (
    <div className="space-y-6">
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Scoring Weights</h3>

        <div className="space-y-4">
          {Object.entries(weights).map(([key, value]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: {value} ({(value * 100).toFixed(0)}%)
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={value}
                onChange={(e) => updateConfig(`scoring.weights.${key}`, parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          ))}
        </div>
      </div>

      {Object.keys(factors).length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Scoring Factors</h3>

          <div className="space-y-4">
            {Object.entries(factors).map(([key, value]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: {value} ({(value * 100).toFixed(0)}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={value}
                  onChange={(e) => updateConfig(`scoring.factors.${key}`, parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const AdvancedTab: React.FC<{ config: ModuleConfig; updateConfig: (path: string, value: any) => void }> = ({
  config,
  updateConfig
}) => {
  const features = config.features || {};

  return (
    <div className="space-y-6">
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Feature Flags</h3>

        <div className="space-y-3">
          {Object.entries(features).map(([key, value]) => (
            <label key={key} className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => updateConfig(`features.${key}`, e.target.checked)}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-700">
          ⚠️ <strong>Warning:</strong> Advanced settings can significantly impact module behavior. Change with caution.
        </p>
      </div>
    </div>
  );
};

export default POCConfigManager;
