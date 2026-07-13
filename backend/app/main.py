"""ArenaMind AI — FastAPI application entry point.

Lifespan is fully graceful: startup continues even if Postgres, MongoDB, and Qdrant
are all unreachable. Simulator, LLM (mock or live), and RAG (local TF-IDF) always boot.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import init_db, close_db
from app.api.v1.router import api_router
from app.agents.master_agent import get_master_agent
from app.rag.retriever import get_local_index

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Always boot: simulator and local KB index need no external services
    try:
        from app.simulators.stadium_simulator import get_simulator
        get_simulator()  # triggers lazy init
    except Exception as e:
        print(f"[Simulator] warning: {e}")

    try:
        get_local_index()._load()  # pre-load TF-IDF index
    except Exception as e:
        print(f"[RAG] warning: {e}")

    # 2. Boot master agent (loads llm_client → picks Anthropic/OpenAI/Mock)
    try:
        get_master_agent()
    except Exception as e:
        print(f"[MasterAgent] warning: {e}")

    # 3. DB is best-effort (Postgres might not be up yet)
    try:
        await init_db()
    except Exception as e:
        print(f"[DB] deferred: {e}")

    print(f"[ArenaMind] booted in {settings.ENVIRONMENT} mode")
    yield

    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Generative AI Operating System for FIFA World Cup 2026 Stadiums",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "message": "ArenaMind AI — Generative AI Operating System for FIFA World Cup 2026 Stadiums",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }