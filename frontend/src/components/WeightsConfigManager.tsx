/**
 * Weights Configuration Manager Component
 *
 * Provides UI for configuring all weights used in RAG system dynamic computation:
 * - Strategy weights (includes tool selection via tool_navigation, tool_ocr, etc.)
 * - Scoring formula weights
 * - Source quality weights
 * - Classification thresholds
 * - Similarity thresholds
 * - Reranking weights
 * - Query preprocessing parameters
 * - Cache configuration
 * - Answer fusion weights (NOT YET IMPLEMENTED - placeholder)
 * - RAG settings (chunk size, top_k, etc.)
 *
 * DEPRECATED (removed in consolidation):
 * - multi_tool_weights (merged into strategy_weights.tool_*)
 */

import React, { useState, useEffect } from 'react';
import { Save, RotateCcw, AlertCircle, CheckCircle, Settings, User, X, TrendingUp, Zap, Target } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CountUp from 'react-countup';

interface WeightsConfig {
  strategy_weights: {
    conversation_only: number;  // 🆕 Conversation-only mode (uses ONLY conversation history)
    rag_short_term: number;
    rag_hybrid: number;
    tool_navigation: number;
    tool_ocr: number;
    tool_docling: number;
    tool_web_scraping: number;
    rag_long_term: number;
    direct_llm: number;
    enable_brain_view: boolean;  // 🧠 Brain View toggle for debug context
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

          // 🧹 One-time migration: Remove deprecated multi_tool_weights
          if (parsedConfig.multi_tool_weights) {
            delete parsedConfig.multi_tool_weights;
            localStorage.setItem('userWeightsConfig', JSON.stringify(parsedConfig));
            console.log('✅ Migrated config: removed deprecated multi_tool_weights');
          }

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

    // 🔧 FIX: Provide default value if key doesn't exist (for backward compatibility with old localStorage configs)
    const value = (config[section] as any)[key] ?? 0;
    const percentage = ((value - min) / (max - min)) * 100;

    return (
      <motion.div
        key={`${section}-${key}`}
        className="mb-3"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="glass-card-light p-3 rounded-lg hover-glow-primary smooth-transition">
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-semibold text-gray-800 dark:text-gray-200">{label}</label>
            <motion.span
              key={value}
              className="text-sm font-bold gradient-text-primary px-2 py-0.5 rounded-md bg-white/50 dark:bg-slate-800/50"
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.2 }}
            >
              {value.toFixed(2)}
            </motion.span>
          </div>
          <div className="relative">
            <input
              type="range"
              min={min}
              max={max}
              step={step}
              value={value}
              onChange={(e) => handleWeightChange(section, key, parseFloat(e.target.value))}
              className="w-full h-2 rounded-full appearance-none cursor-pointer smooth-transition"
              style={{
                background: `linear-gradient(90deg, rgb(107, 144, 128) 0%, rgb(20, 184, 166) ${percentage}%, rgb(226, 232, 240) ${percentage}%, rgb(226, 232, 240) 100%)`,
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1.5">
            <span className="flex items-center gap-1">
              <Target className="w-3 h-3" />
              {min.toFixed(2)}
            </span>
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {max.toFixed(2)}
            </span>
          </div>
        </div>
      </motion.div>
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
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
            {renderSlider('strategy_weights', 'conversation_only', 'Conversation Only (Context Summarization)', 0, 1, 0.05)}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md mb-3 mt-2">
              <p className="text-xs text-blue-800">
                <strong>💬 Conversation Only:</strong> When &gt; 0.8, uses ONLY conversation history (no document RAG). Perfect for multi-model comparisons and context summarization.
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

            {/* 🧠 Brain View Toggle */}
            <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-md">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label className="text-sm font-semibold text-purple-900 flex items-center gap-2">
                    🧠 Brain View (Debug Context)
                  </label>
                  <p className="text-xs text-purple-700 mt-1">
                    Enable real-time context visualization showing tools, documents, and performance metrics.
                    Disable to improve performance by skipping debug context assembly.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    if (config) {
                      setConfig({
                        ...config,
                        strategy_weights: {
                          ...config.strategy_weights,
                          enable_brain_view: !config.strategy_weights.enable_brain_view
                        }
                      });
                    }
                  }}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ml-4 ${
                    config?.strategy_weights.enable_brain_view ? 'bg-purple-600' : 'bg-gray-200'
                  }`}
                  role="switch"
                  aria-checked={config?.strategy_weights.enable_brain_view}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      config?.strategy_weights.enable_brain_view ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
              <div className="mt-2 text-xs text-purple-600">
                Status: {config?.strategy_weights.enable_brain_view ? '✅ Enabled - Full debug context will be collected' : '❌ Disabled - Skipping debug context for better performance'}
              </div>
            </div>
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
            <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> For semantic and keyword reranking weights, see the{' '}
                <button
                  onClick={() => setActiveTab('reranking')}
                  className="text-primary-600 underline hover:text-primary-700"
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-600 via-secondary-600 to-secondary-500 p-8 text-white shadow-2xl">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl">
                <Settings className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-2">Weights Configuration</h1>
                <p className="text-primary-100 text-lg">Fine-tune your RAG system's behavior with precision controls</p>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="glass-card p-4 rounded-xl">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-secondary-300" />
                  <div>
                    <p className="text-xs text-primary-100">Total Parameters</p>
                    <p className="text-2xl font-bold">
                      <CountUp end={50} duration={2} />
                    </p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-4 rounded-xl">
                <div className="flex items-center gap-3">
                  <Target className="w-5 h-5 text-primary-300" />
                  <div>
                    <p className="text-xs text-primary-100">Active Profile</p>
                    <p className="text-xl font-semibold">{hasSessionConfig ? 'Custom' : 'Global'}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-4 rounded-xl">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-secondary-400" />
                  <div>
                    <p className="text-xs text-primary-100">Optimization</p>
                    <p className="text-xl font-semibold">Balanced</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="glass-card-light rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 p-6 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm">
          <div className="flex items-center justify-between">{/* Keeping existing header content */}
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

        {/* Tabs - Pill Style */}
        <div className="p-4 bg-gray-50 dark:bg-slate-800/30">
          <div className="flex overflow-x-auto gap-2 pb-2">
            {[
              { key: 'strategy', label: 'Strategy', icon: '🎯' },
              { key: 'scoring', label: 'Scoring', icon: '📊' },
              { key: 'source_quality', label: 'Source Quality', icon: '⭐' },
              { key: 'classification', label: 'Classification', icon: '🏷️' },
              { key: 'similarity', label: 'Similarity', icon: '🔍' },
              { key: 'reranking', label: 'Reranking', icon: '📈' },
              { key: 'preprocessing', label: 'Preprocessing', icon: '⚙️' },
              { key: 'cache', label: 'Cache', icon: '⚡' },
              { key: 'fusion', label: 'Fusion (Not Implemented)', icon: '🔀' },
              { key: 'rag_settings', label: 'RAG Settings', icon: '🎛️' },
            ].map((tab) => (
              <motion.button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as TabType)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`px-6 py-3 text-sm font-semibold whitespace-nowrap rounded-full smooth-transition ${
                  activeTab === tab.key
                    ? 'bg-gradient-to-r from-primary-600 to-secondary-600 text-white shadow-lg'
                    : 'bg-white dark:bg-slate-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-600 shadow'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </motion.button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="p-6">{renderTabContent()}</div>
      </div>

      <style jsx>{`
        /* Custom slider thumb styles with sage green gradient */
        input[type="range"]::-webkit-slider-thumb {
          appearance: none;
          width: 18px;
          height: 18px;
          background: linear-gradient(135deg, #6b9080 0%, #14b8a6 100%);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2), 0 0 0 3px rgba(107, 144, 128, 0.1);
          transition: all 0.2s ease;
        }

        input[type="range"]::-webkit-slider-thumb:hover {
          transform: scale(1.15);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3), 0 0 0 4px rgba(107, 144, 128, 0.2);
        }

        input[type="range"]::-moz-range-thumb {
          width: 18px;
          height: 18px;
          background: linear-gradient(135deg, #6b9080 0%, #14b8a6 100%);
          cursor: pointer;
          border-radius: 50%;
          border: none;
          box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
          transition: all 0.2s ease;
        }

        input[type="range"]::-moz-range-thumb:hover {
          transform: scale(1.15);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
      `}</style>
    </div>
  );
};

export default WeightsConfigManager;
