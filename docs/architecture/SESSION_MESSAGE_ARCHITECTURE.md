# Session and Message Management Architecture

**Date**: 2025-11-28
**Status**: ✅ Implemented (DB-First with localStorage Cache)
**Purpose**: Comprehensive guide to session/message traceability and data flow

---

## 🎯 Overview

This document provides a complete, unambiguous architecture for session and message management in the Enterprise RAG Chatbot, ensuring full traceability from user interaction to database persistence.

---

## 📊 Database Schema

### **Entity Relationship Diagram**

```
users (PostgreSQL)
  ├── id (UUID, PK)
  ├── username (VARCHAR, UNIQUE)
  ├── email (VARCHAR, UNIQUE)
  └── role (VARCHAR)
      ↓ (1:N)
chat_sessions
  ├── id (UUID, PK)                    ← AUTO-GENERATED
  ├── session_id (VARCHAR, UNIQUE)      ← USER-PROVIDED STRING (e.g., "session-1732123456789-abc123")
  ├── user_id (UUID, FK → users.id)
  ├── title (VARCHAR, NULLABLE)
  ├── created_at (TIMESTAMPTZ)
  ├── updated_at (TIMESTAMPTZ)
  ├── last_activity (TIMESTAMPTZ)
  ├── is_active (BOOLEAN)
  └── meta_info (JSON)
      ↓ (1:N)
conversation_messages
  ├── id (UUID, PK)
  ├── session_id (UUID, FK → chat_sessions.id)  ← CRITICAL: References chat_sessions.id (UUID), NOT session_id (VARCHAR)
  ├── role (VARCHAR: 'user' | 'assistant')
  ├── content (TEXT)
  ├── model_id (VARCHAR)
  ├── model_name (VARCHAR)
  ├── prompt_tokens (INTEGER)
  ├── completion_tokens (INTEGER)
  ├── total_tokens (INTEGER)
  ├── latency_ms (FLOAT)
  ├── cost_usd (FLOAT)
  ├── sources (JSON)
  ├── created_at (TIMESTAMPTZ)
  └── meta_info (JSON)
      ↓ (1:N)
evaluation_results, human_feedback (linked by message_id)
```

---

## 🔑 Key Concepts

### **Session ID vs Chat Session ID**

This is **CRITICAL** for understanding traceability:

| Field | Type | Purpose | Example | Location |
|-------|------|---------|---------|----------|
| `chat_sessions.session_id` | VARCHAR(255) | **User-facing identifier** | `"session-1732123456-abc123"` | URL, frontend state, localStorage |
| `chat_sessions.id` | UUID | **Internal database primary key** | `123e4567-e89b-12d3-a456-426614174000` | Database relationships ONLY |
| `conversation_messages.session_id` | UUID (FK) | **References `chat_sessions.id`** | Same UUID as `chat_sessions.id` | Database relationships |

**Why Two IDs?**
- **session_id (VARCHAR)**: Human-readable, client-generated, used in APIs and URLs
- **id (UUID)**: Database normalization, foreign key relationships, internal integrity

---

## 🌊 Data Flow Architecture

### **1. User Sends Message (Frontend → Backend)**

```mermaid
User types message in ChatInterface
↓
Frontend: handleSendMessage()
↓
POST /api/v1/query
  ├── query: "Hello"
  ├── session_id: "session-1732123456-abc123"  ← VARCHAR string
  └── model_id: "gpt-4"
```

### **2. Backend Processing (main.py:490)**

```python
# Step 1: Parse request
query = "Hello"
session_id = "session-1732123456-abc123"  # VARCHAR string from client

# Step 2: Process query with LLM
result = await enhanced_rag_agent.run(query, session_id, user_preferences)

# Step 3: MESSAGE PERSISTENCE (main.py:643-705)
if session_id:
    # 3a. Get or create chat_sessions record
    chat_session = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    chat_session = chat_session.scalar_one_or_none()

    if not chat_session:
        chat_session = ChatSession(
            id=uuid4(),                    # AUTO: Database PK (UUID)
            session_id=session_id,         # FROM CLIENT: VARCHAR string
            user_id=user_id,
            created_at=now(),
            last_activity=now(),
            is_active=True
        )
        db.add(chat_session)
        await db.flush()  # Get chat_session.id

    # 3b. Save user message
    user_message = ConversationMessage(
        id=uuid4(),
        session_id=chat_session.id,       # CRITICAL: Use UUID, not VARCHAR
        role='user',
        content=query,
        created_at=now()
    )
    db.add(user_message)

    # 3c. Save assistant response
    assistant_message = ConversationMessage(
        id=uuid4(),
        session_id=chat_session.id,       # CRITICAL: Use UUID, not VARCHAR
        role='assistant',
        content=result['answer'],
        sources=result['sources'],
        model_id=result['model'],
        model_name=result['model_used'],
        total_tokens=result['tokens_used'],
        latency_ms=latency_ms,
        created_at=now()
    )
    db.add(assistant_message)

    await db.commit()  # Persist to PostgreSQL

# Step 4: Return response to frontend
return {
    "answer": result['answer'],
    "sources": result['sources'],
    "model_used": result['model_used'],
    "tokens_used": result['tokens_used'],
    "latency_ms": latency_ms
}
```

