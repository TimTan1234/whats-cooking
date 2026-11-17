"""The main journeys, using the demo AI: scan, pantry, suggestions, recipes."""

import re

from sqlmodel import Session, select

from app.db import get_engine
from app.models import CookDraft, CookLog, IdeaSet, PantryItem, Recipe, Taste, User


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


def test_adding_by_hand_files_the_ingredient_under_its_type(mei):
    mei.post("/pantry", data={"name": "Kangkung", "category": "produce"})
    mei.post("/pantry", data={"name": "Sambal", "category": "not-a-type"})  # unknown types fall back to Other
    with Session(get_engine()) as session:
        types = {item.name: item.category for item in session.exec(select(PantryItem))}
    assert types == {"Kangkung": "produce", "Sambal": "other"}
    home = mei.get("/").text
    produce = home.index('<h3 class="pantry-group">Vegetables and fruit <span')
    other = home.index('<h3 class="pantry-group">Other <span')
    assert produce < home.index(">Kangkung<") < other < home.index(">Sambal<")

    # adding it again with nothing new says so instead of claiming an update
    again = mei.post("/pantry", data={"name": "kangkung"})
    assert "Kangkung is already in your kitchen." in again.text  # named as the list shows it


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
        assert mei.post("/cook/questions", data={"source": "pantry", "dish_type": "soup"}).status_code == 200, lang
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
    assert page.url.path == "/cook"  # an address that survives a reload and a language switch
    assert pantry_names("mei") == []

    # switching language on that page comes back to the same list
    back = re.search(r'name="back" value="([^"]+)"', page.text).group(1).replace("&amp;", "&")
    switched = mei.post("/lang", data={"lang": "zh", "back": back})
    assert switched.status_code == 200 and "Tofu (1 block)" in switched.text and "今天煮什么" in switched.text


def test_scan_review_keeps_the_work_when_nothing_is_ticked_or_the_language_changes(mei):
    review = {
        "count": "2", "action": "save",
        "name_0": "Kangkung", "qty_0": "1 bunch", "cat_0": "produce", "num_0": "1", "conf_0": "high",
        "name_1": "Ikan bilis", "qty_1": "", "cat_1": "protein", "num_1": "2", "conf_1": "low", "why_1": "blurry bag",
    }
    unticked = mei.post("/scan/save", data=review)
    assert unticked.status_code == 400 and "Nothing is ticked" in unticked.text
    assert 'value="Kangkung"' in unticked.text and 'value="Ikan bilis"' in unticked.text and "blurry bag" in unticked.text
    assert pantry_names("mei") == []

    # the header's language button sends the review form, so the list comes back in Chinese as it was left
    switched = mei.post("/scan/save", data={**review, "keep_0": "1", "lang": "zh"})
    assert switched.status_code == 200 and "核对清单" in switched.text
    assert 'name="keep_0" value="1" aria-label="保留Kangkung" checked>' in switched.text
    assert 'name="keep_1" value="1" aria-label="保留Ikan bilis">' in switched.text  # still unticked
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


def test_scan_that_finds_nothing_is_an_error_the_page_can_tell_apart(mei, photo, monkeypatch):
    from app.routers import scan as scan_router

    async def nothing(images, lang):
        return []

    monkeypatch.setattr(scan_router, "find_ingredients", nothing)
    page = mei.post("/scan", files=[("photos", ("dark.jpg", photo, "image/jpeg"))])
    assert page.status_code == 422 and "No ingredients could be seen" in page.text
    assert "data-scan-error" in page.text  # the slot the page's script reads the message from


