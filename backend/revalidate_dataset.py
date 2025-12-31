"""
Revalidate the Mayandi_Manzil dataset with the new ChatFormatter
"""
import asyncio
import sys
from uuid import UUID

# Add backend to path
sys.path.insert(0, '/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend')

from app.core.database import AsyncSessionLocal
from app.services.finetuning.finetuning_service import FineTuningService
from app.models.finetuning_models import FineTuningDataset
from sqlalchemy import select

DATASET_ID = "09a719ed-7bec-4e1a-898a-4e182646a312"

async def revalidate():
    """Revalidate the dataset"""
    async with AsyncSessionLocal() as db:
        # Get dataset
        stmt = select(FineTuningDataset).where(FineTuningDataset.id == UUID(DATASET_ID))
        result = await db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            print(f"❌ Dataset not found: {DATASET_ID}")
            return

        print(f"📦 Dataset: {dataset.name}")
        print(f"📁 File: {dataset.filename}")
        print(f"🔧 Format: {dataset.format_type}")
        print(f"📊 Current status: is_valid={dataset.is_valid}")
        print()

        # Create service and validate
        service = FineTuningService(db)
        print("🔍 Running validation...")

        try:
            validation_result = await service.validate_dataset(UUID(DATASET_ID))

            print()
            print("=" * 80)
            print("VALIDATION RESULTS")
            print("=" * 80)
            print()
            print(f"✅ Valid: {validation_result['is_valid']}")
            print(f"📊 Samples: {validation_result.get('num_samples', 0)}")
            print()

            if validation_result.get('errors'):
                print("❌ ERRORS:")
                for error in validation_result['errors']:
                    print(f"   {error}")
                print()

            if validation_result.get('warnings'):
                print("⚠️  WARNINGS:")
                for warning in validation_result['warnings']:
                    print(f"   {warning}")
                print()

            if validation_result.get('suggestions'):
                print("💡 SUGGESTIONS:")
                for suggestion in validation_result['suggestions']:
                    print(f"   {suggestion}")
                print()

            if validation_result.get('sample_preview'):
                print("📝 SAMPLE PREVIEW:")
                for i, sample in enumerate(validation_result['sample_preview'][:3], 1):
                    print(f"\n   Sample {i}:")
                    print(f"   {sample}")

            print()
            print("=" * 80)

            # Refresh dataset to see updated values
            await db.refresh(dataset)
            print()
            print(f"🎯 Updated status: is_valid={dataset.is_valid}, num_samples={dataset.num_samples}")
            print(f"🎯 Sample rows count: {len(dataset.sample_rows) if dataset.sample_rows else 0}")

        except Exception as e:
            print(f"❌ Validation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(revalidate())
