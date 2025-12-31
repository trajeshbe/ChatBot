/**
 * Brain View Component
 *
 * Real-time context visualization showing:
 * - Routing decisions
 * - Conversation history
 * - Tools executed (query-time + document processing)
 * - Documents retrieved
 * - Performance metrics
 */

import React, { useState } from 'react';
import {
  Brain,
  X,
  Activity,
  MessageSquare,
  Wrench,
  FileText,
  Zap,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

interface BrainViewProps {
  debugContext: DebugContext | null;
  isOpen: boolean;
  onToggle: () => void;
}

interface DebugContext {
  routing_decision: {
    strategy: string;
    reason: string;
    strategy_weights: Record<string, number>;
    classification_confidence: number;
  };
  conversation_history: {
    messages_used: number;
    note: string;
  };
  tools_executed: {
    query_time_tools: Tool[];
    document_processing_tools: Tool[];
  };
  documents_retrieved: {
    total_chunks: number;
    chunks: Chunk[];
  };
  performance_metrics: {
    total_latency_ms: number;
    breakdown: Record<string, number>;
    model_used: string;
    tokens_used: number;
  };
}

interface Tool {
  tool_id: string;
  tool_name: string;
  category?: string;
  operation?: string;
  status: string;
  latency_ms: number;
  order?: number;
  quality_score?: number;
  error_message?: string;
  document_id?: string;
  created_at?: string;
}

interface Chunk {
  document_id: string;
  filename: string;
  similarity_score: number;
  memory_type?: string;
  content_preview: string;
}

export const BrainView: React.FC<BrainViewProps> = ({ debugContext, isOpen, onToggle }) => {
  const [activeTab, setActiveTab] = useState<'routing' | 'history' | 'tools' | 'documents' | 'performance'>('tools');

  const tabs = [
    { id: 'routing', label: 'Routing', icon: Activity },
    { id: 'history', label: 'History', icon: MessageSquare },
    { id: 'tools', label: 'Tools', icon: Wrench },
    { id: 'documents', label: 'Docs', icon: FileText },
    { id: 'performance', label: 'Perf', icon: Zap },
  ];

  return (
    <>
      {/* Toggle Button - Only show after first LLM query (when debugContext exists) */}
      {debugContext && (
        <button
          onClick={onToggle}
          className="fixed top-4 right-4 z-50 bg-purple-600 text-white p-3 rounded-full shadow-lg hover:bg-purple-700 transition-all"
          title={isOpen ? 'Close Brain View' : 'Open Brain View'}
        >
          <Brain className="w-5 h-5" />
        </button>
      )}

      {/* Side Panel */}
      <div className={`fixed top-0 right-0 h-full bg-white border-l border-gray-200 shadow-2xl transition-all duration-300 ${isOpen ? 'w-96' : 'w-0'} overflow-hidden z-40`}>
        {isOpen && (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="w-6 h-6" />
                <div>
                  <h2 className="font-bold text-lg">Brain View</h2>
                  <p className="text-xs text-purple-200">Debug Context Inspector</p>
                </div>
              </div>
              <button
                onClick={onToggle}
                className="p-1 hover:bg-purple-800 rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 bg-gray-50">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex-1 px-2 py-3 text-xs font-medium transition-colors flex flex-col items-center gap-1 ${
                      activeTab === tab.id
                        ? 'bg-white text-purple-600 border-b-2 border-purple-600'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {!debugContext ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-8">
                  <Brain className="w-16 h-16 text-gray-300 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">No Debug Context Yet</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Send a query to generate debug context and see detailed information about:
                  </p>
                  <ul className="text-xs text-gray-600 space-y-2 text-left">
                    <li className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-purple-500" />
                      <span>Routing decisions and strategy selection</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-purple-500" />
                      <span>Tools executed (query-time + document processing)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-purple-500" />
                      <span>Documents retrieved with similarity scores</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-purple-500" />
                      <span>Performance metrics and latency breakdown</span>
                    </li>
                  </ul>
                  <div className="mt-6 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <p className="text-xs text-purple-700">
                      <strong>Tip:</strong> Make sure Brain View is enabled in Settings → Strategy tab
                    </p>
                  </div>
                </div>
              ) : activeTab === 'routing' && debugContext && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-sm text-gray-900 mb-3">Routing Decision</h3>

                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-blue-900 mb-1">Strategy</div>
                    <div className="text-sm font-bold text-blue-700">{debugContext.routing_decision.strategy}</div>
                  </div>

                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-gray-700 mb-1">Reason</div>
                    <div className="text-xs text-gray-600">{debugContext.routing_decision.reason}</div>
                  </div>

                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-purple-900 mb-2">Confidence</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${debugContext.routing_decision.classification_confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-purple-700">
                        {(debugContext.routing_decision.classification_confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-gray-700 mb-2">Strategy Weights</div>
                    <div className="space-y-1">
                      {Object.entries(debugContext.routing_decision.strategy_weights).slice(0, 5).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center text-xs">
                          <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                          <span className="font-mono text-gray-900">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'history' && debugContext && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-sm text-gray-900 mb-3">Conversation History</h3>

                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-blue-900 mb-1">Messages Used</div>
                    <div className="text-2xl font-bold text-blue-700">{debugContext.conversation_history.messages_used}</div>
                  </div>

                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-gray-700 mb-1">Note</div>
                    <div className="text-xs text-gray-600">{debugContext.conversation_history.note}</div>
                  </div>
                </div>
              )}

              {activeTab === 'tools' && debugContext && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-sm text-gray-900 mb-3">Tools Executed</h3>

                  {/* Query-Time Tools */}
                  <div>
                    <div className="text-xs font-semibold text-purple-700 mb-2 flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Query Execution Tools
                    </div>
                    <div className="space-y-2">
                      {debugContext.tools_executed?.query_time_tools?.map((tool) => (
                        <div key={tool.tool_id} className="bg-white border border-purple-200 rounded-lg p-2">
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              {tool.status === 'success' ? (
                                <CheckCircle className="w-3 h-3 text-green-600" />
                              ) : (
                                <XCircle className="w-3 h-3 text-red-600" />
                              )}
                              <span className="text-xs font-medium text-gray-900">{tool.tool_name}</span>
                            </div>
                            <span className="text-xs font-mono text-gray-500">{tool.latency_ms.toFixed(1)}ms</span>
                          </div>
                          {tool.order && (
                            <div className="text-xs text-gray-500">Order: {tool.order}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Document Processing Tools */}
                  {debugContext.tools_executed?.document_processing_tools?.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-blue-700 mb-2 flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        Document Processing Tools
                      </div>
                      <div className="space-y-2">
                        {debugContext.tools_executed?.document_processing_tools?.map((tool) => (
                          <div key={tool.tool_id} className="bg-blue-50 border border-blue-200 rounded-lg p-2">
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-2">
                                {tool.status === 'success' ? (
                                  <CheckCircle className="w-3 h-3 text-green-600" />
                                ) : (
                                  <XCircle className="w-3 h-3 text-red-600" />
                                )}
                                <span className="text-xs font-medium text-gray-900">{tool.tool_name}</span>
                              </div>
                              <span className="text-xs font-mono text-gray-500">{tool.latency_ms.toFixed(1)}ms</span>
                            </div>
                            {tool.category && (
                              <div className="text-xs text-gray-600 mt-1">Category: {tool.category.replace(/_/g, ' ')}</div>
                            )}
                            {tool.operation && (
                              <div className="text-xs text-gray-600">Operation: {tool.operation}</div>
                            )}
                            {tool.quality_score !== undefined && (
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-xs text-gray-600">Quality:</span>
                                <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                                  <div
                                    className="bg-blue-500 h-1.5 rounded-full"
                                    style={{ width: `${tool.quality_score * 100}%` }}
                                  />
                                </div>
                                <span className="text-xs font-mono text-gray-600">{(tool.quality_score * 100).toFixed(0)}%</span>
                              </div>
                            )}
                            {tool.error_message && (
                              <div className="text-xs text-red-600 mt-1 bg-red-50 p-1 rounded">Error: {tool.error_message}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'documents' && debugContext && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-sm text-gray-900 mb-3">Documents Retrieved</h3>

                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-blue-900 mb-1">Total Chunks</div>
                    <div className="text-2xl font-bold text-blue-700">{debugContext.documents_retrieved.total_chunks}</div>
                  </div>

                  <div className="space-y-2">
                    {debugContext.documents_retrieved.chunks.map((chunk, idx) => (
                      <div key={idx} className="bg-white border border-gray-200 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-900 truncate">{chunk.filename}</span>
                          <span className="text-xs font-mono text-purple-600">{(chunk.similarity_score * 100).toFixed(0)}%</span>
                        </div>
                        {chunk.memory_type && (
                          <div className="text-xs text-gray-500 mb-1">Type: {chunk.memory_type}</div>
                        )}
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded mt-2">{chunk.content_preview}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'performance' && debugContext && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-sm text-gray-900 mb-3">Performance Metrics</h3>

                  <div className="bg-green-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-green-900 mb-1">Total Latency</div>
                    <div className="text-2xl font-bold text-green-700">{debugContext.performance_metrics.total_latency_ms.toFixed(0)}ms</div>
                  </div>

                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-blue-900 mb-1">Model Used</div>
                    <div className="text-sm font-semibold text-blue-700">{debugContext.performance_metrics.model_used}</div>
                  </div>

                  <div className="bg-purple-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-purple-900 mb-1">Tokens Used</div>
                    <div className="text-2xl font-bold text-purple-700">{debugContext.performance_metrics.tokens_used}</div>
                  </div>

                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs font-medium text-gray-700 mb-2">Latency Breakdown</div>
                    <div className="space-y-2">
                      {Object.entries(debugContext.performance_metrics.breakdown).map(([key, value]) => (
                        value > 0 && (
                          <div key={key} className="flex items-center gap-2">
                            <Clock className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-600 flex-1">{key.replace(/_/g, ' ')}</span>
                            <span className="text-xs font-mono text-gray-900">{value.toFixed(1)}ms</span>
                          </div>
                        )
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
};
