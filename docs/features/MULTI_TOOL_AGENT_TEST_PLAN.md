# Multi-Tool Agent - Phase 6 Comprehensive Test Plan

> **Test Suite Version**: 1.0.0
> **Last Updated**: 2025-11-22
> **Phase**: Phase 6 - API Integration
> **Status**: Ready for Execution

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Test Categories](#test-categories)
4. [Test Cases](#test-cases)
5. [Expected Results](#expected-results)
6. [Execution Plan](#execution-plan)

---

## Overview

### What We're Testing

Phase 6 delivered three major components:
1. **MCP Admin API** - 13 endpoints for MCP server management
2. **Tool Discovery API** - 11 endpoints for tool listing and management
3. **Enhanced RAG Agent** - Multi-tool execution with comprehensive metadata

### Test Objectives

- ✅ Verify all API endpoints are functional
- ✅ Validate response schemas match specifications
- ✅ Test error handling and edge cases
- ✅ Verify graceful degradation when MCP is unavailable
- ✅ Validate multi-tool metadata generation
- ✅ Test filtering, searching, and pagination
- ✅ Verify tool enable/disable functionality

### Success Criteria

- All endpoints return 200 OK for valid requests
- Error responses include proper HTTP status codes (404, 500, etc.)
- Response schemas match Pydantic models
- System gracefully handles missing dependencies
- Multi-tool metadata includes all required fields

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Ensure all services are running
docker-compose up -d

# 2. Verify backend is healthy
curl http://localhost:8000/health

# 3. Check database connectivity
docker-compose exec postgres pg_isready

# 4. Verify environment variables
grep -E "OPENAI_API_KEY|ANTHROPIC_API_KEY" .env
```

### Test Data Requirements

- Active PostgreSQL database with documents
- At least one uploaded document for RAG testing
- Valid API keys for LLM services (if testing LLM-based features)

---

## Test Categories

### Category 1: Tool Discovery API (11 Endpoints)

**Base URL**: `/api/v1/tools`

| Test ID | Endpoint | Method | Priority |
|---------|----------|--------|----------|
| T1.1 | `/api/v1/tools` | GET | High |
| T1.2 | `/api/v1/tools?enabled_only=true` | GET | High |
| T1.3 | `/api/v1/tools?source=built-in` | GET | Medium |
| T1.4 | `/api/v1/tools?tag=document` | GET | Medium |
| T1.5 | `/api/v1/tools?search=rag` | GET | Medium |
| T1.6 | `/api/v1/tools/{tool_id}` | GET | High |
| T1.7 | `/api/v1/tools/{tool_id}/schema` | GET | Medium |
| T1.8 | `/api/v1/tools/categories/list` | GET | High |
| T1.9 | `/api/v1/tools/categories/{category}` | GET | Medium |
| T1.10 | `/api/v1/tools/statistics` | GET | High |
| T1.11 | `/api/v1/tools/{tool_id}/enable` | POST | Medium |
| T1.12 | `/api/v1/tools/{tool_id}/disable` | POST | Medium |
| T1.13 | `/api/v1/tools/llm/format` | GET | High |

### Category 2: MCP Admin API (13 Endpoints)

**Base URL**: `/api/v1/mcp`

| Test ID | Endpoint | Method | Priority |
|---------|----------|--------|----------|
| T2.1 | `/api/v1/mcp/provider/status` | GET | High |
| T2.2 | `/api/v1/mcp/provider/enable` | POST | Low |
| T2.3 | `/api/v1/mcp/provider/disable` | POST | Low |
| T2.4 | `/api/v1/mcp/provider/connection-info` | GET | Medium |
| T2.5 | `/api/v1/mcp/consumer/servers` | GET | High |
| T2.6 | `/api/v1/mcp/consumer/servers/{server_id}` | GET | Medium |
| T2.7 | `/api/v1/mcp/consumer/servers/{server_id}/enable` | POST | Low |
| T2.8 | `/api/v1/mcp/consumer/servers/{server_id}/disable` | POST | Low |
| T2.9 | `/api/v1/mcp/consumer/servers/{server_id}/tools` | GET | Medium |
| T2.10 | `/api/v1/mcp/health` | GET | High |
| T2.11 | `/api/v1/mcp/health/{server_id}` | GET | Medium |
| T2.12 | `/api/v1/mcp/statistics` | GET | High |
| T2.13 | `/api/v1/mcp/consumer/reconnect-failed` | POST | Low |

### Category 3: Enhanced RAG Agent Metadata

**Base URL**: `/api/v1/query`

| Test ID | Test Description | Priority |
|---------|------------------|----------|
| T3.1 | Single tool execution metadata | High |
| T3.2 | Multi-tool execution metadata | High |
| T3.3 | Tool timing information | High |
| T3.4 | Tool selection reasoning | Medium |
| T3.5 | Intent detection | Medium |
| T3.6 | Confidence scores | Medium |
| T3.7 | Error handling in metadata | High |

### Category 4: Error Handling & Edge Cases

| Test ID | Test Description | Priority |
|---------|------------------|----------|
| T4.1 | Non-existent tool ID (404) | High |
| T4.2 | Invalid filter parameters | Medium |
| T4.3 | MCP unavailable (503) | High |
| T4.4 | Empty result sets | Medium |
| T4.5 | Malformed requests (400) | Medium |

---

## Test Cases

### T1.1: List All Tools

**Endpoint**: `GET /api/v1/tools`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools | jq
```

**Expected Response**:
```json
{
  "total": 5,
  "enabled": 4,
  "disabled": 1,
  "tools": [
    {
      "tool_id": "document_rag",
      "name": "Document RAG",
      "description": "Search and retrieve information from uploaded documents",
      "tags": ["document", "search", "rag"],
      "source": "built-in",
      "enabled": true
    }
  ],
  "filters_applied": {
    "enabled_only": false,
    "source": null,
    "tag": null,
    "search": null
  }
}
```

**Validation**:
- ✅ Status code: 200
- ✅ Response contains `total`, `enabled`, `disabled`, `tools` fields
- ✅ Each tool has required fields: `tool_id`, `name`, `description`, `tags`, `source`, `enabled`

---

### T1.2: List Enabled Tools Only

**Endpoint**: `GET /api/v1/tools?enabled_only=true`

**Test Steps**:
```bash
curl -s "http://localhost:8000/api/v1/tools?enabled_only=true" | jq
```

**Expected Response**:
```json
{
  "total": 4,
  "enabled": 4,
  "disabled": 0,
  "tools": [...],
  "filters_applied": {
    "enabled_only": true,
    "source": null,
    "tag": null,
    "search": null
  }
}
```

**Validation**:
- ✅ Status code: 200
- ✅ All returned tools have `enabled: true`
- ✅ `disabled` count is 0

---

### T1.3: Filter by Source

**Endpoint**: `GET /api/v1/tools?source=built-in`

**Test Steps**:
```bash
curl -s "http://localhost:8000/api/v1/tools?source=built-in" | jq
```

**Expected Response**:
```json
{
  "total": 3,
  "enabled": 3,
  "disabled": 0,
  "tools": [...],
  "filters_applied": {
    "enabled_only": false,
    "source": "built-in",
    "tag": null,
    "search": null
  }
}
```

**Validation**:
- ✅ Status code: 200
- ✅ All returned tools have `source: "built-in"`

---

### T1.4: Filter by Tag

**Endpoint**: `GET /api/v1/tools?tag=document`

**Test Steps**:
```bash
curl -s "http://localhost:8000/api/v1/tools?tag=document" | jq
```

**Expected Response**:
```json
{
  "total": 2,
  "enabled": 2,
  "disabled": 0,
  "tools": [...],
  "filters_applied": {
    "enabled_only": false,
    "source": null,
    "tag": "document",
    "search": null
  }
}
```

**Validation**:
- ✅ Status code: 200
- ✅ All returned tools include "document" in their `tags` array

---

### T1.5: Search Tools

**Endpoint**: `GET /api/v1/tools?search=rag`

**Test Steps**:
```bash
curl -s "http://localhost:8000/api/v1/tools?search=rag" | jq
```

**Expected Response**:
- Tools where "rag" appears in name or description

**Validation**:
- ✅ Status code: 200
- ✅ All returned tools contain "rag" (case-insensitive) in name or description

---

### T1.6: Get Specific Tool Details

**Endpoint**: `GET /api/v1/tools/{tool_id}`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools/document_rag | jq
```

**Expected Response**:
```json
{
  "tool_id": "document_rag",
  "name": "Document RAG",
  "description": "Search and retrieve information from uploaded documents using semantic similarity",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "top_k": {
        "type": "integer",
        "description": "Number of results to return",
        "default": 5
      }
    },
    "required": ["query"]
  },
  "tags": ["document", "search", "rag"],
  "source": "built-in",
  "enabled": true,
  "metadata": {
    "version": "1.0.0",
    "supports_streaming": false
  }
}
```

**Validation**:
- ✅ Status code: 200
- ✅ Response includes complete tool information
- ✅ `input_schema` is valid JSON schema

---

### T1.7: Get Tool Input Schema

**Endpoint**: `GET /api/v1/tools/{tool_id}/schema`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools/document_rag/schema | jq
```

**Expected Response**:
```json
{
  "tool_id": "document_rag",
  "name": "Document RAG",
  "input_schema": {...},
  "openai_format": {
    "type": "function",
    "function": {
      "name": "document_rag",
      "description": "Search and retrieve information...",
      "parameters": {...}
    }
  }
}
```

**Validation**:
- ✅ Status code: 200
- ✅ Includes both `input_schema` and `openai_format`
- ✅ OpenAI format matches OpenAI function calling spec

---

### T1.8: List All Categories

**Endpoint**: `GET /api/v1/tools/categories/list`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools/categories/list | jq
```

**Expected Response**:
```json
[
  {
    "tag": "document",
    "tool_count": 3,
    "sample_tools": ["document_rag", "document_upload", "document_search"]
  },
  {
    "tag": "web",
    "tool_count": 2,
    "sample_tools": ["web_scraper", "web_search"]
  }
]
```

**Validation**:
- ✅ Status code: 200
- ✅ Array of categories sorted by tool count (descending)
- ✅ Each category includes tag, count, and sample tools (max 5)

---

### T1.9: List Tools by Category

**Endpoint**: `GET /api/v1/tools/categories/{category}`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools/categories/document | jq
```

**Expected Response**:
```json
[
  {
    "tool_id": "document_rag",
    "name": "Document RAG",
    "description": "...",
    "tags": ["document", "search", "rag"],
    "source": "built-in",
    "enabled": true
  }
]
```

**Validation**:
- ✅ Status code: 200
- ✅ All returned tools include the specified tag

---

### T1.10: Get Tool Statistics

**Endpoint**: `GET /api/v1/tools/statistics`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools/statistics | jq
```

**Expected Response**:
```json
{
  "total_tools": 7,
  "enabled_tools": 6,
  "disabled_tools": 1,
  "builtin_tools": 5,
  "mcp_tools": 2,
  "custom_tools": 0,
  "total_tags": 8,
  "top_tags": [
    {"tag": "document", "count": 3},
    {"tag": "web", "count": 2}
  ]
}
```

**Validation**:
- ✅ Status code: 200
- ✅ All counts are non-negative integers
- ✅ Total tools = enabled + disabled
- ✅ Total tools = builtin + mcp + custom

---

### T1.11: Enable a Tool

**Endpoint**: `POST /api/v1/tools/{tool_id}/enable`

**Test Steps**:
```bash
# First disable a tool
curl -s -X POST http://localhost:8000/api/v1/tools/web_scraper/disable | jq

# Then enable it
curl -s -X POST http://localhost:8000/api/v1/tools/web_scraper/enable | jq
```

**Expected Response**:
```json
{
  "tool_id": "web_scraper",
  "name": "Web Scraper",
  "description": "...",
  "input_schema": {...},
  "tags": ["web", "scraping"],
  "source": "built-in",
  "enabled": true,
  "metadata": {}
}
```

**Validation**:
- ✅ Status code: 200
- ✅ `enabled` field is `true`

---

### T1.12: Disable a Tool

**Endpoint**: `POST /api/v1/tools/{tool_id}/disable`

**Test Steps**:
```bash
curl -s -X POST http://localhost:8000/api/v1/tools/web_scraper/disable | jq
```

**Expected Response**:
```json
{
  "tool_id": "web_scraper",
  "enabled": false
}
```

**Validation**:
- ✅ Status code: 200
- ✅ `enabled` field is `false`

---

### T1.13: Get Tools in LLM Format

**Endpoint**: `GET /api/v1/tools/llm/format`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/tools/llm/format | jq
```

**Expected Response**:
```json
[
  {
    "type": "function",
    "function": {
      "name": "document_rag",
      "description": "Search and retrieve information from uploaded documents",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string"}
        },
        "required": ["query"]
      }
    }
  }
]
```

**Validation**:
- ✅ Status code: 200
- ✅ Array of tools in OpenAI function calling format
- ✅ Only enabled tools are returned by default

---

### T2.1: Get MCP Provider Status

**Endpoint**: `GET /api/v1/mcp/provider/status`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/mcp/provider/status | jq
```

**Expected Response (MCP Available)**:
```json
{
  "enabled": true,
  "server_name": "chatbot-mcp-server",
  "version": "1.0.0",
  "transport": "stdio",
  "host": "localhost",
  "port": 0,
  "tools_exposed": 5,
  "running": true
}
```

**Expected Response (MCP Unavailable)**:
```json
{
  "detail": "MCP Server not initialized"
}
```

**Validation**:
- ✅ Status code: 200 (if available) or 503 (if unavailable)
- ✅ Graceful error message if MCP not available

---

### T2.5: List External MCP Servers

**Endpoint**: `GET /api/v1/mcp/consumer/servers`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/mcp/consumer/servers | jq
```

**Expected Response**:
```json
[
  {
    "server_id": "filesystem",
    "name": "Filesystem Server",
    "enabled": true,
    "connected": true,
    "transport": "stdio",
    "tools_imported": 3,
    "tools": ["read_file", "write_file", "list_directory"],
    "error": null
  }
]
```

**Validation**:
- ✅ Status code: 200 or 503
- ✅ Array of server status objects

---

### T2.10: MCP Overall Health Check

**Endpoint**: `GET /api/v1/mcp/health`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/mcp/health | jq
```

**Expected Response**:
```json
{
  "provider": {
    "enabled": true,
    "running": true,
    "tools_exposed": 5
  },
  "consumers": [
    {
      "server_id": "filesystem",
      "healthy": true,
      "enabled": true,
      "connected": true,
      "tools_imported": 3
    }
  ],
  "overall_healthy": true
}
```

**Validation**:
- ✅ Status code: 200 or 503
- ✅ Includes provider and consumer health info

---

### T2.12: Get MCP Statistics

**Endpoint**: `GET /api/v1/mcp/statistics`

**Test Steps**:
```bash
curl -s http://localhost:8000/api/v1/mcp/statistics | jq
```

**Expected Response**:
```json
{
  "total_servers": 3,
  "enabled_servers": 2,
  "connected_servers": 2,
  "disconnected_servers": 0,
  "total_external_tools": 8,
  "servers_with_errors": 0,
  "health_check_timestamp": "2025-11-22T10:30:00Z"
}
```

**Validation**:
- ✅ Status code: 200 or 503
- ✅ All counts are consistent

---

### T3.1: Single Tool Execution Metadata

**Endpoint**: `POST /api/v1/query`

**Test Steps**:
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What documents do we have?",
    "model": "gpt-4"
  }' | jq '.metadata.tool_usage'
```

**Expected Response**:
```json
{
  "tools_used": ["document_rag"],
  "tool_timing": {
    "document_rag": 234.56
  },
  "tool_execution_summary": {
    "document_rag": {
      "success": true,
      "execution_time_ms": 234.56,
      "error": null
    }
  },
  "tool_selection_method": "llm_based",
  "selection_confidence": 0.95,
  "intent_detected": "document_query",
  "tool_selection_reasoning": "User is asking about available documents",
  "total_time_ms": 567.89,
  "multi_tool_used": false
}
```

**Validation**:
- ✅ Status code: 200
- ✅ `tool_usage` object exists in metadata
- ✅ All required fields present
- ✅ `multi_tool_used` is false for single tool

---

### T3.2: Multi-Tool Execution Metadata

**Endpoint**: `POST /api/v1/query`

**Test Steps**:
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search documents and scrape website X",
    "model": "gpt-4"
  }' | jq '.metadata.tool_usage'
```

**Expected Response**:
```json
{
  "tools_used": ["document_rag", "web_scraper"],
  "tool_timing": {
    "document_rag": 234.56,
    "web_scraper": 1234.56
  },
  "tool_execution_summary": {
    "document_rag": {
      "success": true,
      "execution_time_ms": 234.56,
      "error": null
    },
    "web_scraper": {
      "success": true,
      "execution_time_ms": 1234.56,
      "error": null
    }
  },
  "tool_selection_method": "llm_based",
  "selection_confidence": 0.92,
  "intent_detected": "multi_source_query",
  "tool_selection_reasoning": "User needs both document search and web scraping",
  "total_time_ms": 1567.89,
  "multi_tool_used": true
}
```

**Validation**:
- ✅ Status code: 200
- ✅ Multiple tools in `tools_used` array
- ✅ Timing for each tool
- ✅ Execution summary for each tool
- ✅ `multi_tool_used` is true

---

### T4.1: Non-Existent Tool (404 Error)

**Endpoint**: `GET /api/v1/tools/nonexistent_tool`

**Test Steps**:
```bash
curl -s -w "\nHTTP_CODE:%{http_code}\n" \
  http://localhost:8000/api/v1/tools/nonexistent_tool | jq
```

**Expected Response**:
```json
{
  "detail": "Tool not found: nonexistent_tool"
}
```

**Validation**:
- ✅ Status code: 404
- ✅ Error message explains the issue

---

### T4.3: MCP Unavailable (503 Error)

**Endpoint**: `GET /api/v1/mcp/provider/status`

**Test Steps**:
```bash
# When MCP SDK is not installed
curl -s -w "\nHTTP_CODE:%{http_code}\n" \
  http://localhost:8000/api/v1/mcp/provider/status | jq
```

**Expected Response**:
```json
{
  "detail": "MCP Server not initialized"
}
```

**Validation**:
- ✅ Status code: 503
- ✅ Graceful error message
- ✅ Application continues to function

---

## Expected Results

### Summary of Expected Outcomes

| Category | Total Tests | Expected Pass | Expected Fail (Graceful) |
|----------|-------------|---------------|--------------------------|
| Tool Discovery API | 13 | 13 | 0 |
| MCP Admin API | 13 | Variable* | Variable* |
| Enhanced RAG Agent | 7 | 7 | 0 |
| Error Handling | 5 | 5 | 0 |
| **TOTAL** | **38** | **Variable** | **0** |

*MCP tests depend on whether MCP SDK is installed. All should gracefully return 503 if unavailable.

### Key Performance Indicators (KPIs)

- **API Response Time**: < 500ms for listing endpoints
- **Error Rate**: 0% for valid requests
- **Graceful Degradation**: 100% (all MCP endpoints return 503 gracefully)
- **Schema Validation**: 100% (all responses match Pydantic models)

---

## Execution Plan

### Automated Test Script

Create and run `scripts/testing/test_multi_tool_agent_phase6.sh`:

```bash
#!/bin/bash
# Test script location: scripts/testing/test_multi_tool_agent_phase6.sh

set -e

echo "================================================"
echo "Multi-Tool Agent Phase 6 - Comprehensive Tests"
echo "================================================"
echo ""

# Configuration
BACKEND_URL="http://localhost:8000"
RESULTS_DIR="/tmp/multi_tool_agent_tests"
mkdir -p $RESULTS_DIR

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function to run test
run_test() {
    local test_id=$1
    local test_name=$2
    local endpoint=$3
    local method=$4
    local expected_code=$5

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo "[$test_id] Testing: $test_name"

    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL$endpoint")
    else
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BACKEND_URL$endpoint")
    fi

    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')

    if [ "$http_code" == "$expected_code" ]; then
        echo "  ✅ PASS (HTTP $http_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "$body" > "$RESULTS_DIR/${test_id}.json"
    else
        echo "  ❌ FAIL (Expected $expected_code, got $http_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "$body" > "$RESULTS_DIR/${test_id}_FAIL.json"
    fi

    echo ""
}

# Execute tests
echo "Category 1: Tool Discovery API"
echo "================================"
run_test "T1.1" "List all tools" "/api/v1/tools" "GET" "200"
run_test "T1.2" "List enabled tools" "/api/v1/tools?enabled_only=true" "GET" "200"
run_test "T1.3" "Filter by source" "/api/v1/tools?source=built-in" "GET" "200"
run_test "T1.4" "Filter by tag" "/api/v1/tools?tag=document" "GET" "200"
run_test "T1.5" "Search tools" "/api/v1/tools?search=rag" "GET" "200"
run_test "T1.8" "List categories" "/api/v1/tools/categories/list" "GET" "200"
run_test "T1.10" "Get statistics" "/api/v1/tools/statistics" "GET" "200"
run_test "T1.13" "Get LLM format" "/api/v1/tools/llm/format" "GET" "200"

echo ""
echo "Category 2: MCP Admin API"
echo "================================"
run_test "T2.1" "MCP provider status" "/api/v1/mcp/provider/status" "GET" "200|503"
run_test "T2.5" "List external servers" "/api/v1/mcp/consumer/servers" "GET" "200|503"
run_test "T2.10" "MCP health check" "/api/v1/mcp/health" "GET" "200|503"
run_test "T2.12" "MCP statistics" "/api/v1/mcp/statistics" "GET" "200|503"

echo ""
echo "Category 4: Error Handling"
echo "================================"
run_test "T4.1" "Non-existent tool" "/api/v1/tools/nonexistent_tool" "GET" "404"

echo ""
echo "================================================"
echo "Test Execution Complete"
echo "================================================"
echo "Total Tests:  $TOTAL_TESTS"
echo "Passed:       $PASSED_TESTS"
echo "Failed:       $FAILED_TESTS"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
echo ""
echo "Detailed results saved to: $RESULTS_DIR"
echo "================================================"
```

### Manual Execution Steps

1. **Start Services**
   ```bash
   docker-compose up -d
   ```

2. **Wait for Backend**
   ```bash
   ./scripts/maintenance/validate-services.sh
   ```

3. **Run Test Script**
   ```bash
   chmod +x scripts/testing/test_multi_tool_agent_phase6.sh
   ./scripts/testing/test_multi_tool_agent_phase6.sh
   ```

4. **Review Results**
   ```bash
   ls -lh /tmp/multi_tool_agent_tests/
   cat /tmp/multi_tool_agent_tests/T1.1.json | jq
   ```

---

## Post-Test Validation

### Verification Checklist

- [ ] All tool discovery endpoints return 200 OK
- [ ] MCP endpoints gracefully return 503 if unavailable
- [ ] Response schemas match Pydantic models
- [ ] Error responses include proper status codes
- [ ] Tool enable/disable functionality works
- [ ] Multi-tool metadata includes all fields
- [ ] LLM format endpoint returns valid OpenAI schema

### Known Limitations

1. **MCP Tests**: Will return 503 if MCP SDK not installed (expected behavior)
2. **Multi-Tool Tests**: Require complex queries to trigger multiple tools
3. **Performance**: May vary based on system resources

---

**End of Test Plan**
