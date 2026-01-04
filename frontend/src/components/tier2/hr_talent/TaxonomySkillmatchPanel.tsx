import { useState } from 'react'
import axios from 'axios'
import { Brain, Plus, X, CheckCircle, AlertCircle, Target, TrendingUp , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import FileUpload from '../../FileUpload'

// Types matching backend schemas
type SkillCategory = 'technical' | 'soft_skills' | 'leadership' | 'domain_knowledge' | 'methodologies' | 'tools' | 'certifications'

interface TaxonomyNode {
  skill_name: string
  category: SkillCategory
  synonyms?: string[]
  related_skills?: string[]
  child_skills?: string[]
}

interface SkillMapping {
  original_skill: string
  standardized_skill_name: string
  category: SkillCategory
  match_type: string
  confidence: number
  related_skills?: string[]
  child_skills?: string[]
}

interface SkillTaxonomyRequest {
  skills: string[]
  use_llm_mapping?: boolean
  include_related_skills?: boolean
  session_id?: string
}

interface SkillTaxonomyResponse {
  mappings: SkillMapping[]
  unmapped_skills: string[]
  total_skills_processed: number
  taxonomy_coverage_percent: number
  tier_1_services_used: string[]
}

interface SkillSet {
  skills: string[]
  description?: string
}

interface SkillGap {
  skill_name: string
  category: SkillCategory
  priority: string
  training_resources?: string[]
}

interface SkillMatchResult {
  match_score: number
  matched_skills: string[]
  missing_skills: string[]
  skill_gaps: SkillGap[]
  recommendations: string[]
}

interface SkillMatchRequest {
  required_skillset: SkillSet
  candidate_skillset: SkillSet
  include_gap_analysis?: boolean
  include_recommendations?: boolean
  session_id?: string
}

interface SkillMatchResponse {
  match_result: SkillMatchResult
  required_skills_count: number
  candidate_skills_count: number
  match_score_breakdown: Record<string, number>
  tier_1_services_used: string[]
}

const CATEGORY_COLORS: Record<SkillCategory, string> = {
  technical: 'bg-blue-100 text-blue-800',
  soft_skills: 'bg-green-100 text-green-800',
  leadership: 'bg-purple-100 text-purple-800',
  domain_knowledge: 'bg-amber-100 text-amber-800',
  methodologies: 'bg-pink-100 text-pink-800',
  tools: 'bg-cyan-100 text-cyan-800',
  certifications: 'bg-indigo-100 text-indigo-800',
}

export default function TaxonomySkillmatchPanel() {
  const [mode, setMode] = useState<'taxonomy' | 'match'>('taxonomy')
  const [showConfig, setShowConfig] = useState(false)

  // Taxonomy mode state
  const [skills, setSkills] = useState<string[]>([''])
  const [useLLM, setUseLLM] = useState(true)
  const [includeRelated, setIncludeRelated] = useState(true)
  const [taxonomyResult, setTaxonomyResult] = useState<SkillTaxonomyResponse | null>(null)

  // Match mode state
  const [requiredSkills, setRequiredSkills] = useState<string[]>([''])
  const [candidateSkills, setCandidateSkills] = useState<string[]>([''])
  const [includeGaps, setIncludeGaps] = useState(true)
  const [includeRecommendations, setIncludeRecommendations] = useState(true)
  const [matchResult, setMatchResult] = useState<SkillMatchResponse | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  // Taxonomy mode functions
  const addSkillField = () => setSkills([...skills, ''])
  const removeSkillField = (index: number) => setSkills(skills.filter((_, i) => i !== index))
  const updateSkill = (index: number, value: string) => {
    const updated = [...skills]
    updated[index] = value
    setSkills(updated)
  }

  const handleTaxonomyMap = async () => {
    const validSkills = skills.filter(s => s.trim().length > 0)
    if (validSkills.length === 0) {
      setError('Please enter at least one skill')
      return
    }

    setLoading(true)
    setError(null)
    setTaxonomyResult(null)

    const requestData: SkillTaxonomyRequest = {
      skills: validSkills,
      use_llm_mapping: useLLM,
      include_related_skills: includeRelated,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<SkillTaxonomyResponse>(
        'http://localhost:8000/api/v1/modules/taxonomy-skillmatch/taxonomy/map',
        requestData
      )
      setTaxonomyResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Skill taxonomy mapping failed')
    } finally {
      setLoading(false)
    }
  }

  // Match mode functions
  const addRequiredSkill = () => setRequiredSkills([...requiredSkills, ''])
  const removeRequiredSkill = (index: number) => setRequiredSkills(requiredSkills.filter((_, i) => i !== index))
  const updateRequiredSkill = (index: number, value: string) => {
    const updated = [...requiredSkills]
    updated[index] = value
    setRequiredSkills(updated)
  }

  const addCandidateSkill = () => setCandidateSkills([...candidateSkills, ''])
  const removeCandidateSkill = (index: number) => setCandidateSkills(candidateSkills.filter((_, i) => i !== index))
  const updateCandidateSkill = (index: number, value: string) => {
    const updated = [...candidateSkills]
    updated[index] = value
    setCandidateSkills(updated)
  }

  const handleSkillMatch = async () => {
    const validRequired = requiredSkills.filter(s => s.trim().length > 0)
    const validCandidate = candidateSkills.filter(s => s.trim().length > 0)

    if (validRequired.length === 0 || validCandidate.length === 0) {
      setError('Please enter skills for both required and candidate skillsets')
      return
    }

    setLoading(true)
    setError(null)
    setMatchResult(null)

    const requestData: SkillMatchRequest = {
      required_skillset: { skills: validRequired },
      candidate_skillset: { skills: validCandidate },
      include_gap_analysis: includeGaps,
      include_recommendations: includeRecommendations,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<SkillMatchResponse>(
        'http://localhost:8000/api/v1/modules/taxonomy-skillmatch/skillsets/match',
        requestData
      )
      setMatchResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Skill matching failed')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-8 h-8 text-purple-600" />
          Skill Taxonomy & Matching
        </h1>
        <p className="text-gray-600 mt-2">
          Map skills to standard taxonomy or match skillsets with gap analysis
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
              moduleName="taxonomy_skillmatch"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Document Upload Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          🧠 Upload Skill Data
        </h3>
        <p className="text-sm text-slate-600 mb-4">
          Upload job descriptions, resumes, skill taxonomies, or competency frameworks for mapping and matching.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'hr_talent',
            usecase: 'skill_matching'
          }}
        />
      </div>

      {/* Mode Selector */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex gap-4">
          <button
            onClick={() => { setMode('taxonomy'); setError(null); }}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
              mode === 'taxonomy'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Taxonomy Mapping
          </button>
          <button
            onClick={() => { setMode('match'); setError(null); }}
            className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
              mode === 'match'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Skillset Matching
          </button>
        </div>
      </div>

      {/* Taxonomy Mode */}
      {mode === 'taxonomy' && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6 space-y-6">
          <h2 className="text-xl font-semibold">Map Skills to Taxonomy</h2>

          {/* Skill Inputs */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">Skills</label>
            {skills.map((skill, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => updateSkill(index, e.target.value)}
                  placeholder={`Skill ${index + 1} (e.g., Python, Leadership, Agile)`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
                {skills.length > 1 && (
                  <button
                    onClick={() => removeSkillField(index)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={addSkillField}
            className="flex items-center gap-2 px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            Add Another Skill
          </button>

          {/* Options */}
          <div className="border-t pt-4 space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={useLLM}
                onChange={(e) => setUseLLM(e.target.checked)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700">Use AI for fuzzy skill matching</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeRelated}
                onChange={(e) => setIncludeRelated(e.target.checked)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700">Include related skills</span>
            </label>
          </div>

          <button
            onClick={handleTaxonomyMap}
            disabled={loading}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Mapping Skills...
              </>
            ) : (
              <>
                <Brain className="w-5 h-5" />
                Map to Taxonomy
              </>
            )}
          </button>
        </div>
      )}

      {/* Match Mode */}
      {mode === 'match' && (
        <div className="space-y-6">
          {/* Required Skills */}
          <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
            <h2 className="text-xl font-semibold">Required Skillset (Job/Role)</h2>
            {requiredSkills.map((skill, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => updateRequiredSkill(index, e.target.value)}
                  placeholder={`Required skill ${index + 1}`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
                {requiredSkills.length > 1 && (
                  <button onClick={() => removeRequiredSkill(index)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
            <button onClick={addRequiredSkill} className="flex items-center gap-2 px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg font-medium">
              <Plus className="w-4 h-4" />
              Add Required Skill
            </button>
          </div>

          {/* Candidate Skills */}
          <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
            <h2 className="text-xl font-semibold">Candidate Skillset</h2>
            {candidateSkills.map((skill, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => updateCandidateSkill(index, e.target.value)}
                  placeholder={`Candidate skill ${index + 1}`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
                {candidateSkills.length > 1 && (
                  <button onClick={() => removeCandidateSkill(index)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
            <button onClick={addCandidateSkill} className="flex items-center gap-2 px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg font-medium">
              <Plus className="w-4 h-4" />
              Add Candidate Skill
            </button>
          </div>

          {/* Match Options */}
          <div className="bg-white rounded-lg shadow-md p-6 space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeGaps}
                onChange={(e) => setIncludeGaps(e.target.checked)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700">Include skill gap analysis</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeRecommendations}
                onChange={(e) => setIncludeRecommendations(e.target.checked)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-700">Generate training recommendations</span>
            </label>
          </div>

          <button
            onClick={handleSkillMatch}
            disabled={loading}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Matching Skillsets...
              </>
            ) : (
              <>
                <Target className="w-5 h-5" />
                Match Skillsets
              </>
            )}
          </button>
        </div>
      )}

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

      {/* Taxonomy Results */}
      {mode === 'taxonomy' && taxonomyResult && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Taxonomy Mapping Summary</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">Skills Processed</p>
                <p className="text-3xl font-bold text-purple-900">{taxonomyResult.total_skills_processed}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">Successfully Mapped</p>
                <p className="text-3xl font-bold text-green-900">{taxonomyResult.mappings.length}</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Coverage</p>
                <p className="text-3xl font-bold text-blue-900">{taxonomyResult.taxonomy_coverage_percent.toFixed(0)}%</p>
              </div>
            </div>
          </div>

          {/* Skill Mappings */}
          <div className="space-y-3">
            <h3 className="text-xl font-semibold">Skill Mappings</h3>
            {taxonomyResult.mappings.map((mapping, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-sm text-gray-600">Original: <span className="font-medium">{mapping.original_skill}</span></p>
                    <p className="text-lg font-bold text-gray-900">{mapping.standardized_skill_name}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${CATEGORY_COLORS[mapping.category]}`}>
                      {mapping.category.replace('_', ' ').toUpperCase()}
                    </span>
                    <p className="text-sm text-gray-600 mt-1">
                      {(mapping.confidence * 100).toFixed(0)}% confidence
                    </p>
                  </div>
                </div>
                {mapping.related_skills && mapping.related_skills.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-600 mb-1">Related Skills:</p>
                    <div className="flex flex-wrap gap-1">
                      {mapping.related_skills.map((rel, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">{rel}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {taxonomyResult.unmapped_skills.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <p className="font-medium text-orange-900 mb-2">Unmapped Skills</p>
              <p className="text-sm text-orange-700">{taxonomyResult.unmapped_skills.join(', ')}</p>
            </div>
          )}
        </div>
      )}

      {/* Match Results */}
      {mode === 'match' && matchResult && (
        <div className="space-y-6">
          {/* Match Score */}
          <div className={`rounded-lg shadow-lg p-6 ${getScoreColor(matchResult.match_result.match_score)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold mb-1">Overall Match Score</p>
                <p className="text-5xl font-bold">{(matchResult.match_result.match_score * 100).toFixed(0)}%</p>
              </div>
              <TrendingUp className="w-16 h-16 opacity-50" />
            </div>
          </div>

          {/* Matched Skills */}
          {matchResult.match_result.matched_skills.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Matched Skills ({matchResult.match_result.matched_skills.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {matchResult.match_result.matched_skills.map((skill, idx) => (
                  <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing Skills */}
          {matchResult.match_result.missing_skills.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Missing Skills ({matchResult.match_result.missing_skills.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {matchResult.match_result.missing_skills.map((skill, idx) => (
                  <span key={idx} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Skill Gaps */}
          {matchResult.match_result.skill_gaps && matchResult.match_result.skill_gaps.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Skill Gap Analysis</h3>
              <div className="space-y-3">
                {matchResult.match_result.skill_gaps.map((gap, idx) => (
                  <div key={idx} className="p-3 bg-orange-50 rounded-lg border-l-4 border-orange-500">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-gray-900">{gap.skill_name}</p>
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${CATEGORY_COLORS[gap.category]}`}>
                          {gap.category.replace('_', ' ')}
                        </span>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        gap.priority === 'high' ? 'bg-red-100 text-red-800' :
                        gap.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {gap.priority.toUpperCase()} PRIORITY
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {matchResult.match_result.recommendations && matchResult.match_result.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4">Training Recommendations</h3>
              <ul className="space-y-2">
                {matchResult.match_result.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-1" />
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
