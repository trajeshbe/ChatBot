/**
 * Export Wizard Button Component
 *
 * Provides export functionality for Tier 2 and Tier 3 modules.
 * Allows exporting POCs as production-ready standalone applications.
 *
 * Features:
 * - Module export initiation
 * - Progress tracking
 * - Package download
 * - Deployment options selection
 * - License tier configuration
 */

import { useState } from 'react'
import { Download, Package, Loader2, CheckCircle, AlertCircle, X } from 'lucide-react'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ExportWizardButtonProps {
  moduleCode: string
  moduleName: string
  tier: number
  customerName?: string
  customerEmail?: string
  variant?: 'button' | 'icon'
  size?: 'sm' | 'md' | 'lg'
}

interface ExportJobStatus {
  job_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled'
  progress_percentage: number
  current_step: string
  package_id?: string
  error_message?: string
}

export default function ExportWizardButton({
  moduleCode,
  moduleName,
  tier,
  customerName: initialCustomerName = 'Demo Customer',
  customerEmail: initialCustomerEmail = 'demo@example.com',
  variant = 'button',
  size = 'md'
}: ExportWizardButtonProps) {
  const [showModal, setShowModal] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [jobStatus, setJobStatus] = useState<ExportJobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Customer info (now editable)
  const [customerName, setCustomerName] = useState(initialCustomerName)
  const [customerEmail, setCustomerEmail] = useState(initialCustomerEmail)

  // Export configuration
  const [deploymentType, setDeploymentType] = useState('docker_compose')
  const [licenseTier, setLicenseTier] = useState('professional')
  const [tenantId, setTenantId] = useState('default')
  const [includeEmbeddings, setIncludeEmbeddings] = useState(true)
  const [includeMonitoring, setIncludeMonitoring] = useState(true)

  const initiateExport = async () => {
    setExporting(true)
    setError(null)
    setJobStatus(null)

    try {
      const payload = {
        module_name: moduleCode,
        customer_name: customerName,
        customer_email: customerEmail,
        deployment_type: deploymentType,
        license_tier: licenseTier,
        tenant_id: tenantId,
        options: {
          include_embeddings: includeEmbeddings,
          include_monitoring: includeMonitoring,
          include_backups: true,
          white_label: true,
          security_level: 'advanced',
          enable_telemetry: false
        }
      }

      const response = await axios.post(`${API_BASE}/api/v1/export/initiate`, payload)
      const jobId = response.data.job_id

      // Poll for status
      pollJobStatus(jobId)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to initiate export')
      setExporting(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 60
    let attempts = 0

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/v1/export/jobs/${jobId}`)
        const status: ExportJobStatus = response.data

        setJobStatus(status)

        if (status.status === 'completed') {
          clearInterval(interval)
          setExporting(false)
        } else if (status.status === 'failed') {
          clearInterval(interval)
          setError(status.error_message || 'Export failed')
          setExporting(false)
        }

        attempts++
        if (attempts >= maxAttempts) {
          clearInterval(interval)
          setError('Export timeout - please check job status manually')
          setExporting(false)
        }
      } catch (err: any) {
        clearInterval(interval)
        setError('Failed to check export status')
        setExporting(false)
      }
    }, 5000) // Poll every 5 seconds
  }

  const downloadPackage = async () => {
    if (!jobStatus?.package_id) return

    try {
      const response = await axios.get(
        `${API_BASE}/api/v1/export/packages/${jobStatus.package_id}/download`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${moduleCode}_export_${jobStatus.package_id}.tar.gz`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError('Failed to download package')
    }
  }

  const getSizeClass = () => {
    switch (size) {
      case 'sm': return 'px-2 py-1 text-sm'
      case 'lg': return 'px-6 py-3 text-lg'
      default: return 'px-4 py-2'
    }
  }

  if (variant === 'icon') {
    return (
      <>
        <button
          onClick={() => setShowModal(true)}
          className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="Export Module"
        >
          <Package className="w-5 h-5" />
        </button>
        {renderModal()}
      </>
    )
  }

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className={`${getSizeClass()} bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all flex items-center gap-2 shadow-md`}
      >
        <Package className="w-5 h-5" />
        <span>Export Module</span>
      </button>
      {renderModal()}
    </>
  )

  function renderModal() {
    if (!showModal) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-xl">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold mb-2">Export Module</h2>
                <p className="text-blue-100">
                  Export <strong>{moduleName}</strong> as a standalone application
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Customer Information */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Customer Information</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Customer Name *
                  </label>
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    disabled={exporting}
                    placeholder="Enter customer name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Customer Email *
                  </label>
                  <input
                    type="email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    disabled={exporting}
                    placeholder="customer@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Deployment Configuration */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Deployment Configuration</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Deployment Type
                  </label>
                  <select
                    value={deploymentType}
                    onChange={(e) => setDeploymentType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={exporting}
                  >
                    <option value="docker_compose">Docker Compose (Quick Start)</option>
                    <option value="kubernetes">Kubernetes (Production)</option>
                    <option value="aws_cloudformation">AWS CloudFormation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    License Tier
                  </label>
                  <select
                    value={licenseTier}
                    onChange={(e) => setLicenseTier(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    disabled={exporting}
                  >
                    <option value="starter">Starter - $50K/year</option>
                    <option value="professional">Professional - $100K/year</option>
                    <option value="enterprise">Enterprise - $250K/year</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Export Options */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Export Options</h3>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeEmbeddings}
                    onChange={(e) => setIncludeEmbeddings(e.target.checked)}
                    disabled={exporting}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm">Include Pre-computed Embeddings (faster deployment)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeMonitoring}
                    onChange={(e) => setIncludeMonitoring(e.target.checked)}
                    disabled={exporting}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm">Include Monitoring Stack (Grafana, Prometheus)</span>
                </label>
              </div>
            </div>

            {/* Export Status */}
            {jobStatus && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3">Export Progress</h3>
                <div className="space-y-3">
                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium">{jobStatus.current_step}</span>
                      <span className="text-gray-600">{jobStatus.progress_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          jobStatus.status === 'completed'
                            ? 'bg-green-500'
                            : jobStatus.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-blue-500'
                        }`}
                        style={{ width: `${jobStatus.progress_percentage}%` }}
                      />
                    </div>
                  </div>

                  {/* Status Message */}
                  {jobStatus.status === 'completed' && (
                    <div className="flex items-center gap-2 text-green-700 bg-green-50 p-3 rounded-lg">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-medium">Export completed successfully!</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-2 text-red-700">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Export Failed</p>
                    <p className="text-sm mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end gap-3">
            <button
              onClick={() => setShowModal(false)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              disabled={exporting}
            >
              Close
            </button>

            {jobStatus?.status === 'completed' && jobStatus.package_id && (
              <button
                onClick={downloadPackage}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Download className="w-5 h-5" />
                Download Package
              </button>
            )}

            {!exporting && !jobStatus && (
              <button
                onClick={initiateExport}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all flex items-center gap-2"
              >
                <Package className="w-5 h-5" />
                Start Export
              </button>
            )}

            {exporting && (
              <button
                disabled
                className="px-4 py-2 bg-gray-400 text-white rounded-lg flex items-center gap-2 cursor-not-allowed"
              >
                <Loader2 className="w-5 h-5 animate-spin" />
                Exporting...
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }
}
