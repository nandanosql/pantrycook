from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PantryItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=32)
    expires_on: date | None = None

    @field_validator("name", "unit")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not value:
            raise ValueError("must not be blank")
        return value


class PantryItemOut(PantryItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
