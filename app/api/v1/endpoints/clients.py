from fastapi import APIRouter, Depends, Header, HTTPException, Query, Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, extract_token, require_roles
from app.core.supabase_rest import supabase_get, supabase_post, supabase_patch

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientCreate(BaseModel):
    id_externo: str = Field(min_length=2, max_length=80)
    nombre: str = Field(min_length=2, max_length=150)
    direccion: Optional[str] = None


class ClientUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=150)
    direccion: Optional[str] = None


class ClientListItem(BaseModel):
    id_externo: str
    nombre: str
    direccion: Optional[str] = None
    creado_en: Optional[str] = None


@router.get("", response_model=list[ClientListItem])
async def list_clients(
    q: Optional[str] = Query(default=None),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    params = {
        "select": "id_externo,nombre,direccion,creado_en",
        "order": "nombre.asc",
    }

    if q:
        q = q.strip()
        if q:
            params["or"] = f"(id_externo.ilike.*{q}*,nombre.ilike.*{q}*,direccion.ilike.*{q}*)"

    resp = await supabase_get("/cliente", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.post("")
async def create_client(
    body: ClientCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR", "ODONTOLOGO"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = body.model_dump(mode="json")
    resp = await supabase_post("/cliente", access_token=token, payload=payload)

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.patch("/{id_externo}")
async def update_client(
    id_externo: str = Path(..., min_length=2, max_length=80),
    body: ClientUpdate = ...,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR", "ODONTOLOGO"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = {
        k: v
        for k, v in body.model_dump(mode="json").items()
        if v is not None
    }

    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    resp = await supabase_patch(
        f"/cliente?id_externo=eq.{id_externo}",
        access_token=token,
        payload=payload,
    )

    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"ok": True}