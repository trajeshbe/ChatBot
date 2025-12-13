/**
 * useAgentWebSocket - React Hook for WebSocket connection to agent tasks
 *
 * Provides Claude Code-like real-time visualization of agent execution.
 * Manages WebSocket connection lifecycle and event streaming.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Event types streamed from the WebSocket
 */
export interface AgentEvent {
  type: 'connection' | 'status_update' | 'thinking' | 'tool_use' | 'tool_result' | 'artifact' | 'completed' | 'error';
  timestamp: string;
  [key: string]: any;
}

export interface ConnectionEvent extends AgentEvent {
  type: 'connection';
  task_id: string;
  status: string;
}

export interface StatusUpdateEvent extends AgentEvent {
  type: 'status_update';
  status: string;
  message: string;
}

export interface ThinkingEvent extends AgentEvent {
  type: 'thinking';
  thought: string;
  iteration: number;
}

export interface ToolUseEvent extends AgentEvent {
  type: 'tool_use';
  tool_name: string;
  tool_input: string;
  iteration: number;
}

export interface ToolResultEvent extends AgentEvent {
  type: 'tool_result';
  tool_name: string;
  result: string;
  success: boolean;
  iteration: number;
}

export interface ArtifactEvent extends AgentEvent {
  type: 'artifact';
  artifact_path: string;
  artifact_name: string;
  artifact_type: string;
  download_url: string;
}

export interface CompletedEvent extends AgentEvent {
  type: 'completed';
  status: 'completed' | 'failed' | 'cancelled';
  result: string;
  error?: string;
  artifacts: string[];
  duration_seconds: number;
  iterations: number;
}

export interface ErrorEvent extends AgentEvent {
  type: 'error';
  error: string;
  iteration?: number;
}

interface UseAgentWebSocketReturn {
  /** All events received from the WebSocket */
  events: AgentEvent[];

  /** Current connection status */
  isConnected: boolean;

  /** Is task completed/failed/cancelled */
  isComplete: boolean;

  /** Latest task status */
  taskStatus: string | null;

  /** Latest error message */
  error: string | null;

  /** Connect to WebSocket for a task */
  connect: (taskId: string) => void;

  /** Disconnect from WebSocket */
  disconnect: () => void;

  /** Clear all events and reset state */
  reset: () => void;

  /** Get events of a specific type */
  getEventsByType: <T extends AgentEvent>(type: string) => T[];
}

/**
 * Custom hook for managing WebSocket connection to agent tasks
 *
 * @param apiUrl - Base API URL (default: http://localhost:8000)
 * @returns WebSocket connection state and controls
 *
 * @example
 * ```tsx
 * const { events, isConnected, connect, disconnect } = useAgentWebSocket();
 *
 * useEffect(() => {
 *   connect('task-abc123');
 *   return () => disconnect();
 * }, [taskId]);
 *
 * // Render events
 * events.map(event => {
 *   switch(event.type) {
 *     case 'thinking':
 *       return <div>Agent thinking: {event.thought}</div>
 *     case 'tool_use':
 *       return <div>Using tool: {event.tool_name}</div>
 *   }
 * });
 * ```
 */
export const useAgentWebSocket = (
  apiUrl: string = 'http://localhost:8000'
): UseAgentWebSocketReturn => {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const maxReconnectAttempts = 3;

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  /**
   * Reset all state
   */
  const reset = useCallback(() => {
    disconnect();
    setEvents([]);
    setIsComplete(false);
    setTaskStatus(null);
    setError(null);
  }, [disconnect]);

  /**
   * Connect to WebSocket for a task
   */
  const connect = useCallback((taskId: string) => {
    // Close existing connection
    disconnect();

    // Reset state
    setEvents([]);
    setIsComplete(false);
    setTaskStatus(null);
    setError(null);

    // Build WebSocket URL
    const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
    const socketUrl = `${wsUrl}/api/v1/agent/tasks/${taskId}/ws`;

    console.log('🔌 Connecting to WebSocket:', socketUrl);

    // Create WebSocket connection
    const ws = new WebSocket(socketUrl);
    wsRef.current = ws;

    // Connection opened
    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    // Message received
    ws.onmessage = (event) => {
      try {
        const data: AgentEvent = JSON.parse(event.data);

        console.log('📨 WebSocket event:', data.type, data);

        // Add event to list
        setEvents(prev => [...prev, data]);

        // Update state based on event type
        switch (data.type) {
          case 'connection':
            setTaskStatus('connected');
            break;

          case 'status_update':
            const statusEvent = data as StatusUpdateEvent;
            setTaskStatus(statusEvent.status);
            break;

          case 'completed':
            const completedEvent = data as CompletedEvent;
            setTaskStatus(completedEvent.status);
            setIsComplete(true);

            if (completedEvent.error) {
              setError(completedEvent.error);
            }
            break;

          case 'error':
            const errorEvent = data as ErrorEvent;
            setError(errorEvent.error);
            break;
        }
      } catch (err) {
        console.error('❌ Error parsing WebSocket message:', err);
      }
    };

    // Connection closed
    ws.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      // Attempt reconnection if not intentional close
      if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current += 1;
        const backoffMs = Math.pow(2, reconnectAttemptsRef.current - 1) * 1000;

        console.log(`🔄 Reconnecting in ${backoffMs}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

        reconnectTimeoutRef.current = setTimeout(() => {
          connect(taskId);
        }, backoffMs);
      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setError(`Failed to connect after ${maxReconnectAttempts} attempts`);
      }
    };

    // Connection error
    ws.onerror = (event) => {
      console.error('❌ WebSocket error:', event);
      setError('WebSocket connection error');
    };
  }, [apiUrl, disconnect]);

  /**
   * Get events of a specific type
   */
  const getEventsByType = useCallback(<T extends AgentEvent>(type: string): T[] => {
    return events.filter(e => e.type === type) as T[];
  }, [events]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    events,
    isConnected,
    isComplete,
    taskStatus,
    error,
    connect,
    disconnect,
    reset,
    getEventsByType
  };
};

export default useAgentWebSocket;
