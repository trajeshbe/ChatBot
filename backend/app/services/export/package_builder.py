"""
Package Builder Service

Orchestrates the complete POC export process by coordinating all export services.

This is the main orchestrator that:
1. Creates export job
2. Calls ConfigurationExtractor
3. Calls DocumentMigrator
4. Calls InfrastructureGenerator
5. Generates license key
6. Creates final package
7. Updates job status

Export Process Flow:
┌─────────────────────────────────────────────────────────┐
│ 1. Create Export Job (status: pending)                  │
│ 2. Extract Configuration → config.json                  │
│ 3. Export Documents → data/documents/                   │
│ 4. Export Embeddings → data/embeddings.parquet          │
│ 5. Generate Infrastructure → infrastructure/            │
│ 6. Generate License → license.key                       │
│ 7. Package Everything → .tar.gz                         │
│ 8. Update Job (status: completed)                       │
└─────────────────────────────────────────────────────────┘

Author: Claude Code
Date: 2026-01-03
Phase: 1 - Core Export Engine
"""

import logging
import os
import json
import shutil
import tarfile
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.export_wizard import (
    ExportJob,
    ExportPackage,
    ExportAuditLog,
    ExportStatus,
    DeploymentType,
    LicenseTier
)
from .configuration_extractor import ConfigurationExtractor
from .document_migrator import DocumentMigrator, ExportStats
from .infrastructure_generator import InfrastructureGenerator, InfrastructureOptions
from .module_code_extractor import ModuleCodeExtractor, ModuleCodeStats
from .model_exporter import ModelExporter, ModelExportInfo

logger = logging.getLogger(__name__)


