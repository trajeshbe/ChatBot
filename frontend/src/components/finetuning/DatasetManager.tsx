/**
 * Dataset Manager Component
 *
 * Upload and manage fine-tuning datasets with:
 * - Drag & drop file upload
 * - Dataset validation and preview
 * - Dataset list and deletion
 */

import { useState, useEffect, useCallback } from 'react'
import { Upload, File, Trash2, Eye, CheckCircle, XCircle, AlertTriangle, Database } from 'lucide-react'

interface Dataset {
  id: string
  name: string
  file_path: string
  format: string
  sample_count: number
  valid: boolean
  validation_errors: string[] | null
  created_at: string
  user_id: string | null
  project_id: string | null
}

interface DatasetManagerProps {
  onRefresh?: () => void
}

export default function DatasetManager({ onRefresh }: DatasetManagerProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (response.ok) {
        const data = await response.json()
        setDatasets(data.datasets || [])
      }
    } catch (error) {
      console.error('Error loading datasets:', error)
    }
    setLoading(false)
  }

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadDataset(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadDataset(e.target.files[0])
    }
  }

  const uploadDataset = async (file: File) => {
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('name', file.name)
      formData.append('format', detectFormat(file.name))

      const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets/upload`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        alert(`✅ Dataset uploaded successfully!\n\nName: ${result.name}\nSamples: ${result.sample_count}\nValid: ${result.valid ? 'Yes' : 'No'}`)
        await loadDatasets()
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Upload failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error uploading dataset:', error)
      alert('❌ Upload failed. Please try again.')
    }
    setUploading(false)
  }

  const detectFormat = (filename: string): string => {
    if (filename.endsWith('.json') || filename.endsWith('.jsonl')) return 'json'
    if (filename.endsWith('.csv')) return 'csv'
    if (filename.endsWith('.parquet')) return 'parquet'
    return 'json'
  }

  const deleteDataset = async (id: string, name: string) => {
    if (!confirm(`⚠️ Delete dataset "${name}"?\n\nThis action cannot be undone.`)) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets/${id}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      if (response.ok) {
        alert('✅ Dataset deleted successfully!')
        await loadDatasets()
        if (selectedDataset?.id === id) {
          setSelectedDataset(null)
          setPreviewData(null)
        }
        if (onRefresh) onRefresh()
      } else {
        const error = await response.json()
        alert(`❌ Delete failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error deleting dataset:', error)
      alert('❌ Delete failed. Please try again.')
    }
  }

  const previewDataset = async (dataset: Dataset) => {
    setSelectedDataset(dataset)
    try {
      const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets/${dataset.id}`)
      if (response.ok) {
        const data = await response.json()
        setPreviewData(data)
      }
    } catch (error) {
      console.error('Error loading dataset preview:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Upload Dataset
        </h3>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-blue-500'
          }`}
        >
          <Upload className={`w-12 h-12 mx-auto mb-4 ${dragActive ? 'text-blue-500' : 'text-slate-400'}`} />
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
            Drag and drop your dataset file here, or click to browse
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-500 mb-4">
            Supported formats: JSON, JSONL, CSV, Parquet
          </p>
          <input
            type="file"
            onChange={handleFileInput}
            accept=".json,.jsonl,.csv,.parquet"
            className="hidden"
            id="dataset-upload"
            disabled={uploading}
          />
          <label
            htmlFor="dataset-upload"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer disabled:bg-slate-300 disabled:cursor-not-allowed"
          >
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploading...' : 'Browse Files'}
          </label>
        </div>

        <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-200 font-medium mb-2">
            Dataset Format Requirements:
          </p>
          <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1 ml-4 list-disc">
            <li>JSON/JSONL: Array of objects or line-delimited JSON</li>
            <li>Required fields depend on training objective:</li>
            <li className="ml-4">• QA: {"{"}"prompt", "response"{"}"}</li>
            <li className="ml-4">• Classification: {"{"}"text", "label"{"}"}</li>
            <li className="ml-4">• RLHF: {"{"}"prompt", "chosen", "rejected"{"}"}</li>
          </ul>
        </div>
      </div>

      {/* Datasets List */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Datasets
            </h3>
            <button
              onClick={loadDatasets}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="divide-y divide-slate-200 dark:divide-slate-700">
          {loading ? (
            <div className="px-6 py-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : datasets.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Database className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-slate-500 dark:text-slate-400">No datasets uploaded yet</p>
            </div>
          ) : (
            datasets.map((dataset) => (
              <div
                key={dataset.id}
                className="px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <File className="w-5 h-5 text-slate-400 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {dataset.name}
                        </p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {dataset.sample_count.toLocaleString()} samples
                          </span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            Format: {dataset.format.toUpperCase()}
                          </span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {new Date(dataset.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {dataset.validation_errors && dataset.validation_errors.length > 0 && (
                          <div className="mt-2 text-xs text-red-600 dark:text-red-400">
                            ⚠️ {dataset.validation_errors.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {dataset.valid ? (
                      <CheckCircle className="w-5 h-5 text-green-500" title="Valid dataset" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" title="Invalid dataset" />
                    )}
                    <button
                      onClick={() => previewDataset(dataset)}
                      className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                      title="Preview dataset"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteDataset(dataset.id, dataset.name)}
                      className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      title="Delete dataset"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Preview Modal */}
      {selectedDataset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Dataset Preview: {selectedDataset.name}
                </h3>
                <button
                  onClick={() => {
                    setSelectedDataset(null)
                    setPreviewData(null)
                  }}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6 overflow-y-auto">
              {previewData ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500 dark:text-slate-400">Total Samples</p>
                      <p className="text-lg font-semibold text-slate-900 dark:text-white">
                        {previewData.sample_count}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500 dark:text-slate-400">Format</p>
                      <p className="text-lg font-semibold text-slate-900 dark:text-white">
                        {previewData.format.toUpperCase()}
                      </p>
                    </div>
                  </div>
                  {previewData.samples && previewData.samples.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Sample Data (first 5):
                      </p>
                      <div className="space-y-2">
                        {previewData.samples.slice(0, 5).map((sample: any, idx: number) => (
                          <div
                            key={idx}
                            className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 text-xs font-mono overflow-x-auto"
                          >
                            <pre className="text-slate-700 dark:text-slate-300">
                              {JSON.stringify(sample, null, 2)}
                            </pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
