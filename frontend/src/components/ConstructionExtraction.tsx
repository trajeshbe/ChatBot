import { useState, useRef } from 'react'
import { Upload, Loader2, CheckCircle, XCircle, FileArchive, Building2 } from 'lucide-react'
import axios from 'axios'

interface BuildingMetrics {
  levels_above_ground: string | number
  levels_below_ground: string | number
  gross_floor_area_m2: string | number
  external_area_m2: string | number
  site_area_m2?: string | number
  building_height_m?: string | number
}

interface ExtractionResult {
  success: boolean
  project_name: string
  metrics: BuildingMetrics
  confidence: number
  sources: string[]
  details: {
    metrics_found: number
    total_metrics: number
    documents_processed: number
    aggregation_method: string
  }
  processing_time_seconds?: number
  error?: string
}

export default function ConstructionExtraction() {
  const [isExtracting, setIsExtracting] = useState(false)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.endsWith('.zip')) {
      setError('Please upload a ZIP file containing construction documents')
      return
    }

    setIsExtracting(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('zip_file', file)
    formData.append('project_name', file.name.replace('.zip', ''))
    formData.append('session_id', sessionStorage.getItem('chat_session_id') || 'default')

    try {
      const response = await axios.post<ExtractionResult>(
        'http://localhost:8000/api/v1/construction-metrics/extract',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      setResult(response.data)
    } catch (err: any) {
      console.error('Extraction error:', err)
      setError(err.response?.data?.detail || 'Failed to extract construction metrics')
    } finally {
      setIsExtracting(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const MetricCard = ({ label, value, unit }: { label: string; value: string | number; unit?: string }) => {
    const isNA = value === 'NA' || value === null
    return (
      <div className={`p-4 rounded-lg border ${isNA ? 'bg-slate-50 border-slate-200' : 'bg-emerald-50 border-emerald-200'}`}>
        <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1">{label}</div>
        <div className={`text-2xl font-bold ${isNA ? 'text-slate-400' : 'text-emerald-700'}`}>
          {isNA ? 'NA' : `${value}${unit || ''}`}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white">
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-full max-w-4xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
              <Building2 className="w-8 h-8 text-blue-600" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">
              Construction Metrics Extraction
            </h1>
            <p className="text-slate-600">
              Upload a ZIP file containing construction documents to automatically extract building metrics
            </p>
          </div>

          {/* Upload Button */}
          <div className="mb-8">
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip"
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isExtracting}
              className="w-full py-6 px-8 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex flex-col items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
                  <span className="text-blue-700 font-medium">Processing documents...</span>
                </>
              ) : (
                <>
                  <FileArchive className="w-12 h-12 text-blue-600" />
                  <span className="text-blue-700 font-medium">Click to upload ZIP file</span>
                  <span className="text-sm text-slate-500">Architectural drawings, DA approvals, site photos</span>
                </>
              )}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-red-900">Extraction Failed</div>
                <div className="text-sm text-red-700">{error}</div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-6">
              {/* Success Header */}
              <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-emerald-600" />
                  <div>
                    <div className="font-semibold text-emerald-900">{result.project_name}</div>
                    <div className="text-sm text-emerald-700">
                      Confidence: {(result.confidence * 100).toFixed(0)}% •
                      {result.details.metrics_found}/{result.details.total_metrics} metrics found •
                      {result.details.documents_processed} documents processed
                    </div>
                  </div>
                </div>
                {result.processing_time_seconds && (
                  <div className="text-sm text-emerald-700">
                    {result.processing_time_seconds.toFixed(1)}s
                  </div>
                )}
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <MetricCard
                  label="Levels (Above Ground)"
                  value={result.metrics.levels_above_ground}
                />
                <MetricCard
                  label="Levels (Below Ground)"
                  value={result.metrics.levels_below_ground}
                />
                <MetricCard
                  label="Gross Floor Area"
                  value={result.metrics.gross_floor_area_m2}
                  unit=" m²"
                />
                <MetricCard
                  label="External Area"
                  value={result.metrics.external_area_m2}
                  unit=" m²"
                />
                {result.metrics.site_area_m2 && (
                  <MetricCard
                    label="Site Area"
                    value={result.metrics.site_area_m2}
                    unit=" m²"
                  />
                )}
                {result.metrics.building_height_m && (
                  <MetricCard
                    label="Building Height"
                    value={result.metrics.building_height_m}
                    unit=" m"
                  />
                )}
              </div>

              {/* Sources */}
              {result.sources.length > 0 && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="text-sm font-semibold text-slate-700 mb-2">
                    Source Documents ({result.sources.length})
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {result.sources.map((source, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2 py-1 bg-white border border-slate-200 rounded text-slate-600"
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Download JSON */}
              <button
                onClick={() => {
                  const dataStr = JSON.stringify(result, null, 2)
                  const dataBlob = new Blob([dataStr], { type: 'application/json' })
                  const url = URL.createObjectURL(dataBlob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = `${result.project_name}_metrics.json`
                  link.click()
                  URL.revokeObjectURL(url)
                }}
                className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Download Results as JSON
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
