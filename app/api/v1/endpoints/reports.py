from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict, Literal
from datetime import date, datetime, timezone

from app.api.deps import get_current_user, extract_token
from app.core.supabase_rest import supabase_get

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/consumption")
async def consumption_report(
    desde: date = Query(...),
    hasta: date = Query(...),
    group: Literal["insumo", "procedimiento"] = Query("insumo"),
    only_clinical: bool = Query(True),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    """
    Reporte de consumo basado en movimientos tipo SALIDA.
    - group=insumo: suma por insumo_id
    - group=procedimiento: agrupa por procedimiento_id usando atencion -> procedimiento_id (requiere fetch extra)
    """
    token = extract_token(authorization)

    resp = await supabase_get(
        "/movimiento_inventario",
        access_token=token,
        params={
            "select": "id,insumo_id,tipo,cantidad,atencion_relacionada,creado_en",
            "order": "creado_en.desc",
            "limit": 5000,  # para MVP, suficiente
        },
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    movs = resp.json()

    # filtra solo SALIDAS (case-insensitive)
    movs = [m for m in movs if str(m.get("tipo", "")).lower() == "salida"]

    def to_dt(x: str) -> datetime:
        return datetime.fromisoformat(x.replace("Z", "+00:00")).astimezone(timezone.utc)

    d0 = datetime.combine(desde, datetime.min.time(), tzinfo=timezone.utc)
    d1 = datetime.combine(hasta, datetime.max.time(), tzinfo=timezone.utc)

    movs = [m for m in movs if d0 <= to_dt(m["creado_en"]) <= d1]

    if only_clinical:
        movs = [m for m in movs if m.get("atencion_relacionada")]

    # 2) Agrupar
    if group == "insumo":
        agg: Dict[str, float] = {}
        for m in movs:
            k = m["insumo_id"]
            agg[k] = agg.get(k, 0.0) + float(m["cantidad"])

        # enriquecer con nombre del insumo
        # (MVP: fetch de insumos y map)
        ins = await supabase_get("/insumo", access_token=token, params={"select": "id,nombre,unidad_id"})
        ins_map = {i["id"]: i for i in ins.json()} if ins.status_code == 200 else {}

        return [
            {
                "insumo_id": k,
                "insumo_nombre": ins_map.get(k, {}).get("nombre"),
                "unidad_id": ins_map.get(k, {}).get("unidad_id"),
                "cantidad_total": v,
            }
            for k, v in sorted(agg.items(), key=lambda x: x[1], reverse=True)
        ]

    # group == "procedimiento"
    # Necesitamos mapear atencion_id -> procedimiento_id
    # 1) recolectar atenciones
    at_ids = sorted({m["atencion_relacionada"] for m in movs if m.get("atencion_relacionada")})
    if not at_ids:
        return []

    # Traer atenciones (MVP: trae todas y filtra)
    at = await supabase_get("/atencion", access_token=token, params={"select": "id,procedimiento_id"})
    if at.status_code != 200:
        raise HTTPException(status_code=at.status_code, detail=at.text)
    at_map = {a["id"]: a["procedimiento_id"] for a in at.json()}

    agg2: Dict[str, float] = {}
    for m in movs:
        aid = m.get("atencion_relacionada")
        pid = at_map.get(aid)
        if not pid:
            continue
        agg2[pid] = agg2.get(pid, 0.0) + float(m["cantidad"])

    # enriquecer con nombre procedimiento
    pr = await supabase_get("/procedimiento", access_token=token, params={"select": "id,nombre"})
    pr_map = {p["id"]: p["nombre"] for p in pr.json()} if pr.status_code == 200 else {}

    return [
        {
            "procedimiento_id": k,
            "procedimiento_nombre": pr_map.get(k),
            "cantidad_total": v,
        }
        for k, v in sorted(agg2.items(), key=lambda x: x[1], reverse=True)
    ]