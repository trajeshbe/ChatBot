/**
 * MCP Tools Manager Component
 *
 * Displays and manages available AI agent tools including:
 * - Built-in tools (RAG, Smart Extraction, etc.)
 * - MCP server tools (dynamically discovered)
 * - Tool statistics and categories
 * - Enable/disable tool functionality
 */

import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Search,
  Server,
  Globe,
  FileText,
  Eye,
  Navigation,
  Tag,
  CheckCircle,
  XCircle,
  Activity,
  Info,
  RefreshCw,
  Filter,
  BarChart3
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Tool {
  tool_id: string;
  name: string;
  description: string;
  tags: string[];
  source: string;
  enabled: boolean;
}

interface ToolStatistics {
  total_tools: number;
  enabled_tools: number;
  disabled_tools: number;
  builtin_tools: number;
  mcp_tools: number;
  custom_tools: number;
  total_tags: number;
  top_tags: Array<{ tag: string; count: number }>;
}

interface MCPServer {
  server_id: string;
  name: string;
  enabled: boolean;
  connected: boolean;
  transport: string;
  tools_imported: number;
  tools: string[];
  error?: string;
}

interface MCPStatistics {
  total_servers: number;
  enabled_servers: number;
  connected_servers: number;
  disconnected_servers: number;
  total_external_tools: number;
  servers_with_errors: number;
  health_check_timestamp: string;
}

const getToolIcon = (tags: string[]) => {
  if (tags.includes('rag') || tags.includes('documents')) return FileText;
  if (tags.includes('web scraping')) return Globe;
  if (tags.includes('navigation')) return Navigation;
  if (tags.includes('ocr')) return Eye;
  return Wrench;
};

