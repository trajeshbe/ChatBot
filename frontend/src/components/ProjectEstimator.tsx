import { useState, useEffect, useCallback } from 'react'
import { FileText, Download, Upload, Calculator, FileSpreadsheet, Loader2, Settings, TrendingUp, TrendingDown, Minus, X, File, FolderOpen } from 'lucide-react'
import axios from 'axios'
import { useDropzone } from 'react-dropzone'

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ProjectEstimatorProps {
  sessionId: string
}

interface ScenarioConfig {
  name: string
  description: string
  // Billing Rates ($/hour)
  planning_rate: number
  development_rate: number
  testing_rate: number
  ui_development_rate: number
  solution_architect_rate: number
  scraping_development_rate: number

  // Overhead Percentages (%)
  solution_architect_percentage: number
  project_manager_percentage: number
  business_analyst_percentage: number
  contingency_percentage: number

  // Testing Percentages (%)
  unit_testing_percentage: number
  qa_testing_percentage: number
  integration_testing_percentage: number

  // Infrastructure Costs ($)
  one_time_infrastructure: number
  monthly_bau: number
}

interface EstimationResult {
  scenario: string
  brd_url?: string
  excel_url?: string  // Backend returns excel_url, not cost_estimation_url
  project_name: string
  total_cost?: number
  total_effort_hours?: number
  generated_at: string
}

// Predefined scenarios based on reference guide
const BASELINE_SCENARIO: ScenarioConfig = {
  name: 'Baseline',
  description: 'Standard rates from reference guide - Balanced approach',
  planning_rate: 25,
  development_rate: 30,
  testing_rate: 25,
  ui_development_rate: 22,
  solution_architect_rate: 40,
  scraping_development_rate: 22,
  solution_architect_percentage: 10,
  project_manager_percentage: 5,
  business_analyst_percentage: 5,
  contingency_percentage: 10,
  unit_testing_percentage: 20,
  qa_testing_percentage: 25,
  integration_testing_percentage: 20,
  one_time_infrastructure: 280,
  monthly_bau: 1030
}

const CONSERVATIVE_SCENARIO: ScenarioConfig = {
  name: 'Conservative',
  description: 'Higher rates with increased buffer - Risk-averse estimation',
  planning_rate: 35,
  development_rate: 45,
  testing_rate: 35,
  ui_development_rate: 30,
  solution_architect_rate: 60,
  scraping_development_rate: 30,
  solution_architect_percentage: 15,
  project_manager_percentage: 8,
  business_analyst_percentage: 7,
  contingency_percentage: 20,
  unit_testing_percentage: 25,
  qa_testing_percentage: 30,
  integration_testing_percentage: 25,
  one_time_infrastructure: 500,
  monthly_bau: 1500
}

const AGGRESSIVE_SCENARIO: ScenarioConfig = {
  name: 'Aggressive',
  description: 'Competitive rates with minimal buffer - Optimistic estimation',
  planning_rate: 20,
  development_rate: 25,
  testing_rate: 20,
  ui_development_rate: 18,
  solution_architect_rate: 30,
  scraping_development_rate: 18,
  solution_architect_percentage: 7,
  project_manager_percentage: 3,
  business_analyst_percentage: 3,
  contingency_percentage: 5,
  unit_testing_percentage: 15,
  qa_testing_percentage: 20,
  integration_testing_percentage: 15,
  one_time_infrastructure: 150,
  monthly_bau: 700
}

