"""The main journeys, using the demo AI: scan, pantry, suggestions, recipes."""

import re

from sqlmodel import Session, select

from app.db import get_engine
from app.models import CookLog, IdeaSet, PantryItem, Recipe, User


def pantry_names(username: str) -> list[str]:
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.username == username)).one()
        return sorted(item.name for item in session.exec(select(PantryItem).where(PantryItem.user_id == user.id)))


def stock(client, *names: str) -> None:
    for name in names:
        client.post("/pantry", data={"name": name})


def test_add_edit_and_remove_pantry_items(mei):
    mei.post("/pantry", data={"name": "Tomatoes", "quantity": "3"})
    mei.post("/pantry", data={"name": "tomato", "quantity": "5"})  # same ingredient, new amount
    assert pantry_names("mei") == ["Tomatoes"]
    with Session(get_engine()) as session:
        item = session.exec(select(PantryItem)).one()
        assert item.quantity == "5"
        item_id = item.id
    assert mei.get(f"/pantry/{item_id}").status_code == 200
    mei.post(f"/pantry/{item_id}", data={"name": "Cherry tomatoes", "quantity": "1 punnet", "category": "produce"})
    assert pantry_names("mei") == ["Cherry tomatoes"]
    mei.post(f"/pantry/{item_id}/delete")
    assert pantry_names("mei") == []


def test_blank_ingredient_is_not_added(mei):
    mei.post("/pantry", data={"name": "   "})
    assert pantry_names("mei") == []


def test_every_page_renders_in_both_languages(mei):
    stock(mei, "Eggs", "Rice")
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    for lang in ("en", "zh"):
        mei.post("/lang", data={"lang": lang, "back": "/"})
        for path in ("/", "/scan", "/cook", "/cook/ideas", "/recipes", "/profile"):
            assert mei.get(path).status_code == 200, (lang, path)
    assert mei.get("/no-such-page").status_code == 404


def test_scan_review_and_save(mei, photo):
    page = mei.post("/scan", files=[("photos", ("fridge.jpg", photo, "image/jpeg")), ("photos", ("shelf.jpg", photo, "image/jpeg"))])
    assert page.status_code == 200
    assert page.text.count('value="Kangkung"') == 1  # the same ingredient in two photos is listed once
    assert page.text.count("data:image/jpeg;base64,") == 2  # each photo comes back with numbered boxes
    assert 'name="name_7"' in page.text and 'name="keep_7" value="1" aria-label="Keep Light soy sauce">' in page.text  # a guess starts unticked

    saved = mei.post("/scan/save", data={
        "count": "3", "action": "save",
        "keep_0": "1", "name_0": "Kangkung", "qty_0": "1 bunch", "cat_0": "produce",
        "name_1": "Eggs", "qty_1": "6", "cat_1": "dairy_egg",  # not ticked
        "keep_2": "1", "name_2": "Garlic", "qty_2": "", "cat_2": "produce",
    })
    assert saved.status_code == 200
    assert pantry_names("mei") == ["Garlic", "Kangkung"]


def test_scan_cook_with_just_these_leaves_the_pantry_alone(mei):
    page = mei.post("/scan/save", data={"count": "1", "action": "cook", "keep_0": "1", "name_0": "Tofu", "qty_0": "1 block"})
    assert page.status_code == 200 and "Tofu (1 block)" in page.text
    assert pantry_names("mei") == []


def test_scan_offers_the_camera_and_the_gallery(mei, photo):
    page = mei.get("/scan").text
    assert 'capture="environment"' in page  # opens the rear camera directly
    assert page.count('name="photos"') == 2  # camera and gallery feed the same upload

    # the unused picker sends an empty part; only real photos count
    review = mei.post("/scan", files=[("photos", ("", b"", "application/octet-stream")),
                                      ("photos", ("camera.jpg", photo, "image/jpeg"))])
    assert review.status_code == 200 and review.text.count("data:image/jpeg;base64,") == 1


def test_scan_rejects_bad_uploads(mei, photo, monkeypatch):
    assert mei.post("/scan").status_code == 400
    not_a_photo = mei.post("/scan", files=[("photos", ("notes.txt", b"hello", "text/plain"))])
    assert not_a_photo.status_code == 400
    too_many = mei.post("/scan", files=[("photos", (f"{i}.jpg", photo, "image/jpeg")) for i in range(5)])
    assert too_many.status_code == 400

    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    assert mei.post("/scan", files=[("photos", ("big.jpg", photo, "image/jpeg"))]).status_code == 413


def test_cook_needs_ingredients(mei):
    assert mei.post("/cook", data={"source": "pantry"}).status_code == 400
    assert mei.post("/cook", data={"source": "custom", "custom": "  "}).status_code == 400
    # no suggestions stored yet: the ideas page and recipe writing send you back to the form
    assert mei.get("/cook/ideas").url.path == "/cook"
    assert mei.post("/recipes", data={"pick": "0"}).url.path == "/cook"


