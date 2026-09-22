from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import constraints, health, pantry, recipes, suggest
from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import Base
from app.services.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="PantryCook", version="0.1.0", lifespan=lifespan)
    origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
    allow_all = origins == ["*"] or not origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(pantry.router)
    app.include_router(recipes.router)
    app.include_router(constraints.router)
    app.include_router(suggest.router)
    return app


app = create_app()
