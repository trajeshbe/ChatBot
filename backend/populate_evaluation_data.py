#!/usr/bin/env python3
"""
Populate Evaluation Data Script

Quickly populates the database with sample evaluation results and human feedback
to test the Evaluation Dashboard functionality.

Usage:
    python populate_evaluation_data.py
"""

import asyncio
import sys
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.database_enhanced import (
    ChatSession,
    EvaluationConfig,
    EvaluationResult,
    HumanFeedback,
    User
)


# Sample queries and responses for realistic test data
SAMPLE_DATA = [
    {
        "query": "What is the capital of France?",
        "response": "The capital of France is Paris. It is located in the north-central part of the country.",
        "score_range": (0.85, 0.95)
    },
    {
        "query": "How does photosynthesis work?",
        "response": "Photosynthesis is the process by which plants convert light energy into chemical energy stored in glucose.",
        "score_range": (0.80, 0.90)
    },
    {
        "query": "Who wrote Romeo and Juliet?",
        "response": "William Shakespeare wrote Romeo and Juliet, one of his most famous tragedies.",
        "score_range": (0.90, 0.98)
    },
    {
        "query": "What is machine learning?",
        "response": "Machine learning is a subset of AI that enables systems to learn from data without explicit programming.",
        "score_range": (0.75, 0.88)
    },
    {
        "query": "Explain quantum computing",
        "response": "Quantum computing uses quantum mechanics principles to process information using quantum bits (qubits).",
        "score_range": (0.70, 0.85)
    },
    {
        "query": "What causes climate change?",
        "response": "Climate change is primarily caused by greenhouse gas emissions from human activities like burning fossil fuels.",
        "score_range": (0.82, 0.92)
    },
    {
        "query": "How do vaccines work?",
        "response": "Vaccines work by introducing a weakened or inactive form of a pathogen to stimulate the immune system.",
        "score_range": (0.88, 0.96)
    },
    {
        "query": "What is the theory of relativity?",
        "response": "Einstein's theory of relativity describes how space, time, and gravity are interconnected.",
        "score_range": (0.78, 0.89)
    },
    {
        "query": "Explain blockchain technology",
        "response": "Blockchain is a distributed ledger technology that records transactions in a secure, transparent manner.",
        "score_range": (0.73, 0.86)
    },
    {
        "query": "What is DNA?",
        "response": "DNA (deoxyribonucleic acid) is the molecule that carries genetic instructions for life.",
        "score_range": (0.91, 0.97)
    }
]


def generate_quality_metrics(base_score: float) -> dict:
    """Generate realistic quality metrics based on a base score"""
    variation = random.uniform(-0.05, 0.05)

    return {
        "rag_score": round(base_score + variation, 3),
        "faithfulness": round(base_score + random.uniform(-0.03, 0.03), 3),
        "answer_relevancy": round(base_score + random.uniform(-0.04, 0.04), 3),
        "context_relevancy": round(base_score + random.uniform(-0.02, 0.05), 3),
        "context_precision": round(base_score + random.uniform(-0.05, 0.05), 3),
        "context_recall": round(base_score + random.uniform(-0.03, 0.06), 3),
        "evaluation_time_ms": round(random.uniform(50, 200), 2),
        "enabled_methods": ["rag_score", "faithfulness", "answer_relevancy", "context_relevancy"]
    }


async def create_test_user(db):
    """Create a test user if it doesn't exist"""
    print("🔍 Checking for test user...")

    result = await db.execute(
        select(User).where(User.username == "test_user")
    )
    user = result.scalar_one_or_none()

    if not user:
        print("👤 Creating test user...")
        # Create a simple hashed password for testing
        # In production, use proper password hashing (bcrypt, etc.)
        import hashlib
        hashed_pw = hashlib.sha256("test_password".encode()).hexdigest()

        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password=hashed_pw,
            full_name="Test User",
            role="user",
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ Created test user: {user.username} (ID: {user.id})")
    else:
        print(f"✅ Test user already exists: {user.username} (ID: {user.id})")

    return user


async def create_test_session(db, user):
    """Create a test session with auto-evaluation enabled"""
    print("\n📝 Creating test chat session...")

    session_id = f"test_eval_{uuid.uuid4().hex[:8]}"

    # Create chat session
    chat_session = ChatSession(
        session_id=session_id,
        user_id=user.id,
        title="Evaluation Test Session",
        is_active=True
    )
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)

    print(f"✅ Created chat session: {session_id} (ID: {chat_session.id})")

    # Create evaluation config with auto-evaluation enabled
    print("⚙️  Enabling auto-evaluation for session...")

    eval_config = EvaluationConfig(
        session_id=chat_session.id,
        auto_evaluate=True,
        enable_faithfulness=True,
        enable_answer_relevancy=True,
        enable_context_precision=True,
        enable_context_recall=True,
        enable_ragas=True
    )
    db.add(eval_config)
    await db.commit()

    print("✅ Auto-evaluation enabled!")

    return chat_session


