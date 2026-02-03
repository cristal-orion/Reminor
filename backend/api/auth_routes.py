"""
Authentication Routes for Reminor API
Handles user registration, login, token refresh, and user info.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends

from models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, LLMConfigUpdate, LLMConfigResponse, LanguageUpdate
from core.auth import (
    create_user,
    authenticate_user,
    create_tokens,
    decode_token,
    get_user_by_id,
    get_current_user,
    get_user_llm_config,
    save_user_llm_config,
    update_user_language,
    mask_api_key,
    decrypt_api_key,
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
            name=user_data.name,
            language=user_data.language or "it",
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
        language=user.get("language", "it"),
        created_at=datetime.fromisoformat(user["created_at"]),
    )


@router.put("/settings/language")
async def update_language(
    data: LanguageUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update language preference for the current user.
    Returns new tokens so the frontend can refresh its state.
    """
    success = update_user_language(current_user.id, data.language)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update language",
        )

    # Return new tokens so frontend can refresh
    tokens = create_tokens(current_user.id, current_user.email)
    return {
        "language": data.language,
        **tokens,
    }


@router.get("/settings/llm", response_model=LLMConfigResponse)
async def get_llm_config(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user's saved LLM configuration.
    API key is returned masked.
    """
    config = get_user_llm_config(current_user.id)

    if not config:
        return LLMConfigResponse()

    has_key = bool(config.get("api_key"))
    preview = mask_api_key(config["api_key"]) if has_key else None

    return LLMConfigResponse(
        provider=config.get("provider", "groq"),
        model=config.get("model"),
        has_api_key=has_key,
        api_key_preview=preview,
    )


@router.put("/settings/llm", response_model=LLMConfigResponse)
async def update_llm_config(
    config: LLMConfigUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Save LLM configuration for the current user.
    API key is encrypted before storage.
    """
    save_user_llm_config(
        user_id=current_user.id,
        provider=config.provider,
        model=config.model,
        api_key=config.api_key,
    )

    # Return the saved config with masked key
    saved = get_user_llm_config(current_user.id)
    has_key = bool(saved and saved.get("api_key"))
    preview = mask_api_key(saved["api_key"]) if has_key else None

    return LLMConfigResponse(
        provider=config.provider,
        model=config.model,
        has_api_key=has_key,
        api_key_preview=preview,
    )
