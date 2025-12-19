import React, { useState } from 'react';
import {
  Activity,
  BarChart3,
  Code,
  Database,
  ExternalLink,
  Server,
  Layers,
  Cloud,
  GitBranch,
  Shield,
  Cpu,
  Network,
  Eye,
  DollarSign,
  Terminal,
  Zap,
  Container,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface ServiceLink {
  name: string;
  url: string;
  port?: number;
  status: 'live' | 'k8s-only' | 'configured';
  credentials?: string;
}

interface TechStackCategory {
  category: string;
  icon: React.ReactNode;
  color: string;
  services: {
    name: string;
    description: string;
    links: ServiceLink[];
  }[];
}

const techStack: TechStackCategory[] = [
  {
    category: 'Frontend & Ingress',
    icon: <Code className="w-6 h-6" />,
    color: 'blue',
    services: [
      {
        name: 'Next.js + Tailwind',
        description: 'Frontend UI',
        links: [
          { name: 'UI', url: 'http://localhost:3001', port: 3001, status: 'live' }
        ]
      },
      {
        name: 'Envoy (Contour)',
        description: 'API Gateway & Load Balancer',
        links: [
          { name: 'Proxy', url: 'http://localhost:8888', port: 8888, status: 'live' },
          { name: 'Admin', url: 'http://localhost:9901', port: 9901, status: 'live' }
        ]
      },
      {
        name: 'Istio Ambient',
        description: 'Service Mesh',
        links: [
          { name: 'Config', url: '/infrastructure/istio/ambient-config.yaml', status: 'configured' }
        ]
      }
    ]
  },
  {
    category: 'API & Backend',
    icon: <Server className="w-6 h-6" />,
    color: 'green',
    services: [
      {
        name: 'FastAPI',
        description: 'REST API Backend',
        links: [
          { name: 'API', url: 'http://localhost:8000', port: 8000, status: 'live' },
          { name: 'Docs', url: 'http://localhost:8000/docs', status: 'live' }
        ]
      },
      {
        name: 'GraphQL (Strawberry)',
        description: 'GraphQL API',
        links: [
          { name: 'GraphQL', url: 'http://localhost:8000/graphql', status: 'live' }
        ]
      }
    ]
  },
  {
    category: 'LLM Runtime',
    icon: <Cpu className="w-6 h-6" />,
    color: 'purple',
    services: [
      {
        name: 'Ollama',
        description: 'Local LLM Inference (CPU fallback)',
        links: [
          { name: 'API', url: 'http://localhost:11434', port: 11434, status: 'live' },
          { name: 'Models', url: 'http://localhost:11434/api/tags', status: 'live' }
        ]
      },
      {
        name: 'vLLM on Kube-Ray',
        description: 'Distributed GPU inference',
        links: [
          { name: 'Config', url: '/ml/vllm/', status: 'configured' }
        ]
      }
    ]
  },
  {
    category: 'Data & Storage',
    icon: <Database className="w-6 h-6" />,
    color: 'indigo',
    services: [
      {
        name: 'PostgreSQL + pgvector',
        description: 'Vector database',
        links: [
          { name: 'DB', url: 'postgres://localhost:5433', port: 5433, status: 'live' }
        ]
      },
      {
        name: 'MinIO',
        description: 'Object storage (Ozone-ready)',
        links: [
          { name: 'Console', url: 'http://localhost:9001', port: 9001, status: 'live', credentials: 'minioadmin/minioadmin' },
          { name: 'API', url: 'http://localhost:9000', port: 9000, status: 'live' }
        ]
      },
      {
        name: 'Redis 7.2 + VSS',
        description: 'Semantic cache',
        links: [
          { name: 'Insight', url: 'http://localhost:8002', port: 8002, status: 'live' },
          { name: 'Redis', url: 'redis://localhost:6380', port: 6380, status: 'live' }
        ]
      }
    ]
  },
  {
    category: 'Orchestration & Agents',
    icon: <Network className="w-6 h-6" />,
    color: 'orange',
    services: [
      {
        name: 'Prefect 3',
        description: 'Agent DAG orchestration (LangGraph inside)',
        links: [
          { name: 'UI', url: 'http://localhost:4200', port: 4200, status: 'live' }
        ]
      },
      {
        name: 'Apache Flink',
        description: 'Stream processing for Feast',
        links: [
          { name: 'JobManager', url: 'http://localhost:8081', port: 8081, status: 'live' }
        ]
      },
      {
        name: 'Feast',
        description: 'Feature store on Flink',
        links: [
          { name: 'Config', url: '/ml/feast/', status: 'configured' }
        ]
      }
    ]
  },
  {
    category: 'Observability & Traces',
    icon: <Eye className="w-6 h-6" />,
    color: 'red',
    services: [
      {
        name: 'Grafana',
        description: 'Dashboards & visualization',
        links: [
          { name: 'Dashboard', url: 'http://localhost:3000', port: 3000, status: 'live', credentials: 'admin/admin' },
          { name: 'Fine-Tuning', url: 'http://localhost:3000/d/finetuning-metrics', status: 'live' }
        ]
      },
      {
        name: 'Prometheus',
        description: 'Metrics collection',
        links: [
          { name: 'UI', url: 'http://localhost:9090', port: 9090, status: 'live' },
          { name: 'Targets', url: 'http://localhost:9090/targets', status: 'live' }
        ]
      },
      {
        name: 'Loki',
        description: 'Log aggregation',
        links: [
          { name: 'API', url: 'http://localhost:3100', port: 3100, status: 'live' },
          { name: 'Logs in Grafana', url: 'http://localhost:3000/explore', status: 'live' }
        ]
      },
      {
        name: 'Tempo',
        description: 'Distributed tracing',
        links: [
          { name: 'Config', url: '/observability/tempo/', status: 'configured' },
          { name: 'Traces in Grafana', url: 'http://localhost:3000/explore', status: 'live' }
        ]
      },
      {
        name: 'Promtail',
        description: 'Log shipper to Loki',
        links: [
          { name: 'Running', url: '#', status: 'live' }
        ]
      }
    ]
  },
  {
    category: 'Cost & Governance',
    icon: <DollarSign className="w-6 h-6" />,
    color: 'yellow',
    services: [
      {
        name: 'OpenCost',
        description: 'Real-time $/inference tracking',
        links: [
          { name: 'Config', url: '/observability/opencost/', status: 'configured' },
          { name: 'Dashboard', url: 'http://localhost:9003', port: 9003, status: 'k8s-only' }
        ]
      },
      {
        name: 'OPA Gatekeeper',
        description: 'Policy enforcement',
        links: [
          { name: 'Policies', url: '/infrastructure/opa/', status: 'configured' }
        ]
      }
    ]
  },
  {
    category: 'GitOps & CI/CD',
    icon: <GitBranch className="w-6 h-6" />,
    color: 'pink',
    services: [
      {
        name: 'Argo CD',
        description: 'GitOps deployment',
        links: [
          { name: 'Config', url: '/infrastructure/argocd/', status: 'configured' },
          { name: 'UI', url: 'http://localhost:8080', port: 8080, status: 'k8s-only' }
        ]
      },
      {
        name: 'Tekton',
        description: 'CI/CD pipelines',
        links: [
          { name: 'Dashboard', url: 'http://localhost:9097', port: 9097, status: 'k8s-only' }
        ]
      }
    ]
  },
  {
    category: 'Dev Tools',
    icon: <Terminal className="w-6 h-6" />,
    color: 'gray',
    services: [
      {
        name: 'DevContainer',
        description: 'Containerized dev environment',
        links: [
          { name: 'Config', url: '/.devcontainer/devcontainer.json', status: 'configured' }
        ]
      },
      {
        name: 'Skaffold',
        description: 'Local K8s dev loop',
        links: [
          { name: 'Config', url: '/devops/skaffold/skaffold.yaml', status: 'configured' }
        ]
      },
      {
        name: 'mirrord',
        description: 'Remote debugging',
        links: [
          { name: 'Docs', url: 'https://mirrord.dev', status: 'configured' }
        ]
      }
    ]
  }
];

const colorClasses: Record<string, { bg: string; border: string; text: string; hover: string }> = {
  blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', hover: 'hover:bg-blue-100' },
  green: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', hover: 'hover:bg-green-100' },
  purple: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', hover: 'hover:bg-purple-100' },
  indigo: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-700', hover: 'hover:bg-indigo-100' },
  orange: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', hover: 'hover:bg-orange-100' },
  red: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', hover: 'hover:bg-red-100' },
  yellow: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', hover: 'hover:bg-yellow-100' },
  pink: { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-700', hover: 'hover:bg-pink-100' },
  gray: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', hover: 'hover:bg-gray-100' }
};

const statusBadge: Record<ServiceLink['status'], { bg: string; text: string; label: string }> = {
  live: { bg: 'bg-green-100', text: 'text-green-700', label: '🟢 Live' },
  'k8s-only': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '🟡 K8s Only' },
  configured: { bg: 'bg-gray-100', text: 'text-gray-700', label: '⚙️ Configured' }
};

export default function TechStackMonitoring() {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Observability & Traces']));

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const expandAll = () => {
    setExpandedCategories(new Set(techStack.map(cat => cat.category)));
  };

  const collapseAll = () => {
    setExpandedCategories(new Set());
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tech Stack Monitoring</h1>
          <p className="text-gray-600 mt-1">Comprehensive observability for all platform components</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={expandAll}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 flex items-center gap-2"
          >
            <ChevronDown className="w-4 h-4" />
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 flex items-center gap-2"
          >
            <ChevronUp className="w-4 h-4" />
            Collapse All
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-2">Status Legend:</h3>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">🟢 Live</span>
            <span className="text-sm text-gray-600">Running on localhost</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">🟡 K8s Only</span>
            <span className="text-sm text-gray-600">Available in Kubernetes deployment</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">⚙️ Configured</span>
            <span className="text-sm text-gray-600">Configuration files available</span>
          </div>
        </div>
      </div>

      {/* Tech Stack Categories */}
      <div className="space-y-4">
        {techStack.map((category) => {
          const isExpanded = expandedCategories.has(category.category);
          const colors = colorClasses[category.color];

          return (
            <div key={category.category} className={`border ${colors.border} rounded-lg overflow-hidden`}>
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category.category)}
                className={`w-full ${colors.bg} ${colors.hover} p-4 flex items-center justify-between transition-colors`}
              >
                <div className="flex items-center gap-3">
                  <div className={colors.text}>
                    {category.icon}
                  </div>
                  <h2 className={`text-xl font-semibold ${colors.text}`}>
                    {category.category}
                  </h2>
                  <span className="text-sm text-gray-500">
                    ({category.services.length} services)
                  </span>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-5 h-5 text-gray-600" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-600" />
                )}
              </button>

              {/* Services Grid */}
              {isExpanded && (
                <div className="p-4 bg-white grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {category.services.map((service) => (
                    <div
                      key={service.name}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow"
                    >
                      <h3 className="font-semibold text-gray-900 mb-1">{service.name}</h3>
                      <p className="text-sm text-gray-600 mb-3">{service.description}</p>

                      {/* Links */}
                      <div className="space-y-2">
                        {service.links.map((link, idx) => (
                          <div key={idx}>
                            {link.url.startsWith('http') ? (
                              <a
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between text-sm text-indigo-600 hover:text-indigo-800 group"
                              >
                                <span className="flex items-center gap-2">
                                  <ExternalLink className="w-3 h-3" />
                                  {link.name}
                                  {link.port && (
                                    <code className="text-xs bg-gray-100 px-1 rounded">:{link.port}</code>
                                  )}
                                </span>
                                <span className={`px-2 py-0.5 ${statusBadge[link.status].bg} ${statusBadge[link.status].text} text-xs rounded`}>
                                  {statusBadge[link.status].label}
                                </span>
                              </a>
                            ) : (
                              <div className="flex items-center justify-between text-sm text-gray-600">
                                <span className="flex items-center gap-2">
                                  <Code className="w-3 h-3" />
                                  {link.name}
                                </span>
                                <span className={`px-2 py-0.5 ${statusBadge[link.status].bg} ${statusBadge[link.status].text} text-xs rounded`}>
                                  {statusBadge[link.status].label}
                                </span>
                              </div>
                            )}
                            {link.credentials && (
                              <p className="text-xs text-gray-500 ml-5 mt-1">
                                🔑 {link.credentials}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick Access */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Quick Access: Most Used Dashboards</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <a
            href="http://localhost:3000/d/finetuning-metrics"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white border border-gray-200 rounded p-3 hover:shadow-md transition-shadow flex items-center gap-2"
          >
            <BarChart3 className="w-5 h-5 text-orange-600" />
            <span className="text-sm font-medium">Grafana Metrics</span>
          </a>
          <a
            href="http://localhost:3000/explore"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white border border-gray-200 rounded p-3 hover:shadow-md transition-shadow flex items-center gap-2"
          >
            <Eye className="w-5 h-5 text-red-600" />
            <span className="text-sm font-medium">Logs & Traces</span>
          </a>
          <a
            href="http://localhost:9090/targets"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white border border-gray-200 rounded p-3 hover:shadow-md transition-shadow flex items-center gap-2"
          >
            <Activity className="w-5 h-5 text-red-600" />
            <span className="text-sm font-medium">Prometheus Targets</span>
          </a>
          <a
            href="http://localhost:4200"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white border border-gray-200 rounded p-3 hover:shadow-md transition-shadow flex items-center gap-2"
          >
            <Network className="w-5 h-5 text-orange-600" />
            <span className="text-sm font-medium">Prefect Flows</span>
          </a>
        </div>
      </div>
    </div>
  );
}
