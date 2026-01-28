"""FastAPI application entry point for Manganize Web App"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from manganize_web.api import character, generation, history
from manganize_web.config import settings
from manganize_web.models.database import create_engine, create_session_maker, init_db
from manganize_web.templates import templates

# Rate limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """
    Application lifespan manager.

    Initializes database on startup and cleans up on shutdown.
    """
    # Startup: Create engine and store in app.state
    engine = create_engine()
    app.state.engine = engine
    app.state.session_maker = create_session_maker(engine)

    await init_db(engine)
    yield
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API routers
app.include_router(generation.router, prefix="/api", tags=["generation"])
app.include_router(character.router, prefix="/api", tags=["character"])
app.include_router(history.router, prefix="/api", tags=["history"])


# Root route
@app.get("/")
async def index(request: Request):
    """Main page - manga generation interface"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Manganize - マンガ画像生成"},
    )


# Character management page
@app.get("/character")
async def character_page(request: Request):
    """Character management page"""
    return templates.TemplateResponse(
        "character.html",
        {"request": request, "title": "キャラクター管理 - Manganize"},
    )


# History page
@app.get("/history")
async def history_page(request: Request):
    """Generation history page"""
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "title": "生成履歴 - Manganize"},
    )


# Health check endpoint
@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}
