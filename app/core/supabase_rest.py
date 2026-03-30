import httpx
from typing import Any, Dict, Optional
from fastapi.encoders import jsonable_encoder
from app.core.config import settings

def rest_base_url() -> str:
    return settings.SUPABASE_URL.rstrip("/") + "/rest/v1"


def rpc_base_url() -> str:
    return settings.SUPABASE_URL.rstrip("/") + "/rest/v1/rpc"


def headers(access_token: str) -> Dict[str, str]:
    return {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }

async def supabase_get(path: str, access_token: str, params: Optional[Dict[str, Any]] = None):
    url = rest_base_url() + path
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.get(url, headers=headers(access_token), params=params)

async def supabase_post(path: str, access_token: str, payload: Dict[str, Any]):
    url = rest_base_url() + path
    safe_payload = jsonable_encoder(payload)
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.post(url, headers=headers(access_token), json=safe_payload)

async def supabase_patch(path: str, access_token: str, payload: Dict[str, Any]):
    url = rest_base_url() + path
    safe_payload = jsonable_encoder(payload)
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.patch(url, headers=headers(access_token), json=safe_payload)

async def supabase_post_rpc(fn_name: str, payload: Dict[str, Any], access_token: str):
    url = f"{rpc_base_url()}/{fn_name}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.post(url, headers=headers(access_token), json=payload)
