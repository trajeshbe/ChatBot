"""
Test suite for Fine-Tuning Service

Tests the complete fine-tuning workflow matching actual implementation:
- Dataset creation and validation
- Job creation and submission
- Training metrics tracking
- Base model listing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.finetuning.finetuning_service import FineTuningService
from app.models.finetuning_models import (
    FineTuningJob,
    FineTuningDataset,
    FineTunedModel,
    TrainingMetric,
    get_default_hyperparameters
)


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def finetuning_service(mock_db):
    """Create FineTuningService instance with mocked dependencies"""
    return FineTuningService(db=mock_db)


@pytest.fixture
def sample_dataset_data():
    """Sample dataset creation data"""
    return {
        "name": "test_dataset",
        "filename": "training_data.jsonl",
        "file_path": "finetuning/datasets/test/training_data.jsonl",
        "file_size": 1024000,
        "format_type": "jsonl",
        "columns": {
            "prompt": "input_text",
            "completion": "output_text"
        },
        "uploaded_by": uuid4(),
        "project_id": uuid4(),
        "description": "Test dataset for model fine-tuning"
    }


@pytest.fixture
def sample_job_data():
    """Sample fine-tuning job creation data matching actual signature"""
    return {
        "name": "test_job",
        "base_model": "Qwen/Qwen2.5-7B-Instruct",
        "finetuning_method": "peft",
        "training_objective": "qa",
        "dataset_id": uuid4(),
        "hyperparameters": {
            "learning_rate": 2e-4,
            "batch_size": 4,
            "lora_r": 8,
            "lora_alpha": 16
        },
        "quantization": "4bit",
        "train_split": 0.8,
        "created_by": uuid4(),
        "project_id": uuid4(),
        "description": "Test fine-tuning job"
    }


class TestDatasetManagement:
    """Test dataset creation and management"""

    @pytest.mark.asyncio
    async def test_create_dataset(self, finetuning_service, mock_db, sample_dataset_data):
        """Test creating a new dataset"""
        # Act
        dataset = await finetuning_service.create_dataset(**sample_dataset_data)

        # Assert
        assert dataset is not None
        assert dataset.name == sample_dataset_data["name"]
        assert dataset.filename == sample_dataset_data["filename"]
        assert dataset.minio_path == sample_dataset_data["file_path"]
        assert dataset.file_size == sample_dataset_data["file_size"]
        assert dataset.format_type == sample_dataset_data["format_type"]
        assert dataset.preprocessing_status == "pending"

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_dataset(self, finetuning_service, mock_db):
        """Test dataset validation"""
        # Arrange
        dataset_id = uuid4()
        mock_dataset = Mock(spec=FineTuningDataset)
        mock_dataset.id = dataset_id
        mock_dataset.minio_path = "path/to/dataset.jsonl"
        mock_dataset.format_type = "jsonl"
        mock_dataset.preprocessing_status = "completed"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset

        # Mock the preprocessor's validate_dataset method
        with patch.object(finetuning_service.preprocessor, 'validate_dataset',
                         return_value={"valid": True, "num_samples": 100, "errors": []}):
            # Act
            result = await finetuning_service.validate_dataset(dataset_id)

            # Assert
            assert result is not None
            assert "num_samples" in result or "valid" in result

    @pytest.mark.asyncio
    async def test_list_datasets(self, finetuning_service, mock_db):
        """Test listing datasets with filtering"""
        # Arrange
        project_id = uuid4()
        mock_datasets = [
            Mock(spec=FineTuningDataset, id=uuid4(), name=f"dataset_{i}")
            for i in range(5)
        ]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=Mock(desc=Mock(return_value=Mock(all=Mock(return_value=mock_datasets)))))
        mock_db.query.return_value = mock_query

        # Act
        result = await finetuning_service.list_datasets(project_id=project_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(d, Mock) for d in result)


class TestJobManagement:
    """Test fine-tuning job creation and management"""

    @pytest.mark.asyncio
    async def test_create_job(self, finetuning_service, mock_db, sample_job_data):
        """Test creating a new fine-tuning job"""
        # Arrange
        mock_dataset = Mock(spec=FineTuningDataset)
        mock_dataset.id = sample_job_data["dataset_id"]
        mock_dataset.is_valid = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset

        # Act
        job = await finetuning_service.create_job(**sample_job_data)

        # Assert
        assert job is not None
        assert job.name == sample_job_data["name"]
        assert job.base_model == sample_job_data["base_model"]
        assert job.finetuning_method == sample_job_data["finetuning_method"]
        assert job.status == "pending"
        assert job.progress == 0.0

        # Verify database operations
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_job_invalid_dataset(self, finetuning_service, mock_db, sample_job_data):
        """Test creating job with non-existent dataset fails"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Dataset not found"):
            await finetuning_service.create_job(**sample_job_data)

    @pytest.mark.asyncio
    async def test_create_job_invalid_dataset_not_valid(self, finetuning_service, mock_db, sample_job_data):
        """Test creating job with invalid dataset fails"""
        # Arrange
        mock_dataset = Mock(spec=FineTuningDataset)
        mock_dataset.id = sample_job_data["dataset_id"]
        mock_dataset.is_valid = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_dataset

        # Act & Assert
        with pytest.raises(ValueError, match="Dataset is not valid"):
            await finetuning_service.create_job(**sample_job_data)

    @pytest.mark.asyncio
    async def test_submit_job(self, finetuning_service, mock_db):
        """Test submitting a fine-tuning job"""
        # Arrange
        job_id = uuid4()
        mock_job = Mock(spec=FineTuningJob)
        mock_job.id = job_id
        mock_job.status = "pending"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = await finetuning_service.submit_job(job_id)

        # Assert
        assert result["job_id"] == str(job_id)
        assert result["status"] == "queued"
        assert mock_job.status == "queued"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_submit_job_not_found(self, finetuning_service, mock_db):
        """Test submitting non-existent job fails"""
        # Arrange
        job_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Job not found"):
            await finetuning_service.submit_job(job_id)

    @pytest.mark.asyncio
    async def test_get_job(self, finetuning_service, mock_db):
        """Test retrieving job by ID"""
        # Arrange
        job_id = uuid4()
        mock_job = Mock(spec=FineTuningJob)
        mock_job.id = job_id
        mock_job.status = "running"
        mock_job.progress = 45.5

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        job = await finetuning_service.get_job(job_id)

        # Assert
        assert job is not None
        assert job.id == job_id
        assert job.status == "running"
        assert job.progress == 45.5

    @pytest.mark.asyncio
    async def test_list_jobs(self, finetuning_service, mock_db):
        """Test listing jobs with pagination"""
        # Arrange
        mock_jobs = [
            Mock(spec=FineTuningJob, id=uuid4(), name=f"job_{i}")
            for i in range(5)
        ]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=15)

        # Create nested mock chain for order_by().desc().offset().limit().all()
        mock_all = Mock(return_value=mock_jobs)
        mock_limit = Mock(return_value=Mock(all=mock_all))
        mock_offset = Mock(return_value=Mock(limit=mock_limit))
        mock_desc = Mock(return_value=Mock(offset=mock_offset))
        mock_query.order_by = Mock(return_value=Mock(desc=mock_desc))

        mock_db.query.return_value = mock_query

        # Act
        result = await finetuning_service.list_jobs(status="running", page=1, page_size=5)

        # Assert
        assert isinstance(result["jobs"], list)
        assert len(result["jobs"]) == 5
        assert result["total"] == 15
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert result["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_cancel_job(self, finetuning_service, mock_db):
        """Test cancelling a running job"""
        # Arrange
        job_id = uuid4()
        mock_job = Mock(spec=FineTuningJob)
        mock_job.id = job_id
        mock_job.status = "running"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        # Act
        result = await finetuning_service.cancel_job(job_id)

        # Assert
        assert result["job_id"] == str(job_id)
        assert result["status"] == "cancelled"
        assert mock_job.status == "cancelled"
        assert mock_job.error_message == "Cancelled by user"
        mock_db.commit.assert_called()


class TestTrainingMetrics:
    """Test training metrics tracking"""

    @pytest.mark.asyncio
    async def test_add_metric(self, finetuning_service, mock_db):
        """Test adding a training metric"""
        # Arrange
        job_id = uuid4()
        mock_job = Mock(spec=FineTuningJob)
        mock_job.id = job_id
        mock_job.total_steps = 1000

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        metric_data = {
            "job_id": job_id,
            "epoch": 1,
            "step": 100,
            "metrics": {
                "train_loss": 0.45,
                "eval_loss": 0.50,
                "learning_rate": 2e-4,
                "gpu_utilization": 85.5
            }
        }

        # Act
        metric = await finetuning_service.add_metric(**metric_data)

        # Assert
        assert metric is not None
        assert metric.epoch == 1
        assert metric.step == 100
        assert metric.train_loss == 0.45

        # Verify job was updated
        assert mock_job.current_epoch == 1
        assert mock_job.current_step == 100
        assert mock_job.progress == 0.1  # 100/1000

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_metrics(self, finetuning_service, mock_db):
        """Test retrieving metrics for a job"""
        # Arrange
        job_id = uuid4()
        mock_metrics = [
            Mock(spec=TrainingMetric, epoch=i, step=i*100, train_loss=0.5 - i*0.1)
            for i in range(3)
        ]

        mock_query = Mock()
        # Create nested mock chain for filter().order_by().desc().limit().all()
        mock_all = Mock(return_value=mock_metrics)
        mock_limit = Mock(return_value=Mock(all=mock_all))
        mock_desc = Mock(return_value=Mock(limit=mock_limit))
        mock_order_by = Mock(return_value=Mock(desc=mock_desc))
        mock_query.filter = Mock(return_value=Mock(order_by=mock_order_by))
        mock_db.query.return_value = mock_query

        # Act
        metrics = await finetuning_service.get_metrics(job_id, limit=10)

        # Assert
        assert isinstance(metrics, list)
        assert len(metrics) == 3
        assert metrics[0].epoch == 0
        assert metrics[0].train_loss == 0.5


class TestHyperparameters:
    """Test hyperparameter defaults"""

    def test_default_hyperparameters_peft(self):
        """Test getting default hyperparameters for PEFT"""
        # Act
        defaults = get_default_hyperparameters("peft")

        # Assert
        assert "learning_rate" in defaults
        assert "lora_r" in defaults
        assert "lora_alpha" in defaults
        assert defaults["lora_r"] == 16
        assert defaults["learning_rate"] == 2e-4

    def test_default_hyperparameters_sft(self):
        """Test getting default hyperparameters for SFT"""
        # Act
        defaults = get_default_hyperparameters("sft")

        # Assert
        assert "learning_rate" in defaults
        assert "num_epochs" in defaults
        assert "batch_size" in defaults
        assert defaults["learning_rate"] == 2e-5

    def test_default_hyperparameters_unknown_method(self):
        """Test getting defaults for unknown method returns empty dict"""
        # Act
        defaults = get_default_hyperparameters("unknown_method")

        # Assert
        assert defaults == {}


class TestUtilityMethods:
    """Test utility methods"""

    @pytest.mark.asyncio
    async def test_get_base_models(self, finetuning_service):
        """Test retrieving available base models"""
        # Act
        models = await finetuning_service.get_base_models()

        # Assert
        assert len(models) > 0
        assert all("id" in m for m in models)
        assert all("name" in m for m in models)
        assert all("quantization_options" in m for m in models)

        # Verify specific models
        model_ids = [m["id"] for m in models]
        assert "Qwen/Qwen2.5-7B-Instruct" in model_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
