from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings
from app.models import ConstraintProfile, PantryItem, Recipe, SuggestionRun
from app.schemas.suggest import SuggestRequest, SuggestResponse
from app.services.llm import attach_tips
from app.services.matcher import ConstraintView, Ingredient, PantryLine, RecipeView, rank_recipes

router = APIRouter(tags=["suggest"])


def _recipe_view(row: Recipe) -> RecipeView:
    ingredients = [
        Ingredient(
            name=item.get("name", ""),
            quantity=item.get("quantity"),
            unit=item.get("unit"),
            optional=bool(item.get("optional", False)),
        )
        for item in (row.ingredients or [])
        if item.get("name")
    ]
    return RecipeView(
        id=row.id,
        title=row.title,
        description=row.description or "",
        prep_minutes=row.prep_minutes or 0,
        cook_minutes=row.cook_minutes or 0,
        servings=row.servings or 2,
        diet_tags=list(row.diet_tags or []),
        ingredients=ingredients,
        instructions=list(row.instructions or []),
    )


def _pantry_line(row: PantryItem) -> PantryLine:
    return PantryLine(name=row.name, quantity=row.quantity, unit=row.unit, expires_on=row.expires_on)


def _constraints(profile: ConstraintProfile | None) -> ConstraintView:
    if profile is None:
        return ConstraintView(diet_tags=[], max_cook_minutes=45, servings=2, exclude_ingredients=[])
    return ConstraintView(
        diet_tags=list(profile.diet_tags or []),
        max_cook_minutes=profile.max_cook_minutes,
        servings=profile.servings or 2,
        exclude_ingredients=list(profile.exclude_ingredients or []),
    )


@router.post("/suggest", response_model=SuggestResponse)
async def suggest(payload: SuggestRequest, db: Session = Depends(get_db)) -> SuggestResponse:
    settings = get_settings()
    recipes = [_recipe_view(row) for row in db.query(Recipe).all()]
    pantry_rows = db.query(PantryItem).all()
    pantry = [_pantry_line(row) for row in pantry_rows]
    profile = db.get(ConstraintProfile, 1)
    suggestions = rank_recipes(recipes, pantry, _constraints(profile), limit=payload.limit)
    await attach_tips(suggestions, settings)

    response = SuggestResponse(
        suggestions=suggestions,
        llm_configured=settings.llm_configured,
        pantry_count=len(pantry_rows),
        recipe_count=len(recipes),
    )
    db.add(
        SuggestionRun(
            suggestion_count=len(response.suggestions),
            payload=response.model_dump(mode="json"),
        )
    )
    db.commit()
    return response