def test_suggest_then_recipe_then_save_and_cook(mei):
    stock(mei, "Kangkung", "Eggs", "Garlic")

    ideas = mei.post("/cook", data={"source": "pantry", "minutes": "30", "servings": "2", "extras_ok": "1"})
    assert ideas.status_code == 200 and ideas.url.path == "/cook/ideas"
    with Session(get_engine()) as session:
        stored = session.exec(select(IdeaSet)).one()
        assert stored.options["minutes"] == 30 and len(stored.ideas) >= 3
        best = stored.ideas[0]["title"]
        assert stored.ideas[0]["missing"] == []  # fewest missing ingredients ranks first

    # the best match becomes tonight's leaf on the kitchen page
    home = mei.get("/").text
    assert "Tonight" in home and best in home and "Cook this" in home

    recipe_page = mei.post("/recipes", data={"pick": "0"})
    assert recipe_page.status_code == 200
    recipe_path = recipe_page.url.path
    assert re.fullmatch(r"/recipes/\d+", recipe_path)
    assert mei.post("/recipes", data={"pick": "99"}).url.path == "/cook"  # not one of the suggestions

    mei.post(f"{recipe_path}/save")
    with Session(get_engine()) as session:
        recipe = session.exec(select(Recipe)).one()
        assert recipe.is_saved and recipe.title == best and recipe.data["steps"]
        used_id = session.exec(select(PantryItem).where(PantryItem.name == "Eggs")).one().id
        garlic_id = session.exec(select(PantryItem).where(PantryItem.name == "Garlic")).one().id

    # used ingredients are ticked for removal, except long-lasting staples
    mei.post(f"/pantry/{garlic_id}", data={"name": "Garlic", "category": "sauce_spice"})
    page = mei.get(recipe_path).text
    assert f'name="used" value="{used_id}" checked' in page
    assert f'name="used" value="{garlic_id}">' in page

    cooked = mei.post(f"{recipe_path}/cooked", data={"rating": "5", "used": str(used_id)})
    assert "Cooked " in cooked.text  # the cooked mark on the leaf
    assert pantry_names("mei") == ["Garlic", "Kangkung"]
    with Session(get_engine()) as session:
        assert session.exec(select(CookLog)).one().rating == 5

    assert recipe.title in mei.get("/recipes").text
    home = mei.get("/").text
    assert "Last cooked" in home
    assert f'<h2 class="leaf-title">{best}</h2>' not in home  # the cooked dish is torn off tonight's leaf

    mei.post(f"{recipe_path}/delete")
    with Session(get_engine()) as session:
        assert session.exec(select(Recipe)).first() is None
        assert session.exec(select(CookLog)).first() is None


def test_used_up_ingredients_turn_red_on_tonights_leaf(mei):
    stock(mei, "Kangkung", "Eggs", "Garlic")
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    with Session(get_engine()) as session:
        first = session.exec(select(IdeaSet)).one().ideas[0]
        gone = first["uses"][0]
        gone_id = session.exec(select(PantryItem).where(PantryItem.name == gone)).one().id
    mei.post(f"/pantry/{gone_id}/delete")
    home = mei.get("/").text
    assert f'<li class="is-missing">{gone} ' in home  # now listed as to buy
    assert f'class="numeral-have" aria-hidden="true">{len(first["uses"]) - 1}</span>' in home  # the numeral drops by one

    # the recipe written from this leaf agrees: the used-up ingredient is not in hand
    recipe = mei.post("/recipes", data={"pick": "0"}).text
    assert f'<li class="is-missing"><span class="amount-name">{gone} ' in recipe


def test_tonight_only_comes_from_the_kitchen(mei):
    stock(mei, "Eggs")
    mei.post("/cook", data={"source": "custom", "custom": "Tofu\nSpring onion", "servings": "2"})
    assert "Tofu" not in mei.get("/").text


def test_suggest_different_dishes_replaces_the_set(mei):
    stock(mei, "Eggs", "Rice", "Tofu")
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    again = mei.post("/cook/again")
    assert again.status_code == 200 and again.url.path == "/cook/ideas"
    with Session(get_engine()) as session:
        assert len(session.exec(select(IdeaSet)).all()) == 1


def test_custom_list_does_not_touch_the_pantry(mei):
    ideas = mei.post("/cook", data={"source": "custom", "custom": "Tofu\nSpring onion", "servings": "2"})
    assert ideas.status_code == 200 and "Tofu" in ideas.text
    assert pantry_names("mei") == []


def test_allergy_conflict_is_flagged_on_ideas_and_recipe(mei):
    mei.post("/profile", data={"lang": "en", "allergies": ["egg"], "skill": "home"})
    stock(mei, "Eggs", "Rice")
    ideas = mei.post("/cook", data={"source": "pantry", "servings": "2"})
    assert "Check before cooking" in ideas.text
    recipe_page = mei.post("/recipes", data={"pick": "0"})
    assert "Check before cooking" in recipe_page.text and "Eggs may not fit: Eggs" in recipe_page.text


def test_profile_is_saved_and_pages_follow_language(mei):
    mei.post("/profile", data={
        "lang": "zh", "diets": ["halal"], "allergies": ["peanut"], "other_allergies": "kiwi， mango",
        "dislikes": "bitter gourd", "cuisines": ["malaysian", "nonsense"], "skill": "beginner",
    })
    with Session(get_engine()) as session:
        user = session.exec(select(User)).one()
        assert (user.lang, user.diets, user.skill) == ("zh", ["halal"], "beginner")
        assert user.allergies == ["peanut", "kiwi", "mango"]
        assert user.cuisines == ["malaysian"]
    assert 'lang="zh-Hans"' in mei.get("/").text
