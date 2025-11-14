from fastapi import APIRouter

from app.api.routes import items, login, orders, private, users, utils  # measurements, websocket
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(orders.router, tags=["orders"])
# Measurement control routes temporarily disabled for basic FastAPI template testing
# api_router.include_router(
#     measurements.router, prefix="/measurements", tags=["measurements"]
# )
# api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