class PackageBuilder:
    """Orchestrates complete POC export process."""

    def __init__(self, db: AsyncSession):
        """
        Initialize PackageBuilder.

        Args:
            db: Async database session
        """
        self.db = db
        self.config_extractor = ConfigurationExtractor(db)
        self.doc_migrator = DocumentMigrator(db)
        self.infra_generator = InfrastructureGenerator()
        self.code_extractor = ModuleCodeExtractor()
        self.model_exporter = ModelExporter(db)

    async def build_export_package(
        self,
        module_name: str,
        customer_name: str,
        deployment_type: DeploymentType,
        license_tier: LicenseTier = LicenseTier.PROFESSIONAL,
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> ExportJob:
        """
        Build complete export package.

        This is the main entry point for export process.

        Args:
            module_name: Module to export (e.g., "british_council")
            customer_name: Customer name for licensing
            deployment_type: Type of deployment infrastructure
            license_tier: License tier (starter, professional, enterprise)
            tenant_id: Optional tenant ID for filtering
            session_id: Optional session ID for filtering
            options: Optional export options
            created_by: User who initiated export
            job_id: Optional existing job ID to update (if None, creates new job)

        Returns:
            ExportJob with status and results

        Raises:
            RuntimeError: If export fails at any stage
        """
        logger.info("="*80)
        logger.info(f"🚀 Starting POC Export Process")
        logger.info(f"   Module: {module_name}")
        logger.info(f"   Customer: {customer_name}")
        logger.info(f"   Deployment: {deployment_type.value}")
        logger.info(f"   License Tier: {license_tier.value}")
        if job_id:
            logger.info(f"   Job ID: {job_id} (updating existing)")
        logger.info("="*80)

        # 1. Get or create export job
        if job_id:
            # Update existing job
            from uuid import UUID
            result = await self.db.execute(
                select(ExportJob).where(ExportJob.id == UUID(job_id))
            )
            export_job = result.scalar_one_or_none()
            if not export_job:
                raise ValueError(f"Export job {job_id} not found")

            # Update to in-progress
            export_job.status = ExportStatus.IN_PROGRESS
            export_job.started_at = datetime.utcnow()
            await self.db.commit()
            logger.info(f"✅ Found existing job: {job_id}")
        else:
            # Create new job
            export_job = await self._create_export_job(
                module_name=module_name,
                customer_name=customer_name,
                deployment_type=deployment_type,
                license_tier=license_tier,
                tenant_id=tenant_id,
                options=options or {},
                created_by=created_by
            )
            logger.info(f"✅ Created new job: {export_job.id}")

        try:
            # Create temporary export directory
            export_dir = Path(f"/tmp/exports/{export_job.id}")
            export_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"📁 Export directory: {export_dir}")

            # 2. Update status: Extract configuration
            await self._update_job_progress(export_job, 10, "Extracting configuration")

            config = await self.config_extractor.extract_module_config(
                module_name=module_name,
                tenant_id=tenant_id
            )

            # Save configuration
            config_path = export_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"✅ Configuration extracted: {len(json.dumps(config))} bytes")

            # Generate .env template
            env_template = self.config_extractor.generate_env_template(config)
            env_template_path = export_dir / ".env.example"
            with open(env_template_path, 'w') as f:
                f.write(env_template)

            logger.info(f"✅ Environment template generated")

            # 3. Update status: Export documents
            await self._update_job_progress(export_job, 30, "Exporting documents and embeddings")

            doc_stats = await self.doc_migrator.export_documents(
                tenant_id=tenant_id,
                module_name=module_name,
                export_dir=str(export_dir),
                include_embeddings=options.get('include_embeddings', True),
                session_id=session_id
            )

            logger.info(f"✅ Documents exported: {doc_stats.total_documents} docs, {doc_stats.total_embeddings} embeddings")

            # 4. Update status: Extract module source code
            await self._update_job_progress(export_job, 40, "Extracting module source code")

            code_stats = await self.code_extractor.extract_module_code(
                module_name=module_name,
                export_dir=export_dir
            )

            logger.info(f"✅ Module code extracted:")
            logger.info(f"   Backend: {code_stats.backend_files_copied} files")
            logger.info(f"   Frontend: {code_stats.frontend_files_copied} files")
            logger.info(f"   Tier 1 deps: {code_stats.tier1_files_copied} files")
            logger.info(f"   Python deps: {code_stats.python_dependencies}")
            logger.info(f"   NPM deps: {code_stats.npm_dependencies}")

            # 5. Update status: Export fine-tuned models
            await self._update_job_progress(export_job, 50, "Exporting fine-tuned models")

            exported_models = await self.model_exporter.export_module_models(
                module_name=module_name,
                export_dir=export_dir,
                config=config
            )

            if exported_models:
                total_model_size = sum(m.size_bytes for m in exported_models)
                logger.info(f"✅ Exported {len(exported_models)} models ({total_model_size / (1024**3):.2f} GB)")
            else:
                logger.info(f"ℹ️  No custom models to export (using API providers)")

            # 6. Update status: Generate infrastructure
            await self._update_job_progress(export_job, 65, "Generating deployment infrastructure")

            infra_options = InfrastructureOptions(
                enable_monitoring=options.get('include_monitoring', True),
                enable_backups=options.get('include_backups', True),
                enable_ssl=options.get('enable_ssl', True),
                security_level=options.get('security_level', 'standard')
            )

            infra_result = await self.infra_generator.generate_infrastructure(
                module_name=module_name,
                deployment_type=deployment_type,
                export_dir=str(export_dir),
                config=config,
                options=infra_options
            )

            logger.info(f"✅ Infrastructure generated: {infra_result.total_files} files")

            # 7. Update status: Generate license
            await self._update_job_progress(export_job, 80, "Generating license key")

            license_key = await self._generate_license(
                customer_name=customer_name,
                license_tier=license_tier,
                module_name=module_name,
                max_users=options.get('max_users'),
                expiry_days=options.get('license_expiry_days', 365)
            )

            # Save license
            license_path = export_dir / "LICENSE.key"
            with open(license_path, 'w') as f:
                f.write(license_key)

            logger.info(f"✅ License key generated")

            # 8. Update status: Creating package
            await self._update_job_progress(export_job, 90, "Creating export package")

            package_path = await self._create_package(
                export_dir=export_dir,
                job_id=export_job.id,
                module_name=module_name,
                customer_name=customer_name
            )

            package_size = os.path.getsize(package_path)

            logger.info(f"✅ Package created: {package_path}")
            logger.info(f"   Size: {package_size / (1024*1024):.2f} MB")

            # 9. Create export package record
            export_package = await self._create_export_package(
                export_job=export_job,
                package_path=package_path,
                package_size=package_size,
                license_key=license_key,
                manifest={
                    "configuration": str(config_path),
                    "documents_exported": doc_stats.total_documents,
                    "embeddings_exported": doc_stats.total_embeddings,
                    "infrastructure_files": infra_result.total_files,
                    "deployment_type": deployment_type.value,
                    "readme": infra_result.readme_path,
                    "backend_files": code_stats.backend_files_copied,
                    "frontend_files": code_stats.frontend_files_copied,
                    "tier1_files": code_stats.tier1_files_copied,
                    "python_dependencies": code_stats.python_dependencies,
                    "npm_dependencies": code_stats.npm_dependencies,
                    "models_exported": len(exported_models),
                    "model_details": [
                        {
                            "name": m.model_name,
                            "type": m.model_type,
                            "is_finetuned": m.is_finetuned,
                            "size_gb": round(m.size_bytes / (1024**3), 2)
                        }
                        for m in exported_models
                    ] if exported_models else []
                }
            )

            # 10. Update job status: Complete
            await self._complete_export_job(
                export_job=export_job,
                export_package=export_package,
                stats={
                    "documents_exported": doc_stats.total_documents,
                    "embeddings_exported": doc_stats.total_embeddings,
                    "total_chunks": doc_stats.total_chunks,
                    "configuration_items": len(config.keys()),
                    "processing_time_seconds": doc_stats.processing_time_seconds,
                    "package_size_bytes": package_size,
                    "infrastructure_files": infra_result.total_files,
                    "backend_files": code_stats.backend_files_copied,
                    "frontend_files": code_stats.frontend_files_copied,
                    "tier1_files": code_stats.tier1_files_copied,
                    "python_dependencies": code_stats.python_dependencies,
                    "npm_dependencies": code_stats.npm_dependencies,
                    "models_exported": len(exported_models),
                    "total_model_size_gb": round(sum(m.size_bytes for m in exported_models) / (1024**3), 2) if exported_models else 0
                }
            )

            # 11. Log audit event
            await self._log_audit_event(
                event_type="export_completed",
                export_job_id=export_job.id,
                export_package_id=export_package.id,
                user_id=created_by,
                details={
                    "module": module_name,
                    "customer": customer_name,
                    "deployment_type": deployment_type.value,
                    "license_tier": license_tier.value,
                    "package_size_mb": round(package_size / (1024*1024), 2),
                    "includes_source_code": True,
                    "includes_models": len(exported_models) > 0,
                    "models_count": len(exported_models)
                }
            )

            logger.info("="*80)
            logger.info(f"✅ POC Export Complete!")
            logger.info(f"   Job ID: {export_job.id}")
            logger.info(f"   Package ID: {export_package.id}")
            logger.info(f"   Package: {package_path}")
            logger.info(f"   Size: {package_size / (1024*1024):.2f} MB")
            logger.info("="*80)

            return export_job

        except Exception as e:
            # Handle failure
            logger.error(f"❌ Export failed: {e}", exc_info=True)

            await self._fail_export_job(
                export_job=export_job,
                error_message=str(e),
                error_details={"exception": type(e).__name__}
            )

            # Log failure
            await self._log_audit_event(
                event_type="export_failed",
                export_job_id=export_job.id,
                user_id=created_by,
                status="failure",
                error_message=str(e),
                details={
                    "module": module_name,
                    "customer": customer_name,
                    "error_type": type(e).__name__
                }
            )

            raise RuntimeError(f"Export failed: {e}")

    async def _create_export_job(
        self,
        module_name: str,
        customer_name: str,
        deployment_type: DeploymentType,
        license_tier: LicenseTier,
        tenant_id: Optional[str],
        options: Dict[str, Any],
        created_by: Optional[str]
    ) -> ExportJob:
        """Create export job record."""

        job_name = f"{customer_name}_{module_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        export_job = ExportJob(
            job_name=job_name,
            tenant_id=tenant_id or "default",
            module_name=module_name,
            created_by=created_by,
            deployment_type=deployment_type,
            license_tier=license_tier,
            customer_name=customer_name,
            customer_email=options.get('customer_email'),
            license_expiry=datetime.utcnow() + timedelta(days=options.get('license_expiry_days', 365)),
            max_users=options.get('max_users'),
            options=options,
            status=ExportStatus.PENDING,
            progress_percentage=0.0,
            current_step="Initializing export"
        )

        self.db.add(export_job)
        await self.db.commit()
        await self.db.refresh(export_job)

        logger.info(f"📝 Created export job: {export_job.id}")

        # Log audit event
        await self._log_audit_event(
            event_type="export_initiated",
            export_job_id=export_job.id,
            user_id=created_by,
            details={
                "module": module_name,
                "customer": customer_name,
                "deployment_type": deployment_type.value,
                "license_tier": license_tier.value
            }
        )

        return export_job

    async def _update_job_progress(
        self,
        job: ExportJob,
        progress: float,
        step: str
    ) -> None:
        """Update export job progress."""

        job.status = ExportStatus.IN_PROGRESS
        job.progress_percentage = progress
        job.current_step = step

        if not job.started_at:
            job.started_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"📊 Progress: {progress}% - {step}")

    async def _generate_license(
        self,
        customer_name: str,
        license_tier: LicenseTier,
        module_name: str,
        max_users: Optional[int],
        expiry_days: int = 365
    ) -> str:
        """
        Generate RSA-4096 signed license key.

        In production, this would:
        1. Use actual RSA-4096 private key
        2. Sign license data digitally
        3. Encode in base64

        For now, generating a structured license key.

        Args:
            customer_name: Customer name
            license_tier: License tier
            module_name: Module name
            max_users: Maximum users allowed
            expiry_days: License validity in days

        Returns:
            License key string
        """
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.backends import default_backend
        import base64

        license_data = {
            "customer": customer_name,
            "tier": license_tier.value,
            "module": module_name,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=expiry_days)).isoformat(),
            "max_users": max_users,
            "license_id": str(uuid4())
        }

        # Serialize license data
        license_json = json.dumps(license_data, sort_keys=True)

        # In production: Load actual private key
        # For now: Generate temporary key (demo purposes only)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )

        # Sign license data
        signature = private_key.sign(
            license_json.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Encode license
        license_key = base64.b64encode(
            json.dumps({
                "data": license_data,
                "signature": base64.b64encode(signature).decode()
            }).encode()
        ).decode()

        return license_key

    async def _create_package(
        self,
        export_dir: Path,
        job_id: str,
        module_name: str,
        customer_name: str
    ) -> str:
        """
        Create compressed package (.tar.gz) of export.

        Args:
            export_dir: Export directory
            job_id: Export job ID
            module_name: Module name
            customer_name: Customer name

        Returns:
            Path to package file
        """
        package_name = f"{customer_name}_{module_name}_{job_id}.tar.gz"
        package_path = f"/tmp/packages/{package_name}"

        # Create packages directory
        os.makedirs("/tmp/packages", exist_ok=True)

        # Create tarball
        with tarfile.open(package_path, "w:gz") as tar:
            tar.add(export_dir, arcname=f"{customer_name}_{module_name}")

        logger.info(f"📦 Package created: {package_path}")

        return package_path

    async def _create_export_package(
        self,
        export_job: ExportJob,
        package_path: str,
        package_size: int,
        license_key: str,
        manifest: Dict[str, Any]
    ) -> ExportPackage:
        """Create export package record."""

        import hashlib

        # Calculate checksum
        sha256 = hashlib.sha256()
        with open(package_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        checksum = sha256.hexdigest()

        package = ExportPackage(
            package_name=f"{export_job.customer_name}_{export_job.module_name}",
            version="1.0.0",
            tenant_id=export_job.tenant_id,
            module_name=export_job.module_name,
            export_job_id=export_job.id,
            deployment_type=export_job.deployment_type,
            package_path=package_path,
            package_size_bytes=package_size,
            checksum_sha256=checksum,
            manifest=manifest,
            license_key=license_key,
            license_tier=export_job.license_tier,
            license_expires_at=export_job.license_expiry,
            customer_name=export_job.customer_name,
            customer_email=export_job.customer_email,
            max_users=export_job.max_users
        )

        self.db.add(package)
        await self.db.commit()
        await self.db.refresh(package)

        logger.info(f"📦 Export package record created: {package.id}")

        return package

    async def _complete_export_job(
        self,
        export_job: ExportJob,
        export_package: ExportPackage,
        stats: Dict[str, Any]
    ) -> None:
        """Mark export job as completed."""

        export_job.status = ExportStatus.COMPLETED
        export_job.progress_percentage = 100.0
        export_job.current_step = "Export complete"
        export_job.completed_at = datetime.utcnow()
        export_job.export_package_id = export_package.id
        export_job.package_path = export_package.package_path
        export_job.package_size_bytes = export_package.package_size_bytes
        export_job.stats = stats

        await self.db.commit()

        logger.info(f"✅ Export job completed: {export_job.id}")

    async def _fail_export_job(
        self,
        export_job: ExportJob,
        error_message: str,
        error_details: Dict[str, Any]
    ) -> None:
        """Mark export job as failed."""

        export_job.status = ExportStatus.FAILED
        export_job.completed_at = datetime.utcnow()
        export_job.error_message = error_message
        export_job.error_details = error_details

        await self.db.commit()

        logger.error(f"❌ Export job failed: {export_job.id}")

    async def _log_audit_event(
        self,
        event_type: str,
        export_job_id: Optional[str] = None,
        export_package_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit event."""

        audit_log = ExportAuditLog(
            event_type=event_type,
            export_job_id=export_job_id,
            export_package_id=export_package_id,
            user_id=user_id,
            details=details or {},
            status=status,
            error_message=error_message
        )

        self.db.add(audit_log)
        await self.db.commit()

    async def get_export_job_status(self, job_id: str) -> Optional[ExportJob]:
        """
        Get export job status.

        Args:
            job_id: Export job ID

        Returns:
            ExportJob or None if not found
        """
        result = await self.db.execute(
            select(ExportJob).where(ExportJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def cancel_export_job(self, job_id: str) -> bool:
        """
        Cancel running export job.

        Args:
            job_id: Export job ID

        Returns:
            True if cancelled, False if not found or already complete
        """
        result = await self.db.execute(
            select(ExportJob).where(ExportJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return False

        if job.status in [ExportStatus.COMPLETED, ExportStatus.FAILED, ExportStatus.CANCELLED]:
            return False

        job.status = ExportStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        job.error_message = "Cancelled by user"

        await self.db.commit()

        logger.info(f"🛑 Export job cancelled: {job_id}")

        return True
