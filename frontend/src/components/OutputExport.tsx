/**
 * OutputExport Component - Export chat responses to various formats
 *
 * Features:
 * - Export to Excel, Word, Markdown, JSON
 * - Template selection
 * - One-click quick export
 * - Download handling
 * - Beautiful UI with icons
 */

import { useState } from 'react'
import { Download, FileText, Table, Code, FileDown, X, CheckCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

interface OutputTemplate {
  id: string
  name: string
  description: string
  template_type: string
  template_config: any
}

interface Props {
  content: string
  messageId?: string
  onClose?: () => void
  defaultFormat?: 'excel' | 'word' | 'markdown' | 'json'
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function OutputExport({ content, messageId, onClose, defaultFormat = 'markdown' }: Props) {
  const [selectedFormat, setSelectedFormat] = useState<string>(defaultFormat)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [templates, setTemplates] = useState<OutputTemplate[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)
  const [exportStatus, setExportStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [showTemplateSelector, setShowTemplateSelector] = useState(false)

  // Format configurations
  const formats = [
    {
      id: 'excel',
      name: 'Excel',
      icon: Table,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      borderColor: 'border-green-200 dark:border-green-800',
      description: 'Export as .xlsx spreadsheet',
      extension: '.xlsx'
    },
    {
      id: 'word',
      name: 'Word',
      icon: FileText,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      borderColor: 'border-blue-200 dark:border-blue-800',
      description: 'Export as .docx document',
      extension: '.docx'
    },
    {
      id: 'markdown',
      name: 'Markdown',
      icon: FileDown,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      borderColor: 'border-purple-200 dark:border-purple-800',
      description: 'Export as .md file',
      extension: '.md'
    },
    {
      id: 'json',
      name: 'JSON',
      icon: Code,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20',
      borderColor: 'border-orange-200 dark:border-orange-800',
      description: 'Export as .json file',
      extension: '.json'
    }
  ]

  const currentFormat = formats.find(f => f.id === selectedFormat) || formats[2]

  // Load templates when format changes
  const loadTemplates = async (format: string) => {
    setIsLoadingTemplates(true)
    try {
      const response = await axios.get(`${API_URL}/api/v1/templates`, {
        params: { template_type: format, page: 1, page_size: 20 }
      })
      setTemplates(response.data.templates || [])

      // Auto-select first template if available
      if (response.data.templates?.length > 0) {
        setSelectedTemplate(response.data.templates[0].id)
      } else {
        setSelectedTemplate(null)
      }
    } catch (error) {
      console.error('Error loading templates:', error)
      setTemplates([])
      setSelectedTemplate(null)
    } finally {
      setIsLoadingTemplates(false)
    }
  }

  const handleFormatChange = async (format: string) => {
    setSelectedFormat(format)
    setExportStatus('idle')
    if (showTemplateSelector) {
      await loadTemplates(format)
    }
  }

  const handleQuickExport = async () => {
    // Quick export without template selection
    await handleExport()
  }

  const handleExportWithTemplate = async () => {
    setShowTemplateSelector(true)
    await loadTemplates(selectedFormat)
  }

  const handleExport = async () => {
    setIsLoading(true)
    setExportStatus('idle')

    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      const filename = `export_${timestamp}${currentFormat.extension}`

      const payload: any = {
        content: content,
        filename: filename
      }

      // Add template if selected
      if (selectedTemplate) {
        payload.template_id = selectedTemplate
      } else {
        // Use default template config based on format
        payload.template_config = getDefaultTemplateConfig(selectedFormat)
        payload.template_type = selectedFormat
      }

      const response = await axios.post(`${API_URL}/api/v1/export`, payload, {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setExportStatus('success')

      // Auto-close after success
      setTimeout(() => {
        if (onClose) onClose()
      }, 1500)
    } catch (error) {
      console.error('Error exporting:', error)
      setExportStatus('error')
    } finally {
      setIsLoading(false)
    }
  }

  const getDefaultTemplateConfig = (format: string) => {
    switch (format) {
      case 'excel':
        return {
          sheets: [{ name: 'Export', data: content }],
          auto_width: true
        }
      case 'word':
        return {
          title: 'Exported Content',
          content: content
        }
      case 'markdown':
        return {
          content: content,
          metadata: { exported_at: new Date().toISOString() }
        }
      case 'json':
        return {
          data: content,
          metadata: { exported_at: new Date().toISOString() }
        }
      default:
        return {}
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 w-96">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Download className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Export Response
          </h3>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
          >
            <X className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        )}
      </div>

      {/* Format Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Format
        </label>
        <div className="grid grid-cols-2 gap-2">
          {formats.map((format) => {
            const Icon = format.icon
            const isSelected = selectedFormat === format.id
            return (
              <button
                key={format.id}
                onClick={() => handleFormatChange(format.id)}
                className={`
                  p-3 rounded-lg border-2 transition-all text-left
                  ${isSelected
                    ? `${format.bgColor} ${format.borderColor} ${format.color}`
                    : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                  }
                `}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{format.name}</span>
                </div>
                <p className="text-xs opacity-80">{format.description}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Template Selection (Optional) */}
      {showTemplateSelector && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select Template (Optional)
          </label>
          {isLoadingTemplates ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            </div>
          ) : templates.length > 0 ? (
            <select
              value={selectedTemplate || ''}
              onChange={(e) => setSelectedTemplate(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Default Template</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              No templates available for this format
            </p>
          )}
        </div>
      )}

      {/* Status Messages */}
      {exportStatus === 'success' && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
          <span className="text-sm text-green-700 dark:text-green-300">
            Export successful! File downloaded.
          </span>
        </div>
      )}

      {exportStatus === 'error' && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <span className="text-sm text-red-700 dark:text-red-300">
            Export failed. Please try again.
          </span>
        </div>
      )}

      {/* Content Preview */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Content Preview
        </label>
        <div className="p-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg max-h-32 overflow-y-auto">
          <p className="text-xs text-gray-600 dark:text-gray-400 font-mono whitespace-pre-wrap line-clamp-6">
            {content.slice(0, 200)}{content.length > 200 ? '...' : ''}
          </p>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {content.length} characters
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        {!showTemplateSelector ? (
          <>
            <button
              onClick={handleQuickExport}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors text-sm font-medium"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              Quick Export
            </button>
            <button
              onClick={handleExportWithTemplate}
              disabled={isLoading}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium"
            >
              With Template
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setShowTemplateSelector(false)}
              disabled={isLoading}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium"
            >
              Back
            </button>
            <button
              onClick={handleExport}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors text-sm font-medium"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              Export {currentFormat.name}
            </button>
          </>
        )}
      </div>

      {/* Help Text */}
      <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
        <p className="text-xs text-blue-700 dark:text-blue-300">
          💡 <strong>Quick Export:</strong> Uses default template. <strong>With Template:</strong> Choose from available templates for customized output.
        </p>
      </div>
    </div>
  )
}
