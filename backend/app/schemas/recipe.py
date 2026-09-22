from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import clean_str_list


class IngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=32)
    optional: bool = False

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not value:
            raise ValueError("name is required")
        return value

    @field_validator("unit")
    @classmethod
    def strip_unit(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        return value or None


class RecipeIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = ""
    instructions: list[str] = Field(default_factory=list)
    prep_minutes: int = Field(default=0, ge=0, le=600)
    cook_minutes: int = Field(default=0, ge=0, le=600)
    servings: int = Field(default=2, ge=1, le=24)
    diet_tags: list[str] = Field(default_factory=list)
    ingredients: list[IngredientIn] = Field(min_length=1)

    @field_validator("title", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("instructions")
    @classmethod
    def clean_steps(cls, value: list[str]) -> list[str]:
        return [step.strip() for step in value if step and step.strip()]

    @field_validator("diet_tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        return clean_str_list(value)


class RecipeOut(RecipeIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
