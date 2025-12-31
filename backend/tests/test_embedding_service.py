import pytest
import asyncio
from app.services.embedding_service import embedding_service


@pytest.mark.asyncio
async def test_embedding_initialization():
    """Test embedding service initialization"""
    await embedding_service.initialize()
    assert embedding_service._initialized is True
    assert embedding_service.model is not None


@pytest.mark.asyncio
async def test_get_single_embedding():
    """Test getting embedding for single text"""
    await embedding_service.initialize()

    text = "This is a test document about artificial intelligence."
    embedding = await embedding_service.get_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384  # Default embedding dimension
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_get_batch_embeddings():
    """Test getting embeddings for multiple texts"""
    await embedding_service.initialize()

    texts = [
        "First document about machine learning",
        "Second document about deep learning",
        "Third document about neural networks"
    ]

    embeddings = await embedding_service.get_embeddings_batch(texts)

    assert len(embeddings) == len(texts)
    assert all(len(emb) == 384 for emb in embeddings)


def test_cosine_similarity():
    """Test cosine similarity calculation"""
    emb1 = [1.0, 0.0, 0.0]
    emb2 = [1.0, 0.0, 0.0]
    emb3 = [0.0, 1.0, 0.0]

    # Identical vectors should have similarity of 1.0
    assert abs(embedding_service.cosine_similarity(emb1, emb2) - 1.0) < 0.001

    # Orthogonal vectors should have similarity of 0.0
    assert abs(embedding_service.cosine_similarity(emb1, emb3)) < 0.001


@pytest.mark.asyncio
async def test_embedding_caching():
    """Test that embeddings are cached"""
    await embedding_service.initialize()

    text = "This is a test for caching"

    # First call - should compute
    embedding1 = await embedding_service.get_embedding(text)

    # Second call - should use cache
    embedding2 = await embedding_service.get_embedding(text)

    # Results should be identical
    assert embedding1 == embedding2
