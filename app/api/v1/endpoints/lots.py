from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.api.deps import get_current_user
from app.core.supabase_rest import supabase_get, supabase_post_rpc

from app.schemas.lots import EntryCreate, ExitCreate

router = APIRouter(prefix="/inventory", tags=["inventory"])

def extract_token(authorization: str) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return authorization.split(" ", 1)[1].strip()

@router.get("/lots")
async def list_lots(
    insumo_id: UUID = Query(...),
    only_available: bool = Query(True),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Lista lotes de un insumo (útil para seleccionar de cuál consumir).
    """
    token = extract_token(authorization)

    # filtros PostgREST
    params = {
        "select": "id,insumo_id,codigo,vence_en,cantidad_actual,creado_en",
        "insumo_id": f"eq.{insumo_id}",
        "order": "vence_en.asc",
    }
    if only_available:
        params["cantidad_actual"] = "gt.0"

    resp = await supabase_get("/lote_insumo", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()

@router.post("/entries")
async def create_entry(
    body: EntryCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Entrada: crea/suma a un lote + crea movimiento tipo 'entrada' + actualiza stock_actual.
    """
    token = extract_token(authorization)

    payload = {
        "p_insumo_id": str(body.insumo_id),
        "p_codigo_lote": body.codigo_lote,
        "p_vence_en": body.vence_en.isoformat(),
        "p_cantidad": float(body.cantidad),
        "p_motivo": body.motivo,
    }

    resp = await supabase_post_rpc("inv_entrada", payload=payload, access_token=token)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail=resp.text)

    return resp.json()

@router.post("/exits")
async def create_exit(
    body: ExitCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Salida: descuenta del lote + crea movimiento (salida/merma/baja/ajuste) + actualiza stock_actual.
    """
    token = extract_token(authorization)

    payload = {
        "p_insumo_id": str(body.insumo_id),
        "p_lote_id": str(body.lote_id),
        "p_tipo": body.tipo,
        "p_cantidad": float(body.cantidad),
        "p_motivo": body.motivo,
        "p_atencion_relacionada": str(body.atencion_relacionada) if body.atencion_relacionada else None,
    }

    resp = await supabase_post_rpc("inv_salida", payload=payload, access_token=token)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail=resp.text)

    return resp.json()

@router.get("/alerts/expiry")
async def expiry_alerts(
    days: int = Query(30, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Alerta simple: lotes que vencen en <= days y aún tienen cantidad.
    """
    token = extract_token(authorization)

    # PostgREST no soporta "current_date + interval" directo en filtro.
    # Así que calculamos la fecha límite en Python y filtramos por <=
    from datetime import date, timedelta
    limit_date = date.today() + timedelta(days=days)

    params = {
        "select": "id,insumo_id,codigo,vence_en,cantidad_actual",
        "vence_en": f"lte.{limit_date.isoformat()}",
        "cantidad_actual": "gt.0",
        "order": "vence_en.asc",
    }

    resp = await supabase_get("/lote_insumo", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()