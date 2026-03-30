from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from typing import Optional

class UnidadCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    simbolo: str = Field(min_length=1, max_length=10)

class InsumoCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    categoria: Optional[str] = None  # si es enum en DB, usamos string con valores válidos
    unidad_id: UUID
    stock_minimo: Decimal = Field(ge=0)
    activo: bool = True

class InsumoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=120)
    categoria: Optional[str] = None
    unidad_id: Optional[UUID] = None
    stock_minimo: Optional[Decimal] = Field(default=None, ge=0)
    activo: Optional[bool] = None