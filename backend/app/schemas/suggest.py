from pydantic import BaseModel, Field


class SuggestRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=20)


class IngredientMatch(BaseModel):
    name: str
    coverage: float
    near_expiry: bool = False
    optional: bool = False
    assumed: bool = False
    detail: str = ""


class MissingIngredient(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
    partial: bool = False


class ShoppingLine(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
    note: str = "missing"


class SuggestionOut(BaseModel):
    recipe_id: int | None = None
    title: str
    description: str = ""
    score: float
    coverage: float
    prep_minutes: int = 0
    cook_minutes: int = 0
    servings: int = 2
    scaled_servings: int = 2
    diet_tags: list[str] = Field(default_factory=list)
    matched_ingredients: list[IngredientMatch]
    missing_ingredients: list[MissingIngredient]
    shopping_delta: list[ShoppingLine]
    why: str
    use_soon: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    llm_tip: str | None = None


class SuggestResponse(BaseModel):
    suggestions: list[SuggestionOut]
    llm_configured: bool
    pantry_count: int
    recipe_count: int
