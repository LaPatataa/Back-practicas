from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import date

from app.api.deps import get_current_user, extract_token
from app.core.supabase_rest import supabase_get

router = APIRouter(prefix="/reports/clinical-detail", tags=["reports"])


class ClinicalDetailRow(BaseModel):
    movimiento_id: str
    atencion_id: str
    paciente_id_externo: Optional[str] = None
    paciente_nombre: Optional[str] = None
    procedimiento_id: Optional[str] = None
    procedimiento_nombre: Optional[str] = None
    realizado_en: Optional[str] = None
    realizado_por: Optional[str] = None
    insumo_id: Optional[str] = None
    insumo_nombre: Optional[str] = None
    lote_id: Optional[str] = None
    lote_codigo: Optional[str] = None
    cantidad: Optional[float] = None
    motivo: Optional[str] = None
    creado_en: Optional[str] = None


@router.get("", response_model=list[ClinicalDetailRow])
async def clinical_consumption_detail(
    desde: date = Query(...),
    hasta: date = Query(...),
    q: Optional[str] = Query(default=None),
    authorization: str = Header(default=""),
    user: Dict[str, Any] = Depends(get_current_user),
):
    token = extract_token(authorization)

    # Movimientos clínicos: solo SALIDA y ligados a atención
    params = {
        "select": ",".join([
            "id",
            "insumo_id",
            "lote_id",
            "cantidad",
            "motivo",
            "creado_en",
            "atencion_relacionada",
            "insumo(nombre)",
            "lote_insumo(codigo)",
            "atencion:atencion_relacionada("
            "id,"
            "id_externo_paciente,"
            "procedimiento_id,"
            "realizado_en,"
            "realizado_por,"
            "cliente(nombre),"
            "procedimiento(nombre)"
            ")",
        ]),
        "tipo": "eq.SALIDA",
        "creado_en": f"gte.{desde.isoformat()}",
        "order": "creado_en.desc",
        "atencion_relacionada": "not.is.null",
    }

    # hasta inclusivo
    params["and"] = f"(creado_en.lte.{hasta.isoformat()}T23:59:59)"

    resp = await supabase_get("/movimiento_inventario", access_token=token, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    rows = resp.json() or []

    result: list[ClinicalDetailRow] = []
    for row in rows:
        atencion = row.get("atencion") or {}
        cliente = atencion.get("cliente") if isinstance(atencion, dict) else None
        procedimiento = atencion.get("procedimiento") if isinstance(atencion, dict) else None
        insumo = row.get("insumo") or {}
        lote = row.get("lote_insumo") or {}

        mapped = {
            "movimiento_id": row.get("id"),
            "atencion_id": atencion.get("id") if isinstance(atencion, dict) else row.get("atencion_relacionada"),
            "paciente_id_externo": atencion.get("id_externo_paciente") if isinstance(atencion, dict) else None,
            "paciente_nombre": cliente.get("nombre") if isinstance(cliente, dict) else None,
            "procedimiento_id": atencion.get("procedimiento_id") if isinstance(atencion, dict) else None,
            "procedimiento_nombre": procedimiento.get("nombre") if isinstance(procedimiento, dict) else None,
            "realizado_en": atencion.get("realizado_en") if isinstance(atencion, dict) else None,
            "realizado_por": atencion.get("realizado_por") if isinstance(atencion, dict) else None,
            "insumo_id": row.get("insumo_id"),
            "insumo_nombre": insumo.get("nombre") if isinstance(insumo, dict) else None,
            "lote_id": row.get("lote_id"),
            "lote_codigo": lote.get("codigo") if isinstance(lote, dict) else None,
            "cantidad": row.get("cantidad"),
            "motivo": row.get("motivo"),
            "creado_en": row.get("creado_en"),
        }

        result.append(mapped)

    if q:
        q = q.strip().lower()
        if q:
            result = [
                item for item in result
                if q in (item["paciente_id_externo"] or "").lower()
                or q in (item["paciente_nombre"] or "").lower()
                or q in (item["procedimiento_nombre"] or "").lower()
                or q in (item["insumo_nombre"] or "").lower()
                or q in (item["lote_codigo"] or "").lower()
                or q in (item["realizado_por"] or "").lower()
            ]

    return result