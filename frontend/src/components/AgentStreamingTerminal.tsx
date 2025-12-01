/**
 * Agent Streaming Terminal Component
 *
 * Displays real-time agent execution:
 * - Tool calls and results
 * - Iteration progress
 * - Cost tracking
 * - Status indicators
 */

import React, { useState, useEffect, useRef } from 'react';

interface AgentEvent {
  type: string;
  task_id: string;
  session_id: string;
  timestamp: string;
  data: any;
}

interface AgentStreamingTerminalProps {
  taskId: string;
  sessionId: string;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export const AgentStreamingTerminal: React.FC<AgentStreamingTerminalProps> = ({
  taskId,
  sessionId,
  onComplete,
  onError
}) => {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [status, setStatus] = useState<'running' | 'completed' | 'failed'>('running');
  const [currentIteration, setCurrentIteration] = useState(0);
  const [maxIterations, setMaxIterations] = useState(20);
  const [totalCost, setTotalCost] = useState(0);
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [events]);

  // TODO: Connect to WebSocket for real-time events
  // For now, we'll simulate with polling
  useEffect(() => {
    // This will be replaced with WebSocket connection
    const ws = connectToAgentEvents(sessionId, taskId);

    ws.onmessage = (event: MessageEvent) => {
      const agentEvent: AgentEvent = JSON.parse(event.data);
      handleAgentEvent(agentEvent);
    };

    return () => {
      if (ws) ws.close();
    };
  }, [sessionId, taskId]);

  const connectToAgentEvents = (sessionId: string, taskId: string): any => {
    // TODO: Implement actual WebSocket connection
    // For now, return a mock WebSocket
    return {
      onmessage: null,
      close: () => {}
    };
  };

  const handleAgentEvent = (event: AgentEvent) => {
    setEvents(prev => [...prev, event]);

    switch (event.type) {
      case 'agent_started':
        setStatus('running');
        setMaxIterations(event.data.max_iterations || 20);
        break;

      case 'iteration_started':
        setCurrentIteration(event.data.iteration);
        break;

      case 'tool_execution':
        // Tool execution event
        break;

      case 'agent_completed':
        setStatus('completed');
        if (onComplete) {
          onComplete(event.data);
        }
        break;

      case 'agent_failed':
        setStatus('failed');
        if (onError) {
          onError(event.data.error);
        }
        break;

      case 'budget_limit_reached':
        setStatus('failed');
        if (onError) {
          onError(event.data.reason);
        }
        break;
    }

    // Track cost
    if (event.data.cost) {
      setTotalCost(prev => prev + event.data.cost);
    }
  };

  const getStatusColor = (): string => {
    switch (status) {
      case 'running': return 'text-primary-600 dark:text-primary-400';
      case 'completed': return 'text-green-600 dark:text-green-400';
      case 'failed': return 'text-red-600 dark:text-red-400';
    }
  };

