import { MessageSquare, Upload, Globe, FileText, BarChart3, FileSpreadsheet, Calculator, Wrench, Sliders, History, Home, Plus, FolderOpen } from 'lucide-react'
import { ThemeToggle } from '@/theme/ThemeToggle'

interface Props {
  activeTab: 'dashboard' | 'chat' | 'upload' | 'scrape' | 'history' | 'evaluation' | 'estimator' | 'tools' | 'weights' | 'library'
  setActiveTab: (tab: 'dashboard' | 'chat' | 'upload' | 'scrape' | 'history' | 'evaluation' | 'estimator' | 'tools' | 'weights' | 'library') => void
  currentUser?: string
  onNewChat?: () => void
}

export default function Sidebar({ activeTab, setActiveTab, currentUser, onNewChat }: Props) {
  const tabs = [
    { id: 'dashboard' as const, icon: Home, label: 'Dashboard' },
    { id: 'chat' as const, icon: MessageSquare, label: 'Chat' },
    { id: 'history' as const, icon: History, label: 'Chat History' },
    { id: 'library' as const, icon: FolderOpen, label: 'Library' },
    { id: 'upload' as const, icon: Upload, label: 'Upload Files' },
    { id: 'scrape' as const, icon: Globe, label: 'Web Scraping' },
    { id: 'estimator' as const, icon: Calculator, label: 'Project Estimator' },
    { id: 'evaluation' as const, icon: BarChart3, label: 'Evaluation' },
    { id: 'tools' as const, icon: Wrench, label: 'Tool Usage' },
    { id: 'weights' as const, icon: Sliders, label: 'Weights Config' },
  ]

  return (
    <div className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-xl flex items-center justify-center shadow-sm">
            <MessageSquare className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">Enterprise AI</h2>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Intelligent Assistant</p>
          </div>
          <ThemeToggle />
        </div>

        {/* Username Display */}
        {currentUser && currentUser !== 'Anonymous' && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
              <div className="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-700 dark:text-primary-300 font-semibold">
                {currentUser.charAt(0).toUpperCase()}
              </div>
              <span className="font-medium">{currentUser}</span>
            </div>
          </div>
        )}
      </div>

      {/* New Chat Button */}
      {onNewChat && (
        <div className="p-3 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => {
              console.log('🆕 [Sidebar] New Chat button clicked')
              onNewChat()
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white font-medium transition-colors shadow-sm hover:shadow-md"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>
      )}

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
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800'
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