export default function ProjectEstimator({ sessionId }: ProjectEstimatorProps) {
  // State
  const [projectScope, setProjectScope] = useState('')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  // Multi-file upload states
  const [projectScopeFiles, setProjectScopeFiles] = useState<File[]>([])
  const [sampleDataFiles, setSampleDataFiles] = useState<File[]>([])
  const [referenceBRDFiles, setReferenceBRDFiles] = useState<File[]>([])
  const [costTemplateFiles, setCostTemplateFiles] = useState<File[]>([])

  const [isGenerating, setIsGenerating] = useState(false)
  const [estimationResults, setEstimationResults] = useState<EstimationResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [globalSelectedModel, setGlobalSelectedModel] = useState<string>('gpt-4-turbo')

  // Project type selection for agentic workflow
  const [projectType, setProjectType] = useState<'POC' | 'Staff Augmentation' | 'Full Service'>('Full Service')

  // Scenario management
  const [activeScenario, setActiveScenario] = useState<'baseline' | 'conservative' | 'aggressive'>('baseline')
  const [showConfig, setShowConfig] = useState(false)

  const [baselineConfig, setBaselineConfig] = useState<ScenarioConfig>(BASELINE_SCENARIO)
  const [conservativeConfig, setConservativeConfig] = useState<ScenarioConfig>(CONSERVATIVE_SCENARIO)
  const [aggressiveConfig, setAggressiveConfig] = useState<ScenarioConfig>(AGGRESSIVE_SCENARIO)

  // Get current scenario config
  const getCurrentConfig = () => {
    switch (activeScenario) {
      case 'baseline': return baselineConfig
      case 'conservative': return conservativeConfig
      case 'aggressive': return aggressiveConfig
    }
  }

  const updateCurrentConfig = (updates: Partial<ScenarioConfig>) => {
    switch (activeScenario) {
      case 'baseline':
        setBaselineConfig({ ...baselineConfig, ...updates })
        break
      case 'conservative':
        setConservativeConfig({ ...conservativeConfig, ...updates })
        break
      case 'aggressive':
        setAggressiveConfig({ ...aggressiveConfig, ...updates })
        break
    }
  }

  // File Management Helpers
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getTotalFileSize = (files: File[]): number => {
    return files.reduce((total, file) => total + file.size, 0)
  }

  const removeFile = (files: File[], setFiles: React.Dispatch<React.SetStateAction<File[]>>, index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  // Dropzone callbacks
  const onDropScope = useCallback((acceptedFiles: File[]) => {
    setProjectScopeFiles(prev => [...prev, ...acceptedFiles])
    setError(null)
  }, [])

  const onDropSampleData = useCallback((acceptedFiles: File[]) => {
    setSampleDataFiles(prev => [...prev, ...acceptedFiles])
    setError(null)
  }, [])

  const onDropBRD = useCallback((acceptedFiles: File[]) => {
    setReferenceBRDFiles(prev => [...prev, ...acceptedFiles])
    setError(null)
  }, [])

  const onDropCostTemplates = useCallback((acceptedFiles: File[]) => {
    setCostTemplateFiles(prev => [...prev, ...acceptedFiles])
    setError(null)
  }, [])

  // Configure dropzones
  const scopeDropzone = useDropzone({
    onDrop: onDropScope,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  })

  const sampleDataDropzone = useDropzone({
    onDrop: onDropSampleData,
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  })

  const brdDropzone = useDropzone({
    onDrop: onDropBRD,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  })

  const costTemplatesDropzone = useDropzone({
    onDrop: onDropCostTemplates,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  })

  // Load defaults from API and merge with saved state on mount
  useEffect(() => {
    const loadDefaults = async () => {
      try {
        // Fetch defaults from API
        const response = await axios.get(`${API_BASE_URL}/api/v1/project-estimator/defaults`)
        const apiDefaults = response.data

        // Transform API response to match our config structure
        const transformScenario = (scenarioData: any): ScenarioConfig => ({
          name: scenarioData.name,
          description: scenarioData.description,
          ...scenarioData.billing_rates,
          ...scenarioData.overhead_percentages,
          ...scenarioData.testing_percentages,
          ...scenarioData.infrastructure_costs
        })

        // Get API defaults for each scenario
        const apiBaseline = transformScenario(apiDefaults.scenarios.baseline)
        const apiConservative = transformScenario(apiDefaults.scenarios.conservative)
        const apiAggressive = transformScenario(apiDefaults.scenarios.aggressive)

        if (typeof window !== 'undefined') {
          const savedScope = localStorage.getItem('projectEstimator_scope')
          const savedModel = localStorage.getItem('globalSelectedModel')
          const savedBaseline = localStorage.getItem('projectEstimator_baseline')
          const savedConservative = localStorage.getItem('projectEstimator_conservative')
          const savedAggressive = localStorage.getItem('projectEstimator_aggressive')

          if (savedScope) setProjectScope(savedScope)
          if (savedModel) setGlobalSelectedModel(savedModel)

          // Use localStorage if exists (user changes take precedence), otherwise use API defaults
          setBaselineConfig(savedBaseline ? JSON.parse(savedBaseline) : apiBaseline)
          setConservativeConfig(savedConservative ? JSON.parse(savedConservative) : apiConservative)
          setAggressiveConfig(savedAggressive ? JSON.parse(savedAggressive) : apiAggressive)
        }
      } catch (error) {
        console.error('Failed to load defaults from API, using hardcoded defaults:', error)
        // Fallback to hardcoded defaults if API fails
        if (typeof window !== 'undefined') {
          const savedScope = localStorage.getItem('projectEstimator_scope')
          const savedModel = localStorage.getItem('globalSelectedModel')
          const savedBaseline = localStorage.getItem('projectEstimator_baseline')
          const savedConservative = localStorage.getItem('projectEstimator_conservative')
          const savedAggressive = localStorage.getItem('projectEstimator_aggressive')

          if (savedScope) setProjectScope(savedScope)
          if (savedModel) setGlobalSelectedModel(savedModel)
          if (savedBaseline) setBaselineConfig(JSON.parse(savedBaseline))
          if (savedConservative) setConservativeConfig(JSON.parse(savedConservative))
          if (savedAggressive) setAggressiveConfig(JSON.parse(savedAggressive))
        }
      }
    }

    loadDefaults()
  }, [])

  // Save state to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('projectEstimator_scope', projectScope)
      localStorage.setItem('projectEstimator_baseline', JSON.stringify(baselineConfig))
      localStorage.setItem('projectEstimator_conservative', JSON.stringify(conservativeConfig))
      localStorage.setItem('projectEstimator_aggressive', JSON.stringify(aggressiveConfig))
    }
  }, [projectScope, baselineConfig, conservativeConfig, aggressiveConfig])

  // Listen for global model changes
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'globalSelectedModel' && e.newValue) {
        setGlobalSelectedModel(e.newValue)
      }
    }
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setUploadedFile(file)
      setError(null)
    }
  }

  const handleGenerateEstimation = async () => {
    if (!projectScope.trim() && !uploadedFile) {
      setError('Please provide a project scope description or upload a scope document')
      return
    }

    setIsGenerating(true)
    setError(null)
    setEstimationResults([])

    try {
      // Generate estimation for baseline scenario only (by default)
      const scenarios = [
        { name: 'baseline', config: baselineConfig }
        // Uncomment below to generate all 3 scenarios:
        // { name: 'conservative', config: conservativeConfig },
        // { name: 'aggressive', config: aggressiveConfig }
      ]

      const results: EstimationResult[] = []

      for (const scenario of scenarios) {
        const formData = new FormData()

        // NEW AGENTIC WORKFLOW PARAMETERS
        formData.append('project_scope', projectScope)
        formData.append('project_type', projectType)
        formData.append('scenario', scenario.name) // 'baseline', 'conservative', or 'aggressive'

        // Rate configuration (extract from scenario config)
        const rateConfig = {
          planning_rate: scenario.config.planning_rate,
          development_rate: scenario.config.development_rate,
          testing_rate: scenario.config.testing_rate,
          ui_development_rate: scenario.config.ui_development_rate,
          solution_architect_rate: scenario.config.solution_architect_rate,
          scraping_development_rate: scenario.config.scraping_development_rate,
          // Add new rate categories if not present
          devops_rate: (scenario.config as any).devops_rate || 35,
          data_engineering_rate: (scenario.config as any).data_engineering_rate || 40,
          ml_engineering_rate: (scenario.config as any).ml_engineering_rate || 50
        }
        formData.append('rate_config', JSON.stringify(rateConfig))

        // Overhead configuration
        const overheadConfig = {
          overhead_percentage: scenario.config.contingency_percentage / 100
        }
        formData.append('overhead_config', JSON.stringify(overheadConfig))

        // Append multi-file uploads (NEW PARAMETER NAMES)
        // Note: projectScopeFiles not used in new API, combined with project_scope text

        sampleDataFiles.forEach((file) => {
          formData.append('sample_files', file)  // Changed from 'sample_data_files'
        })

        referenceBRDFiles.forEach((file) => {
          formData.append('brd_files', file)  // Changed from 'reference_brd_files'
        })

        costTemplateFiles.forEach((file) => {
          formData.append('cost_files', file)  // Changed from 'cost_template_files'
        })

        const response = await axios.post(
          `${API_BASE_URL}/api/v1/project-estimator/generate-agentic`,  // NEW ENDPOINT
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        )

        results.push({
          ...response.data,
          scenario: scenario.name
        })
      }

      setEstimationResults(results)
    } catch (err: any) {
      console.error('Estimation generation error:', err)

      // Handle Pydantic validation errors and other error formats
      let errorMessage = 'Failed to generate estimation';

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;

        if (Array.isArray(detail)) {
          // Pydantic validation error array
          errorMessage = detail.map(e => {
            const location = e.loc ? e.loc.join('.') : 'field';
            return `${location}: ${e.msg}`;
          }).join('; ');
        } else if (typeof detail === 'string') {
          // Simple string error
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail.msg) {
          // Single validation error object
          const location = detail.loc ? detail.loc.join('.') : 'field';
          errorMessage = `${location}: ${detail.msg}`;
        } else if (typeof detail === 'object') {
          // Generic object - try to extract meaningful message
          errorMessage = JSON.stringify(detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await axios.get(url, {
        responseType: 'blob',
      })

      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = downloadUrl
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('Download error:', err)
      setError('Failed to download file')
    }
  }

  const getScenarioIcon = (scenario: string) => {
    switch (scenario) {
      case 'baseline': return <Minus className="h-5 w-5" />
      case 'conservative': return <TrendingUp className="h-5 w-5" />
      case 'aggressive': return <TrendingDown className="h-5 w-5" />
      default: return null
    }
  }

  const getScenarioTextColor = (scenario: string) => {
    switch (scenario) {
      case 'baseline': return 'text-primary-600 dark:text-blue-400'
      case 'conservative': return 'text-red-600 dark:text-red-400'
      case 'aggressive': return 'text-green-600 dark:text-green-400'
      default: return 'text-slate-600 dark:text-slate-400'
    }
  }

  const getScenarioButtonClasses = (scenario: string, disabled: boolean) => {
    if (disabled) {
      return 'px-3 py-1 text-xs bg-slate-300 dark:bg-slate-700 text-white rounded transition-colors'
    }
    switch (scenario) {
      case 'baseline':
        return 'px-3 py-1 text-xs bg-primary-600 hover:bg-primary-700 text-white rounded transition-colors'
      case 'conservative':
        return 'px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded transition-colors'
      case 'aggressive':
        return 'px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded transition-colors'
      default:
        return 'px-3 py-1 text-xs bg-slate-600 hover:bg-slate-700 text-white rounded transition-colors'
    }
  }

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-3">
            <Calculator className="h-8 w-8 text-primary-600 dark:text-blue-400" />
            Project Estimator
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Generate BRD and cost estimations with AI-powered analysis. Compare 3 scenarios side-by-side.
          </p>
        </div>

        {/* Main Content */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md border border-slate-200 dark:border-slate-700 p-6 mb-6">
          {/* Multi-File Upload Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-primary-600 dark:text-blue-400" />
              Upload Reference Files (Recommended for Higher Quality)
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Upload historical templates and sample data to improve estimation accuracy using AI-powered pattern matching.
            </p>

            <div className="grid grid-cols-2 gap-4">
              {/* 1. Project Scope Documents */}
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                  1. Project Scope Documents ({projectScopeFiles.length})
                </label>
                <div
                  {...scopeDropzone.getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                    scopeDropzone.isDragActive
                      ? 'border-primary-500 bg-primary-50 dark:bg-blue-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'
                  }`}
                >
                  <input {...scopeDropzone.getInputProps()} />
                  <Upload className="h-6 w-6 mx-auto mb-2 text-slate-400" />
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Drop scope docs or click
                  </p>
                  <p className="text-xs text-slate-500 mt-1">PDF, DOCX, TXT</p>
                </div>
                {projectScopeFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {projectScopeFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <File className="h-3 w-3 text-primary-600 flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                          <span className="text-slate-500">{formatFileSize(file.size)}</span>
                        </div>
                        <button
                          onClick={() => removeFile(projectScopeFiles, setProjectScopeFiles, idx)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 2. Sample Data Files */}
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                  2. Sample Data Files ({sampleDataFiles.length})
                </label>
                <div
                  {...sampleDataDropzone.getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                    sampleDataDropzone.isDragActive
                      ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-green-400'
                  }`}
                >
                  <input {...sampleDataDropzone.getInputProps()} />
                  <Upload className="h-6 w-6 mx-auto mb-2 text-slate-400" />
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Drop sample data or click
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Any format</p>
                </div>
                {sampleDataFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {sampleDataFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <File className="h-3 w-3 text-green-600 flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                          <span className="text-slate-500">{formatFileSize(file.size)}</span>
                        </div>
                        <button
                          onClick={() => removeFile(sampleDataFiles, setSampleDataFiles, idx)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 3. Reference BRD Templates */}
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                  3. Reference BRD Templates ({referenceBRDFiles.length})
                </label>
                <div
                  {...brdDropzone.getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                    brdDropzone.isDragActive
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-purple-400'
                  }`}
                >
                  <input {...brdDropzone.getInputProps()} />
                  <Upload className="h-6 w-6 mx-auto mb-2 text-slate-400" />
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Drop BRD templates or click
                  </p>
                  <p className="text-xs text-slate-500 mt-1">DOCX, PDF</p>
                </div>
                {referenceBRDFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {referenceBRDFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <File className="h-3 w-3 text-purple-600 flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                          <span className="text-slate-500">{formatFileSize(file.size)}</span>
                        </div>
                        <button
                          onClick={() => removeFile(referenceBRDFiles, setReferenceBRDFiles, idx)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 4. Historical Cost Templates */}
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                  4. Historical Cost Templates ({costTemplateFiles.length})
                </label>
                <div
                  {...costTemplatesDropzone.getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                    costTemplatesDropzone.isDragActive
                      ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-orange-400'
                  }`}
                >
                  <input {...costTemplatesDropzone.getInputProps()} />
                  <Upload className="h-6 w-6 mx-auto mb-2 text-slate-400" />
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Drop cost templates or click
                  </p>
                  <p className="text-xs text-slate-500 mt-1">XLSX, XLS, CSV</p>
                </div>
                {costTemplateFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {costTemplateFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <FileSpreadsheet className="h-3 w-3 text-orange-600 flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                          <span className="text-slate-500">{formatFileSize(file.size)}</span>
                        </div>
                        <button
                          onClick={() => removeFile(costTemplateFiles, setCostTemplateFiles, idx)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Total file count and size */}
            {(projectScopeFiles.length + sampleDataFiles.length + referenceBRDFiles.length + costTemplateFiles.length) > 0 && (
              <div className="mt-4 p-3 bg-primary-50 dark:bg-blue-900/20 rounded-lg border border-primary-200 dark:border-primary-800">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-primary-900 dark:text-primary-100">
                    Total: {projectScopeFiles.length + sampleDataFiles.length + referenceBRDFiles.length + costTemplateFiles.length} files
                  </span>
                  <span className="text-primary-700 dark:text-primary-300">
                    {formatFileSize(
                      getTotalFileSize(projectScopeFiles) +
                      getTotalFileSize(sampleDataFiles) +
                      getTotalFileSize(referenceBRDFiles) +
                      getTotalFileSize(costTemplateFiles)
                    )}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Project Scope Text Area */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Project Scope Description
            </label>
            <textarea
              value={projectScope}
              onChange={(e) => setProjectScope(e.target.value)}
              placeholder="Describe your project scope in detail. Include objectives, features, requirements, timeline, team size, technology stack, etc."
              className="w-full h-48 px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 resize-none"
            />
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              The more detailed your description, the more accurate the estimation will be
            </p>
          </div>

          {/* Project Type Selector */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Project Type (Determines scope and team composition)
            </label>
            <div className="grid grid-cols-3 gap-4">
              <button
                onClick={() => setProjectType('POC')}
                type="button"
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  projectType === 'POC'
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-purple-400'
                }`}
              >
                <div className="font-semibold text-slate-900 dark:text-white mb-1">
                  Proof of Concept
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Quick MVP (4-8 weeks)
                </p>
              </button>

              <button
                onClick={() => setProjectType('Staff Augmentation')}
                type="button"
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  projectType === 'Staff Augmentation'
                    ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-orange-400'
                }`}
              >
                <div className="font-semibold text-slate-900 dark:text-white mb-1">
                  Staff Augmentation
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Specific resources/skills
                </p>
              </button>

              <button
                onClick={() => setProjectType('Full Service')}
                type="button"
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  projectType === 'Full Service'
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-green-400'
                }`}
              >
                <div className="font-semibold text-slate-900 dark:text-white mb-1">
                  Full Service
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  End-to-end (8-16 weeks)
                </p>
              </button>
            </div>
          </div>

          {/* Scenario Selector */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Estimation Scenarios (All 3 will be generated for comparison)
            </label>
            <div className="grid grid-cols-3 gap-4">
              <button
                onClick={() => setActiveScenario('baseline')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  activeScenario === 'baseline'
                    ? 'border-primary-500 bg-primary-50 dark:bg-blue-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Minus className="h-5 w-5 text-primary-600 dark:text-blue-400" />
                  <span className="font-semibold text-slate-900 dark:text-white">Baseline</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Standard rates - Balanced approach
                </p>
              </button>

              <button
                onClick={() => setActiveScenario('conservative')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  activeScenario === 'conservative'
                    ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-red-400'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-red-600 dark:text-red-400" />
                  <span className="font-semibold text-slate-900 dark:text-white">Conservative</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Higher rates - Risk-averse
                </p>
              </button>

              <button
                onClick={() => setActiveScenario('aggressive')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  activeScenario === 'aggressive'
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-green-400'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <span className="font-semibold text-slate-900 dark:text-white">Aggressive</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Competitive rates - Optimistic
                </p>
              </button>
            </div>
          </div>

          {/* Configuration Section */}
          <div className="mb-6">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-blue-400 hover:underline"
            >
              <Settings className="h-4 w-4" />
              {showConfig ? 'Hide' : 'Show'} {getCurrentConfig().name} Configuration
            </button>

            {showConfig && (
              <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">
                  {getCurrentConfig().name} Scenario Settings
                </h3>

                {/* Billing Rates */}
                <div className="mb-6">
                  <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3">
                    Billing Rates ($/hour)
                  </h4>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { key: 'planning_rate', label: 'Planning', min: 15, max: 50 },
                      { key: 'development_rate', label: 'Development', min: 20, max: 60 },
                      { key: 'testing_rate', label: 'Testing', min: 15, max: 50 },
                      { key: 'ui_development_rate', label: 'UI Development', min: 15, max: 40 },
                      { key: 'solution_architect_rate', label: 'Solution Architect', min: 30, max: 80 },
                      { key: 'scraping_development_rate', label: 'Scraping Dev', min: 15, max: 40 }
                    ].map(({ key, label, min, max }) => (
                      <div key={key}>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          {label}: ${getCurrentConfig()[key as keyof ScenarioConfig]}/hr
                        </label>
                        <input
                          type="range"
                          min={min}
                          max={max}
                          value={getCurrentConfig()[key as keyof ScenarioConfig] as number}
                          onChange={(e) => updateCurrentConfig({ [key]: Number(e.target.value) })}
                          className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Overhead Percentages */}
                <div className="mb-6">
                  <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3">
                    Overhead Percentages (%)
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { key: 'solution_architect_percentage', label: 'Solution Architect', min: 5, max: 20 },
                      { key: 'project_manager_percentage', label: 'Project Manager', min: 3, max: 10 },
                      { key: 'business_analyst_percentage', label: 'Business Analyst', min: 3, max: 10 },
                      { key: 'contingency_percentage', label: 'Contingency', min: 5, max: 25 }
                    ].map(({ key, label, min, max }) => (
                      <div key={key}>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          {label}: {getCurrentConfig()[key as keyof ScenarioConfig]}%
                        </label>
                        <input
                          type="range"
                          min={min}
                          max={max}
                          value={getCurrentConfig()[key as keyof ScenarioConfig] as number}
                          onChange={(e) => updateCurrentConfig({ [key]: Number(e.target.value) })}
                          className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Testing Percentages */}
                <div className="mb-6">
                  <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3">
                    Testing Percentages (% of Dev Hours)
                  </h4>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { key: 'unit_testing_percentage', label: 'Unit Testing', min: 10, max: 30 },
                      { key: 'qa_testing_percentage', label: 'QA Testing', min: 15, max: 35 },
                      { key: 'integration_testing_percentage', label: 'Integration Testing', min: 10, max: 30 }
                    ].map(({ key, label, min, max }) => (
                      <div key={key}>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                          {label}: {getCurrentConfig()[key as keyof ScenarioConfig]}%
                        </label>
                        <input
                          type="range"
                          min={min}
                          max={max}
                          value={getCurrentConfig()[key as keyof ScenarioConfig] as number}
                          onChange={(e) => updateCurrentConfig({ [key]: Number(e.target.value) })}
                          className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Infrastructure Costs */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3">
                    Infrastructure Costs ($)
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        One-time: ${getCurrentConfig().one_time_infrastructure}
                      </label>
                      <input
                        type="range"
                        min={0}
                        max={1000}
                        step={10}
                        value={getCurrentConfig().one_time_infrastructure}
                        onChange={(e) => updateCurrentConfig({ one_time_infrastructure: Number(e.target.value) })}
                        className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Monthly BAU: ${getCurrentConfig().monthly_bau}
                      </label>
                      <input
                        type="range"
                        min={0}
                        max={3000}
                        step={50}
                        value={getCurrentConfig().monthly_bau}
                        onChange={(e) => updateCurrentConfig({ monthly_bau: Number(e.target.value) })}
                        className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerateEstimation}
            disabled={isGenerating || (!projectScope.trim() && !uploadedFile)}
            className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Generating All 3 Scenarios...
              </>
            ) : (
              <>
                <Calculator className="h-5 w-5" />
                Generate BRD & Cost Estimations (All Scenarios)
              </>
            )}
          </button>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}
        </div>

        {/* Results Section - Scenario Comparison */}
        {estimationResults.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md border border-slate-200 dark:border-slate-700 p-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
              Scenario Comparison
            </h2>

            {/* Comparison Table */}
            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-200 dark:border-slate-700">
                    <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Scenario</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Total Cost</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Total Hours</th>
                    <th className="text-center py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Documents</th>
                  </tr>
                </thead>
                <tbody>
                  {estimationResults.map((result) => (
                    <tr key={result.scenario} className="border-b border-slate-200 dark:border-slate-700">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {getScenarioIcon(result.scenario)}
                          <span className={`font-semibold ${getScenarioTextColor(result.scenario)} capitalize`}>
                            {result.scenario}
                          </span>
                        </div>
                      </td>
                      <td className="text-right py-3 px-4 font-mono font-bold text-slate-900 dark:text-white">
                        ${result.total_cost?.toLocaleString() || 'N/A'}
                      </td>
                      <td className="text-right py-3 px-4 font-mono text-slate-900 dark:text-white">
                        {result.total_effort_hours?.toLocaleString() || 'N/A'} hrs
                      </td>
                      <td className="text-center py-3 px-4">
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => handleDownload(
                              result.brd_url!,
                              `BRD_${result.scenario}_${result.project_name}.docx`
                            )}
                            disabled={!result.brd_url}
                            className={getScenarioButtonClasses(result.scenario, !result.brd_url)}
                          >
                            BRD
                          </button>
                          <button
                            onClick={() => handleDownload(
                              result.excel_url!,
                              `Cost_${result.scenario}_${result.project_name}.xlsx`
                            )}
                            disabled={!result.excel_url}
                            className={getScenarioButtonClasses(result.scenario, !result.excel_url)}
                          >
                            Excel
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Cost Variance Analysis */}
            {estimationResults.length === 3 && (
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-primary-50 dark:bg-blue-900/20 rounded-lg border border-primary-200 dark:border-primary-800">
                  <p className="text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Baseline Estimate</p>
                  <p className="text-xl font-bold text-primary-900 dark:text-primary-100">
                    ${estimationResults.find(r => r.scenario === 'baseline')?.total_cost?.toLocaleString()}
                  </p>
                  <p className="text-xs text-primary-600 dark:text-blue-400 mt-1">Reference standard</p>
                </div>

                <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                  <p className="text-xs font-medium text-red-700 dark:text-red-300 mb-1">Conservative Range</p>
                  <p className="text-xl font-bold text-red-900 dark:text-red-100">
                    ${estimationResults.find(r => r.scenario === 'conservative')?.total_cost?.toLocaleString()}
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    +{Math.round(((estimationResults.find(r => r.scenario === 'conservative')?.total_cost || 0) /
                      (estimationResults.find(r => r.scenario === 'baseline')?.total_cost || 1) - 1) * 100)}% buffer
                  </p>
                </div>

                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <p className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">Aggressive Estimate</p>
                  <p className="text-xl font-bold text-green-900 dark:text-green-100">
                    ${estimationResults.find(r => r.scenario === 'aggressive')?.total_cost?.toLocaleString()}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    {Math.round(((estimationResults.find(r => r.scenario === 'aggressive')?.total_cost || 0) /
                      (estimationResults.find(r => r.scenario === 'baseline')?.total_cost || 1) - 1) * 100)}% savings
                  </p>
                </div>
              </div>
            )}

            <p className="mt-4 text-xs text-slate-500 dark:text-slate-400 text-center">
              Generated on {new Date(estimationResults[0].generated_at).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
