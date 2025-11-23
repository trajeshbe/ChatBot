# MCP Server Implementation - Exposing Internal Tools

> **Created**: 2025-11-23
> **Status**: Service Layer Complete | Routes & Database Pending
> **Purpose**: Expose our internal tools as MCP services for external consumption

---

## Overview

We've implemented an **MCP (Model Context Protocol) Server** that exposes our internal tools so external applications can discover and use them. This allows other AI applications to leverage our tools like smart_extraction, web_scraper, document_rag, etc.

### Architecture

```
External Application (Claude Desktop, etc.)
          ↓
     MCP Protocol
          ↓
   Our MCP Server API
          ↓
   MCPServerService
          ↓
  Internal Tools (document_rag, smart_extraction, web_scraper, etc.)
```

---

## Features

### 1. Tool Discovery
- **`/api/v1/mcp/tools`** - List all available tools
- Returns tool definitions with parameters, descriptions, and enabled status
- Supports filtering (enabled only vs all tools)

### 2. Tool Execution
- **`/api/v1/mcp/tools/{tool_name}/execute`** - Execute a specific tool
- Parameter validation
- API key authentication (optional)
- Usage tracking and audit logging

### 3. Tool Management
- **Enable/Disable Tools** - Admin can control which tools are exposed
- **API Key Management** - Generate and manage API keys for external access
- **Usage Monitoring** - Track tool execution and usage statistics

---

## Available Tools

Our MCP server exposes 7 internal tools:

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| **document_rag** | Query documents using RAG | `query`, `session_id`, `top_k` |
| **smart_extraction** | AI-powered data extraction from web pages | `url`, `user_instructions`, `llm_provider` |
| **web_scraper** | Scrape web content with compliance checking | `url`, `scrape_prompt`, `strategy` |
| **template_extraction** | Extract data using predefined templates | `url`, `template_id` |
| **docling_pdf** | Extract text/structure from PDFs | `url`, `extract_tables` |
| **ocr** | Extract text from images | `image_url`, `language` |
| **navigation_agent** | AI-powered web navigation | `start_url`, `goal` |

---

## Files Created

### 1. Service Layer
**File**: `backend/app/services/mcp_server_service.py` (450+ lines)

**Key Classes**:
- `MCPServerService` - Main service class

**Key Methods**:
- `list_tools()` - List available tools
- `get_tool()` - Get tool details
- `toggle_tool()` - Enable/disable tools
- `execute_tool()` - Execute tool with validation
- `_validate_api_key()` - API key authentication
- `_log_tool_execution()` - Usage logging

**Tool Handlers** (already implemented):
- `execute_document_rag()` - RAG query execution
- `execute_smart_extraction()` - Smart extraction execution
- `execute_web_scraper()` - Web scraping execution
- Placeholder handlers for other tools

---

## Database Schema (To Be Created)

### mcp_tool_configs Table
Stores configuration for each tool

```sql
CREATE TABLE mcp_tool_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    description TEXT,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### mcp_api_keys Table
API keys for external applications

```sql
CREATE TABLE mcp_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- Hashed API key
    application_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    rate_limit_per_hour INTEGER DEFAULT 100
);
```

### mcp_tool_execution_log Table
Audit log for tool executions

```sql
CREATE TABLE mcp_tool_execution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name VARCHAR(100) NOT NULL,
    api_key_id VARCHAR(50),  -- First 8 chars of key for identification
    parameters JSONB,
    success BOOLEAN,
    error_message TEXT,
    execution_time_ms FLOAT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mcp_execution_tool ON mcp_tool_execution_log(tool_name);
CREATE INDEX idx_mcp_execution_time ON mcp_tool_execution_log(executed_at);
```

---

## API Endpoints (To Be Created)

### Tool Discovery

#### List All Tools
```http
GET /api/v1/mcp/tools
GET /api/v1/mcp/tools?include_disabled=true
```

**Response**:
```json
{
  "tools": [
    {
      "name": "smart_extraction",
      "description": "Extract structured data from web pages using AI",
      "enabled": true,
      "parameters": {
        "url": {"type": "string", "required": true},
        "user_instructions": {"type": "string", "required": true},
        "llm_provider": {"type": "string", "required": false, "default": "openai"}
      }
    }
  ],
  "count": 7
}
```

#### Get Tool Details
```http
GET /api/v1/mcp/tools/{tool_name}
```

**Response**:
```json
{
  "name": "document_rag",
  "description": "Query documents using RAG",
  "enabled": true,
  "parameters": {
    "query": {"type": "string", "required": true},
    "session_id": {"type": "string", "required": false},
    "top_k": {"type": "integer", "required": false, "default": 5}
  }
}
```

### Tool Execution

#### Execute Tool
```http
POST /api/v1/mcp/tools/{tool_name}/execute
X-API-Key: your-api-key  (optional)
Content-Type: application/json

{
  "parameters": {
    "url": "https://books.toscrape.com",
    "user_instructions": "Extract all book titles and prices"
  }
}
```

**Response**:
```json
{
  "success": true,
  "tool": "smart_extraction",
  "result": {
    "table": [...],
    "columns": [...],
    "row_count": 20
  }
}
```

### Tool Management (Admin Only)

#### Enable/Disable Tool
```http
PUT /api/v1/admin/mcp/tools/{tool_name}
Content-Type: application/json

{
  "enabled": true
}
```

#### Generate API Key
```http
POST /api/v1/admin/mcp/api-keys
Content-Type: application/json

