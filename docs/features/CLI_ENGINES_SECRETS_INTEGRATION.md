# CLI Engines - Secrets Service Integration

> **Date**: 2025-12-13
> **Update**: CLI engines now use existing SecretsService for API key management
> **Status**: ✅ Complete

---

## Summary

Updated CLI engines to use the **existing SecretsService** instead of environment variables for API key management. This integrates seamlessly with the existing Admin UI for managing API keys.

---

## What Changed

### Before (Environment Variables)

```python
class ClaudeCodeCLIEngine(AgentEngine):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
```

**Problems**:
- API keys hardcoded in `.env` file
- No centralized management
- No encryption at rest
- No audit logging
- No UI for updating keys

### After (SecretsService Integration)

```python
class ClaudeCodeCLIEngine(AgentEngine):
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self.provider_name = "anthropic"

    async def _get_api_key(self) -> Optional[str]:
        secrets_service = get_secrets_service()
        return await secrets_service.get_api_key(
            db=self.db_session,
            provider=self.provider_name
        )
```

**Benefits**:
- ✅ API keys stored encrypted (Fernet encryption)
- ✅ Centralized in database
- ✅ Admin UI for management
- ✅ Automatic audit logging
- ✅ Access tracking (last_used_at)
- ✅ Soft delete (inactive flag)

---

## Files Modified

### 1. `backend/app/services/engines/claude_code_cli_engine.py`

**Changes**:
- Added `db_session` parameter to `__init__()`
- Removed `api_key` parameter
- Added `_get_api_key()` method to retrieve from secrets service
- Updated `execute()` to retrieve API key before execution
- Return helpful error if API key not configured

**Key Code**:
```python:45-73
async def _get_api_key(self) -> Optional[str]:
    """Retrieve Anthropic API key from secrets service"""
    if not self.db_session:
        self.logger.error("❌ No database session provided")
        return None

    try:
        from app.services.secrets_service import get_secrets_service

        secrets_service = get_secrets_service()
        api_key = await secrets_service.get_api_key(
            db=self.db_session,
            provider=self.provider_name
        )

        if not api_key:
            self.logger.warning(f"⚠️ No API key found for provider: {self.provider_name}")
            self.logger.info(f"💡 Please add API key via Admin UI")

        return api_key

    except Exception as e:
        self.logger.error(f"❌ Error retrieving API key: {e}")
        return None
```

**Command Execution**:
```python:124-130
command = [
    "docker", "exec", "-i",
    "-e", f"ANTHROPIC_API_KEY={api_key}",  # Pass key to container
    "rag-agent-runtime",
    "claude",
    task_description
]
```

### 2. `backend/app/services/engines/codex_cli_engine.py`

**Changes**: Identical to Claude Code CLI engine, but:
- Provider name: `"openai"`
- Environment variable: `OPENAI_API_KEY`

**Key Code**:
```python:48-76
async def _get_api_key(self) -> Optional[str]:
    """Retrieve OpenAI API key from secrets service"""
    # Same implementation as Claude Code CLI
    secrets_service = get_secrets_service()
    api_key = await secrets_service.get_api_key(
        db=self.db_session,
        provider="openai"
    )
    return api_key
```

### 3. `backend/app/services/agent_service.py`

**Changes**: Pass database session to CLI engines when instantiating

**Before**:
```python
cli_engine = CodexCLIEngine()
```

**After**:
```python:1007-1012
# Instantiate the appropriate engine with database session
# Database session is required to retrieve API keys from secrets service
if engine == "codex-cli":
    cli_engine = CodexCLIEngine(db_session=db)
elif engine == "claude-code-cli":
    cli_engine = ClaudeCodeCLIEngine(db_session=db)
```

---

## How to Use

### 1. Add API Keys via Admin UI

**OpenAI API Key**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/secrets/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-your-openai-key-here"
  }'
```

**Anthropic API Key**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/secrets/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "api_key": "sk-ant-api03-your-key-here"
  }'
```

### 2. Verify Keys Are Stored

**List All Providers**:
```bash
curl "http://localhost:8000/api/v1/admin/secrets/api-keys"
```

