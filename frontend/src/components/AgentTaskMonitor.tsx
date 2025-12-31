import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import AgentWorkspaceFileUpload from './AgentWorkspaceFileUpload';
import ProjectSelector from './ProjectSelector';
import InteractiveTerminal from './InteractiveTerminal';
import { FileText, CheckCircle, XCircle, Loader2, X, Zap, MessageSquare, Wrench, CheckCircle2, AlertCircle, Terminal } from 'lucide-react';
import { useAgentWebSocket } from '../hooks/useAgentWebSocket';

interface AgentTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  task_description: string;
  session_id?: string;
  model: string;
  current_iteration?: number;
  max_iterations: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  result?: string;
  artifacts: string[];
  tools_used: string[];
  llm_calls?: number;
  error?: string;
  error_details?: any;
  created_at: string;
  minio_base_path?: string;  // 🆕 MinIO base path for artifacts folder link
  meta_info?: {
    engine?: string;
    [key: string]: any;
  };
}

interface Document {
  id: string;
  filename: string;
  file_size: number;
  processing_status: string;
  has_embeddings: boolean;
  chunk_count: number;
  created_at: string;
}

interface AgentTaskMonitorProps {
  sessionId?: string;
  currentUser?: {
    id: string;
    username: string;
    role: string;
    department_id?: string;
    team_id?: string;
    department?: string;
    team?: string;
  };
}

// Get or create session ID
const getSessionId = (): string => {
  if (typeof window === 'undefined') return ''

  let sessionId = sessionStorage.getItem('chat_session_id')
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem('chat_session_id', sessionId)
    console.log('🆔 Created new session:', sessionId)
  }
  return sessionId
}

