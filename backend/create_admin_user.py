"""
Script to create a default admin user
Usage: python create_admin_user.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Import models
from app.models.database_enhanced import User, UserRole, Base
from app.core.config import settings
from app.core.security import get_password_hash  # 🔧 FIX: Use bcrypt hashing


async def create_default_admin():
    """Create a default admin user if one doesn't exist"""

    # Create async engine
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        future=True
    )

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Check if admin user already exists
            query = select(User).where(User.username == 'admin')
            result = await session.execute(query)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print("✓ Admin user already exists")
                print(f"   Username: {existing_admin.username}")
                print(f"   Email: {existing_admin.email}")
                print(f"   Role: {existing_admin.role.value}")
                return

            # Create admin user
            # Default password: 'admin' (change in production!)
            default_password = 'admin'
            # 🔧 FIX: Changed from hashlib.sha256 to bcrypt
            hashed_password = get_password_hash(default_password)

            admin_user = User(
                username='admin',
                email='admin@example.com',
                full_name='System Administrator',
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("✓ Default admin user created successfully!")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Password: {default_password}")
            print(f"   Role: {admin_user.role.value}")
            print("\n⚠️  IMPORTANT: Change the default password after first login!")

        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("Creating default admin user...")
    asyncio.run(create_default_admin())
