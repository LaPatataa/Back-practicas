"""Supabase Auth validation.

Backend does NOT handle login/registration.
It only validates the Bearer access_token issued by Supabase.

Strategy used here: call Supabase endpoint /auth/v1/user.
This avoids handling JWKS key rotation manually.
"""

from typing import Any, Dict, Optional

import httpx
from fastapi import Header, HTTPException, status

from app.core.config import settings

SUPABASE_USER_ENDPOINT = "/auth/v1/user"

async def get_supabase_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    url = settings.SUPABASE_URL.rstrip("/") + SUPABASE_USER_ENDPOINT
    headers = {
        "Authorization": authorization,
        "apikey": settings.SUPABASE_ANON_KEY,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code == 200:
        return resp.json()

    if resp.status_code in (401, 403):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Supabase auth error: {resp.status_code}",
    )
