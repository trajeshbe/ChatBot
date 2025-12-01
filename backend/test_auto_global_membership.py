#!/usr/bin/env python3
"""
Test script to verify new users are automatically added to Global project
"""
import asyncio
import sys
sys.path.insert(0, '/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import uuid

from app.services.auth_service import AuthService
from app.models.database import User
from app.models.database_enhanced import Project, ProjectMember

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ragchatbot"

async def test_auto_global_membership():
    """Test that new users are automatically added to Global project"""

    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create auth service
        auth_service = AuthService(db)

        # Generate unique username
        test_username = f"test_user_{int(asyncio.get_event_loop().time())}"
        test_email = f"{test_username}@test.com"

        print(f"\n1. Creating new user: {test_username}")

        try:
            # Register new user
            new_user = await auth_service.register_user(
                username=test_username,
                email=test_email,
                password="testpassword123",
                full_name="Test User Auto Global",
                role="USER"
            )

            print(f"   ✅ User created successfully: {new_user.id}")

            # Check if user is in Global project
            print(f"\n2. Checking Global project membership...")

            # Find Global project
            stmt = select(Project).where(Project.name == 'Global')
            result = await db.execute(stmt)
            global_project = result.scalar_one_or_none()

            if not global_project:
                print("   ❌ ERROR: Global project not found!")
                return False

            print(f"   ✅ Global project found: {global_project.id}")

            # Check if user is a member
            stmt = select(ProjectMember).where(
                (ProjectMember.project_id == global_project.id) &
                (ProjectMember.user_id == new_user.id)
            )
            result = await db.execute(stmt)
            membership = result.scalar_one_or_none()

            if membership:
                print(f"   ✅ User is AUTOMATICALLY a member of Global project!")
                print(f"      Role: {membership.role}")
                print(f"      Joined: {membership.joined_at}")
                return True
            else:
                print(f"   ❌ ERROR: User is NOT a member of Global project!")
                return False

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False
        finally:
            await engine.dispose()

if __name__ == "__main__":
    result = asyncio.run(test_auto_global_membership())

    if result:
        print(f"\n✅ TEST PASSED: New users are automatically added to Global project")
        sys.exit(0)
    else:
        print(f"\n❌ TEST FAILED: Automatic Global project membership not working")
        sys.exit(1)
