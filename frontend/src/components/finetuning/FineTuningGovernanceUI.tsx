import React, { useState, useEffect } from 'react';
import {
  Database, Layers, Zap, Target, GitBranch, Rocket,
  Activity, Shield, ChevronRight, User, Settings,
  TrendingUp, AlertCircle, GitMerge
} from 'lucide-react';
import ModelCatalog from './ModelCatalog';
import DatasetInspector from './DatasetInspector';
import JobManager from './JobManager';  // ✅ FIX 1: Use JobManager (has hyperparameter config!)
import EvaluationHub from './EvaluationHub';
import AdapterVersions from './AdapterVersions';
import ModelMergeManager from './ModelMergeManager';
import DeploymentManager from './DeploymentManager';
import MonitoringDashboard from './MonitoringDashboard';
import GovernanceAudit from './GovernanceAudit';

/**
 * FineTuningGovernanceUI - State-of-the-art ML Workflow Cockpit
 *
 * A governed ML workflow interface for fine-tuning that serves:
 * - Product Managers / SMEs: Upload data, review outputs, approve
 * - ML Engineers: Control adapters, hyperparams, evaluations
 * - Platform Owners: Monitor cost, security, versioning
 *
 * Follows enterprise-grade practices with role-based access and comprehensive governance.
 */

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType<any>;
  roles: string[]; // Which roles can access this section
  badge?: number | string;
}

