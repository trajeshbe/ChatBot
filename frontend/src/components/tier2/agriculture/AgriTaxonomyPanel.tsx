import { useState } from 'react'
import axios from 'axios'
import { Sprout, Plus, X, CheckCircle, AlertCircle, Leaf, Thermometer, Droplets } from 'lucide-react'

// Types matching backend schemas
type CropCategory =
  | 'cereals'
  | 'legumes'
  | 'vegetables'
  | 'fruits'
  | 'oilseeds'
  | 'fiber_crops'
  | 'forage_crops'
  | 'tuber_crops'
  | 'spices'
  | 'medicinal_plants'

type SoilType = 'sandy' | 'loamy' | 'clay' | 'silt' | 'peaty' | 'chalky' | 'saline'
type ClimateZone = 'tropical' | 'subtropical' | 'temperate' | 'continental' | 'polar' | 'arid' | 'semi_arid'

interface GrowingRequirements {
  preferred_soil_types?: SoilType[]
  climate_zones?: ClimateZone[]
  temperature_optimal_celsius?: number
  ph_optimal?: number
  rainfall_min_mm?: number
  rainfall_max_mm?: number
}

interface SeasonalInfo {
  growth_duration_days?: number
  planting_season?: string
  harvest_season?: string
  growth_stages?: string[]
}

interface CropClassification {
  common_name: string
  scientific_name?: string
  category: CropCategory
  family?: string
  varieties?: string[]
}

interface CropTaxonomy {
  crop_id: string
  classification: CropClassification
  growing_requirements: GrowingRequirements
  seasonal_info: SeasonalInfo
}

interface TaxonomyClassificationRequest {
  crop_names: string[]
  include_requirements?: boolean
  include_seasonal_info?: boolean
  use_llm_enrichment?: boolean
  session_id?: string
}

interface TaxonomyClassificationResponse {
  classifications: CropTaxonomy[]
  unclassified_crops: string[]
  total_crops_processed: number
  taxonomy_coverage_percent: number
}

const CATEGORY_COLORS: Record<CropCategory, string> = {
  cereals: 'bg-yellow-100 text-yellow-800',
  legumes: 'bg-green-100 text-green-800',
  vegetables: 'bg-emerald-100 text-emerald-800',
  fruits: 'bg-red-100 text-red-800',
  oilseeds: 'bg-amber-100 text-amber-800',
  fiber_crops: 'bg-blue-100 text-blue-800',
  forage_crops: 'bg-lime-100 text-lime-800',
  tuber_crops: 'bg-orange-100 text-orange-800',
  spices: 'bg-pink-100 text-pink-800',
  medicinal_plants: 'bg-purple-100 text-purple-800',
}

