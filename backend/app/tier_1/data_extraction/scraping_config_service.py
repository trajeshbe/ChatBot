"""
Scraping Configuration & Compliance Service

Manages domain-specific scraping policies, robots.txt compliance,
rate limiting, API integrations, and audit logging.
"""

from typing import Dict, Optional, List, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.sql import func
import uuid
import httpx
from datetime import datetime, timedelta
from urllib.parse import urlparse
import urllib.robotparser
import asyncio
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)


class ScrapingConfigService:
    """
    Service for managing scraping configurations and compliance
    """

    def __init__(self):
        # Initialize encryption key for API keys
        # In production, load from secure key management system
        encryption_key = os.getenv("SCRAPING_CONFIG_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a key if none exists (development only)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Using generated encryption key - set SCRAPING_CONFIG_ENCRYPTION_KEY in production")
        self.cipher_suite = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage"""
        return self.cipher_suite.encrypt(api_key.encode()).decode()

    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key"""
        return self.cipher_suite.decrypt(encrypted_key.encode()).decode()

    async def create_config(
        self,
        db: AsyncSession,
        domain: str,
        allow_scraping: bool = False,
        robots_txt_compliant: bool = True,
        rate_limit_requests_per_minute: int = 10,
        rate_limit_delay_seconds: float = 2.0,
        use_api: bool = False,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        preferred_method: str = 'auto',
        notes: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a new scraping configuration for a domain
        """
        try:
            from app.models.scraping_models import ScrapingConfig

            # Encrypt API key if provided
            api_key_encrypted = None
            if api_key:
                api_key_encrypted = self._encrypt_api_key(api_key)

            config = ScrapingConfig(
                domain=domain,
                allow_scraping=allow_scraping,
                robots_txt_compliant=robots_txt_compliant,
                rate_limit_requests_per_minute=rate_limit_requests_per_minute,
                rate_limit_delay_seconds=rate_limit_delay_seconds,
                use_api=use_api,
                api_endpoint=api_endpoint,
                api_key_encrypted=api_key_encrypted,
                preferred_method=preferred_method,
                notes=notes,
                created_by=created_by
            )

            db.add(config)
            await db.commit()
            await db.refresh(config)

            logger.info(f"Created scraping config for domain: {domain}")

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error creating scraping config: {e}")
            await db.rollback()
            raise

    async def get_config(
        self,
        db: AsyncSession,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get scraping configuration for a domain
        """
        try:
            from app.models.scraping_models import ScrapingConfig

            query = select(ScrapingConfig).where(ScrapingConfig.domain == domain)
            result = await db.execute(query)
            config = result.scalar_one_or_none()

            if not config:
                return None

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error retrieving scraping config for {domain}: {e}")
            return None

    async def update_config(
        self,
        db: AsyncSession,
        domain: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update scraping configuration for a domain
        """
        try:
            from app.models.scraping_models import ScrapingConfig

            # Encrypt API key if being updated
            if 'api_key' in kwargs and kwargs['api_key']:
                kwargs['api_key_encrypted'] = self._encrypt_api_key(kwargs['api_key'])
                del kwargs['api_key']

            # Remove None values
            update_data = {k: v for k, v in kwargs.items() if v is not None}

            query = (
                update(ScrapingConfig)
                .where(ScrapingConfig.domain == domain)
                .values(**update_data)
                .returning(ScrapingConfig)
            )

            result = await db.execute(query)
            await db.commit()
            config = result.scalar_one_or_none()

            if not config:
                return None

            logger.info(f"Updated scraping config for domain: {domain}")
            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error updating scraping config for {domain}: {e}")
            await db.rollback()
            raise

    async def delete_config(
        self,
        db: AsyncSession,
        domain: str
    ) -> bool:
        """
        Delete scraping configuration for a domain
        """
        try:
            from app.models.scraping_models import ScrapingConfig

            query = delete(ScrapingConfig).where(ScrapingConfig.domain == domain)
            result = await db.execute(query)
            await db.commit()

            if result.rowcount > 0:
                logger.info(f"Deleted scraping config for domain: {domain}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting scraping config for {domain}: {e}")
            await db.rollback()
            raise

    async def list_configs(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        allow_scraping: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all scraping configurations with optional filters
        """
        try:
            from app.models.scraping_models import ScrapingConfig

            query = select(ScrapingConfig)

            # Apply filters
            if status:
                query = query.where(ScrapingConfig.status == status)
            if allow_scraping is not None:
                query = query.where(ScrapingConfig.allow_scraping == allow_scraping)

            query = query.order_by(ScrapingConfig.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            configs = result.scalars().all()

            return [self._config_to_dict(config) for config in configs]

        except Exception as e:
            logger.error(f"Error listing scraping configs: {e}")
            return []

    async def check_scraping_allowed(
        self,
        db: AsyncSession,
        url: str
    ) -> Dict[str, Any]:
        """
        Check if scraping is allowed for a given URL
        Returns detailed compliance information
        """
        try:
            from app.core.config import settings

            # Extract domain from URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Get config for domain
            config = await self.get_config(db, domain)

            if not config:
                # No config exists - check if compliance is enforced
                if settings.SCRAPING_ENFORCE_COMPLIANCE:
                    # Production mode: require explicit configuration
                    return {
                        'allowed': False,
                        'reason': 'No scraping configuration exists for this domain',
                        'status': 'no_config',
                        'recommendation': 'Create a scraping config with proper permissions'
                    }
                else:
                    # Development mode: allow by default with warning
                    logger.warning(f"⚠️ No scraping config for {domain}, allowing by default (SCRAPING_ENFORCE_COMPLIANCE=False)")
                    return {
                        'allowed': True,
                        'status': 'allowed_no_config',
                        'reason': 'No config exists but compliance enforcement is disabled',
                        'rate_limit': {
                            'requests_per_minute': 30,
                            'delay_seconds': 2.0
                        },
                        'preferred_method': 'auto'
                    }

            # Check if explicitly blocked
            if not config['allow_scraping']:
                return {
                    'allowed': False,
                    'reason': config.get('block_reason', 'Domain is blocked'),
                    'status': config['status'],
                    'alternative': config.get('notes')
                }

            # Check if API should be used instead
            if config['use_api']:
                return {
                    'allowed': True,
                    'use_api': True,
                    'api_endpoint': config['api_endpoint'],
                    'reason': 'Use official API instead of scraping',
                    'status': 'api_preferred'
                }

            # Check robots.txt compliance if enabled
            if config['robots_txt_compliant']:
                robots_allowed = await self._check_robots_txt(url)
                if not robots_allowed:
                    return {
                        'allowed': False,
                        'reason': 'Blocked by robots.txt',
                        'status': 'robots_blocked',
                        'recommendation': 'Respect robots.txt or request permission'
                    }

            # All checks passed
            return {
                'allowed': True,
                'rate_limit': {
                    'requests_per_minute': config['rate_limit_requests_per_minute'],
                    'delay_seconds': config['rate_limit_delay_seconds']
                },
                'preferred_method': config['preferred_method'],
                'status': 'allowed'
            }

        except Exception as e:
            logger.error(f"Error checking scraping allowed for {url}: {e}")
            return {
                'allowed': False,
                'reason': f'Error checking permissions: {str(e)}',
                'status': 'error'
            }

    async def _check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt
        """
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            # Fetch robots.txt
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(robots_url)

            if response.status_code == 404:
                # No robots.txt = allow all
                return True

            # Parse robots.txt
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(response.text.splitlines())

            # Check if our user agent can fetch the URL
            user_agent = "ChatBot/1.0"
            return rp.can_fetch(user_agent, url)

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # On error, default to disallow for safety
            return False

    async def log_scraping_attempt(
        self,
        db: AsyncSession,
        url: str,
        method: str,
        success: bool,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        response_time_ms: Optional[float] = None,
        bytes_downloaded: Optional[int] = None,
        robots_txt_allowed: Optional[bool] = None,
        rate_limit_respected: bool = True,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None
    ):
        """
        Log a scraping attempt to the audit log
        """
        try:
            from app.models.scraping_models import ScrapingAuditLog

            # Extract domain from URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Get config_id if exists
            config = await self.get_config(db, domain)
            config_id = uuid.UUID(config['id']) if config else None

            audit_log = ScrapingAuditLog(
                config_id=config_id,
                domain=domain,
                url=url,
                method=method,
                status_code=status_code,
                success=success,
                error_message=error_message,
                response_time_ms=response_time_ms,
                bytes_downloaded=bytes_downloaded,
                robots_txt_allowed=robots_txt_allowed,
                rate_limit_respected=rate_limit_respected,
                user_id=user_id,
                session_id=session_id
            )

            db.add(audit_log)
            await db.commit()

            # Update domain statistics
            await self._update_domain_stats(db, domain, success, response_time_ms or 0, bytes_downloaded or 0)

            logger.debug(f"Logged scraping attempt for {url}")

        except Exception as e:
            logger.error(f"Error logging scraping attempt: {e}")
            await db.rollback()

    async def _update_domain_stats(
        self,
        db: AsyncSession,
        domain: str,
        success: bool,
        response_time_ms: float,
        bytes_downloaded: int
    ):
        """
        Update aggregate statistics for a domain
        """
        try:
            from app.models.scraping_models import DomainStatistics

            # Check if stats exist
            query = select(DomainStatistics).where(DomainStatistics.domain == domain)
            result = await db.execute(query)
            stats = result.scalar_one_or_none()

            if not stats:
                # Create new stats entry
                stats = DomainStatistics(
                    domain=domain,
                    total_requests=1,
                    successful_requests=1 if success else 0,
                    failed_requests=0 if success else 1,
                    total_bytes_downloaded=bytes_downloaded,
                    avg_response_time_ms=response_time_ms,
                    first_scraped_at=func.now(),
                    last_scraped_at=func.now()
                )
                db.add(stats)
            else:
                # Update existing stats
                total_requests = stats.total_requests + 1
                successful_requests = stats.successful_requests + (1 if success else 0)
                failed_requests = stats.failed_requests + (0 if success else 1)
                total_bytes = stats.total_bytes_downloaded + bytes_downloaded

                # Calculate new average response time
                old_avg = stats.avg_response_time_ms or 0
                new_avg = ((old_avg * stats.total_requests) + response_time_ms) / total_requests

                update_query = (
                    update(DomainStatistics)
                    .where(DomainStatistics.domain == domain)
                    .values(
                        total_requests=total_requests,
                        successful_requests=successful_requests,
                        failed_requests=failed_requests,
                        total_bytes_downloaded=total_bytes,
                        avg_response_time_ms=new_avg,
                        last_scraped_at=func.now()
                    )
                )
                await db.execute(update_query)

            await db.commit()

        except Exception as e:
            logger.error(f"Error updating domain stats for {domain}: {e}")
            await db.rollback()

    async def get_domain_stats(
        self,
        db: AsyncSession,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregate statistics for a domain
        """
        try:
            from app.models.scraping_models import DomainStatistics

            query = select(DomainStatistics).where(DomainStatistics.domain == domain)
            result = await db.execute(query)
            stats = result.scalar_one_or_none()

            if not stats:
                return None

            return {
                'domain': stats.domain,
                'total_requests': stats.total_requests,
                'successful_requests': stats.successful_requests,
                'failed_requests': stats.failed_requests,
                'blocked_requests': stats.blocked_requests,
                'total_bytes_downloaded': stats.total_bytes_downloaded,
                'avg_response_time_ms': stats.avg_response_time_ms,
                'rate_limit_violations': stats.rate_limit_violations,
                'robots_txt_violations': stats.robots_txt_violations,
                'first_scraped_at': stats.first_scraped_at.isoformat() if stats.first_scraped_at else None,
                'last_scraped_at': stats.last_scraped_at.isoformat() if stats.last_scraped_at else None
            }

        except Exception as e:
            logger.error(f"Error retrieving domain stats for {domain}: {e}")
            return None

    async def get_audit_logs(
        self,
        db: AsyncSession,
        domain: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get scraping audit logs with optional filters
        """
        try:
            from app.models.scraping_models import ScrapingAuditLog

            query = select(ScrapingAuditLog)

            # Apply filters
            if domain:
                query = query.where(ScrapingAuditLog.domain == domain)
            if success is not None:
                query = query.where(ScrapingAuditLog.success == success)

            query = query.order_by(ScrapingAuditLog.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    'id': str(log.id),
                    'domain': log.domain,
                    'url': log.url,
                    'method': log.method,
                    'status_code': log.status_code,
                    'success': log.success,
                    'error_message': log.error_message,
                    'response_time_ms': log.response_time_ms,
                    'bytes_downloaded': log.bytes_downloaded,
                    'robots_txt_allowed': log.robots_txt_allowed,
                    'rate_limit_respected': log.rate_limit_respected,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []

    def _config_to_dict(self, config) -> Dict[str, Any]:
        """
        Convert ScrapingConfig model to dictionary
        """
        return {
            'id': str(config.id),
            'domain': config.domain,
            'allow_scraping': config.allow_scraping,
            'robots_txt_compliant': config.robots_txt_compliant,
            'robots_txt_url': config.robots_txt_url,
            'robots_txt_checked_at': config.robots_txt_checked_at.isoformat() if config.robots_txt_checked_at else None,
            'rate_limit_enabled': config.rate_limit_enabled,
            'rate_limit_requests_per_minute': config.rate_limit_requests_per_minute,
            'rate_limit_delay_seconds': config.rate_limit_delay_seconds,
            'max_concurrent_requests': config.max_concurrent_requests,
            'use_api': config.use_api,
            'api_endpoint': config.api_endpoint,
            'api_documentation_url': config.api_documentation_url,
            'terms_checked': config.terms_checked,
            'terms_url': config.terms_url,
            'terms_checked_at': config.terms_checked_at.isoformat() if config.terms_checked_at else None,
            'terms_notes': config.terms_notes,
            'permission_granted': config.permission_granted,
            'permission_contact': config.permission_contact,
            'permission_granted_at': config.permission_granted_at.isoformat() if config.permission_granted_at else None,
            'permission_expires_at': config.permission_expires_at.isoformat() if config.permission_expires_at else None,
            'permission_document_url': config.permission_document_url,
            'preferred_method': config.preferred_method,
            'user_agent': config.user_agent,
            'custom_headers': config.custom_headers,
            'notes': config.notes,
            'status': config.status,
            'block_reason': config.block_reason,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            'last_scraped_at': config.last_scraped_at.isoformat() if config.last_scraped_at else None
        }


# Singleton instance
scraping_config_service = ScrapingConfigService()
