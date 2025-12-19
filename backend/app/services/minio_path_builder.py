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
        department: str,
        team: str,
        project_name: str,
        username: str,
        filename: str,
        folder: str = "documents"
    ) -> str:
        """
        Build hierarchical MinIO path for a document.

        Args:
            department: Department name (Technology, Data Operations, etc.)
            team: Team name (Tech Team 1, Data Team 5, etc.)
            project_name: Project name (ChatBot RAG, ML Pipeline, etc.)
            username: User's username (john.doe)
            filename: Original filename (requirements.pdf)
            folder: Folder type (documents, extractions, exports, temp)

        Returns:
            Full MinIO path string

        Example:
            >>> build_document_path(
            ...     department='Technology',
            ...     team='Tech Team 1',
            ...     project_name='ChatBot RAG',
            ...     username='john.doe',
            ...     filename='requirements.pdf',
            ...     folder='documents'
            ... )
            'technology/tech-team-1/chatbot-rag/john.doe/documents/requirements.pdf'
        """
        # Validate folder
        if folder not in MinIOPathBuilder.VALID_FOLDERS:
            logger.warning(f"Invalid folder '{folder}', defaulting to 'documents'")
            folder = 'documents'

        # Sanitize all components except filename
        sanitized_dept = MinIOPathBuilder.sanitize(department)
        sanitized_team = MinIOPathBuilder.sanitize(team)
        sanitized_username = MinIOPathBuilder.sanitize(username)
        sanitized_project = MinIOPathBuilder.sanitize(project_name)

        # Filename is kept as-is (preserve original name)
        # MinIO/S3 handles special chars in filenames

        # Build path: {dept}/{team}/{project}/{username}/{folder}/{filename}
        path = f"{sanitized_dept}/{sanitized_team}/{sanitized_project}/{sanitized_username}/{folder}/{filename}"

        logger.debug(f"Built MinIO path: {path}")
        return path

    @staticmethod
    def build_export_path(
        department: str,
        team: str,
        project_name: str,
        username: str,
        filename: str
    ) -> str:
        """Build path for exported files (chat exports, reports, etc.)"""
        return MinIOPathBuilder.build_document_path(
            department, team, project_name, username, filename, folder='exports'
        )

    @staticmethod
    def build_extraction_path(
        department: str,
        team: str,
        project_name: str,
        username: str,
        filename: str
    ) -> str:
        """Build path for extracted data files"""
        return MinIOPathBuilder.build_document_path(
            department, team, project_name, username, filename, folder='extractions'
        )

    @staticmethod
    def build_temp_path(
        department: str,
        team: str,
        project_name: str,
        username: str,
        filename: str
    ) -> str:
        """Build path for temporary files"""
        return MinIOPathBuilder.build_document_path(
            department, team, project_name, username, filename, folder='temp'
        )

    @staticmethod
    def build_agent_task_path(
        department: str,
        team: str,
        project_name: str,
        username: str,
        task_name: str,
        task_id: str,
        subfolder: str,
        filename: str
    ) -> str:
        """
        Build hierarchical MinIO path for agent task artifacts.

        Args:
            department: Department name (Technology, Data Operations, etc.)
            team: Team name (Backend Development, Data Science Team, etc.)
            project_name: Project name (ChatBot RAG, Construction Intelligence, etc.)
            username: User's username
            task_name: Human-readable task name (e.g., 'sales_analysis_chart')
            task_id: Unique task execution ID (e.g., 'task-a81656d4e7e9')
            subfolder: Folder within task ('input', 'artifacts', 'logs')
            filename: File name

        Returns:
            Full MinIO path string

        Example:
            >>> build_agent_task_path(
            ...     department='Technology',
            ...     team='Backend Development',
            ...     project_name='Construction Intelligence',
            ...     username='admin',
            ...     task_name='sales_analysis_chart',
            ...     task_id='task-a81656d4e7e9',
            ...     subfolder='artifacts',
            ...     filename='revenue_chart.html'
            ... )
            'technology/backend-development/construction-intelligence/admin/agent-tasks/sales_analysis_chart/task-a81656d4e7e9/artifacts/revenue_chart.html'
        """
        # Sanitize components
        sanitized_dept = MinIOPathBuilder.sanitize(department)
        sanitized_team = MinIOPathBuilder.sanitize(team)
        sanitized_project = MinIOPathBuilder.sanitize(project_name)
        sanitized_username = MinIOPathBuilder.sanitize(username)
        sanitized_task_name = MinIOPathBuilder.sanitize(task_name)

        # Validate subfolder
        valid_subfolders = ['input', 'artifacts', 'logs']
        if subfolder not in valid_subfolders:
            logger.warning(f"Invalid subfolder '{subfolder}', defaulting to 'artifacts'")
            subfolder = 'artifacts'

        # Build path: {dept}/{team}/{project}/{username}/agent-tasks/{task}/{task-id}/{subfolder}/{file}
        path = (
            f"{sanitized_dept}/{sanitized_team}/{sanitized_project}/{sanitized_username}/agent-tasks/"
            f"{sanitized_task_name}/{task_id}/{subfolder}/{filename}"
        )

        logger.debug(f"Built agent task MinIO path: {path}")
        return path

    @staticmethod
    def get_agent_task_prefix(
        project_id: str,
        username: str,
        task_name: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> str:
        """
        Get prefix for listing agent task files.

        Examples:
            # All tasks for user in project
            get_agent_task_prefix('global-project', 'admin')
            → 'projects/global-project/admin/agent-tasks/*'

            # All executions of specific task
            get_agent_task_prefix('global-project', 'admin', 'sales_analysis_chart')
            → 'projects/global-project/admin/agent-tasks/sales_analysis_chart/*'

            # Specific task execution
            get_agent_task_prefix('global-project', 'admin', 'sales_analysis_chart', 'task-123')
            → 'projects/global-project/admin/agent-tasks/sales_analysis_chart/task-123/*'
        """
        sanitized_project = MinIOPathBuilder.sanitize(project_id)
        sanitized_username = MinIOPathBuilder.sanitize(username)

        prefix = f"projects/{sanitized_project}/{sanitized_username}/agent-tasks/"

        if task_name:
            sanitized_task_name = MinIOPathBuilder.sanitize(task_name)
            prefix += f"{sanitized_task_name}/"

            if task_id:
                prefix += f"{task_id}/"

        prefix += "*"
        return prefix

    @staticmethod
    def build_finetuning_dataset_path(
        department_name: str,
        team_name: str,
        project_name: str,
        username: str,
        dataset_name: str,
        dataset_id: str,
        filename: str
    ) -> str:
        """
        Build hierarchical MinIO path for fine-tuning dataset.

        Args:
            department_name: Department name (e.g., 'Technology')
            team_name: Team name (e.g., 'Backend Development')
            project_name: Project name (e.g., 'ChatBot RAG')
            username: User's username (e.g., 'admin')
            dataset_name: Human-readable dataset name (e.g., 'cloudsync-support-qa')
            dataset_id: Unique dataset ID (UUID)
            filename: Original file name

        Returns:
            Full MinIO path string

        Example:
            >>> build_finetuning_dataset_path(
            ...     department_name='Technology',
            ...     team_name='Backend Development',
            ...     project_name='ChatBot RAG',
            ...     username='admin',
            ...     dataset_name='cloudsync-support-qa',
            ...     dataset_id='3b8234e1-b542-44ad-9c09-f45059888511',
            ...     filename='cloudsync_support_qa.jsonl'
            ... )
            'Technology/Backend-Development/ChatBot-RAG/admin/finetuning/datasets/cloudsync-support-qa/3b8234e1-b542-44ad-9c09-f45059888511/cloudsync_support_qa.jsonl'
        """
        sanitized_department = MinIOPathBuilder.sanitize(department_name)
        sanitized_team = MinIOPathBuilder.sanitize(team_name)
        sanitized_project = MinIOPathBuilder.sanitize(project_name)
        sanitized_username = MinIOPathBuilder.sanitize(username)
        sanitized_dataset_name = MinIOPathBuilder.sanitize(dataset_name)

        path = (
            f"{sanitized_department}/{sanitized_team}/{sanitized_project}/"
            f"{sanitized_username}/finetuning/datasets/{sanitized_dataset_name}/{dataset_id}/{filename}"
        )

        logger.debug(f"Built fine-tuning dataset MinIO path: {path}")
        return path

    @staticmethod
    def build_finetuning_checkpoint_path(
        department_name: str,
        team_name: str,
        project_name: str,
        job_name: str,
        job_id: str,
        checkpoint_type: str,
        filename: str
    ) -> str:
        """
        Build hierarchical MinIO path for fine-tuning checkpoints.

        Args:
            department_name: Department name (e.g., 'Technology')
            team_name: Team name (e.g., 'Backend Development')
            project_name: Project name (e.g., 'ChatBot RAG')
            job_name: Human-readable job name
            job_id: Unique job ID (UUID)
            checkpoint_type: Type of checkpoint ('adapters', 'full_model', 'optimizer_state')
            filename: Checkpoint file name

        Returns:
            Full MinIO path string

        Example:
            >>> build_finetuning_checkpoint_path(
            ...     department_name='Technology',
            ...     team_name='Backend Development',
            ...     project_name='ChatBot RAG',
            ...     job_name='qwen-2.5-cloudsync',
            ...     job_id='c4ad0963-b194-4f85-b816-3fd0fdaaff9d',
            ...     checkpoint_type='adapters',
            ...     filename='adapter_model.bin'
            ... )
            'Technology/Backend-Development/ChatBot-RAG/finetuning/checkpoints/qwen-2.5-cloudsync/c4ad0963-b194-4f85-b816-3fd0fdaaff9d/adapters/adapter_model.bin'
        """
        sanitized_department = MinIOPathBuilder.sanitize(department_name)
        sanitized_team = MinIOPathBuilder.sanitize(team_name)
        sanitized_project = MinIOPathBuilder.sanitize(project_name)
        sanitized_job_name = MinIOPathBuilder.sanitize(job_name)

        # Validate checkpoint type
        valid_checkpoint_types = ['adapters', 'full_model', 'optimizer_state', 'config']
        if checkpoint_type not in valid_checkpoint_types:
            logger.warning(f"Invalid checkpoint type '{checkpoint_type}', defaulting to 'adapters'")
            checkpoint_type = 'adapters'

        path = (
            f"{sanitized_department}/{sanitized_team}/{sanitized_project}/"
            f"finetuning/checkpoints/{sanitized_job_name}/{job_id}/{checkpoint_type}/{filename}"
        )

        logger.debug(f"Built fine-tuning checkpoint MinIO path: {path}")
        return path

    @staticmethod
    def get_finetuning_prefix(
        project_id: str,
        username: str,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None
    ) -> str:
        """
        Get prefix for listing fine-tuning files.

        Args:
            project_id: Project UUID or 'global-project'
            username: User's username
            resource_type: 'datasets', 'checkpoints', or None for all
            resource_name: Specific dataset/job name or None for all

        Examples:
            # All fine-tuning resources for user
            get_finetuning_prefix('global-project', 'admin')
            → 'projects/global-project/admin/finetuning/*'

            # All datasets
            get_finetuning_prefix('global-project', 'admin', 'datasets')
            → 'projects/global-project/admin/finetuning/datasets/*'

            # Specific dataset
            get_finetuning_prefix('global-project', 'admin', 'datasets', 'cloudsync-support-qa')
            → 'projects/global-project/admin/finetuning/datasets/cloudsync-support-qa/*'
        """
        sanitized_project = MinIOPathBuilder.sanitize(project_id)
        sanitized_username = MinIOPathBuilder.sanitize(username)

        prefix = f"projects/{sanitized_project}/{sanitized_username}/finetuning/"

        if resource_type:
            prefix += f"{resource_type}/"

            if resource_name:
                sanitized_resource_name = MinIOPathBuilder.sanitize(resource_name)
                prefix += f"{sanitized_resource_name}/"

        prefix += "*"
        return prefix

    @staticmethod
    def build_finetuning_checkpoint_with_dataset(
        department_name: str,
        team_name: str,
        project_name: str,
        username: str,
        dataset_name: str,
        job_name: str,
        job_id: str,
        checkpoint_stage: str = "final",
        model_type: str = "merged_model",
        filename: str = ""
    ) -> str:
        """
        Build hierarchical MinIO path for fine-tuning checkpoints under dataset.

        This creates a dataset-linked organizational hierarchy:
        {dept}/{team}/{project}/{user}/finetuning/datasets/{dataset}/checkpoints/{job}/{job_id}/{stage}/{type}/{file}

        NOTE: Bucket name (e.g., 'documents') is NOT included in the returned path.
        It should be added separately when constructing the MinIO URI.

        Args:
            department_name: Department (e.g., 'Technology')
            team_name: Team (e.g., 'Backend Development')
            project_name: Project (e.g., 'global', 'ChatBot RAG')
            username: User's username (e.g., 'admin')
            dataset_name: Dataset name (e.g., 'story8', 'cloudsync-qa')
            job_name: Job name (e.g., 'qwen-story-job')
            job_id: Unique job ID (UUID)
            checkpoint_stage: Stage ('final', 'epoch-1', 'epoch-2', 'best')
            model_type: Type ('adapter_model', 'merged_model')
            filename: Specific file name (empty for directory path)

        Returns:
            MinIO object path (without bucket name)

        Examples:
            >>> build_finetuning_checkpoint_with_dataset(
            ...     department_name='Technology',
            ...     team_name='Backend Development',
            ...     project_name='global',
            ...     username='admin',
            ...     dataset_name='story8',
            ...     job_name='qwen-story-job',
            ...     job_id='c4ad0963-b194-4f85-b816-3fd0fdaaff9d',
            ...     checkpoint_stage='final',
            ...     model_type='merged_model',
            ...     filename='model.safetensors'
            ... )
            'technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/qwen-story-job/c4ad0963-b194-4f85-b816-3fd0fdaaff9d/final/merged_model/model.safetensors'
        """
        # Sanitize components
        sanitized_dept = MinIOPathBuilder.sanitize(department_name)
        sanitized_team = MinIOPathBuilder.sanitize(team_name)
        sanitized_project = MinIOPathBuilder.sanitize(project_name)
        sanitized_username = MinIOPathBuilder.sanitize(username)
        sanitized_dataset = MinIOPathBuilder.sanitize(dataset_name)
        sanitized_job = MinIOPathBuilder.sanitize(job_name)

        # Build path: {dept}/{team}/{project}/{user}/finetuning/datasets/{dataset}/checkpoints/{job}/{job_id}/{stage}/{type}
        # Full MinIO URI will be: minio://documents/{dept}/{team}/...
        # Bucket name "documents" is added separately in URI construction
        path = (
            f"{sanitized_dept}/{sanitized_team}/{sanitized_project}/"
            f"{sanitized_username}/finetuning/datasets/{sanitized_dataset}/"
            f"checkpoints/{sanitized_job}/{job_id}/{checkpoint_stage}/{model_type}"
        )

        if filename:
            path += f"/{filename}"

        logger.debug(f"Built dataset-linked checkpoint path: {path}")
        return path

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