export default function AgriTaxonomyPanel() {
  const [cropNames, setCropNames] = useState<string[]>([''])
  const [includeRequirements, setIncludeRequirements] = useState(true)
  const [includeSeasonal, setIncludeSeasonal] = useState(true)
  const [useLLM, setUseLLM] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TaxonomyClassificationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const addCropField = () => {
    setCropNames([...cropNames, ''])
  }

  const removeCropField = (index: number) => {
    setCropNames(cropNames.filter((_, i) => i !== index))
  }

  const updateCropName = (index: number, value: string) => {
    const updated = [...cropNames]
    updated[index] = value
    setCropNames(updated)
  }

  const handleClassify = async () => {
    const validCrops = cropNames.filter(name => name.trim().length > 0)

    if (validCrops.length === 0) {
      setError('Please enter at least one crop name')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const requestData: TaxonomyClassificationRequest = {
      crop_names: validCrops,
      include_requirements: includeRequirements,
      include_seasonal_info: includeSeasonal,
      use_llm_enrichment: useLLM,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<TaxonomyClassificationResponse>(
        'http://localhost:8000/api/v1/modules/agri-taxonomy/classify',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Crop classification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Sprout className="w-8 h-8 text-green-600" />
          Agricultural Taxonomy Classifier
        </h1>
        <p className="text-gray-600 mt-2">
          Classify crops with scientific names, growing requirements, and seasonal information
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6 space-y-6">
        <h2 className="text-xl font-semibold">Crop Names</h2>

        {/* Crop Name Inputs */}
        <div className="space-y-3">
          {cropNames.map((crop, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={crop}
                onChange={(e) => updateCropName(index, e.target.value)}
                placeholder={`Crop ${index + 1} (e.g., rice, wheat, tomato)`}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              {cropNames.length > 1 && (
                <button
                  onClick={() => removeCropField(index)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={addCropField}
          className="flex items-center gap-2 px-4 py-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          Add Another Crop
        </button>

        {/* Options */}
        <div className="border-t pt-4">
          <p className="text-sm font-semibold text-gray-700 mb-3">Classification Options</p>
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeRequirements}
                onChange={(e) => setIncludeRequirements(e.target.checked)}
                className="rounded text-green-600 focus:ring-green-500"
              />
              <span className="text-sm text-gray-700">Include growing requirements (soil, climate, temperature, pH)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeSeasonal}
                onChange={(e) => setIncludeSeasonal(e.target.checked)}
                className="rounded text-green-600 focus:ring-green-500"
              />
              <span className="text-sm text-gray-700">Include seasonal information (planting, harvest, duration)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={useLLM}
                onChange={(e) => setUseLLM(e.target.checked)}
                className="rounded text-green-600 focus:ring-green-500"
              />
              <span className="text-sm text-gray-700">Use AI enrichment for unknown crops</span>
            </label>
          </div>
        </div>

        {/* Classify Button */}
        <button
          onClick={handleClassify}
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Classifying Crops...
            </>
          ) : (
            <>
              <Leaf className="w-5 h-5" />
              Classify Crops
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
            <h3 className="text-xl font-semibold mb-4">Classification Summary</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">Total Crops</p>
                <p className="text-3xl font-bold text-green-900">{result.total_crops_processed}</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Successfully Classified</p>
                <p className="text-3xl font-bold text-blue-900">{result.classifications.length}</p>
              </div>
              <div className="p-4 bg-amber-50 rounded-lg">
                <p className="text-sm text-amber-600">Coverage</p>
                <p className="text-3xl font-bold text-amber-900">{result.taxonomy_coverage_percent.toFixed(0)}%</p>
              </div>
            </div>

            {result.unclassified_crops.length > 0 && (
              <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-orange-900">Unclassified Crops</p>
                  <p className="text-sm text-orange-700">{result.unclassified_crops.join(', ')}</p>
                </div>
              </div>
            )}
          </div>

          {/* Crop Classifications */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Crop Taxonomies</h3>
            {result.classifications.map((crop) => (
              <div key={crop.crop_id} className="bg-white rounded-lg shadow-md p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-2xl font-bold text-gray-900">{crop.classification.common_name}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${CATEGORY_COLORS[crop.classification.category]}`}>
                        {crop.classification.category.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    {crop.classification.scientific_name && (
                      <p className="text-gray-600 italic text-sm">
                        {crop.classification.scientific_name}
                        {crop.classification.family && ` • Family: ${crop.classification.family}`}
                      </p>
                    )}
                  </div>
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                </div>

                {/* Growing Requirements */}
                {includeRequirements && crop.growing_requirements && (
                  <div className="mb-4 p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-semibold text-green-900 mb-3 flex items-center gap-2">
                      <Leaf className="w-4 h-4" />
                      Growing Requirements
                    </p>
                    <div className="grid md:grid-cols-2 gap-4">
                      {/* Soil Types */}
                      {crop.growing_requirements.preferred_soil_types && crop.growing_requirements.preferred_soil_types.length > 0 && (
                        <div>
                          <p className="text-xs text-green-700 mb-1">Soil Types</p>
                          <div className="flex flex-wrap gap-1">
                            {crop.growing_requirements.preferred_soil_types.map((soil, idx) => (
                              <span key={idx} className="px-2 py-0.5 bg-green-200 text-green-800 rounded text-xs">
                                {soil}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Climate Zones */}
                      {crop.growing_requirements.climate_zones && crop.growing_requirements.climate_zones.length > 0 && (
                        <div>
                          <p className="text-xs text-green-700 mb-1">Climate Zones</p>
                          <div className="flex flex-wrap gap-1">
                            {crop.growing_requirements.climate_zones.map((zone, idx) => (
                              <span key={idx} className="px-2 py-0.5 bg-blue-200 text-blue-800 rounded text-xs">
                                {zone.replace('_', ' ')}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Temperature */}
                      {crop.growing_requirements.temperature_optimal_celsius && (
                        <div className="flex items-center gap-2">
                          <Thermometer className="w-4 h-4 text-red-600" />
                          <div>
                            <p className="text-xs text-gray-600">Optimal Temperature</p>
                            <p className="text-sm font-semibold">{crop.growing_requirements.temperature_optimal_celsius}°C</p>
                          </div>
                        </div>
                      )}

                      {/* pH */}
                      {crop.growing_requirements.ph_optimal && (
                        <div className="flex items-center gap-2">
                          <Droplets className="w-4 h-4 text-blue-600" />
                          <div>
                            <p className="text-xs text-gray-600">Optimal pH</p>
                            <p className="text-sm font-semibold">{crop.growing_requirements.ph_optimal}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Seasonal Info */}
                {includeSeasonal && crop.seasonal_info && (
                  <div className="p-4 bg-amber-50 rounded-lg">
                    <p className="text-sm font-semibold text-amber-900 mb-3">Seasonal Information</p>
                    <div className="grid md:grid-cols-3 gap-4">
                      {crop.seasonal_info.growth_duration_days && (
                        <div>
                          <p className="text-xs text-amber-700">Growth Duration</p>
                          <p className="text-sm font-semibold text-amber-900">{crop.seasonal_info.growth_duration_days} days</p>
                        </div>
                      )}
                      {crop.seasonal_info.planting_season && (
                        <div>
                          <p className="text-xs text-amber-700">Planting Season</p>
                          <p className="text-sm font-semibold text-amber-900">{crop.seasonal_info.planting_season}</p>
                        </div>
                      )}
                      {crop.seasonal_info.harvest_season && (
                        <div>
                          <p className="text-xs text-amber-700">Harvest Season</p>
                          <p className="text-sm font-semibold text-amber-900">{crop.seasonal_info.harvest_season}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
