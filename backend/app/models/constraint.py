from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.pantry import utcnow


class ConstraintProfile(Base):
    """Single household profile. v0.1 keeps one row (id=1)."""

    __tablename__ = "constraint_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diet_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    max_cook_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    exclude_ingredients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
