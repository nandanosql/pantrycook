"""API smoke coverage: seed, CRUD, constraints, and offline suggest."""


def test_health_and_seed(client):
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["service"] == "pantrycook"
    assert body["llm_configured"] is False

    recipes = client.get("/recipes")
    assert recipes.status_code == 200
    rows = recipes.json()
    assert 18 <= len(rows) <= 25
    assert rows[0]["ingredients"]
    assert "diet_tags" in rows[0]


def test_pantry_crud(client):
    created = client.post(
        "/pantry",
        json={"name": "Lemon", "quantity": 2, "unit": "piece", "expires_on": "2026-09-28"},
    )
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "Lemon"

    fetched = client.get(f"/pantry/{item['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["quantity"] == 2

    updated = client.put(
        f"/pantry/{item['id']}",
        json={"name": "Lemon", "quantity": 1, "unit": "piece", "expires_on": None},
    )
    assert updated.status_code == 200
    assert updated.json()["quantity"] == 1

    assert client.delete(f"/pantry/{item['id']}").status_code == 204
    assert client.get(f"/pantry/{item['id']}").status_code == 404


def test_recipe_crud_roundtrip(client):
    payload = {
        "title": "Test Toast",
        "description": "A recipe created in the test suite.",
        "instructions": ["Toast the bread."],
        "prep_minutes": 2,
        "cook_minutes": 3,
        "servings": 1,
        "diet_tags": ["Vegetarian"],
        "ingredients": [{"name": "bread", "quantity": 1, "unit": "slice", "optional": False}],
    }
    created = client.post("/recipes", json=payload)
    assert created.status_code == 201
    recipe = created.json()
    assert recipe["diet_tags"] == ["vegetarian"]

    payload["title"] = "Test Toast Updated"
    updated = client.put(f"/recipes/{recipe['id']}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["title"] == "Test Toast Updated"

    assert client.delete(f"/recipes/{recipe['id']}").status_code == 204
    assert client.get(f"/recipes/{recipe['id']}").status_code == 404


def test_constraints_roundtrip_and_offline_suggest(client):
    saved = client.put(
        "/constraints",
        json={
            "diet_tags": ["vegan"],
            "max_cook_minutes": 90,
            "servings": 2,
            "exclude_ingredients": ["shrimp"],
        },
    )
    assert saved.status_code == 200
    assert saved.json()["diet_tags"] == ["vegan"]
    assert client.get("/constraints").json()["exclude_ingredients"] == ["shrimp"]

    suggested = client.post("/suggest", json={"limit": 20})
    assert suggested.status_code == 200
    body = suggested.json()
    assert body["llm_configured"] is False
    assert body["recipe_count"] >= 18
    assert body["suggestions"]
    for item in body["suggestions"]:
        assert "vegan" in item["diet_tags"]
        assert "score" in item
        assert "matched_ingredients" in item
        assert "missing_ingredients" in item
        assert "shopping_delta" in item
        assert item["llm_tip"] is None
        assert "shrimp" not in item["title"].lower()

    client.put(
        "/constraints",
        json={"diet_tags": [], "max_cook_minutes": 45, "servings": 2, "exclude_ingredients": []},
    )


def test_sample_pantry_is_idempotent(client):
    first = client.post("/pantry/sample")
    assert first.status_code == 200
    names = {item["name"].lower() for item in first.json()}
    assert "tomato" in names
    assert "canned tomatoes" in names
    assert len(first.json()) >= 10
    second = client.post("/pantry/sample")
    assert len(second.json()) == len(first.json())