### **3. Frontend Updates State**

```typescript
// ChatInterfaceEnhanced.tsx:555-730
const handleSendMessage = async () => {
  // 1. Optimistic UI update
  setMessages(prev => [...prev, userMessage]);

  // 2. Send to backend
  const response = await fetch('/api/v1/query', {
    method: 'POST',
    body: formData  // Contains session_id
  });

  // 3. Add assistant response to UI
  setMessages(prev => [...prev, assistantMessage]);

  // 4. Save to localStorage (CACHE ONLY)
  saveMessages(sessionId, messages);
  // ↑ IMPORTANT: This is a performance cache, NOT source of truth
  // Database is the source of truth
};
```

---

## 🔄 Session Loading Flow

### **When User Clicks Chat History Item**

```typescript
// ChatHistory.tsx:154-165
const loadSession = (sessionId: string) => {
  // 1. Store session_id (VARCHAR) in sessionStorage
  sessionStorage.setItem('chat_session_id', sessionId);

  // 2. Trigger session-changed event
  onSessionSelect(sessionId);
};

// index.tsx:126-132
onSessionSelect={(sessionId) => {
  setActiveTab('chat');
  window.dispatchEvent(new CustomEvent('session-changed', {
    detail: { sessionId }
  }));
}

// ChatInterfaceEnhanced.tsx:388-440
useEffect(() => {
  const handleSessionChanged = async (event: CustomEvent) => {
    const loadSessionId = event.detail?.sessionId;  // VARCHAR string

    // 1. Fetch from DATABASE (source of truth)
    const response = await fetch(
      `/api/v1/sessions/${loadSessionId}/messages`
    );

    if (response.ok) {
      const data = await response.json();
      setMessages(data.messages);  // Load from DB
    } else {
      // 2. Fallback to localStorage cache
      const cached = loadMessages(loadSessionId);
      setMessages(cached);
    }
  };

  window.addEventListener('session-changed', handleSessionChanged);
}, []);
```

### **Backend Session Messages Endpoint**

```python
# main.py:1302-1351
@app.get("/api/v1/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):  # VARCHAR string
    # 1. Find chat_sessions record by session_id (VARCHAR)
    session = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = session.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    # 2. Get messages using chat_sessions.id (UUID)
    messages = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session.id)  # UUID FK
        .order_by(ConversationMessage.created_at.asc())
    )

    # 3. Return formatted messages
    return {
        "session_id": session_id,  # VARCHAR (user-facing)
        "title": session.title,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "sources": msg.sources,
                "model_used": msg.model_name or msg.model_id,
                "tokens_used": msg.total_tokens,
                "latency_ms": msg.latency_ms,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }
```

---

## 📍 Complete Traceability Matrix

| Layer | Component | Session Identifier | Message Storage | Purpose |
|-------|-----------|-------------------|-----------------|---------|
| **Frontend** | Browser | `sessionStorage['chat_session_id']` = VARCHAR | `localStorage[session_id]` | Performance cache |
| **API Layer** | REST Endpoint | URL param `{session_id}` = VARCHAR | Request body | Client-server communication |
| **Backend** | FastAPI | `session_id: str` = VARCHAR | FormData | Request handling |
| **Database** | chat_sessions | `session_id` = VARCHAR (UNIQUE) | N/A | User-facing identifier |
| **Database** | chat_sessions | `id` = UUID (PK) | N/A | Internal identifier |
| **Database** | conversation_messages | `session_id` = UUID (FK) | `content`, `sources`, etc. | Message persistence |
| **Database** | audit_logs | `session_id` = UUID (FK) | N/A | Audit trail |

### **Traceability Example**

```
User Action: Click history item "are you there?"
   ↓
Frontend: session_id = "session-1764131365470-lw4n60yx5" (VARCHAR)
   ↓
API Call: GET /api/v1/sessions/session-1764131365470-lw4n60yx5/messages
   ↓
Backend: Query chat_sessions WHERE session_id = 'session-1764131365470-lw4n60yx5'
   ↓
Database: Find chat_sessions.id = 'a1b2c3d4-...' (UUID)
   ↓
Backend: Query conversation_messages WHERE session_id = 'a1b2c3d4-...' (UUID FK)
   ↓
Database: Return all messages with session_id = 'a1b2c3d4-...'
   ↓
API Response: { session_id: "session-1764131365470-lw4n60yx5", messages: [...] }
   ↓
Frontend: setMessages(data.messages)
   ↓
User sees: Full conversation history
```

---

## 🗂️ Legacy Tables (Not Currently Used)

### **messages (OLD)**
- **Table**: `messages`
- **Structure**: conversation_id (UUID FK → conversations.id)
- **Status**: ❌ Not used in current implementation
- **Reason**: Replaced by `conversation_messages` for better session management

### **conversations (OLD)**
- **Table**: `conversations`
- **Structure**: session_id (VARCHAR)
- **Status**: ❌ Not used in current implementation
- **Reason**: Functionality merged into `chat_sessions`

