/**
 * Agent Mode Toggle Component
 *
 * Provides checkbox to enable Claude Code agent mode with:
 * - Budget display (daily and monthly)
 * - Force Claude CLI option (advanced)
 * - Real-time usage stats
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

export type AgentSelectionMode = 'automatic' | 'local_only' | 'claude_only';

interface AgentModeToggleProps {
  useAgentMode: boolean;
  onToggleAgentMode: (enabled: boolean) => void;
  agentSelection?: AgentSelectionMode;
  onAgentSelectionChange?: (mode: AgentSelectionMode) => void;
}

interface BudgetStats {
  daily: {
    limit: number;
    spent: number;
    remaining: number;
    percentage_used: number;
    tasks: number;
  };
  monthly: {
    limit: number;
    spent: number;
    remaining: number;
    percentage_used: number;
    tasks: number;
  };
  warnings: Array<{
    level: string;
    message: string;
  }>;
}

export const AgentModeToggle: React.FC<AgentModeToggleProps> = ({
  useAgentMode,
  onToggleAgentMode,
  agentSelection = 'automatic',
  onAgentSelectionChange
}) => {
  const [budgetStats, setBudgetStats] = useState<BudgetStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Fetch budget stats when agent mode is enabled
  useEffect(() => {
    if (useAgentMode) {
      fetchBudgetStats();
      // Refresh every 30 seconds
      const interval = setInterval(fetchBudgetStats, 30000);
      return () => clearInterval(interval);
    }
  }, [useAgentMode]);

  const fetchBudgetStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/agent/budget-stats');
      setBudgetStats(response.data);
    } catch (error) {
      console.error('Failed to fetch budget stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBudgetColor = (percentage: number): string => {
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 80) return 'text-orange-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getBudgetBarColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 80) return 'bg-orange-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 mb-4 bg-white dark:bg-slate-800">
      {/* Main Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="agent-mode"
            checked={useAgentMode}
            onChange={(e) => onToggleAgentMode(e.target.checked)}
            className="w-5 h-5 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
          />
          <label
            htmlFor="agent-mode"
            className="text-sm font-medium text-slate-900 dark:text-slate-100 cursor-pointer"
          >
            🤖 Use Claude Code Agent
          </label>
        </div>

        {useAgentMode && budgetStats && (
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
          >
            {showAdvanced ? 'Hide Details' : 'Show Details'}
          </button>
        )}
      </div>

      {/* Description */}
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 ml-8">
        {useAgentMode
          ? 'Autonomous coding agent will handle complex tasks (code generation, data analysis, vision)'
          : 'Enable for complex tasks requiring code execution, data analysis, or multi-step workflows'
        }
      </p>

      {/* Agent Selection Options */}
      {useAgentMode && onAgentSelectionChange && (
        <div className="mt-4 ml-8 space-y-2">
          <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
            Agent Selection:
          </h4>

          {/* Automatic (Recommended) */}
          <label className="flex items-start space-x-3 cursor-pointer group">
            <input
              type="radio"
              name="agent-selection"
              value="automatic"
              checked={agentSelection === 'automatic'}
              onChange={(e) => onAgentSelectionChange(e.target.value as AgentSelectionMode)}
              className="mt-0.5 w-4 h-4 text-primary-600 focus:ring-2 focus:ring-primary-500"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100 group-hover:text-primary-600 dark:group-hover:text-primary-400">
                🎯 Automatic (Smart Routing) <span className="text-xs text-green-600 dark:text-green-400 font-semibold">Recommended</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Intelligently routes between local and cloud agents based on task complexity and budget. Best balance of cost and performance.
              </p>
            </div>
          </label>

          {/* Local Agent Only */}
          <label className="flex items-start space-x-3 cursor-pointer group">
            <input
              type="radio"
              name="agent-selection"
              value="local_only"
              checked={agentSelection === 'local_only'}
              onChange={(e) => onAgentSelectionChange(e.target.value as AgentSelectionMode)}
              className="mt-0.5 w-4 h-4 text-primary-600 focus:ring-2 focus:ring-primary-500"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100 group-hover:text-primary-600 dark:group-hover:text-primary-400">
                💻 Local Agent Only <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold">Free</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Uses only local Ollama models (Qwen2.5-Coder, Llama-Vision, DeepSeek). No API costs, runs on your hardware.
              </p>
            </div>
          </label>

          {/* Claude CLI Only */}
          <label className="flex items-start space-x-3 cursor-pointer group">
            <input
              type="radio"
              name="agent-selection"
              value="claude_only"
              checked={agentSelection === 'claude_only'}
              onChange={(e) => onAgentSelectionChange(e.target.value as AgentSelectionMode)}
              className="mt-0.5 w-4 h-4 text-primary-600 focus:ring-2 focus:ring-primary-500"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100 group-hover:text-primary-600 dark:group-hover:text-primary-400">
                ☁️ Claude CLI Only <span className="text-xs text-amber-600 dark:text-amber-400 font-semibold">Premium</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Always uses Anthropic's Claude API. Highest quality for research and complex tasks. Costs apply ($3-15/MTok).
              </p>
            </div>
          </label>
        </div>
      )}

      {/* Budget Display (Compact) */}
      {useAgentMode && budgetStats && !showAdvanced && (
        <div className="mt-3 ml-8 space-y-2">
          {/* Daily Budget */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-600 dark:text-slate-400">
              Daily: ${budgetStats.daily.spent.toFixed(2)} / ${budgetStats.daily.limit.toFixed(2)}
            </span>
            <span className={`font-medium ${getBudgetColor(budgetStats.daily.percentage_used)}`}>
              {budgetStats.daily.percentage_used.toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full ${getBudgetBarColor(budgetStats.daily.percentage_used)}`}
              style={{ width: `${Math.min(budgetStats.daily.percentage_used, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Advanced Details */}
      {useAgentMode && showAdvanced && budgetStats && (
        <div className="mt-4 ml-8 space-y-4 border-t border-slate-200 dark:border-slate-700 pt-4">
          {/* Daily Budget Details */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Daily Budget
              </h4>
              <span className={`text-sm font-semibold ${getBudgetColor(budgetStats.daily.percentage_used)}`}>
                ${budgetStats.daily.remaining.toFixed(2)} remaining
              </span>
            </div>
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getBudgetBarColor(budgetStats.daily.percentage_used)}`}
                style={{ width: `${Math.min(budgetStats.daily.percentage_used, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span>Spent: ${budgetStats.daily.spent.toFixed(2)}</span>
              <span>Tasks: {budgetStats.daily.tasks}</span>
              <span>Limit: ${budgetStats.daily.limit.toFixed(2)}</span>
            </div>
          </div>

          {/* Monthly Budget Details */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Monthly Budget
              </h4>
              <span className={`text-sm font-semibold ${getBudgetColor(budgetStats.monthly.percentage_used)}`}>
                ${budgetStats.monthly.remaining.toFixed(2)} remaining
              </span>
            </div>
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getBudgetBarColor(budgetStats.monthly.percentage_used)}`}
                style={{ width: `${Math.min(budgetStats.monthly.percentage_used, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span>Spent: ${budgetStats.monthly.spent.toFixed(2)}</span>
              <span>Tasks: {budgetStats.monthly.tasks}</span>
              <span>Limit: ${budgetStats.monthly.limit.toFixed(2)}</span>
            </div>
          </div>

          {/* Warnings */}
          {budgetStats.warnings && budgetStats.warnings.length > 0 && (
            <div className="space-y-2">
              {budgetStats.warnings.map((warning, index) => (
                <div
                  key={index}
                  className={`text-xs p-2 rounded ${
                    warning.level === 'critical'
                      ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                      : 'bg-orange-100 dark:bg-orange-900/20 text-orange-800 dark:text-orange-200'
                  }`}
                >
                  {warning.level === 'critical' ? '🚨' : '⚠️'} {warning.message}
                </div>
              ))}
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={fetchBudgetStats}
            disabled={loading}
            className="w-full text-xs text-primary-600 dark:text-primary-400 hover:underline disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : '🔄 Refresh Budget Stats'}
          </button>
        </div>
      )}

      {/* Loading State */}
      {useAgentMode && !budgetStats && loading && (
        <div className="mt-3 ml-8 text-xs text-slate-500 dark:text-slate-400">
          Loading budget information...
        </div>
      )}
    </div>
  );
};