async def populate_evaluation_results(db, session, num_results=50):
    """Populate evaluation results with sample data"""
    print(f"\n📊 Populating {num_results} evaluation results...")

    created_count = 0
    start_date = datetime.now() - timedelta(days=7)  # Start 7 days ago

    for i in range(num_results):
        # Select random sample data
        sample = random.choice(SAMPLE_DATA)

        # Generate random score within the sample's range
        score_range = sample["score_range"]
        base_score = random.uniform(score_range[0], score_range[1])

        # Generate quality metrics
        quality_metrics = generate_quality_metrics(base_score)

        # Create timestamp (spread over last 7 days)
        created_at = start_date + timedelta(
            seconds=random.randint(0, 7 * 24 * 60 * 60)
        )

        # Create evaluation result
        eval_result = EvaluationResult(
            session_id=session.id,
            query=sample["query"],
            response=sample["response"],
            overall_score=base_score,
            scores=quality_metrics,
            evaluation_time_ms=quality_metrics["evaluation_time_ms"],
            enabled_methods=quality_metrics["enabled_methods"],
            metadata={
                "model_used": random.choice(["gpt-4", "claude-3-sonnet", "ollama/mistral"]),
                "query_latency_ms": round(random.uniform(100, 500), 2),
                "num_sources": random.randint(2, 8),
                "auto_evaluated": True
            },
            created_at=created_at
        )

        db.add(eval_result)
        created_count += 1

        # Commit in batches of 10
        if created_count % 10 == 0:
            await db.commit()
            print(f"  ✓ Created {created_count}/{num_results} evaluation results")

    # Final commit
    await db.commit()
    print(f"✅ Successfully created {created_count} evaluation results!")


async def populate_human_feedback(db, session, num_feedback=20):
    """Populate human feedback entries"""
    print(f"\n👥 Populating {num_feedback} human feedback entries...")

    created_count = 0
    start_date = datetime.now() - timedelta(days=7)

    for i in range(num_feedback):
        # Random feedback type
        feedback_types = ["thumbs_up", "thumbs_down", "rating"]
        feedback_type = random.choice(feedback_types)

        # Generate feedback data based on type
        if feedback_type == "thumbs_up":
            thumbs_up = True
            rating = None
            feedback_text = "Helpful and accurate response!"
        elif feedback_type == "thumbs_down":
            thumbs_up = False
            rating = None
            feedback_text = "Response could be more detailed."
        else:  # rating
            thumbs_up = None
            rating = random.randint(3, 5)  # Mostly positive ratings
            feedback_text = f"Rated {rating} stars - good quality"

        # Create timestamp
        created_at = start_date + timedelta(
            seconds=random.randint(0, 7 * 24 * 60 * 60)
        )

        # Create feedback
        feedback = HumanFeedback(
            session_id=session.id,
            message_id=None,  # Not linking to specific message for test data
            thumbs_up=thumbs_up,
            rating=rating,
            accuracy_rating=rating if rating else None,
            helpfulness_rating=rating if rating else None,
            clarity_rating=rating if rating else None,
            feedback_text=feedback_text,
            feedback_type="inline"
        )

        db.add(feedback)
        created_count += 1

        # Commit in batches of 5
        if created_count % 5 == 0:
            await db.commit()
            print(f"  ✓ Created {created_count}/{num_feedback} feedback entries")

    # Final commit
    await db.commit()
    print(f"✅ Successfully created {created_count} human feedback entries!")


async def main():
    """Main execution function"""
    print("=" * 80)
    print("🚀 EVALUATION DATA POPULATION SCRIPT")
    print("=" * 80)
    print()

    try:
        # Create database session
        async with AsyncSessionLocal() as db:
            # Create test user
            user = await create_test_user(db)

            # Create test session with auto-evaluation
            session = await create_test_session(db, user)

            # Populate evaluation results
            await populate_evaluation_results(db, session, num_results=50)

            # Populate human feedback
            await populate_human_feedback(db, session, num_feedback=20)

            print("\n" + "=" * 80)
            print("✅ DATA POPULATION COMPLETE!")
            print("=" * 80)
            print()
            print(f"📌 Test Session ID: {session.session_id}")
            print(f"📌 Session UUID: {session.id}")
            print(f"📌 User: {user.username}")
            print()
            print("🎯 You can now:")
            print("   1. View the Evaluation Dashboard in the UI")
            print("   2. Use this session ID for testing auto-evaluation")
            print("   3. Submit test queries to see real-time evaluation")
            print()
            print(f"🔗 Session URL: http://localhost:3001?session={session.session_id}")
            print()

    except Exception as e:
        print(f"\n❌ Error populating data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
