import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Award, TrendingUp, Activity, Brain, Zap, CheckCircle2 } from 'lucide-react';

interface RewardBreakdown {
  score: number;
  weight: number;
  contribution: number;
  applicable: boolean;
}

interface RewardBreakdownMessage {
  type: 'multi_reward_breakdown' | 'batch_aggregate_rewards' | 'reward_weights_config';
  timestamp: string;
  batch_idx?: number;
  response_idx?: number;
  total_reward?: number;
  breakdown?: Record<string, RewardBreakdown>;
  reasoning_steps_count?: number;
  avg_total_reward?: number;
  avg_rewards?: Record<string, number>;
  avg_steps_count?: number;
  avg_tokens_per_step?: number;
  weights?: Record<string, number>;
}

interface RewardTrendData {
  batch: number;
  total: number;
  Correctness: number;
  ReasoningClarity: number;
  StepByStep: number;
  Efficiency: number;
  MathematicalNotation: number;
  Coherence: number;
}

interface ReasoningQualityData {
  batch: number;
  steps: number;
  tokens_per_step: number;
}

const REWARD_COLORS = {
  Correctness: '#10b981',      // green
  ReasoningClarity: '#3b82f6', // blue
  StepByStep: '#8b5cf6',       // purple
  Efficiency: '#f59e0b',       // orange
  MathematicalNotation: '#ef4444', // red
  Coherence: '#eab308'         // yellow
};

const REWARD_ICONS = {
  Correctness: CheckCircle2,
  ReasoningClarity: Brain,
  StepByStep: Activity,
  Efficiency: Zap,
  MathematicalNotation: Award,
  Coherence: TrendingUp
};

interface RewardBreakdownChartProps {
  jobId: string;
}

