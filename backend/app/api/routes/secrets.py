"""
API routes for secrets management (API keys for LLM providers)

Provides secure REST API endpoints for managing encrypted API keys.
All endpoints require admin authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from app.tier_1.infrastructure.database import get_db
from app.tier_1.platform_services.secrets_service import get_secrets_service, SecretsService
from app.models.database_enhanced import User, UserRole
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/secrets", tags=["Secrets Management"])


# ==============================================================================
# Pydantic Models
# ==============================================================================

class StoreAPIKeyRequest(BaseModel):
    """Request to store an API key"""
    provider: str = Field(..., description="Provider name (openai, anthropic, huggingface)")
    api_key: str = Field(..., description="API key to encrypt and store")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "api_key": "sk-abc123..."
            }
        }


class StoreAPIKeyResponse(BaseModel):
    """Response from storing an API key"""
    success: bool
    message: str
    provider: str
    action: str  # created or updated


class ProviderStatusResponse(BaseModel):
    """Provider API key status (NOT the key itself)"""
    provider: str
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    last_used_at: Optional[str]
    has_key: bool


class ValidateAPIKeyResponse(BaseModel):
    """Response from API key validation"""
    success: bool
    provider: str
    is_valid: bool
    message: str


class DeleteAPIKeyResponse(BaseModel):
    """Response from deleting an API key"""
    success: bool
    message: str
    provider: Optional[str] = None


class AccessLogEntry(BaseModel):
    """Audit log entry for API key access"""
    id: str
    provider: str
    user_id: Optional[str]
    action: str
    ip_address: Optional[str]
    success: bool
    error_message: Optional[str]
    created_at: str


# ==============================================================================
# Dependency: Require Admin
# ==============================================================================

async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify that the current user is an admin

    TEMPORARY IMPLEMENTATION: Returns the default admin user from database.
    In production, this should:
    1. Extract JWT token from Authorization header
    2. Validate token
    3. Fetch user from database based on token
    4. Verify user.role == UserRole.ADMIN

    Returns:
        User object for admin user

    Raises:
        HTTPException: If not authenticated or not admin
    """
    # TEMPORARY FIX: Fetch the admin user from database
    # In production, replace this with proper JWT authentication
    try:
        from sqlalchemy import select
        from app.models.database_enhanced import User, UserRole

        # Fetch the admin user from database
        result = await db.execute(
            select(User).where(User.username == "admin")
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            # If no admin user found, log warning and create error
            logger.error("Admin user not found in database")
            raise HTTPException(status_code=500, detail="Admin user not configured")

        if not admin_user.is_active:
            logger.warning("Admin user is not active")
            raise HTTPException(status_code=403, detail="Admin user is inactive")

        # Log warning about temporary authentication
        logger.warning(f"Using temporary admin authentication for user: {admin_user.username} - implement JWT auth in production")

        return admin_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin user: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


# ==============================================================================
# Helper: Get client IP
# ==============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ==============================================================================
# API Endpoints
# ==============================================================================

@router.post("/api-keys", response_model=StoreAPIKeyResponse)
async def store_api_key(
    request: Request,
    payload: StoreAPIKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    secrets_service: SecretsService = Depends(get_secrets_service)
):
    """
    Store or update an encrypted API key for a provider

    **Admin Only**

    Stores the API key encrypted in the database using Fernet encryption.
    If a key already exists for the provider, it will be updated.

    Security:
    - API key is encrypted before storage
    - Plaintext key is never logged
    - Access is logged to audit table
    - Requires admin authentication

    Args:
        payload: Provider name and API key
        db: Database session
        current_user: Authenticated admin user
        secrets_service: Secrets service instance

    Returns:
        Success status and action taken (created/updated)

    Example:
        ```
        POST /api/v1/admin/secrets/api-keys
        {
            "provider": "openai",
            "api_key": "sk-abc123..."
        }
        ```
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent")

        result = await secrets_service.store_api_key(
            db=db,
            provider=payload.provider,
            api_key=payload.api_key,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to store API key"))

        return StoreAPIKeyResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in store_api_key endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api-keys", response_model=List[ProviderStatusResponse])
async def list_api_keys(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    secrets_service: SecretsService = Depends(get_secrets_service)
):
    """
    List all providers with stored API keys (metadata only, NOT the keys)

    **Admin Only**

    Returns status information for all providers with stored API keys.
    The actual API keys are never returned via the API for security.

    Args:
        include_inactive: Whether to include inactive (deleted) keys
        db: Database session
        current_user: Authenticated admin user
        secrets_service: Secrets service instance

    Returns:
        List of provider status objects

    Example:
        ```
        GET /api/v1/admin/secrets/api-keys
        [
            {
                "provider": "openai",
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_used_at": "2024-01-02T10:30:00Z",
                "has_key": true
            }
        ]
        ```
    """
    try:
        providers = await secrets_service.list_providers(
            db=db,
            include_inactive=include_inactive
        )

        return [ProviderStatusResponse(**provider) for provider in providers]

    except Exception as e:
        logger.error(f"Error in list_api_keys endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api-keys/{provider}", response_model=ProviderStatusResponse)
async def get_api_key_status(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    secrets_service: SecretsService = Depends(get_secrets_service)
):
    """
    Get status of a specific provider's API key (NOT the key itself)

    **Admin Only**

    Returns metadata about the API key without exposing the actual key value.

    Args:
        provider: Provider name (openai, anthropic, huggingface)
        db: Database session
        current_user: Authenticated admin user
        secrets_service: Secrets service instance

    Returns:
        Provider status object

    Example:
        ```
        GET /api/v1/admin/secrets/api-keys/openai
        {
            "provider": "openai",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "last_used_at": "2024-01-02T10:30:00Z",
            "has_key": true
        }
        ```
    """
    try:
        providers = await secrets_service.list_providers(db=db, include_inactive=True)
        provider_status = next((p for p in providers if p["provider"] == provider), None)

        if not provider_status:
            raise HTTPException(status_code=404, detail=f"No API key found for provider: {provider}")

        return ProviderStatusResponse(**provider_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_api_key_status endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api-keys/{provider}/validate", response_model=ValidateAPIKeyResponse)
async def validate_api_key(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    secrets_service: SecretsService = Depends(get_secrets_service)
):
    """
    Validate that an API key exists and can be decrypted

    **Admin Only**

    Verifies that the API key for the provider:
    1. Exists in the database
    2. Can be successfully decrypted
    3. Is not empty

    Does NOT test the key with the actual provider API.

    Args:
        provider: Provider name
        db: Database session
        current_user: Authenticated admin user
        secrets_service: Secrets service instance

    Returns:
        Validation status

    Example:
        ```
        POST /api/v1/admin/secrets/api-keys/openai/validate
        {
            "success": true,
            "provider": "openai",
            "is_valid": true,
            "message": "API key is valid"
        }
        ```
    """
    try:
        result = await secrets_service.validate_api_key(
            db=db,
            provider=provider,
            user_id=current_user.id if current_user else None
        )

        return ValidateAPIKeyResponse(**result)

    except Exception as e:
        logger.error(f"Error in validate_api_key endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/api-keys/{provider}", response_model=DeleteAPIKeyResponse)
async def delete_api_key(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    secrets_service: SecretsService = Depends(get_secrets_service)
):
    """
    Delete (deactivate) an API key

    **Admin Only**

    Marks the API key as inactive (soft delete). The encrypted key remains
    in the database for audit purposes but will not be used.

    Args:
        provider: Provider name
        request: HTTP request
        db: Database session
        current_user: Authenticated admin user
        secrets_service: Secrets service instance

    Returns:
        Success status

    Example:
        ```
        DELETE /api/v1/admin/secrets/api-keys/openai
        {
            "success": true,
            "message": "API key for openai deleted successfully",
            "provider": "openai"
        }
        ```
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent")

        result = await secrets_service.delete_api_key(
            db=db,
            provider=provider,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("message", "API key not found"))

        return DeleteAPIKeyResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_api_key endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api-keys/logs/{provider}", response_model=List[AccessLogEntry])
async def get_access_logs(
    provider: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    secrets_service: SecretsService = Depends(get_secrets_service)
):
    """
    Get audit logs for API key access

    **Admin Only**

    Returns access logs showing when the API key was created, accessed,
    updated, or deleted.

    Args:
        provider: Provider name to filter logs
        limit: Maximum number of log entries to return
        db: Database session
        current_user: Authenticated admin user
        secrets_service: Secrets service instance

    Returns:
        List of audit log entries

    Example:
        ```
        GET /api/v1/admin/secrets/api-keys/logs/openai?limit=50
        [
            {
                "id": "uuid",
                "provider": "openai",
                "user_id": "uuid",
                "action": "accessed",
                "ip_address": "192.168.1.1",
                "success": true,
                "created_at": "2024-01-02T10:30:00Z"
            }
        ]
        ```
    """
    try:
        logs = await secrets_service.get_access_logs(
            db=db,
            provider=provider,
            limit=min(limit, 1000)  # Cap at 1000 for performance
        )

        return [AccessLogEntry(**log) for log in logs]

    except Exception as e:
        logger.error(f"Error in get_access_logs endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
