/**
 * ExportWizardButton Component - POC-to-Production Export Package Generator
 *
 * Features:
 * - Select module from tier 2 or tier 3
 * - Create export package via API
 * - Monitor export progress
 * - Download generated ZIP
 * - Beautiful UI with status indicators
 *
 * Related: Requirement #10 - Export Wizard Enhancement
 */

import { useState, useEffect } from 'react'
import { Package, Download, Loader2, CheckCircle, AlertCircle, X, Archive, FileCode } from 'lucide-react'
import axios from 'axios'

interface Module {
  name: string
  code: string
  description: string
  category: string
  tags: string[]
}

interface ExportJob {
  export_id: string
  status: 'started' | 'completed' | 'failed'
  progress: number
  current_step: string
  zip_path?: string
  error?: string
}

interface Props {
  onExportComplete?: (zipPath: string) => void
  className?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ExportWizardButton({ onExportComplete, className = '' }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [step, setStep] = useState<'select-tier' | 'select-module' | 'exporting' | 'complete'>('select-tier')
  const [selectedTier, setSelectedTier] = useState<2 | 3 | null>(null)
  const [modules, setModules] = useState<Module[]>([])
  const [selectedModule, setSelectedModule] = useState<string | null>(null)
  const [isLoadingModules, setIsLoadingModules] = useState(false)
  const [exportJob, setExportJob] = useState<ExportJob | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Poll for export status
  useEffect(() => {
    if (!exportJob || exportJob.status === 'completed' || exportJob.status === 'failed') {
      return
    }

    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/export-wizard/status/${exportJob.export_id}`)
        setExportJob(response.data)

        if (response.data.status === 'completed') {
          setStep('complete')
          if (onExportComplete && response.data.zip_path) {
            onExportComplete(response.data.zip_path)
          }
        } else if (response.data.status === 'failed') {
          setError(response.data.error || 'Export failed')
        }
      } catch (err: any) {
        console.error('Failed to poll export status:', err)
        setError(err.response?.data?.detail || 'Failed to check export status')
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [exportJob, onExportComplete])

  // Load modules when tier is selected
  useEffect(() => {
    if (selectedTier) {
      loadModules(selectedTier)
    }
  }, [selectedTier])

  const loadModules = async (tier: 2 | 3) => {
    setIsLoadingModules(true)
    setError(null)

    try {
      const response = await axios.get(`${API_URL}/api/v1/export-wizard/modules/tier/${tier}`)
      setModules(response.data.modules || [])
      setStep('select-module')
    } catch (err: any) {
      console.error('Failed to load modules:', err)
      setError(err.response?.data?.detail || 'Failed to load modules')
    } finally {
      setIsLoadingModules(false)
    }
  }

  const startExport = async () => {
    if (!selectedModule || !selectedTier) return

    setError(null)
    setStep('exporting')

    try {
      const response = await axios.post(`${API_URL}/api/v1/export-wizard/export`, {
        module_name: selectedModule,
        module_tier: selectedTier
      })

      setExportJob({
        export_id: response.data.export_id,
        status: 'started',
        progress: 0,
        current_step: 'Initializing export...'
      })
    } catch (err: any) {
      console.error('Failed to start export:', err)
      setError(err.response?.data?.detail || 'Failed to start export')
      setStep('select-module')
    }
  }

  const downloadExport = async () => {
    if (!exportJob?.export_id) return

    try {
      // Download file
      const response = await axios.get(
        `${API_URL}/api/v1/export-wizard/download/${exportJob.export_id}`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Extract filename from content-disposition header or use default
      const contentDisposition = response.headers['content-disposition']
      const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/)
      const filename = filenameMatch?.[1] || `export_${exportJob.export_id}.zip`

      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Failed to download export:', err)
      setError(err.response?.data?.detail || 'Failed to download export package')
    }
  }

  const resetWizard = () => {
    setStep('select-tier')
    setSelectedTier(null)
    setSelectedModule(null)
    setModules([])
    setExportJob(null)
    setError(null)
    setIsOpen(false)
  }

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600
          hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg transition-all
          shadow-md hover:shadow-lg ${className}`}
      >
        <Package size={20} />
        <span>Export POC Package</span>
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Package className="text-purple-600 dark:text-purple-400" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Export Wizard
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Create POC-to-Production deployment package
                  </p>
                </div>
              </div>
              <button
                onClick={resetWizard}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Error Display */}
              {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
                  <AlertCircle size={20} className="text-red-600 dark:text-red-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900 dark:text-red-200">Error</p>
                    <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
                  </div>
                  <button
                    onClick={() => setError(null)}
                    className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                  >
                    <X size={16} />
                  </button>
                </div>
              )}

