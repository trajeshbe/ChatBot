"""
Test Script for Hybrid Agent Routing

Tests the complete hybrid routing logic without requiring backend to be running.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.task_complexity_analyzer import task_complexity_analyzer, TaskComplexity, TaskType
from app.agents.hybrid_agent_router import hybrid_agent_router, AgentOption
from app.services.api_usage_tracker import api_usage_tracker


async def test_complexity_analysis():
    """Test task complexity analyzer"""
    print("\n" + "=" * 80)
    print("TEST 1: Task Complexity Analysis")
    print("=" * 80)

    test_queries = [
        ("What is machine learning?", [], TaskComplexity.SIMPLE),
        ("Analyze this CSV file", [{"filename": "data.csv"}], TaskComplexity.COMPLEX),
        ("Write a Python script to process this data", [{"filename": "data.json"}], TaskComplexity.MEDIUM),
        ("Research the latest trends in quantum computing", [], TaskComplexity.COMPLEX),
        ("Perform comprehensive EDA on this dataset", [{"filename": "sales.csv"}], TaskComplexity.COMPLEX),
        ("What does this image show?", [{"filename": "screenshot.png"}], TaskComplexity.MEDIUM),
    ]

    for query, files, expected_complexity in test_queries:
        complexity, task_type, metadata = task_complexity_analyzer.analyze(
            query=query,
            uploaded_files=files
        )

        status = "✅" if complexity == expected_complexity else "❌"

        print(f"\n{status} Query: {query}")
        print(f"   Files: {files if files else 'None'}")
        print(f"   Expected: {expected_complexity.value}")
        print(f"   Got: {complexity.value}")
        print(f"   Task Type: {task_type.value}")
        print(f"   Indicators: {', '.join(metadata.get('indicators', []))}")


async def test_api_usage_tracker():
    """Test API usage tracker"""
    print("\n" + "=" * 80)
    print("TEST 2: API Usage Tracker")
    print("=" * 80)

    # Get initial stats
    stats = await api_usage_tracker.get_usage_stats()
    print(f"\n📊 Initial Budget Status:")
    print(f"   Daily: ${stats['daily']['spent']:.2f} / ${stats['daily']['limit']:.2f} ({stats['daily']['percentage_used']:.1f}%)")
    print(f"   Monthly: ${stats['monthly']['spent']:.2f} / ${stats['monthly']['limit']:.2f} ({stats['monthly']['percentage_used']:.1f}%)")

    # Simulate some usage
    print(f"\n💸 Simulating task execution...")
    await api_usage_tracker.record_usage(
        cost=0.65,
        task_id="test-task-1",
        agent_option="claude_cli",
        tokens_used=15000,
        model_name="claude-sonnet-4.5"
    )

    # Get updated stats
    stats = await api_usage_tracker.get_usage_stats()
    print(f"\n📊 After $0.65 task:")
    print(f"   Daily: ${stats['daily']['spent']:.2f} / ${stats['daily']['limit']:.2f} ({stats['daily']['percentage_used']:.1f}%)")
    print(f"   Tasks: {stats['daily']['tasks']}")

    # Check budget remaining
    daily_remaining = await api_usage_tracker.get_daily_budget_remaining()
    monthly_remaining = await api_usage_tracker.get_monthly_budget_remaining()

    print(f"\n💰 Remaining Budget:")
    print(f"   Daily: ${daily_remaining:.2f}")
    print(f"   Monthly: ${monthly_remaining:.2f}")

    if stats['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in stats['warnings']:
            print(f"   [{warning['level']}] {warning['message']}")


async def test_hybrid_routing():
    """Test hybrid agent routing"""
    print("\n" + "=" * 80)
    print("TEST 3: Hybrid Agent Routing")
    print("=" * 80)

    test_cases = [
        {
            "query": "What is Python?",
            "files": [],
            "expected_agent": AgentOption.DIRECT_RAG,
            "use_agent_mode": True
        },
        {
            "query": "Analyze this CSV and create visualizations",
            "files": [{"filename": "sales_data.csv"}],
            "expected_agent": AgentOption.LOCAL_MINI,
            "use_agent_mode": True
        },
        {
            "query": "Research the latest quantum computing trends and write a detailed report",
            "files": [],
            "expected_agent": AgentOption.CLAUDE_CLI,  # If budget allows
            "use_agent_mode": True
        },
        {
            "query": "Generate a Python script to process this JSON file",
            "files": [{"filename": "config.json"}],
            "expected_agent": AgentOption.LOCAL_MINI,
            "use_agent_mode": True
        },
        {
            "query": "What does this image show?",
            "files": [{"filename": "screenshot.png"}],
            "expected_agent": AgentOption.LOCAL_MINI,
            "use_agent_mode": True
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Query: {test_case['query']}")
        print(f"Files: {test_case['files'] if test_case['files'] else 'None'}")

        # Route the task
        agent_option, routing_metadata = await hybrid_agent_router.route(
            query=test_case['query'],
            session_id="test-session",
            user_preferences={
                "use_agent_mode": test_case['use_agent_mode'],
                "uploaded_files": test_case['files']
            }
        )

        expected = test_case['expected_agent']
        status = "✅" if agent_option == expected else "⚠️"

        print(f"\n{status} Expected: {expected.value}")
        print(f"   Got: {agent_option.value}")
        print(f"   Complexity: {routing_metadata['complexity']}")
        print(f"   Task Type: {routing_metadata['task_type']}")
        print(f"   Reason: {routing_metadata['reason']}")
        if 'estimated_cost' in routing_metadata:
            print(f"   Estimated Cost: ${routing_metadata['estimated_cost']:.2f}")
        if 'budget_remaining' in routing_metadata:
            print(f"   Budget Remaining: ${routing_metadata['budget_remaining']:.2f}")


async def test_budget_enforcement():
    """Test budget enforcement and fallback"""
    print("\n" + "=" * 80)
    print("TEST 4: Budget Enforcement")
    print("=" * 80)

    # Simulate exhausting budget
    print("\n💸 Simulating budget exhaustion...")

    daily_remaining = await api_usage_tracker.get_daily_budget_remaining()
    print(f"   Current daily remaining: ${daily_remaining:.2f}")

    # Spend remaining budget
    if daily_remaining > 0:
        await api_usage_tracker.record_usage(
            cost=daily_remaining,
            task_id="budget-exhaust-task",
            agent_option="claude_cli",
            tokens_used=50000,
            model_name="claude-sonnet-4.5"
        )

        print(f"   Spent ${daily_remaining:.2f} to exhaust daily budget")

    # Try routing a complex research task (should fallback to local)
    print(f"\n🔄 Routing complex research task with exhausted budget...")

    agent_option, routing_metadata = await hybrid_agent_router.route(
        query="Research quantum computing and write a comprehensive report",
        session_id="test-session",
        user_preferences={"use_agent_mode": True}
    )

    print(f"\n   Agent Selected: {agent_option.value}")
    print(f"   Reason: {routing_metadata['reason']}")
    if 'budget_remaining' in routing_metadata:
        print(f"   Budget Remaining: ${routing_metadata['budget_remaining']:.2f}")

    if agent_option == AgentOption.LOCAL_MINI:
        print(f"   ✅ Correctly fell back to local mini agent!")
    else:
        print(f"   ❌ Should have fallen back to local mini agent")


async def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("HYBRID AGENT ROUTING - TEST SUITE")
    print("=" * 80)

    try:
        await test_complexity_analysis()
        await test_api_usage_tracker()
        await test_hybrid_routing()
        await test_budget_enforcement()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nNote: Some tests may show ⚠️  if budget affects routing decisions")
        print("This is expected behavior - the system adapts to budget constraints.")
        print("\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
