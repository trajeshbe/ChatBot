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
  ThumbsDown,
  Star
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

interface HumanFeedback {
  id: string;
  session_id: string;
  message_id: string | null;
  thumbs_up: boolean | null;
  thumbs_down: boolean | null;
  rating: number | null;
  accuracy_rating: number | null;
  helpfulness_rating: number | null;
  clarity_rating: number | null;
  feedback_text: string | null;
  feedback_type: string;
  created_at: string;
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
  const [feedback, setFeedback] = useState<HumanFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchAnalytics();
    fetchRecentScores();
    fetchFeedback();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAnalytics();
        fetchRecentScores();
        fetchFeedback();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [sessionId, autoRefresh, refreshInterval]);

  const fetchAnalytics = async () => {
    try {
      setError(null);
      const params: any = { days: 30 };
      if (sessionId) {
        params.session_id = sessionId;
      }

      const response = await axios.get(`${API_URL}/api/v1/evaluation/analytics`, { params });
      setAnalytics(response.data);
      setLoading(false);
    } catch (error: any) {
      console.error('Failed to fetch analytics:', error);
      setError(error?.response?.data?.detail || error?.message || 'Failed to load evaluation analytics');
      setLoading(false);
      // Set empty analytics on error so UI doesn't stay in loading state
      setAnalytics({
        total_evaluations: 0,
        avg_overall_score: 0,
        avg_scores_by_method: {},
        score_distribution: {},
        common_issues: {},
        time_series: []
      });
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
      setRecentScores([]);
    }
  };

  const fetchFeedback = async () => {
    try {
      const params: any = { limit: 20 };
      if (sessionId) {
        params.session_id = sessionId;
      }

      const response = await axios.get(`${API_URL}/api/v1/evaluation/feedback`, { params });
      setFeedback(response.data);
    } catch (error) {
      console.error('Failed to fetch feedback:', error);
      setFeedback([]);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 bg-white rounded-lg shadow-lg">
        <Activity className="w-6 h-6 animate-pulse text-blue-600" />
        <span className="ml-2 text-gray-600">Loading evaluation analytics...</span>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-lg shadow-lg">
        <XCircle className="w-16 h-16 text-red-400 mb-4" />
        <h3 className="text-xl font-semibold text-gray-800 mb-2">Unable to Load Dashboard</h3>
        <p className="text-gray-600 text-center max-w-md">
          Failed to fetch evaluation data. Please check the backend connection and try again.
        </p>
        <button
          onClick={() => { setLoading(true); fetchAnalytics(); fetchRecentScores(); }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="text-red-800 font-semibold">Error Loading Data</h4>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Empty State */}
      {analytics.total_evaluations === 0 && !error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <BarChart className="w-12 h-12 text-blue-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No Evaluations Yet</h3>
          <p className="text-gray-600 max-w-lg mx-auto">
            Start using the RAG system with evaluation enabled to see metrics and insights here.
            Per-response evaluation metrics appear automatically after each chat response.
          </p>
        </div>
      )}

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

      {/* Human Feedback */}
      {feedback.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <ThumbsUp className="w-5 h-5 mr-2 text-blue-600" />
            Human Feedback
          </h3>

          {/* Feedback Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Thumbs Up/Down Summary */}
            <div className="border rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-3">Helpful Ratings</div>
              <div className="flex items-center justify-around">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <ThumbsUp className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-green-600">
                    {feedback.filter(f => f.thumbs_up === true).length}
                  </div>
                  <div className="text-xs text-gray-500">Helpful</div>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <ThumbsDown className="w-6 h-6 text-red-600" />
                  </div>
                  <div className="text-2xl font-bold text-red-600">
                    {feedback.filter(f => f.thumbs_up === false).length}
                  </div>
                  <div className="text-xs text-gray-500">Not Helpful</div>
                </div>
              </div>
            </div>

            {/* Star Ratings Summary */}
            <div className="border rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-3">Star Ratings</div>
              <div className="space-y-1">
                {[5, 4, 3, 2, 1].map(stars => {
                  const count = feedback.filter(f => f.rating === stars).length;
                  const percentage = feedback.length > 0 ? (count / feedback.length) * 100 : 0;
                  return (
                    <div key={stars} className="flex items-center space-x-2">
                      <div className="flex items-center space-x-1 w-16">
                        <span className="text-xs text-gray-600">{stars}</span>
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                      </div>
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-yellow-500 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600 w-8">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Average Rating */}
            <div className="border rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-3">Average Rating</div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">
                  {feedback.filter(f => f.rating !== null).length > 0
                    ? (
                        feedback
                          .filter(f => f.rating !== null)
                          .reduce((sum, f) => sum + (f.rating || 0), 0) /
                        feedback.filter(f => f.rating !== null).length
                      ).toFixed(1)
                    : 'N/A'}
                </div>
                <div className="flex justify-center mt-2">
                  {[1, 2, 3, 4, 5].map(star => (
                    <Star
                      key={star}
                      className={`w-5 h-5 ${
                        feedback.filter(f => f.rating !== null).length > 0 &&
                        star <=
                          feedback
                            .filter(f => f.rating !== null)
                            .reduce((sum, f) => sum + (f.rating || 0), 0) /
                            feedback.filter(f => f.rating !== null).length
                          ? 'text-yellow-500 fill-current'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Based on {feedback.filter(f => f.rating !== null).length} ratings
                </div>
              </div>
            </div>
          </div>

          {/* Recent Feedback Entries */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Feedback</h4>
            {feedback.slice(0, 10).map((fb) => (
              <div key={fb.id} className="border-l-4 border-blue-500 bg-gray-50 rounded-r-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {fb.thumbs_up !== null && (
                        <div className="flex items-center space-x-1">
                          {fb.thumbs_up ? (
                            <ThumbsUp className="w-4 h-4 text-green-600" />
                          ) : (
                            <ThumbsDown className="w-4 h-4 text-red-600" />
                          )}
                          <span className={`text-sm font-medium ${fb.thumbs_up ? 'text-green-600' : 'text-red-600'}`}>
                            {fb.thumbs_up ? 'Helpful' : 'Not Helpful'}
                          </span>
                        </div>
                      )}
                      {fb.rating !== null && (
                        <div className="flex items-center space-x-1">
                          {[...Array(fb.rating)].map((_, i) => (
                            <Star key={i} className="w-4 h-4 text-yellow-500 fill-current" />
                          ))}
                          <span className="text-sm text-gray-600 ml-1">
                            ({fb.rating}/5)
                          </span>
                        </div>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(fb.created_at).toLocaleString()}
                      </span>
                    </div>
                    {fb.feedback_text && (
                      <p className="text-sm text-gray-700 italic">"{fb.feedback_text}"</p>
                    )}
                  </div>
                </div>
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
