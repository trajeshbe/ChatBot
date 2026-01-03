import React, { useState, useEffect } from 'react';
import {
  Send,
  Loader2,
  Info,
  CheckCircle2,
  XCircle,
  FileText,
  Sparkles,
  Upload,
  Download,
  History,
  Trash2,
  Eye,
  ChevronDown,
  ChevronUp,
  AlertCircle
} from 'lucide-react';
import axios from 'axios';

interface EnhancedModulePanelProps {
  moduleId: string;
  moduleName: string;
  moduleType: 'tier2' | 'tier3';
  moduleCategory?: string;
  moduleDescription?: string;
  sessionId: string;
  supportsFileUpload?: boolean;
  customFields?: CustomField[];
}

interface CustomField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox';
  required?: boolean;
  options?: string[];
  placeholder?: string;
  min?: number;
  max?: number;
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
  processing_time?: number;
  tier_1_services_used?: string[];
}

interface HistoryItem {
  id: string;
  timestamp: string;
  query: string;
  result: ModuleResponse;
}

const EnhancedModulePanel: React.FC<EnhancedModulePanelProps> = ({
  moduleId,
  moduleName,
  moduleType,
  moduleCategory,
  moduleDescription,
  sessionId,
  supportsFileUpload = true,
  customFields = []
}) => {
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [response, setResponse] = useState<ModuleResponse | null>(null);
  const [status, setStatus] = useState<ModuleStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showRawResponse, setShowRawResponse] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(null);
  const [customFieldValues, setCustomFieldValues] = useState<Record<string, any>>({});

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // Construct endpoint based on module type
  const getEndpointPrefix = () => {
    if (moduleType === 'tier3') {
      return `${API_BASE_URL}/api/v1/customer/${moduleId}`;
    } else {
      return `${API_BASE_URL}/api/v1/domain/${moduleId}`;
    }
  };

  // Load history from sessionStorage
  useEffect(() => {
    const storageKey = `module_history_${moduleId}_${sessionId}`;
    const storedHistory = sessionStorage.getItem(storageKey);
    if (storedHistory) {
      try {
        setHistory(JSON.parse(storedHistory));
      } catch (e) {
        console.error('Failed to parse history:', e);
      }
    }
  }, [moduleId, sessionId]);

  // Save history to sessionStorage
  const saveToHistory = (query: string, result: ModuleResponse) => {
    const newItem: HistoryItem = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      query,
      result
    };
    const updatedHistory = [newItem, ...history].slice(0, 10); // Keep last 10
    setHistory(updatedHistory);

    const storageKey = `module_history_${moduleId}_${sessionId}`;
    sessionStorage.setItem(storageKey, JSON.stringify(updatedHistory));
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

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const uploadResponse = await axios.post(
        `${API_BASE_URL}/api/v1/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      setUploadedDocumentId(uploadResponse.data.document_id);
      console.log('✅ File uploaded:', uploadResponse.data.document_id);
    } catch (err: any) {
      console.error('File upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload file');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const endpoint = `${getEndpointPrefix()}/process`;
      const payload: any = {
        session_id: sessionId,
        query: query.trim(),
        context: context.trim() ? JSON.parse(context) : {},
        ...customFieldValues
      };

      if (uploadedDocumentId) {
        payload.document_id = uploadedDocumentId;
      }

      const res = await axios.post(endpoint, payload);
      setResponse(res.data);
      saveToHistory(query, res.data);
    } catch (err: any) {
      console.error('Module processing error:', err);
      setError(err.response?.data?.detail || 'Failed to process request');
    } finally {
      setLoading(false);
    }
  };

  const loadHistoryItem = (item: HistoryItem) => {
    setQuery(item.query);
    setResponse(item.result);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setHistory([]);
    const storageKey = `module_history_${moduleId}_${sessionId}`;
    sessionStorage.removeItem(storageKey);
  };

  const exportResults = () => {
    if (!response) return;

    const dataStr = JSON.stringify(response, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${moduleId}_results_${Date.now()}.json`;
    link.click();
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
            <div className="flex items-center gap-2 mt-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {moduleType === 'tier3' ? 'Customer Solution POC' : 'Domain Vertical Module'}
              </p>
              {moduleCategory && (
                <>
                  <span className="text-gray-400">•</span>
                  <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded-full">
                    {moduleCategory}
                  </span>
                </>
              )}
            </div>
            {moduleDescription && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{moduleDescription}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            {/* History Toggle */}
            {history.length > 0 && (
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <History className="w-4 h-4" />
                History ({history.length})
              </button>
            )}

            {/* Export Button */}
            {response && (
              <button
                onClick={exportResults}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            )}

            {/* Status Indicator */}
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

      {/* History Sidebar */}
      {showHistory && (
        <div className="border-b border-gray-200 dark:border-slate-700 p-4 bg-gray-50 dark:bg-slate-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Recent Queries</h3>
            <button
              onClick={clearHistory}
              className="text-xs text-red-600 hover:text-red-700 dark:text-red-400 flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" />
              Clear
            </button>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {history.map((item) => (
              <div
                key={item.id}
                onClick={() => loadHistoryItem(item)}
                className="p-2 bg-white dark:bg-slate-700 rounded border border-gray-200 dark:border-slate-600 cursor-pointer hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
              >
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {new Date(item.timestamp).toLocaleString()}
                </p>
                <p className="text-sm text-gray-900 dark:text-white truncate">{item.query}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Input Form */}
        <form onSubmit={handleSubmit} className="mb-6">
          <div className="space-y-4">
            {/* File Upload (if supported) */}
            {supportsFileUpload && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Upload Document (Optional)
                </label>
                <div className="flex items-center gap-3">
                  <label className="flex-1 flex items-center justify-center px-4 py-3 border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer">
                    <Upload className="w-5 h-5 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {uploadedFile ? uploadedFile.name : 'Choose file...'}
                    </span>
                    <input
                      type="file"
                      onChange={handleFileUpload}
                      className="hidden"
                      disabled={loading}
                    />
                  </label>
                  {uploadedDocumentId && (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  )}
                </div>
              </div>
            )}

            {/* Custom Fields */}
            {customFields.map((field) => (
              <div key={field.name}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                {field.type === 'select' ? (
                  <select
                    value={customFieldValues[field.name] || ''}
                    onChange={(e) =>
                      setCustomFieldValues({ ...customFieldValues, [field.name]: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white"
                    required={field.required}
                  >
                    <option value="">Select...</option>
                    {field.options?.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : field.type === 'textarea' ? (
                  <textarea
                    value={customFieldValues[field.name] || ''}
                    onChange={(e) =>
                      setCustomFieldValues({ ...customFieldValues, [field.name]: e.target.value })
                    }
                    placeholder={field.placeholder}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white resize-none"
                    rows={3}
                    required={field.required}
                  />
                ) : field.type === 'checkbox' ? (
                  <input
                    type="checkbox"
                    checked={customFieldValues[field.name] || false}
                    onChange={(e) =>
                      setCustomFieldValues({ ...customFieldValues, [field.name]: e.target.checked })
                    }
                    className="w-4 h-4"
                  />
                ) : (
                  <input
                    type={field.type}
                    value={customFieldValues[field.name] || ''}
                    onChange={(e) =>
                      setCustomFieldValues({
                        ...customFieldValues,
                        [field.name]: field.type === 'number' ? parseFloat(e.target.value) : e.target.value
                      })
                    }
                    placeholder={field.placeholder}
                    min={field.min}
                    max={field.max}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white"
                    required={field.required}
                  />
                )}
              </div>
            ))}

            {/* Query Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Query / Request <span className="text-red-500">*</span>
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your query or request for this module..."
                className="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-slate-800 dark:text-white resize-none"
                rows={4}
                disabled={loading}
                required
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
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  Results
                </h3>
                {response.processing_time && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Processed in {response.processing_time.toFixed(2)}s
                  </span>
                )}
              </div>

              {/* Insights */}
              {response.insights && (
                <div className="mb-4 p-4 bg-blue-50 dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-slate-700">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    Insights
                  </h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{response.insights}</p>
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
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto whitespace-pre-wrap">
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
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(response.extracted_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Services Used */}
              {response.tier_1_services_used && response.tier_1_services_used.length > 0 && (
                <div className="mb-4 p-3 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold mb-2">
                    Tier 1 Services Used:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {response.tier_1_services_used.map((svc, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 text-xs rounded-full"
                      >
                        {svc}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw Result Toggle */}
              <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
                <button
                  onClick={() => setShowRawResponse(!showRawResponse)}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white mb-2"
                >
                  {showRawResponse ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  Full Result (JSON)
                </button>
                {showRawResponse && (
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto max-h-96 overflow-y-auto whitespace-pre-wrap">
                    {JSON.stringify(response.result, null, 2)}
                  </pre>
                )}
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

export default EnhancedModulePanel;
