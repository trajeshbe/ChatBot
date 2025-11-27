/**
 * Weights Configuration Manager Component
 *
 * Provides UI for configuring all weights used in RAG system dynamic computation:
 * - Strategy weights
 * - Scoring formula weights
 * - Source quality weights
 * - Classification thresholds
 * - Similarity thresholds
 * - Reranking weights
 * - Query preprocessing parameters
 * - Cache configuration
 * - Multi-tool weights
 * - Answer fusion weights
 */

import React, { useState, useEffect } from 'react';
import { Save, RotateCcw, AlertCircle, CheckCircle, Settings, User, X } from 'lucide-react';

interface WeightsConfig {
  strategy_weights: {
    rag_short_term: number;
    rag_hybrid: number;
    tool_navigation: number;
    tool_ocr: number;
    tool_docling: number;
    tool_web_scraping: number;
    rag_long_term: number;
    direct_llm: number;
  };
  scoring_formula_weights: {
    strategy_weight: number;
    confidence: number;
    source_quality_score: number;
    relevance_score: number;
    completeness_score: number;
    diversity_bonus: number;
  };
  source_quality_weights: {
    short_term: number;
    long_term: number;
    general: number;
    scraped: number;
    ocr: number;
  };
  classification_thresholds: {
    general_knowledge_skip: number;
    ai_personal_skip: number;
    ambiguous_use_rag: number;
    min_llm_classification_confidence: number;
  };
  similarity_thresholds: {
    default: number;
    proper_nouns: number;
    short_query: number;
    minimum: number;
    maximum: number;
  };
  reranking_weights: {
    semantic: number;
    keyword: number;
    recency: number;
  };
  query_preprocessing: {
    max_length_for_expansion: number;
    min_query_length: number;
    max_query_length: number;
  };
  cache: {
    similarity_threshold: number;
    ttl_seconds: number;
  };
  multi_tool_weights: {
    document_rag: number;
    navigation_agent: number;
    ocr_tool: number;
    web_scraping: number;
    docling: number;
  };
  answer_fusion: {
    best_answer_weight: number;
    second_best_weight: number;
    third_best_weight: number;
  };
  rag_settings: {
    top_k: number;
    no_relevant_docs_threshold: number;
    chunk_size: number;
    chunk_overlap: number;
  };
}

interface ApiResponse {
  success: boolean;
  data?: WeightsConfig;
  message?: string;
  error?: string;
}

type TabType =
  | 'strategy'
  | 'scoring'
  | 'source_quality'
  | 'classification'
  | 'similarity'
  | 'reranking'
  | 'preprocessing'
  | 'cache'
  | 'multi_tool'
  | 'fusion'
  | 'rag_settings';

