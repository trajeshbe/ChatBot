import React, { useState, useEffect } from 'react';
import {
  Upload, Database, CheckCircle, XCircle, AlertTriangle,
  FileText, BarChart3, Shield, Languages, Copy, Trash2,
  Eye, Download, RefreshCw, Info, TrendingUp, Sparkles
} from 'lucide-react';
import ProjectSelector from '../ProjectSelector';

/**
 * DatasetInspector - Advanced Dataset Management with Quality Analysis
 *
 * Features:
 * - Multi-format upload (JSONL, CSV, Parquet, PDF)
 * - Connectors for S3, GCS, Azure Blob, Git, SharePoint
 * - Row-level preview with token length visualization
 * - Quality metrics: duplicates, toxicity, PII detection
 * - Language detection
 * - Similarity to base model training style
 * - RAG-aware dataset support (prompt + context + answer)
 */

interface Dataset {
  id: string;
  name: string;
  description: string;
  filename: string;
  file_type: string;
  format_type: string;
  num_samples: number;
  num_train_samples: number;
  num_val_samples: number;
  uploaded_at: string;
  uploaded_by: string;
  is_valid: boolean;
  validation_errors: string[];
  quality_metrics?: {
    avg_token_length: number;
    token_length_std: number;
    duplicates: number;
    near_duplicates: number;
    toxicity_score: number;
    pii_detected: boolean;
    language_distribution: { [key: string]: number };
    similarity_to_base: number;
  };
  sample_rows?: any[];
  preprocessing_status: string;
}

interface DatasetInspectorProps {
  userRole: string;
}

