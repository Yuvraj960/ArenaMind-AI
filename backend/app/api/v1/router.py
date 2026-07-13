from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    chat,
    crowd,
    emergency,
    health,
    knowledge,
    navigation,
    operations,
    stadium,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(navigation.router, prefix="/navigation", tags=["navigation"])
api_router.include_router(crowd.router, prefix="/crowd", tags=["crowd"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(stadium.router, prefix="/stadium", tags=["stadium"])