**Response**:
```json
[
  {
    "provider": "openai",
    "is_active": true,
    "created_at": "2025-12-13T10:00:00Z",
    "updated_at": "2025-12-13T10:00:00Z",
    "last_used_at": null,
    "has_key": true
  },
  {
    "provider": "anthropic",
    "is_active": true,
    "created_at": "2025-12-13T10:01:00Z",
    "updated_at": "2025-12-13T10:01:00Z",
    "last_used_at": null,
    "has_key": true
  }
]
```

### 3. Use CLI Engines

**Create Task with Claude Code CLI**:
```bash
curl -X POST "http://localhost:8000/api/v1/agents/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a Python function to calculate factorial",
    "engine": "claude-code-cli",
    "model": "claude-3-5-sonnet-20241022"
  }'
```

**Create Task with Codex CLI**:
```bash
curl -X POST "http://localhost:8000/api/v1/agents/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Write a JavaScript function to validate email",
    "engine": "codex-cli",
    "model": "gpt-4-turbo-preview"
  }'
```

### 4. Track API Key Usage

**View Access Logs**:
```bash
curl "http://localhost:8000/api/v1/admin/secrets/api-keys/logs/anthropic?limit=10"
```

**Response**:
```json
[
  {
    "id": "uuid",
    "provider": "anthropic",
    "user_id": "admin-uuid",
    "action": "accessed",
    "ip_address": "192.168.1.1",
    "success": true,
    "error_message": null,
    "created_at": "2025-12-13T11:30:00Z"
  }
]
```

---

## Security Features

### 1. Encryption at Rest

**Fernet Symmetric Encryption**:
- Keys encrypted before storage
- Master key stored in environment (`MASTER_ENCRYPTION_KEY`)
- AES-128 encryption standard

**Example**:
```python
# API key: "sk-abc123..."
# Stored in DB: "gAAAAABh2..."  # Encrypted base64
```

### 2. Audit Logging

Every API key access is logged:
- **Created**: When key is first added
- **Accessed**: When key is retrieved for use
- **Updated**: When key is modified
- **Deleted**: When key is marked inactive
- **Validated**: When key is checked

### 3. Soft Delete

Keys are never permanently deleted:
- `is_active=false` flag marks as deleted
- Encrypted key remains in database for audit
- Can be reactivated by updating

### 4. Access Tracking

**Automatic Timestamps**:
- `created_at`: When key was first added
- `updated_at`: When key was last modified
- `last_used_at`: When key was last accessed

---

## Error Handling

### No API Key Configured

**Scenario**: User selects CLI engine but API key not added

**Response**:
```json
{
  "success": false,
  "error": "Anthropic API key not configured. Please add it via Admin UI at /api/v1/admin/secrets/api-keys",
  "engine": "claude-code-cli"
}
```

**Log Message**:
```
⚠️ No API key found for provider: anthropic
💡 Please add API key via Admin UI: POST /api/v1/admin/secrets/api-keys
```

### Invalid API Key

**Scenario**: API key exists but is invalid/expired

**Behavior**:
- Key retrieved from secrets service successfully
- Passed to CLI in container
- CLI returns authentication error
- Task marked as FAILED with error message

### Database Session Missing

**Scenario**: Engine instantiated without db_session

**Response**:
```
❌ No database session provided to retrieve API key
```

---

## Migration Guide

### For Existing Deployments

If you previously used environment variables:

1. **Keep existing `.env` for now** (fallback):
   ```bash
   # .env (optional fallback)
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   ```

2. **Add API keys via Admin UI**:
   ```bash
   # Add OpenAI key
   curl -X POST "http://localhost:8000/api/v1/admin/secrets/api-keys" \
     -d '{"provider": "openai", "api_key": "sk-..."}'

   # Add Anthropic key
   curl -X POST "http://localhost:8000/api/v1/admin/secrets/api-keys" \
     -d '{"provider": "anthropic", "api_key": "sk-ant-..."}'
   ```

3. **Verify CLI engines work**:
   ```bash
   # Test Codex CLI
   curl -X POST "http://localhost:8000/api/v1/agents/tasks" \
     -d '{"task_description": "test", "engine": "codex-cli"}'

   # Test Claude Code CLI
   curl -X POST "http://localhost:8000/api/v1/agents/tasks" \
     -d '{"task_description": "test", "engine": "claude-code-cli"}'
   ```

