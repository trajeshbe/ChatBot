"""
Quick test script for the Robust RAG Pipeline

Run this to verify the pipeline is working correctly.
"""

import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_imports():
    """Test that all modules can be imported"""
    logger.info("Testing imports...")

    try:
        from app.rag_pipeline import (
            rag_answer,
            get_rag_settings,
            embed_query,
            retrieve_hybrid,
            rerank_with_ollama,
            get_cached_answer,
            store_answer
        )
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config():
    """Test configuration loading"""
    logger.info("Testing configuration...")

    try:
        from app.rag_pipeline import get_rag_settings, get_model_context_window, is_large_context_model

        settings = get_rag_settings()
        logger.info(f"✓ Settings loaded: {settings.GENERATION_MODEL_NAME}")

        # Test context window helpers
        gpt4_context = get_model_context_window("gpt-4-turbo-preview")
        logger.info(f"✓ GPT-4 context window: {gpt4_context}")

        is_large = is_large_context_model("claude-3-opus-20240229")
        logger.info(f"✓ Claude-3 is large model: {is_large}")

        return True
    except Exception as e:
        logger.error(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding():
    """Test embedding generation"""
    logger.info("Testing embedding generation...")

    try:
        from app.rag_pipeline import embed_query, get_embedding_manager

        manager = await get_embedding_manager()
        embedding = await embed_query("test query")

        logger.info(f"✓ Embedding generated: dimension={len(embedding)}")
        return True
    except Exception as e:
        logger.error(f"✗ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_stages():
    """Test individual pipeline stages"""
    logger.info("Testing pipeline stages...")

    try:
        from app.rag_pipeline.pipeline import (
            normalize_query,
            RagState
        )
        from app.rag_pipeline import get_rag_settings

        settings = get_rag_settings()

        # Test normalization
        state = RagState(user_query="  What is this project?  ")
        state = normalize_query(state, settings)
        logger.info(f"✓ Query normalized: '{state.normalized_query}'")

        return True
    except Exception as e:
        logger.error(f"✗ Pipeline stages test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_routes():
    """Test that API routes are properly defined"""
    logger.info("Testing API routes...")

    try:
        from app.api.routes import rag_pipeline_routes

        logger.info(f"✓ Router loaded: {rag_pipeline_routes.router.prefix}")
        logger.info(f"✓ Routes count: {len(rag_pipeline_routes.router.routes)}")

        return True
    except Exception as e:
        logger.error(f"✗ API routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Robust RAG Pipeline Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Embedding", test_embedding),
        ("Pipeline Stages", test_pipeline_stages),
        ("API Routes", test_api_routes),
    ]

    results = []
    for name, test_func in tests:
        logger.info(f"\n--- {name} ---")
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.error(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
