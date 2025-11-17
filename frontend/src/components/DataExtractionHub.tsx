import { useState } from 'react'
import { FileSpreadsheet, Sparkles, Zap } from 'lucide-react'
import TemplateExtractor from './TemplateExtractor'
import { SmartExtractor } from './SmartExtractor'
import { SmartTemplateMapper } from './SmartTemplateMapper'

interface Props {
  sessionId: string
}

type ExtractionMode = 'template' | 'smart' | 'mapper'

export default function DataExtractionHub({ sessionId }: Props) {
  const [mode, setMode] = useState<ExtractionMode>('smart')

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Data Extraction
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Extract structured data from websites using templates or AI
          </p>
        </div>

        {/* Mode Selector */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-2 mb-6 inline-flex gap-2 border border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setMode('smart')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${
              mode === 'smart'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Sparkles className="h-5 w-5" />
            Smart Extraction
          </button>

          <button
            onClick={() => setMode('mapper')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${
              mode === 'mapper'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <Zap className="h-5 w-5" />
            Template Mapper
            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-blue-200 text-xs font-bold rounded-full">
              NEW
            </span>
          </button>

          <button
            onClick={() => setMode('template')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${
              mode === 'template'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
          >
            <FileSpreadsheet className="h-5 w-5" />
            Template-Based
          </button>
        </div>

        {/* Feature Comparison */}
        {mode === 'smart' && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-700 dark:text-slate-300">
                <p className="font-semibold mb-2">Smart Extraction Features:</p>
                <ul className="list-disc ml-4 space-y-1">
                  <li><strong>No template needed</strong> - Just describe what you want to extract</li>
                  <li><strong>AI-powered mapping</strong> - LLM intelligently identifies and extracts fields</li>
                  <li><strong>Dynamic columns</strong> - AI suggests optimal columns based on content</li>
                  <li><strong>Natural language instructions</strong> - Guide the extraction with plain English</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {mode === 'mapper' && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-700 dark:text-slate-300">
                <p className="font-semibold mb-2">Smart Template Mapper Features:</p>
                <ul className="list-disc ml-4 space-y-1">
                  <li><strong>Custom column mapping</strong> - Provide your own Excel template columns</li>
                  <li><strong>AI-powered data mapping</strong> - LLM maps scraped data to your columns</li>
                  <li><strong>Transparent missing values</strong> - Fields marked as "requires research" instead of null</li>
                  <li><strong>Perfect for predefined templates</strong> - Paste columns from Excel directly</li>
                </ul>
                <p className="mt-3 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-3 py-2 rounded">
                  <strong>💡 Use this when:</strong> You have a predefined list of columns (like from an Excel template) and want AI to map data to them
                </p>
              </div>
            </div>
          </div>
        )}

        {mode === 'template' && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <FileSpreadsheet className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-700 dark:text-slate-300">
                <p className="font-semibold mb-2">Template-Based Extraction Features:</p>
                <ul className="list-disc ml-4 space-y-1">
                  <li><strong>Upload Excel templates</strong> - AI maps data to your custom Excel columns</li>
                  <li><strong>Predefined templates</strong> - Use built-in templates for common sites</li>
                  <li><strong>Consistent structure</strong> - Always get the same fields</li>
                  <li><strong>LLM-powered extraction</strong> - Intelligent data mapping</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div>
          {mode === 'smart' ? (
            <SmartExtractor />
          ) : mode === 'mapper' ? (
            <SmartTemplateMapper />
          ) : (
            <TemplateExtractor sessionId={sessionId} />
          )}
        </div>
      </div>
    </div>
  )
}
