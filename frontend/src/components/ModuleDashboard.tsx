import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Upload,
  Globe,
  History,
  Calculator,
  BarChart3,
  Wrench,
  Sliders,
  Shield,
  LucideIcon,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface Module {
  id: string;
  name: string;
  code: string;
  description: string;
  icon: string;
  route: string | null;
  display_order: number;
  is_active: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Map icon names to Lucide icons
const iconMap: Record<string, LucideIcon> = {
  MessageSquare: MessageSquare,
  History: History,
  Upload: Upload,
  Globe: Globe,
  Calculator: Calculator,
  BarChart3: BarChart3,
  Wrench: Wrench,
  Sliders: Sliders,
  Shield: Shield,
};

// Map module codes to internal tab names
const moduleToTab: Record<string, string> = {
  rag_chat: 'chat',
  file_upload: 'upload',
  web_scraping: 'scrape',
  data_extraction: 'scrape', // Merged with web scraping
  project_estimator: 'estimator',
  evaluation: 'evaluation',
  tools_dashboard: 'tools',
  weights_config: 'weights',
  admin_panel: 'admin',
  audit_logs: 'admin',
};

interface ModuleDashboardProps {
  onModuleClick: (tabName: string) => void;
}

export default function ModuleDashboard({ onModuleClick }: ModuleDashboardProps) {
  const { user, token } = useAuth();
  const [modules, setModules] = useState<Module[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAccessibleModules();
  }, [user, token]);

  const fetchAccessibleModules = async () => {
    if (!user || !token) {
      setError('Not authenticated');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/api/v1/modules/user/${user.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch modules: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Fetched accessible modules:', data);

      // Filter out admin/audit_logs from main dashboard (they're in sidebar)
      const filteredModules = data.filter(
        (m: Module) => m.code !== 'admin_panel' && m.code !== 'audit_logs'
      );

      // Sort by display_order
      filteredModules.sort((a: Module, b: Module) => a.display_order - b.display_order);

      setModules(filteredModules);
    } catch (err) {
      console.error('Error fetching modules:', err);
      setError(err instanceof Error ? err.message : 'Failed to load modules');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModuleClick = (module: Module) => {
    const tabName = moduleToTab[module.code] || module.code;
    onModuleClick(tabName);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading your modules...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={fetchAccessibleModules}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (modules.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <Shield className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400 mb-2">No modules available</p>
          <p className="text-sm text-slate-500 dark:text-slate-500">
            Contact your administrator to request access to modules
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="p-8 border-b border-slate-200 dark:border-slate-700">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Welcome back, {user?.full_name || user?.username}!
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          Select a module to get started. You have access to {modules.length} module{modules.length !== 1 ? 's' : ''}.
        </p>
      </div>

      {/* Module Grid */}
      <div className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {modules.map((module) => {
            const IconComponent = iconMap[module.icon] || MessageSquare;

            return (
              <button
                key={module.id}
                onClick={() => handleModuleClick(module)}
                className="group relative flex flex-col items-start p-6 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:shadow-lg hover:border-blue-500 dark:hover:border-blue-500 transition-all duration-200 hover:-translate-y-1"
              >
                {/* Icon */}
                <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg mb-4 group-hover:scale-110 transition-transform">
                  <IconComponent className="w-6 h-6 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  {module.name}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                  {module.description}
                </p>

                {/* Hover Indicator */}
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="flex items-center justify-center w-6 h-6 bg-blue-500 rounded-full">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-8 mt-8">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                Role-Based Access
              </h4>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                You're logged in as <strong>{user?.role}</strong>. The modules shown above are based on your role permissions.
                {user?.role === 'admin' && ' As an admin, you have access to all modules.'}
                {user?.role !== 'admin' && ' Contact your administrator to request access to additional modules.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
