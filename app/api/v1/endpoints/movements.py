from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict, Optional
from datetime import date

from app.api.deps import get_current_user, extract_token
from app.core.supabase_rest import supabase_get

router = APIRouter(prefix="/movements", tags=["movements"])


@router.get("")
async def list_movements(
    insumo_id: Optional[str] = Query(default=None),
    lote_id: Optional[str] = Query(default=None),
    tipo: Optional[str] = Query(default=None),  # ENTRADA|SALIDA|AJUSTE
    atencion_id: Optional[str] = Query(default=None),
    desde: Optional[date] = Query(default=None),
    hasta: Optional[date] = Query(default=None),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    params = {
        "select": "id,insumo_id,tipo,cantidad,motivo,lote_id,atencion_relacionada,creado_por,creado_en",
        "order": "creado_en.desc",
    }

    if insumo_id:
        params["insumo_id"] = f"eq.{insumo_id}"
    if lote_id:
        params["lote_id"] = f"eq.{lote_id}"
    if tipo:
        params["tipo"] = f"eq.{tipo}"
    if atencion_id:
        params["atencion_relacionada"] = f"eq.{atencion_id}"

    # filtro por fechas (si creado_en es timestamptz)
    if desde:
        params["creado_en"] = f"gte.{desde.isoformat()}T00:00:00Z"
    if hasta:
        # si ya existe creado_en, necesitamos AND. PostgREST lo permite usando &creado_en=gte...&creado_en=lte...
        # supabase_get ya manda params como dict; para soportar duplicadas claves habría que armar query string.
        # MVP: si dan hasta, ignoramos desde o viceversa. Mejor: si ambos, usa rango en backend (simple).
        pass

    resp = await supabase_get("/movimiento_inventario", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()

    # Si hay rango completo, filtramos en backend por simplicidad
    if desde and hasta:
        from datetime import datetime
        def to_dt(x: str) -> datetime:
            return datetime.fromisoformat(x.replace("Z", "+00:00"))
        d0 = datetime.combine(desde, datetime.min.time()).astimezone()
        d1 = datetime.combine(hasta, datetime.max.time()).astimezone()
        data = [m for m in data if d0 <= to_dt(m["creado_en"]) <= d1]

    return data