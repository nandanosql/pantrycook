from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import ConstraintProfile
from app.models.pantry import utcnow
from app.schemas.constraint import ConstraintIn, ConstraintOut

router = APIRouter(prefix="/constraints", tags=["constraints"])


def get_or_create_profile(db: Session) -> ConstraintProfile:
    profile = db.get(ConstraintProfile, 1)
    if profile is None:
        profile = ConstraintProfile(
            id=1,
            diet_tags=[],
            max_cook_minutes=45,
            servings=2,
            exclude_ingredients=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ConstraintOut)
def read_constraints(db: Session = Depends(get_db)) -> ConstraintProfile:
    return get_or_create_profile(db)


@router.put("", response_model=ConstraintOut)
def update_constraints(payload: ConstraintIn, db: Session = Depends(get_db)) -> ConstraintProfile:
    profile = get_or_create_profile(db)
    data = payload.model_dump()
    profile.diet_tags = data["diet_tags"]
    profile.max_cook_minutes = data["max_cook_minutes"]
    profile.servings = data["servings"]
    profile.exclude_ingredients = data["exclude_ingredients"]
    profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)
    return profile