export const AgentTaskMonitor: React.FC<AgentTaskMonitorProps> = ({ currentUser }) => {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedProject, setSelectedProject] = useState<any>(null);

  // Define API_URL before using it in hooks
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // 🆕 WebSocket hook for real-time task streaming
  const {
    events: wsEvents,
    isConnected: wsConnected,
    isComplete: wsComplete,
    taskStatus: wsStatus,
    error: wsError,
    connect: wsConnect,
    disconnect: wsDisconnect,
    reset: wsReset
  } = useAgentWebSocket(API_URL);

  // Form state - 🆕 FIX: Persist taskDescription to sessionStorage
  const [taskDescription, setTaskDescription] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = sessionStorage.getItem('agent_task_draft');
      if (saved) {
        console.log('📝 Restored task draft from sessionStorage');
        return saved;
      }
    }
    return '';
  });
  const [model, setModel] = useState('qwen2.5-coder:7b'); // Will be synced from main chat UI
  const [engine, setEngine] = useState('default'); // 🆕 Engine selection
  const [maxIterations, setMaxIterations] = useState(20);
  const [timeoutSeconds, setTimeoutSeconds] = useState(600);

  // File selection state - which uploaded files to make available to agent
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set()); // File paths for display
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(new Set()); // Document UUIDs for API
  const [uploadedDocuments, setUploadedDocuments] = useState<Document[]>([]);
  const [filesListKey, setFilesListKey] = useState(0); // Force refresh uploaded files list

  // Initialize session ID and sync model from main chat UI
  useEffect(() => {
    const sid = getSessionId();
    setSessionId(sid);

    // Load selected project from localStorage (sync with chat UI)
    if (typeof window !== 'undefined') {
      const savedProjectId = localStorage.getItem('selected_project_id');
      if (savedProjectId) {
        setSelectedProjectId(savedProjectId);
        console.log('📁 [AgentTaskMonitor] Loaded project ID from localStorage:', savedProjectId);
      }

      // ✅ FIX: Sync model selection from main chat UI
      const globalModel = localStorage.getItem('globalSelectedModel');
      if (globalModel) {
        setModel(globalModel);
        console.log('🤖 [AgentTaskMonitor] Synced model from main chat UI:', globalModel);
      }
    }
  }, []);

  // 🆕 FIX: Save taskDescription to sessionStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined' && taskDescription) {
      sessionStorage.setItem('agent_task_draft', taskDescription);
      console.log('💾 Saved task draft to sessionStorage');
    }
  }, [taskDescription]);

  // 🆕 WebSocket connection effect - connect when task is selected
  useEffect(() => {
    if (selectedTask && selectedTask.task_id) {
      console.log('🔌 Connecting WebSocket for task:', selectedTask.task_id);
      wsConnect(selectedTask.task_id);

      // Cleanup: disconnect when task is deselected
      return () => {
        console.log('🔌 Disconnecting WebSocket for task:', selectedTask.task_id);
        wsDisconnect();
      };
    } else {
      // Reset when no task is selected
      wsReset();
    }
  }, [selectedTask, wsConnect, wsDisconnect, wsReset]);

  // Fetch tasks on mount and periodically refresh
  useEffect(() => {
    if (sessionId) {
      fetchTasks();
      const interval = setInterval(fetchTasks, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [sessionId]);

  const fetchTasks = async () => {
    try {
      const params: any = { page: 1, page_size: 50 };
      if (sessionId) {
        params.session_id = sessionId;
      }

      // 🆕 FIX: Include JWT token for user authentication
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await axios.get(`${API_URL}/api/v1/agent/tasks`, { params, headers });
      setTasks(response.data.tasks || []);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  // Toggle file selection for agent workspace
  const toggleFileSelection = (filename: string, documentId?: string) => {
    setSelectedFiles(prev => {
      const newSet = new Set(prev);
      const workspacePath = `/workspace/${filename}`;

      if (newSet.has(workspacePath)) {
        newSet.delete(workspacePath);
      } else {
        newSet.add(workspacePath);
      }
      return newSet;
    });

    // Also track document ID if provided
    if (documentId) {
      setSelectedDocumentIds(prev => {
        const newSet = new Set(prev);
        if (newSet.has(documentId)) {
          newSet.delete(documentId);
        } else {
          newSet.add(documentId);
        }
        return newSet;
      });
    }
  };

  const createTask = async () => {
    if (!taskDescription.trim()) {
      alert('Please enter a task description');
      return;
    }

    setCreating(true);
    try {
      // Enhance task description with file context if files are selected
      let enhancedDescription = taskDescription;
      if (selectedFiles.size > 0) {
        enhancedDescription += `\n\n📂 Available files in /workspace/:\n${Array.from(selectedFiles).map(f => `- ${f}`).join('\n')}`;
      }

      const payload: any = {
        task_description: enhancedDescription,
        session_id: sessionId,
        model,
        engine, // 🆕 Add engine selection
        max_iterations: maxIterations,
        timeout_seconds: timeoutSeconds,
        project_id: selectedProjectId || undefined,
        meta_info: {
          files_available: Array.from(selectedFiles),
          project_id: selectedProjectId,
          engine // 🆕 Add to meta_info for tracking
        }
      };

      // ✅ FIX: Pass document IDs to enable automatic file syncing from MinIO
      if (selectedDocumentIds.size > 0) {
        payload.document_ids = Array.from(selectedDocumentIds);
        console.log('📂 Selected document IDs:', payload.document_ids);
      }

      // 🆕 FIX: Include JWT token for user authentication
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      console.log('[AgentTaskMonitor] Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NULL');

      await axios.post(`${API_URL}/api/v1/agent/tasks`, payload, { headers });

      console.log('✅ Task created successfully');
      setTaskDescription('');
      // 🆕 FIX: Clear saved draft when task is successfully created
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('agent_task_draft');
        console.log('🗑️ Cleared task draft from sessionStorage');
      }
      await fetchTasks();
    } catch (error: any) {
      console.error('Error creating task:', error);
      alert(`Failed to create task: ${error.response?.data?.detail || error.message}`);
    } finally {
      setCreating(false);
    }
  };

  const cancelTask = async (taskId: string) => {
    try {
      // 🆕 FIX: Include JWT token for user authentication
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      await axios.delete(`${API_URL}/api/v1/agent/tasks/${taskId}`, { headers });
      console.log(`🚫 Task ${taskId} cancelled`);
      await fetchTasks();
    } catch (error) {
      console.error('Error cancelling task:', error);
      alert('Failed to cancel task');
    }
  };

  // ✨ NEW: Complete and close terminal (graceful exit for Claude Code CLI)
  const completeAndCloseTerminal = async (taskId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await axios.post(
        `${API_URL}/api/v1/agent/tasks/${taskId}/complete-and-close`,
        {},
        { headers }
      );

      const result = response.data;
      console.log(`✅ Terminal closed successfully for task ${taskId}:`, result);

      // Show beautiful toast notification with all details
      toast.success(
        (t) => (
          <div className="flex flex-col gap-2 py-1">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
              <span className="font-semibold text-base">Terminal Closed Successfully!</span>
            </div>

            <div className="ml-7 space-y-1.5 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-slate-300">Artifacts Found:</span>
                <span className="font-medium text-white">{result.artifacts_found}</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-slate-300">Status:</span>
                <span className="font-medium text-green-400">{result.status}</span>
              </div>

              <div className="pt-2 pb-1 border-t border-slate-600">
                <div className="flex items-start gap-2 bg-indigo-900/40 px-3 py-2 rounded-md">
                  <span className="text-base">🔐</span>
                  <div>
                    <div className="font-semibold text-indigo-300">OAuth Session Preserved!</div>
                    <div className="text-xs text-indigo-400 mt-0.5">No re-login needed next time</div>
                  </div>
                </div>
              </div>

              {result.minio_path && (
                <div className="pt-1">
                  <div className="text-xs text-slate-400 mb-1">📦 Artifacts uploaded to:</div>
                  <div className="text-xs font-mono text-slate-300 bg-slate-800 px-2 py-1.5 rounded break-all">
                    {result.minio_path}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => toast.dismiss(t.id)}
              className="ml-7 mt-2 text-xs text-slate-400 hover:text-white underline self-start"
            >
              Dismiss
            </button>
          </div>
        ),
        {
          duration: 8000,
          style: {
            background: '#1e293b',
            color: '#fff',
            maxWidth: '550px',
            padding: '16px',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
          },
        }
      );

      // Close modal and refresh tasks
      setSelectedTask(null);
      await fetchTasks();
    } catch (error: any) {
      console.error('Error completing task:', error);

      // Show error toast
      toast.error(
        (t) => (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <span className="font-semibold">Failed to Complete Task</span>
            </div>
            <div className="ml-7 text-sm text-slate-300">
              {error.response?.data?.detail || error.message}
            </div>
            <button
              onClick={() => toast.dismiss(t.id)}
              className="ml-7 text-xs text-slate-400 hover:text-white underline self-start"
            >
              Dismiss
            </button>
          </div>
        ),
        {
          duration: 7000,
          style: {
            background: '#1e293b',
            maxWidth: '500px',
            padding: '16px',
          },
        }
      );
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'cancelled': return '🚫';
      case 'running': return '⚙️';
      default: return '⏳';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700';
      case 'failed': return 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700';
      case 'cancelled': return 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-700';
      case 'running': return 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700';
      default: return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700';
    }
  };

  return (
    <div className="container mx-auto p-2 max-w-7xl">
      {/* Project Selector */}
      <div className="bg-white dark:bg-slate-800 rounded shadow-sm p-2 mb-2 border border-slate-200 dark:border-slate-700">
        <h2 className="text-xs font-semibold mb-2 text-slate-700 dark:text-slate-300">📁 Project Context</h2>
        <ProjectSelector
          value={selectedProjectId}
          onChange={(projectId, project) => {
            setSelectedProject(project);
            setSelectedProjectId(projectId);
            // ✅ FIX: Save project ID to localStorage so FileUpload can access it
            if (projectId) {
              localStorage.setItem('selected_project_id', projectId);
              console.log('📁 [AgentTaskMonitor] Saved project ID to localStorage:', projectId);
            } else {
              localStorage.removeItem('selected_project_id');
              console.log('📁 [AgentTaskMonitor] Removed project ID from localStorage');
            }
            setSelectedFiles(new Set());
            setSelectedDocumentIds(new Set()); // Clear selected document IDs
            setUploadedDocuments([]);
            setFilesListKey(prev => prev + 1);
          }}
          currentUser={currentUser}
        />
      </div>

      {/* File Upload & Management Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 mb-2">
        {/* Upload New Files */}
        <div className="bg-white dark:bg-slate-800 rounded shadow-sm p-3 border border-slate-200 dark:border-slate-700">
          <h2 className="text-xs font-semibold mb-2 text-slate-700 dark:text-slate-300">📤 Upload Files to Agent Workspace</h2>
          <div className="scale-90 origin-top max-h-48 pb-2">
            <AgentWorkspaceFileUpload
              sessionId={sessionId || 'default'}  // ✅ Pass sessionId (required)
              projectId={selectedProjectId}  // ✅ Pass selected project from parent
              currentUser={currentUser}
              onUploadComplete={() => {
                // Refresh file list when upload completes
                setFilesListKey(prev => prev + 1);
              }}
            />
          </div>
        </div>

        {/* Browse & Select Uploaded Files */}
        <div className="bg-white dark:bg-slate-800 rounded shadow-sm p-2 border border-slate-200 dark:border-slate-700">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              📁 Select Files ({selectedFiles.size})
            </h2>
            <button
              onClick={() => setFilesListKey(prev => prev + 1)}
              className="text-xs px-2 py-1 text-[#6b9080] dark:text-[#85c4a6] hover:bg-[#f0f7f4] dark:hover:bg-[#2b3d37] rounded"
            >
              🔄
            </button>
          </div>

          {/* Custom file list with checkboxes */}
          <div className="max-h-48 overflow-y-auto space-y-0.5">
            {sessionId ? (
              <UploadedFilesListWithSelection
                sessionId={sessionId}
                projectId={selectedProjectId}
                selectedFiles={selectedFiles}
                onToggleFile={toggleFileSelection}
                onDocumentsLoaded={setUploadedDocuments}
                refreshKey={filesListKey}
              />
            ) : (
              <p className="text-xs text-center py-4 text-slate-500 dark:text-slate-400">Loading...</p>
            )}
          </div>
        </div>
      </div>

      {/* Selected Files Summary */}
      {selectedFiles.size > 0 && (
        <div className="bg-[#f0f7f4] dark:bg-[#2b3d37] rounded p-2 mb-2 border border-[#6b9080] dark:border-[#85c4a6]">
          <h3 className="text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
            📎 Selected ({selectedFiles.size})
          </h3>
          <div className="flex flex-wrap gap-1">
            {Array.from(selectedFiles).map(filePath => (
              <div
                key={filePath}
                className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-white dark:bg-slate-800 rounded border border-[#6b9080] dark:border-[#85c4a6] text-xs"
              >
                <FileText size={10} className="text-[#6b9080] dark:text-[#85c4a6]" />
                <span className="truncate max-w-[150px] text-slate-700 dark:text-slate-300">{filePath.split('/').pop()}</span>
                <button
                  onClick={() => {
                    const filename = filePath.split('/').pop() || '';
                    toggleFileSelection(filename);
                  }}
                  className="text-slate-400 hover:text-red-600"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Task Form */}
      <div className="bg-white dark:bg-slate-800 rounded shadow-sm p-2 mb-2 border border-slate-200 dark:border-slate-700">
        <h2 className="text-xs font-semibold mb-2 text-slate-700 dark:text-slate-300">🎯 Create Task</h2>

        <div className="space-y-2">
          <textarea
            rows={5}
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            placeholder="Describe the task in detail... Be specific about what you want the agent to do."
            className="w-full px-2 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded focus:ring-1 focus:ring-[#6b9080] dark:focus:ring-[#85c4a6] bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
          />

          <div className="grid grid-cols-2 gap-1 mb-1">
            <div>
              <label className="text-[10px] text-slate-500 dark:text-slate-400 mb-0.5 block">Engine</label>
              <select
                value={engine}
                onChange={(e) => setEngine(e.target.value)}
                className="w-full px-2 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              >
                <option value="default">🏠 Default (LangGraph)</option>
                <option value="codex-cli">🤖 Codex CLI (GPT-4)</option>
                <option value="claude-code-cli">🧠 Claude Code CLI</option>
              </select>
            </div>
            <div className="px-2 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 truncate flex items-center">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mr-1">🤖</span>
              <span className="truncate">{model.split(':')[0] || model}</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1">
            <input
              type="number"
              value={maxIterations}
              onChange={(e) => setMaxIterations(parseInt(e.target.value))}
              placeholder="Max Iterations"
              className="w-full px-1 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            />
            <input
              type="number"
              value={timeoutSeconds}
              onChange={(e) => setTimeoutSeconds(parseInt(e.target.value))}
              placeholder="Timeout (sec)"
              className="w-full px-1 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            />
          </div>

          <button
            onClick={createTask}
            disabled={creating || !taskDescription.trim()}
            className="w-full px-3 py-1.5 text-xs bg-[#6b9080] hover:bg-[#527566] dark:bg-[#85c4a6] dark:hover:bg-[#b3dbc7] text-white font-medium rounded disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {creating ? (
              <>
                <Loader2 className="animate-spin" size={12} />
                Creating...
              </>
            ) : (
              <>🚀 Create</>
            )}
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="bg-white dark:bg-slate-800 rounded shadow-sm p-2 border border-slate-200 dark:border-slate-700">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xs font-semibold text-slate-700 dark:text-slate-300">📋 Tasks ({tasks.length})</h2>
          <button
            onClick={fetchTasks}
            className="text-xs px-2 py-1 text-[#6b9080] dark:text-[#85c4a6] hover:bg-[#f0f7f4] dark:hover:bg-[#2b3d37] rounded"
          >
            🔄
          </button>
        </div>

        {tasks.length === 0 ? (
          <p className="text-xs text-center py-8 text-slate-500 dark:text-slate-400">
            No tasks yet. Create your first agent task above!
          </p>
        ) : (
          <div className="space-y-2">
            {tasks.map((task) => (
              <div
                key={task.task_id}
                className="border border-slate-200 dark:border-slate-600 rounded p-2 hover:border-[#6b9080] dark:hover:border-[#85c4a6] cursor-pointer text-xs transition-colors"
                onClick={() => setSelectedTask(task)}
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 mb-1">
                      <span className="text-sm">{getStatusIcon(task.status)}</span>
                      <span className={`px-1.5 py-0.5 rounded-full text-xs border ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    <p className="truncate font-medium text-slate-700 dark:text-slate-300">{task.task_description.split('\n')[0]}</p>
                  </div>
                  {(task.status === 'pending' || task.status === 'running') && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        cancelTask(task.task_id);
                      }}
                      className="ml-2 px-2 py-0.5 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900 rounded"
                    >
                      Cancel
                    </button>
                  )}
                </div>

                <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600 dark:text-slate-400">
                  <div>🤖 {task.model.split(':')[0]}</div>
                  <div>📅 {new Date(task.created_at).toLocaleTimeString()}</div>
                  {task.current_iteration && <div>🔄 {task.current_iteration}/{task.max_iterations}</div>}
                  {task.duration_seconds && <div>⏱️ {task.duration_seconds.toFixed(1)}s</div>}
                  {task.llm_calls && <div>💬 {task.llm_calls} calls</div>}
                  {task.tools_used && task.tools_used.length > 0 && <div>🔧 {task.tools_used.length} tools</div>}
                </div>

                {task.result && (
                  <div className="mt-1 p-1 bg-slate-50 dark:bg-slate-900 rounded text-xs">
                    <p className="line-clamp-2 text-slate-700 dark:text-slate-300">{task.result}</p>
                  </div>
                )}

                {task.error && (
                  <div className="mt-1 p-1 bg-red-50 dark:bg-red-900 rounded text-xs text-red-700 dark:text-red-300">
                    <p className="line-clamp-2">Error: {task.error}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">Task Details</h3>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* 🆕 FIX: Display Task ID for tracing */}
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Task ID</label>
                <div className="mt-1 font-mono text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 px-2 py-1 rounded">
                  {selectedTask.task_id}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Status</label>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-lg">{getStatusIcon(selectedTask.status)}</span>
                  <span className={`px-2 py-1 rounded text-sm border ${getStatusColor(selectedTask.status)}`}>
                    {selectedTask.status}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Task Description</label>
                <p className="mt-1 text-sm whitespace-pre-wrap text-slate-700 dark:text-slate-300">{selectedTask.task_description}</p>
              </div>

              {/* ✅ Interactive Terminal for Claude CLI */}
              {selectedTask.meta_info?.engine === 'claude_code_cli' && selectedTask.status === 'running' && (
                <div className="my-4">
                  <div className="mb-3 flex items-center justify-between bg-indigo-50 dark:bg-indigo-900/30 px-4 py-3 rounded-lg border border-indigo-200 dark:border-indigo-800">
                    <div className="flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                      <div>
                        <h4 className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
                          Claude Code Interactive Terminal
                        </h4>
                        <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-0.5">
                          🔐 OAuth session preserved - no re-login needed next time
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => completeAndCloseTerminal(selectedTask.task_id)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm flex items-center gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      Complete & Close Terminal
                    </button>
                  </div>
                  <InteractiveTerminal taskId={selectedTask.task_id} />
                </div>
              )}

              {/* 🆕 Real-Time Event Stream (WebSocket) */}
              {wsEvents.length > 0 && (
                <div className="border border-indigo-200 dark:border-indigo-800 rounded-lg overflow-hidden">
                  <div className="bg-indigo-50 dark:bg-indigo-900/30 px-3 py-2 border-b border-indigo-200 dark:border-indigo-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                      <span className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
                        Real-Time Event Stream
                      </span>
                      {wsConnected && (
                        <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                          Connected
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-indigo-600 dark:text-indigo-400">
                      {wsEvents.length} events
                    </span>
                  </div>

                  <div className="max-h-96 overflow-y-auto bg-slate-50 dark:bg-slate-900/50">
                    <div className="p-3 space-y-2">
                      {wsEvents.map((event, idx) => {
                        // Render different event types with appropriate styling
                        // ✅ NEW: Handle terminal output from Claude CLI
                        if (event.type === 'terminal_output') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-1 bg-slate-900 dark:bg-slate-950 rounded border border-slate-700 dark:border-slate-800">
                              <Terminal className="w-3 h-3 mt-0.5 text-green-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-mono text-green-400 whitespace-pre-wrap break-words">
                                  {event.output}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'thinking') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                              <MessageSquare className="w-4 h-4 mt-0.5 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                                  Thinking (Iteration {event.iteration})
                                </div>
                                <div className="text-xs text-slate-700 dark:text-slate-300 mt-1 italic">
                                  {event.thought}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'tool_use') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-800">
                              <Wrench className="w-4 h-4 mt-0.5 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium text-amber-700 dark:text-amber-300">
                                  Using Tool: {event.tool_name}
                                </div>
                                <div className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-mono bg-white dark:bg-slate-900 p-2 rounded border border-slate-200 dark:border-slate-700 overflow-x-auto">
                                  {event.tool_input}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'tool_result') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                              <CheckCircle2 className="w-4 h-4 mt-0.5 text-green-600 dark:text-green-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium text-green-700 dark:text-green-300">
                                  Tool Result: {event.tool_name}
                                </div>
                                <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                                  {event.result}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'artifact') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                              <FileText className="w-4 h-4 mt-0.5 text-purple-600 dark:text-purple-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium text-purple-700 dark:text-purple-300">
                                  Artifact Created
                                </div>
                                <a
                                  href={event.download_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-purple-600 dark:text-purple-400 hover:underline mt-1 flex items-center gap-1"
                                >
                                  📎 {event.artifact_name}
                                </a>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'status_update') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                              <Loader2 className="w-4 h-4 mt-0.5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium text-blue-700 dark:text-blue-300">
                                  Status: {event.status}
                                </div>
                                <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                                  {event.message}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'error') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                              <AlertCircle className="w-4 h-4 mt-0.5 text-red-600 dark:text-red-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium text-red-700 dark:text-red-300">
                                  Error
                                </div>
                                <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                                  {event.error}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (event.type === 'completed') {
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-green-100 dark:bg-green-900/30 rounded border-2 border-green-500 dark:border-green-600">
                              <CheckCircle className="w-5 h-5 mt-0.5 text-green-600 dark:text-green-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-semibold text-green-700 dark:text-green-300">
                                  Task {event.status}
                                </div>
                                <div className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                                  Duration: {event.duration_seconds?.toFixed(2)}s | Iterations: {event.iterations}
                                </div>
                                {event.result && (
                                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-2 p-2 bg-white dark:bg-slate-900 rounded">
                                    {event.result}
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        } else {
                          // Generic event fallback
                          return (
                            <div key={idx} className="flex gap-2 items-start p-2 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                {event.type}
                              </div>
                            </div>
                          );
                        }
                      })}
                    </div>
                  </div>
                </div>
              )}

              {selectedTask.result && (
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Result</label>
                  <div className="mt-1 p-3 bg-slate-50 dark:bg-slate-900 rounded text-sm whitespace-pre-wrap text-slate-700 dark:text-slate-300">
                    {selectedTask.result}
                  </div>
                </div>
              )}

              {selectedTask.error && (
                <div>
                  <label className="text-xs font-medium text-red-500 dark:text-red-400">Error</label>
                  <div className="mt-1 p-3 bg-red-50 dark:bg-red-900 rounded text-sm whitespace-pre-wrap text-red-700 dark:text-red-300">
                    {selectedTask.error}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Model</label>
                  <p className="mt-1 text-slate-700 dark:text-slate-300">{selectedTask.model}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Iterations</label>
                  <p className="mt-1 text-slate-700 dark:text-slate-300">{selectedTask.current_iteration || 0} / {selectedTask.max_iterations}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">LLM Calls</label>
                  <p className="mt-1 text-slate-700 dark:text-slate-300">{selectedTask.llm_calls || 0}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Duration</label>
                  <p className="mt-1 text-slate-700 dark:text-slate-300">{selectedTask.duration_seconds ? `${selectedTask.duration_seconds.toFixed(2)}s` : 'N/A'}</p>
                </div>
              </div>

              {selectedTask.tools_used && selectedTask.tools_used.length > 0 && (
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Tools Used</label>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {selectedTask.tools_used.map((tool, idx) => (
                      <span key={idx} className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-700 dark:text-slate-300">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Code Viewer - Extract Python code from conversation history */}
              {selectedTask.meta_info?.conversation_history && (() => {
                const codeBlocks: Array<{code: string; iteration: number}> = [];
                const history = selectedTask.meta_info.conversation_history;

                // Extract execute_python tool calls
                history.forEach((msg: any, idx: number) => {
                  if (msg.role === 'assistant' && msg.content?.startsWith('TOOL_CALL: execute_python')) {
                    try {
                      const argsMatch = msg.content.match(/ARGS: ({[\s\S]*?})/);
                      if (argsMatch) {
                        const args = JSON.parse(argsMatch[1]);
                        if (args.code) {
                          codeBlocks.push({
                            code: args.code,
                            iteration: Math.floor(idx / 2) + 1
                          });
                        }
                      }
                    } catch (e) {
                      console.error('Failed to parse code:', e);
                    }
                  }
                });

                if (codeBlocks.length > 0) {
                  return (
                    <div>
                      <label className="text-xs font-medium text-slate-500 dark:text-slate-400">
                        💻 Executed Code ({codeBlocks.length})
                      </label>
                      <div className="mt-1 space-y-2">
                        {codeBlocks.map((block, idx) => (
                          <div key={idx} className="border border-slate-300 dark:border-slate-600 rounded overflow-hidden">
                            <div className="flex items-center justify-between px-2 py-1 bg-slate-100 dark:bg-slate-700 border-b border-slate-300 dark:border-slate-600">
                              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                                Iteration {block.iteration}
                              </span>
                              <button
                                onClick={() => {
                                  const blob = new Blob([block.code], { type: 'text/plain' });
                                  const url = URL.createObjectURL(blob);
                                  const a = document.createElement('a');
                                  a.href = url;
                                  a.download = `code_iteration_${block.iteration}.py`;
                                  a.click();
                                  URL.revokeObjectURL(url);
                                }}
                                className="px-2 py-0.5 bg-[#6b9080] hover:bg-[#527566] dark:bg-[#85c4a6] dark:hover:bg-[#b3dbc7] text-white text-xs rounded flex items-center gap-1 transition-colors"
                                title="Download code"
                              >
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                .py
                              </button>
                            </div>
                            <pre className="p-2 bg-slate-50 dark:bg-slate-900 text-xs overflow-x-auto">
                              <code className="text-slate-800 dark:text-slate-200 font-mono">{block.code}</code>
                            </pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              })()}

              {selectedTask.artifacts && selectedTask.artifacts.length > 0 && (
                <div>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">
                    📁 Artifacts ({selectedTask.artifacts.length})
                  </label>
                  <div className="mt-1 space-y-1">
                    {selectedTask.artifacts.map((artifact, idx) => {
                      // Extract filename from path (e.g., /artifacts/file.png -> file.png)
                      const filename = artifact.split('/').pop() || artifact;
                      const downloadUrl = `http://localhost:8000/api/v1/agent/tasks/${selectedTask.task_id}/artifacts/${filename}`;

                      return (
                        <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-900 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                          <span className="text-xs text-slate-700 dark:text-slate-300 font-mono truncate flex-1">
                            {artifact}
                          </span>
                          <a
                            href={downloadUrl}
                            download={filename}
                            className="ml-2 px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded flex items-center gap-1 transition-colors"
                            title={`Download ${filename}`}
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Download
                          </a>
                        </div>
                      );
                    })}
                  </div>

                  {/* 🆕 MinIO Browser Link */}
                  {selectedTask.minio_base_path && (
                    <div className="mt-2">
                      <a
                        href={`http://localhost:9001/browser/documents/${selectedTask.minio_base_path}artifacts/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-3 py-2 bg-[#6b9080] hover:bg-[#527566] dark:bg-[#85c4a6] dark:hover:bg-[#b3dbc7] text-white text-xs rounded transition-colors"
                        title="Open artifacts folder in MinIO browser"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                        Open Artifacts Folder in MinIO
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper component to render uploaded files list with selection checkboxes
const UploadedFilesListWithSelection: React.FC<{
  sessionId: string;
  projectId?: string;
  selectedFiles: Set<string>;
  onToggleFile: (filename: string, documentId?: string) => void;  // ✅ FIX: Pass document ID
  onDocumentsLoaded: (docs: Document[]) => void;
  refreshKey: number;
}> = ({ sessionId, projectId, selectedFiles, onToggleFile, onDocumentsLoaded, refreshKey }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const loadDocuments = async () => {
      setLoading(true);
      try {
        let url: string;

        // If project is selected, fetch ALL project files (from any session)
        if (projectId) {
          url = `${API_URL}/api/v1/documents?project_id=${projectId}`;
          console.log(`📂 Loading all files for project ${projectId}`);
        } else {
          // Otherwise, fetch files from current session only
          url = `${API_URL}/api/v1/sessions/${sessionId}/documents`;
        }

        const response = await axios.get(url);
        // Handle both response formats:
        // - /api/v1/documents?project_id=X returns array directly
        // - /api/v1/sessions/{id}/documents returns { documents: [...] }
        const docs = Array.isArray(response.data) ? response.data : (response.data.documents || []);
        setDocuments(docs);
        onDocumentsLoaded(docs);
        console.log(`✅ Loaded ${docs.length} files for ${projectId ? 'project' : 'session'}`);
      } catch (error) {
        console.error('Error loading documents:', error);
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    };

    if (sessionId || projectId) {
      loadDocuments();
    }
  }, [sessionId, projectId, refreshKey]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="animate-spin text-[#6b9080] dark:text-[#85c4a6]" size={20} />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <p className="text-xs text-center py-4 text-slate-500 dark:text-slate-400">
        No files uploaded yet. Upload files above to select them for agent tasks.
      </p>
    );
  }

  return (
    <>
      {documents.map((doc) => {
        const workspacePath = `/workspace/${doc.filename}`;
        const isSelected = selectedFiles.has(workspacePath);

        return (
          <div
            key={doc.id}
            onClick={() => onToggleFile(doc.filename, doc.id)}  // ✅ FIX: Pass document ID
            className={`flex items-center gap-1 p-1 rounded cursor-pointer text-xs transition-colors ${
              isSelected
                ? 'bg-[#f0f7f4] dark:bg-[#2b3d37] border border-[#6b9080] dark:border-[#85c4a6]'
                : 'bg-slate-50 dark:bg-slate-700 border border-transparent hover:bg-slate-100 dark:hover:bg-slate-600'
            }`}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => {}} // Handled by parent div onClick
              className="w-3 h-3 accent-[#6b9080] dark:accent-[#85c4a6] flex-shrink-0"
            />
            <FileText className="text-slate-400 flex-shrink-0" size={12} />
            <div className="flex-1 min-w-0 flex items-center justify-between gap-1">
              <span className="font-medium truncate text-slate-700 dark:text-slate-300">{doc.filename}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0">{formatFileSize(doc.file_size)}</span>
            </div>
            {doc.has_embeddings && (
              <span className="text-xs text-green-600 dark:text-green-400 flex-shrink-0">✓</span>
            )}
          </div>
        );
      })}
    </>
  );
};

export default AgentTaskMonitor;
