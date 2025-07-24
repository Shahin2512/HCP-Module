from fastapi import APIRouter

from app.api.v1.endpoints import hcps, interactions

api_router = APIRouter()
api_router.include_router(hcps.router, prefix="/hcps", tags=["hcps"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])