"""
Template Storage - Store and retrieve extraction templates

This module handles:
- Storing templates in PostgreSQL
- Storing template files in MinIO
- Template versioning
- Template retrieval and management
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class TemplateStorage:
    """
    Storage management for extraction templates

    Features:
    - PostgreSQL storage for template metadata
    - MinIO storage for template files
    - Template versioning
    - CRUD operations
    """

    def __init__(self, db: Session, minio_client=None):
        """
        Initialize template storage

        Args:
            db: SQLAlchemy database session
            minio_client: MinIO client instance
        """
        self.db = db
        self.minio_client = minio_client
        self.logger = logger
        self.bucket_name = "extraction-templates"

    async def create_template(
        self,
        template_data: Dict[str, Any],
        template_file_path: Optional[str] = None
    ) -> Optional[UUID]:
        """
        Create new extraction template

        Args:
            template_data: Template dictionary
            template_file_path: Optional path to template file in MinIO

        Returns:
            Template ID if successful, None otherwise
        """
        try:
            from ..models.extraction_template import ExtractionTemplate

            # Generate UUID
            template_id = uuid4()

            # Create template record
            template = ExtractionTemplate(
                id=template_id,
                name=template_data['name'],
                description=template_data.get('description'),
                template_type=template_data.get('template_type', 'json'),
                template_file_path=template_file_path,
                schema_definition=template_data.get('schema_definition', {}),
                fields=template_data.get('fields', []),
                validation_rules=template_data.get('validation_rules'),
                transformation_rules=template_data.get('transformation_rules'),
                version=1,
                is_active=True
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            self.logger.info(f"Created template: {template.name} (ID: {template_id})")
            return template_id

        except Exception as e:
            self.logger.error(f"Failed to create template: {str(e)}")
            self.db.rollback()
            return None

    async def get_template(self, template_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get template by ID

        Args:
            template_id: Template UUID

        Returns:
            Template dictionary or None
        """
        try:
            from ..models.extraction_template import ExtractionTemplate

            template = self.db.query(ExtractionTemplate).filter(
                ExtractionTemplate.id == template_id
            ).first()

            if not template:
                return None

            return self._template_to_dict(template)

        except Exception as e:
            self.logger.error(f"Failed to get template: {str(e)}")
            return None

    async def list_templates(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List templates

        Args:
            active_only: Only return active templates
            limit: Maximum number of templates to return
            offset: Offset for pagination

        Returns:
            List of template dictionaries
        """
        try:
            from ..models.extraction_template import ExtractionTemplate

            query = self.db.query(ExtractionTemplate)

            if active_only:
                query = query.filter(ExtractionTemplate.is_active == True)

            query = query.order_by(ExtractionTemplate.created_at.desc())
            query = query.limit(limit).offset(offset)

            templates = query.all()

            return [self._template_to_dict(t) for t in templates]

        except Exception as e:
            self.logger.error(f"Failed to list templates: {str(e)}")
            return []

    async def update_template(
        self,
        template_id: UUID,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update template

        Args:
            template_id: Template UUID
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            from ..models.extraction_template import ExtractionTemplate

            template = self.db.query(ExtractionTemplate).filter(
                ExtractionTemplate.id == template_id
            ).first()

            if not template:
                self.logger.error(f"Template not found: {template_id}")
                return False

            # Update allowed fields
            allowed_fields = ['name', 'description', 'fields', 'is_active']
            for field in allowed_fields:
                if field in updates:
                    setattr(template, field, updates[field])

            template.updated_at = datetime.utcnow()

            self.db.commit()
            self.logger.info(f"Updated template: {template_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update template: {str(e)}")
            self.db.rollback()
            return False

    async def delete_template(self, template_id: UUID) -> bool:
        """
        Delete template (soft delete - set is_active to False)

        Args:
            template_id: Template UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            from ..models.extraction_template import ExtractionTemplate

            template = self.db.query(ExtractionTemplate).filter(
                ExtractionTemplate.id == template_id
            ).first()

            if not template:
                return False

            template.is_active = False
            template.updated_at = datetime.utcnow()

            self.db.commit()
            self.logger.info(f"Deleted template: {template_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete template: {str(e)}")
            self.db.rollback()
            return False

    def _template_to_dict(self, template) -> Dict[str, Any]:
        """Convert SQLAlchemy template to dictionary"""
        return {
            'id': str(template.id),
            'name': template.name,
            'description': template.description,
            'template_type': template.template_type,
            'template_file_path': template.template_file_path,
            'schema_definition': template.schema_definition,
            'fields': template.fields,
            'validation_rules': template.validation_rules,
            'transformation_rules': template.transformation_rules,
            'version': template.version,
            'is_active': template.is_active,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        }

    async def upload_template_file(
        self,
        file_content: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Upload template file to MinIO

        Args:
            file_content: File content as bytes
            filename: Original filename

        Returns:
            MinIO file path if successful, None otherwise
        """
        if not self.minio_client:
            self.logger.warning("MinIO client not configured")
            return None

        try:
            # Ensure bucket exists
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)

            # Generate unique filename
            file_path = f"templates/{uuid4()}_{filename}"

            # Upload file
            from io import BytesIO
            self.minio_client.put_object(
                self.bucket_name,
                file_path,
                BytesIO(file_content),
                length=len(file_content)
            )

            self.logger.info(f"Uploaded template file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to upload template file: {str(e)}")
            return None
