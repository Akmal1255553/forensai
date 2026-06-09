"""Supabase JWT verification for API requests."""
from __future__ import annotations

import jwt
from fastapi import Header, HTTPException

from config import SUPABASE_ENABLED, SUPABASE_JWT_SECRET


def verify_access_token(token: str) -> str | None:
    if not SUPABASE_JWT_SECRET:
        return None
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def resolve_user_id(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        uid = verify_access_token(token)
        if uid:
            return uid
        raise HTTPException(401, "invalid_token")

    if SUPABASE_ENABLED:
        raise HTTPException(401, "auth_required")

    uid = (x_user_id or "").strip()
    if not uid:
        raise HTTPException(400, "user_id_required")
    return uid


def optional_user_id(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        return verify_access_token(token)
    if SUPABASE_ENABLED:
        return None
    return (x_user_id or "").strip() or None
