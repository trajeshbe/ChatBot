import { MessageSquare, Upload, Globe, FileText } from 'lucide-react'

interface Props {
  activeTab: 'chat' | 'upload' | 'scrape'
  setActiveTab: (tab: 'chat' | 'upload' | 'scrape') => void
}

export default function Sidebar({ activeTab, setActiveTab }: Props) {
  const tabs = [
    { id: 'chat' as const, icon: MessageSquare, label: 'Chat' },
    { id: 'upload' as const, icon: Upload, label: 'Upload Files' },
    { id: 'scrape' as const, icon: Globe, label: 'Web Scraping' },
  ]

  return (
    <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col">
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-400 rounded-lg flex items-center justify-center">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 dark:text-white">RAG Bot</h2>
            <p className="text-xs text-slate-500">Enterprise Edition</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-slate-200 dark:border-slate-700">
        <div className="text-xs text-slate-500 space-y-1">
          <p>Tech Stack:</p>
          <ul className="list-disc list-inside text-[10px] space-y-0.5">
            <li>vLLM + llama.cpp</li>
            <li>pgvector + MinIO</li>
            <li>Redis VSS Cache</li>
            <li>Prefect + LangGraph</li>
            <li>Istio + Envoy</li>
            <li>OTEL + Grafana</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
