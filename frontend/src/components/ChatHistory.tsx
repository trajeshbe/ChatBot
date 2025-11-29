import React, { useState, useEffect } from 'react';
import { MessageSquare, Trash2, Search, Clock, Calendar, ChevronRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { generateMissingTitles, ChatSession } from '@/utils/sessionTitles';

interface GroupedSessions {
  today: ChatSession[];
  yesterday: ChatSession[];
  lastWeek: ChatSession[];
  lastMonth: ChatSession[];
  older: ChatSession[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ChatHistoryProps {
  onSessionSelect?: (sessionId: string) => void;
}

export default function ChatHistory({ onSessionSelect }: ChatHistoryProps = {}) {
  const { user, token } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [filteredSessions, setFilteredSessions] = useState<ChatSession[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch chat sessions
  useEffect(() => {
    fetchChatSessions();
  }, [user, token]);

  // Filter sessions based on search
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredSessions(sessions);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = sessions.filter(
        (session) =>
          (session.title?.toLowerCase().includes(query)) ||
          (session.preview?.toLowerCase().includes(query)) ||
          (session.session_id?.toLowerCase().includes(query))
      );
      setFilteredSessions(filtered);
    }
  }, [searchQuery, sessions]);

  const fetchChatSessions = async () => {
    if (!token) {
      setError('Not authenticated');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/sessions`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Fetched chat sessions:', data);

      // Transform sessions and auto-generate titles for untitled ones (using shared utility)
      const sessionsData = data.sessions || [];
      const sessionsWithTitles = await generateMissingTitles(sessionsData, token);

      setSessions(sessionsWithTitles);
      setFilteredSessions(sessionsWithTitles);
    } catch (err) {
      console.error('Error fetching chat sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load chat history');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!token) return;
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      // Remove from local state
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));

      // Also remove from localStorage if current session
      const currentSessionId = sessionStorage.getItem('chat_session_id');
      if (currentSessionId === sessionId) {
        sessionStorage.removeItem('chat_session_id');
        localStorage.removeItem(`chat_messages_${sessionId}`);
      }
    } catch (err) {
      console.error('Error deleting session:', err);
      alert('Failed to delete conversation');
    }
  };

  const loadSession = (sessionId: string) => {
    // Set the session ID in sessionStorage
    sessionStorage.setItem('chat_session_id', sessionId);

    // Use callback if provided, otherwise reload
    if (onSessionSelect) {
      onSessionSelect(sessionId);
    } else {
      // Reload the page to load the conversation
      window.location.reload();
    }
  };

  const groupSessionsByDate = (sessions: ChatSession[]): GroupedSessions => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    const grouped: GroupedSessions = {
      today: [],
      yesterday: [],
      lastWeek: [],
      lastMonth: [],
      older: [],
    };

    sessions.forEach((session) => {
      const sessionDate = new Date(session.last_activity);

      if (sessionDate >= today) {
        grouped.today.push(session);
      } else if (sessionDate >= yesterday) {
        grouped.yesterday.push(session);
      } else if (sessionDate >= lastWeek) {
        grouped.lastWeek.push(session);
      } else if (sessionDate >= lastMonth) {
        grouped.lastMonth.push(session);
      } else {
        grouped.older.push(session);
      }
    });

    return grouped;
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const renderSessionGroup = (title: string, sessions: ChatSession[]) => {
    if (sessions.length === 0) return null;

    return (
      <div className="mb-6">
        <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-4 mb-2">
          {title}
        </h3>
        <div className="space-y-1">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className="group flex items-center justify-between px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg cursor-pointer transition-colors"
            >
              <div
                className="flex-1 min-w-0"
                onClick={() => loadSession(session.session_id)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <MessageSquare className="w-4 h-4 text-slate-400 dark:text-slate-500 flex-shrink-0" />
                  <h4 className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {session.title || 'Untitled Conversation'}
                  </h4>
                </div>

                {session.preview && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate ml-6">
                    {session.preview}
                  </p>
                )}

                <div className="flex items-center gap-3 text-xs text-slate-400 dark:text-slate-500 mt-1 ml-6">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(session.last_activity)}
                  </span>
                  {session.message_count !== undefined && (
                    <span>{session.message_count} messages</span>
                  )}
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(session.session_id);
                }}
                className="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-all"
                title="Delete conversation"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
          <p className="text-sm text-slate-600 dark:text-slate-400">Loading chat history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <p className="text-sm text-red-600 dark:text-red-400 mb-2">{error}</p>
          <button
            onClick={fetchChatSessions}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const groupedSessions = groupSessionsByDate(filteredSessions);

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Chat History</h2>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto py-4">
        {filteredSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <MessageSquare className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-3" />
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {searchQuery ? 'No conversations found' : 'No chat history yet'}
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
              {searchQuery ? 'Try a different search term' : 'Start a conversation to see it here'}
            </p>
          </div>
        ) : (
          <>
            {renderSessionGroup('Today', groupedSessions.today)}
            {renderSessionGroup('Yesterday', groupedSessions.yesterday)}
            {renderSessionGroup('Last 7 Days', groupedSessions.lastWeek)}
            {renderSessionGroup('Last 30 Days', groupedSessions.lastMonth)}
            {renderSessionGroup('Older', groupedSessions.older)}
          </>
        )}
      </div>
    </div>
  );
}
