import { useState } from 'react'
import axios from 'axios'
import { Activity, Plus, X, TrendingUp, AlertTriangle, CheckCircle, Users , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'

// Types matching backend schemas
type EngagementLevel = 'very_low' | 'low' | 'moderate' | 'high' | 'very_high'
type RiskLevel = 'low' | 'moderate' | 'high' | 'critical'
type FeedbackCategory = 'compensation' | 'work_life_balance' | 'career_growth' | 'management' | 'culture' | 'benefits' | 'workload' | 'recognition' | 'other'

interface EmployeeFeedback {
  employee_id: string
  feedback_text: string
  department?: string
  role?: string
  tenure_months?: number
  engagement_score?: number
}

interface SentimentScore {
  positive: number
  neutral: number
  negative: number
}

interface SentimentAnalysis {
  overall_sentiment: 'positive' | 'neutral' | 'negative' | 'mixed'
  sentiment_score: SentimentScore
  confidence: number
  key_themes: string[]
}

interface EngagementMetrics {
  engagement_score: number
  engagement_level: EngagementLevel
  participation_rate: number
  response_quality_score: number
}

interface AttritionRisk {
  employee_id: string
  risk_level: RiskLevel
  risk_score: number
  risk_factors: string[]
  recommendations: string[]
}

interface TalentPulseRequest {
  feedback_data: EmployeeFeedback[]
  analyze_sentiment?: boolean
  calculate_engagement?: boolean
  assess_attrition_risk?: boolean
  session_id?: string
}

interface TalentPulseResponse {
  overall_sentiment?: SentimentAnalysis
  engagement_metrics?: EngagementMetrics
  department_breakdown: Record<string, any>
  category_insights: Record<string, any>
  attrition_risks: AttritionRisk[]
  trends: any[]
  key_insights: string[]
  action_items: string[]
  total_feedback_analyzed: number
}

const ENGAGEMENT_COLORS: Record<EngagementLevel, { bg: string; text: string }> = {
  very_low: { bg: 'bg-red-50', text: 'text-red-800' },
  low: { bg: 'bg-orange-50', text: 'text-orange-800' },
  moderate: { bg: 'bg-yellow-50', text: 'text-yellow-800' },
  high: { bg: 'bg-green-50', text: 'text-green-800' },
  very_high: { bg: 'bg-emerald-50', text: 'text-emerald-800' },
}

const RISK_COLORS: Record<RiskLevel, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-500' },
  moderate: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-500' },
  high: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-500' },
  critical: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-500' },
}

