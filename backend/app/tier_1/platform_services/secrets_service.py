"""
Secrets Management Service - Database-backed encrypted API key storage

This service provides secure storage and retrieval of API keys for LLM providers
using Fernet encryption. Keys are stored encrypted in PostgreSQL and never logged
in plaintext.

Security Features:
- Fernet symmetric encryption (AES-128)
- Master key stored as environment variable (not in database)
- Audit logging for all access
- IP address tracking
- Key rotation support via encryption_key_id
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import base64

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.models.database_enhanced import APICredential, APIKeyAccessLog
from app.tier_1.infrastructure.config import settings

logger = logging.getLogger(__name__)


class SecretsService:
    """Service for managing encrypted API keys"""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize secrets service with master encryption key

        Args:
            master_key: Base64-encoded Fernet key. If not provided, reads from environment.

        Raises:
            ValueError: If master key is not set or invalid
        """
        self.master_key = master_key or os.getenv("MASTER_ENCRYPTION_KEY")

        if not self.master_key:
            raise ValueError(
                "MASTER_ENCRYPTION_KEY not set. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        try:
            self.cipher = Fernet(self.master_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid MASTER_ENCRYPTION_KEY: {e}")


    async def store_api_key(
        self,
        db: AsyncSession,
        provider: str,
        api_key: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store encrypted API key in database

        Args:
            db: Database session
            provider: Provider name (openai, anthropic, huggingface)
            api_key: Plaintext API key to encrypt and store
            user_id: ID of user storing the key
            ip_address: IP address of requester
            user_agent: User agent string

        Returns:
            Dictionary with success status and message

        Security Notes:
            - API key is encrypted before storage
            - Plaintext key is never logged
            - Access is logged to audit table
        """
        try:
            # Encrypt the API key
            encrypted_key = self.cipher.encrypt(api_key.encode())
            # Store as bytes directly (column is bytea, not text)

            # Check if provider already exists
            result = await db.execute(
                select(APICredential).where(APICredential.provider == provider)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                await db.execute(
                    update(APICredential)
                    .where(APICredential.provider == provider)
                    .values(
                        api_key_encrypted=encrypted_key,
                        updated_at=datetime.utcnow(),
                        is_active=True
                    )
                )
                action = "updated"
            else:
                # Create new
                new_credential = APICredential(
                    provider=provider,
                    api_key_encrypted=encrypted_key,
                    created_by=user_id,
                    is_active=True
                )
                db.add(new_credential)
                action = "created"

            # Log access
            await self._log_access(
                db=db,
                provider=provider,
                user_id=user_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )

            await db.commit()

            logger.info(f"API key {action} for provider: {provider}")

            return {
                "success": True,
                "message": f"API key for {provider} {action} successfully",
                "provider": provider,
                "action": action
            }

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error storing API key for {provider}: {e}")

            # Log failed attempt
            await self._log_access(
                db=db,
                provider=provider,
                user_id=user_id,
                action="created",
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e)
            )

            return {
                "success": False,
                "message": "Database error occurred",
                "error": str(e)
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error storing API key for {provider}: {e}")

            return {
                "success": False,
                "message": "Unexpected error occurred",
                "error": str(e)
            }


    async def get_api_key(
        self,
        db: AsyncSession,
        provider: str,
        user_id: Optional[UUID] = None
    ) -> Optional[str]:
        """
        Retrieve and decrypt API key from database

        Args:
            db: Database session
            provider: Provider name (openai, anthropic, huggingface)
            user_id: ID of user accessing the key (for audit logging)

        Returns:
            Decrypted API key or None if not found

        Security Notes:
            - Updates last_used_at timestamp
            - Logs access to audit table
            - Never logs decrypted key
        """
        try:
            # Fetch encrypted key
            result = await db.execute(
                select(APICredential)
                .where(APICredential.provider == provider)
                .where(APICredential.is_active == True)
            )
            credential = result.scalar_one_or_none()

            if not credential:
                logger.warning(f"No active API key found for provider: {provider}")
                return None

            # Decrypt key
            try:
                # api_key_encrypted is stored as bytes (bytea column)
                decrypted_bytes = self.cipher.decrypt(credential.api_key_encrypted)
                api_key = decrypted_bytes.decode('utf-8')
            except InvalidToken:
                logger.error(f"Failed to decrypt API key for {provider} - invalid token or corrupted data")
                return None

            # Update last used timestamp
            await db.execute(
                update(APICredential)
                .where(APICredential.provider == provider)
                .values(last_used_at=datetime.utcnow())
            )

            # Log access
            await self._log_access(
                db=db,
                provider=provider,
                user_id=user_id,
                action="accessed",
                success=True
            )

            await db.commit()

            logger.info(f"API key retrieved for provider: {provider}")

            return api_key

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving API key for {provider}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error retrieving API key for {provider}: {e}")
            return None


    async def delete_api_key(
        self,
        db: AsyncSession,
        provider: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete API key from database

        Args:
            db: Database session
            provider: Provider name
            user_id: ID of user deleting the key
            ip_address: IP address of requester
            user_agent: User agent string

        Returns:
            Dictionary with success status and message
        """
        try:
            # Mark as inactive instead of deleting (soft delete)
            result = await db.execute(
                update(APICredential)
                .where(APICredential.provider == provider)
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            if result.rowcount == 0:
                return {
                    "success": False,
                    "message": f"No API key found for provider: {provider}"
                }

            # Log deletion
            await self._log_access(
                db=db,
                provider=provider,
                user_id=user_id,
                action="deleted",
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )

            await db.commit()

            logger.info(f"API key deleted for provider: {provider}")

            return {
                "success": True,
                "message": f"API key for {provider} deleted successfully",
                "provider": provider
            }

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error deleting API key for {provider}: {e}")

            return {
                "success": False,
                "message": "Database error occurred",
                "error": str(e)
            }


    async def list_providers(
        self,
        db: AsyncSession,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all providers with stored API keys (metadata only, not the keys)

        Args:
            db: Database session
            include_inactive: Whether to include inactive keys

        Returns:
            List of provider metadata dictionaries
        """
        try:
            query = select(APICredential)

            if not include_inactive:
                query = query.where(APICredential.is_active == True)

            result = await db.execute(query.order_by(APICredential.provider))
            credentials = result.scalars().all()

            return [
                {
                    "provider": cred.provider,
                    "is_active": cred.is_active,
                    "created_at": cred.created_at.isoformat() if cred.created_at else None,
                    "updated_at": cred.updated_at.isoformat() if cred.updated_at else None,
                    "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
                    "has_key": bool(cred.api_key_encrypted)
                }
                for cred in credentials
            ]

        except SQLAlchemyError as e:
            logger.error(f"Database error listing providers: {e}")
            return []


    async def validate_api_key(
        self,
        db: AsyncSession,
        provider: str,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Validate that an API key exists and can be decrypted

        Args:
            db: Database session
            provider: Provider name
            user_id: ID of user validating the key

        Returns:
            Dictionary with validation status
        """
        try:
            api_key = await self.get_api_key(db, provider, user_id)

            is_valid = api_key is not None and len(api_key) > 0

            # Log validation
            await self._log_access(
                db=db,
                provider=provider,
                user_id=user_id,
                action="validated",
                success=is_valid
            )

            return {
                "success": True,
                "provider": provider,
                "is_valid": is_valid,
                "message": "API key is valid" if is_valid else "API key not found or invalid"
            }

        except Exception as e:
            logger.error(f"Error validating API key for {provider}: {e}")

            return {
                "success": False,
                "provider": provider,
                "is_valid": False,
                "error": str(e)
            }


    async def _log_access(
        self,
        db: AsyncSession,
        provider: str,
        user_id: Optional[UUID],
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Log API key access to audit table

        Args:
            db: Database session
            provider: Provider name
            user_id: User ID
            action: Action performed (created, accessed, deleted, validated)
            ip_address: IP address
            user_agent: User agent string
            success: Whether the operation succeeded
            error_message: Error message if failed
        """
        try:
            log_entry = APIKeyAccessLog(
                provider=provider,
                user_id=user_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            db.add(log_entry)
            # Don't commit here - let caller commit

        except Exception as e:
            logger.error(f"Failed to log API key access: {e}")
            # Don't raise - logging failure shouldn't break the main operation


    async def get_access_logs(
        self,
        db: AsyncSession,
        provider: Optional[str] = None,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs for API key access

        Args:
            db: Database session
            provider: Filter by provider
            user_id: Filter by user
            action: Filter by action type
            limit: Maximum number of logs to return

        Returns:
            List of audit log entries
        """
        try:
            query = select(APIKeyAccessLog)

            if provider:
                query = query.where(APIKeyAccessLog.provider == provider)
            if user_id:
                query = query.where(APIKeyAccessLog.user_id == user_id)
            if action:
                query = query.where(APIKeyAccessLog.action == action)

            query = query.order_by(APIKeyAccessLog.created_at.desc()).limit(limit)

            result = await db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    "id": str(log.id),
                    "provider": log.provider,
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "ip_address": log.ip_address,
                    "success": log.success,
                    "error_message": log.error_message,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving access logs: {e}")
            return []


# Helper function to generate master encryption key
def generate_master_key() -> str:
    """
    Generate a new Fernet master encryption key

    Returns:
        Base64-encoded Fernet key as string

    Usage:
        Add this to your .env file:
        MASTER_ENCRYPTION_KEY=<generated_key>
    """
    return Fernet.generate_key().decode()


# Helper function to get or create secrets service instance
_secrets_service_instance: Optional[SecretsService] = None

def get_secrets_service() -> SecretsService:
    """
    Get singleton instance of SecretsService

    Returns:
        SecretsService instance

    Raises:
        ValueError: If MASTER_ENCRYPTION_KEY not set
    """
    global _secrets_service_instance

    if _secrets_service_instance is None:
        _secrets_service_instance = SecretsService()

    return _secrets_service_instance
