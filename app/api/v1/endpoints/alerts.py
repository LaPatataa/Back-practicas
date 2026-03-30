from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict
from datetime import date, timedelta

from app.api.deps import get_current_user, extract_token
from app.core.supabase_rest import supabase_get

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/stock-min")
async def stock_min_alerts(
    only_active: bool = Query(True),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Insumos con stock_actual <= stock_minimo
    """
    token = extract_token(authorization)

    params = {
        "select": "id,nombre,categoria,unidad_id,stock_minimo,stock_actual,activo",
        "order": "nombre.asc",
    }
    if only_active:
        params["activo"] = "eq.true"

    resp = await supabase_get("/insumo", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    items = resp.json()
    low = [i for i in items if float(i["stock_actual"]) <= float(i["stock_minimo"])]

    return low


@router.get("/expiry")
async def expiry_alerts(
    days: int = Query(30, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Lotes que vencen en <= days y con cantidad_actual > 0
    (Versión "bonita" con join para traer nombre del insumo)
    """
    token = extract_token(authorization)
    limit_date = date.today() + timedelta(days=days)

    params = {
        "select": "id,insumo_id,codigo,vence_en,cantidad_actual,insumo(nombre,unidad_id)",
        "vence_en": f"lte.{limit_date.isoformat()}",
        "cantidad_actual": "gt.0",
        "order": "vence_en.asc",
    }

    resp = await supabase_get("/lote_insumo", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()