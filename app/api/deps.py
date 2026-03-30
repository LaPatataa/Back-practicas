from fastapi import Header, HTTPException, status, Depends
from typing import Callable, List, Any, Dict

from app.core.security.supabase_auth import get_supabase_user
from app.services.roles_service import get_user_roles

async def get_current_user(user: Dict[str, Any] = Depends(get_supabase_user)) -> Dict[str, Any]:
    return user

def extract_token(authorization: str) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return authorization.split(" ", 1)[1].strip()

def require_roles(allowed: List[str]) -> Callable:
    async def _guard(
        user: Dict[str, Any] = Depends(get_current_user),
        authorization: str = Header(default=""),
    ) -> Dict[str, Any]:
        token = extract_token(authorization)
        roles = await get_user_roles(user_id=user["id"], access_token=token)

        if not any(r in allowed for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {allowed}",
            )

        # Opcional: adjuntamos roles al user para no reconsultar
        user["roles"] = roles
        return user

    return _guard