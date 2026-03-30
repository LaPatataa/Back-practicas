from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import lots
from app.api.v1.endpoints import insumos
from app.api.v1.endpoints import visits
from app.api.v1.endpoints import clients
from app.api.v1.endpoints import procedures
from app.api.v1.endpoints import alerts, movements, reports, reports_clinical

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(lots.router)
api_router.include_router(visits.router)
api_router.include_router(insumos.router)
api_router.include_router(procedures.router)
api_router.include_router(alerts.router)
api_router.include_router(movements.router)
api_router.include_router(reports.router)
api_router.include_router(reports_clinical.router)
api_router.include_router(clients.router)


