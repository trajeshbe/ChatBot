import React from 'react';
import { AlertCircle, Construction } from 'lucide-react';

interface EnhancedModulePanelProps {
  moduleId: string;
  moduleName: string;
  moduleType: 'tier2' | 'tier3';
  moduleCategory?: string;
  moduleDescription?: string;
  sessionId: string;
  supportsFileUpload?: boolean;
  customFields?: any[];
}

/**
 * EnhancedModulePanel - Fallback component for modules without specialized UI
 *
 * This component is used when a module doesn't have a dedicated specialized component yet.
 * It shows a clean message instead of a generic interface.
 */
const EnhancedModulePanel: React.FC<EnhancedModulePanelProps> = ({
  moduleId,
  moduleName,
  moduleDescription
}) => {
  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-2xl w-full text-center">
        {/* Icon */}
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-blue-100 mb-6">
          <Construction className="w-10 h-10 text-blue-600" />
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-slate-900 mb-3">
          {moduleName}
        </h1>

        {/* Description */}
        {moduleDescription && (
          <p className="text-lg text-slate-600 mb-6">
            {moduleDescription}
          </p>
        )}

        {/* Info Message */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div className="text-left">
              <h3 className="font-semibold text-blue-900 mb-2">
                Specialized UI Coming Soon
              </h3>
              <p className="text-sm text-blue-800">
                This module is being developed with a custom interface tailored to its specific functionality.
                The specialized UI will provide an optimized experience for this use case.
              </p>
            </div>
          </div>
        </div>

        {/* Module Info */}
        <div className="text-sm text-slate-500 space-y-1">
          <p>Module ID: <span className="font-mono text-slate-700">{moduleId}</span></p>
          <p>All module configurations can be managed via the configuration panel once the UI is ready.</p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedModulePanel;
