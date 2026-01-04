import { useState } from 'react'
import axios from 'axios'
import { Search, Plus, X, Users, Star, TrendingUp, Award, Briefcase , Settings} from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import FileUpload from '../../FileUpload'

// Types matching backend schemas
type ExperienceLevel = 'entry' | 'mid' | 'senior' | 'lead' | 'executive'
type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'freelance' | 'internship'

interface Skill {
  name: string
  proficiency?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  required?: boolean
  years_of_experience?: number
}

interface JobRequirement {
  job_id?: string
  job_title: string
  experience_level: ExperienceLevel
  required_skills: Skill[]
  preferred_skills?: Skill[]
  years_of_experience_min?: number
  years_of_experience_max?: number
  education_level?: string
  employment_type?: EmploymentType
  location?: string
  salary_range_min?: number
  salary_range_max?: number
}

interface CandidateProfile {
  candidate_id: string
  name: string
  current_title?: string
  years_of_experience?: number
  skills: Skill[]
  education?: string
  location?: string
  expected_salary?: number
  resume_summary?: string
}

interface MatchScore {
  overall_score: number
  skills_score: number
  experience_score: number
  education_score: number
  location_score: number
  salary_score: number
}

interface TalentMatch {
  candidate: CandidateProfile
  match_score: MatchScore
  matched_skills: string[]
  missing_skills: string[]
  strengths: string[]
  gaps: string[]
  recommendation: string
  rank: number
}

interface ScoringWeights {
  skills_weight?: number
  experience_weight?: number
  education_weight?: number
  location_weight?: number
  salary_weight?: number
}

interface TalentSearchRequest {
  job_requirement: JobRequirement
  candidate_pool?: CandidateProfile[]
  top_n?: number
  min_score_threshold?: number
  use_semantic_matching?: boolean
  weights?: ScoringWeights
  session_id?: string
}

interface TalentSearchResponse {
  matches: TalentMatch[]
  total_candidates_evaluated: number
  total_matches_found: number
  avg_match_score: number
  processing_time_seconds: number
  tier_1_services_used: string[]
}

