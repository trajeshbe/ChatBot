import { useState, useEffect } from 'react'
import { Key, Lock, CheckCircle, XCircle, Eye, EyeOff, Trash2, Plus, AlertCircle, Clock } from 'lucide-react'
import axios from 'axios'

interface ProviderStatus {
  provider: string
  is_active: boolean
  created_at: string | null
  updated_at: string | null
  last_used_at: string | null
  has_key: boolean
}

interface StoreAPIKeyRequest {
  provider: string
  api_key: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SUPPORTED_PROVIDERS = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4, GPT-3.5-turbo models',
    placeholder: 'sk-...',
    icon: '🤖',
    docsUrl: 'https://platform.openai.com/api-keys'
  },
  {
    id: 'anthropic',
    name: 'Anthropic (Claude)',
    description: 'Claude 3 Opus, Sonnet, Haiku',
    placeholder: 'sk-ant-...',
    icon: '🧠',
    docsUrl: 'https://console.anthropic.com/settings/keys'
  },
  {
    id: 'huggingface',
    name: 'HuggingFace',
    description: 'For vLLM model downloads',
    placeholder: 'hf_...',
    icon: '🤗',
    docsUrl: 'https://huggingface.co/settings/tokens'
  }
]

export default function APIKeysManager() {
  const [providers, setProviders] = useState<ProviderStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Form state
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchProviders()
  }, [])

  const fetchProviders = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_URL}/api/v1/admin/secrets/api-keys`)
      setProviders(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load API keys')
      console.error('Error fetching providers:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStoreKey = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedProvider || !apiKey.trim()) {
      setError('Please select a provider and enter an API key')
      return
    }

    try {
      setSubmitting(true)
      setError(null)
      setSuccess(null)

      const payload: StoreAPIKeyRequest = {
        provider: selectedProvider,
        api_key: apiKey
      }

      const response = await axios.post(
        `${API_URL}/api/v1/admin/secrets/api-keys`,
        payload
      )

      setSuccess(`${response.data.message}`)
      setApiKey('')
      setSelectedProvider(null)

      // Refresh provider list
      await fetchProviders()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to store API key')
      console.error('Error storing API key:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteKey = async (provider: string) => {
    if (!confirm(`Are you sure you want to delete the ${provider} API key? This action cannot be undone.`)) {
      return
    }

    try {
      setError(null)
      setSuccess(null)

      await axios.delete(`${API_URL}/api/v1/admin/secrets/api-keys/${provider}`)

      setSuccess(`API key for ${provider} deleted successfully`)

      // Refresh provider list
      await fetchProviders()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete API key')
      console.error('Error deleting API key:', err)
    }
  }

  const handleValidateKey = async (provider: string) => {
    try {
      setError(null)
      setSuccess(null)

      const response = await axios.post(
        `${API_URL}/api/v1/admin/secrets/api-keys/${provider}/validate`
      )

      if (response.data.is_valid) {
        setSuccess(`${provider} API key is valid and can be decrypted`)
      } else {
        setError(`${provider} API key validation failed: ${response.data.message}`)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate API key')
      console.error('Error validating API key:', err)
    }
  }

  const getProviderConfig = (providerId: string) => {
    return SUPPORTED_PROVIDERS.find(p => p.id === providerId)
  }

  const getProviderStatus = (providerId: string): ProviderStatus | undefined => {
    return providers.find(p => p.provider === providerId)
  }

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Key className="w-6 h-6 text-blue-500" />
        <h2 className="text-2xl font-bold text-gray-900">API Keys Management</h2>
      </div>

      <p className="text-gray-600">
        Securely manage LLM provider API keys. Keys are encrypted using Fernet encryption before storage.
        Changes take effect immediately without requiring container restart.
      </p>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-red-800">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-green-800">Success</h3>
            <p className="text-green-700 text-sm">{success}</p>
          </div>
          <button onClick={() => setSuccess(null)} className="text-green-500 hover:text-green-700">
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Add/Update API Key Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Add or Update API Key
        </h3>

        <form onSubmit={handleStoreKey} className="space-y-4">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Provider
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {SUPPORTED_PROVIDERS.map((provider) => {
                const status = getProviderStatus(provider.id)
                const isActive = status?.has_key && status?.is_active

                return (
                  <button
                    key={provider.id}
                    type="button"
                    onClick={() => setSelectedProvider(provider.id)}
                    className={`relative p-4 rounded-lg border-2 transition-all text-left ${
                      selectedProvider === provider.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{provider.icon}</span>
                        <div>
                          <h4 className="font-medium text-gray-900">{provider.name}</h4>
                          <p className="text-xs text-gray-500">{provider.description}</p>
                        </div>
                      </div>
                      {isActive && (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* API Key Input */}
          {selectedProvider && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                  <a
                    href={getProviderConfig(selectedProvider)?.docsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-blue-600 hover:text-blue-800 text-xs"
                  >
                    (Get API key)
                  </a>
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={getProviderConfig(selectedProvider)?.placeholder}
                    className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Your API key is encrypted before storage and never logged in plaintext
                </p>
              </div>

              <button
                type="submit"
                disabled={submitting || !apiKey.trim()}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
              >
                <Lock className="w-4 h-4" />
                {submitting ? 'Saving...' : 'Save API Key (Encrypted)'}
              </button>
            </>
          )}
        </form>
      </div>

      {/* Existing API Keys */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Key className="w-5 h-5" />
            Configured API Keys
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">
            Loading API keys...
          </div>
        ) : providers.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No API keys configured yet. Add one above to get started.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {SUPPORTED_PROVIDERS.map((providerConfig) => {
              const status = getProviderStatus(providerConfig.id)
              if (!status?.has_key) return null

              return (
                <div key={providerConfig.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <span className="text-3xl">{providerConfig.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-gray-900">{providerConfig.name}</h4>
                          {status.is_active ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <CheckCircle className="w-3 h-3" />
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              <XCircle className="w-3 h-3" />
                              Inactive
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{providerConfig.description}</p>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Created:</span>
                            <span className="ml-2 text-gray-700">{formatDate(status.created_at)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Last Updated:</span>
                            <span className="ml-2 text-gray-700">{formatDate(status.updated_at)}</span>
                          </div>
                          <div className="col-span-2">
                            <span className="text-gray-500 flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              Last Used:
                            </span>
                            <span className="ml-2 text-gray-700">{formatDate(status.last_used_at)}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleValidateKey(providerConfig.id)}
                        className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 flex items-center gap-1"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Validate
                      </button>
                      <button
                        onClick={() => handleDeleteKey(providerConfig.id)}
                        className="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 flex items-center gap-1"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Lock className="w-5 h-5 text-blue-500 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900 mb-1">Security Features</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• All API keys are encrypted using Fernet (AES-128) before storage</li>
              <li>• Keys are never logged in plaintext or exposed via API responses</li>
              <li>• Full audit trail tracks all access and modifications</li>
              <li>• Soft delete preserves history while preventing future use</li>
              <li>• Master encryption key stored separately from database</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
