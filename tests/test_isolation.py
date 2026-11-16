"""One user must never see or change another user's data."""

from sqlmodel import Session, select

from app.db import get_engine
from app.models import PantryItem, Recipe
from tests.test_flows import pantry_names


def test_pantry_is_private(mei, ali):
    mei.post("/pantry", data={"name": "Secret saffron"})
    with Session(get_engine()) as session:
        item_id = session.exec(select(PantryItem)).one().id

    assert "Secret saffron" not in ali.get("/").text
    assert ali.get(f"/pantry/{item_id}").status_code == 404
    assert ali.post(f"/pantry/{item_id}", data={"name": "Hacked"}).status_code == 404
    assert ali.post(f"/pantry/{item_id}/delete").status_code == 404
    assert pantry_names("mei") == ["Secret saffron"]


def test_suggestions_and_recipes_are_private(mei, ali):
    mei.post("/pantry", data={"name": "Secret saffron"})
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    path = mei.post("/recipes", data={"pick": "0"}).url.path
    mei.post(f"{path}/save")

    # Ali has no suggestions of his own, and cannot see or use Mei's
    assert ali.get("/cook/ideas").url.path == "/cook"
    assert ali.post("/recipes", data={"pick": "0"}).url.path == "/cook"
    assert "Secret saffron" not in ali.get("/").text

    assert ali.get(path).status_code == 404
    for action in ("save", "cooked", "delete"):
        assert ali.post(f"{path}/{action}").status_code == 404
    with Session(get_engine()) as session:
        recipe = session.exec(select(Recipe)).one()
        assert recipe.is_saved
    assert recipe.title not in ali.get("/recipes").text


def test_cooking_cannot_remove_someone_elses_ingredients(mei, ali):
    mei.post("/pantry", data={"name": "Eggs"})
    ali.post("/pantry", data={"name": "Rice"})
    with Session(get_engine()) as session:
        mei_item = session.exec(select(PantryItem).where(PantryItem.name == "Eggs")).one().id
    ali.post("/cook", data={"source": "pantry", "servings": "2"})
    path = ali.post("/recipes", data={"pick": "0"}).url.path
    ali.post(f"{path}/cooked", data={"used": str(mei_item)})
    assert pantry_names("mei") == ["Eggs"]
