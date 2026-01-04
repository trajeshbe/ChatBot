import { useState, useRef } from 'react'
import { Upload, Loader2, CheckCircle, XCircle, FileText, DollarSign, TrendingUp, Download, Settings } from 'lucide-react'
import axios from 'axios'
import POCConfigManager from './POCConfigManager'
import FileUpload from './FileUpload'
import ExportWizardButton from './ExportWizardButton'

interface ExtractedDatapoint {
  field_name: string
  value: number | string
  page_no: number
  reference_notes: string
  extraction_status: string
}

interface SubCalculation {
  sub_field_name: string
  calculated_value: number | null
  calculation_status: string
}

interface FinancialRatios {
  // Liquidity Ratios
  current_ratio?: number
  quick_ratio?: number
  cash_ratio?: number

  // Leverage Ratios
  debt_to_equity?: number
  debt_ratio?: number
  equity_ratio?: number
  interest_coverage?: number

  // Profitability Ratios
  return_on_equity?: number
  return_on_assets?: number
  profit_margin?: number
  ebitda_margin?: number
  net_profit_margin?: number

  // Efficiency Ratios
  asset_turnover?: number
  inventory_turnover?: number
  receivables_turnover?: number
  days_sales_outstanding?: number
  days_inventory_outstanding?: number
  days_payable_outstanding?: number
  cash_conversion_cycle?: number
}

interface ExtractionResult {
  md5_hash: string
  status: string
  company_name: string | null
  total_datapoints: number
  datapoints_extracted: number
  progress_percentage: number
  extracted_datapoints: ExtractedDatapoint[]
  sub_calculations: SubCalculation[]
  financial_ratios: FinancialRatios
  excel_output_path: string | null
  processing_time_seconds: number | null
}

