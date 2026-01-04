import { useState } from 'react'
import axios from 'axios'
import { Building2, TrendingUp, AlertCircle, Award, Clock, DollarSign, Star , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import FileUpload from '../../FileUpload'

// Types matching backend schemas
type VendorCategory =
  | 'it_hardware'
  | 'it_software'
  | 'it_services'
  | 'office_supplies'
  | 'facilities'
  | 'professional_services'
  | 'marketing'
  | 'manufacturing'
  | 'logistics'
  | 'construction'
  | 'consulting'
  | 'telecommunications'

type EvaluationCriteria =
  | 'cost'
  | 'quality'
  | 'delivery_time'
  | 'reliability'
  | 'location'
  | 'certifications'
  | 'sustainability'
  | 'payment_terms'
  | 'customer_service'
  | 'innovation'

interface SelectionCriteria {
  criteria: EvaluationCriteria
  weight: number
}

interface VendorRecommendationRequest {
  category: VendorCategory
  requirement_description: string
  selection_criteria?: SelectionCriteria[]
  budget_range_max?: number
  required_delivery_days?: number
  required_certifications?: string[]
  minimum_quality_rating?: number
  exclude_vendor_ids?: string[]
  top_n?: number
  session_id?: string
  project_id?: string
}

interface VendorPerformance {
  vendor_id: string
  vendor_name: string
  quality_rating?: number
  avg_delivery_days?: number
  certifications?: string[]
}

interface VendorRecommendation {
  recommendation_id: string
  vendor_id: string
  vendor_name: string
  category: VendorCategory
  total_score: number
  rank: number
  recommendation_reason: string
  key_strengths: string[]
  potential_risks: string[]
  estimated_cost?: number
  estimated_delivery_days?: number
  confidence_level: number
  performance_metrics: VendorPerformance
}

interface VendorRecommendationResponse {
  category: VendorCategory
  requirement_description: string
  total_vendors_evaluated: number
  recommendations: VendorRecommendation[]
  selection_criteria_used: SelectionCriteria[]
  processing_time_seconds: number
  tier_1_services_used: string[]
}

const CATEGORIES: { value: VendorCategory; label: string }[] = [
  { value: 'it_hardware', label: 'IT Hardware' },
  { value: 'it_software', label: 'IT Software' },
  { value: 'it_services', label: 'IT Services' },
  { value: 'office_supplies', label: 'Office Supplies' },
  { value: 'facilities', label: 'Facilities' },
  { value: 'professional_services', label: 'Professional Services' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'logistics', label: 'Logistics' },
  { value: 'construction', label: 'Construction' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'telecommunications', label: 'Telecommunications' },
]

const CRITERIA_OPTIONS: { value: EvaluationCriteria; label: string }[] = [
  { value: 'cost', label: 'Cost' },
  { value: 'quality', label: 'Quality' },
  { value: 'delivery_time', label: 'Delivery Time' },
  { value: 'reliability', label: 'Reliability' },
  { value: 'certifications', label: 'Certifications' },
  { value: 'sustainability', label: 'Sustainability' },
  { value: 'customer_service', label: 'Customer Service' },
  { value: 'innovation', label: 'Innovation' },
]

export default function VendorRecommendationPanel() {
  const [category, setCategory] = useState<VendorCategory>('it_hardware')
  const [showConfig, setShowConfig] = useState(false)
  const [requirement, setRequirement] = useState<string>('')
  const [budgetMax, setBudgetMax] = useState<number>(200)
  const [deliveryDays, setDeliveryDays] = useState<number>(14)
  const [minQuality, setMinQuality] = useState<number>(4.0)
  const [topN, setTopN] = useState<number>(5)
  const [selectedCriteria, setSelectedCriteria] = useState<SelectionCriteria[]>([
    { criteria: 'cost', weight: 0.3 },
    { criteria: 'quality', weight: 0.3 },
    { criteria: 'delivery_time', weight: 0.2 },
    { criteria: 'certifications', weight: 0.2 },
  ])

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<VendorRecommendationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const handleCriteriaWeightChange = (criteria: EvaluationCriteria, weight: number) => {
    setSelectedCriteria(prev =>
      prev.map(c => c.criteria === criteria ? { ...c, weight } : c)
    )
  }

  const handleRecommend = async () => {
    if (!requirement.trim()) {
      setError('Please provide a requirement description')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const requestData: VendorRecommendationRequest = {
      category,
      requirement_description: requirement,
      selection_criteria: selectedCriteria,
      budget_range_max: budgetMax,
      required_delivery_days: deliveryDays,
      minimum_quality_rating: minQuality,
      top_n: topN,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<VendorRecommendationResponse>(
        'http://localhost:8000/api/v1/modules/vendor-recommendation/recommend',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Vendor recommendation failed')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-orange-600 bg-orange-50'
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-orange-600'
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Building2 className="w-8 h-8 text-blue-600" />
          Vendor Recommendation
        </h1>
        <p className="text-gray-600 mt-2">
          Get AI-powered vendor recommendations based on your procurement requirements and weighted criteria
        </p>
      </div>
          </div>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Configure
          </button>
        </div>

        {/* Configuration Panel */}
        {showConfig && (
          <div className="mb-6">
            <POCConfigManager
              moduleName="vendor_recommendation"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Document Upload Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          🏢 Upload Vendor Data
        </h3>
        <p className="text-sm text-slate-600 mb-4">
          Upload vendor profiles, capability statements, performance reports, or RFP responses for evaluation.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'procurement',
            usecase: 'vendor_recommendation'
          }}
        />
      </div>

      {/* Configuration Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6 space-y-6">
        <h2 className="text-xl font-semibold">Procurement Requirements</h2>

        {/* Category Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Vendor Category
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as VendorCategory)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {CATEGORIES.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>

        {/* Requirement Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Requirement Description
          </label>
          <textarea
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
            placeholder="e.g., Need 100 laptops for new office with warranty and support"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Constraints */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Budget (per unit)
            </label>
            <input
              type="number"
              value={budgetMax}
              onChange={(e) => setBudgetMax(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Required Delivery (days)
            </label>
            <input
              type="number"
              value={deliveryDays}
              onChange={(e) => setDeliveryDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Quality Rating
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="5"
              value={minQuality}
              onChange={(e) => setMinQuality(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Top N Vendors
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Selection Criteria Weights */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Evaluation Criteria Weights (Total: {selectedCriteria.reduce((sum, c) => sum + c.weight, 0).toFixed(1)})
          </label>
          <div className="grid md:grid-cols-2 gap-4">
            {selectedCriteria.map(criterion => (
              <div key={criterion.criteria} className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700 w-32">
                  {CRITERIA_OPTIONS.find(c => c.value === criterion.criteria)?.label}:
                </span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={criterion.weight}
                  onChange={(e) => handleCriteriaWeightChange(criterion.criteria, Number(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm font-semibold text-gray-900 w-12">
                  {(criterion.weight * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recommend Button */}
        <button
          onClick={handleRecommend}
          disabled={loading || !requirement.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Finding Best Vendors...
            </>
          ) : (
            <>
              <TrendingUp className="w-5 h-5" />
              Get Vendor Recommendations
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Error</p>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Recommendation Summary</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Vendors Evaluated</p>
                <p className="text-3xl font-bold text-blue-900">{result.total_vendors_evaluated}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">Top Recommendations</p>
                <p className="text-3xl font-bold text-green-900">{result.recommendations.length}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Processing Time</p>
                <p className="text-3xl font-bold text-gray-900">{result.processing_time_seconds.toFixed(1)}s</p>
              </div>
            </div>
          </div>

          {/* Vendor Recommendations */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Top {result.recommendations.length} Vendors</h3>
            {result.recommendations.map((vendor) => (
              <div key={vendor.recommendation_id} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                {/* Vendor Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-3 py-1 bg-blue-600 text-white rounded-full text-sm font-bold">
                        #{vendor.rank}
                      </span>
                      <h4 className="text-xl font-bold text-gray-900">{vendor.vendor_name}</h4>
                    </div>
                    <p className="text-gray-600 italic">{vendor.recommendation_reason}</p>
                  </div>
                  <div className="text-right ml-4">
                    <div className={`text-3xl font-bold px-4 py-2 rounded-lg ${getScoreColor(vendor.total_score)}`}>
                      {vendor.total_score.toFixed(1)}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Score</p>
                  </div>
                </div>

                {/* Vendor Details Grid */}
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                  {vendor.estimated_cost && (
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-green-600" />
                      <div>
                        <p className="text-xs text-gray-500">Est. Cost/Unit</p>
                        <p className="font-semibold">${vendor.estimated_cost}</p>
                      </div>
                    </div>
                  )}

                  {vendor.estimated_delivery_days && (
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-600" />
                      <div>
                        <p className="text-xs text-gray-500">Delivery</p>
                        <p className="font-semibold">{vendor.estimated_delivery_days} days</p>
                      </div>
                    </div>
                  )}

                  {vendor.performance_metrics.quality_rating && (
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-yellow-600" />
                      <div>
                        <p className="text-xs text-gray-500">Quality</p>
                        <p className="font-semibold">{vendor.performance_metrics.quality_rating.toFixed(1)}/5.0</p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <Award className="w-4 h-4 text-purple-600" />
                    <div>
                      <p className="text-xs text-gray-500">Confidence</p>
                      <p className={`font-semibold ${getConfidenceColor(vendor.confidence_level)}`}>
                        {(vendor.confidence_level * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Strengths and Risks */}
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Strengths */}
                  {vendor.key_strengths.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-green-700 mb-2">Key Strengths</p>
                      <ul className="space-y-1">
                        {vendor.key_strengths.map((strength, idx) => (
                          <li key={idx} className="text-sm text-green-600 flex items-start gap-2">
                            <span className="text-green-400">✓</span>
                            <span>{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Risks */}
                  {vendor.potential_risks.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-orange-700 mb-2">Potential Risks</p>
                      <ul className="space-y-1">
                        {vendor.potential_risks.map((risk, idx) => (
                          <li key={idx} className="text-sm text-orange-600 flex items-start gap-2">
                            <span className="text-orange-400">⚠</span>
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Certifications */}
                {vendor.performance_metrics.certifications && vendor.performance_metrics.certifications.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm font-semibold text-gray-700 mb-2">Certifications</p>
                    <div className="flex flex-wrap gap-2">
                      {vendor.performance_metrics.certifications.map((cert, idx) => (
                        <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                          {cert}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Tech Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Category:</strong> {result.category.replace('_', ' ').toUpperCase()}</p>
            <p><strong>Requirement:</strong> {result.requirement_description}</p>
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  )
}
