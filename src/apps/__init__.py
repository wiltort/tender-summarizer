from fastapi import APIRouter
from src.apps.tender.routes import tender_router


apps_router = APIRouter(prefix="/api/v1")

apps_router.include_router(tender_router)
