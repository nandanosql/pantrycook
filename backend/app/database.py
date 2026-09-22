from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


def ensure_sqlite_parent(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    # sqlite:////data/app.db -> /data/app.db ; sqlite:///./app.db -> ./app.db
    raw = url.split("sqlite:///", 1)[-1]
    if not raw or raw == ":memory:":
        return
    Path(raw).parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
ensure_sqlite_parent(settings.database_url)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