              {/* Step 1: Select Tier */}
              {step === 'select-tier' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Step 1: Select Module Tier
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Choose between Domain Verticals (Tier 2) or Customer Solutions (Tier 3)
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Tier 2 */}
                    <button
                      onClick={() => setSelectedTier(2)}
                      className="p-6 border-2 border-gray-200 dark:border-gray-700 hover:border-purple-500
                        dark:hover:border-purple-500 rounded-xl transition-all hover:shadow-lg group"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg group-hover:bg-purple-100
                          dark:group-hover:bg-purple-900/30 transition-colors">
                          <FileCode size={24} className="text-blue-600 dark:text-blue-400 group-hover:text-purple-600
                            dark:group-hover:text-purple-400 transition-colors" />
                        </div>
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                          Tier 2
                        </h4>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 text-left">
                        <span className="font-medium">Domain Verticals</span><br />
                        Industry-specific solutions (Analytics, HR, Procurement, etc.)
                      </p>
                    </button>

                    {/* Tier 3 */}
                    <button
                      onClick={() => setSelectedTier(3)}
                      className="p-6 border-2 border-gray-200 dark:border-gray-700 hover:border-purple-500
                        dark:hover:border-purple-500 rounded-xl transition-all hover:shadow-lg group"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg group-hover:bg-purple-100
                          dark:group-hover:bg-purple-900/30 transition-colors">
                          <Archive size={24} className="text-green-600 dark:text-green-400 group-hover:text-purple-600
                            dark:group-hover:text-purple-400 transition-colors" />
                        </div>
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                          Tier 3
                        </h4>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 text-left">
                        <span className="font-medium">Customer Solutions</span><br />
                        Customer-specific POCs (British Council, Grant Thornton, CRU, etc.)
                      </p>
                    </button>
                  </div>
                </div>
              )}

              {/* Step 2: Select Module */}
              {step === 'select-module' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Step 2: Select Module to Export
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Choose the module you want to export (Tier {selectedTier})
                    </p>
                  </div>

                  {isLoadingModules ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="animate-spin text-purple-600" size={32} />
                    </div>
                  ) : modules.length === 0 ? (
                    <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                      No modules available for Tier {selectedTier}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-3 max-h-96 overflow-y-auto">
                      {modules.map((module) => (
                        <button
                          key={module.code}
                          onClick={() => setSelectedModule(module.name)}
                          className={`p-4 border-2 rounded-lg text-left transition-all ${
                            selectedModule === module.name
                              ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                                {module.name}
                              </h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                {module.description}
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {module.tags.slice(0, 3).map((tag) => (
                                  <span
                                    key={tag}
                                    className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700
                                      text-gray-700 dark:text-gray-300 rounded"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                            {selectedModule === module.name && (
                              <CheckCircle size={20} className="text-purple-600 dark:text-purple-400 ml-2" />
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Step 3: Exporting */}
              {step === 'exporting' && exportJob && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Creating Export Package...
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Module: {selectedModule} (Tier {selectedTier})
                    </p>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-700 dark:text-gray-300">{exportJob.current_step}</span>
                      <span className="text-gray-500 dark:text-gray-400">{exportJob.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-purple-600 to-indigo-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${exportJob.progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Status Icon */}
                  <div className="flex items-center justify-center py-8">
                    <div className="p-4 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                      <Loader2 className="animate-spin text-purple-600 dark:text-purple-400" size={48} />
                    </div>
                  </div>

                  <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                    This may take 2-5 minutes. You can close this dialog and check back later.
                  </div>
                </div>
              )}

              {/* Step 4: Complete */}
              {step === 'complete' && exportJob && (
                <div className="space-y-6">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center p-4 bg-green-100 dark:bg-green-900/30
                      rounded-full mb-4">
                      <CheckCircle size={48} className="text-green-600 dark:text-green-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Export Package Ready!
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Your {selectedModule} export package is ready to download
                    </p>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Module:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{selectedModule}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Tier:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{selectedTier}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Export ID:</span>
                      <span className="font-mono text-xs text-gray-900 dark:text-white">{exportJob.export_id}</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">Package Contents:</span><br />
                      • Complete application codebase (backend + frontend)<br />
                      • All Tier 1 core modules + {selectedModule}<br />
                      • Filtered database setup scripts (11 modules)<br />
                      • Docker Compose configuration<br />
                      • Installation guide (INSTALL.md)<br />
                      • Verification script (verify-export.sh)
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-6 bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center justify-between gap-4">
                <button
                  onClick={() => {
                    if (step === 'select-module') {
                      setStep('select-tier')
                      setSelectedModule(null)
                    } else if (step === 'complete') {
                      resetWizard()
                    } else {
                      resetWizard()
                    }
                  }}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200
                    dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  {step === 'complete' ? 'Close' : 'Back'}
                </button>

                <div className="flex gap-3">
                  {step === 'select-module' && (
                    <button
                      onClick={startExport}
                      disabled={!selectedModule}
                      className={`flex items-center gap-2 px-6 py-2 rounded-lg transition-all ${
                        selectedModule
                          ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
                          : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <Package size={18} />
                      <span>Create Export Package</span>
                    </button>
                  )}

                  {step === 'complete' && (
                    <button
                      onClick={downloadExport}
                      className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-green-600 to-emerald-600
                        hover:from-green-700 hover:to-emerald-700 text-white rounded-lg transition-all"
                    >
                      <Download size={18} />
                      <span>Download ZIP Package</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
