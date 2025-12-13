# CLI Engines Installation Guide

> **For Phase 2 Implementation**
> **Date**: 2025-12-13
> **Status**: ⏸️ Pending Implementation

---

## Overview

This guide provides step-by-step instructions for installing Claude Code CLI and OpenAI CLI in the `agent-runtime` container to enable CLI engine execution.

**Prerequisites**: Phase 1 must be complete (engine abstraction layer implemented).

---

## Quick Start

### 1. Update Dockerfile

**File**: `backend/Dockerfile.agent-runtime`

**Add the following sections**:

```dockerfile
# Install Node.js (required for Claude Code CLI)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Install OpenAI CLI
RUN pip install --no-cache-dir openai

# Verify installations
RUN claude --version || echo "⚠️ Claude CLI not found"
RUN which openai || echo "⚠️ OpenAI CLI not found"
RUN node --version
RUN npm --version
```

### 2. Add API Keys via Admin UI

**No `.env` or `docker-compose.yml` changes needed!**

API keys are managed via the existing SecretsService and Admin UI:

```bash
# Add Anthropic API key
curl -X POST "http://localhost:8000/api/v1/admin/secrets/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "api_key": "sk-ant-api03-your-key-here"
  }'

# Add OpenAI API key
curl -X POST "http://localhost:8000/api/v1/admin/secrets/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-your-openai-key-here"
  }'

# Verify keys were added
curl "http://localhost:8000/api/v1/admin/secrets/api-keys"
```

**Benefits**:
- ✅ Keys stored encrypted in database (Fernet encryption)
- ✅ No need to modify configuration files
- ✅ Centralized management via Admin UI
- ✅ Automatic audit logging
- ✅ Access tracking with timestamps

**Note**: You already have this secrets management system! Just use it to add CLI provider keys.

### 3. Rebuild and Restart

```bash
# Stop agent-runtime
docker-compose stop rag-agent-runtime

# Rebuild with no cache
docker-compose build --no-cache rag-agent-runtime

# Start agent-runtime
docker-compose up -d rag-agent-runtime

# Verify CLIs are installed
docker exec rag-agent-runtime claude --version
docker exec rag-agent-runtime which openai
docker exec rag-agent-runtime env | grep API_KEY
```

### 4. Test Engine Health

```bash
# Test health check endpoint (once implemented)
curl http://localhost:8000/api/v1/agents/engines/health
```

Expected response:
```json
{
  "engines": {
    "default": {
      "available": true,
      "message": "Default engine ready"
    },
    "codex-cli": {
      "available": true,
      "version": "openai 1.x.x",
      "message": "OpenAI CLI is available"
    },
    "claude-code-cli": {
      "available": true,
      "version": "/usr/local/bin/claude",
      "message": "Claude Code CLI is available"
    }
  }
}
```

---

## Detailed Installation Steps

### Step 1: Obtain API Keys

#### Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy key (starts with `sk-ant-api03-`)

#### OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign in or create account
3. Navigate to "API Keys"
4. Click "Create new secret key"
5. Copy key (starts with `sk-`)

### Step 2: Update Dockerfile.agent-runtime

**Location**: `backend/Dockerfile.agent-runtime`

**Current Dockerfile** (partial):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-agent.txt .
RUN pip install --no-cache-dir -r requirements-agent.txt

# ... rest of Dockerfile ...
```

**Add after system dependencies**:

```dockerfile
# ============================================
# CLI ENGINES INSTALLATION (Phase 2)
# ============================================

# Install Node.js 18.x (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm
RUN node --version && npm --version

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install OpenAI Python package (includes CLI)
RUN pip install --no-cache-dir openai

# Create workspace and artifacts directories
RUN mkdir -p /workspace /workspace/artifacts

# Verify CLI installations
RUN echo "Verifying CLI installations..." \
    && claude --version || echo "⚠️ Claude CLI not found (will be configured at runtime)" \
    && which openai || echo "⚠️ OpenAI CLI not found" \
    && python -c "import openai; print(f'OpenAI Python: {openai.__version__}')"

