from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.pantry import utcnow


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    instructions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    prep_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cook_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    servings: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    diet_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ingredients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
