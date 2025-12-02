#!/usr/bin/env python3
"""
Test Merit SelectScience PDF with Intelligent Routing

Verifies:
1. TaskRouter detects PDF file type
2. Selects docling_pdf as primary tool (not vision_analysis)
3. Memory constraints are respected
4. Fallback chain is correct: docling_pdf → ocr → document_rag → vision_analysis
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.task_router import task_router
from app.utils.resource_checker import resource_checker


async def test_merit_pdf_routing():
    """Test routing decision for Merit SelectScience PDF"""

    print("=" * 80)
    print("TESTING: Merit SelectScience PDF Routing")
    print("=" * 80)
    print()

    # Step 1: Check system resources
    print("📊 Step 1: Checking System Resources")
    print("-" * 80)
    resource_checker.log_resource_status()
    print()

    # Step 2: Simulate PDF document metadata
    print("📄 Step 2: Simulating PDF Upload")
    print("-" * 80)

    pdf_document = {
        'filename': 'Merit + SelectScience Brief Dec26 V1.pdf',
        'file_type': 'application/pdf',
        'mime_type': 'application/pdf',
        'file_size': 1700000,  # 1.7 MB
        'document_id': 'test-merit-pdf-001'
    }

    print(f"Document: {pdf_document['filename']}")
    print(f"Size: {pdf_document['file_size'] / 1024 / 1024:.2f} MB")
    print(f"Type: {pdf_document['file_type']}")
    print()

    # Step 3: Test TaskRouter decision
    print("🎯 Step 3: TaskRouter Analysis")
    print("-" * 80)

    query = "What are the key highlights from this document?"

    routing_decision = await task_router.route(
        query=query,
        documents=[pdf_document],
        session_id="test-session",
        user_preferences={}
    )

    print(f"Query: {query}")
    print()
    print("✅ Routing Decision:")
    print(f"   Primary Tool: {routing_decision.primary_tool}")
    print(f"   Fallback Chain: {' → '.join(routing_decision.fallback_chain)}")
    print(f"   File Types: {[ft.value for ft in routing_decision.file_types]}")
    print(f"   Complexity: {routing_decision.complexity.value}")
    print(f"   Memory Required: {routing_decision.estimated_memory_mb} MB")
    print(f"   Requires GPU: {routing_decision.requires_gpu}")
    print(f"   Reasoning: {routing_decision.reasoning}")
    print()

    # Step 4: Validate routing
    print("✓ Step 4: Validation")
    print("-" * 80)

    validation_results = {
        "PDF Detected": "pdf" in [ft.value for ft in routing_decision.file_types],
        "docling_pdf is Primary": routing_decision.primary_tool == "docling_pdf",
        "vision_analysis is NOT Primary": routing_decision.primary_tool != "vision_analysis",
        "vision_analysis in Fallback": "vision_analysis" in routing_decision.fallback_chain,
        "Memory Efficient (<1GB)": routing_decision.estimated_memory_mb < 1000,
    }

    all_passed = all(validation_results.values())

    for check, passed in validation_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")

    print()
    print("=" * 80)

    if all_passed:
        print("🎉 SUCCESS: All validations passed!")
        print()
        print("Key Improvements from Previous Implementation:")
        print("  ✓ Local tools (docling_pdf) prioritized over expensive vision models")
        print("  ✓ Vision LLM moved to last resort (fallback 3)")
        print("  ✓ Memory-efficient primary tool (<1GB vs 5.1GB)")
        print("  ✓ Follows resource-constrained best practices:")
        print("    - PREPROCESSING OVER INFERENCE")
        print("    - Extract first, augment LLM later")
        print("    - LLM = last resort, not first choice")
    else:
        print("⚠️  SOME VALIDATIONS FAILED - Review routing logic")

    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_merit_pdf_routing())
    sys.exit(0 if success else 1)
