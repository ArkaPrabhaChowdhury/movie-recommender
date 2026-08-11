"""Authentication and ownership checks for multi-tenant API routes."""
import os
from typing import Optional

from fastapi import Header, HTTPException
from config.constants import SUPABASE_KEY, SUPABASE_URL


def _required() -> bool:
    return os.getenv("REQUIRE_AUTH", "false").lower() == "true"


def authenticated_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        if _required():
            raise HTTPException(status_code=401, detail="Bearer token required")
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token or not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=401, detail="Invalid authentication configuration")
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        user = client.auth.get_user(token).user
        return str(user.id)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def assert_owner(requested_user_id: str, authenticated_id: Optional[str]) -> None:
    if _required() and authenticated_id != requested_user_id:
        raise HTTPException(status_code=403, detail="User resource belongs to another tenant")
