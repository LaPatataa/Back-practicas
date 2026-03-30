from typing import List
import httpx
from app.core.config import settings

async def get_user_roles(user_id: str, access_token: str) -> List[str]:
    """
    Lee roles del usuario desde Supabase PostgREST.
    """
    base = settings.SUPABASE_URL.rstrip("/") + "/rest/v1"
    url = f"{base}/user_roles?user_id=eq.{user_id}&select=roles(name)"

    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code != 200:
        return []

    roles: List[str] = []
    for row in resp.json():
        r = row.get("roles")
        if isinstance(r, dict) and r.get("name"):
            roles.append(r["name"])

    return roles