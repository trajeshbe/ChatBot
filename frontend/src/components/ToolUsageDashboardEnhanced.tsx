/**
 * Tool Usage Dashboard - Enhanced Version
 *
 * Modern UI with glass morphism, animations, and interactive charts
 * Displays comprehensive tool usage statistics and analytics
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import CountUp from 'react-countup';
import {
  Activity, Clock, DollarSign, CheckCircle, XCircle,
  TrendingUp, Zap, Target, BarChart3, AlertTriangle
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

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

const COLORS = ['#6b9080', '#14b8a6', '#10b981', '#f59e0b', '#ef4444', '#0d9488', '#059669'];

const ToolUsageDashboardEnhanced: React.FC = () => {
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 glass-card-light rounded-xl border border-red-500/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-red-700 dark:text-red-300">Error Loading Statistics</p>
            <p className="text-sm text-red-600 dark:text-red-400 mt-1">{error}</p>
            <button
              onClick={fetchStats}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 smooth-transition"
            >
              Retry
            </button>
          </div>
        </div>
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
    ? ((summary.total_successful / summary.total_invocations) * 100)
    : 0;

  // Prepare data for pie chart
  const pieData = categories.map((category, index) => ({
    name: category.replace(/_/g, ' '),
    value: by_category[category].reduce((sum, tool) => sum + tool.total_invocations, 0),
    color: COLORS[index % COLORS.length]
  }));

  // Prepare data for bar chart (top 5 tools by invocations)
  const topTools = [...all_tools]
    .sort((a, b) => b.total_invocations - a.total_invocations)
    .slice(0, 5)
    .map(tool => ({
      name: tool.tool_name.length > 15 ? tool.tool_name.substring(0, 15) + '...' : tool.tool_name,
      calls: tool.total_invocations,
      success: tool.successful_invocations,
      failed: tool.failed_invocations
    }));

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
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl">
                  <BarChart3 className="w-8 h-8" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold mb-2">Tool Usage Analytics</h1>
                  <p className="text-primary-100 text-lg">Real-time monitoring and performance insights</p>
                </div>
              </div>

              {/* Time Range Filter */}
              <div className="glass-card px-4 py-2 rounded-xl">
                <select
                  value={days}
                  onChange={(e) => setDays(parseInt(e.target.value))}
                  className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
                >
                  <option value={1} className="text-slate-900">Last 24 hours</option>
                  <option value={7} className="text-slate-900">Last 7 days</option>
                  <option value={30} className="text-slate-900">Last 30 days</option>
                  <option value={90} className="text-slate-900">Last 90 days</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Summary Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl">
              <Target className="w-5 h-5 text-white" />
            </div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Total Tools</p>
          </div>
          <p className="text-3xl font-bold gradient-text-primary">
            <CountUp end={summary.total_tools} duration={2} />
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-secondary-500 to-primary-500 rounded-xl">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Total Calls</p>
          </div>
          <p className="text-3xl font-bold gradient-text-primary">
            <CountUp end={summary.total_invocations} duration={2} separator="," />
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl">
              <CheckCircle className="w-5 h-5 text-white" />
            </div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Success Rate</p>
          </div>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">
            <CountUp end={successRate} decimals={1} suffix="%" duration={2} />
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
              <DollarSign className="w-5 h-5 text-white" />
            </div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Total Cost</p>
          </div>
          <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
            $<CountUp end={summary.total_cost_usd} decimals={2} duration={2} />
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-xl">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Total Tokens</p>
          </div>
          <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
            <CountUp end={summary.total_tokens_used} duration={2} separator="," />
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
          className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-red-500 to-rose-500 rounded-xl">
              <XCircle className="w-5 h-5 text-white" />
            </div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Failed Calls</p>
          </div>
          <p className="text-3xl font-bold text-red-600 dark:text-red-400">
            <CountUp end={summary.total_failed} duration={2} />
          </p>
        </motion.div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Pie Chart - Category Distribution */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
          className="glass-card-light p-6 rounded-2xl"
        >
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500"></div>
            Usage by Category
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Bar Chart - Top Tools */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
          className="glass-card-light p-6 rounded-2xl"
        >
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-secondary-500 to-primary-500"></div>
            Top 5 Tools by Usage
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topTools}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="success" fill="#10b981" name="Successful" />
              <Bar dataKey="failed" fill="#ef4444" name="Failed" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Category Filter Pills */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedCategory(null)}
            className={`px-6 py-3 rounded-full font-semibold smooth-transition ${
              selectedCategory === null
                ? 'bg-gradient-to-r from-primary-600 to-secondary-600 text-white shadow-lg'
                : 'glass-card-light hover:shadow-md'
            }`}
          >
            All Categories
          </motion.button>
          {categories.map((category) => (
            <motion.button
              key={category}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSelectedCategory(category)}
              className={`px-6 py-3 rounded-full font-semibold smooth-transition ${
                selectedCategory === category
                  ? 'bg-gradient-to-r from-primary-600 to-secondary-600 text-white shadow-lg'
                  : 'glass-card-light hover:shadow-md'
              }`}
            >
              {category.replace(/_/g, ' ').toUpperCase()}
            </motion.button>
          ))}
        </div>
      )}

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {all_tools.length === 0 ? (
          <div className="col-span-full text-center p-12 glass-card-light rounded-2xl">
            <Activity className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <p className="text-lg text-gray-600 dark:text-gray-400">
              No tool usage data available for the selected time range
            </p>
          </div>
        ) : (
          all_tools.map((tool, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * (idx % 9) }}
              className="glass-card-light p-6 rounded-2xl hover-glow-primary smooth-transition relative overflow-hidden"
            >
              {/* Background decoration */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-500/10 to-transparent rounded-full blur-2xl"></div>

              <div className="relative z-10">
                {/* Tool Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h4 className="font-bold text-lg mb-1">{tool.tool_name}</h4>
                    <span className="px-2 py-1 rounded-full text-xs bg-slate-200 dark:bg-slate-700">
                      {tool.tool_category.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className={`p-2 rounded-xl ${
                    tool.success_rate_pct >= 95 ? 'bg-green-500/20' :
                    tool.success_rate_pct >= 80 ? 'bg-yellow-500/20' : 'bg-red-500/20'
                  }`}>
                    {tool.success_rate_pct >= 95 ? <CheckCircle className="w-5 h-5 text-green-500" /> :
                     tool.success_rate_pct >= 80 ? <AlertTriangle className="w-5 h-5 text-yellow-500" /> :
                     <XCircle className="w-5 h-5 text-red-500" />}
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Calls</p>
                    <p className="text-2xl font-bold gradient-text-primary">
                      {tool.total_invocations.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Success Rate</p>
                    <p className={`text-2xl font-bold ${
                      tool.success_rate_pct >= 95 ? 'text-green-600 dark:text-green-400' :
                      tool.success_rate_pct >= 80 ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-red-600 dark:text-red-400'
                    }`}>
                      {tool.success_rate_pct.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Avg Latency
                    </p>
                    <p className="text-lg font-semibold">{tool.avg_latency_ms.toFixed(0)}ms</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> P95 Latency
                    </p>
                    <p className="text-lg font-semibold">
                      {tool.p95_latency_ms ? `${tool.p95_latency_ms.toFixed(0)}ms` : 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Cost and Tokens */}
                {(tool.total_tokens_used > 0 || tool.total_cost_usd > 0) && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Tokens</p>
                        <p className="font-semibold">{tool.total_tokens_used.toLocaleString()}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500 dark:text-gray-400">Cost</p>
                        <p className="font-semibold text-orange-600 dark:text-orange-400">
                          ${tool.total_cost_usd.toFixed(4)}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
};

export default ToolUsageDashboardEnhanced;