def test_cook_needs_ingredients(mei):
    page = mei.post("/cook", data={"source": "pantry", "dish_type": "soup"})
    assert page.url.path == "/cook" and "Your kitchen has no ingredients yet" in page.text
    assert 'value="soup" checked' in page.text  # the choices are kept
    page = mei.post("/cook", data={"source": "custom", "custom": "  "})
    assert page.url.path == "/cook" and "Type at least one ingredient" in page.text
    assert 'aria-invalid="true" aria-describedby="custom-error" autofocus' in page.text  # said at the list itself
    assert 'notice-error' not in page.text and "Type at least one ingredient" not in mei.get("/cook").text  # once
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
        to_buy = [len(idea["missing"]) for idea in stored.ideas]
    # each leaf says how much there is to buy, which is what the order follows
    tallies = re.findall(r'<p class="leaf-tally leaf-tally-sub" aria-hidden="true">([^<]+)</p>', ideas.text)
    assert tallies == ["Nothing to buy" if n == 0 else "1 to buy" if n == 1 else f"{n} to buy" for n in to_buy]
    assert "in hand. Nothing to buy.</p>" in ideas.text  # and screen readers hear it with the count
    # each "Get the recipe" is named with its dish
    assert re.search(r'id="idea-1">([^<]+)</h2>', ideas.text).group(1) == best
    assert 'id="get-1" aria-labelledby="get-1 idea-1"' in ideas.text

    # the best match becomes tonight's leaf on the kitchen page
    home = mei.get("/").text
    assert "Tonight" in home and best in home and "Get the recipe" in home

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

    # deleting a cooked recipe keeps its cook and rating in the history, which still shapes suggestions
    deleted = mei.post(f"{recipe_path}/delete")
    assert "Its cooks stay in your cooking history" in deleted.text
    assert f'<span class="row-name">{recipe.title}</span>' in deleted.text and f'href="{recipe_path}' not in deleted.text
    assert mei.get(recipe_path).status_code == 404
    with Session(get_engine()) as session:
        assert session.exec(select(CookLog)).one().rating == 5
        assert not session.exec(select(Recipe)).one().is_saved

    # one never cooked leaves nothing behind
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    uncooked_path = mei.post("/recipes", data={"pick": "0"}).url.path
    assert "Recipe deleted." in mei.post(f"{uncooked_path}/delete").text
    with Session(get_engine()) as session:
        assert len(session.exec(select(Recipe)).all()) == 1


def test_a_recipe_opened_from_the_saved_tab_leads_back_to_it(mei):
    stock(mei, "Kangkung", "Eggs", "Garlic")
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    recipe_path = mei.post("/recipes", data={"pick": "0"}).url.path
    mei.post(f"{recipe_path}/cooked", data={"rating": "4"})  # cooked, never saved: only in Cooking history

    saved_tab = mei.get("/recipes").text
    assert f'href="{recipe_path}?from=saved"' in saved_tab

    def belongs_to_saved(page: str) -> bool:
        return ('<a class="back" href="/recipes">' in page
                and 'href="/recipes" aria-current="page"' in page)

    assert belongs_to_saved(mei.get(f"{recipe_path}?from=saved").text)
    assert not belongs_to_saved(mei.get(recipe_path).text)  # reached from the dish ideas: back to them

    # saving, unsaving and logging another cook keep the page in the Saved tab
    for action, form in [("save", {}), ("save", {}), ("cooked", {"rating": "0"})]:
        page = mei.post(f"{recipe_path}/{action}?from=saved", data=form)
        assert "from=saved" in str(page.url) and belongs_to_saved(page.text)


def test_a_reopened_recipe_is_marked_against_the_kitchen_as_it_is_now(mei):
    stock(mei, "Kangkung", "Eggs", "Garlic")
    mei.post("/cook", data={"source": "pantry", "servings": "2", "extras_ok": "1"})
    with Session(get_engine()) as session:
        pick = next(i for i, idea in enumerate(session.exec(select(IdeaSet)).one().ideas) if idea["missing"])
    recipe_path = mei.post("/recipes", data={"pick": str(pick)}).url.path
    with Session(get_engine()) as session:
        ingredients = session.exec(select(Recipe)).one().data["ingredients"]
        used = next(item["name"] for item in ingredients if item["have"] and not item["staple"])
        to_buy = {item["name"] for item in ingredients if not item["have"]}
        used_id = session.exec(select(PantryItem).where(PantryItem.name == used)).one().id

    def needed(page: str) -> set[str]:
        return set(re.findall(r'<li class="is-missing"><span class="amount-name">([^<]+?) <span', page))

    assert needed(mei.get(recipe_path).text) == to_buy
    mei.post(f"{recipe_path}/cooked", data={"rating": "0", "used": str(used_id)})
    assert needed(mei.get(recipe_path).text) == to_buy | {used}  # used up by that cook: to buy again
    stock(mei, *to_buy, used)
    assert needed(mei.get(recipe_path).text) == set()  # bought since


