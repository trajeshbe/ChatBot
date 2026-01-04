"""
Create British Council Module Configuration

This script creates the initial module configuration for the British Council POC
in the module_configurations database table.

Usage:
    python -m scripts.british_council.create_module_config
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tier_1.infrastructure.database import AsyncSessionLocal
from app.services.poc_config_service import poc_config_service


async def create_british_council_config():
    """Create module configuration for British Council POC."""

    print("🚀 Creating British Council Module Configuration...")

    config = {
        "llm": {
            "profile_extraction": {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "top_p": 0.95,
                "max_tokens": 1000,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            "query_classification": {
                "model": "gpt-4o-mini",  # Override qwen2.5vl that fails at JSON
                "temperature": 0.0,
                "top_p": 1.0,
                "max_tokens": 150,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        },
        "retrieval": {
            "top_k": 50,
            "rerank_top_k": 20,
            "min_score": 0.3,
            "use_direct_search": False  # Feature flag: set to True to bypass IntelligentRetrievalService
        },
        "scoring": {
            "weights": {
                "semantic": 0.6,
                "profile": 0.4
            },
            "factors": {
                "level_match": 0.3,
                "format_match": 0.2,
                "availability_match": 0.2,
                "skill_match": 0.3
            }
        },
        "thresholds": {
            "similarity_threshold": 0.7,
            "min_profile_score": 0.3,
            "high_confidence": 0.8
        },
        "prompts": {
            "system": {
                "profile_extraction": """You are an expert at extracting structured user profiles from natural language input.

Extract the following information:
- skills: List of professional skills (e.g., ["software engineering", "data analysis"])
- interests: Learning interests and goals (e.g., ["business English", "IELTS preparation"])
- education_level: Current English level - must be one of: "beginner", "intermediate", "advanced"
- career_goals: Professional aspirations (e.g., ["work internationally", "get promoted"])
- preferred_format: Course delivery preference - must be one of: "online", "in-person", "hybrid"
- language_proficiency: CEFR level - must be one of: "A1", "A2", "B1", "B2", "C1", "C2"
- availability: Schedule preference - must be one of: "weekdays", "weekends", "flexible"

Return ONLY valid JSON matching this schema. Do not include any explanatory text."""
            },
            "user": {
                "recommendation_query": "Based on the user's profile: {profile}, recommend courses that match their {interests} and {career_goals}."
            }
        },
        "features": {
            "enable_reranking": True,
            "enable_profile_scoring": True,
            "enable_llm_classification": True
        },
        "parameters": {
            "cefr_level_mapping": {
                "A1": "beginner",
                "A2": "beginner",
                "B1": "intermediate",
                "B2": "intermediate",
                "C1": "advanced",
                "C2": "advanced"
            }
        }
    }

    async with AsyncSessionLocal() as db:
        try:
            # Check if config already exists
            existing = await poc_config_service.get_config(
                db=db,
                module_name="british_council",
                include_overrides=False
            )

            if existing:
                print("⚠️  British Council config already exists")
                print("   Use update endpoint to modify existing config")
                return False

        except Exception:
            # Config doesn't exist, proceed with creation
            pass

        try:
            module_config = await poc_config_service.create_module_config(
                db=db,
                module_name="british_council",
                display_name="British Council Course Recommender",
                module_type="tier3_customer_solution",
                config=config,
                description="Personalized English course recommendations using hybrid retrieval and profile-based scoring",
                category="education",
                created_by=None  # System creation
            )

            await db.commit()

            print("✅ British Council module configuration created successfully!")
            print(f"   Module Name: {module_config.module_name}")
            print(f"   Display Name: {module_config.display_name}")
            print(f"   Type: {module_config.module_type}")
            print(f"   Category: {module_config.category}")
            print(f"   Created At: {module_config.created_at}")
            print()
            print("📋 Configuration Summary:")
            print(f"   - LLM Models: {len(config['llm'])} stages")
            print(f"     • Profile Extraction: {config['llm']['profile_extraction']['model']}")
            print(f"     • Query Classification: {config['llm']['query_classification']['model']}")
            print(f"   - Retrieval: top_k={config['retrieval']['top_k']}, rerank_top_k={config['retrieval']['rerank_top_k']}")
            print(f"   - Scoring Weights: semantic={config['scoring']['weights']['semantic']}, profile={config['scoring']['weights']['profile']}")
            print(f"   - Features: {', '.join([k for k, v in config['features'].items() if v])}")
            print()
            print("🎯 Next Steps:")
            print("   1. Test via API: POST /api/v1/module-config/modules/british_council")
            print("   2. View in UI: Open British Council POC → Click Configure button")
            print("   3. Customize: Adjust LLM models, weights, thresholds via UI")

            return True

        except Exception as e:
            print(f"❌ Error creating British Council config: {e}")
            await db.rollback()
            raise


async def main():
    """Main entry point."""
    try:
        success = await create_british_council_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