**Decision**: Keep these tables for backward compatibility but do not use them in new code.

---

## 🔐 Database Constraints & Cascading

```sql
-- chat_sessions
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
  → If user deleted, sessions remain but user_id = NULL

-- conversation_messages
FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
  → If chat_session deleted, all messages automatically deleted

-- evaluation_results
FOREIGN KEY (message_id) REFERENCES conversation_messages(id) ON DELETE CASCADE
  → If message deleted, all evaluation results automatically deleted

-- human_feedback
FOREIGN KEY (message_id) REFERENCES conversation_messages(id) ON DELETE CASCADE
  → If message deleted, all feedback automatically deleted

-- audit_logs
FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL
  → If chat_session deleted, audit logs remain but session_id = NULL
```

---

## 🔍 Query Examples for Tracing

### **Find all messages for a session (by VARCHAR session_id)**
```sql
SELECT
    cm.role,
    cm.content,
    cm.model_name,
    cm.created_at
FROM conversation_messages cm
JOIN chat_sessions cs ON cm.session_id = cs.id
WHERE cs.session_id = 'session-1764131365470-lw4n60yx5'
ORDER BY cm.created_at ASC;
```

### **Find all sessions for a user**
```sql
SELECT
    cs.session_id,
    cs.title,
    cs.created_at,
    COUNT(cm.id) as message_count
FROM chat_sessions cs
LEFT JOIN conversation_messages cm ON cm.session_id = cs.id
WHERE cs.user_id = 'user-uuid-here'
GROUP BY cs.id
ORDER BY cs.last_activity DESC;
```

### **Get conversation with full context**
```sql
SELECT
    cs.session_id,
    cs.title,
    u.username,
    cm.role,
    cm.content,
    cm.model_name,
    cm.total_tokens,
    cm.latency_ms,
    cm.created_at
FROM chat_sessions cs
LEFT JOIN users u ON cs.user_id = u.id
LEFT JOIN conversation_messages cm ON cm.session_id = cs.id
WHERE cs.session_id = 'session-1764131365470-lw4n60yx5'
ORDER BY cm.created_at ASC;
```

---

## 📈 Performance Optimization

### **Why localStorage Cache?**
- **Fast Initial Load**: Don't wait for API roundtrip
- **Offline Support**: View recent messages without internet
- **Bandwidth Savings**: Reduce API calls for current session

### **Why Database is Source of Truth?**
- **Cross-Device Sync**: Same chat on desktop and mobile
- **No Data Loss**: Browser cache can be cleared
- **Searchable**: Full-text search across all messages
- **Audit Trail**: Complete history forever
- **Analytics**: Usage patterns, model performance

---

## 🚦 State Machine

```
User Login
   ↓
[Load Existing Session OR Create New Session]
   ↓
session_id generated (VARCHAR): "session-{timestamp}-{random}"
   ↓
sessionStorage.setItem('chat_session_id', session_id)
   ↓
User sends message
   ↓
[DATABASE PERSISTENCE]
   ├── Create chat_sessions record (if new)
   ├── Save user message → conversation_messages
   └── Save assistant response → conversation_messages
   ↓
[CACHE UPDATE]
   └── localStorage[session_id] = messages (for fast reload)
   ↓
User navigates away
   ↓
Session remains in database forever
   ↓
User returns & clicks history
   ↓
[LOAD FROM DATABASE]
   ├── GET /api/v1/sessions/{session_id}/messages
   └── Fallback to localStorage if DB unavailable
```

---

## ✅ Verification Commands

```bash
# Check session exists
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT * FROM chat_sessions WHERE session_id = 'YOUR-SESSION-ID';"

# Check messages for session
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT cm.* FROM conversation_messages cm
   JOIN chat_sessions cs ON cm.session_id = cs.id
   WHERE cs.session_id = 'YOUR-SESSION-ID'
   ORDER BY cm.created_at;"

# Test API endpoint
curl -s "http://localhost:8000/api/v1/sessions/YOUR-SESSION-ID/messages" | jq

# Count total messages
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM conversation_messages;"
```

---

## 🎯 Summary

| Aspect | Implementation |
|--------|---------------|
| **Session Identifier** | VARCHAR string (client-generated, user-facing) |
| **Database Primary Key** | UUID (server-generated, internal) |
| **Message Storage** | PostgreSQL `conversation_messages` table |
| **Message Linking** | `conversation_messages.session_id` → `chat_sessions.id` (UUID FK) |
| **Source of Truth** | PostgreSQL database |
| **Performance Cache** | localStorage (frontend only) |
| **Cross-Device Sync** | ✅ Yes (via database) |
| **Search** | ✅ Full-text search on `content` field |
| **Audit Trail** | ✅ Complete in `audit_logs` table |
| **Data Loss Risk** | ✅ None (database persisted) |

---

**Status**: ✅ Production-Ready
**Architecture**: DB-First with localStorage Cache
**Traceability**: 100% (session_id → chat_sessions.id → conversation_messages)