export default function TalentPulsePanel() {
  const [feedbackItems, setFeedbackItems] = useState<EmployeeFeedback[]>([
    { employee_id: '', feedback_text: '', department: '' }
  ])
  const [showConfig, setShowConfig] = useState(false)
  const [analyzeSentiment, setAnalyzeSentiment] = useState(true)
  const [calculateEngagement, setCalculateEngagement] = useState(true)
  const [assessRisk, setAssessRisk] = useState(true)

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TalentPulseResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const addFeedbackItem = () => {
    setFeedbackItems([...feedbackItems, { employee_id: '', feedback_text: '', department: '' }])
  }

  const removeFeedbackItem = (index: number) => {
    setFeedbackItems(feedbackItems.filter((_, i) => i !== index))
  }

  const updateFeedbackItem = (index: number, field: keyof EmployeeFeedback, value: any) => {
    const updated = [...feedbackItems]
    updated[index] = { ...updated[index], [field]: value }
    setFeedbackItems(updated)
  }

  const handleAnalyze = async () => {
    const validFeedback = feedbackItems.filter(item =>
      item.employee_id.trim() && item.feedback_text.trim()
    )

    if (validFeedback.length === 0) {
      setError('Please enter at least one feedback item with employee ID and feedback text')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const requestData: TalentPulseRequest = {
      feedback_data: validFeedback,
      analyze_sentiment: analyzeSentiment,
      calculate_engagement: calculateEngagement,
      assess_attrition_risk: assessRisk,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<TalentPulseResponse>(
        'http://localhost:8000/api/v1/modules/talent-pulse/analyze',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Talent pulse analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Activity className="w-8 h-8 text-purple-600" />
          Talent Pulse - Employee Engagement Analytics
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze employee sentiment, engagement, and attrition risk from feedback data
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
              moduleName="talent_pulse"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Feedback Input Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6 space-y-6">
        <h2 className="text-xl font-semibold">Employee Feedback Data</h2>

        <div className="space-y-4">
          {feedbackItems.map((item, index) => (
            <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex justify-between items-start mb-3">
                <p className="text-sm font-semibold text-gray-700">Feedback Item {index + 1}</p>
                {feedbackItems.length > 1 && (
                  <button
                    onClick={() => removeFeedbackItem(index)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Employee ID</label>
                  <input
                    type="text"
                    value={item.employee_id}
                    onChange={(e) => updateFeedbackItem(index, 'employee_id', e.target.value)}
                    placeholder="e.g., emp-123"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Department (Optional)</label>
                  <input
                    type="text"
                    value={item.department || ''}
                    onChange={(e) => updateFeedbackItem(index, 'department', e.target.value)}
                    placeholder="e.g., Engineering, Sales"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-gray-600 mb-1">Feedback Text</label>
                <textarea
                  value={item.feedback_text}
                  onChange={(e) => updateFeedbackItem(index, 'feedback_text', e.target.value)}
                  placeholder="Enter employee feedback, survey response, or comment..."
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={addFeedbackItem}
          className="flex items-center gap-2 px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          Add Another Feedback Item
        </button>

        {/* Analysis Options */}
        <div className="border-t pt-4 space-y-2">
          <p className="text-sm font-semibold text-gray-700 mb-3">Analysis Options</p>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={analyzeSentiment}
              onChange={(e) => setAnalyzeSentiment(e.target.checked)}
              className="rounded text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-700">Analyze sentiment (positive/neutral/negative)</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={calculateEngagement}
              onChange={(e) => setCalculateEngagement(e.target.checked)}
              className="rounded text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-700">Calculate engagement metrics</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={assessRisk}
              onChange={(e) => setAssessRisk(e.target.checked)}
              className="rounded text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-700">Assess attrition risk</span>
          </label>
        </div>

        {/* Analyze Button */}
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Analyzing Talent Pulse...
            </>
          ) : (
            <>
              <Activity className="w-5 h-5" />
              Analyze Talent Pulse
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="font-medium text-red-900">Error</p>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Overall Metrics */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Overall Metrics</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Engagement */}
              {result.engagement_metrics && (
                <div className={`p-4 rounded-lg ${ENGAGEMENT_COLORS[result.engagement_metrics.engagement_level].bg}`}>
                  <p className="text-sm font-medium mb-1">Engagement Level</p>
                  <p className={`text-2xl font-bold ${ENGAGEMENT_COLORS[result.engagement_metrics.engagement_level].text}`}>
                    {result.engagement_metrics.engagement_level.replace('_', ' ').toUpperCase()}
                  </p>
                  <p className="text-sm mt-1">Score: {result.engagement_metrics.engagement_score.toFixed(0)}/100</p>
                </div>
              )}

              {/* Sentiment */}
              {result.overall_sentiment && (
                <div className={`p-4 rounded-lg ${
                  result.overall_sentiment.overall_sentiment === 'positive' ? 'bg-green-50' :
                  result.overall_sentiment.overall_sentiment === 'negative' ? 'bg-red-50' :
                  'bg-gray-50'
                }`}>
                  <p className="text-sm font-medium mb-1">Overall Sentiment</p>
                  <p className={`text-2xl font-bold ${
                    result.overall_sentiment.overall_sentiment === 'positive' ? 'text-green-800' :
                    result.overall_sentiment.overall_sentiment === 'negative' ? 'text-red-800' :
                    'text-gray-800'
                  }`}>
                    {result.overall_sentiment.overall_sentiment.toUpperCase()}
                  </p>
                  <p className="text-sm mt-1">Confidence: {(result.overall_sentiment.confidence * 100).toFixed(0)}%</p>
                </div>
              )}

              {/* Feedback Analyzed */}
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600 font-medium mb-1">Feedback Analyzed</p>
                <p className="text-2xl font-bold text-blue-900">{result.total_feedback_analyzed}</p>
                <p className="text-sm text-blue-700 mt-1">Employee responses</p>
              </div>
            </div>
          </div>

          {/* Sentiment Breakdown */}
          {result.overall_sentiment && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Sentiment Distribution</h3>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-700 mb-1">Positive</p>
                  <p className="text-3xl font-bold text-green-900">
                    {(result.overall_sentiment.sentiment_score.positive * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-700 mb-1">Neutral</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {(result.overall_sentiment.sentiment_score.neutral * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg">
                  <p className="text-sm text-red-700 mb-1">Negative</p>
                  <p className="text-3xl font-bold text-red-900">
                    {(result.overall_sentiment.sentiment_score.negative * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {result.overall_sentiment.key_themes && result.overall_sentiment.key_themes.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Key Themes</p>
                  <div className="flex flex-wrap gap-2">
                    {result.overall_sentiment.key_themes.map((theme, idx) => (
                      <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Attrition Risks */}
          {result.attrition_risks && result.attrition_risks.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                Attrition Risk Alerts ({result.attrition_risks.length})
              </h3>
              <div className="space-y-3">
                {result.attrition_risks.map((risk, idx) => {
                  const riskColors = RISK_COLORS[risk.risk_level]
                  return (
                    <div key={idx} className={`p-4 rounded-lg border-l-4 ${riskColors.border} ${riskColors.bg}`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold text-gray-900">Employee: {risk.employee_id}</p>
                          <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-bold ${riskColors.text}`}>
                            {risk.risk_level.toUpperCase()} RISK
                          </span>
                        </div>
                        <p className="text-2xl font-bold text-gray-900">{risk.risk_score.toFixed(0)}%</p>
                      </div>

                      {risk.risk_factors.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Risk Factors:</p>
                          <ul className="space-y-1">
                            {risk.risk_factors.map((factor, i) => (
                              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                <span className="text-orange-500">•</span>
                                <span>{factor}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {risk.recommendations.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Recommendations:</p>
                          <ul className="space-y-1">
                            {risk.recommendations.map((rec, i) => (
                              <li key={i} className="text-sm text-green-700 flex items-start gap-2">
                                <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                <span>{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Key Insights */}
          {result.key_insights && result.key_insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Key Insights
              </h3>
              <ul className="space-y-2">
                {result.key_insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <span className="text-blue-600 font-bold">{idx + 1}.</span>
                    <span className="text-gray-900">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {result.action_items && result.action_items.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Recommended Actions
              </h3>
              <ul className="space-y-2">
                {result.action_items.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-900">{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