def test_saved_rows_say_how_much_is_in_hand_and_how_it_went(mei):
    stock(mei, "Kangkung", "Eggs", "Garlic")
    mei.post("/cook", data={"source": "pantry", "servings": "2"})
    first = mei.post("/recipes", data={"pick": "0"}).url.path
    second = mei.post("/recipes", data={"pick": "0"}).url.path  # the same dish written twice
    for path in (first, second):
        mei.post(f"{path}/save")
    mei.post(f"{first}/cooked", data={"rating": "4"})
    mei.post(f"{first}/cooked", data={"rating": "0"})  # a later cook without a rating keeps the last one

    saved_tab = mei.get("/recipes").text
    assert "in hand" in saved_tab and saved_tab.count("Rated 4 of 5") == 2  # saved row and history row
    assert len(re.findall(r"Written [^<·]+ · \d+ min", saved_tab)) == 2  # twins are told apart by the day they were written

    page = mei.get(first).text
    assert "Cooked 2 times · Last rated 4 of 5" in page
    assert 'data-confirm="Tap again to delete. Its cooking history stays."' in page
    assert 'data-confirm="Tap again to delete"' in mei.get(second).text


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
    assert ideas.status_code == 200 and "Tofu" in ideas.text and "<h1>Dishes for your list</h1>" in ideas.text
    assert pantry_names("mei") == []
    mei.post("/cook", data={"source": "custom", "custom": "豆腐、葱；姜", "servings": "2"})  # as typed in Chinese
    with Session(get_engine()) as session:
        assert session.exec(select(IdeaSet)).one().options["ingredients"] == ["豆腐", "葱", "姜"]


def test_allergy_conflict_is_flagged_on_ideas_and_recipe(mei):
    mei.post("/profile", data={"lang": "en", "allergies": ["egg"], "skill": "home"})
    stock(mei, "Eggs", "Rice")
    ideas = mei.post("/cook", data={"source": "pantry", "servings": "2"})
    assert "Check before cooking" in ideas.text
    recipe_page = mei.post("/recipes", data={"pick": "0"})
    assert "Check before cooking" in recipe_page.text and "Eggs may not fit: Eggs" in recipe_page.text


def test_when_every_dish_clashes_the_page_warns_once(mei):
    mei.post("/profile", data={"lang": "en", "allergies": ["egg"], "skill": "home"})
    stock(mei, "Eggs")
    ideas = mei.post("/cook", data={"source": "pantry", "servings": "2"}).text
    leaves = ideas.count('<article class="leaf">')
    assert ideas.count('class="notice notice-warn"') == leaves  # each leaf still says what to check
    assert ideas.count('role="alert"') == 1 and "Every dish here may clash with your profile (Eggs)" in ideas
    assert ideas.index("Every dish here") < ideas.index('<article class="leaf">')
    titles = re.findall(r'<h2 class="leaf-title" id="idea-\d+">([^<]+)</h2>', ideas)
    assert titles and not [t for t in titles if f"<li>{t} may not fit" in ideas]  # the ingredient line already says it
    assert ideas.count("This check can miss things") == 1  # said once, on the page warning
    assert "btn-primary" not in ideas  # no dish is offered as the one to cook


def test_tonight_leads_with_a_dish_the_profile_allows(mei):
    stock(mei, "Rice", "Tofu")
    mei.post("/cook", data={"source": "pantry", "servings": "2"})

    def needs_eggs(*indexes):
        with Session(get_engine()) as session:
            stored = session.exec(select(IdeaSet)).one()
            ideas = [dict(idea) for idea in stored.ideas]
            for index in indexes:
                ideas[index]["missing"] = ["Eggs"]
            stored.ideas = ideas
            session.add(stored)
            session.commit()
            return [idea["title"] for idea in ideas]

    # an allergy added after the suggestions were made: the first dish is passed over for a safe one
    titles = needs_eggs(0)
    mei.post("/profile", data={"lang": "en", "allergies": ["egg"], "skill": "home"})
    home = mei.get("/").text
    assert f'<h2 class="leaf-title">{titles[1]}</h2>' in home
    assert 'name="pick" value="1"' in home and "Check before cooking" not in home

    # when every dish conflicts, the warning leads the leaf and points to the others
    needs_eggs(*range(len(titles)))
    home = mei.get("/").text
    assert 'name="pick" value="0"' in home
    assert home.index("Check before cooking") < home.index('class="numeral') < home.index('class="leaf-title"')
    assert "numeral-large" not in home and 'href="/cook/ideas">See the other dishes' in home


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
    assert "饮食：清真 · 避开：花生、kiwi、mango。" in mei.get("/cook").text  # a diet is kept, an allergy avoided
    mei.post("/profile", data={"lang": "en", "allergies": ["egg"], "skill": "home"})
    assert "Avoiding: Eggs." in mei.get("/cook").text


