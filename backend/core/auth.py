"""
JWT Authentication Module for Reminor
Handles password hashing, token creation/verification, and user authentication.
"""

import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import uuid

from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Bearer token security
bearer_scheme = HTTPBearer(auto_error=False)

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def get_users_db() -> dict:
    """Load users database from JSON file."""
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_users_db(users: dict) -> None:
    """Save users database to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


# ==================== PASSWORD FUNCTIONS ====================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Truncates to 72 bytes (bcrypt limit)."""
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash. Truncates to 72 bytes (bcrypt limit)."""
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ==================== TOKEN FUNCTIONS ====================


def create_access_token(user_id: str, email: str) -> str:
    """Create a new access token."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a new refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_tokens(user_id: str, email: str) -> dict:
    """Create both access and refresh tokens."""
    return {
        "access_token": create_access_token(user_id, email),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    }


# ==================== USER FUNCTIONS ====================


def get_user_by_email(email: str) -> Optional[dict]:
    """Find a user by email address."""
    users = get_users_db()
    for user_id, user_data in users.items():
        if user_data.get("email", "").lower() == email.lower():
            return {"id": user_id, **user_data}
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Find a user by ID."""
    users = get_users_db()
    if user_id in users:
        return {"id": user_id, **users[user_id]}
    return None


def create_user(email: str, password: str, name: Optional[str] = None, language: str = "it") -> dict:
    """Create a new user."""
    users = get_users_db()

    # Check if email already exists
    if get_user_by_email(email):
        raise ValueError("Email already registered")

    # Generate unique user ID
    user_id = str(uuid.uuid4())[:8]  # Short UUID for cleaner paths

    # Create user data
    user_data = {
        "email": email.lower(),
        "password_hash": hash_password(password),
        "name": name,
        "language": language if language in ("it", "en") else "it",
        "created_at": datetime.utcnow().isoformat(),
    }

    # Save to database
    users[user_id] = user_data
    save_users_db(users)

    # Create user data directory
    user_dir = DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "journal").mkdir(exist_ok=True)

    return {"id": user_id, **user_data}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user with email and password."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return user


# ==================== API KEY ENCRYPTION ====================


def _get_fernet() -> Fernet:
    """Derive a Fernet key from JWT_SECRET_KEY."""
    key_bytes = JWT_SECRET_KEY.encode("utf-8")
    # Derive a 32-byte key using SHA256, then base64-encode for Fernet
    derived = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key using Fernet."""
    f = _get_fernet()
    return f.encrypt(api_key.encode("utf-8")).decode("utf-8")


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key using Fernet."""
    f = _get_fernet()
    return f.decrypt(encrypted_key.encode("utf-8")).decode("utf-8")


def mask_api_key(api_key: str) -> str:
    """Return a masked preview of an API key, e.g. 'sk-...abc123'."""
    if not api_key or len(api_key) < 8:
        return "***"
    return api_key[:3] + "..." + api_key[-4:]


# ==================== LLM CONFIG FUNCTIONS ====================


def get_user_llm_config(user_id: str) -> Optional[dict]:
    """
    Get the saved LLM config for a user from users.json.
    Returns dict with provider, model, api_key (decrypted) or None.
    """
    users = get_users_db()
    user_data = users.get(user_id)
    if not user_data:
        return None

    llm_config = user_data.get("llm_config")
    if not llm_config:
        return None

    result = {
        "provider": llm_config.get("provider", "groq"),
        "model": llm_config.get("model"),
        "api_key": None,
    }

    encrypted_key = llm_config.get("encrypted_api_key")
    if encrypted_key:
        try:
            result["api_key"] = decrypt_api_key(encrypted_key)
        except Exception:
            result["api_key"] = None

    return result


def save_user_llm_config(user_id: str, provider: str, model: Optional[str] = None, api_key: Optional[str] = None) -> None:
    """
    Save LLM config for a user in users.json.
    The API key is encrypted before storage.
    """
    users = get_users_db()
    if user_id not in users:
        return

    llm_config = {
        "provider": provider,
        "model": model,
    }

    if api_key:
        llm_config["encrypted_api_key"] = encrypt_api_key(api_key)
    else:
        # Preserve existing encrypted key if no new key provided
        existing = users[user_id].get("llm_config", {})
        if existing.get("encrypted_api_key"):
            llm_config["encrypted_api_key"] = existing["encrypted_api_key"]

    users[user_id]["llm_config"] = llm_config
    save_users_db(users)


def update_user_language(user_id: str, language: str) -> bool:
    """Update the language preference for a user."""
    if language not in ("it", "en"):
        return False
    users = get_users_db()
    if user_id not in users:
        return False
    users[user_id]["language"] = language
    save_users_db(users)
    return True


# ==================== FASTAPI DEPENDENCIES ====================


class CurrentUser:
    """Represents the authenticated current user."""
    def __init__(self, user_id: str, email: str, name: Optional[str] = None, language: str = "it"):
        self.id = user_id
        self.email = email
        self.name = name
        self.language = language


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> CurrentUser:
    """
    FastAPI dependency to get the current authenticated user.
    Extracts user info from JWT token in Authorization header.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    email = payload.get("email")

    if user_id is None or email is None:
        raise credentials_exception

    # Optionally verify user still exists
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return CurrentUser(
        user_id=user_id,
        email=email,
        name=user.get("name"),
        language=user.get("language", "it"),
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[CurrentUser]:
    """
    Optional user dependency - returns None if not authenticated.
    Useful for endpoints that work with or without auth.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
