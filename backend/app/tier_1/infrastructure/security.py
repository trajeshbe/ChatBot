"""
Security utilities for authentication and password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings
import uuid

# JWT settings
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary containing user data (must include 'sub' key with user ID)
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and extract user ID

    Args:
        token: JWT token string

    Returns:
        User ID (UUID string) if valid, None otherwise
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    return user_id


async def get_current_user_from_request(request, db):
    """
    Extract and validate the current user from request headers

    Args:
        request: FastAPI Request object
        db: AsyncSession database connection

    Returns:
        User object if authenticated, None otherwise
    """
    from fastapi import HTTPException, status
    from sqlalchemy import select
    import logging

    logger = logging.getLogger(__name__)

    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.info("🔓 No Authorization header or invalid format")
        return None

    token = auth_header.replace("Bearer ", "")
    logger.info(f"🔑 Token extracted: {token[:20]}...")

    # Verify token and extract user ID
    user_id_str = verify_token(token)
    if not user_id_str:
        logger.info("❌ Token verification failed")
        return None

    logger.info(f"✅ Token verified, user_id: {user_id_str}")

    # Convert user_id string to UUID for database query
    try:
        user_id_uuid = uuid.UUID(user_id_str)
        logger.info(f"✅ Converted to UUID: {user_id_uuid}")
    except (ValueError, AttributeError) as e:
        logger.error(f"❌ Invalid user_id format: {user_id_str}, error: {e}")
        return None

    # Fetch user from database
    from app.models.database_enhanced import User

    query = select(User).where(User.id == user_id_uuid)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user:
        logger.info(f"✅ User found: {user.username} (department_id: {user.department_id})")
    else:
        logger.info(f"❌ No user found for UUID: {user_id_uuid}")

    return user
