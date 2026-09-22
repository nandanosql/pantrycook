from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import clean_str_list


class ConstraintIn(BaseModel):
    diet_tags: list[str] = Field(default_factory=list)
    max_cook_minutes: int | None = Field(default=None, ge=1, le=300)
    servings: int = Field(default=2, ge=1, le=12)
    exclude_ingredients: list[str] = Field(default_factory=list)

    @field_validator("diet_tags", "exclude_ingredients")
    @classmethod
    def clean_lists(cls, value: list[str]) -> list[str]:
        return clean_str_list(value)


class ConstraintOut(ConstraintIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime
