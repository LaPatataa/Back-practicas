from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class VisitCreate(BaseModel):
    id_externo_paciente: Optional[str] = None
    procedimiento_id: UUID
    realizado_en: Optional[datetime] = None
    notas: Optional[str] = None

class ConsumeItem(BaseModel):
    insumo_id: UUID
    lote_id: UUID
    cantidad: Decimal = Field(gt=0)

class ConsumeRequest(BaseModel):
    items: List[ConsumeItem]
    motivo: Optional[str] = "Consumo por atención"