4. **Remove from `.env`** (once verified):
   ```bash
   # Remove these lines:
   # ANTHROPIC_API_KEY=...
   # OPENAI_API_KEY=...
   ```

### For New Deployments

1. **Generate master encryption key**:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Add to `.env`**:
   ```bash
   MASTER_ENCRYPTION_KEY=<generated-key>
   ```

3. **Add API keys via UI** (no need for ANTHROPIC_API_KEY or OPENAI_API_KEY)

---

## Advantages Over Environment Variables

| Feature | Environment Variables | SecretsService |
|---------|----------------------|----------------|
| **Encryption** | ❌ Plaintext in .env | ✅ Fernet encrypted |
| **Centralized** | ❌ Multiple files | ✅ Single database |
| **UI Management** | ❌ Manual editing | ✅ Admin UI |
| **Audit Logging** | ❌ None | ✅ Full audit trail |
| **Access Tracking** | ❌ None | ✅ Timestamps logged |
| **Multi-Provider** | ❌ One var per provider | ✅ Unlimited providers |
| **Key Rotation** | ❌ Requires restart | ✅ Hot reload |
| **Soft Delete** | ❌ Permanent removal | ✅ Inactive flag |
| **Version Control** | ❌ Risk of commit | ✅ Never in git |

---

## Provider Names Reference

When adding API keys via Admin UI, use these provider names:

| CLI Engine | Provider Name | API Key Format |
|------------|--------------|----------------|
| Codex CLI (OpenAI) | `openai` | `sk-...` |
| Claude Code CLI | `anthropic` | `sk-ant-api03-...` |

**Future Providers** (can be added):
- `huggingface`: HuggingFace API key
- `cohere`: Cohere API key
- `openrouter`: OpenRouter API key

---

## Testing

### Unit Test Example

```python
import pytest
from app.services.engines import ClaudeCodeCLIEngine
from app.services.secrets_service import SecretsService

@pytest.mark.asyncio
async def test_cli_engine_retrieves_api_key(db_session):
    # Add API key to secrets service
    secrets_service = SecretsService()
    await secrets_service.store_api_key(
        db=db_session,
        provider="anthropic",
        api_key="sk-ant-test123"
    )

    # Initialize CLI engine with db session
    engine = ClaudeCodeCLIEngine(db_session=db_session)

    # Retrieve API key
    api_key = await engine._get_api_key()

    # Verify
    assert api_key == "sk-ant-test123"
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_cli_engine_execution_with_secrets(db_session, mock_docker):
    # Setup: Add API key
    secrets_service = SecretsService()
    await secrets_service.store_api_key(
        db=db_session,
        provider="anthropic",
        api_key="sk-ant-test123"
    )

    # Execute task with CLI engine
    engine = ClaudeCodeCLIEngine(db_session=db_session)
    result = await engine.execute(
        task_description="test task",
        workspace_path="/workspace/test",
        artifacts_path="/workspace/test/artifacts"
    )

    # Verify API key was used
    assert "ANTHROPIC_API_KEY=sk-ant-test123" in mock_docker.last_command

    # Verify access was logged
    logs = await secrets_service.get_access_logs(
        db=db_session,
        provider="anthropic",
        action="accessed"
    )
    assert len(logs) == 1
```

---

## Related Documentation

- **SecretsService Implementation**: `backend/app/services/secrets_service.py`
- **Secrets API Routes**: `backend/app/api/routes/secrets.py`
- **CLI Engines Implementation**: `docs/features/CLI_ENGINES_IMPLEMENTATION_STATUS.md`
- **Phase 1 Summary**: `docs/features/CLI_ENGINES_PHASE1_COMPLETE.md`

---

## Next Steps

1. ✅ **API Keys Integrated** - CLI engines now use SecretsService
2. ⏸️ **Install CLIs** - Still need to install Claude Code CLI and OpenAI CLI in agent-runtime
3. ⏸️ **Interactive Auth** - Implement bidirectional WebSocket auth flow
4. ⏸️ **Test End-to-End** - Verify complete flow with real API keys

---

**End of Secrets Integration Document**
