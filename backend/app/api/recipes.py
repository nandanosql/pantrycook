from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Recipe
from app.models.pantry import utcnow
from app.schemas.recipe import RecipeIn, RecipeOut

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _get_recipe(db: Session, recipe_id: int) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


def _apply(recipe: Recipe, payload: RecipeIn) -> None:
    data = payload.model_dump()
    recipe.title = data["title"]
    recipe.description = data["description"]
    recipe.instructions = data["instructions"]
    recipe.prep_minutes = data["prep_minutes"]
    recipe.cook_minutes = data["cook_minutes"]
    recipe.servings = data["servings"]
    recipe.diet_tags = data["diet_tags"]
    recipe.ingredients = data["ingredients"]


@router.get("", response_model=list[RecipeOut])
def list_recipes(q: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[Recipe]:
    query = db.query(Recipe)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(Recipe.title.ilike(term) | Recipe.description.ilike(term))
    return query.order_by(Recipe.title.asc()).all()


@router.post("", response_model=RecipeOut, status_code=201)
def create_recipe(payload: RecipeIn, db: Session = Depends(get_db)) -> Recipe:
    recipe = Recipe()
    _apply(recipe, payload)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)) -> Recipe:
    return _get_recipe(db, recipe_id)


@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: int, payload: RecipeIn, db: Session = Depends(get_db)) -> Recipe:
    recipe = _get_recipe(db, recipe_id)
    _apply(recipe, payload)
    recipe.updated_at = utcnow()
    db.commit()
    db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)) -> None:
    recipe = _get_recipe(db, recipe_id)
    db.delete(recipe)
    db.commit()