export default function RewardBreakdownChart({ jobId }: RewardBreakdownChartProps) {
  const [currentBreakdown, setCurrentBreakdown] = useState<Record<string, RewardBreakdown> | null>(null);
  const [currentTotal, setCurrentTotal] = useState<number>(0);
  const [trendData, setTrendData] = useState<RewardTrendData[]>([]);
  const [reasoningData, setReasoningData] = useState<ReasoningQualityData[]>([]);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/jobs/${jobId}/metrics`;

    console.log(`📡 Connecting to WebSocket: ${wsUrl}`);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message: RewardBreakdownMessage = JSON.parse(event.data);
        console.log('📊 Received metrics:', message.type);

        if (message.type === 'multi_reward_breakdown' && message.breakdown) {
          // Update current breakdown
          setCurrentBreakdown(message.breakdown);
          setCurrentTotal(message.total_reward || 0);

          // Add to trend data
          if (message.batch_idx !== undefined) {
            const newPoint: RewardTrendData = {
              batch: message.batch_idx,
              total: message.total_reward || 0,
              Correctness: message.breakdown.Correctness?.score || 0,
              ReasoningClarity: message.breakdown.ReasoningClarity?.score || 0,
              StepByStep: message.breakdown.StepByStep?.score || 0,
              Efficiency: message.breakdown.Efficiency?.score || 0,
              MathematicalNotation: message.breakdown.MathematicalNotation?.score || 0,
              Coherence: message.breakdown.Coherence?.score || 0
            };

            setTrendData((prev) => {
              const updated = [...prev, newPoint];
              // Keep last 100 points
              return updated.slice(-100);
            });
          }
        } else if (message.type === 'batch_aggregate_rewards') {
          // Update reasoning quality data
          if (message.batch_idx !== undefined) {
            const newPoint: ReasoningQualityData = {
              batch: message.batch_idx,
              steps: message.avg_steps_count || 0,
              tokens_per_step: message.avg_tokens_per_step || 0
            };

            setReasoningData((prev) => {
              const updated = [...prev, newPoint];
              return updated.slice(-100);
            });
          }
        } else if (message.type === 'reward_weights_config' && message.weights) {
          setWeights(message.weights);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setConnected(false);
    };

    // Cleanup
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [jobId]);

  const formatRewardName = (name: string) => {
    // Convert camelCase to Title Case with spaces
    return name.replace(/([A-Z])/g, ' $1').trim();
  };

  const currentBreakdownData = currentBreakdown
    ? Object.entries(currentBreakdown)
        .filter(([_, details]) => details.applicable)
        .map(([name, details]) => ({
          name: formatRewardName(name),
          score: details.score,
          contribution: details.contribution,
          weight: details.weight
        }))
    : [];

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm font-medium">
            {connected ? '🔴 Live Metrics' : '⚫ Disconnected'}
          </span>
        </div>
        {error && (
          <span className="text-sm text-red-500">{error}</span>
        )}
      </div>

      {/* Current Total Reward */}
      <div className="p-6 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm opacity-90">Current Total Reward</p>
            <p className="text-4xl font-bold mt-1">
              {currentTotal.toFixed(3)}
            </p>
          </div>
          <Award className="w-16 h-16 opacity-50" />
        </div>
        <div className="mt-2 text-sm opacity-90">
          {currentBreakdownData.length} active reward functions
        </div>
      </div>

      {/* Current Breakdown - Bar Chart */}
      {currentBreakdownData.length > 0 && (
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart className="w-5 h-5" />
            Current Reward Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={currentBreakdownData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis domain={[0, 1]} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  value.toFixed(3),
                  name === 'score' ? 'Score' : name === 'contribution' ? 'Contribution' : 'Weight'
                ]}
              />
              <Legend />
              <Bar dataKey="score" fill="#3b82f6" name="Score" />
              <Bar dataKey="contribution" fill="#10b981" name="Contribution" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Reward Weights */}
      {Object.keys(weights).length > 0 && (
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Reward Weights Configuration
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(weights).map(([name, weight]) => {
              const IconComponent = REWARD_ICONS[name as keyof typeof REWARD_ICONS] || Award;
              const color = REWARD_COLORS[name as keyof typeof REWARD_COLORS] || '#666';
              return (
                <div key={name} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <IconComponent className="w-5 h-5" style={{ color }} />
                  <div className="flex-1">
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {formatRewardName(name)}
                    </div>
                    <div className="text-lg font-bold" style={{ color }}>
                      {weight.toFixed(1)}x
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Reward Trend - Line Chart */}
      {trendData.length > 0 && (
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Reward Trends Over Time
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="batch" label={{ value: 'Batch', position: 'insideBottom', offset: -5 }} />
              <YAxis domain={[0, 1]} label={{ value: 'Score', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => value.toFixed(3)} />
              <Legend />
              <Line type="monotone" dataKey="total" stroke="#000" strokeWidth={3} name="Total" />
              {Object.entries(REWARD_COLORS).map(([name, color]) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={color}
                  strokeWidth={2}
                  name={formatRewardName(name)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Reward Contribution - Stacked Area */}
      {trendData.length > 0 && (
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Reward Contribution (Stacked)
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="batch" label={{ value: 'Batch', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Score', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => value.toFixed(3)} />
              <Legend />
              {Object.entries(REWARD_COLORS).map(([name, color]) => (
                <Area
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stackId="1"
                  stroke={color}
                  fill={color}
                  fillOpacity={0.6}
                  name={formatRewardName(name)}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Reasoning Quality */}
      {reasoningData.length > 0 && (
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Reasoning Quality Metrics
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={reasoningData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="batch" label={{ value: 'Batch', position: 'insideBottom', offset: -5 }} />
              <YAxis yAxisId="left" label={{ value: 'Steps', angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'Tokens/Step', angle: 90, position: 'insideRight' }} />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="steps"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Avg Steps Count"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="tokens_per_step"
                stroke="#f59e0b"
                strokeWidth={2}
                name="Avg Tokens/Step"
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded">
              <div className="text-sm text-purple-600 dark:text-purple-400">Optimal Steps</div>
              <div className="text-lg font-bold text-purple-700 dark:text-purple-300">3-7 steps</div>
            </div>
            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded">
              <div className="text-sm text-orange-600 dark:text-orange-400">Optimal Tokens/Step</div>
              <div className="text-lg font-bold text-orange-700 dark:text-orange-300">15-50 tokens</div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!connected && trendData.length === 0 && (
        <div className="p-12 text-center bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Activity className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            Waiting for training metrics...
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
            Metrics will appear when GRPO training starts
          </p>
        </div>
      )}
    </div>
  );
}
