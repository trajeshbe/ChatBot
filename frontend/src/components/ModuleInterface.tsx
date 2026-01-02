import React, { useState, useEffect } from 'react';
import { Send, Loader2, Info, CheckCircle2, XCircle, FileText, Sparkles } from 'lucide-react';
import axios from 'axios';

interface ModuleInterfaceProps {
  moduleId: string;
  moduleName: string;
  moduleType: 'tier2' | 'tier3';
  sessionId: string;
}

interface ModuleStatus {
  success: boolean;
  status: string;
  description: string;
  tier_2_modules_used?: string[];
  capabilities?: string[];
}

interface ModuleResponse {
  success: boolean;
  session_id: string;
  result: any;
  insights?: string;
  recommendations?: string[];
  analysis?: any;
  extracted_data?: any;
}

const ModuleInterface: React.FC<ModuleInterfaceProps> = ({
  moduleId,
  moduleName,
  moduleType,
  sessionId
}) => {
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [response, setResponse] = useState<ModuleResponse | null>(null);
  const [status, setStatus] = useState<ModuleStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // Construct endpoint based on module type
  const getEndpointPrefix = () => {
    if (moduleType === 'tier3') {
      return `${API_BASE_URL}/api/v1/customer/${moduleId}`;
    } else {
      return `${API_BASE_URL}/api/v1/domain/${moduleId}`;
    }
  };

  // Fetch module status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoadingStatus(true);
        const endpoint = `${getEndpointPrefix()}/status`;
        const res = await axios.get(endpoint);
        setStatus(res.data);
      } catch (err: any) {
        console.error('Failed to fetch module status:', err);
        setError(err.response?.data?.detail || 'Failed to load module status');
      } finally {
        setLoadingStatus(false);
      }
    };

    fetchStatus();
  }, [moduleId, moduleType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const endpoint = `${getEndpointPrefix()}/process`;
      const payload = {
        session_id: sessionId,
        query: query.trim(),
        context: context.trim() ? JSON.parse(context) : {}
      };

      const res = await axios.post(endpoint, payload);
      setResponse(res.data);
    } catch (err: any) {
      console.error('Module processing error:', err);
      setError(err.response?.data?.detail || 'Failed to process request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-slate-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-blue-600" />
              {moduleName}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {moduleType === 'tier3' ? 'Customer Solution POC' : 'Domain Vertical Module'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {loadingStatus ? (
              <span className="text-sm text-gray-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading...
              </span>
            ) : status?.success ? (
              <span className="text-sm text-green-600 dark:text-green-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                {status.status}
              </span>
            ) : (
              <span className="text-sm text-red-600 dark:text-red-400 flex items-center gap-2">
                <XCircle className="w-4 h-4" />
                Unavailable
              </span>
            )}
          </div>
        </div>

        {/* Module Status Info */}
        {status && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-slate-700">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                  {status.description}
                </p>
                {status.tier_2_modules_used && status.tier_2_modules_used.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold mb-1">
                      Uses Tier 2 Modules:
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {status.tier_2_modules_used.map((mod, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-blue-100 dark:bg-slate-700 text-blue-800 dark:text-blue-300 text-xs rounded-full"
                        >
                          {mod}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {status.capabilities && status.capabilities.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold mb-1">
                      Capabilities:
                    </p>
                    <ul className="text-xs text-gray-600 dark:text-gray-400 list-disc list-inside">
                      {status.capabilities.map((cap, idx) => (
                        <li key={idx}>{cap}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Input Form */}
        <form onSubmit={handleSubmit} className="mb-6">
          <div className="space-y-4">
            {/* Query Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Query / Request
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your query or request for this module..."
                className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white resize-none"
                rows={4}
                disabled={loading}
              />
            </div>

            {/* Optional Context Input */}
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
                Advanced: Add Context (JSON)
              </summary>
              <div className="mt-2">
                <textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder='{"key": "value", "department": "Engineering"}'
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white font-mono text-sm resize-none"
                  rows={3}
                  disabled={loading}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Optional JSON context object for the request
                </p>
              </div>
            </details>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Submit Request
                </>
              )}
            </button>
          </div>
        </form>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-2">
              <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-300">Error</p>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Response Display */}
        {response && response.success && (
          <div className="space-y-4">
            <div className="border-t border-gray-200 dark:border-slate-700 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Response
              </h3>

              {/* Insights */}
              {response.insights && (
                <div className="mb-4 p-4 bg-blue-50 dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-slate-700">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Insights
                  </h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{response.insights}</p>
                </div>
              )}

              {/* Recommendations */}
              {response.recommendations && response.recommendations.length > 0 && (
                <div className="mb-4 p-4 bg-green-50 dark:bg-slate-800 rounded-lg border border-green-200 dark:border-slate-700">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Recommendations
                  </h4>
                  <ul className="list-disc list-inside space-y-1">
                    {response.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Analysis (if present) */}
              {response.analysis && (
                <div className="mb-4 p-4 bg-purple-50 dark:bg-slate-800 rounded-lg border border-purple-200 dark:border-slate-700">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Analysis
                  </h4>
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
                    {JSON.stringify(response.analysis, null, 2)}
                  </pre>
                </div>
              )}

              {/* Extracted Data (if present) */}
              {response.extracted_data && (
                <div className="mb-4 p-4 bg-yellow-50 dark:bg-slate-800 rounded-lg border border-yellow-200 dark:border-slate-700">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Extracted Data
                  </h4>
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
                    {JSON.stringify(response.extracted_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Raw Result */}
              <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Full Result
                </h4>
                <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto max-h-96 overflow-y-auto">
                  {JSON.stringify(response.result, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* No response yet message */}
        {!response && !error && !loading && (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              Enter a query above to interact with this module
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModuleInterface;
