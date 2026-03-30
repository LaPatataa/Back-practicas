from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from datetime import date
from typing import Optional

class EntryCreate(BaseModel):
    insumo_id: UUID
    codigo_lote: str = Field(min_length=1, max_length=80)
    vence_en: date
    cantidad: Decimal = Field(gt=0)
    motivo: Optional[str] = None

class ExitCreate(BaseModel):
    insumo_id: UUID
    lote_id: UUID
    tipo: str  
    cantidad: Decimal = Field(gt=0)
    motivo: Optional[str] = None
    atencion_relacionada: Optional[UUID] = None