from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.api.deps import get_current_user, extract_token, require_roles
from app.core.supabase_rest import supabase_get, supabase_post, supabase_post_rpc
from app.schemas.visits import VisitCreate, ConsumeRequest

router = APIRouter(prefix="/visits", tags=["visits"])


class VisitListItem(BaseModel):
    id: UUID
    id_externo_paciente: Optional[str] = None
    procedimiento_id: UUID
    procedimiento_nombre: Optional[str] = None
    realizado_en: Optional[datetime] = None
    notas: Optional[str] = None


@router.get("", response_model=list[VisitListItem])
async def list_visits(
    q: Optional[str] = Query(default=None),
    only_recent: bool = Query(default=False),
    user: Dict[str, Any] = Depends(get_current_user),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    params = {
        "select": "id,id_externo_paciente,procedimiento_id,realizado_en,notas,procedimiento(nombre)",
        "order": "realizado_en.desc",
    }

    if q:
        q = q.strip()
        if q:
            params["or"] = f"(id_externo_paciente.ilike.*{q}*,notas.ilike.*{q}*)"

    if only_recent:
        params["limit"] = "50"

    resp = await supabase_get("/atencion", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    rows = resp.json() or []

    result = []
    for row in rows:
        procedimiento = row.get("procedimiento")
        result.append({
            "id": row["id"],
            "id_externo_paciente": row.get("id_externo_paciente"),
            "procedimiento_id": row["procedimiento_id"],
            "procedimiento_nombre": procedimiento.get("nombre") if isinstance(procedimiento, dict) else None,
            "realizado_en": row.get("realizado_en"),
            "notas": row.get("notas"),
        })

    return result


@router.post("")
async def create_visit(
    body: VisitCreate,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR", "ODONTOLOGO"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    payload = body.model_dump(mode="json")
    payload["realizado_por"] = user["id"]
    payload["realizado_en"] = payload.get("realizado_en") or datetime.utcnow().isoformat()

    resp = await supabase_post("/atencion", access_token=token, payload=payload)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.post("/{atencion_id}/consume")
async def consume_visit(
    atencion_id: UUID,
    body: ConsumeRequest,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR", "ODONTOLOGO"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    results = []
    for item in body.items:
        consumo_payload = {
            "atencion_id": str(atencion_id),
            "insumo_id": str(item.insumo_id),
            "cantidad": float(item.cantidad),
        }
        c = await supabase_post("/consumo_atencion", access_token=token, payload=consumo_payload)

        if c.status_code not in (200, 201):
            if '"code":"23505"' not in c.text:
                raise HTTPException(status_code=400, detail=f"consumo_atencion error: {c.text}")

        rpc_payload = {
            "p_insumo_id": str(item.insumo_id),
            "p_lote_id": str(item.lote_id),
            "p_tipo": "SALIDA",
            "p_cantidad": float(item.cantidad),
            "p_motivo": body.motivo,
            "p_atencion_relacionada": str(atencion_id),
        }
        m = await supabase_post_rpc("inv_salida", payload=rpc_payload, access_token=token)
        if m.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail=f"inv_salida error: {m.text}")

        results.append({
            "consumo": c.json() if c.status_code in (200, 201) else {"ok": True},
            "movimiento": m.json()
        })

    return {"ok": True, "items": results}


@router.post("/{atencion_id}/consume-defaults")
async def consume_defaults(
    atencion_id: UUID,
    body: ConsumeRequest,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR", "ODONTOLOGO"])),
    authorization: str = Header(default=""),
):
    """
    Versión simple: el front manda items ya armados (insumo_id, lote_id, cantidad)
    usando como base procedimiento_insumo_default.
    """
    return await consume_visit(atencion_id, body, user, authorization)


@router.get("/{atencion_id}")
async def get_visit(
    atencion_id: UUID,
    user: Dict[str, Any] = Depends(require_roles(["ADMIN", "AUXILIAR", "ODONTOLOGO"])),
    authorization: str = Header(default=""),
):
    token = extract_token(authorization)

    a = await supabase_get(
        f"/atencion?id=eq.{atencion_id}",
        access_token=token,
        params={"select": "*"},
    )
    if a.status_code != 200:
        raise HTTPException(status_code=a.status_code, detail=a.text)

    atenciones = a.json()
    if not atenciones:
        raise HTTPException(status_code=404, detail="Atencion not found")

    c = await supabase_get(
        f"/consumo_atencion?atencion_id=eq.{atencion_id}",
        access_token=token,
        params={"select": "*"},
    )

    m = await supabase_get(
        f"/movimiento_inventario?atencion_relacionada=eq.{atencion_id}",
        access_token=token,
        params={"select": "*", "order": "creado_en.desc"},
    )

    return {
        "atencion": atenciones[0],
        "consumos": c.json() if c.status_code == 200 else [],
        "movimientos": m.json() if m.status_code == 200 else [],
    }