export const WeightsConfigManager: React.FC = () => {
  const [config, setConfig] = useState<WeightsConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('strategy');
  const [hasSessionConfig, setHasSessionConfig] = useState(false);

  // Fetch configuration on mount and check for session config
  useEffect(() => {
    // 🆕 FIX: Check localStorage FIRST before fetching from API
    if (typeof window !== 'undefined') {
      const sessionConfig = localStorage.getItem('userWeightsConfig');
      if (sessionConfig) {
        try {
          const parsedConfig = JSON.parse(sessionConfig);
          setConfig(parsedConfig);
          setHasSessionConfig(true);
          setLoading(false); // 🔧 CRITICAL FIX: Set loading to false when using localStorage
          console.log('✅ WeightsConfigManager loaded USER SESSION config from localStorage');
          return; // Don't fetch from API if we have session config
        } catch (parseError) {
          console.error('Failed to parse session config:', parseError);
        }
      }
    }

    // Only fetch from API if no session config
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/api/v1/config/weights');
      const result: ApiResponse = await response.json();

      if (result.success && result.data) {
        setConfig(result.data);
      } else {
        setError(result.message || 'Failed to load configuration');
      }
    } catch (err) {
      setError('Error fetching configuration: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const updateWeights = async () => {
    if (!config) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('http://localhost:8000/api/v1/config/weights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      const result = await response.json();

      if (result.success) {
        setSuccess('Weights updated successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(result.message || 'Failed to update weights');
      }
    } catch (err) {
      setError('Error updating weights: ' + (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const saveToSession = () => {
    if (!config) return;

    try {
      // Save to localStorage
      localStorage.setItem('userWeightsConfig', JSON.stringify(config));
      setHasSessionConfig(true);
      setSuccess('Settings applied to your session! These will be used for your queries.');
      setTimeout(() => setSuccess(null), 5000);

      // 🆕 FIX: Dispatch custom event to notify ChatInterface that config was updated
      const event = new CustomEvent('weightsConfigUpdated', { detail: config });
      window.dispatchEvent(event);
      console.log('🔔 Dispatched weightsConfigUpdated event with', Object.keys(config).length, 'parameter groups');
    } catch (err) {
      setError('Error saving to session: ' + (err as Error).message);
    }
  };

  const clearSessionConfig = () => {
    try {
      localStorage.removeItem('userWeightsConfig');
      setHasSessionConfig(false);
      setSuccess('Session config cleared! Using global defaults.');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Error clearing session: ' + (err as Error).message);
    }
  };

  const resetToDefaults = async () => {
    if (!confirm('Are you sure you want to reset all weights to default values?')) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('http://localhost:8000/api/v1/config/weights/reset', {
        method: 'POST',
      });

      const result = await response.json();

      if (result.success) {
        await fetchConfig();
        setSuccess('Weights reset to defaults successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(result.message || 'Failed to reset weights');
      }
    } catch (err) {
      setError('Error resetting weights: ' + (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleWeightChange = (section: keyof WeightsConfig, key: string, value: number) => {
    if (!config) return;

    setConfig({
      ...config,
      [section]: {
        ...(config[section] as any),
        [key]: value,
      },
    });
  };

  const renderSlider = (
    section: keyof WeightsConfig,
    key: string,
    label: string,
    min: number = 0,
    max: number = 1,
    step: number = 0.05
  ) => {
    if (!config) return null;

    const value = (config[section] as any)[key];

    return (
      <div key={`${section}-${key}`} className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <label className="text-sm font-medium text-gray-700">{label}</label>
          <span className="text-sm font-mono text-gray-600">{value.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => handleWeightChange(section, key, parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
      </div>
    );
  };

  const renderNumberInput = (
    section: keyof WeightsConfig,
    key: string,
    label: string,
    min: number = 1,
    max: number = 5000
  ) => {
    if (!config) return null;

    const value = (config[section] as any)[key];

    return (
      <div key={`${section}-${key}`} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <input
          type="number"
          min={min}
          max={max}
          value={value}
          onChange={(e) => handleWeightChange(section, key, parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    );
  };

  const renderTabContent = () => {
    if (!config) return null;

    switch (activeTab) {
      case 'strategy':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Strategy Base Weights</h3>
            <p className="text-sm text-gray-600 mb-4">
              Higher weight = strategy is preferred when confidence is equal. <strong>Keep values below 0.8 to enable BALANCED mode (GPT-4 tool selection)</strong>.
            </p>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-md mb-4">
              <p className="text-xs text-amber-800">
                <strong>⚠️ Important:</strong> If rag_short_term OR rag_long_term &gt; 0.8, system will force RAG mode and bypass tool selection.
              </p>
            </div>
            {renderSlider('strategy_weights', 'rag_short_term', 'RAG Short-term (Session Docs)', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'rag_hybrid', 'RAG Hybrid', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'tool_navigation', 'Tool: Navigation', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'tool_ocr', 'Tool: OCR', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'tool_docling', 'Tool: Docling', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'tool_web_scraping', 'Tool: Web Scraping', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'rag_long_term', 'RAG Long-term (All Docs)', 0, 1, 0.05)}
            {renderSlider('strategy_weights', 'direct_llm', 'Direct LLM (No RAG)', 0, 1, 0.05)}
          </div>
        );

      case 'scoring':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Scoring Formula Weights</h3>
            <p className="text-sm text-gray-600 mb-4">
              How different factors contribute to final score (should sum to ~1.0)
            </p>
            {renderSlider('scoring_formula_weights', 'strategy_weight', 'Strategy Weight (30%)', 0, 1, 0.05)}
            {renderSlider('scoring_formula_weights', 'confidence', 'LLM Confidence (25%)', 0, 1, 0.05)}
            {renderSlider(
              'scoring_formula_weights',
              'source_quality_score',
              'Source Quality (25%)',
              0,
              1,
              0.05
            )}
            {renderSlider('scoring_formula_weights', 'relevance_score', 'Relevance (15%)', 0, 1, 0.05)}
            {renderSlider('scoring_formula_weights', 'completeness_score', 'Completeness (5%)', 0, 1, 0.05)}
            {renderSlider(
              'scoring_formula_weights',
              'diversity_bonus',
              'Diversity Bonus (Additive)',
              0,
              0.5,
              0.05
            )}
          </div>
        );

      case 'source_quality':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Source Quality Weights</h3>
            <p className="text-sm text-gray-600 mb-4">
              Quality score multipliers for different source types
            </p>
            {renderSlider('source_quality_weights', 'short_term', 'Short-term Memory', 0, 1.5, 0.05)}
            {renderSlider('source_quality_weights', 'long_term', 'Long-term Memory', 0, 1.5, 0.05)}
            {renderSlider('source_quality_weights', 'general', 'General Knowledge', 0, 1.5, 0.05)}
            {renderSlider('source_quality_weights', 'scraped', 'Scraped Content', 0, 1.5, 0.05)}
            {renderSlider('source_quality_weights', 'ocr', 'OCR Extracted', 0, 1.5, 0.05)}
          </div>
        );

      case 'classification':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Classification Thresholds</h3>
            <p className="text-sm text-gray-600 mb-4">
              Confidence thresholds for query classification decisions
            </p>
            {renderSlider(
              'classification_thresholds',
              'general_knowledge_skip',
              'Skip RAG for General Knowledge',
              0,
              1,
              0.05
            )}
            {renderSlider(
              'classification_thresholds',
              'ai_personal_skip',
              'Skip RAG for AI-Personal Questions',
              0,
              1,
              0.05
            )}
            {renderSlider(
              'classification_thresholds',
              'ambiguous_use_rag',
              'Use RAG for Ambiguous Queries',
              0,
              1,
              0.05
            )}
            {renderSlider(
              'classification_thresholds',
              'min_llm_classification_confidence',
              'Min LLM Classification Confidence',
              0,
              1,
              0.05
            )}
          </div>
        );

      case 'similarity':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Similarity Thresholds</h3>
            <p className="text-sm text-gray-600 mb-4">
              Vector similarity thresholds for retrieval
            </p>
            {renderSlider('similarity_thresholds', 'default', 'Default Threshold', 0, 1, 0.05)}
            {renderSlider('similarity_thresholds', 'proper_nouns', 'Proper Nouns (Names, Places)', 0, 1, 0.05)}
            {renderSlider('similarity_thresholds', 'short_query', 'Short Queries', 0, 1, 0.05)}
            {renderSlider('similarity_thresholds', 'minimum', 'Minimum Threshold', 0, 1, 0.05)}
            {renderSlider('similarity_thresholds', 'maximum', 'Maximum Threshold', 0, 1, 0.05)}
          </div>
        );

      case 'reranking':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Reranking Weights</h3>
            <p className="text-sm text-gray-600 mb-4">
              Weights for reranking retrieved chunks (should sum to 1.0)
            </p>
            {renderSlider('reranking_weights', 'semantic', 'Semantic Similarity', 0, 1, 0.05)}
            {renderSlider('reranking_weights', 'keyword', 'Keyword Overlap', 0, 1, 0.05)}
            {renderSlider('reranking_weights', 'recency', 'Recency', 0, 1, 0.05)}
          </div>
        );

      case 'preprocessing':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Query Preprocessing</h3>
            <p className="text-sm text-gray-600 mb-4">
              Parameters for query preprocessing and expansion
            </p>
            {renderNumberInput(
              'query_preprocessing',
              'max_length_for_expansion',
              'Max Length for Expansion (words)',
              1,
              20
            )}
            {renderNumberInput('query_preprocessing', 'min_query_length', 'Minimum Query Length', 1, 10)}
            {renderNumberInput('query_preprocessing', 'max_query_length', 'Maximum Query Length', 10, 5000)}
          </div>
        );

      case 'cache':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Cache Configuration</h3>
            <p className="text-sm text-gray-600 mb-4">
              Semantic cache settings
            </p>
            {renderSlider('cache', 'similarity_threshold', 'Similarity Threshold for Cache Hit', 0, 1, 0.05)}
            {renderNumberInput('cache', 'ttl_seconds', 'TTL (seconds)', 60, 86400)}
          </div>
        );

      case 'multi_tool':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Multi-Tool Agent Weights</h3>
            <p className="text-sm text-gray-600 mb-4">
              Weights for multi-tool agent strategy selection (0-1 scale)
            </p>
            {renderSlider('multi_tool_weights', 'document_rag', 'Document RAG Tool', 0, 1, 0.05)}
            {renderSlider('multi_tool_weights', 'navigation_agent', 'Navigation Agent', 0, 1, 0.05)}
            {renderSlider('multi_tool_weights', 'ocr_tool', 'OCR Tool', 0, 1, 0.05)}
            {renderSlider('multi_tool_weights', 'web_scraping', 'Web Scraping', 0, 1, 0.05)}
            {renderSlider('multi_tool_weights', 'docling', 'Docling', 0, 1, 0.05)}
          </div>
        );

      case 'fusion':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">Answer Fusion Weights</h3>
            <p className="text-sm text-gray-600 mb-4">
              Weights for combining multiple answers (should sum to 1.0)
            </p>
            {renderSlider('answer_fusion', 'best_answer_weight', 'Best Answer', 0, 1, 0.05)}
            {renderSlider('answer_fusion', 'second_best_weight', 'Second Best Answer', 0, 1, 0.05)}
            {renderSlider('answer_fusion', 'third_best_weight', 'Third Best Answer', 0, 1, 0.05)}
          </div>
        );

      case 'rag_settings':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">RAG Settings</h3>
            <p className="text-sm text-gray-600 mb-4">
              Core retrieval and document processing parameters
            </p>
            {renderSlider('rag_settings', 'top_k', 'Top K Documents to Retrieve', 1, 20, 1)}
            {renderSlider(
              'rag_settings',
              'no_relevant_docs_threshold',
              'No Relevant Docs Threshold',
              0,
              1,
              0.05
            )}
            {renderSlider('rag_settings', 'chunk_size', 'Chunk Size (characters)', 100, 2000, 50)}
            {renderSlider('rag_settings', 'chunk_overlap', 'Chunk Overlap (characters)', 0, 500, 10)}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> For semantic and keyword reranking weights, see the{' '}
                <button
                  onClick={() => setActiveTab('reranking')}
                  className="text-blue-600 underline hover:text-blue-700"
                >
                  Reranking tab
                </button>
                .
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Settings className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Weights Configuration</h2>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={resetToDefaults}
                disabled={saving}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Reset to Defaults</span>
              </button>
              <button
                onClick={saveToSession}
                disabled={saving}
                className="px-4 py-2 border border-emerald-300 rounded-md shadow-sm text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                title="Apply these settings to your session only (won't affect other users)"
              >
                <User className="w-4 h-4" />
                <span>Apply to My Session</span>
              </button>
              <button
                onClick={updateWeights}
                disabled={saving}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                title="⚠️ Warning: Saves globally for ALL users"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Saving...' : 'Save Globally ⚠️'}</span>
              </button>
            </div>
          </div>

          {/* Session Config Indicator */}
          {hasSessionConfig && (
            <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-md flex items-center justify-between">
              <div className="flex items-start space-x-2">
                <User className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-emerald-800">
                    Using Custom Session Config
                  </p>
                  <p className="text-xs text-emerald-600 mt-1">
                    Your personal settings are active. Only you can see and use these changes.
                  </p>
                </div>
              </div>
              <button
                onClick={clearSessionConfig}
                className="px-3 py-1 text-xs font-medium text-emerald-700 hover:text-emerald-900 flex items-center space-x-1"
                title="Clear your session config and use global defaults"
              >
                <X className="w-3 h-3" />
                <span>Clear</span>
              </button>
            </div>
          )}

          {/* Status messages */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-red-800">{error}</span>
            </div>
          )}

          {success && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-start space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-green-800">{success}</span>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {[
              { key: 'strategy', label: 'Strategy' },
              { key: 'scoring', label: 'Scoring' },
              { key: 'source_quality', label: 'Source Quality' },
              { key: 'classification', label: 'Classification' },
              { key: 'similarity', label: 'Similarity' },
              { key: 'reranking', label: 'Reranking' },
              { key: 'preprocessing', label: 'Preprocessing' },
              { key: 'cache', label: 'Cache' },
              { key: 'multi_tool', label: 'Multi-Tool' },
              { key: 'fusion', label: 'Fusion' },
              { key: 'rag_settings', label: 'RAG Settings' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as TabType)}
                className={`px-6 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="p-6">{renderTabContent()}</div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: #3b82f6;
          cursor: pointer;
          border-radius: 50%;
        }

        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          background: #3b82f6;
          cursor: pointer;
          border-radius: 50%;
          border: none;
        }
      `}</style>
    </div>
  );
};

export default WeightsConfigManager;
