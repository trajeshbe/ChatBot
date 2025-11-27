"""
Authentication Service
Handles user authentication, login, and session management
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.database import User
from app.core.security import verify_password, get_password_hash, create_access_token


class AuthService:
    """Service for handling authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        stmt = select(User).where(
            (User.username == username) | (User.email == username)
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Check if user is active
        if not user.is_active:
            return None

        # Verify password
        if not user.hashed_password:
            # For users without password, check if it's the default admin
            if username == "admin" and password == "admin":
                # Set the password for first time login
                user.hashed_password = get_password_hash("admin")
                await self.db.commit()
                return user
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def create_user_token(self, user: User) -> str:
        """
        Create JWT token for authenticated user

        Args:
            user: Authenticated user object

        Returns:
            JWT token string
        """
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        await self.db.commit()

        # Create token with user data
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role
        }

        return create_access_token(token_data)

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from JWT token

        Args:
            token: JWT token string

        Returns:
            User object if token valid, None otherwise
        """
        from app.core.security import verify_token

        user_id = verify_token(token)
        if not user_id:
            return None

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        stmt = select(User).where(User.id == user_uuid)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        return user

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "USER"
    ) -> User:
        """
        Register a new user

        Args:
            username: Unique username
            email: User email
            password: Plain text password
            full_name: Optional full name
            role: User role (default: USER)

        Returns:
            Created user object

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Username '{username}' already exists")

        # Check if email exists
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Email '{email}' already registered")

        # Create new user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True,
            is_verified=True  # Auto-verify for now
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password

        Args:
            user_id: User UUID
            old_password: Current password
            new_password: New password

        Returns:
            True if successful, False otherwise
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            return False

        # Set new password
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

        return True
