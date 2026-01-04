"""
British Council Course Catalog Data Ingestion Script

Loads course_catalog_sample.json into the database with proper field mapping.
Ensures courses are available for the recommendation engine to search.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tier_1.infrastructure.database import AsyncSessionLocal
from app.tier_1.infrastructure.config import Settings
import uuid
from datetime import datetime


def map_cefr_to_level(cefr_level: str) -> str:
    """
    Map CEFR levels to beginner/intermediate/advanced.

    Handles single levels (A1, B1, C1) and ranges (A2-B1, B1-C1).
    For ranges, uses the starting level.
    """
    if not cefr_level:
        return 'intermediate'  # default

    # Extract first level from range (e.g., "B1-C1" -> "B1")
    first_level = cefr_level.split('-')[0].strip()

    if first_level.startswith('A'):  # A1, A2
        return 'beginner'
    elif first_level.startswith('B'):  # B1, B2
        return 'intermediate'
    elif first_level.startswith('C'):  # C1, C2
        return 'advanced'
    else:
        return 'intermediate'  # default


def map_mode_to_format(mode: str) -> str:
    """Map mode to format."""
    mode_lower = mode.lower()
    if 'online' in mode_lower:
        return 'online'
    elif 'hybrid' in mode_lower:
        return 'hybrid'
    elif 'in-person' in mode_lower or 'classroom' in mode_lower:
        return 'in-person'
    else:
        return 'online'  # default


async def ingest_courses():
    """Load British Council course catalog into database."""

    # Load sample data
    # __file__ = /app/scripts/british_council/ingest_course_catalog.py
    # parent.parent.parent = /app/
    sample_data_path = Path(__file__).parent.parent.parent / "sample_data" / "tier3_customer_pocs" / "british_council" / "course_catalog_sample.json"

    print(f"Loading course catalog from: {sample_data_path}")

    with open(sample_data_path, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses to ingest")

    # Initialize database session
    async with AsyncSessionLocal() as db:
        settings = Settings()

        try:
            ingested_count = 0

            for course in courses:
                print(f"\nIngesting: {course['course_name']}")

                # Map fields from sample data format to service expectations
                level = map_cefr_to_level(course.get('level_required', 'B1'))
                format_type = map_mode_to_format(course.get('mode', 'Online'))

                # Create rich text content for vector search
                duration_text = f"{course.get('duration_weeks', 'N/A')} weeks, {course.get('hours_per_week', 'N/A')} hours/week"
                start_dates_text = ', '.join(course.get('start_dates', []))
                includes_text = ', '.join(course.get('includes', []))

                content = f"""
