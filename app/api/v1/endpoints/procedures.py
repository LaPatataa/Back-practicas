from fastapi import APIRouter, Depends, Header, HTTPException, Query, Path
from typing import Any, Dict
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional

from app.api.deps import get_current_user, extract_token, require_roles
from app.core.supabase_rest import supabase_get, supabase_post, supabase_patch

router = APIRouter(prefix="/procedures", tags=["procedures"])


# ---------- Schemas inline (para hacerlo rápido) ----------
class ProcedureCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: Optional[str] = None
    activo: bool = True

class ProcedureUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=120)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class DefaultItemCreate(BaseModel):
    insumo_id: UUID
    cantidad_default: Decimal = Field(gt=0)


# ---------- Procedures ----------
@router.get("")
async def list_procedures(
    q: Optional[str] = Query(default=None),
    only_active: bool = Query(default=True),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    params = {"select": "id,nombre,descripcion,activo,creado_en", "order": "nombre.asc"}
    if only_active:
        params["activo"] = "eq.true"
    if q:
        params["nombre"] = f"ilike.*{q}*"

    resp = await supabase_get("/procedimiento", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.post("")
async def create_procedure(
    body: ProcedureCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = body.model_dump(mode="json")
    resp = await supabase_post("/procedimiento", access_token=token, payload=payload)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.patch("/{procedimiento_id}")
async def update_procedure(
    procedimiento_id: UUID,
    body: ProcedureUpdate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    resp = await supabase_patch(
        f"/procedimiento?id=eq.{procedimiento_id}",
        access_token=token,
        payload=payload,
    )
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"ok": True}


# ---------- Defaults: procedimiento_insumo_default ----------
@router.get("/{procedimiento_id}/defaults")
async def list_defaults(
    procedimiento_id: UUID,
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    resp = await supabase_get(
        f"/procedimiento_insumo_default?procedimiento_id=eq.{procedimiento_id}",
        access_token=token,
        params={"select": "procedimiento_id,insumo_id,cantidad_default,insumo(nombre,unidad_id)"},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.post("/{procedimiento_id}/defaults")
async def add_default_item(
    procedimiento_id: UUID,
    body: DefaultItemCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = {
        "procedimiento_id": str(procedimiento_id),
        "insumo_id": str(body.insumo_id),
        "cantidad_default": float(body.cantidad_default),
    }

    resp = await supabase_post("/procedimiento_insumo_default", access_token=token, payload=payload)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

class DefaultItemUpdate(BaseModel):
    cantidad_default: Decimal = Field(gt=0)

@router.patch("/{procedimiento_id}/defaults/{insumo_id}")
async def update_default_item(
    procedimiento_id: UUID = Path(...),
    insumo_id: UUID = Path(...),
    body: DefaultItemUpdate = ...,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = {"cantidad_default": float(body.cantidad_default)}

    # PK compuesta: procedimiento_id + insumo_id
    resp = await supabase_patch(
        f"/procedimiento_insumo_default?procedimiento_id=eq.{procedimiento_id}&insumo_id=eq.{insumo_id}",
        access_token=token,
        payload=payload,
    )
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"ok": True}