def test_questions_then_answers_make_ideas_and_are_learned(mei):
    stock(mei, "Eggs", "Rice")
    page = mei.post("/cook/questions", data={
        "source": "pantry", "servings": "2", "dish_type": "soup", "craving": "something warm",
    })
    assert page.status_code == 200 and "Clear or creamy?" in page.text
    assert page.text.count('value="" checked><span>Either is fine') == 2  # every question can be skipped

    ideas = mei.post("/cook/answers", data={"q0": "Clear broth", "q1": "Not a listed answer"})
    assert ideas.url.path == "/cook/ideas"
    stub = re.sub(r"<[^>]+>", "", re.search(r'<p class="order-stub-line">(.*?)</p>', ideas.text, re.S).group(1))
    assert stub == "Soup · “something warm” · 2 in your kitchen · No rush · Clear or creamy? Clear broth"
    leaf = ideas.text[ideas.text.index('<article class="leaf">'):]
    assert leaf.index('class="leaf-title"') < leaf.index(" in hand")  # read after the heading, not before it
    with Session(get_engine()) as session:
        options = session.exec(select(IdeaSet)).one().options
        assert options["dish_type"] == "soup" and options["craving"] == "something warm"
        assert options["answers"] == ["Clear or creamy? → Clear broth"]
        assert session.exec(select(CookDraft)).first() is None
        taste = session.exec(select(Taste)).one()
        assert taste.dish_types == {"soup": 1} and taste.cravings == ["something warm"]
        assert taste.answers == ["Clear or creamy? → Clear broth"]
    assert mei.post("/cook/answers").url.path == "/cook"  # the questions are answered once


def test_questions_page_survives_a_reload_and_a_language_switch(mei):
    stock(mei, "Eggs")
    page = mei.post("/cook/questions", data={"source": "pantry", "servings": "2", "dish_type": "soup"})
    assert page.url.path == "/cook/questions" and "Clear or creamy?" in page.text
    switched = mei.post("/lang", data={"lang": "zh", "back": "/cook/questions"})
    assert switched.status_code == 200 and "问你几个问题" in switched.text and "Clear or creamy?" in switched.text


def test_questions_continue_the_order_and_show_what_was_asked(mei):
    stock(mei, "Eggs", "Rice")
    page = mei.post("/cook/questions", data={
        "source": "pantry", "servings": "2", "dish_type": "soup", "minutes": "30",
        "craving": "Something warm with egg and plenty of ginger, like my mum makes",
    }).text
    assert "<h1>Tonight&#39;s order</h1>" in page and "2 quick questions" in page
    stub = re.sub(r"<[^>]+>", "", re.search(r'<p class="order-stub-line">(.*?)</p>', page, re.S).group(1))
    assert stub == "Soup · “Something warm with egg and plenty of…” · 2 in your kitchen · 30 min"
    assert 'order-stub-change' not in page and 'class="back" href="/cook?change=1"' in page


def test_failed_dishes_after_answering_go_back_to_the_answered_questions(mei, monkeypatch):
    from app.ai import AIError
    from app.ai.mock import MockAI

    async def busy(self, ctx, count=5):
        raise AIError("busy")

    stock(mei, "Eggs")
    mei.post("/cook/questions", data={"source": "pantry", "servings": "2", "dish_type": "soup"})
    monkeypatch.setattr(MockAI, "suggest_dishes", busy)
    page = mei.post("/cook/answers", data={"q0": "Clear broth"})
    assert page.url.path == "/cook/questions" and "The AI service is busy" in page.text
    assert 'value="Clear broth" checked' in page.text
    assert page.text.count('value="" checked><span>Either is fine') == 1


def test_change_my_choices_brings_back_the_request(mei):
    stock(mei, "Eggs")
    mei.post("/cook", data={"source": "custom", "custom": "Tofu (1 block)\nSpring onion", "dish_type": "noodles",
                            "craving": "something warm", "minutes": "30", "servings": "4", "extras_ok": "1"})
    ideas = mei.get("/cook/ideas")
    assert 'href="/cook?change=1"' in ideas.text
    page = mei.get("/cook?change=1")
    assert 'value="custom" checked' in page.text and "Tofu (1 block)\nSpring onion</textarea>" in page.text
    assert 'value="noodles" checked' in page.text and "something warm</textarea>" in page.text
    assert 'value="30" checked' in page.text and 'value="4" selected' in page.text
    # the tab itself keeps the settings but leaves tonight's dish and craving open
    page = mei.get("/cook")
    assert 'value="" checked><span>Anything' in page.text and "something warm</textarea>" not in page.text
    assert 'value="30" checked' in page.text and "30 min · Any cuisine · 4 people · Buying a few is fine" in page.text

    # from the questions, the choices waiting on them come back instead
    mei.post("/cook/questions", data={"source": "pantry", "servings": "2", "dish_type": "soup"})
    page = mei.get("/cook?change=1")
    assert 'value="soup" checked' in page.text and 'value="pantry" checked' in page.text


