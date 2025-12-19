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
  RefreshCw,
  ChevronRight,
  CheckCircle,
  Loader,
  ExternalLink,
  BarChart3,
  Server,
  Eye
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

interface RunningJob {
  id: string;
  name: string;
  base_model: string;
  status: string;
  progress: number;
  training_stage: string;
  stage_details: any;
  stage_started_at: string | null;
  stage_completed_at: string | null;
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];
const REFRESH_INTERVAL = 5000; // 5 seconds

export default function MonitoringDashboard({ userRole }: { userRole: string }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [gpuStats, setGPUStats] = useState<GPUStats | null>(null);
  const [recentMetrics, setRecentMetrics] = useState<MetricPoint[]>([]);
  const [driftAlerts, setDriftAlerts] = useState<DriftAlert[]>([]);
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [runningJobs, setRunningJobs] = useState<RunningJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDashboardData = async () => {
    try {
      // Fetch dashboard stats (using public endpoint for testing)
      const statsRes = await fetch('http://localhost:8000/api/v1/finetuning/stats-public', {
        headers: { 'Content-Type': 'application/json' }
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Fetch GPU stats (using public endpoint for testing)
      const gpuRes = await fetch('http://localhost:8000/api/v1/finetuning/gpu/stats-public', {
        headers: { 'Content-Type': 'application/json' }
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

        // Filter running jobs for pipeline stage visualization
        const running = (jobsData.jobs || []).filter((j: any) => j.status === 'running' || j.status === 'queued');
        setRunningJobs(running);

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

      {/* External Monitoring Dashboards */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Eye className="w-6 h-6 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">External Monitoring & Observability</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Grafana */}
          <a
            href="http://localhost:3000/d/finetuning-metrics"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white hover:bg-gray-50 border border-gray-200 rounded-lg p-4 transition-all hover:shadow-lg group"
          >
            <div className="flex items-center justify-between mb-2">
              <BarChart3 className="w-8 h-8 text-orange-600" />
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-orange-600 transition-colors" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">Grafana</h4>
            <p className="text-sm text-gray-600 mb-2">Training metrics & loss curves</p>
            <span className="text-xs text-orange-600 font-medium">View Dashboard →</span>
          </a>

          {/* Prometheus */}
          <a
            href="http://localhost:9090/graph"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white hover:bg-gray-50 border border-gray-200 rounded-lg p-4 transition-all hover:shadow-lg group"
          >
            <div className="flex items-center justify-between mb-2">
              <Server className="w-8 h-8 text-red-600" />
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">Prometheus</h4>
            <p className="text-sm text-gray-600 mb-2">Raw metrics & queries</p>
            <span className="text-xs text-red-600 font-medium">Query Metrics →</span>
          </a>

          {/* MinIO */}
          <a
            href="http://localhost:9001"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white hover:bg-gray-50 border border-gray-200 rounded-lg p-4 transition-all hover:shadow-lg group"
          >
            <div className="flex items-center justify-between mb-2">
              <Database className="w-8 h-8 text-purple-600" />
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-purple-600 transition-colors" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">MinIO</h4>
            <p className="text-sm text-gray-600 mb-2">Model checkpoints & datasets</p>
            <span className="text-xs text-purple-600 font-medium">Browse Storage →</span>
          </a>

          {/* Redis Insight */}
          <a
            href="http://localhost:8002"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white hover:bg-gray-50 border border-gray-200 rounded-lg p-4 transition-all hover:shadow-lg group"
          >
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-8 h-8 text-green-600" />
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-green-600 transition-colors" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">Redis Insight</h4>
            <p className="text-sm text-gray-600 mb-2">Cache & session data</p>
            <span className="text-xs text-green-600 font-medium">Inspect Cache →</span>
          </a>
        </div>
        <div className="mt-4 bg-white/50 border border-indigo-100 rounded p-3">
          <p className="text-xs text-gray-600">
            <strong className="text-indigo-700">💡 Pro Tip:</strong> Use Grafana for live training metrics,
            Prometheus for custom queries, MinIO to download checkpoints, and Redis Insight to debug caching issues.
          </p>
        </div>
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

      {/* Pipeline Stage Visualization */}
      {runningJobs.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Active Training Pipelines</h3>
          <div className="space-y-4">
            {runningJobs.map((job) => (
              <PipelineStageVisualization key={job.id} job={job} />
            ))}
          </div>
        </div>
      )}

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

function PipelineStageVisualization({ job }: { job: RunningJob }) {
  // Define pipeline stages in order
  const stages = [
    { id: 'queued', label: 'Queued' },
    { id: 'setup', label: 'Setup' },
    { id: 'tokenizer_load', label: 'Tokenizer' },
    { id: 'model_download', label: 'Download' },
    { id: 'model_load', label: 'Load Model' },
    { id: 'dataset_prep', label: 'Prep Data' },
    { id: 'training', label: 'Training' },
    { id: 'checkpoint_save', label: 'Checkpoint' },
    { id: 'completed', label: 'Complete' }
  ];

  const currentStageIndex = stages.findIndex(s => s.id === job.training_stage);

  const getStageStatus = (index: number) => {
    if (index < currentStageIndex) return 'completed';
    if (index === currentStageIndex) return 'active';
    return 'pending';
  };

  const formatElapsedTime = (startTime: string | null) => {
    if (!startTime) return '';
    const start = new Date(startTime).getTime();
    const now = Date.now();
    const elapsed = Math.floor((now - start) / 1000); // seconds

    if (elapsed < 60) return `${elapsed}s`;
    if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m`;
    return `${Math.floor(elapsed / 3600)}h ${Math.floor((elapsed % 3600) / 60)}m`;
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      {/* Job Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="font-semibold text-gray-900">{job.name}</h4>
          <p className="text-sm text-gray-600">{job.base_model}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-indigo-600">{job.progress.toFixed(0)}%</div>
          {job.stage_started_at && (
            <div className="text-xs text-gray-500">
              {formatElapsedTime(job.stage_started_at)} elapsed
            </div>
          )}
        </div>
      </div>

      {/* Pipeline Stages */}
      <div className="relative">
        <div className="flex items-center justify-between">
          {stages.map((stage, index) => {
            const status = getStageStatus(index);
            return (
              <div key={stage.id} className="flex flex-col items-center flex-1">
                {/* Stage Icon */}
                <div className="relative z-10">
                  {status === 'completed' && (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  )}
                  {status === 'active' && (
                    <Loader className="w-6 h-6 text-blue-600 animate-spin" />
                  )}
                  {status === 'pending' && (
                    <div className="w-6 h-6 rounded-full border-2 border-gray-300" />
                  )}
                </div>
                {/* Stage Label */}
                <div className={`mt-2 text-xs text-center ${
                  status === 'active' ? 'font-semibold text-blue-600' :
                  status === 'completed' ? 'text-gray-700' :
                  'text-gray-400'
                }`}>
                  {stage.label}
                </div>
              </div>
            );
          })}
        </div>

        {/* Connecting Line */}
        <div className="absolute top-3 left-0 right-0 h-0.5 bg-gray-200 -z-0" style={{ width: '100%', marginLeft: '0', marginRight: '0' }}>
          <div
            className="h-full bg-blue-600 transition-all duration-500"
            style={{ width: `${(currentStageIndex / (stages.length - 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Stage Details */}
      {job.stage_details && Object.keys(job.stage_details).length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
          <p className="font-semibold text-gray-700 mb-1">Stage Details:</p>
          <div className="space-y-1">
            {Object.entries(job.stage_details).map(([key, value]) => (
              <div key={key} className="flex justify-between text-gray-600">
                <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-mono">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
