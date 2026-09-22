"""Rank recipes against a pantry and a constraint profile.

The score is pantry coverage (0–1) plus a small boost for matched ingredients
that expire soon. Coverage is quantity-aware when units can be converted.
The engine does not call the network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

# Each near-expiry ingredient used by a recipe adds this much, up to the cap.
# The boost is small so a clearly better pantry match still wins.
EXPIRY_BONUS_EACH = 0.05
EXPIRY_BONUS_CAP = 0.15
NEAR_EXPIRY_DAYS = 3
# Name matched, but amounts could not be compared.
NAME_ONLY_CREDIT = 0.7

_PATTERN_RANK = {"pescatarian": 1, "vegetarian": 2, "vegan": 3}
_PATTERNS = set(_PATTERN_RANK)

_STOPWORDS = {
    "fresh",
    "dried",
    "ground",
    "large",
    "small",
    "medium",
    "raw",
    "boneless",
    "skinless",
    "extra",
    "virgin",
    "chopped",
    "minced",
    "sliced",
}

_ALIASES = {
    "scallion": "green onion",
    "spring onion": "green onion",
    "coriander": "cilantro",
    "cilantro leaf": "cilantro",
    "garbanzo": "chickpea",
    "garbanzo bean": "chickpea",
    "chick pea": "chickpea",
    "capsicum": "bell pepper",
    "prawn": "shrimp",
    "soya sauce": "soy sauce",
    "greek yogurt": "yogurt",
    "plain yogurt": "yogurt",
    "natural yogurt": "yogurt",
    "spaghetti": "pasta",
    "penne": "pasta",
    "linguine": "pasta",
    "fettuccine": "pasta",
    "chicken breast": "chicken",
    "chicken thigh": "chicken",
    "ground beef": "beef",
    "minced beef": "beef",
    "canned tomato": "tomato",
    "chopped tomato": "tomato",
    "roma tomato": "tomato",
    "cherry tomato": "tomato",
    "yellow onion": "onion",
    "brown onion": "onion",
    "white onion": "onion",
    "red bell pepper": "bell pepper",
    "green bell pepper": "bell pepper",
    "vegetable stock": "stock",
    "veg stock": "stock",
}

_MASS = {"g": 1.0, "kg": 1000.0}
_VOLUME = {"ml": 1.0, "l": 1000.0, "cup": 240.0, "tbsp": 15.0, "tsp": 5.0}
_UNIT_ALIASES = {
    "gram": "g",
    "grams": "g",
    "kilogram": "kg",
    "kilograms": "kg",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "pcs": "piece",
    "pc": "piece",
    "pieces": "piece",
    "cloves": "clove",
    "cans": "can",
    "bunches": "bunch",
    "slices": "slice",
    "heads": "head",
}


@dataclass
class Ingredient:
    name: str
    quantity: float | None = None
    unit: str | None = None
    optional: bool = False


@dataclass
class PantryLine:
    name: str
    quantity: float | None = None
    unit: str | None = None
    expires_on: date | None = None


@dataclass
class ConstraintView:
    diet_tags: list[str] = field(default_factory=list)
    max_cook_minutes: int | None = None
    servings: int = 2
    exclude_ingredients: list[str] = field(default_factory=list)


@dataclass
class RecipeView:
    id: int | None
    title: str
    description: str = ""
    prep_minutes: int = 0
    cook_minutes: int = 0
    servings: int = 2
    diet_tags: list[str] = field(default_factory=list)
    ingredients: list[Ingredient] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)


def singularize(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("oes"):
        return token[:-2]
    if token.endswith(("shes", "ches", "xes")) and len(token) > 4:
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def normalize_name(name: str) -> str:
    text = name.lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    tokens = [singularize(token) for token in text.split() if token and token not in _STOPWORDS]
    normalized = " ".join(tokens)
    return _ALIASES.get(normalized, normalized)


def names_match(left: str, right: str) -> bool:
    a = normalize_name(left)
    b = normalize_name(right)
    if not a or not b:
        return False
    if a == b:
        return True
    a_tokens = a.split()
    b_tokens = b.split()
    if a_tokens[-1] == b_tokens[-1] and (set(a_tokens) <= set(b_tokens) or set(b_tokens) <= set(a_tokens)):
        return True
    return False


def is_excluded(ingredient_name: str, exclusions: list[str]) -> bool:
    ingredient = normalize_name(ingredient_name)
    if not ingredient:
        return False
    tokens = set(ingredient.split())
    for raw in exclusions:
        excluded = normalize_name(raw)
        if not excluded:
            continue
        if names_match(ingredient_name, raw):
            return True
        # "peanut" should skip "peanut butter" even though the last word differs.
        if len(excluded) >= 4 and (excluded in tokens or excluded in ingredient.split()):
            return True
        if len(excluded) >= 4 and f" {excluded} " in f" {ingredient} ":
            return True
    return False


def diet_allows(recipe_tags: list[str], required_tags: list[str]) -> bool:
    """Pattern tags are ordered (vegan > vegetarian > pescatarian).

    Vegan meals also satisfy vegetarian, pescatarian, and dairy-free.
    Vegetarian meals also satisfy pescatarian. Gluten-free is never implied.
    """
    have = {tag.strip().lower() for tag in recipe_tags if tag and tag.strip()}
    required = {tag.strip().lower() for tag in required_tags if tag and tag.strip()}
    if "vegan" in have:
        have.update({"vegetarian", "pescatarian", "dairy-free"})
    if "vegetarian" in have:
        have.add("pescatarian")

    patterns = required & _PATTERNS
    if patterns:
        strictest = max(patterns, key=lambda tag: _PATTERN_RANK[tag])
        recipe_rank = max((_PATTERN_RANK[tag] for tag in have if tag in _PATTERN_RANK), default=0)
        if recipe_rank < _PATTERN_RANK[strictest]:
            return False
    for attribute in required - _PATTERNS:
        if attribute not in have:
            return False
    return True


def norm_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    cleaned = unit.strip().lower()
    if not cleaned:
        return None
    return _UNIT_ALIASES.get(cleaned, cleaned)


def quantity_in_unit(quantity: float | None, from_unit: str | None, to_unit: str | None) -> float | None:
    if quantity is None:
        return None
    src = norm_unit(from_unit)
    dst = norm_unit(to_unit)
    if src is None or dst is None:
        return None
    if src == dst:
        return float(quantity)
    if src in _MASS and dst in _MASS:
        return float(quantity) * _MASS[src] / _MASS[dst]
    if src in _VOLUME and dst in _VOLUME:
        return float(quantity) * _VOLUME[src] / _VOLUME[dst]
    return None


def _round(value: float, places: int = 3) -> float:
    return round(float(value), places)


def is_near_expiry(expires_on: date | None, today: date) -> bool:
    if expires_on is None:
        return False
    delta = (expires_on - today).days
    return -1 <= delta <= NEAR_EXPIRY_DAYS


def _servings_scale(recipe: RecipeView, constraints: ConstraintView) -> float:
    recipe_servings = recipe.servings or 1
    target = constraints.servings or recipe_servings
    return target / recipe_servings


def _passes_filters(recipe: RecipeView, constraints: ConstraintView) -> bool:
    if not diet_allows(recipe.diet_tags, constraints.diet_tags):
        return False
    if constraints.max_cook_minutes is not None:
        total = (recipe.prep_minutes or 0) + (recipe.cook_minutes or 0)
        if total > constraints.max_cook_minutes:
            return False
    exclusions = constraints.exclude_ingredients or []
    if exclusions and any(is_excluded(ingredient.name, exclusions) for ingredient in recipe.ingredients):
        return False
    return True


def _cover_ingredient(
    ingredient: Ingredient,
    pantry: list[PantryLine],
    scale: float,
    today: date,
) -> dict:
    need_qty = None if ingredient.quantity is None else ingredient.quantity * scale
    matches = [item for item in pantry if names_match(item.name, ingredient.name)]
    convertible: list[tuple[PantryLine, float]] = []
    for item in matches:
        if need_qty is None or not ingredient.unit:
            continue
        converted = quantity_in_unit(item.quantity, item.unit, ingredient.unit)
        if converted is not None:
            convertible.append((item, converted))

    used = [item for item, _qty in convertible] if convertible else matches
    near = [item for item in used if is_near_expiry(item.expires_on, today)]
    expires_on = min((item.expires_on for item in near), default=None)

    if need_qty is None:
        credit = 1.0 if matches else 0.0
        have_qty = None
    elif convertible:
        have_qty = sum(qty for _item, qty in convertible)
        credit = 1.0 if need_qty <= 0 else min(1.0, have_qty / need_qty)
    elif matches:
        have_qty = None
        credit = NAME_ONLY_CREDIT
    else:
        have_qty = 0.0
        credit = 0.0

    detail = ""
    if need_qty is not None and ingredient.unit and have_qty is not None and credit < 1:
        detail = f"have {_round(have_qty, 2)} {ingredient.unit} / need {_round(need_qty, 2)} {ingredient.unit}"
    elif credit >= 1 and need_qty is not None and ingredient.unit:
        detail = f"{_round(need_qty, 2)} {ingredient.unit} on hand"
    elif credit > 0 and not convertible:
        detail = "on hand, amount not compared"

    return {
        "name": ingredient.name,
        "need_qty": None if need_qty is None else _round(need_qty, 2),
        "unit": ingredient.unit,
        "have_qty": None if have_qty is None else _round(have_qty, 2),
        "credit": credit,
        "optional": ingredient.optional,
        "near_expiry": bool(near) and credit > 0,
        "expires_on": expires_on.isoformat() if expires_on else None,
        "detail": detail,
        "pantry_name": used[0].name if used else None,
    }


def _why(required_count: int, covered_count: int, coverage: float, use_soon: list[str], missing_names: list[str]) -> str:
    if required_count == 0:
        return "This recipe has no required ingredients to match."
    percent = round(coverage * 100)
    if covered_count == 0:
        sentence = f"None of the {required_count} ingredients are in your pantry yet."
    else:
        sentence = f"Uses {covered_count} of {required_count} ingredients you need ({percent}% covered)."
    parts = [sentence]
    if use_soon:
        listed = ", ".join(use_soon)
        parts.append(f"Cook soon to use up {listed}.")
    if missing_names:
        preview = ", ".join(missing_names[:4])
        extra = len(missing_names) - 4
        if extra > 0:
            preview = f"{preview} +{extra} more"
        parts.append(f"Still to buy: {preview}.")
    return " ".join(parts)


def _shopping_note(credit: float) -> str:
    if credit <= 0:
        return "missing"
    if credit < 1:
        return "short"
    return "check amount"


def score_recipe(
    recipe: RecipeView,
    pantry: list[PantryLine],
    constraints: ConstraintView,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    scale = _servings_scale(recipe, constraints)
    scaled_servings = constraints.servings or recipe.servings or 2
    rows = [_cover_ingredient(ingredient, pantry, scale, today) for ingredient in recipe.ingredients]
    required = [row for row in rows if not row["optional"]]
    if not required:
        coverage = 1.0
    else:
        coverage = sum(row["credit"] for row in required) / len(required)

    use_soon = []
    for row in required:
        if row["near_expiry"] and row["credit"] > 0 and row["name"] not in use_soon:
            use_soon.append(row["name"])
    bonus = min(EXPIRY_BONUS_CAP, EXPIRY_BONUS_EACH * len(use_soon))
    score = _round(coverage + bonus, 4)
    coverage = _round(coverage, 4)

    matched = []
    missing = []
    shopping = []
    for row in rows:
        if row["credit"] > 0:
            matched.append(
                {
                    "name": row["name"],
                    "coverage": _round(row["credit"], 3),
                    "near_expiry": row["near_expiry"],
                    "optional": row["optional"],
                    "assumed": False,
                    "detail": row["detail"],
                }
            )
        if row["optional"] or row["credit"] >= 1:
            continue
        missing.append(
            {
                "name": row["name"],
                "quantity": row["need_qty"],
                "unit": row["unit"],
                "partial": row["credit"] > 0,
            }
        )
        shortfall = None
        if row["need_qty"] is not None and row["have_qty"] is not None and row["credit"] > 0:
            shortfall = _round(max(0.0, row["need_qty"] - row["have_qty"]), 2)
        elif row["need_qty"] is not None and row["credit"] <= 0:
            shortfall = row["need_qty"]
        else:
            shortfall = row["need_qty"]
        shopping.append(
            {
                "name": row["name"],
                "quantity": shortfall,
                "unit": row["unit"],
                "note": _shopping_note(row["credit"]) if row["have_qty"] is not None or row["credit"] <= 0 else "check amount",
            }
        )

    covered_count = sum(1 for row in required if row["credit"] > 0)
    missing_names = [row["name"] for row in missing]
    return {
        "recipe_id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "score": score,
        "coverage": coverage,
        "prep_minutes": recipe.prep_minutes,
        "cook_minutes": recipe.cook_minutes,
        "servings": recipe.servings,
        "scaled_servings": scaled_servings,
        "diet_tags": list(recipe.diet_tags),
        "matched_ingredients": matched,
        "missing_ingredients": missing,
        "shopping_delta": shopping,
        "why": _why(len(required), covered_count, coverage, use_soon, missing_names),
        "use_soon": use_soon,
        "instructions": list(recipe.instructions),
        "llm_tip": None,
    }


def rank_recipes(
    recipes: list[RecipeView],
    pantry: list[PantryLine],
    constraints: ConstraintView,
    *,
    limit: int = 5,
    today: date | None = None,
) -> list[dict]:
    today = today or date.today()
    ranked = [
        score_recipe(recipe, pantry, constraints, today)
        for recipe in recipes
        if _passes_filters(recipe, constraints)
    ]
    ranked.sort(
        key=lambda item: (
            -item["score"],
            -item["coverage"],
            -len(item["use_soon"]),
            item["prep_minutes"] + item["cook_minutes"],
            item["title"].lower(),
        )
    )
    return ranked[: max(1, limit)]


def expiry_horizon(today: date | None = None) -> date:
    today = today or date.today()
    return today + timedelta(days=NEAR_EXPIRY_DAYS)
