import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Zap,
  Clock,
  Database,
  RefreshCw
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface DashboardStats {
  running_jobs: number;
  pending_approvals: number;
  active_models: number;
  datasets_ready: number;
}

interface GPUStats {
  total_gpus: number;
  allocated_gpus: number;
  available_gpus: number;
  active_jobs: string[];
}

interface MetricPoint {
  id: string;
  job_id: string;
  step: number;
  epoch: number;
  loss: number;
  learning_rate: number;
  accuracy?: number;
  additional_metrics?: Record<string, any>;
  timestamp: string;
}

interface DriftAlert {
  model_id: string;
  model_name: string;
  metric: string;
  baseline: number;
  current: number;
  degradation_pct: number;
  severity: 'warning' | 'critical';
}

interface CostSummary {
  total_gpu_hours: number;
  estimated_cost_usd: number;
  storage_gb: number;
  active_training_cost_per_hour: number;
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];
const REFRESH_INTERVAL = 5000; // 5 seconds

export default function MonitoringDashboard({ userRole }: { userRole: string }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [gpuStats, setGPUStats] = useState<GPUStats | null>(null);
  const [recentMetrics, setRecentMetrics] = useState<MetricPoint[]>([]);
  const [driftAlerts, setDriftAlerts] = useState<DriftAlert[]>([]);
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDashboardData = async () => {
    try {
      // Fetch dashboard stats
      const statsRes = await fetch('http://localhost:8000/api/v1/finetuning/stats', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Fetch GPU stats
      const gpuRes = await fetch('http://localhost:8000/api/v1/finetuning/gpu/stats', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
      });
      if (gpuRes.ok) {
        const gpuData = await gpuRes.json();
        setGPUStats(gpuData);
      }

      // Fetch recent training jobs to get metrics
      const jobsRes = await fetch('http://localhost:8000/api/v1/finetuning/jobs-public?limit=10', {
        headers: { 'Content-Type': 'application/json' }
      });
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();

        // Collect metrics from recent jobs
        let allMetrics: MetricPoint[] = [];
        for (const job of jobsData.jobs || []) {
          if (job.status === 'running' || job.status === 'completed') {
            const metricsRes = await fetch(
              `http://localhost:8000/api/v1/finetuning/jobs-public/${job.id}/metrics`,
              { headers: { 'Content-Type': 'application/json' } }
            );
            if (metricsRes.ok) {
              const metricsData = await metricsRes.json();
              allMetrics = [...allMetrics, ...(metricsData.metrics || [])];
            }
          }
        }
        setRecentMetrics(allMetrics.slice(0, 100)); // Keep last 100 points

        // Calculate cost summary
        const totalJobs = jobsData.jobs?.length || 0;
        const runningJobs = jobsData.jobs?.filter((j: any) => j.status === 'running').length || 0;
        const estimatedGPUHours = totalJobs * 2.5; // Mock: avg 2.5 hours per job
        const costPerGPUHour = 1.2; // Mock: $1.20/hour

        setCostSummary({
          total_gpu_hours: estimatedGPUHours,
          estimated_cost_usd: estimatedGPUHours * costPerGPUHour,
          storage_gb: totalJobs * 5.2, // Mock: 5.2 GB per job
          active_training_cost_per_hour: runningJobs * costPerGPUHour
        });
      }

      // Mock drift alerts (TODO: implement actual drift detection)
      const mockDriftAlerts: DriftAlert[] = [];
      if (Math.random() > 0.7) {
        mockDriftAlerts.push({
          model_id: 'mock-model-1',
          model_name: 'Customer Support QA v1.2.0',
          metric: 'accuracy',
          baseline: 0.87,
          current: 0.79,
          degradation_pct: -9.2,
          severity: 'warning'
        });
      }
      setDriftAlerts(mockDriftAlerts);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, REFRESH_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Prepare chart data
  const lossChartData = recentMetrics
    .filter(m => m.loss !== undefined)
    .slice(-30)
    .map(m => ({
      step: m.step,
      loss: m.loss,
      epoch: m.epoch
    }));

  const accuracyChartData = recentMetrics
    .filter(m => m.accuracy !== undefined)
    .slice(-30)
    .map(m => ({
      step: m.step,
      accuracy: (m.accuracy || 0) * 100,
      epoch: m.epoch
    }));

  const gpuUtilizationData = gpuStats ? [
    { name: 'Allocated', value: gpuStats.allocated_gpus },
    { name: 'Available', value: gpuStats.available_gpus }
  ] : [];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-6 h-6 text-indigo-600" />
          <h2 className="text-2xl font-bold">Monitoring Dashboard</h2>
        </div>
        <button
          onClick={() => setAutoRefresh(!autoRefresh)}
          className={`flex items-center gap-2 px-4 py-2 rounded ${
            autoRefresh ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
          Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
        </button>
      </div>

      {/* Drift Alerts */}
      {driftAlerts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <h3 className="font-semibold text-yellow-900">Model Drift Detected</h3>
          </div>
          <div className="space-y-2">
            {driftAlerts.map((alert, idx) => (
              <div key={idx} className="flex items-center justify-between bg-white rounded p-3">
                <div>
                  <p className="font-medium text-gray-900">{alert.model_name}</p>
                  <p className="text-sm text-gray-600">
                    {alert.metric}: {(alert.current * 100).toFixed(1)}% (baseline: {(alert.baseline * 100).toFixed(1)}%)
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingDown className="w-5 h-5 text-red-500" />
                  <span className="text-red-600 font-semibold">{alert.degradation_pct.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Running Jobs"
          value={stats?.running_jobs || 0}
          icon={<Zap className="w-6 h-6 text-yellow-600" />}
          color="yellow"
        />
        <StatCard
          title="Pending Approvals"
          value={stats?.pending_approvals || 0}
          icon={<Clock className="w-6 h-6 text-blue-600" />}
          color="blue"
        />
        <StatCard
          title="Active Models"
          value={stats?.active_models || 0}
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
          color="green"
        />
        <StatCard
          title="Datasets Ready"
          value={stats?.datasets_ready || 0}
          icon={<Database className="w-6 h-6 text-purple-600" />}
          color="purple"
        />
      </div>

      {/* GPU & Cost Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GPU Utilization */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">GPU Utilization</h3>
          {gpuStats ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total GPUs</span>
                <span className="text-2xl font-bold">{gpuStats.total_gpus}</span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={gpuUtilizationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={(entry) => `${entry.name}: ${entry.value}`}
                  >
                    {gpuUtilizationData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-green-50 rounded p-2 text-center">
                  <p className="text-gray-600">Allocated</p>
                  <p className="text-xl font-bold text-green-600">{gpuStats.allocated_gpus}</p>
                </div>
                <div className="bg-blue-50 rounded p-2 text-center">
                  <p className="text-gray-600">Available</p>
                  <p className="text-xl font-bold text-blue-600">{gpuStats.available_gpus}</p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No GPU data available</p>
          )}
        </div>

        {/* Cost Tracking */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-green-600" />
            <h3 className="text-lg font-semibold">Cost Tracking</h3>
          </div>
          {costSummary ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-sm text-gray-600">Total GPU Hours</p>
                  <p className="text-2xl font-bold text-gray-900">{costSummary.total_gpu_hours.toFixed(1)}</p>
                </div>
                <div className="bg-green-50 rounded p-3">
                  <p className="text-sm text-gray-600">Estimated Cost</p>
                  <p className="text-2xl font-bold text-green-600">${costSummary.estimated_cost_usd.toFixed(2)}</p>
                </div>
                <div className="bg-blue-50 rounded p-3">
                  <p className="text-sm text-gray-600">Storage Used</p>
                  <p className="text-2xl font-bold text-blue-600">{costSummary.storage_gb.toFixed(1)} GB</p>
                </div>
                <div className="bg-orange-50 rounded p-3">
                  <p className="text-sm text-gray-600">Active Cost/Hour</p>
                  <p className="text-2xl font-bold text-orange-600">${costSummary.active_training_cost_per_hour.toFixed(2)}</p>
                </div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-sm text-yellow-800">
                  💡 <strong>Cost Optimization:</strong> Consider using QLoRA for 60% cost reduction compared to full fine-tuning.
                </p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No cost data available</p>
          )}
        </div>
      </div>

      {/* Training Metrics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Loss Over Time */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Training Loss</h3>
          {lossChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={lossChartData}>
                <defs>
                  <linearGradient id="colorLoss" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" label={{ value: 'Training Step', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Loss', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white border border-gray-200 rounded p-2 shadow">
                          <p className="text-sm">Step: {payload[0].payload.step}</p>
                          <p className="text-sm">Epoch: {payload[0].payload.epoch}</p>
                          <p className="text-sm font-semibold text-red-600">
                            Loss: {payload[0].value?.toFixed(4)}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="loss"
                  stroke="#ef4444"
                  fillOpacity={1}
                  fill="url(#colorLoss)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No training data available
            </div>
          )}
        </div>

        {/* Accuracy Over Time */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Training Accuracy</h3>
          {accuracyChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={accuracyChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" label={{ value: 'Training Step', position: 'insideBottom', offset: -5 }} />
                <YAxis
                  domain={[0, 100]}
                  label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white border border-gray-200 rounded p-2 shadow">
                          <p className="text-sm">Step: {payload[0].payload.step}</p>
                          <p className="text-sm">Epoch: {payload[0].payload.epoch}</p>
                          <p className="text-sm font-semibold text-green-600">
                            Accuracy: {payload[0].value?.toFixed(2)}%
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981', r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No accuracy data available
            </div>
          )}
        </div>
      </div>

      {/* System Health Indicators */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <HealthIndicator
            label="Training Pipeline"
            status={stats && stats.running_jobs > 0 ? 'active' : 'idle'}
            message={stats && stats.running_jobs > 0
              ? `${stats.running_jobs} job(s) running`
              : 'No active training jobs'
            }
          />
          <HealthIndicator
            label="GPU Pool"
            status={gpuStats && gpuStats.available_gpus > 0 ? 'healthy' : 'warning'}
            message={gpuStats
              ? `${gpuStats.available_gpus}/${gpuStats.total_gpus} GPUs available`
              : 'No GPU data'
            }
          />
          <HealthIndicator
            label="Model Drift"
            status={driftAlerts.length > 0 ? 'warning' : 'healthy'}
            message={driftAlerts.length > 0
              ? `${driftAlerts.length} model(s) degraded`
              : 'All models performing normally'
            }
          />
        </div>
      </div>
    </div>
  );
}

// Helper Components

function StatCard({ title, value, icon, color }: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'yellow' | 'blue' | 'green' | 'purple';
}) {
  const colorClasses = {
    yellow: 'bg-yellow-50 border-yellow-200',
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    purple: 'bg-purple-50 border-purple-200'
  };

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-4`}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-gray-600">{title}</p>
        {icon}
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function HealthIndicator({ label, status, message }: {
  label: string;
  status: 'healthy' | 'warning' | 'active' | 'idle';
}) {
  const statusConfig = {
    healthy: { color: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
    warning: { color: 'bg-yellow-500', text: 'text-yellow-700', bg: 'bg-yellow-50' },
    active: { color: 'bg-blue-500', text: 'text-blue-700', bg: 'bg-blue-50' },
    idle: { color: 'bg-gray-400', text: 'text-gray-700', bg: 'bg-gray-50' }
  };

  const config = statusConfig[status];

  return (
    <div className={`${config.bg} border border-gray-200 rounded p-4`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-3 h-3 rounded-full ${config.color} ${status === 'active' ? 'animate-pulse' : ''}`} />
        <p className="font-semibold text-gray-900">{label}</p>
      </div>
      <p className={`text-sm ${config.text}`}>{message}</p>
    </div>
  );
}