export const MCPToolsManager: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [toolStats, setToolStats] = useState<ToolStatistics | null>(null);
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);
  const [mcpStats, setMcpStats] = useState<MCPStatistics | null>(null);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'tools' | 'mcp'>('tools');

  useEffect(() => {
    loadData();
  }, [selectedSource, selectedTag, searchQuery]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load tool statistics
      const statsRes = await fetch(`${API_BASE}/api/v1/tools/statistics`);
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setToolStats(stats);
      }

      // Load tools with filters
      const params = new URLSearchParams();
      if (selectedSource !== 'all') params.append('source', selectedSource);
      if (selectedTag !== 'all') params.append('tag', selectedTag);
      if (searchQuery) params.append('search', searchQuery);

      const toolsRes = await fetch(`${API_BASE}/api/v1/tools?${params}`);
      if (toolsRes.ok) {
        const data = await toolsRes.json();
        setTools(data.tools);
      }

      // Load MCP servers
      const mcpServersRes = await fetch(`${API_BASE}/api/v1/mcp/consumer/servers`);
      if (mcpServersRes.ok) {
        const servers = await mcpServersRes.json();
        setMcpServers(servers);
      }

      // Load MCP statistics
      const mcpStatsRes = await fetch(`${API_BASE}/api/v1/mcp/statistics`);
      if (mcpStatsRes.ok) {
        const stats = await mcpStatsRes.json();
        setMcpStats(stats);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = async (toolId: string, currentlyEnabled: boolean) => {
    try {
      const endpoint = currentlyEnabled ? 'disable' : 'enable';
      const res = await fetch(`${API_BASE}/api/v1/tools/${toolId}/${endpoint}`, {
        method: 'POST'
      });

      if (res.ok) {
        await loadData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle tool');
    }
  };

  const toggleMCPServer = async (serverId: string, currentlyEnabled: boolean) => {
    try {
      const endpoint = currentlyEnabled ? 'disable' : 'enable';
      const res = await fetch(`${API_BASE}/api/v1/mcp/consumer/servers/${serverId}/${endpoint}`, {
        method: 'POST'
      });

      if (res.ok) {
        await loadData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle MCP server');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            MCP & Tools Manager
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Manage AI agent tools and MCP server connections
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      {/* View Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <div className="flex space-x-8">
          <button
            onClick={() => setActiveView('tools')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeView === 'tools'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Wrench className="w-4 h-4" />
              <span>Tools</span>
              {toolStats && (
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                  {toolStats.total_tools}
                </span>
              )}
            </div>
          </button>
          <button
            onClick={() => setActiveView('mcp')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeView === 'mcp'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Server className="w-4 h-4" />
              <span>MCP Servers</span>
              {mcpStats && (
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200">
                  {mcpStats.total_servers}
                </span>
              )}
            </div>
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      {activeView === 'tools' && toolStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 dark:text-blue-400">Total Tools</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">{toolStats.total_tools}</p>
              </div>
              <Wrench className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 dark:text-green-400">Enabled</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">{toolStats.enabled_tools}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600 dark:text-orange-400">Built-in</p>
                <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">{toolStats.builtin_tools}</p>
              </div>
              <Activity className="w-8 h-8 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600 dark:text-purple-400">MCP Tools</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">{toolStats.mcp_tools}</p>
              </div>
              <Server className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>
      )}

      {activeView === 'mcp' && mcpStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600 dark:text-purple-400">Total Servers</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">{mcpStats.total_servers}</p>
              </div>
              <Server className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 dark:text-green-400">Connected</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">{mcpStats.connected_servers}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 dark:text-blue-400">External Tools</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">{mcpStats.total_external_tools}</p>
              </div>
              <Wrench className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600 dark:text-red-400">With Errors</p>
                <p className="text-2xl font-bold text-red-900 dark:text-red-100">{mcpStats.servers_with_errors}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
          </div>
        </div>
      )}

      {/* Tools View */}
      {activeView === 'tools' && (
        <>
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Search Tools
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name or description..."
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-800 dark:text-white"
                />
              </div>
            </div>
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Source
              </label>
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-800 dark:text-white"
              >
                <option value="all">All Sources</option>
                <option value="built-in">Built-in</option>
                <option value="mcp">MCP</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            {toolStats && toolStats.top_tags.length > 0 && (
              <div className="min-w-[150px]">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Category
                </label>
                <select
                  value={selectedTag}
                  onChange={(e) => setSelectedTag(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg dark:bg-slate-800 dark:text-white"
                >
                  <option value="all">All Categories</option>
                  {toolStats.top_tags.map((tag) => (
                    <option key={tag.tag} value={tag.tag}>
                      {tag.tag} ({tag.count})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Tools List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tools.map((tool) => {
              const IconComponent = getToolIcon(tool.tags);
              return (
                <div
                  key={tool.tool_id}
                  className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 transition-colors cursor-pointer"
                  onClick={() => setSelectedTool(tool)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <IconComponent className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-slate-900 dark:text-white">{tool.name}</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
                          {tool.description}
                        </p>
                        <div className="flex flex-wrap gap-2 mt-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            tool.source === 'built-in'
                              ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200'
                              : tool.source === 'mcp'
                              ? 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200'
                              : 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200'
                          }`}>
                            {tool.source}
                          </span>
                          {tool.tags.slice(0, 2).map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 text-xs rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleTool(tool.tool_id, tool.enabled);
                      }}
                      className={`ml-4 p-2 rounded-lg ${
                        tool.enabled
                          ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {tool.enabled ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* MCP Servers View */}
      {activeView === 'mcp' && (
        <div className="space-y-4">
          {mcpServers.map((server) => (
            <div
              key={server.server_id}
              className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1">
                  <div className={`p-2 rounded-lg ${
                    server.connected
                      ? 'bg-green-100 dark:bg-green-900'
                      : 'bg-gray-100 dark:bg-gray-800'
                  }`}>
                    <Server className={`w-5 h-5 ${
                      server.connected
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-gray-600 dark:text-gray-400'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900 dark:text-white">{server.name}</h3>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {server.transport}
                      </span>
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {server.tools_imported} tools
                      </span>
                      <span className={`text-sm font-medium ${
                        server.connected
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {server.connected ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>
                    {server.error && (
                      <p className="text-sm text-red-600 dark:text-red-400 mt-1">{server.error}</p>
                    )}
                    {server.tools.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {server.tools.slice(0, 5).map((tool) => (
                          <span
                            key={tool}
                            className="px-2 py-1 text-xs rounded-full bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200"
                          >
                            {tool}
                          </span>
                        ))}
                        {server.tools.length > 5 && (
                          <span className="px-2 py-1 text-xs rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                            +{server.tools.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => toggleMCPServer(server.server_id, server.enabled)}
                  className={`ml-4 px-4 py-2 rounded-lg font-medium ${
                    server.enabled
                      ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  {server.enabled ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>
          ))}

          {mcpServers.length === 0 && (
            <div className="text-center py-12">
              <Server className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400">No MCP servers configured</p>
            </div>
          )}
        </div>
      )}

      {/* Tool Details Modal */}
      {selectedTool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">{selectedTool.name}</h3>
                <button
                  onClick={() => setSelectedTool(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Description</h4>
                  <p className="text-slate-600 dark:text-slate-400">{selectedTool.description}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Tool ID</h4>
                  <code className="px-2 py-1 bg-slate-100 dark:bg-slate-900 rounded text-sm">
                    {selectedTool.tool_id}
                  </code>
                </div>
                <div>
                  <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Source</h4>
                  <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm">
                    {selectedTool.source}
                  </span>
                </div>
                <div>
                  <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedTool.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-full text-sm"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2">Status</h4>
                  <div className="flex items-center space-x-2">
                    {selectedTool.enabled ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                        <span className="text-green-600 dark:text-green-400">Enabled</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        <span className="text-gray-600 dark:text-gray-400">Disabled</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
