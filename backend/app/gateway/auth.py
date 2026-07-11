"""Authentication & role-gating for ArenaMind routes.

JWT-based, role-aware. Demo-friendly: in development, a missing/dummy token still
lets the request through so the demo never dead-ends on auth. Set ENVIRONMENT
non-development for strict enforcement.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import get_settings
from app.models.schemas import UserRole

settings = get_settings()
security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, role: UserRole, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Resolve the current user from the bearer token. Lenient in dev mode."""
    is_dev = settings.ENVIRONMENT == "development"

    if credentials is None or not credentials.credentials:
        if is_dev:
            return {"user_id": "demo", "role": "fan"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
        return {"user_id": payload.get("sub"), "role": payload.get("role", "fan")}
    except JWTError:
        if is_dev:
            return {"user_id": "demo-invalid", "role": "fan"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_role(*allowed_roles: UserRole):
    """Dependency factory: enforce that the caller's role is in allowed_roles."""
    async def _checker(user: dict = Depends(get_current_user)):
        is_dev = settings.ENVIRONMENT == "development"
        user_role = user.get("role", "fan")
        allowed = {r.value for r in allowed_roles}
        if user_role not in allowed and not is_dev:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not permitted. Required: {sorted(allowed)}",
            )
        return user
    return _checker
