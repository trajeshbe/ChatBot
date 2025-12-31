/**
 * Tool Usage Dashboard
 *
 * Displays comprehensive tool usage statistics and analytics
 * including LLM calls, document processing, web scraping, and RAG services
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ToolStats {
  tool_category: string;
  tool_name: string;
  total_invocations: number;
  successful_invocations: number;
  failed_invocations: number;
  avg_latency_ms: number;
  median_latency_ms: number;
  p95_latency_ms: number;
  total_tokens_used: number;
  total_cost_usd: number;
  avg_quality_score: number;
  success_rate_pct: number;
  first_used: string;
  last_used: string;
}

interface Summary {
  total_tools: number;
  total_invocations: number;
  total_successful: number;
  total_failed: number;
  total_tokens_used: number;
  total_cost_usd: number;
}

interface ToolStatsResponse {
  summary: Summary;
  by_category: Record<string, ToolStats[]>;
  all_tools: ToolStats[];
}

const ToolUsageDashboard: React.FC = () => {
  const [stats, setStats] = useState<ToolStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, [days, selectedCategory]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        days: days.toString()
      });

      if (selectedCategory) {
        params.append('category', selectedCategory);
      }

      const response = await axios.get(
        `http://localhost:8000/api/v1/tool-stats/summary?${params}`
      );

      setStats(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch tool statistics');
      console.error('Error fetching tool stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-slate-600 dark:text-slate-400">Loading tool statistics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-red-700 dark:text-red-300">Error: {error}</p>
        <button
          onClick={fetchStats}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center p-8 text-slate-500 dark:text-slate-400">
        No tool statistics available
      </div>
    );
  }

  const { summary, by_category, all_tools } = stats;

  const categories = Object.keys(by_category);
  const successRate = summary.total_invocations > 0
    ? ((summary.total_successful / summary.total_invocations) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          🔧 Tool Usage Analytics
        </h2>

        {/* Time Range Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600 dark:text-slate-400">
            Time Range:
          </label>
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="px-3 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
          >
            <option value={1}>Last 24 hours</option>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div className="bg-gradient-to-br from-primary-500 to-primary-600 text-white p-4 rounded-lg shadow">
          <div className="text-xs uppercase opacity-90 mb-1">Total Tools</div>
          <div className="text-3xl font-bold">{summary.total_tools}</div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-4 rounded-lg shadow">
          <div className="text-xs uppercase opacity-90 mb-1">Total Calls</div>
          <div className="text-3xl font-bold">{summary.total_invocations.toLocaleString()}</div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-4 rounded-lg shadow">
          <div className="text-xs uppercase opacity-90 mb-1">Success Rate</div>
          <div className="text-3xl font-bold">{successRate}%</div>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-4 rounded-lg shadow">
          <div className="text-xs uppercase opacity-90 mb-1">Total Cost</div>
          <div className="text-3xl font-bold">${summary.total_cost_usd.toFixed(2)}</div>
        </div>

        <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 text-white p-4 rounded-lg shadow">
          <div className="text-xs uppercase opacity-90 mb-1">Total Tokens</div>
          <div className="text-3xl font-bold">{summary.total_tokens_used.toLocaleString()}</div>
        </div>

        <div className="bg-gradient-to-br from-red-500 to-red-600 text-white p-4 rounded-lg shadow">
          <div className="text-xs uppercase opacity-90 mb-1">Failed Calls</div>
          <div className="text-3xl font-bold">{summary.total_failed}</div>
        </div>
      </div>

      {/* Category Filter */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1 rounded text-sm font-medium ${
              selectedCategory === null
                ? 'bg-primary-600 text-white'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
            }`}
          >
            All Categories
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedCategory === category
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
              }`}
            >
              {category.replace(/_/g, ' ').toUpperCase()}
            </button>
          ))}
        </div>
      )}

      {/* Tools Table */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Tool
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Category
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Calls
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Success Rate
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Avg Latency
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  P95 Latency
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Tokens
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase">
                  Cost
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {all_tools.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                    No tool usage data available for the selected time range
                  </td>
                </tr>
              ) : (
                all_tools.map((tool, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                    <td className="px-4 py-3 text-sm font-medium text-slate-900 dark:text-white">
                      {tool.tool_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-200 dark:bg-slate-600">
                        {tool.tool_category.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-slate-900 dark:text-white">
                      {tool.total_invocations.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={`${
                        tool.success_rate_pct >= 95
                          ? 'text-green-600 dark:text-green-400'
                          : tool.success_rate_pct >= 80
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {tool.success_rate_pct}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-slate-600 dark:text-slate-400">
                      {tool.avg_latency_ms.toFixed(0)}ms
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-slate-600 dark:text-slate-400">
                      {tool.p95_latency_ms ? tool.p95_latency_ms.toFixed(0) : 'N/A'}ms
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-slate-600 dark:text-slate-400">
                      {tool.total_tokens_used ? tool.total_tokens_used.toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-slate-600 dark:text-slate-400">
                      {tool.total_cost_usd ? `$${tool.total_cost_usd.toFixed(4)}` : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Category Breakdown */}
      {categories.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {categories.map((category) => {
            const categoryTools = by_category[category];
            const categoryTotal = categoryTools.reduce((sum, tool) => sum + tool.total_invocations, 0);

            return (
              <div
                key={category}
                className="bg-white dark:bg-slate-800 rounded-lg shadow p-4"
              >
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
                  {category.replace(/_/g, ' ').toUpperCase()}
                </h3>
                <div className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                  Total Invocations: <span className="font-semibold text-slate-900 dark:text-white">{categoryTotal.toLocaleString()}</span>
                </div>
                <div className="space-y-1">
                  {categoryTools.map((tool, idx) => {
                    const percentage = categoryTotal > 0 ? (tool.total_invocations / categoryTotal) * 100 : 0;
                    return (
                      <div key={idx} className="flex items-center gap-2">
                        <div className="flex-1">
                          <div className="flex justify-between text-xs mb-0.5">
                            <span className="text-slate-700 dark:text-slate-300">{tool.tool_name}</span>
                            <span className="text-slate-500 dark:text-slate-400">{tool.total_invocations}</span>
                          </div>
                          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ToolUsageDashboard;