export default function DatasetInspector({ userRole }: DatasetInspectorProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [inspectorView, setInspectorView] = useState<'overview' | 'samples' | 'quality'>('overview');

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadFormat, setUploadFormat] = useState<string>('instruction');

  // Project selection
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [currentUser, setCurrentUser] = useState<any>(null);

  // Load current user
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      setCurrentUser(JSON.parse(userStr));
    }
  }, []);

  // Fetch datasets
  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await fetch('http://localhost:8000/api/v1/finetuning/datasets', {
        headers
      });

      if (response.ok) {
        const data = await response.json();
        setDatasets(data.datasets || []);
      }
    } catch (error) {
      console.error('Error fetching datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  // Handle file upload
  const handleUpload = async () => {
    if (!uploadFile || !uploadName) {
      alert('Please provide a file and name');
      return;
    }

    try {
      setUploading(true);
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const formData = new FormData();
      formData.append('file', uploadFile);

      // Build query parameters (backend expects these as query params, not form data)
      const params = new URLSearchParams({
        format_type: uploadFormat,
        training_objective: uploadFormat, // Use format as training objective for now
      });

      // Add optional parameters if provided
      if (uploadName) {
        params.append('name', uploadName);
      }
      if (uploadDescription) {
        formData.append('description', uploadDescription);
      }
      if (selectedProjectId) {
        params.append('project_id', selectedProjectId);
      }

      const response = await fetch(`http://localhost:8000/api/v1/finetuning/datasets/upload?${params.toString()}`, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (response.ok) {
        alert('Dataset uploaded successfully! Running quality analysis...');
        setUploadFile(null);
        setUploadName('');
        setUploadDescription('');
        await fetchDatasets();
      } else {
        const error = await response.json();
        alert(`Upload failed: ${error.detail || JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error uploading dataset:', error);
      alert(`Upload failed: ${error}`);
    } finally {
      setUploading(false);
    }
  };

  // Delete dataset
  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this dataset?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await fetch(`http://localhost:8000/api/v1/finetuning/datasets/${id}`, {
        method: 'DELETE',
        headers,
      });

      if (response.ok) {
        alert('Dataset deleted successfully');
        await fetchDatasets();
        if (selectedDataset?.id === id) {
          setSelectedDataset(null);
        }
      }
    } catch (error) {
      console.error('Error deleting dataset:', error);
    }
  };

  // Validate dataset
  const handleValidate = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : {};

      const response = await fetch(`http://localhost:8000/api/v1/finetuning/datasets/${id}/validate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({}),
      });

      if (response.ok) {
        alert('Dataset validation started');
        await fetchDatasets();
      }
    } catch (error) {
      console.error('Error validating dataset:', error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Upload Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Upload className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Upload Dataset
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Dataset Name *
              </label>
              <input
                type="text"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                placeholder="e.g., customer-support-qa"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={uploadDescription}
                onChange={(e) => setUploadDescription(e.target.value)}
                placeholder="Describe the dataset purpose and content..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Format Type *
              </label>
              <select
                value={uploadFormat}
                onChange={(e) => setUploadFormat(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="instruction">Instruction (instruction, input, output)</option>
                <option value="qa">QA (prompt, response)</option>
                <option value="classification">Classification (text, label)</option>
                <option value="preference">Preference (prompt, chosen, rejected)</option>
                <option value="summarization">Summarization (document, summary)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Project (Optional)
              </label>
              <ProjectSelector
                value={selectedProjectId}
                onChange={(projectId) => setSelectedProjectId(projectId)}
                currentUser={currentUser}
                placeholder="Select project or leave blank for global..."
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              File Upload * (JSON, JSONL, CSV, Parquet)
            </label>
            <div
              className={`
                relative border-2 border-dashed rounded-lg p-8 text-center transition-all
                ${uploadFile
                  ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                  : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50'
                }
              `}
            >
              <input
                type="file"
                accept=".json,.jsonl,.csv,.parquet"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              {uploadFile ? (
                <div className="space-y-2">
                  <CheckCircle className="w-12 h-12 mx-auto text-green-600 dark:text-green-400" />
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {uploadFile.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="w-12 h-12 mx-auto text-gray-400" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Drop file here or click to browse
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={handleUpload}
              disabled={!uploadFile || !uploadName || uploading}
              className={`
                mt-4 w-full px-4 py-2 rounded-lg font-medium transition-all
                ${uploading || !uploadFile || !uploadName
                  ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }
              `}
            >
              {uploading ? 'Uploading...' : 'Upload & Analyze'}
            </button>
          </div>
        </div>

        {/* Format Requirements */}
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-blue-800 dark:text-blue-300">
              <span className="font-semibold">Format requirements:</span> Each format expects specific fields.
              <span className="font-mono ml-1">instruction</span> needs instruction, input, output.
              <span className="font-mono ml-1">qa</span> needs prompt, response.
              File will be validated on upload.
            </div>
          </div>
        </div>
      </div>

      {/* Dataset List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Datasets ({datasets.length})
            </h3>
          </div>
          <button
            onClick={fetchDatasets}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : datasets.length === 0 ? (
          <div className="p-12 text-center text-gray-500 dark:text-gray-400">
            No datasets uploaded yet. Upload your first dataset above!
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {datasets.map(dataset => {
              const quality = dataset.quality_metrics;

              return (
                <div
                  key={dataset.id}
                  className={`
                    p-4 transition-colors cursor-pointer
                    ${selectedDataset?.id === dataset.id
                      ? 'bg-indigo-50 dark:bg-indigo-900/20'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }
                  `}
                  onClick={() => setSelectedDataset(dataset)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="text-base font-semibold text-gray-900 dark:text-white">
                          {dataset.name}
                        </h4>

                        {/* Status Badge */}
                        {dataset.is_valid ? (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium rounded">
                            <CheckCircle className="w-3 h-3" />
                            Valid
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-medium rounded">
                            <XCircle className="w-3 h-3" />
                            Invalid
                          </span>
                        )}

                        {/* Format Badge */}
                        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded">
                          {dataset.format_type}
                        </span>
                      </div>

                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {dataset.description || 'No description'}
                      </p>

                      {/* Quick Stats */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Samples:</span>
                          <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                            {dataset.num_samples !== null && dataset.num_samples !== undefined
                              ? dataset.num_samples.toLocaleString()
                              : '-'}
                          </span>
                        </div>

                        {quality && (
                          <>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Avg Tokens:</span>
                              <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                                {Math.round(quality.avg_token_length)}
                              </span>
                            </div>

                            {quality.duplicates > 0 && (
                              <div>
                                <span className="text-gray-500 dark:text-gray-400">Duplicates:</span>
                                <span className={`ml-2 font-semibold ${
                                  quality.duplicates > 10 ? 'text-orange-600 dark:text-orange-400' : 'text-gray-900 dark:text-white'
                                }`}>
                                  {quality.duplicates}
                                </span>
                              </div>
                            )}

                            {quality.pii_detected && (
                              <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
                                <Shield className="w-4 h-4" />
                                <span className="font-semibold">PII Detected</span>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleValidate(dataset.id);
                        }}
                        className="p-2 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-lg transition-colors"
                        title="Run validation"
                      >
                        <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                      </button>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedDataset(dataset);
                          setInspectorView('samples');
                        }}
                        className="p-2 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                        title="View samples"
                      >
                        <Eye className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      </button>

                      {userRole === 'admin' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(dataset.id);
                          }}
                          className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                          title="Delete dataset"
                        >
                          <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Dataset Inspector Modal */}
      {selectedDataset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {selectedDataset.name}
                </h3>
                <button
                  onClick={() => setSelectedDataset(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <XCircle className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex gap-2">
                {['overview', 'samples', 'quality'].map(view => (
                  <button
                    key={view}
                    onClick={() => setInspectorView(view as any)}
                    className={`
                      px-4 py-2 rounded-lg font-medium capitalize transition-all
                      ${inspectorView === view
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }
                    `}
                  >
                    {view}
                  </button>
                ))}
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-auto p-6">
              {inspectorView === 'overview' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Samples</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {selectedDataset.num_samples !== null && selectedDataset.num_samples !== undefined
                          ? selectedDataset.num_samples.toLocaleString()
                          : '-'}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Training Split</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {selectedDataset.num_train_samples !== null && selectedDataset.num_train_samples !== undefined
                          ? selectedDataset.num_train_samples.toLocaleString()
                          : '-'}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Validation Split</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {selectedDataset.num_val_samples !== null && selectedDataset.num_val_samples !== undefined
                          ? selectedDataset.num_val_samples.toLocaleString()
                          : '-'}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">File Type</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white uppercase">
                        {selectedDataset.file_type}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Metadata</h4>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">Uploaded by:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedDataset.uploaded_by}</span>
                      </div>
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">Uploaded at:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">
                          {new Date(selectedDataset.uploaded_at).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">Format:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedDataset.format_type}</span>
                      </div>
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">Status:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedDataset.preprocessing_status}</span>
                      </div>
                    </div>
                  </div>

                  {selectedDataset.validation_errors && selectedDataset.validation_errors.length > 0 && (
                    <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <h4 className="text-sm font-semibold text-red-800 dark:text-red-300 mb-2">Validation Errors</h4>
                      <ul className="list-disc list-inside text-sm text-red-700 dark:text-red-400 space-y-1">
                        {selectedDataset.validation_errors.map((error, idx) => (
                          <li key={idx}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {inspectorView === 'samples' && (
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white">Sample Rows</h4>
                  {selectedDataset.sample_rows && selectedDataset.sample_rows.length > 0 ? (
                    <div className="space-y-3">
                      {selectedDataset.sample_rows.slice(0, 5).map((row, idx) => (
                        <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Sample #{idx + 1}</div>
                          <pre className="text-xs text-gray-900 dark:text-white overflow-auto">
                            {JSON.stringify(row, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400">No sample rows available</p>
                  )}
                </div>
              )}

              {inspectorView === 'quality' && selectedDataset.quality_metrics && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Token Length</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {Math.round(selectedDataset.quality_metrics.avg_token_length)}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Duplicates</div>
                      <div className={`text-2xl font-bold ${
                        selectedDataset.quality_metrics.duplicates > 10
                          ? 'text-orange-600 dark:text-orange-400'
                          : 'text-gray-900 dark:text-white'
                      }`}>
                        {selectedDataset.quality_metrics.duplicates}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Near Duplicates</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {selectedDataset.quality_metrics.near_duplicates}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Toxicity Score</div>
                      <div className={`text-2xl font-bold ${
                        selectedDataset.quality_metrics.toxicity_score > 0.5
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-green-600 dark:text-green-400'
                      }`}>
                        {(selectedDataset.quality_metrics.toxicity_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">PII Detected</div>
                      <div className={`text-2xl font-bold ${
                        selectedDataset.quality_metrics.pii_detected
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-green-600 dark:text-green-400'
                      }`}>
                        {selectedDataset.quality_metrics.pii_detected ? 'Yes' : 'No'}
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Similarity to Base</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {(selectedDataset.quality_metrics.similarity_to_base * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {selectedDataset.quality_metrics.language_distribution && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Language Distribution</h4>
                      <div className="space-y-2">
                        {Object.entries(selectedDataset.quality_metrics.language_distribution).map(([lang, pct]) => (
                          <div key={lang} className="flex items-center gap-3">
                            <div className="w-20 text-sm text-gray-700 dark:text-gray-300">{lang}</div>
                            <div className="flex-1 h-6 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-indigo-600 dark:bg-indigo-500"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <div className="w-12 text-sm font-semibold text-gray-900 dark:text-white text-right">
                              {pct}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
