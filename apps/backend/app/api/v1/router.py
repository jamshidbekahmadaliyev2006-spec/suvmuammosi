from fastapi import APIRouter

from app.api.v1 import auth, bot, dashboard, detection_rules, incidents, sources, system

api_router = APIRouter(prefix="/api/v1")
for module in (auth, dashboard, system, incidents, detection_rules, sources, bot):
    api_router.include_router(module.router)
