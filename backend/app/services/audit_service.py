"""
Audit Logging Service

Tracks all user actions for compliance and security auditing.
"""

from typing import Dict, Optional, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
import uuid
import json

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for comprehensive audit logging
    """

    async def log_action(
        self,
        db: AsyncSession,
        action: str,  # ActionType enum value
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        latency_ms: Optional[float] = None,
        meta_info: Optional[Dict] = None
    ):
        """
        Log an auditable action to the database
        """
        try:
            from app.models.database_enhanced import AuditLog, ActionType, ChatSession

            # Convert session_id string to UUID if provided
            session_uuid = None
            if session_id:
                from sqlalchemy import select
                session_query = select(ChatSession).where(ChatSession.session_id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                if session:
                    session_uuid = session.id

            # Sanitize sensitive data
            sanitized_request = self._sanitize_data(request_data) if request_data else None
            sanitized_response = self._sanitize_data(response_data) if response_data else None

            audit_log = AuditLog(
                user_id=user_id,
                session_id=session_uuid,
                action=ActionType(action),
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                request_data=sanitized_request,
                response_data=sanitized_response,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=status_code,
                error_message=error_message,
                latency_ms=latency_ms,
                meta_info=meta_info
            )

            db.add(audit_log)
            await db.commit()

            logger.debug(f"Audit log created: {action} by user {user_id}")

        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            await db.rollback()
            # Don't raise - audit logging should not break the main flow

    async def log_query(
        self,
        db: AsyncSession,
        query_text: str,
        user_id: Optional[uuid.UUID],
        session_id: Optional[str],
        model_id: str,
        response: Dict,
        latency_ms: float,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Convenience method for logging queries"""
        await self.log_action(
            db=db,
            action='query',
            user_id=user_id,
            session_id=session_id,
            resource_type='query',
            description=f"Query: {query_text[:100]}...",
            request_data={'query': query_text, 'model_id': model_id},
            response_data={
                'model': response.get('model'),
                'tokens': response.get('tokens_used'),
                'num_sources': response.get('num_sources')
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=200,
            latency_ms=latency_ms
        )

    async def log_upload(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        filename: str,
        file_size: int,
        user_id: Optional[uuid.UUID],
        session_id: Optional[str],
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Convenience method for logging file uploads"""
        await self.log_action(
            db=db,
            action='upload',
            user_id=user_id,
            session_id=session_id,
            resource_type='document',
            resource_id=document_id,
            description=f"Uploaded: {filename} ({file_size} bytes)",
            request_data={'filename': filename, 'file_size': file_size},
            ip_address=ip_address,
            status_code=200 if success else 500,
            error_message=error_message
        )

    async def log_scrape(
        self,
        db: AsyncSession,
        url: str,
        document_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
        session_id: Optional[str],
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Convenience method for logging web scrapes"""
        await self.log_action(
            db=db,
            action='scrape',
            user_id=user_id,
            session_id=session_id,
            resource_type='document',
            resource_id=document_id,
            description=f"Scraped: {url}",
            request_data={'url': url},
            ip_address=ip_address,
            status_code=200 if success else 500,
            error_message=error_message
        )

    async def log_login(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ):
        """Convenience method for logging login attempts"""
        await self.log_action(
            db=db,
            action='login',
            user_id=user_id if success else None,
            description=f"Login {'successful' if success else 'failed'}: {username}",
            request_data={'username': username},
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=200 if success else 401
        )

    async def get_user_activity(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Retrieve audit logs for a specific user"""
        try:
            from app.models.database_enhanced import AuditLog
            from sqlalchemy import select

            query = select(AuditLog).where(
                AuditLog.user_id == user_id
            ).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    'id': str(log.id),
                    'action': log.action.value if log.action else None,
                    'resource_type': log.resource_type,
                    'resource_id': str(log.resource_id) if log.resource_id else None,
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'status_code': log.status_code,
                    'created_at': log.created_at.isoformat(),
                    'latency_ms': log.latency_ms
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"Error retrieving user activity: {e}")
            return []

    async def get_session_activity(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve audit logs for a specific session"""
        try:
            from app.models.database_enhanced import AuditLog, ChatSession
            from sqlalchemy import select

            # Get session UUID
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                return []

            query = select(AuditLog).where(
                AuditLog.session_id == session.id
            ).order_by(AuditLog.created_at.desc()).limit(limit)

            result = await db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    'id': str(log.id),
                    'action': log.action.value if log.action else None,
                    'resource_type': log.resource_type,
                    'description': log.description,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"Error retrieving session activity: {e}")
            return []

    def _sanitize_data(self, data: Any) -> Any:
        """
        Remove sensitive fields from logged data
        """
        if not isinstance(data, dict):
            return data

        sensitive_fields = ['password', 'api_key', 'token', 'secret', 'hashed_password']

        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_data(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized


# Singleton instance
audit_service = AuditService()
