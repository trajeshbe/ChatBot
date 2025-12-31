"""
Authentication API Routes
Endpoints for login, logout, registration, and token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.database_enhanced import User, UserTeam
from app.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
    ChangePasswordRequest
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_user_primary_team_id(db: AsyncSession, user_id: str) -> str:
    """
    Get user's primary team ID from user_teams table

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Primary team UUID or None
    """
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)

        # Find primary team
        stmt = select(UserTeam).where(
            (UserTeam.user_id == user_uuid) &
            (UserTeam.is_primary == True)
        )
        result = await db.execute(stmt)
        user_team = result.scalar_one_or_none()

        if user_team:
            return str(user_team.team_id)

        # If no primary team, get the first team
        stmt = select(UserTeam).where(UserTeam.user_id == user_uuid)
        result = await db.execute(stmt)
        user_team = result.scalar_one_or_none()

        return str(user_team.team_id) if user_team else None
    except Exception as e:
        print(f"Error fetching user team: {e}")
        return None


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(db)


@router.post("/login", response_model=LoginResponse, summary="User login")
async def login(
    credentials: LoginRequest,
    auth: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token

    Default credentials:
    - Username: admin
    - Password: admin
    """
    # Authenticate user
    user = await auth.authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = await auth.create_user_token(user)

    # Get user's primary team
    team_id = await get_user_primary_team_id(db, str(user.id))

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            department_id=str(user.department_id) if user.department_id else None,
            team_id=team_id
        )
    )


@router.post("/register", response_model=UserResponse, summary="Register new user")
async def register(
    user_data: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account"""
    try:
        user = await auth.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )

        # Get user's primary team
        team_id = await get_user_primary_team_id(db, str(user.id))

        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            department_id=str(user.department_id) if user.department_id else None,
            team_id=team_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user information"""
    token = credentials.credentials

    user = await auth.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user's primary team
    team_id = await get_user_primary_team_id(db, str(user.id))

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
        department_id=str(user.department_id) if user.department_id else None,
        team_id=team_id
    )


# Dependency function for required authentication
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth: AuthService = Depends(get_auth_service)
) -> User:
    """
    Dependency function to get current authenticated user.
    Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user = await auth.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Dependency function for optional authentication (for public endpoints)
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    auth: AuthService = Depends(get_auth_service)
):
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user = await auth.get_current_user(token)
        return user
    except Exception:
        return None


@router.post("/change-password", summary="Change password")
async def change_password(
    password_data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth: AuthService = Depends(get_auth_service)
):
    """Change current user's password"""
    token = credentials.credentials

    user = await auth.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    success = await auth.change_password(
        user.id,
        password_data.old_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    return {"message": "Password changed successfully"}


@router.post("/logout", summary="Logout (client-side token removal)")
async def logout():
    """
    Logout endpoint (stateless - client should remove token)

    Since JWT is stateless, actual logout happens on client side by removing the token.
    This endpoint is provided for consistency and can be extended with token blacklisting.
    """
    return {"message": "Logout successful. Please remove the token from client storage."}