# ============================================
# END CLI ENGINES INSTALLATION
# ============================================
```

### Step 3: Update docker-compose.yml

**Location**: `docker-compose.yml`

**Find the `rag-agent-runtime` service** and update:

```yaml
rag-agent-runtime:
  container_name: rag-agent-runtime
  build:
    context: ./backend
    dockerfile: Dockerfile.agent-runtime
  volumes:
    - agent-workspace:/workspace
    - ./backend/app:/app
  environment:
    # Existing environment variables
    - DOCKER_HOST=unix:///var/run/docker.sock
    - PYTHONPATH=/app

    # 🆕 CLI Engine API Keys
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    - OPENAI_API_KEY=${OPENAI_API_KEY}

  # ... rest of service config ...
```

### Step 4: Update .env File

**Location**: `.env` (create from `.env.example` if needed)

```bash
# ============================================
# CLI Engine Configuration (Phase 2)
# ============================================

# Anthropic Claude Code CLI
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key-here

# OpenAI Codex CLI
OPENAI_API_KEY=sk-your-openai-key-here

# ============================================
```

**Important**: Never commit `.env` file to git. It's already in `.gitignore`.

### Step 5: Rebuild Container

```bash
# Option 1: Stop, rebuild, start
docker-compose stop rag-agent-runtime
docker-compose build --no-cache rag-agent-runtime
docker-compose up -d rag-agent-runtime

# Option 2: One command (slower)
docker-compose up -d --build --force-recreate rag-agent-runtime

# View build logs
docker-compose logs rag-agent-runtime
```

### Step 6: Verify Installation

```bash
# Check if Claude CLI is installed
docker exec rag-agent-runtime claude --version

# Expected output:
# claude version x.x.x

# Check if OpenAI package is installed
docker exec rag-agent-runtime python -c "import openai; print(openai.__version__)"

# Expected output:
# 1.x.x

# Check if API keys are set
docker exec rag-agent-runtime env | grep API_KEY

# Expected output:
# ANTHROPIC_API_KEY=sk-ant-api03-...
# OPENAI_API_KEY=sk-...

# Check Node.js
docker exec rag-agent-runtime node --version

# Expected output:
# v18.x.x
```

---

## Testing CLI Engines

### Test 1: Manual CLI Execution

```bash
# Test Claude CLI
docker exec -i rag-agent-runtime claude "What is 2+2?"

# Test OpenAI CLI (if available)
docker exec -i rag-agent-runtime openai api chat.completions.create \
  -m gpt-4 \
  -g user "What is 2+2?"
```

### Test 2: Engine Health Check

Create health check endpoint (if not exists):

**File**: `backend/app/api/routes/agent_routes.py`

```python
@router.get("/api/v1/agents/engines/health")
async def check_engines_health():
    """Check availability of all engines"""
    from app.services.engines import (
        DefaultAgentEngine,
        CodexCLIEngine,
        ClaudeCodeCLIEngine
    )

    default = await DefaultAgentEngine().health_check()
    codex = await CodexCLIEngine().health_check()
    claude = await ClaudeCodeCLIEngine().health_check()

    return {
        "engines": {
            "default": default,
            "codex-cli": codex,
            "claude-code-cli": claude
        }
    }
```

Test:
```bash
curl http://localhost:8000/api/v1/agents/engines/health | python -m json.tool
```

### Test 3: Full Task Execution

```bash
# Create task via API
curl -X POST "http://localhost:8000/api/v1/agents/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a Python function that calculates factorial",
    "engine": "claude-code-cli",
    "model": "claude-3-5-sonnet-20241022",
    "max_iterations": 10,
    "timeout_seconds": 300
  }'