export default function GrantThorntonExtraction() {
  const [isExtracting, setIsExtracting] = useState(false)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [currentStage, setCurrentStage] = useState<string>('')
  const [companyName, setCompanyName] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [activeTab, setActiveTab] = useState<'datapoints' | 'calculations' | 'ratios'>('datapoints')
  const [showConfig, setShowConfig] = useState(false)

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file (annual report)')
      return
    }

    setIsExtracting(true)
    setError(null)
    setResult(null)
    setProgress(0)
    setCurrentStage('Uploading PDF...')

    const formData = new FormData()
    formData.append('pdf_file', file)
    formData.append('session_id', sessionStorage.getItem('chat_session_id') || 'default')
    if (companyName.trim()) {
      formData.append('company_name', companyName.trim())
    }

    try {
      const response = await axios.post<ExtractionResult>(
        'http://localhost:8000/api/v1/grant-thornton/extract',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0
            setProgress(percentCompleted)
          }
        }
      )

      setResult(response.data)
      setProgress(100)
      setCurrentStage('Complete!')
    } catch (err: any) {
      console.error('Extraction error:', err)
      setError(err.response?.data?.detail || 'Failed to extract financial data')
    } finally {
      setIsExtracting(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const downloadExcel = async () => {
    if (!result?.excel_output_path) return

    try {
      const response = await axios.get(
        `http://localhost:8000/api/v1/grant-thornton/download/${result.md5_hash}`,
        { responseType: 'blob' }
      )

      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = `grant_thornton_${result.company_name || 'report'}.xlsx`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download error:', err)
      setError('Failed to download Excel file')
    }
  }

  const DatapointCard = ({ datapoint }: { datapoint: ExtractedDatapoint }) => {
    const isSuccess = datapoint.extraction_status === 'success'
    return (
      <div className={`p-4 rounded-lg border ${isSuccess ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
        <div className="flex items-start justify-between mb-2">
          <div className="text-sm font-semibold text-slate-700">{datapoint.field_name}</div>
          {isSuccess ? (
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : (
            <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          )}
        </div>
        <div className={`text-2xl font-bold mb-1 ${isSuccess ? 'text-emerald-700' : 'text-red-700'}`}>
          {isSuccess ? datapoint.value : 'N/A'}
        </div>
        <div className="text-xs text-slate-600">
          Page {datapoint.page_no} • {datapoint.reference_notes}
        </div>
      </div>
    )
  }

  const RatioCard = ({ category, ratios }: { category: string; ratios: Array<{name: string; value?: number}> }) => {
    return (
      <div className="p-4 bg-white border border-slate-200 rounded-lg">
        <div className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide">
          {category}
        </div>
        <div className="space-y-2">
          {ratios.map((ratio, idx) => (
            <div key={idx} className="flex items-center justify-between">
              <span className="text-sm text-slate-600">{ratio.name}</span>
              <span className={`text-sm font-semibold ${ratio.value != null ? 'text-blue-700' : 'text-slate-400'}`}>
                {ratio.value != null ? ratio.value.toFixed(2) : 'N/A'}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white">
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-start justify-between mb-4">
              <div className="text-center flex-1">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
                  <DollarSign className="w-8 h-8 text-blue-600" />
                </div>
                <h1 className="text-3xl font-bold text-slate-900 mb-2">
                  Grant Thornton Financial Analysis
                </h1>
                <p className="text-slate-600">
                  Upload an annual report PDF to automatically extract 50+ financial datapoints, calculate ratios, and generate Excel reports
                </p>
              </div>
              <div className="flex gap-2">
                <ExportWizardButton
                  moduleCode="grant_thornton"
                  moduleName="Grant Thornton Financial Analysis"
                  tier={3}
                  customerName="Grant Thornton"
                  customerEmail="export@grantthornton.com"
                  variant="button"
                  size="md"
                />
                <button
                  onClick={() => setShowConfig(!showConfig)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Settings className="w-4 h-4" />
                  Configure
                </button>
              </div>
            </div>

            {/* Configuration Panel */}
            {showConfig && (
              <div className="mb-6">
                <POCConfigManager
                  moduleName="grant_thornton"
                  onClose={() => setShowConfig(false)}
                />
              </div>
            )}

            {/* Supporting Documents Upload */}
            <div className="mb-6 max-w-4xl mx-auto">
              <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800 mb-2">
                  📊 Upload Supporting Documents (Optional)
                </h3>
                <p className="text-sm text-slate-600 mb-4">
                  Upload industry benchmarks, credit ratings, or reference materials for enhanced analysis.
                </p>
                <FileUpload
                  hideProjectSelector={true}
                  compact={true}
                  metadata={{
                    company: 'grant_thornton',
                    usecase: 'financial_analysis'
                  }}
                />
              </div>
            </div>
          </div>

          {/* Company Name Input */}
          <div className="mb-6 max-w-2xl mx-auto">
            <label htmlFor="companyName" className="block text-sm font-medium text-slate-700 mb-2">
              Company Name (Optional)
            </label>
            <input
              type="text"
              id="companyName"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., ACME Corporation"
              disabled={isExtracting}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-slate-500">
              Used for organizing PDFs in storage. If not provided, filename will be used.
            </p>
          </div>

          {/* Upload Button */}
          <div className="mb-8">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
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
                  <span className="text-blue-700 font-medium">{currentStage}</span>
                  <div className="w-64 bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </>
              ) : (
                <>
                  <FileText className="w-12 h-12 text-blue-600" />
                  <span className="text-blue-700 font-medium">Click to upload Annual Report PDF</span>
                  <span className="text-sm text-slate-500">Financial statements, balance sheet, income statement</span>
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
                    <div className="font-semibold text-emerald-900">{result.company_name || 'Financial Report'}</div>
                    <div className="text-sm text-emerald-700">
                      {result.datapoints_extracted}/{result.total_datapoints} datapoints extracted •
                      Success rate: {((result.datapoints_extracted / result.total_datapoints) * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
                <div className="text-sm text-emerald-700">
                  {result.processing_time_seconds?.toFixed(1)}s
                </div>
              </div>

              {/* Download Excel Button */}
              {result.excel_output_path && (
                <button
                  onClick={downloadExcel}
                  className="w-full py-3 px-4 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium flex items-center justify-center gap-2"
                >
                  <Download className="w-5 h-5" />
                  Download Complete Excel Report
                </button>
              )}

              {/* Tabs */}
              <div className="flex gap-2 border-b border-slate-200">
                <button
                  onClick={() => setActiveTab('datapoints')}
                  className={`px-4 py-2 font-medium transition-colors ${
                    activeTab === 'datapoints'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Extracted Datapoints ({result.extracted_datapoints.length})
                </button>
                <button
                  onClick={() => setActiveTab('calculations')}
                  className={`px-4 py-2 font-medium transition-colors ${
                    activeTab === 'calculations'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Sub-Calculations ({result.sub_calculations.length})
                </button>
                <button
                  onClick={() => setActiveTab('ratios')}
                  className={`px-4 py-2 font-medium transition-colors ${
                    activeTab === 'ratios'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Financial Ratios
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'datapoints' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {result.extracted_datapoints.map((datapoint, idx) => (
                    <DatapointCard key={idx} datapoint={datapoint} />
                  ))}
                </div>
              )}

              {activeTab === 'calculations' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.sub_calculations.map((calc, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border ${
                      calc.calculation_status === 'success'
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-slate-50 border-slate-200'
                    }`}>
                      <div className="text-sm font-semibold text-slate-700 mb-2">
                        {calc.sub_field_name}
                      </div>
                      <div className={`text-2xl font-bold ${
                        calc.calculation_status === 'success'
                          ? 'text-blue-700'
                          : 'text-slate-400'
                      }`}>
                        {calc.calculated_value !== null ? calc.calculated_value.toFixed(2) : 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'ratios' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <RatioCard
                    category="Liquidity Ratios"
                    ratios={[
                      { name: 'Current Ratio', value: result.financial_ratios.current_ratio },
                      { name: 'Quick Ratio', value: result.financial_ratios.quick_ratio },
                      { name: 'Cash Ratio', value: result.financial_ratios.cash_ratio },
                    ]}
                  />
                  <RatioCard
                    category="Leverage Ratios"
                    ratios={[
                      { name: 'Debt to Equity', value: result.financial_ratios.debt_to_equity },
                      { name: 'Debt Ratio', value: result.financial_ratios.debt_ratio },
                      { name: 'Equity Ratio', value: result.financial_ratios.equity_ratio },
                      { name: 'Interest Coverage', value: result.financial_ratios.interest_coverage },
                    ]}
                  />
                  <RatioCard
                    category="Profitability Ratios"
                    ratios={[
                      { name: 'Return on Equity (ROE)', value: result.financial_ratios.return_on_equity },
                      { name: 'Return on Assets (ROA)', value: result.financial_ratios.return_on_assets },
                      { name: 'Profit Margin', value: result.financial_ratios.profit_margin },
                      { name: 'EBITDA Margin', value: result.financial_ratios.ebitda_margin },
                      { name: 'Net Profit Margin', value: result.financial_ratios.net_profit_margin },
                    ]}
                  />
                  <RatioCard
                    category="Efficiency Ratios"
                    ratios={[
                      { name: 'Asset Turnover', value: result.financial_ratios.asset_turnover },
                      { name: 'Inventory Turnover', value: result.financial_ratios.inventory_turnover },
                      { name: 'Receivables Turnover', value: result.financial_ratios.receivables_turnover },
                      { name: 'Days Sales Outstanding (DSO)', value: result.financial_ratios.days_sales_outstanding },
                      { name: 'Days Inventory Outstanding (DIO)', value: result.financial_ratios.days_inventory_outstanding },
                      { name: 'Days Payable Outstanding (DPO)', value: result.financial_ratios.days_payable_outstanding },
                      { name: 'Cash Conversion Cycle', value: result.financial_ratios.cash_conversion_cycle },
                    ]}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
