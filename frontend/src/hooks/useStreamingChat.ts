/**
 * useStreamingChat - React Hook for Server-Sent Events (SSE) Streaming
 *
 * Provides ChatGPT-like real-time streaming of LLM responses.
 * Connects to backend SSE endpoint and manages streaming state.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

interface StreamingConfig {
  modelId?: string;
  sessionId?: string;
  projectId?: string;
  maxTokens?: number;
  temperature?: number;
  // 🆕 RAG configuration - identical to query endpoint
  unifiedConfig?: string;  // JSON string with complete RAG config
  topK?: number;
  similarityThreshold?: number;
  minSimilarityThreshold?: number;
  noRelevantDocsThreshold?: number;
  semanticWeight?: number;
  keywordWeight?: number;
  enableEvaluation?: boolean;
  enabledTools?: string;
  selectedAgent?: string;
  conversationHistory?: string;
}

interface UseStreamingChatReturn {
  streamingContent: string;
  isStreaming: boolean;
  error: string | null;
  sources: any[];  // 🆕 RAG sources
  modelUsed: string | null;  // 🆕 Model that was used
  startStreaming: (query: string, config?: StreamingConfig) => void;
  stopStreaming: () => void;
  resetStream: () => void;
}

export const useStreamingChat = (apiUrl: string = 'http://localhost:8000'): UseStreamingChatReturn => {
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sources, setSources] = useState<any[]>([]);  // 🆕 RAG sources
  const [modelUsed, setModelUsed] = useState<string | null>(null);  // 🆕 Model used

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const maxReconnectAttempts = 3;

  /**
   * Stop the current streaming connection
   */
  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsStreaming(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  /**
   * Reset streaming state
   */
  const resetStream = useCallback(() => {
    stopStreaming();
    setStreamingContent('');
    setError(null);
    setSources([]);  // 🆕 Clear sources
    setModelUsed(null);  // 🆕 Clear model
  }, [stopStreaming]);

  /**
   * Start streaming from the SSE endpoint
   */
  const startStreaming = useCallback((
    query: string,
    config: StreamingConfig = {}
  ) => {
    // Reset state
    setStreamingContent('');
    setError(null);
    setSources([]);  // 🆕 Clear previous sources
    setModelUsed(null);  // 🆕 Clear previous model
    setIsStreaming(true);

    // Build query parameters (🆕 now includes unified_config and all RAG params)
    console.log('🔍 useStreamingChat: config.projectId =', config.projectId);

    const params = new URLSearchParams({
      query: query,
      ...(config.modelId && { model_id: config.modelId }),
      ...(config.sessionId && { session_id: config.sessionId }),
      ...(config.projectId && { project_id: config.projectId }),
      ...(config.maxTokens && { max_tokens: config.maxTokens.toString() }),
      ...(config.temperature && { temperature: config.temperature.toString() }),
      // 🆕 RAG configuration parameters
      ...(config.unifiedConfig && { unified_config: config.unifiedConfig }),
      ...(config.topK !== undefined && { top_k: config.topK.toString() }),
      ...(config.similarityThreshold !== undefined && { similarity_threshold: config.similarityThreshold.toString() }),
      ...(config.minSimilarityThreshold !== undefined && { min_similarity_threshold: config.minSimilarityThreshold.toString() }),
      ...(config.noRelevantDocsThreshold !== undefined && { no_relevant_docs_threshold: config.noRelevantDocsThreshold.toString() }),
      ...(config.semanticWeight !== undefined && { semantic_weight: config.semanticWeight.toString() }),
      ...(config.keywordWeight !== undefined && { keyword_weight: config.keywordWeight.toString() }),
      ...(config.enableEvaluation !== undefined && { enable_evaluation: config.enableEvaluation.toString() }),
      ...(config.enabledTools && { enabled_tools: config.enabledTools }),
      ...(config.selectedAgent && { selected_agent: config.selectedAgent }),
      ...(config.conversationHistory && { conversation_history: config.conversationHistory })
    });

    const streamUrl = `${apiUrl}/api/v1/chat/stream?${params.toString()}`;

    console.log('🌊 Starting SSE stream:', streamUrl);
    console.log('🔍 project_id in params:', params.get('project_id'));

    // Create EventSource connection
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    // Handle message events (content chunks)
    eventSource.addEventListener('message', (e) => {
      try {
        const data = JSON.parse(e.data);

        if (data.type === 'content') {
          // Append content chunk
          setStreamingContent(prev => prev + data.content);
          if (data.model) {
            setModelUsed(data.model);
          }
        }
      } catch (err) {
        console.error('Error parsing SSE message:', err);
      }
    });

    // 🆕 Handle sources event (RAG sources sent before content)
    eventSource.addEventListener('sources', (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'sources' && data.sources) {
          console.log('📚 Received RAG sources:', data.sources.length);
          setSources(data.sources);
          if (data.model) {
            setModelUsed(data.model);
          }
        }
      } catch (err) {
        console.error('Error parsing sources event:', err);
      }
    });

    // Handle completion
    eventSource.addEventListener('done', (e) => {
      console.log('✅ Stream completed:', e.data);
      setIsStreaming(false);
      stopStreaming();
    });

    // Handle errors
    eventSource.addEventListener('error', (e: any) => {
      console.error('❌ SSE error:', e);

      try {
        if (e.data) {
          const errorData = JSON.parse(e.data);
          setError(errorData.error || 'Streaming error occurred');
        }
      } catch (parseErr) {
        // EventSource error object
        if (eventSource.readyState === EventSource.CLOSED) {
          setError('Connection closed unexpectedly');
        } else if (eventSource.readyState === EventSource.CONNECTING) {
          // Attempting to reconnect
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current += 1;
            console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
            return; // Let EventSource handle reconnection
          } else {
            setError(`Failed to connect after ${maxReconnectAttempts} attempts`);
          }
        } else {
          setError('Streaming error occurred');
        }
      }

      setIsStreaming(false);
      stopStreaming();
    });

    // Handle generic error event
    eventSource.onerror = (e) => {
      console.error('❌ EventSource error:', e);

      if (eventSource.readyState === EventSource.CLOSED) {
        // Connection closed, attempt reconnect if within limits
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`Attempting reconnect ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);

          // Exponential backoff: 1s, 2s, 4s
          const backoffMs = Math.pow(2, reconnectAttemptsRef.current - 1) * 1000;

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Reconnecting after backoff...');
            // EventSource automatically reconnects when created again
            // For simplicity, we let the user retry manually
            setError('Connection lost. Please try again.');
            setIsStreaming(false);
          }, backoffMs);
        } else {
          setError(`Connection failed after ${maxReconnectAttempts} attempts`);
          setIsStreaming(false);
        }
      }
    };
  }, [apiUrl, stopStreaming]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, [stopStreaming]);

  return {
    streamingContent,
    isStreaming,
    error,
    sources,  // 🆕 RAG sources
    modelUsed,  // 🆕 Model used
    startStreaming,
    stopStreaming,
    resetStream
  };
};

export default useStreamingChat;
