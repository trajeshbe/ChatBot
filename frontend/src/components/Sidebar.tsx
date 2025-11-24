import { MessageSquare, Upload, Globe, FileText, BarChart3, FileSpreadsheet, Calculator, Wrench, Sliders } from 'lucide-react'

interface Props {
  activeTab: 'chat' | 'upload' | 'scrape' | 'extract' | 'evaluation' | 'estimator' | 'tools' | 'weights'
  setActiveTab: (tab: 'chat' | 'upload' | 'scrape' | 'extract' | 'evaluation' | 'estimator' | 'tools' | 'weights') => void
  currentUser?: string
}

export default function Sidebar({ activeTab, setActiveTab, currentUser }: Props) {
  const tabs = [
    { id: 'chat' as const, icon: MessageSquare, label: 'Chat' },
    { id: 'upload' as const, icon: Upload, label: 'Upload Files' },
    { id: 'scrape' as const, icon: Globe, label: 'Web Scraping' },
    { id: 'extract' as const, icon: FileSpreadsheet, label: 'Data Extraction' },
    { id: 'estimator' as const, icon: Calculator, label: 'Project Estimator' },
    { id: 'evaluation' as const, icon: BarChart3, label: 'Evaluation' },
    { id: 'tools' as const, icon: Wrench, label: 'Tool Usage' },
    { id: 'weights' as const, icon: Sliders, label: 'Weights Config' },
  ]

  return (
    <div className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-sm">
            <MessageSquare className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">RAG Bot</h2>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Enterprise AI</p>
          </div>
        </div>

        {/* Username Display */}
        {currentUser && currentUser !== 'Anonymous' && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
              <div className="w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center text-emerald-700 dark:text-emerald-300 font-semibold">
                {currentUser.charAt(0).toUpperCase()}
              </div>
              <span className="font-medium">{currentUser}</span>
            </div>
          </div>
        )}
      </div>

      <nav className="flex-1 p-3 overflow-y-auto">
        <div className="space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
                  isActive
                    ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </nav>

      <div className="p-3 border-t border-slate-200 dark:border-slate-800">
        <a
          href="/admin"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50"
        >
          <FileText className="w-4 h-4" />
          <span className="font-medium">Admin</span>
        </a>
      </div>
    </div>
  )
}