# Get task ID from response
# Poll for completion
curl http://localhost:8000/api/v1/agents/tasks/{task_id}
```

---

## Troubleshooting

### Issue 1: Claude CLI Not Found

**Error**: `claude: command not found`

**Solutions**:
1. Check if npm install succeeded:
   ```bash
   docker exec rag-agent-runtime npm list -g @anthropic-ai/claude-code
   ```

2. Try alternative installation:
   ```dockerfile
   RUN npm install -g @anthropic-ai/claude-code-cli@latest
   ```

3. Check npm global path:
   ```bash
   docker exec rag-agent-runtime npm root -g
   ```

### Issue 2: OpenAI CLI Not Found

**Error**: `openai: command not found`

**Solutions**:
1. Verify package installed:
   ```bash
   docker exec rag-agent-runtime pip show openai
   ```

2. Use Python module instead:
   ```python
   # In codex_cli_engine.py
   command = [
       "docker", "exec", "-i", "rag-agent-runtime",
       "python", "-m", "openai.cli",
       "api", "chat.completions.create",
       "-m", model,
       "-g", "user", task_description
   ]
   ```

### Issue 3: API Keys Not Set

**Error**: `ANTHROPIC_API_KEY not found`

**Solutions**:
1. Check .env file exists and has keys:
   ```bash
   cat .env | grep API_KEY
   ```

2. Restart services to pick up new env vars:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. Manually set for testing:
   ```bash
   docker exec -e ANTHROPIC_API_KEY=sk-ant-... rag-agent-runtime claude "test"
   ```

### Issue 4: Authentication Required

**Error**: Claude CLI prompts for authentication URL

**Solution**: This is expected behavior. See "Interactive Authentication" section below.

---

## Interactive Authentication (Phase 2 Advanced)

### Claude Code CLI Authentication Flow

Claude Code CLI requires interactive authentication on first use:

```bash
$ claude "test"
Visit: https://auth.anthropic.com/activate?code=XXXX-XXXX
Paste your authentication code: _
```

### Implementation Required

**Backend Changes** (`claude_code_cli_engine.py`):

```python
async def execute(self, task_description: str, ...):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE  # ✅ Already configured
    )

    # Read stdout asynchronously
    async for line in process.stdout:
        line_str = line.decode('utf-8')

        # Detect auth URL
        if "Visit:" in line_str and "auth.anthropic.com" in line_str:
            # Extract URL
            url_match = re.search(r'https://[^\s]+', line_str)
            if url_match:
                auth_url = url_match.group(0)

                # Send to frontend via WebSocket
                await self.send_event({
                    "type": "auth_required",
                    "auth_url": auth_url,
                    "message": "Please authenticate via browser"
                })

                # Wait for key from frontend (via WebSocket)
                auth_key = await self.wait_for_auth_key()

                # Pass key to CLI stdin
                process.stdin.write(f"{auth_key}\n".encode())
                await process.stdin.drain()
```

**Frontend Changes** (AgentTaskMonitor.tsx):

```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/api/v1/agents/stream');

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'auth_required') {
      // Display auth UI
      setAuthUrl(data.auth_url);
      setShowAuthModal(true);
    }
  };
}, []);

const handleAuthSubmit = (authKey: string) => {
  // Send key back to backend
  ws.send(JSON.stringify({
    type: 'auth_key',
    key: authKey
  }));
  setShowAuthModal(false);
};
```

**Status**: ⏸️ Not implemented in Phase 1

---

## Next Steps After Installation

Once CLIs are installed:

1. ✅ Test health check endpoint
2. ✅ Test manual CLI execution
3. ✅ Create test task via API
4. ⏸️ Implement interactive authentication (Phase 2)
5. ⏸️ Add WebSocket streaming endpoint
6. ⏸️ Create auth UI components
7. ⏸️ Write integration tests

---

## Security Considerations

### API Key Management

- ✅ Store keys in `.env` (not in code)
- ✅ `.env` is in `.gitignore`
- ✅ Pass keys via environment variables only
- ❌ Never log or display full API keys
- ❌ Never commit keys to git

### Container Isolation

- ✅ CLIs run in isolated `agent-runtime` container
- ✅ Container has limited resource access
- ✅ No direct network access from backend to CLI
- ✅ Communication only via docker exec

### Input Validation

- ✅ Validate task descriptions before passing to CLI
- ⚠️ Sanitize file paths for workspace access
- ⚠️ Limit max iterations and timeout
- ⚠️ Monitor resource usage (CPU, memory)

---

## References

- Claude Code CLI Docs: https://code.claude.com/docs/en/setup
- Anthropic API Docs: https://docs.anthropic.com/
- OpenAI API Docs: https://platform.openai.com/docs/
- Implementation Status: `docs/features/CLI_ENGINES_IMPLEMENTATION_STATUS.md`
- Phase 1 Summary: `docs/features/CLI_ENGINES_PHASE1_COMPLETE.md`

---

**End of Installation Guide**
