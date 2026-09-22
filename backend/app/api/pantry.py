from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import PantryItem
from app.models.pantry import utcnow
from app.schemas.pantry import PantryItemIn, PantryItemOut
from app.services.seed import load_sample_pantry

router = APIRouter(prefix="/pantry", tags=["pantry"])


def _sort_items(items: list[PantryItem]) -> list[PantryItem]:
    return sorted(items, key=lambda item: (item.expires_on is None, item.expires_on or date.max, item.name.lower()))


def _get_item(db: Session, item_id: int) -> PantryItem:
    item = db.get(PantryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return item


@router.get("", response_model=list[PantryItemOut])
def list_pantry(db: Session = Depends(get_db)) -> list[PantryItem]:
    return _sort_items(db.query(PantryItem).all())


@router.post("/sample", response_model=list[PantryItemOut])
def sample_pantry(db: Session = Depends(get_db)) -> list[PantryItem]:
    return _sort_items(load_sample_pantry(db))


@router.post("", response_model=PantryItemOut, status_code=201)
def create_pantry_item(payload: PantryItemIn, db: Session = Depends(get_db)) -> PantryItem:
    item = PantryItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=PantryItemOut)
def get_pantry_item(item_id: int, db: Session = Depends(get_db)) -> PantryItem:
    return _get_item(db, item_id)


@router.put("/{item_id}", response_model=PantryItemOut)
def update_pantry_item(item_id: int, payload: PantryItemIn, db: Session = Depends(get_db)) -> PantryItem:
    item = _get_item(db, item_id)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.updated_at = utcnow()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_pantry_item(item_id: int, db: Session = Depends(get_db)) -> None:
    item = _get_item(db, item_id)
    db.delete(item)
    db.commit()
