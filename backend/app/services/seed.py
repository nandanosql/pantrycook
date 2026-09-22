"""Load the bundled recipe library and the optional sample pantry."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ConstraintProfile, PantryItem, Recipe


def _pantry_key(name: str) -> str:
    """Identity for deduping stored items. Synonyms stay distinct (tomato vs canned tomatoes)."""
    return " ".join(name.strip().lower().split())

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_json(name: str) -> list:
    path = DATA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def seed_if_empty(db: Session) -> None:
    if db.query(Recipe).count() == 0:
        for item in _read_json("seed_recipes.json"):
            db.add(
                Recipe(
                    title=item["title"].strip(),
                    description=(item.get("description") or "").strip(),
                    instructions=item.get("instructions") or [],
                    prep_minutes=int(item.get("prep_minutes") or 0),
                    cook_minutes=int(item.get("cook_minutes") or 0),
                    servings=int(item.get("servings") or 2),
                    diet_tags=[tag.strip().lower() for tag in item.get("diet_tags") or []],
                    ingredients=item.get("ingredients") or [],
                )
            )
        db.commit()

    if db.get(ConstraintProfile, 1) is None:
        db.add(
            ConstraintProfile(
                id=1,
                diet_tags=[],
                max_cook_minutes=45,
                servings=2,
                exclude_ingredients=[],
            )
        )
        db.commit()


def load_sample_pantry(db: Session, today: date | None = None) -> list[PantryItem]:
    """Add demo pantry items that are not already present. Expiry is relative to today."""
    today = today or date.today()
    existing = {_pantry_key(item.name): item for item in db.query(PantryItem).all()}
    for item in _read_json("sample_pantry.json"):
        key = _pantry_key(item["name"])
        if key in existing:
            continue
        days = item.get("expires_in_days")
        expires = None if days is None else today + timedelta(days=int(days))
        row = PantryItem(
            name=item["name"].strip(),
            quantity=float(item["quantity"]),
            unit=item["unit"].strip(),
            expires_on=expires,
        )
        db.add(row)
        existing[key] = row
    db.commit()
    return db.query(PantryItem).all()
