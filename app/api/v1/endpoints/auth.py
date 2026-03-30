from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict

from app.api.deps import get_current_user, extract_token
from app.services.roles_service import get_user_roles

router = APIRouter(prefix="/auth", tags=["auth"])

class MeResponse(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    roles: List[str] = []

@router.get("/me", response_model=MeResponse)
async def me(
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)
    roles = await get_user_roles(user_id=user["id"], access_token=token)

    return MeResponse(
        id=user.get("id"),
        email=user.get("email"),
        roles=roles,
    )