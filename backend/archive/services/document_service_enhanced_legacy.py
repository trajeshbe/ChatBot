"""
Enhanced Document Service with Hierarchical MinIO Paths
Extends base document_service.py with project tracking and normalized organization.

Path Structure: role/department/team/username/project/folder/filename
"""

from typing import Optional
import uuid
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import DocumentService as BaseDocumentService
from app.services.minio_path_builder import MinIOPathBuilder
from app.models.database import Document
from app.core.config import settings
import io

logger = logging.getLogger(__name__)


class EnhancedDocumentService(BaseDocumentService):
    """
    Enhanced document service with hierarchical file organization.

    Adds support for:
    - Project-based file organization
    - Hierarchical MinIO paths (role/dept/team/username/project/folder/file)
    - Department and team tracking
    - Normalized FK references
    """

    async def upload_file_with_project(
        self,
        file_data: bytes,
        filename: str,
        file_type: str,
        user_dict: dict,  # {id, username, role, department_id, team_id}
        project_dict: dict,  # {id, name, department_id, team_id}
        source_type: str = "upload",
        source_url: Optional[str] = None,
        session_id: Optional[str] = None,
        folder: str = "documents",
        db: AsyncSession = None
    ) -> Document:
        """
        Upload file with full hierarchical organization.

        Args:
            file_data: File binary data
            filename: Original filename
            file_type: MIME type
            user_dict: User info {id, username, role, department_id, team_id}
            project_dict: Project info {id, name, department_id, team_id}
            source_type: 'upload' or 'scrape'
            source_url: URL if scraped
            session_id: Chat session ID
            folder: Folder type (documents/extractions/exports/temp)
            db: Database session

        Returns:
            Document object with hierarchical path

        Example:
            >>> await service.upload_file_with_project(
            ...     file_data=pdf_bytes,
            ...     filename='requirements.pdf',
            ...     file_type='application/pdf',
            ...     user_dict={'id': '...', 'username': 'john.doe', 'role': 'admin', ...},
            ...     project_dict={'id': '...', 'name': 'ChatBot RAG', ...},
            ...     db=db
            ... )
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get department and team names from database
            dept_name, team_name = await self._get_dept_team_names(
                department_id=project_dict.get('department_id'),
                team_id=project_dict.get('team_id'),
                db=db
            )

            # Build hierarchical MinIO path
            minio_path = MinIOPathBuilder.build_document_path(
                role=user_dict['role'],
                department=dept_name,
                team=team_name,
                username=user_dict['username'],
                project_name=project_dict['name'],
                filename=filename,
                folder=folder
            )

            logger.info(f"Generated MinIO path: {minio_path}")

            # Upload to MinIO using hierarchical path
            self.minio_client.put_object(
                settings.MINIO_BUCKET_NAME,
                minio_path,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=file_type
            )

            logger.info(f"Uploaded file to MinIO: {minio_path}")

            # Create database record with full traceability
            document = Document(
                id=uuid.uuid4(),
                filename=filename,
                file_path=minio_path,  # Full hierarchical path
                minio_path=minio_path,  # Stored for reference
                file_type=file_type,
                file_size=len(file_data),
                source_type=source_type,
                source_url=source_url,
                processed=False,

                # Project tracking (normalized FK references)
                project_id=project_dict.get('id'),
                uploaded_by=user_dict.get('id'),
                department_id=project_dict.get('department_id'),
                team_id=project_dict.get('team_id'),
                user_role=user_dict.get('role')  # Role at upload time (for history)
            )

            if db:
                db.add(document)
                await db.flush()
                await db.refresh(document)

                # Associate with session if provided
                if session_id:
                    try:
                        from app.models.database_enhanced import SessionDocument
                        session_doc = SessionDocument(
                            session_id=uuid.UUID(session_id) if isinstance(session_id, str) else session_id,
                            document_id=document.id
                        )
                        db.add(session_doc)
                        await db.flush()
                        logger.info(f"Associated document {document.id} with session {session_id}")
                    except Exception as e:
                        logger.warning(f"Could not associate document with session: {e}")

                logger.info(
                    f"Created document record: {document.id} "
                    f"(user: {user_dict['username']}, project: {project_dict['name']})"
                )

            return document

        except Exception as e:
            logger.error(f"Error uploading file with project: {e}", exc_info=True)
            raise

    async def _get_dept_team_names(
        self,
        department_id: Optional[str],
        team_id: Optional[str],
        db: AsyncSession
    ) -> tuple[str, str]:
        """
        Get department and team names from IDs.

        Returns:
            (department_name, team_name)
        """
        try:
            # Import models
            from app.models.database_enhanced import Department, Team

            dept_name = "unknown"
            team_name = "unknown"

            # Get department name
            if department_id:
                result = await db.execute(
                    select(Department).where(Department.id == department_id)
                )
                dept = result.scalar_one_or_none()
                if dept:
                    dept_name = dept.name

            # Get team name
            if team_id:
                result = await db.execute(
                    select(Team).where(Team.id == team_id)
                )
                team = result.scalar_one_or_none()
                if team:
                    team_name = team.name

            return dept_name, team_name

        except Exception as e:
            logger.warning(f"Could not get dept/team names: {e}, using defaults")
            return "unknown", "unknown"

    async def get_file_download_url(
        self,
        document_id: str,
        db: AsyncSession,
        expires_hours: int = 1
    ) -> str:
        """
        Generate presigned download URL for a document.

        Args:
            document_id: Document UUID
            db: Database session
            expires_hours: URL expiration time in hours

        Returns:
            Presigned download URL
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Generate presigned URL
            from datetime import timedelta
            url = self.minio_client.presigned_get_object(
                settings.MINIO_BUCKET_NAME,
                document.minio_path,
                expires=timedelta(hours=expires_hours)
            )

            logger.info(f"Generated download URL for document {document_id}")
            return url

        except Exception as e:
            logger.error(f"Error generating download URL: {e}")
            raise

    async def delete_file(
        self,
        document_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete file from both MinIO and database.

        Args:
            document_id: Document UUID
            db: Database session

        Returns:
            True if deleted successfully
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Delete from MinIO
            try:
                self.minio_client.remove_object(
                    settings.MINIO_BUCKET_NAME,
                    document.minio_path
                )
                logger.info(f"Deleted from MinIO: {document.minio_path}")
            except Exception as e:
                logger.warning(f"Could not delete from MinIO: {e}")

            # Delete from database (CASCADE will delete chunks)
            await db.delete(document)
            await db.flush()

            logger.info(f"Deleted document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise


# Singleton instance
enhanced_document_service = EnhancedDocumentService()