Course: {course['course_name']}
Course ID: {course['course_id']}
Level Required: {course.get('level_required', 'Not specified')} ({level})
Duration: {duration_text}
Mode: {course.get('mode', 'Online')}
Price: £{course.get('price_gbp', 'N/A')}
Focus Areas: {', '.join(course.get('focus_areas', []))}
Start Dates: {start_dates_text}
Max Students: {course.get('max_students', 'N/A')}
Instructor: {course.get('instructor_qualification', 'British Council Certified Instructor')}
Includes: {includes_text}
Target Score: {course.get('target_score', 'N/A')}
"""

                # Create metadata with mapped fields
                metadata = {
                    "course_id": course["course_id"],
                    "course_name": course["course_name"],

                    # Mapped fields (service expects these names)
                    "level": level,  # beginner/intermediate/advanced
                    "format": format_type,  # online/in-person/hybrid
                    "skills": course.get("focus_areas", []),  # List of skills

                    # Original fields from sample data
                    "cefr_level": course.get("level_required", ""),
                    "mode": course.get("mode", ""),
                    "focus_areas": course.get("focus_areas", []),

                    # Course details from sample data
                    "duration_weeks": course.get("duration_weeks", None),
                    "hours_per_week": course.get("hours_per_week", None),
                    "price_gbp": course.get("price_gbp", None),
                    "start_dates": course.get("start_dates", []),
                    "max_students": course.get("max_students", None),
                    "target_score": course.get("target_score", None),
                    "instructor_qualification": course.get("instructor_qualification", ""),
                    "includes": course.get("includes", []),

                    # Legacy fields for compatibility (if needed)
                    "duration": duration_text,
                    "cost": f"£{course.get('price_gbp', 'N/A')}",
                    "instructor": course.get("instructor_qualification", ""),
                    "schedule": "See start_dates",

                    # Categorization
                    "company": "british_council",
                    "usecase": "course_recommendation",
                    "module": "british_council_poc",
                    "source_type": "course_catalog"
                }

                # Store in documents table
                from app.models.database import Document, DocumentChunk

                # Create document record
                document = Document(
                    id=uuid.uuid4(),
                    filename=f"{course['course_id']}.txt",
                    file_path=f"british_council/courses/{course['course_id']}.txt",
                    file_type="text/plain",
                    file_size=len(content.encode('utf-8')),
                    source_type="uploaded",
                    meta_info=metadata,  # Note: mapped to 'metadata' column in DB
                    processing_status='completed',
                    created_at=datetime.utcnow()
                )

                db.add(document)
                await db.flush()  # Get document ID

                # Create embedding for the course content
                from app.tier_1.embeddings.embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                await embedding_service.initialize()  # Initialize the service

                embedding_vector = await embedding_service.get_embedding(content)

                # Create chunk (one chunk per course for simplicity)
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    chunk_index=0,
                    content=content.strip(),
                    embedding=embedding_vector,
                    meta_info=metadata,  # Note: mapped to JSON column
                    created_at=datetime.utcnow()
                )

                db.add(chunk)

                print(f"  ✓ Created document and chunk with embedding")
                print(f"  ✓ Level: {course.get('level_required')} → {level}")
                print(f"  ✓ Mode: {course.get('mode')} → {format_type}")
                print(f"  ✓ Skills: {len(course.get('focus_areas', []))} focus areas")

                ingested_count += 1

            # Commit all changes
            await db.commit()

            print(f"\n{'='*60}")
            print(f"✓ Successfully ingested {ingested_count} courses")
            print(f"{'='*60}")

            # Verify ingestion
            from sqlalchemy import select, func
            result = await db.execute(
                select(func.count(Document.id)).where(
                    Document.meta_info['company'].astext == 'british_council'
                )
            )
            count = result.scalar()
            print(f"\nVerification: {count} British Council documents in database")

        except Exception as e:
            print(f"\n❌ Error during ingestion: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


async def verify_ingestion():
    """Verify that courses can be retrieved by the recommendation engine."""

    async with AsyncSessionLocal() as db:
        settings = Settings()

        try:
            from app.tier_1.rag.intelligent_retrieval_service import IntelligentRetrievalService

            retrieval_service = IntelligentRetrievalService()

            # Test query: "I want to improve my business English skills"
            test_query = "I want to improve my business English skills for professional communication"

            print(f"\n{'='*60}")
            print("Testing Retrieval with Query:")
            print(f"  '{test_query}'")
            print(f"{'='*60}")

            results = await retrieval_service.intelligent_search(
                db=db,
                query=test_query,
                top_k=3,
                company="british_council"
            )

            print(f"\nRetrieved {len(results)} courses:")
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                print(f"\n{i}. {metadata.get('course_name', 'Unknown')}")
                print(f"   Score: {result.get('score', 0.0):.4f}")
                print(f"   Level: {metadata.get('cefr_level')} ({metadata.get('level')})")
                print(f"   Mode: {metadata.get('mode')} ({metadata.get('format')})")
                skills = metadata.get('focus_areas', [])
                if skills:
                    skills_text = ', '.join(skills)
                    print(f"   Skills: {skills_text[:80]}{'...' if len(skills_text) > 80 else ''}")

            if len(results) > 0:
                print(f"\n✓ Verification successful - courses are retrievable!")
            else:
                print(f"\n⚠️ Warning: No courses retrieved - check vector search configuration")

        except Exception as e:
            print(f"\n❌ Verification error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


async def clean_british_council_data():
    """Remove all British Council courses from database (for re-ingestion)."""

    async with AsyncSessionLocal() as db:
        try:
            from app.models.database import Document, DocumentChunk
            from sqlalchemy import delete, select

            # Delete chunks first (foreign key constraint)
            result = await db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id.in_(
                        select(Document.id).where(
                            Document.meta_info['company'].astext == 'british_council'
                        )
                    )
                )
            )
            chunks_deleted = result.rowcount

            # Delete documents
            result = await db.execute(
                delete(Document).where(
                    Document.meta_info['company'].astext == 'british_council'
                )
            )
            docs_deleted = result.rowcount

            await db.commit()

            print(f"Cleaned {docs_deleted} documents and {chunks_deleted} chunks")

        except Exception as e:
            print(f"❌ Cleanup error: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="British Council Course Catalog Ingestion")
    parser.add_argument("--clean", action="store_true", help="Clean existing data before ingesting")
    parser.add_argument("--verify-only", action="store_true", help="Only verify retrieval, don't ingest")

    args = parser.parse_args()

    if args.verify_only:
        print("Running verification only...")
        asyncio.run(verify_ingestion())
    else:
        if args.clean:
            print("Cleaning existing British Council data...")
            asyncio.run(clean_british_council_data())

        print("Starting course catalog ingestion...")
        asyncio.run(ingest_courses())

        print("\nRunning verification...")
        asyncio.run(verify_ingestion())

        print("\n" + "="*60)
        print("✓ INGESTION COMPLETE")
        print("="*60)
        print("\nYou can now test the British Council POC at:")
        print("  http://localhost:3001")
        print("\nThe course recommendation engine should now return results!")