def test_back_from_the_questions_keeps_what_was_typed(mei):
    from datetime import timedelta

    from app.models import utcnow

    stock(mei, "Eggs")
    mei.post("/cook/questions", data={"source": "custom", "custom": "Tofu\nSpring onion", "dish_type": "soup",
                                      "craving": "something warm", "servings": "2"})
    page = mei.get("/cook")  # what the browser loads on Back
    assert 'value="custom" checked' in page.text and "Tofu\nSpring onion</textarea>" in page.text
    assert 'value="soup" checked' in page.text and "something warm</textarea>" in page.text
    assert 'autocomplete="off"' not in page.text

    # an order left unfinished hours ago no longer decides tonight's dish
    with Session(get_engine()) as session:
        draft = session.exec(select(CookDraft)).one()
        draft.created_at = utcnow() - timedelta(hours=4)
        session.add(draft)
        session.commit()
    page = mei.get("/cook")
    assert 'value="" checked><span>Anything' in page.text and "something warm</textarea>" not in page.text
    assert "something warm</textarea>" in mei.get("/cook?change=1").text


def test_questions_that_fail_go_straight_to_dishes(mei, monkeypatch):
    from app.ai import AIError
    from app.ai.mock import MockAI

    async def busy(self, ctx):
        raise AIError("busy")

    monkeypatch.setattr(MockAI, "ask_questions", busy)
    stock(mei, "Eggs")
    assert mei.post("/cook/questions", data={"source": "pantry", "servings": "2"}).url.path == "/cook/ideas"


def test_today_for_you_that_fails_returns_to_the_page_it_was_asked_from(mei, monkeypatch):
    from app.ai import AIError
    from app.ai.mock import MockAI

    async def busy(self, ctx, count=5):
        raise AIError("busy")

    monkeypatch.setattr(MockAI, "suggest_dishes", busy)
    assert 'name="back" value="/cook"' in mei.get("/cook").text
    page = mei.post("/today", data={"back": "/cook"})
    assert page.url.path == "/cook" and "The AI service is busy" in page.text
    assert mei.post("/today", data={"back": "//elsewhere.example"}).url.path == "/"


def test_today_for_you_comes_from_taste_and_is_kept_for_the_day(mei, monkeypatch):
    from app.ai.mock import MockAI

    asked = []
    original = MockAI.suggest_dishes

    async def counted(self, ctx, count=5):
        asked.append(ctx.today)
        return await original(self, ctx, count)

    monkeypatch.setattr(MockAI, "suggest_dishes", counted)
    page = mei.post("/today")  # works with an empty kitchen
    assert page.url.path == "/cook/ideas" and "Picked for you today" in page.text
    assert "order-stub" not in page.text  # nothing was ordered, so there is nothing to recap
    assert '<li class="is-missing">Eggs ' in page.text

    stock(mei, "Eggs")
    with Session(get_engine()) as session:
        session.delete(session.exec(select(IdeaSet)).one())
        session.commit()
    page = mei.post("/today")
    assert "<li>Eggs<span" in page.text  # what the kitchen has is marked in hand
    assert mei.post("/today").url.path == "/cook/ideas" and asked == [True, True]  # same day: no new request
    assert "<h1>Today for you</h1>" in mei.get("/").text

    recipe = mei.post("/recipes", data={"pick": "0"})
    assert recipe.status_code == 200 and recipe.url.path.startswith("/recipes/")


def test_taste_is_shown_on_the_profile_and_can_be_forgotten(mei):
    from app.services import recommend

    stock(mei, "Eggs")
    for _ in range(2):
        mei.post("/cook", data={"source": "pantry", "servings": "2", "dish_type": "noodles"})
    mei.post("/profile", data={"lang": "en", "skill": "home", "likes": "laksa, chicken rice"})
    page = mei.get("/profile").text
    assert "You often ask for" in page and "<dd>Noodles</dd>" in page and 'value="laksa, chicken rice"' in page
    with Session(get_engine()) as session:
        user = session.exec(select(User)).one()
        ctx = recommend.build_context(session, user, recommend.CookOptions())
        assert ctx.usual_dish_types == ["a noodle dish"] and ctx.likes == "laksa, chicken rice"

    mei.post("/profile/taste/reset")
    page = mei.get("/profile").text
    assert "You often ask for" not in page and 'value="laksa, chicken rice"' in page
