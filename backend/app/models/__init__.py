"""Database models for the RAG chatbot application"""
from app.models.database import (
    Base,
    Document,
    DocumentChunk,
    Conversation,
    Message,
    WebScrapeJob,
    QueryCache,
)

from app.models.finetuning_models import (
    FineTuningDataset,
    FineTuningJob,
    FineTunedModel,
    TrainingMetric,
)

__all__ = [
    "Base",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "WebScrapeJob",
    "QueryCache",
    # Fine-tuning models
    "FineTuningDataset",
    "FineTuningJob",
    "FineTunedModel",
    "TrainingMetric",
]