{
  "key_name": "External App 1",
  "application_name": "Claude Desktop",
  "rate_limit_per_hour": 100
}
```

**Response**:
```json
{
  "key_id": "uuid",
  "key_name": "External App 1",
  "api_key": "mcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "rate_limit_per_hour": 100,
  "created_at": "2025-11-23T10:00:00Z"
}
```

#### List API Keys
```http
GET /api/v1/admin/mcp/api-keys
```

#### Revoke API Key
```http
DELETE /api/v1/admin/mcp/api-keys/{key_id}
```

### Usage Statistics

#### Get Tool Usage Stats
```http
GET /api/v1/admin/mcp/stats/tools
GET /api/v1/admin/mcp/stats/tools?tool_name=smart_extraction&days=7
```

**Response**:
```json
{
  "tool_name": "smart_extraction",
  "total_executions": 1500,
  "successful_executions": 1450,
  "failed_executions": 50,
  "avg_execution_time_ms": 250,
  "last_24h_executions": 150,
  "period": "7 days"
}
```

---

## Example Usage

### External Application (Python)

```python
import requests

MCP_API_URL = "http://localhost:8000/api/v1/mcp"
API_KEY = "mcp_your_api_key_here"

# Discover available tools
response = requests.get(
    f"{MCP_API_URL}/tools",
    headers={"X-API-Key": API_KEY}
)
tools = response.json()["tools"]
print(f"Available tools: {[t['name'] for t in tools]}")

# Execute smart_extraction
response = requests.post(
    f"{MCP_API_URL}/tools/smart_extraction/execute",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "parameters": {
            "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
            "user_instructions": "Extract all mystery books with title and price"
        }
    }
)

result = response.json()
if result["success"]:
    print(f"Extracted {len(result['result']['table'])} books")
    for book in result['result']['table'][:3]:
        print(f"- {book.get('title', book.get('Title'))}: {book.get('price', book.get('Price'))}")
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rag-chatbot": {
      "command": "python",
      "args": ["-m", "mcp_client"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8000/api/v1/mcp",
        "MCP_API_KEY": "your_api_key"
      }
    }
  }
}
```

---

## Implementation Status

### ✅ Completed
1. ✅ **MCPServerService** - Core service layer with tool management
2. ✅ **Tool Definitions** - 7 tools with complete parameter definitions
3. ✅ **Tool Execution Handlers** - 3 implemented (document_rag, smart_extraction, web_scraper)
4. ✅ **API Key Validation** - Authentication mechanism
5. ✅ **Usage Logging** - Execution tracking

### ⏳ Pending
1. **Database Migration** - Create MCP tables
2. **API Routes** - Create FastAPI endpoints
3. **Admin UI Component** - MCP management interface
4. **Implement Remaining Handlers**:
   - `execute_template_extraction()`
   - `execute_docling_pdf()`
   - `execute_ocr()`
   - `execute_navigation_agent()`

---

## Next Steps

### 1. Create Database Migration

```bash
# Create migration file
cat > backend/migrations/005_add_mcp_server.sql << 'EOF'
-- MCP Server tables...
EOF

# Apply migration
psql -U postgres -d ragchatbot -f backend/migrations/005_add_mcp_server.sql
```

### 2. Create API Routes

**File**: `backend/app/api/routes/mcp_routes.py`

```python
from fastapi import APIRouter, Depends, Header
from app.services.mcp_server_service import mcp_server_service

router = APIRouter()

@router.get("/tools")
async def list_tools(...):
    return await mcp_server_service.list_tools(db)

@router.post("/tools/{tool_name}/execute")
async def execute_tool(...):
    return await mcp_server_service.execute_tool(db, tool_name, params)
```

### 3. Integrate in main.py

```python
from app.api.routes import mcp_routes

app.include_router(
    mcp_routes.router,
    prefix="/api/v1/mcp",
    tags=["mcp"]
)
```

### 4. Create Admin UI Component

**File**: `frontend/src/components/MCPServerManagement.tsx`

Features:
- Toggle tools on/off
- Generate/revoke API keys
- View usage statistics
- Monitor tool executions

---

## Security Considerations

### 1. API Key Management
- **Hashed Storage** - Never store plaintext keys
- **Key Rotation** - Support for rotating keys
- **Rate Limiting** - Per-key rate limits
- **Expiration** - Optional key expiration dates

### 2. Tool Execution
- **Input Validation** - Validate all parameters
- **Sandboxing** - Execute tools in isolated contexts
- **Resource Limits** - Prevent resource exhaustion
- **Audit Logging** - Log all executions

### 3. Access Control
- **Admin-Only Management** - Tool configuration requires admin role
- **Per-Tool Permissions** - Granular control over tool access
- **IP Whitelisting** - Optional IP restrictions

---

## Benefits

### For Our Application
1. **Monetization** - Can charge for API access
2. **Integration** - Easy integration with external tools
3. **Visibility** - Increased tool discoverability
4. **Monitoring** - Comprehensive usage tracking

### For External Applications
1. **Tool Access** - Access to powerful AI tools via simple API
2. **No Setup** - No need to install/configure tools locally
3. **Scalability** - We handle infrastructure
4. **Documentation** - Self-describing tool interface

---

## MCP Protocol Compliance

Our implementation follows the MCP protocol specification:

- ✅ **Tool Discovery** - List available tools with schemas
- ✅ **Tool Execution** - Execute tools with parameter validation
- ✅ **Error Handling** - Standardized error responses
- ✅ **Authentication** - API key-based auth
- ⏳ **Streaming** - Support for streaming responses (future)
- ⏳ **Webhooks** - Callback support for long-running tools (future)

---

## Related Files

- **Service**: `backend/app/services/mcp_server_service.py`
- **Routes** (to create): `backend/app/api/routes/mcp_routes.py`
- **Migration** (to create): `backend/migrations/005_add_mcp_server.sql`
- **Frontend** (to create): `frontend/src/components/MCPServerManagement.tsx`

---

**Implementation Date**: 2025-11-23
**Status**: 🚧 In Progress | Service Layer Complete