  const getStatusIcon = (): string => {
    switch (status) {
      case 'running': return '⏳';
      case 'completed': return '✅';
      case 'failed': return '❌';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const renderEvent = (event: AgentEvent, index: number) => {
    switch (event.type) {
      case 'agent_started':
        return (
          <div key={index} className="mb-2">
            <span className="text-primary-500">🚀 Agent started</span>
            <div className="text-xs text-slate-500 dark:text-slate-400 ml-4">
              Task ID: {event.task_id}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 ml-4">
              Agent: {event.data.agent_type}
            </div>
            {event.data.estimated_cost && (
              <div className="text-xs text-slate-500 dark:text-slate-400 ml-4">
                Estimated cost: ${event.data.estimated_cost.toFixed(2)}
              </div>
            )}
          </div>
        );

      case 'iteration_started':
        return (
          <div key={index} className="mb-2">
            <span className="text-purple-500">
              🔄 Iteration {event.data.iteration}/{event.data.max_iterations}
            </span>
          </div>
        );

      case 'tool_execution':
        return (
          <div key={index} className="mb-2">
            <span className="text-green-500">🔧 Tool: {event.data.tool}</span>
            {event.data.args && (
              <div className="text-xs text-slate-500 dark:text-slate-400 ml-4 mt-1">
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(event.data.args, null, 2)}
                </pre>
              </div>
            )}
          </div>
        );

      case 'tool_result':
        return (
          <div key={index} className="mb-2">
            <span className="text-gray-400">📤 Result:</span>
            <div className="text-xs text-slate-600 dark:text-slate-300 ml-4 mt-1 bg-gray-100 dark:bg-slate-800 p-2 rounded">
              <pre className="whitespace-pre-wrap">
                {typeof event.data.result === 'string'
                  ? event.data.result
                  : JSON.stringify(event.data.result, null, 2)}
              </pre>
            </div>
          </div>
        );

      case 'agent_completed':
        return (
          <div key={index} className="mb-2">
            <span className="text-green-500 font-semibold">
              ✅ Task completed successfully
            </span>
            <div className="text-xs text-slate-500 dark:text-slate-400 ml-4">
              Iterations: {event.data.iterations}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 ml-4">
              Artifacts: {event.data.artifacts || 0}
            </div>
            {event.data.cost !== undefined && (
              <div className="text-xs text-slate-500 dark:text-slate-400 ml-4">
                Cost: ${event.data.cost.toFixed(2)}
              </div>
            )}
          </div>
        );

      case 'agent_failed':
        return (
          <div key={index} className="mb-2">
            <span className="text-red-500 font-semibold">
              ❌ Task failed
            </span>
            <div className="text-xs text-red-400 ml-4">
              Error: {event.data.error}
            </div>
          </div>
        );

      case 'budget_limit_reached':
        return (
          <div key={index} className="mb-2">
            <span className="text-orange-500 font-semibold">
              ⚠️ Budget limit reached
            </span>
            <div className="text-xs text-orange-400 ml-4">
              {event.data.reason}
            </div>
          </div>
        );

      default:
        return (
          <div key={index} className="mb-2 text-gray-400">
            <span className="text-xs">[{event.type}]</span> {JSON.stringify(event.data)}
          </div>
        );
    }
  };

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden bg-white dark:bg-slate-800">
      {/* Header */}
      <div className="bg-slate-100 dark:bg-slate-900 px-4 py-2 flex items-center justify-between border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center space-x-3">
          <span className={`font-medium ${getStatusColor()}`}>
            {getStatusIcon()} Agent Execution
          </span>
          {status === 'running' && (
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Iteration {currentIteration}/{maxIterations}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-4 text-xs">
          {totalCost > 0 && (
            <span className="text-slate-600 dark:text-slate-400">
              Cost: ${totalCost.toFixed(2)}
            </span>
          )}
          <span className="text-slate-600 dark:text-slate-400">
            Task: {taskId.slice(0, 8)}...
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      {status === 'running' && maxIterations > 0 && (
        <div className="bg-slate-50 dark:bg-slate-900 px-4 py-2">
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
            <div
              className="bg-primary-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${(currentIteration / maxIterations) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Terminal Content */}
      <div
        ref={terminalRef}
        className="p-4 h-96 overflow-y-auto font-mono text-sm bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200"
      >
        {events.length === 0 ? (
          <div className="text-gray-400 dark:text-gray-500 text-center py-8">
            Waiting for agent events...
          </div>
        ) : (
          events.map((event, index) => (
            <div key={index} className="mb-1">
              <span className="text-gray-400 text-xs mr-2">
                [{formatTimestamp(event.timestamp)}]
              </span>
              {renderEvent(event, index)}
            </div>
          ))
        )}

        {status === 'running' && (
          <div className="text-gray-400 animate-pulse">
            <span className="inline-block">▊</span>
          </div>
        )}
      </div>
    </div>
  );
};
