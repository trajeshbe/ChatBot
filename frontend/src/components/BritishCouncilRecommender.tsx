import { useState } from 'react'
import axios from 'axios'
import { Settings } from 'lucide-react'
import POCConfigManager from './POCConfigManager'

interface UserProfile {
  skills: string[]
  interests: string[]
  education_level: string
  career_goals: string[]
  preferred_format: string
  language_proficiency: string
  availability: string
}

interface CourseRecommendation {
  course_id: string
  course_name: string
  description: string
  match_score: number
  semantic_score: number
  profile_score: number
  reasons: string[]
  metadata: Record<string, any>
}

interface RecommendationResponse {
  recommendations: CourseRecommendation[]
  profile: UserProfile
  total_courses_analyzed: number
  status: string
}

export default function BritishCouncilRecommender() {
  const [userInput, setUserInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [recommendations, setRecommendations] = useState<CourseRecommendation[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)

  const handleAnalyzeProfile = async () => {
    if (!userInput.trim()) {
      setError('Please enter your learning goals and preferences')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('http://localhost:8000/api/v1/british-council/profile/analyze', {
        user_input: userInput
      })

      setProfile(response.data.profile)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze profile')
      console.error('Profile analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleGetRecommendations = async () => {
    if (!userInput.trim()) {
      setError('Please enter your learning goals and preferences')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post<RecommendationResponse>(
        'http://localhost:8000/api/v1/british-council/courses/recommend',
        {
          user_input: userInput,
          top_k: 10
        }
      )

      setRecommendations(response.data.recommendations)
      setProfile(response.data.profile)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get recommendations')
      console.error('Recommendation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-emerald-600 bg-emerald-50'
    if (score >= 0.6) return 'text-blue-600 bg-blue-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getLevelBadgeColor = (level: string) => {
    const colors: Record<string, string> = {
      'beginner': 'bg-green-100 text-green-800',
      'intermediate': 'bg-blue-100 text-blue-800',
      'advanced': 'bg-purple-100 text-purple-800'
    }
    return colors[level.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">
              🎓 British Council Course Recommender
            </h1>
            <p className="text-slate-600">
              AI-powered course recommendations based on your profile and goals
            </p>
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
              moduleName="british_council"
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}

        {/* Input Section */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-slate-800 mb-4">
            Tell us about your learning goals
          </h2>

          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Example: I'm a software engineer looking to improve my business English. I have intermediate level English (B1) and prefer online courses on weekends. I want to advance my career in international companies."
            className="w-full h-32 px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />

          <div className="flex gap-3 mt-4">
            <button
              onClick={handleAnalyzeProfile}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '⏳ Analyzing...' : '🔍 Analyze Profile'}
            </button>

            <button
              onClick={handleGetRecommendations}
              disabled={loading}
              className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '⏳ Finding Courses...' : '🎯 Get Recommendations'}
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              ❌ {error}
            </div>
          )}
        </div>

        {/* Profile Display */}
        {profile && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">
              👤 Your Learning Profile
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-600">Skills</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {profile.skills.map((skill, idx) => (
                    <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-600">Interests</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {profile.interests.map((interest, idx) => (
                    <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
                      {interest}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-600">Education Level</label>
                <div className="mt-1">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLevelBadgeColor(profile.education_level)}`}>
                    {profile.education_level}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-600">Language Proficiency (CEFR)</label>
                <div className="mt-1">
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    {profile.language_proficiency}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-600">Preferred Format</label>
                <div className="mt-1">
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm">
                    {profile.preferred_format}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-slate-600">Availability</label>
                <div className="mt-1">
                  <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm">
                    {profile.availability}
                  </span>
                </div>
              </div>

              <div className="col-span-2">
                <label className="text-sm font-medium text-slate-600">Career Goals</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {profile.career_goals.map((goal, idx) => (
                    <span key={idx} className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm">
                      {goal}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">
              🎯 Course Recommendations ({recommendations.length})
            </h2>

            <div className="space-y-4">
              {recommendations.map((course, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-800 mb-1">
                        {idx + 1}. {course.course_name}
                      </h3>
                      <p className="text-sm text-slate-600 line-clamp-2">
                        {course.description}
                      </p>
                    </div>

                    <div className="ml-4 text-right">
                      <div className={`px-4 py-2 rounded-lg font-bold ${getMatchScoreColor(course.match_score)}`}>
                        {(course.match_score * 100).toFixed(0)}% Match
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3 text-sm mb-3">
                    <div className="flex items-center gap-1">
                      <span className="text-slate-600">Semantic:</span>
                      <span className="font-medium text-blue-600">
                        {(course.semantic_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-slate-600">Profile:</span>
                      <span className="font-medium text-purple-600">
                        {(course.profile_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="text-xs font-medium text-slate-600 mb-2">Why this course matches:</p>
                    <ul className="space-y-1">
                      {course.reasons.map((reason, ridx) => (
                        <li key={ridx} className="text-sm text-slate-700 flex items-start">
                          <span className="mr-2">✓</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {recommendations.length === 0 && !loading && !profile && (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="text-6xl mb-4">🎓</div>
            <h3 className="text-xl font-semibold text-slate-800 mb-2">
              Ready to find your perfect course?
            </h3>
            <p className="text-slate-600">
              Tell us about your learning goals and we'll recommend the best British Council courses for you
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