export default function TalentSearchPanel() {
  const [jobTitle, setJobTitle] = useState('')
  const [showConfig, setShowConfig] = useState(false)
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>('mid')
  const [requiredSkills, setRequiredSkills] = useState<string[]>([''])
  const [preferredSkills, setPreferredSkills] = useState<string[]>([''])
  const [yearsMin, setYearsMin] = useState<number>(2)
  const [topN, setTopN] = useState<number>(10)
  const [minScore, setMinScore] = useState<number>(60)
  const [useSemanticMatching, setUseSemanticMatching] = useState(true)

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TalentSearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sessionId = typeof window !== 'undefined'
    ? sessionStorage.getItem('sessionId') || `session_${Date.now()}`
    : `session_${Date.now()}`

  const addRequiredSkill = () => setRequiredSkills([...requiredSkills, ''])
  const removeRequiredSkill = (index: number) => setRequiredSkills(requiredSkills.filter((_, i) => i !== index))
  const updateRequiredSkill = (index: number, value: string) => {
    const updated = [...requiredSkills]
    updated[index] = value
    setRequiredSkills(updated)
  }

  const addPreferredSkill = () => setPreferredSkills([...preferredSkills, ''])
  const removePreferredSkill = (index: number) => setPreferredSkills(preferredSkills.filter((_, i) => i !== index))
  const updatePreferredSkill = (index: number, value: string) => {
    const updated = [...preferredSkills]
    updated[index] = value
    setPreferredSkills(updated)
  }

  const handleSearch = async () => {
    if (!jobTitle.trim()) {
      setError('Please enter a job title')
      return
    }

    const validRequiredSkills = requiredSkills.filter(s => s.trim().length > 0)
    if (validRequiredSkills.length === 0) {
      setError('Please enter at least one required skill')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const validPreferredSkills = preferredSkills.filter(s => s.trim().length > 0)

    const requestData: TalentSearchRequest = {
      job_requirement: {
        job_title: jobTitle,
        experience_level: experienceLevel,
        required_skills: validRequiredSkills.map(name => ({ name, required: true })),
        preferred_skills: validPreferredSkills.map(name => ({ name, required: false })),
        years_of_experience_min: yearsMin,
      },
      top_n: topN,
      min_score_threshold: minScore,
      use_semantic_matching: useSemanticMatching,
      session_id: sessionId,
    }

    try {
      const response = await axios.post<TalentSearchResponse>(
        'http://localhost:8000/api/v1/modules/talent-search/search',
        requestData
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Talent search failed')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-orange-600 bg-orange-50'
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Users className="w-8 h-8 text-blue-600" />
          AI-Powered Talent Search
        </h1>
        <p className="text-gray-600 mt-2">
          Find the best candidates with multi-dimensional matching and semantic analysis
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
              moduleName="talent_search"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

      {/* Document Upload Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          📄 Upload Resumes & Job Descriptions
        </h3>
        <p className="text-sm text-slate-600 mb-4">
          Upload resumes, CVs, job descriptions, or candidate profiles for intelligent matching.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'hr_talent',
            usecase: 'talent_search'
          }}
        />
      </div>

      {/* Job Requirements Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6 space-y-6">
        <h2 className="text-xl font-semibold">Job Requirements</h2>

        {/* Job Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Title
          </label>
          <input
            type="text"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g., Senior Python Developer"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Experience Level & Years */}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Experience Level
            </label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value as ExperienceLevel)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
              <option value="executive">Executive</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Years of Experience
            </label>
            <input
              type="number"
              min="0"
              max="30"
              value={yearsMin}
              onChange={(e) => setYearsMin(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Required Skills */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Required Skills
          </label>
          <div className="space-y-2">
            {requiredSkills.map((skill, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => updateRequiredSkill(index, e.target.value)}
                  placeholder={`Required skill ${index + 1}`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                {requiredSkills.length > 1 && (
                  <button
                    onClick={() => removeRequiredSkill(index)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            onClick={addRequiredSkill}
            className="mt-2 flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            Add Required Skill
          </button>
        </div>

        {/* Preferred Skills */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Skills (Optional)
          </label>
          <div className="space-y-2">
            {preferredSkills.map((skill, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => updatePreferredSkill(index, e.target.value)}
                  placeholder={`Preferred skill ${index + 1}`}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                {preferredSkills.length > 1 && (
                  <button
                    onClick={() => removePreferredSkill(index)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            onClick={addPreferredSkill}
            className="mt-2 flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            Add Preferred Skill
          </button>
        </div>

        {/* Search Parameters */}
        <div className="border-t pt-4">
          <p className="text-sm font-semibold text-gray-700 mb-3">Search Parameters</p>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">Top N Results</label>
              <input
                type="number"
                min="1"
                max="50"
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Min Match Score (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={useSemanticMatching}
                  onChange={(e) => setUseSemanticMatching(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Use AI semantic matching</span>
              </label>
            </div>
          </div>
        </div>

        {/* Search Button */}
        <button
          onClick={handleSearch}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Searching Talent Pool...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Search for Talent
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
          {/* Summary */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Search Summary</h3>
            <div className="grid md:grid-cols-4 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Candidates Evaluated</p>
                <p className="text-3xl font-bold text-blue-900">{result.total_candidates_evaluated}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">Matches Found</p>
                <p className="text-3xl font-bold text-green-900">{result.total_matches_found}</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">Avg Match Score</p>
                <p className="text-3xl font-bold text-purple-900">{result.avg_match_score.toFixed(0)}%</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Processing Time</p>
                <p className="text-3xl font-bold text-gray-900">{result.processing_time_seconds.toFixed(1)}s</p>
              </div>
            </div>
          </div>

          {/* Talent Matches */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Top {result.matches.length} Candidates</h3>
            {result.matches.map((match) => (
              <div key={match.candidate.candidate_id} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-3 py-1 bg-blue-600 text-white rounded-full text-sm font-bold">
                        #{match.rank}
                      </span>
                      <div>
                        <h4 className="text-xl font-bold text-gray-900">{match.candidate.name}</h4>
                        {match.candidate.current_title && (
                          <p className="text-sm text-gray-600">{match.candidate.current_title}</p>
                        )}
                      </div>
                    </div>
                    <p className="text-gray-700 italic text-sm">{match.recommendation}</p>
                  </div>
                  <div className="text-right ml-4">
                    <div className={`text-3xl font-bold px-4 py-2 rounded-lg ${getScoreColor(match.match_score.overall_score)}`}>
                      {match.match_score.overall_score.toFixed(0)}%
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Overall Match</p>
                  </div>
                </div>

                {/* Match Score Breakdown */}
                <div className="grid md:grid-cols-5 gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Skills</p>
                    <p className="text-lg font-bold text-blue-600">{match.match_score.skills_score.toFixed(0)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Experience</p>
                    <p className="text-lg font-bold text-green-600">{match.match_score.experience_score.toFixed(0)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Education</p>
                    <p className="text-lg font-bold text-purple-600">{match.match_score.education_score.toFixed(0)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Location</p>
                    <p className="text-lg font-bold text-amber-600">{match.match_score.location_score.toFixed(0)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Salary</p>
                    <p className="text-lg font-bold text-pink-600">{match.match_score.salary_score.toFixed(0)}%</p>
                  </div>
                </div>

                {/* Candidate Details */}
                <div className="grid md:grid-cols-3 gap-4 mb-4">
                  {match.candidate.years_of_experience && (
                    <div className="flex items-center gap-2">
                      <Briefcase className="w-4 h-4 text-blue-600" />
                      <div>
                        <p className="text-xs text-gray-600">Experience</p>
                        <p className="font-semibold">{match.candidate.years_of_experience} years</p>
                      </div>
                    </div>
                  )}
                  {match.candidate.education && (
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-purple-600" />
                      <div>
                        <p className="text-xs text-gray-600">Education</p>
                        <p className="font-semibold text-sm">{match.candidate.education}</p>
                      </div>
                    </div>
                  )}
                  {match.candidate.location && (
                    <div>
                      <p className="text-xs text-gray-600">Location</p>
                      <p className="font-semibold text-sm">{match.candidate.location}</p>
                    </div>
                  )}
                </div>

                {/* Skills Analysis */}
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  {/* Matched Skills */}
                  {match.matched_skills.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-green-700 mb-2">Matched Skills ({match.matched_skills.length})</p>
                      <div className="flex flex-wrap gap-1">
                        {match.matched_skills.map((skill, idx) => (
                          <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Skills */}
                  {match.missing_skills.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-red-700 mb-2">Missing Skills ({match.missing_skills.length})</p>
                      <div className="flex flex-wrap gap-1">
                        {match.missing_skills.map((skill, idx) => (
                          <span key={idx} className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Strengths & Gaps */}
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Strengths */}
                  {match.strengths.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-blue-700 mb-2 flex items-center gap-1">
                        <Star className="w-4 h-4" />
                        Strengths
                      </p>
                      <ul className="space-y-1">
                        {match.strengths.map((strength, idx) => (
                          <li key={idx} className="text-sm text-blue-600 flex items-start gap-2">
                            <span className="text-blue-400">+</span>
                            <span>{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Gaps */}
                  {match.gaps.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-orange-700 mb-2 flex items-center gap-1">
                        <TrendingUp className="w-4 h-4" />
                        Development Areas
                      </p>
                      <ul className="space-y-1">
                        {match.gaps.map((gap, idx) => (
                          <li key={idx} className="text-sm text-orange-600 flex items-start gap-2">
                            <span className="text-orange-400">→</span>
                            <span>{gap}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Tech Info */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p><strong>Tier 1 Services:</strong> {result.tier_1_services_used.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  )
}
