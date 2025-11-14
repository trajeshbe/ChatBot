/**
 * Evaluation Dashboard Component
 *
 * Real-time visualization of evaluation metrics and analytics:
 * - Overall score trends
 * - Method-specific scores
 * - Common issues detection
 * - Performance metrics
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Activity,
  Clock,
  Target,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

interface EvaluationScore {
  id: string;
  overall_score: number;
  scores: Record<string, any>;
  evaluation_time_ms: number;
  enabled_methods: string[];
  metadata: any;
  errors: any[];
  created_at: string;
}

interface EvaluationAnalytics {
  total_evaluations: number;
  avg_overall_score: number;
  avg_scores_by_method: Record<string, number>;
  score_distribution: Record<string, number>;
  common_issues: Record<string, number>;
  time_series: Array<{
    date: string;
    avg_score: number;
    count: number;
  }>;
}

interface EvaluationDashboardProps {
  sessionId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const EvaluationDashboard: React.FC<EvaluationDashboardProps> = ({
  sessionId,
  autoRefresh = true,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [analytics, setAnalytics] = useState<EvaluationAnalytics | null>(null);
  const [recentScores, setRecentScores] = useState<EvaluationScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchAnalytics();
    fetchRecentScores();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAnalytics();
        fetchRecentScores();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [sessionId, autoRefresh, refreshInterval]);

  const fetchAnalytics = async () => {
    try {
      const params: any = { days: 30 };
      if (sessionId) {
        params.session_id = sessionId;
      }

      const response = await axios.get(`${API_URL}/api/v1/evaluation/analytics`, { params });
      setAnalytics(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      setLoading(false);
    }
  };

  const fetchRecentScores = async () => {
    try {
      const params: any = { limit: 10 };
      if (sessionId) {
        params.session_id = sessionId;
      }

      const response = await axios.get(`${API_URL}/api/v1/evaluation/results`, { params });
      setRecentScores(response.data);
    } catch (error) {
      console.error('Failed to fetch recent scores:', error);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (score >= 0.6) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  if (loading || !analytics) {
    return (
      <div className="flex items-center justify-center p-8 bg-white rounded-lg shadow-lg">
        <Activity className="w-6 h-6 animate-pulse text-blue-600" />
        <span className="ml-2 text-gray-600">Loading evaluation analytics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Evaluations */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Evaluations</p>
              <p className="text-2xl font-bold text-gray-800">{analytics.total_evaluations}</p>
            </div>
            <BarChart className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        {/* Average Score */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Average Score</p>
              <p className={`text-2xl font-bold ${analytics.avg_overall_score >= 0.7 ? 'text-green-600' : 'text-yellow-600'}`}>
                {(analytics.avg_overall_score * 100).toFixed(1)}%
              </p>
            </div>
            <Target className="w-8 h-8 text-green-600" />
          </div>
        </div>

        {/* High Quality */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">High Quality (≥80%)</p>
              <p className="text-2xl font-bold text-green-600">
                {analytics.score_distribution['0.8-1.0'] || 0}
              </p>
            </div>
            <ThumbsUp className="w-8 h-8 text-green-600" />
          </div>
        </div>

        {/* Issues Detected */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Issues Detected</p>
              <p className="text-2xl font-bold text-red-600">
                {Object.values(analytics.common_issues).reduce((sum, count) => sum + count, 0)}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Score Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
          Score Distribution
        </h3>
        <div className="space-y-3">
          {Object.entries(analytics.score_distribution).map(([range, count]) => {
            const total = analytics.total_evaluations;
            const percentage = total > 0 ? (count / total) * 100 : 0;
            const color = range === '0.8-1.0' ? 'bg-green-500' :
                         range === '0.6-0.8' ? 'bg-blue-500' :
                         range === '0.4-0.6' ? 'bg-yellow-500' : 'bg-red-500';

            return (
              <div key={range}>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>{range}</span>
                  <span>{count} ({percentage.toFixed(1)}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`${color} h-2 rounded-full transition-all duration-500`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Average Scores by Method */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-600" />
          Average Scores by Method
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(analytics.avg_scores_by_method).map(([method, score]) => {
            const scoreValue = typeof score === 'number' ? score : 0;
            const displayName = method.split('.').pop()?.replace(/_/g, ' ') || method;

            return (
              <div
                key={method}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedMetric(method)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {displayName}
                  </span>
                  {getScoreIcon(scoreValue)}
                </div>
                <div className="flex items-end space-x-2">
                  <span className={`text-2xl font-bold ${getScoreColor(scoreValue)}`}>
                    {(scoreValue * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      scoreValue >= 0.8 ? 'bg-green-500' :
                      scoreValue >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${scoreValue * 100}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Common Issues */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2 text-red-600" />
          Common Issues
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(analytics.common_issues).map(([issue, count]) => (
            <div key={issue} className="border rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 capitalize">
                  {issue.replace(/_/g, ' ')}
                </span>
                <span className={`px-2 py-1 rounded text-sm font-bold ${
                  count > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
                }`}>
                  {count}
                </span>
              </div>
              {count > 0 && (
                <div className="mt-2 text-xs text-red-600">
                  Detected in {((count / analytics.total_evaluations) * 100).toFixed(1)}% of evaluations
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Time Series Chart */}
      {analytics.time_series.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-blue-600" />
            Score Trends (Last 30 Days)
          </h3>
          <div className="space-y-2">
            {analytics.time_series.slice(-14).map((dataPoint) => (
              <div key={dataPoint.date} className="flex items-center space-x-4">
                <span className="text-sm text-gray-600 w-24">{dataPoint.date}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
                  <div
                    className={`h-6 rounded-full flex items-center justify-end pr-2 text-xs font-medium text-white ${
                      dataPoint.avg_score >= 0.8 ? 'bg-green-500' :
                      dataPoint.avg_score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${dataPoint.avg_score * 100}%` }}
                  >
                    {(dataPoint.avg_score * 100).toFixed(0)}%
                  </div>
                </div>
                <span className="text-sm text-gray-500 w-16">
                  ({dataPoint.count})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Evaluations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-blue-600" />
          Recent Evaluations
        </h3>
        <div className="space-y-3">
          {recentScores.map((score) => (
            <div key={score.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    {getScoreIcon(score.overall_score)}
                    <span className="font-semibold text-gray-800">
                      Overall Score: {(score.overall_score * 100).toFixed(1)}%
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(score.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {score.enabled_methods.map((method) => (
                      <span
                        key={method}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                      >
                        {method.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                  {score.errors.length > 0 && (
                    <div className="flex items-center space-x-2 text-red-600 text-sm">
                      <AlertCircle className="w-4 h-4" />
                      <span>{score.errors.length} evaluation error(s)</span>
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">Evaluation Time</div>
                  <div className="font-medium text-gray-800">
                    {score.evaluation_time_ms.toFixed(0)}ms
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EvaluationDashboard;
