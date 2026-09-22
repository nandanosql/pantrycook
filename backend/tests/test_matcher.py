"""Matcher scoring: coverage, filters, and near-expiry preference."""

from datetime import date

from app.services.matcher import (
    ConstraintView,
    Ingredient,
    PantryLine,
    RecipeView,
    rank_recipes,
)


def _recipe(title: str, ingredients: list[Ingredient], **kwargs) -> RecipeView:
    return RecipeView(id=kwargs.pop("id", None), title=title, ingredients=ingredients, **kwargs)


def _open(**kwargs) -> ConstraintView:
    base = dict(diet_tags=[], max_cook_minutes=None, servings=2, exclude_ingredients=[])
    base.update(kwargs)
    return ConstraintView(**base)


def test_full_pantry_outranks_partial_and_lists_the_gap():
    pantry = [
        PantryLine("tomato", 3, "piece", None),
        PantryLine("garlic", 6, "clove", None),
    ]
    complete = _recipe(
        "Garlic tomatoes",
        [Ingredient("tomato", 2, "piece"), Ingredient("garlic", 2, "clove")],
        servings=2,
    )
    incomplete = _recipe(
        "Tomato garlic saffron",
        [
            Ingredient("tomato", 2, "piece"),
            Ingredient("garlic", 2, "clove"),
            Ingredient("saffron", 1, "tsp"),
        ],
        servings=2,
    )
    ranked = rank_recipes([incomplete, complete], pantry, _open(), limit=5)
    assert [item["title"] for item in ranked] == ["Garlic tomatoes", "Tomato garlic saffron"]
    assert ranked[0]["coverage"] == 1
    assert ranked[0]["shopping_delta"] == []
    assert ranked[1]["coverage"] == round(2 / 3, 4)
    assert ranked[1]["missing_ingredients"][0]["name"] == "saffron"
    assert ranked[1]["shopping_delta"][0]["name"] == "saffron"
    assert ranked[1]["shopping_delta"][0]["note"] == "missing"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_diet_exclusion_and_time_filters():
    pantry = [PantryLine("onion", 2, "piece", None)]
    lentil = _recipe(
        "Lentil bowl",
        [Ingredient("onion", 1, "piece"), Ingredient("red lentils", 100, "g")],
        diet_tags=["vegan", "vegetarian", "dairy-free", "gluten-free"],
        prep_minutes=10,
        cook_minutes=20,
        servings=2,
    )
    salmon = _recipe(
        "Salmon plate",
        [Ingredient("salmon", 200, "g"), Ingredient("lemon", 1, "piece")],
        diet_tags=["pescatarian", "gluten-free", "dairy-free"],
        prep_minutes=5,
        cook_minutes=10,
        servings=2,
    )
    beef = _recipe(
        "Beef skillet",
        [Ingredient("ground beef", 200, "g"), Ingredient("onion", 1, "piece")],
        diet_tags=["gluten-free"],
        prep_minutes=10,
        cook_minutes=20,
        servings=2,
    )
    noodles = _recipe(
        "Peanut noodles",
        [Ingredient("noodles", 100, "g"), Ingredient("peanut butter", 2, "tbsp")],
        diet_tags=["vegan", "vegetarian", "dairy-free"],
        prep_minutes=5,
        cook_minutes=10,
        servings=2,
    )
    slow = _recipe(
        "All-afternoon stew",
        [Ingredient("onion", 1, "piece")],
        diet_tags=["vegan", "vegetarian", "dairy-free", "gluten-free"],
        prep_minutes=20,
        cook_minutes=90,
        servings=2,
    )
    recipes = [lentil, salmon, beef, noodles, slow]

    vegetarian = rank_recipes(recipes, pantry, _open(diet_tags=["vegetarian"]), limit=10)
    assert {item["title"] for item in vegetarian} == {"Lentil bowl", "Peanut noodles", "All-afternoon stew"}

    pescatarian = rank_recipes(recipes, pantry, _open(diet_tags=["pescatarian"]), limit=10)
    assert "Beef skillet" not in {item["title"] for item in pescatarian}
    assert "Salmon plate" in {item["title"] for item in pescatarian}
    assert "Lentil bowl" in {item["title"] for item in pescatarian}

    no_peanut = rank_recipes(recipes, pantry, _open(exclude_ingredients=["peanut"]), limit=10)
    assert "Peanut noodles" not in {item["title"] for item in no_peanut}

    quick = rank_recipes(recipes, pantry, _open(max_cook_minutes=40), limit=10)
    assert "All-afternoon stew" not in {item["title"] for item in quick}
    assert "Lentil bowl" in {item["title"] for item in quick}


def test_near_expiry_boosts_only_recipes_that_use_the_item():
    today = date(2026, 9, 22)
    soon = PantryLine("spinach", 200, "g", date(2026, 9, 23))
    later = PantryLine("spinach", 200, "g", date(2026, 10, 20))
    rice = PantryLine("rice", 500, "g", None)
    spinach_meal = _recipe(
        "Spinach rice",
        [Ingredient("spinach", 100, "g"), Ingredient("rice", 150, "g")],
        servings=2,
    )
    plain_rice = _recipe("Plain rice", [Ingredient("rice", 150, "g")], servings=2)

    with_soon = rank_recipes([spinach_meal, plain_rice], [soon, rice], _open(), today=today)
    with_later = rank_recipes([spinach_meal], [later, rice], _open(), today=today)

    soon_spinach = next(item for item in with_soon if item["title"] == "Spinach rice")
    later_spinach = with_later[0]
    plain = next(item for item in with_soon if item["title"] == "Plain rice")

    assert soon_spinach["coverage"] == later_spinach["coverage"] == 1
    assert soon_spinach["score"] > later_spinach["score"]
    assert soon_spinach["score"] > soon_spinach["coverage"]
    assert "spinach" in soon_spinach["use_soon"]
    assert plain["use_soon"] == []
    assert soon_spinach["score"] > plain["score"]


def test_partial_quantity_shortfall_and_unit_conversion():
    short = rank_recipes(
        [_recipe("Rice bowl", [Ingredient("rice", 200, "g"), Ingredient("salt", 1, "tsp", optional=True)], servings=2)],
        [PantryLine("rice", 100, "g", None)],
        _open(servings=2),
    )[0]
    assert short["coverage"] == 0.5
    assert short["shopping_delta"][0]["quantity"] == 100
    assert short["shopping_delta"][0]["unit"] == "g"
    assert short["shopping_delta"][0]["note"] == "short"
    assert all(item["name"] != "salt" for item in short["missing_ingredients"])

    converted = rank_recipes(
        [_recipe("Half kilo", [Ingredient("rice", 500, "g")], servings=2)],
        [PantryLine("rice", 1, "kg", None)],
        _open(servings=2),
    )[0]
    assert converted["coverage"] == 1
    assert converted["shopping_delta"] == []

    scaled = rank_recipes(
        [_recipe("Family rice", [Ingredient("rice", 200, "g")], servings=2)],
        [PantryLine("rice", 100, "g", None)],
        _open(servings=4),
    )[0]
    assert scaled["coverage"] == 0.25
    assert scaled["shopping_delta"][0]["quantity"] == 300
    assert scaled["scaled_servings"] == 4
