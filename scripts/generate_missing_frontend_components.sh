#!/bin/bash
###############################################################################
# Generate Missing Frontend Components for Tier 2 Domain Verticals
#
# This script creates all missing React/TypeScript components based on
# existing patterns.
###############################################################################

set -e

COMPONENTS_DIR="/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/frontend/src/components/tier2"

echo "🚀 Generating missing frontend components..."
echo ""

# Function to create a component file
create_component() {
    local path=$1
    local component_name=$2
    local module_id=$3
    local title=$4
    local description=$5
    local icon=$6
    local color=$7

    mkdir -p "$(dirname "$path")"

    cat > "$path" << EOF
import { useState } from 'react'
import axios from 'axios'
import { ${icon}, Upload, AlertTriangle } from 'lucide-react'

interface ${component_name}Response {
  results: any
  insights: string[]
  recommendations?: string[]
}

export default function ${component_name}() {
  const [file, setFile] = useState<File | null>(null)
  const [textInput, setTextInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<${component_name}Response | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleSubmit = async () => {
    if (!file && !textInput.trim()) {
      setError('Please upload a file or enter text')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      if (file) {
        formData.append('file', file)
      }
      if (textInput.trim()) {
        formData.append('text', textInput)
      }

      const response = await axios.post<${component_name}Response>(
        'http://localhost:8000/api/v1/modules/${module_id}/analyze',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <${icon} className="w-8 h-8 text-${color}-600" />
          ${title}
        </h1>
        <p className="text-gray-600 mt-2">${description}</p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Upload Data or Enter Text</h2>

        {/* File Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-${color}-400 transition-colors mb-4">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label className="cursor-pointer">
            <span className="text-${color}-600 hover:text-${color}-700 font-medium">
              Click to upload
            </span>
            <span className="text-gray-600"> or drag and drop</span>
            <input
              type="file"
              accept=".csv,.pdf,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-500 mt-2">PDF, CSV, or TXT files</p>
        </div>

        {file && (
          <p className="mt-3 text-sm text-gray-700 mb-4">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        {/* Text Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Or enter text directly
          </label>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Enter your data or query here..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${color}-500"
          />
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={loading || (!file && !textInput.trim())}
          className="w-full bg-${color}-600 hover:bg-${color}-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Processing...
            </>
          ) : (
            <>
              <${icon} className="w-5 h-5" />
              Analyze
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">Error</p>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Results</h3>
            <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>

          {result.insights && result.insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Insights</h3>
              <ul className="space-y-2">
                {result.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-${color}-50 rounded-lg">
                    <span className="text-${color}-600 font-bold">{idx + 1}.</span>
                    <span className="text-gray-900">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.recommendations && result.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <span className="text-green-600 font-bold">✓</span>
                    <span className="text-gray-900">{rec}</span>
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
EOF

    echo "✅ Created: $component_name"
}

# Construction Components
echo "📐 Creating Construction components..."
create_component \
    "$COMPONENTS_DIR/construction/EstimatorAUPanel.tsx" \
    "EstimatorAUPanel" \
    "estimator-au" \
    "AU Cost Estimator" \
    "Australian construction cost estimation and forecasting" \
    "Calculator" \
    "blue"

create_component \
    "$COMPONENTS_DIR/construction/BuildingMetricsPanel.tsx" \
    "BuildingMetricsPanel" \
    "construction" \
    "Building Metrics" \
    "Construction project metrics extraction and analysis" \
    "Building" \
    "orange"

# Agriculture Component
echo "🌾 Creating Agriculture components..."
create_component \
    "$COMPONENTS_DIR/agriculture/AgronomyDecisionPanel.tsx" \
    "AgronomyDecisionPanel" \
    "agronomy-decision" \
    "Agronomy Decision Support" \
    "AI-powered agricultural decision support system" \
    "Leaf" \
    "green"

# Procurement Component
echo "📦 Creating Procurement components..."
create_component \
    "$COMPONENTS_DIR/procurement/SpendSmartPanel.tsx" \
    "SpendSmartPanel" \
    "spend-smart" \
    "Spend Analytics" \
    "Procurement spend analysis and optimization" \
    "PieChart" \
    "purple"

# Maritime Component
echo "🚢 Creating Maritime components..."
mkdir -p "$COMPONENTS_DIR/maritime"
create_component \
    "$COMPONENTS_DIR/maritime/MaritimeReportPanel.tsx" \
    "MaritimeReportPanel" \
    "maritime-logistics" \
    "Maritime Report Generation" \
    "Generate maritime logistics and shipping reports" \
    "Ship" \
    "blue"

# Marketing Components
echo "📢 Creating Marketing components..."
mkdir -p "$COMPONENTS_DIR/marketing"
create_component \
    "$COMPONENTS_DIR/marketing/CampaignOptimizerPanel.tsx" \
    "CampaignOptimizerPanel" \
    "campaign-optimizer" \
    "Campaign Optimizer" \
    "Optimize marketing campaigns with AI insights" \
    "Target" \
    "pink"

create_component \
    "$COMPONENTS_DIR/marketing/SentimentSocialPanel.tsx" \
    "SentimentSocialPanel" \
    "sentiment-social" \
    "Social Sentiment Analysis" \
    "Analyze social media sentiment and trends" \
    "MessageCircle" \
    "indigo"

# E-commerce Component
echo "🛒 Creating E-commerce components..."
mkdir -p "$COMPONENTS_DIR/ecommerce"
create_component \
    "$COMPONENTS_DIR/ecommerce/ProductRecommendationPanel.tsx" \
    "ProductRecommendationPanel" \
    "product-recommendation" \
    "Product Recommendations" \
    "AI-powered product recommendation engine" \
    "ShoppingCart" \
    "green"

# Industry Verticals Components
echo "🏢 Creating Industry Verticals components..."
mkdir -p "$COMPONENTS_DIR/industry_verticals"

create_component \
    "$COMPONENTS_DIR/industry_verticals/EducationalContentPanel.tsx" \
    "EducationalContentPanel" \
    "educational-content" \
    "Educational Content Generation" \
    "Generate educational content and learning materials" \
    "GraduationCap" \
    "blue"

create_component \
    "$COMPONENTS_DIR/industry_verticals/HealthcareDiagnosticsPanel.tsx" \
    "HealthcareDiagnosticsPanel" \
    "healthcare-diagnostics" \
    "Healthcare Diagnostics Support" \
    "AI-powered diagnostic assistance for healthcare" \
    "Heart" \
    "red"

create_component \
    "$COMPONENTS_DIR/industry_verticals/InsuranceRiskPanel.tsx" \
    "InsuranceRiskPanel" \
    "insurance-risk" \
    "Insurance Risk Assessment" \
    "Assess insurance risk and pricing" \
    "Shield" \
    "orange"

create_component \
    "$COMPONENTS_DIR/industry_verticals/LegalDocumentPanel.tsx" \
    "LegalDocumentPanel" \
    "legal-document" \
    "Legal Document Analysis" \
    "Analyze and extract insights from legal documents" \
    "Scale" \
    "purple"

create_component \
    "$COMPONENTS_DIR/industry_verticals/RealEstatePanel.tsx" \
    "RealEstatePanel" \
    "real-estate" \
    "Real Estate Analysis" \
    "Real estate valuation and market analysis" \
    "Home" \
    "green"

# Advanced Capabilities Components
echo "⚡ Creating Advanced Capabilities components..."
mkdir -p "$COMPONENTS_DIR/advanced_capabilities"

create_component \
    "$COMPONENTS_DIR/advanced_capabilities/CodeAnalysisPanel.tsx" \
    "CodeAnalysisPanel" \
    "code-analysis" \
    "Code Analysis" \
    "Analyze code quality, security, and performance" \
    "Code" \
    "blue"

create_component \
    "$COMPONENTS_DIR/advanced_capabilities/MultilingualTranslatorPanel.tsx" \
    "MultilingualTranslatorPanel" \
    "multilingual-translator" \
    "Multilingual Translation" \
    "Translate content across multiple languages" \
    "Languages" \
    "indigo"

echo ""
echo "✨ Component generation complete!"
echo ""
echo "📊 Summary:"
echo "  - Construction: 2 components"
echo "  - Agriculture: 1 component"
echo "  - Procurement: 1 component"
echo "  - Maritime: 1 component"
echo "  - Marketing: 2 components"
echo "  - E-commerce: 1 component"
echo "  - Industry Verticals: 5 components"
echo "  - Advanced Capabilities: 2 components"
echo "  - Analytics: 4 components (created earlier)"
echo "  TOTAL: 19 new components"
echo ""
echo "✅ All missing frontend components have been generated!"
