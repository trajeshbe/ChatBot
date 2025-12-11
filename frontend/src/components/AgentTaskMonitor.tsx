import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FileUpload from './FileUpload';
import ProjectSelector from './ProjectSelector';
import { FileText, CheckCircle, XCircle, Loader2, X } from 'lucide-react';

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

  // Form state
  const [taskDescription, setTaskDescription] = useState('');
  const [model, setModel] = useState('qwen2.5-coder:7b'); // Will be synced from main chat UI
  const [maxIterations, setMaxIterations] = useState(20);
  const [timeoutSeconds, setTimeoutSeconds] = useState(600);

  // File selection state - which uploaded files to make available to agent
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set()); // File paths for display
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(new Set()); // Document UUIDs for API
  const [uploadedDocuments, setUploadedDocuments] = useState<Document[]>([]);
  const [filesListKey, setFilesListKey] = useState(0); // Force refresh uploaded files list

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

      const response = await axios.get(`${API_URL}/api/v1/agent/tasks`, { params });
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
        max_iterations: maxIterations,
        timeout_seconds: timeoutSeconds,
        project_id: selectedProjectId || undefined,
        meta_info: {
          files_available: Array.from(selectedFiles),
          project_id: selectedProjectId
        }
      };

      // ✅ FIX: Pass document IDs to enable automatic file syncing from MinIO
      if (selectedDocumentIds.size > 0) {
        payload.document_ids = Array.from(selectedDocumentIds);
        console.log('📂 Selected document IDs:', payload.document_ids);
      }

      await axios.post(`${API_URL}/api/v1/agent/tasks`, payload);

      console.log('✅ Task created successfully');
      setTaskDescription('');
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
      await axios.delete(`${API_URL}/api/v1/agent/tasks/${taskId}`);
      console.log(`🚫 Task ${taskId} cancelled`);
      await fetchTasks();
    } catch (error) {
      console.error('Error cancelling task:', error);
      alert('Failed to cancel task');
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
          <h2 className="text-xs font-semibold mb-2 text-slate-700 dark:text-slate-300">📤 Upload Files</h2>
          <div className="scale-90 origin-top max-h-48 pb-2">
            <FileUpload
              currentUser={currentUser}
              sessionId={sessionId}
              projectId={selectedProjectId}  // ✅ Pass selected project from parent
              hideProjectSelector={true}  // ✅ Hide internal selector (we have one above)
              compact={true}  // ✅ Use compact mode for better scaling
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

          <div className="grid grid-cols-3 gap-1">
            <div className="px-2 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 truncate flex items-center">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mr-1">🤖</span>
              <span className="truncate">{model.split(':')[0] || model}</span>
            </div>
            <input
              type="number"
              value={maxIterations}
              onChange={(e) => setMaxIterations(parseInt(e.target.value))}
              placeholder="Iterations"
              className="w-full px-1 py-1 text-xs border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            />
            <input
              type="number"
              value={timeoutSeconds}
              onChange={(e) => setTimeoutSeconds(parseInt(e.target.value))}
              placeholder="Timeout"
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
                      const argsMatch = msg.content.match(/ARGS: ({.*})/s);
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
