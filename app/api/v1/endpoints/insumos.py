from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict, Optional

from app.api.deps import get_current_user, extract_token, require_roles
from app.core.supabase_rest import supabase_get, supabase_post, supabase_patch

from app.schemas.insumos import UnidadCreate, InsumoCreate, InsumoUpdate

router = APIRouter(prefix="/catalog", tags=["catalog"])

@router.get("/units")
async def list_units(
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    resp = await supabase_get(
        "/unidad_medida",
        access_token=token,
        params={"select": "id,nombre,simbolo,creado_en", "order": "nombre.asc"},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.post("/units")
async def create_unit(
    body: UnidadCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    resp = await supabase_post(
        "/unidad_medida",
        access_token=token,
        payload=body.model_dump(),
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

# -------- Insumos --------

@router.get("/supplies")
async def list_supplies(
    q: Optional[str] = Query(default=None),
    only_active: bool = Query(default=True),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    params = {
        "select": "id,nombre,categoria,unidad_id,stock_minimo,stock_actual,activo,creado_en",
        "order": "nombre.asc",
    }
    if only_active:
        params["activo"] = "eq.true"

    # Filtro simple por nombre (ilike)
    if q:
        params["nombre"] = f"ilike.*{q}*"

    resp = await supabase_get("/insumo", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.post("/supplies")
async def create_supply(
    body: InsumoCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = body.model_dump(mode="json")
    resp = await supabase_post("/insumo", access_token=token, payload=payload)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.patch("/supplies/{insumo_id}")
async def update_supply(
    insumo_id: str,
    body: InsumoUpdate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}

    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    resp = await supabase_patch(
        f"/insumo?id=eq.{insumo_id}",
        access_token=token,
        payload=payload,
    )
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"ok": True}