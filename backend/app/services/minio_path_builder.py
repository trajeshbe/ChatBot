"""
MinIO Path Builder Service
Builds hierarchical paths for file storage following enterprise organization structure.

Path Structure: {role}/{department}/{team}/{username}/{project}/{folder}/{filename}
Example: admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf

Created: 2025-11-28
"""

import re
from typing import Optional, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathComponents:
    """Structured representation of MinIO path components"""
    role: str
    department: str
    team: str
    username: str
    project: str
    folder: str
    filename: str

    def to_path(self) -> str:
        """Convert components to full path string"""
        return f"{self.role}/{self.department}/{self.team}/{self.username}/{self.project}/{self.folder}/{self.filename}"


class MinIOPathBuilder:
    """
    Build and parse hierarchical MinIO paths.

    Hierarchy: Role → Department → Team → Username → Project → Folder → File

    Benefits:
    - Aligns with organizational structure
    - Efficient role-based access control
    - Easy department/team-wide operations
    - Scalable for multi-tenancy
    """

    # Valid folder types
    VALID_FOLDERS = ['documents', 'extractions', 'exports', 'temp']

    @staticmethod
    def sanitize(component: str) -> str:
        """
        Sanitize path component for MinIO/S3 compatibility.

        Rules:
        - Lowercase
        - Replace spaces with hyphens
        - Remove special characters (keep alphanumeric, hyphens, underscores, dots)
        - Strip leading/trailing whitespace and hyphens

        Args:
            component: Raw string component

        Returns:
            Sanitized string safe for use in MinIO paths

        Examples:
            "Technology" → "technology"
            "Tech Team 1" → "tech-team-1"
            "John Doe" → "john-doe"
            "ChatBot RAG!!!" → "chatbot-rag"
        """
        if not component:
            return "unknown"

        # Lowercase and strip
        sanitized = component.lower().strip()

        # Replace multiple spaces with single hyphen
        sanitized = re.sub(r'\s+', '-', sanitized)

        # Remove all special characters except alphanumeric, hyphens, underscores, dots
        sanitized = re.sub(r'[^a-z0-9\-_.]', '', sanitized)

        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')

        # Handle empty result
        if not sanitized:
            return "unknown"

        return sanitized

    @staticmethod
    def build_document_path(
        role: str,
        department: str,
        team: str,
        username: str,
        project_name: str,
        filename: str,
        folder: str = "documents"
    ) -> str:
        """
        Build hierarchical MinIO path for a document.

        Args:
            role: User role (admin, user, viewer)
            department: Department name (Technology, Data Operations, etc.)
            team: Team name (Tech Team 1, Data Team 5, etc.)
            username: User's username (john.doe)
            project_name: Project name (ChatBot RAG, ML Pipeline, etc.)
            filename: Original filename (requirements.pdf)
            folder: Folder type (documents, extractions, exports, temp)

        Returns:
            Full MinIO path string

        Example:
            >>> build_document_path(
            ...     role='admin',
            ...     department='Technology',
            ...     team='Tech Team 1',
            ...     username='john.doe',
            ...     project_name='ChatBot RAG',
            ...     filename='requirements.pdf',
            ...     folder='documents'
            ... )
            'admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf'
        """
        # Validate folder
        if folder not in MinIOPathBuilder.VALID_FOLDERS:
            logger.warning(f"Invalid folder '{folder}', defaulting to 'documents'")
            folder = 'documents'

        # Sanitize all components except filename
        sanitized_role = MinIOPathBuilder.sanitize(role)
        sanitized_dept = MinIOPathBuilder.sanitize(department)
        sanitized_team = MinIOPathBuilder.sanitize(team)
        sanitized_username = MinIOPathBuilder.sanitize(username)
        sanitized_project = MinIOPathBuilder.sanitize(project_name)

        # Filename is kept as-is (preserve original name)
        # MinIO/S3 handles special chars in filenames

        # Build path
        path = f"{sanitized_role}/{sanitized_dept}/{sanitized_team}/{sanitized_username}/{sanitized_project}/{folder}/{filename}"

        logger.debug(f"Built MinIO path: {path}")
        return path

    @staticmethod
    def build_export_path(
        role: str,
        department: str,
        team: str,
        username: str,
        project_name: str,
        filename: str
    ) -> str:
        """Build path for exported files (chat exports, reports, etc.)"""
        return MinIOPathBuilder.build_document_path(
            role, department, team, username, project_name, filename, folder='exports'
        )

    @staticmethod
    def build_extraction_path(
        role: str,
        department: str,
        team: str,
        username: str,
        project_name: str,
        filename: str
    ) -> str:
        """Build path for extracted data files"""
        return MinIOPathBuilder.build_document_path(
            role, department, team, username, project_name, filename, folder='extractions'
        )

    @staticmethod
    def build_temp_path(
        role: str,
        department: str,
        team: str,
        username: str,
        project_name: str,
        filename: str
    ) -> str:
        """Build path for temporary files"""
        return MinIOPathBuilder.build_document_path(
            role, department, team, username, project_name, filename, folder='temp'
        )

    @staticmethod
    def parse_path(minio_path: str) -> PathComponents:
        """
        Parse MinIO path back into components.

        Args:
            minio_path: Full MinIO path string

        Returns:
            PathComponents object

        Raises:
            ValueError: If path format is invalid

        Example:
            >>> parse_path('admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf')
            PathComponents(
                role='admin',
                department='technology',
                team='tech-team-1',
                username='john.doe',
                project='chatbot-rag',
                folder='documents',
                filename='requirements.pdf'
            )
        """
        parts = minio_path.split('/')

        if len(parts) < 7:
            raise ValueError(
                f"Invalid MinIO path format. Expected 7+ parts, got {len(parts)}. "
                f"Path: {minio_path}"
            )

        # Handle filenames with slashes (rare but possible)
        filename = '/'.join(parts[6:])

        return PathComponents(
            role=parts[0],
            department=parts[1],
            team=parts[2],
            username=parts[3],
            project=parts[4],
            folder=parts[5],
            filename=filename
        )

    @staticmethod
    def get_role_prefix(role: str) -> str:
        """Get role prefix for MinIO policy/query"""
        return f"{MinIOPathBuilder.sanitize(role)}/*"

    @staticmethod
    def get_department_prefix(role: str, department: str) -> str:
        """Get department prefix for MinIO policy/query"""
        return f"{MinIOPathBuilder.sanitize(role)}/{MinIOPathBuilder.sanitize(department)}/*"

    @staticmethod
    def get_team_prefix(role: str, department: str, team: str) -> str:
        """Get team prefix for MinIO policy/query"""
        return (
            f"{MinIOPathBuilder.sanitize(role)}/"
            f"{MinIOPathBuilder.sanitize(department)}/"
            f"{MinIOPathBuilder.sanitize(team)}/*"
        )

    @staticmethod
    def get_user_prefix(role: str, department: str, team: str, username: str) -> str:
        """Get user prefix for MinIO policy/query"""
        return (
            f"{MinIOPathBuilder.sanitize(role)}/"
            f"{MinIOPathBuilder.sanitize(department)}/"
            f"{MinIOPathBuilder.sanitize(team)}/"
            f"{MinIOPathBuilder.sanitize(username)}/*"
        )

    @staticmethod
    def get_project_prefix(
        role: str,
        department: str,
        team: str,
        username: str,
        project_name: str
    ) -> str:
        """Get project prefix for MinIO policy/query"""
        return (
            f"{MinIOPathBuilder.sanitize(role)}/"
            f"{MinIOPathBuilder.sanitize(department)}/"
            f"{MinIOPathBuilder.sanitize(team)}/"
            f"{MinIOPathBuilder.sanitize(username)}/"
            f"{MinIOPathBuilder.sanitize(project_name)}/*"
        )

    @staticmethod
    def validate_path(minio_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate MinIO path format.

        Returns:
            (is_valid, error_message)
        """
        try:
            components = MinIOPathBuilder.parse_path(minio_path)

            # Check folder is valid
            if components.folder not in MinIOPathBuilder.VALID_FOLDERS:
                return False, f"Invalid folder: {components.folder}"

            # Check no empty components
            for field, value in components.__dict__.items():
                if not value or value == 'unknown':
                    return False, f"Invalid/empty component: {field}"

            return True, None
        except ValueError as e:
            return False, str(e)


# Convenience instance
path_builder = MinIOPathBuilder()
