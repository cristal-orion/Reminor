"""
Authentication Routes for Reminor API
Handles user registration, login, token refresh, and user info.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends

from models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from core.auth import (
    create_user,
    authenticate_user,
    create_tokens,
    decode_token,
    get_user_by_id,
    get_current_user,
    CurrentUser,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user account.

    Returns JWT tokens on successful registration.
    """
    try:
        user = create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Create and return tokens
    tokens = create_tokens(user["id"], user["email"])
    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT tokens.
    """
    user = authenticate_user(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = create_tokens(user["id"], user["email"])
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using a valid refresh token.
    """
    payload = decode_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    tokens = create_tokens(user["id"], user["email"])
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    """
    user = get_user_by_id(current_user.id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        created_at=datetime.fromisoformat(user["created_at"]),
    )
