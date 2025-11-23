import React, { useState, useEffect } from 'react';
import { Settings, ChevronDown, ChevronUp, Info } from 'lucide-react';

interface SettingsPanelProps {
  onSettingsChange: (settings: MetricsSettings) => void;
}

export interface MetricsSettings {
  enableEvaluation: boolean;
  showPerformanceMetrics: boolean;
  showToolsUsed: boolean;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onSettingsChange }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [settings, setSettings] = useState<MetricsSettings>({
    enableEvaluation: false,
    showPerformanceMetrics: true,
    showToolsUsed: true,
  });

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('metricsSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
        onSettingsChange(parsed);
      } catch (e) {
        console.error('Failed to load settings:', e);
      }
    }
  }, []);

  // Save settings to localStorage and notify parent
  const updateSettings = (newSettings: MetricsSettings) => {
    setSettings(newSettings);
    localStorage.setItem('metricsSettings', JSON.stringify(newSettings));
    onSettingsChange(newSettings);
  };

  const toggleEvaluation = () => {
    updateSettings({
      ...settings,
      enableEvaluation: !settings.enableEvaluation,
    });
  };

  const togglePerformanceMetrics = () => {
    updateSettings({
      ...settings,
      showPerformanceMetrics: !settings.showPerformanceMetrics,
    });
  };

  const toggleToolsUsed = () => {
    updateSettings({
      ...settings,
      showToolsUsed: !settings.showToolsUsed,
    });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm mb-4">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-t-lg"
      >
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-600" />
          <span className="font-medium text-gray-700">Metrics & Evaluation Settings</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      {/* Settings Panel */}
      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-200 space-y-4">
          {/* Evaluation Toggle */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="enableEvaluation"
                  className="text-sm font-medium text-gray-700 cursor-pointer"
                >
                  Enable RAG Evaluation Metrics
                </label>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-64 p-2 mt-1 text-xs text-white bg-gray-800 rounded shadow-lg -right-2">
                    Enables quality metrics: faithfulness, answer relevancy, context precision.
                    <br />
                    <span className="text-yellow-300">Warning: Adds 2-5s latency and extra cost (~$0.01-0.02 per query)</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Evaluate answer quality using RAGAS metrics (adds latency)
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input
                id="enableEvaluation"
                type="checkbox"
                checked={settings.enableEvaluation}
                onChange={toggleEvaluation}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Performance Metrics Toggle */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="showPerformanceMetrics"
                  className="text-sm font-medium text-gray-700 cursor-pointer"
                >
                  Show Performance Metrics
                </label>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-64 p-2 mt-1 text-xs text-white bg-gray-800 rounded shadow-lg -right-2">
                    Shows response time, token usage, retrieval count, and tool execution time below each response.
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Display latency, tokens, and tool execution details
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input
                id="showPerformanceMetrics"
                type="checkbox"
                checked={settings.showPerformanceMetrics}
                onChange={togglePerformanceMetrics}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Tools Used Toggle */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="showToolsUsed"
                  className="text-sm font-medium text-gray-700 cursor-pointer"
                >
                  Show Tools Used
                </label>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-64 p-2 mt-1 text-xs text-white bg-gray-800 rounded shadow-lg -right-2">
                    Shows which tools were invoked for each response: document_rag, web_scraper, docling, navigation_agent, smart_extraction, etc.
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Display tool invocations (RAG, scraper, navigation, extraction)
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input
                id="showToolsUsed"
                type="checkbox"
                checked={settings.showToolsUsed}
                onChange={toggleToolsUsed}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Status Indicators */}
          <div className="pt-3 border-t border-gray-100">
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${settings.enableEvaluation ? 'bg-yellow-500' : 'bg-gray-300'}`} />
                <span className="text-gray-600">
                  Evaluation: {settings.enableEvaluation ? (
                    <span className="text-yellow-600 font-medium">ON (slower)</span>
                  ) : (
                    <span className="text-gray-500">OFF</span>
                  )}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${settings.showPerformanceMetrics ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-gray-600">
                  Performance: {settings.showPerformanceMetrics ? (
                    <span className="text-green-600 font-medium">ON</span>
                  ) : (
                    <span className="text-gray-500">OFF</span>
                  )}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${settings.showToolsUsed ? 'bg-blue-500' : 'bg-gray-300'}`} />
                <span className="text-gray-600">
                  Tools: {settings.showToolsUsed ? (
                    <span className="text-blue-600 font-medium">ON</span>
                  ) : (
                    <span className="text-gray-500">OFF</span>
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPanel;