export default function FineTuningGovernanceUI() {
  const [activeSection, setActiveSection] = useState<string>('models');
  const [userRole, setUserRole] = useState<string>('ml_engineer'); // admin, ml_engineer, pm, readonly
  const [stats, setStats] = useState({
    runningJobs: 0,
    pendingApprovals: 0,
    activeModels: 0,
    datasetsReady: 0,
  });

  // ✅ FIX 3: Navigation structure - CONSOLIDATED (9 → 6 tabs for better UX)
  const navigation: NavigationItem[] = [
    {
      id: 'models',
      label: 'Models',
      icon: <Layers className="w-5 h-5" />,
      component: ModelCatalog,
      roles: ['admin', 'ml_engineer', 'pm', 'readonly'],
    },
    {
      id: 'datasets',
      label: 'Datasets',
      icon: <Database className="w-5 h-5" />,
      component: DatasetInspector,
      roles: ['admin', 'ml_engineer', 'pm'],
    },
    {
      id: 'training',
      label: 'Training',  // ✅ Renamed from "Fine-tuning Jobs"
      icon: <Zap className="w-5 h-5" />,
      component: JobManager,  // ✅ FIX 1: Use JobManager (has hyperparameter config!)
      roles: ['admin', 'ml_engineer'],
      badge: stats.runningJobs,
    },
    {
      id: 'evaluations',
      label: 'Evaluation',  // ✅ Shortened label
      icon: <Target className="w-5 h-5" />,
      component: EvaluationHub,  // ✅ Combines: Evaluations + Monitoring (will add monitoring section to EvaluationHub later)
      roles: ['admin', 'ml_engineer', 'pm'],
      badge: stats.pendingApprovals,
    },
    // ✅ CONSOLIDATED: Adapters + Merge + Deployment → Single "Model Management" tab
    // For now, using EvaluationHub which includes model lifecycle features
    // TODO Phase 1: Create ModelLifecycleManager component with sub-tabs:
    //   - Adapters & Versions
    //   - Merge Models
    //   - Deployment
    {
      id: 'adapters',
      label: 'Adapters & Versions',
      icon: <GitBranch className="w-5 h-5" />,
      component: AdapterVersions,
      roles: ['admin', 'ml_engineer'],
    },
    {
      id: 'governance',
      label: 'Governance',  // ✅ Shortened label
      icon: <Shield className="w-5 h-5" />,
      component: GovernanceAudit,
      roles: ['admin'],
    },
  ];

  // Filter navigation based on user role
  const accessibleNavigation = navigation.filter(item =>
    item.roles.includes(userRole)
  );

  // Fetch user role from auth context
  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        const response = await fetch('http://localhost:8000/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const userData = await response.json();
          // Map backend role to UI role
          const roleMapping: { [key: string]: string } = {
            'admin': 'admin',
            'user': 'ml_engineer',
            'readonly': 'readonly',
          };
          setUserRole(roleMapping[userData.role] || 'ml_engineer');
        }
      } catch (error) {
        console.error('Error fetching user role:', error);
      }
    };

    fetchUserRole();
  }, []);

  // Fetch stats for badges
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};

        const response = await fetch('http://localhost:8000/api/v1/finetuning/stats', {
          headers
        });

        if (response.ok) {
          const data = await response.json();
          setStats({
            runningJobs: data.running_jobs || 0,
            pendingApprovals: data.pending_approvals || 0,
            activeModels: data.active_models || 0,
            datasetsReady: data.datasets_ready || 0,
          });
        }
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Get active navigation item
  const activeNav = accessibleNavigation.find(item => item.id === activeSection);
  const ActiveComponent = activeNav?.component;

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Left Rail Navigation */}
      <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Settings className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">
              Fine-Tuning Hub
            </h1>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
            <User className="w-3 h-3" />
            <span className="capitalize">{userRole.replace('_', ' ')}</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto p-3">
          <div className="space-y-1">
            {accessibleNavigation.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`
                  w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg
                  transition-all duration-200 group
                  ${activeSection === item.id
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  <div className={`
                    ${activeSection === item.id
                      ? 'text-indigo-600 dark:text-indigo-400'
                      : 'text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400'
                    }
                  `}>
                    {item.icon}
                  </div>
                  <span className="text-sm font-medium">{item.label}</span>
                </div>

                <div className="flex items-center gap-2">
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-red-500 text-white rounded-full">
                      {item.badge}
                    </span>
                  )}
                  <ChevronRight className={`
                    w-4 h-4 transition-transform
                    ${activeSection === item.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'}
                  `} />
                </div>
              </button>
            ))}
          </div>
        </nav>

        {/* System Status Footer */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-700">
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
              <span>Running Jobs</span>
              <span className="font-semibold">{stats.runningJobs}</span>
            </div>
            <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
              <span>Active Models</span>
              <span className="font-semibold">{stats.activeModels}</span>
            </div>
            <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
              <span>Ready Datasets</span>
              <span className="font-semibold">{stats.datasetsReady}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {activeNav?.label}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {getRoleBasedDescription(activeSection, userRole)}
              </p>
            </div>

            {/* Quick Stats Pills */}
            <div className="flex items-center gap-3">
              {stats.runningJobs > 0 && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 rounded-full">
                  <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    {stats.runningJobs} Training
                  </span>
                </div>
              )}
              {stats.pendingApprovals > 0 && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-900/30 rounded-full">
                  <AlertCircle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                  <span className="text-sm font-medium text-orange-700 dark:text-orange-300">
                    {stats.pendingApprovals} Pending
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Component Content */}
        <div className="flex-1 overflow-auto">
          {ActiveComponent ? (
            <ActiveComponent userRole={userRole} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 dark:text-gray-400">
                Component not yet implemented
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper function to provide role-based descriptions
function getRoleBasedDescription(section: string, role: string): string {
  const descriptions: { [key: string]: { [key: string]: string } } = {
    models: {
      admin: 'Manage base models, licenses, and compatibility',
      ml_engineer: 'Select base models for fine-tuning with cost estimation',
      pm: 'Browse available models and capabilities',
      readonly: 'View model catalog and specifications',
    },
    datasets: {
      admin: 'Manage dataset uploads, validation, and quality metrics',
      ml_engineer: 'Upload and inspect datasets with quality analysis',
      pm: 'Upload domain-specific datasets for fine-tuning',
    },
    jobs: {
      admin: 'Monitor and manage all fine-tuning jobs across the platform',
      ml_engineer: 'Create, configure, and monitor fine-tuning experiments',
    },
    evaluations: {
      admin: 'Review and approve model evaluations and deployments',
      ml_engineer: 'Run evaluations and compare model performance',
      pm: 'Review model outputs and provide domain feedback',
    },
    adapters: {
      admin: 'Manage adapter versions, lineage, and storage',
      ml_engineer: 'Track adapter experiments with Git-like versioning',
    },
    merge: {
      admin: 'Merge LoRA adapters with base models for deployment',
      ml_engineer: 'Request merge operations and monitor merge progress',
    },
    deployment: {
      admin: 'Manage deployments, rollbacks, and canary releases',
      ml_engineer: 'Deploy models to Ollama, vLLM, or cloud endpoints',
    },
    monitoring: {
      admin: 'Monitor system health, costs, and usage across tenants',
      ml_engineer: 'Track model performance, drift, and resource usage',
      pm: 'Monitor deployed model quality and user feedback',
    },
    governance: {
      admin: 'Audit data lineage, approvals, costs, and compliance',
    },
  };

  return descriptions[section]?.[role] || 'Manage fine-tuning workflows';
}
