/**
 * Tools Dashboard Page
 *
 * Displays tool usage statistics and analytics
 */

import React from 'react';
import ToolUsageDashboard from '../components/ToolUsageDashboard';

export default function ToolsDashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          Tool Usage Dashboard
        </h1>
        <ToolUsageDashboard />
      </div>
    </div>
  );
}
