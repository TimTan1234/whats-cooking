"""Pure logic: ingredient keys, allergy and diet checks, ranking, translations."""

from app import i18n
from app.schemas import Detection, DishIdea, FullRecipe, IdeaList, QuestionList, json_schema
from app.services.safety import dish_conflicts, find_conflicts
from app.services.text import name_key, split_list


def conflicts(ingredients, allergies=(), diets=()):
    return [(c.ingredient, c.rule) for c in find_conflicts(list(ingredients), list(allergies), list(diets))]


def test_name_key_merges_spelling_variants():
    assert name_key("Tomatoes") == name_key(" TOMATO ") == "tomato"
    assert name_key("Eggs") == "egg"
    assert name_key("couscous") == "couscous"
    assert name_key("Cherries") == "cherry"
    assert name_key("鸡蛋") == "鸡蛋"
    assert name_key("  !! ") == ""


def test_split_list_dedupes_and_handles_chinese_commas():
    assert split_list("peanuts, shellfish，kiwi\nPeanuts") == ["peanuts", "shellfish", "kiwi"]


def test_allergens_are_found_but_lookalikes_are_not():
    assert conflicts(["Eggplant", "Eggs", "coconut milk"], ["egg", "dairy"]) == [("Eggs", "egg")]
    assert conflicts(["Butternut squash", "nutmeg", "Cashews"], ["tree_nut", "dairy"]) == [("Cashews", "tree_nut")]
    assert conflicts(["Oyster sauce", "oyster mushroom"], ["shellfish"]) == [("Oyster sauce", "shellfish")]
    assert conflicts(["rice noodles", "Egg noodles"], ["gluten"]) == [("Egg noodles", "gluten")]


def test_diet_rules():
    assert conflicts(["Hamburger bun", "Bacon", "Shaoxing wine", "rice vinegar"], diets=["halal"]) == [
        ("Bacon", "halal"), ("Shaoxing wine", "halal")]
    assert conflicts(["鸡蛋", "Chicken thigh", "Tofu"], diets=["vegetarian"]) == [("Chicken thigh", "vegetarian")]


def test_chinese_and_custom_allergies():
    assert conflicts(["豆腐", "猪肉"], ["soy"], ["no_pork"]) == [("豆腐", "soy"), ("猪肉", "no_pork")]
    assert conflicts(["Kiwi fruit", "kiwis", "kiwifruit jam"], ["kiwi"]) == [("Kiwi fruit", "kiwi"), ("kiwis", "kiwi")]


def test_detections_from_several_photos_merge_into_one_numbered_list():
    from types import SimpleNamespace as Seen

    from app.services.detect import clean_box, merge

    def seen(name, quantity="", confidence="high", box=(100, 100, 300, 300)):
        return Seen(name=name, quantity=quantity, category="produce", confidence=confidence, evidence="why", box_2d=list(box))

    found = merge([
        [seen("Tomatoes", confidence="low"), seen("Eggs", "6"), seen("  ")],
        [seen("tomato", "3", confidence="high", box=(0, 0, 50, 50)), seen("Garlic", box=(5, 5))],
    ])
    assert [(f.number, f.name, f.quantity, f.confidence) for f in found] == [
        (1, "Tomatoes", "3", "high"), (2, "Eggs", "6", "high"), (3, "Garlic", "", "high")]
    assert found[0].boxes == [(0, (100, 100, 300, 300)), (1, (0, 0, 50, 50))]  # seen in both photos
    assert found[2].boxes == []  # a malformed box is dropped, the ingredient is kept

    assert clean_box([10, 20, 2000, -5]) is None  # no width once clamped to the photo
    assert clean_box([10, 20, 2000, 400]) == (10, 20, 1000, 400)
    assert clean_box("nonsense") is None and clean_box(None) is None


def test_staples_never_count_and_numerals_agree():
    from app.services.recommend import is_staple, recipe_count, tidy_idea

    assert is_staple("Salt") and is_staple("salt, to taste") and is_staple("食用油") and is_staple("Cooking oil")
    assert not is_staple("Sesame oil") and not is_staple("Salted egg") and not is_staple("Brown sugar")

    idea = tidy_idea(DishIdea(title="T", blurb="", minutes=10, difficulty="easy", cuisine="",
                              uses=["Eggs", "Salt", "Rice"], missing=["Cooking oil", "Spring onion"]))
    assert (idea.uses, idea.missing) == (["Eggs", "Rice"], ["Spring onion"])

    lines = [{"name": "Eggs", "have": True}, {"name": "Rice", "have": True}, {"name": "Spring onion", "have": False},
             {"name": "Salt", "have": True}, {"name": "Water", "have": False}]  # older recipes have no "staple" key
    assert recipe_count(lines) == (2, 3)  # same 2 of 3 as the idea it came from


def test_ranking_puts_conflicts_last_then_fewest_missing():
    from app.models import User
    from app.services.recommend import rank_ideas

    def idea(title, uses, missing, minutes=20):
        return DishIdea(title=title, blurb="", minutes=minutes, difficulty="easy", cuisine="", uses=uses, missing=missing)

    user = User(username="x", password_hash="x", allergies=["peanut"], diets=[])
    ranked = rank_ideas([
        idea("Satay", ["chicken"], ["peanuts"]),
        idea("Two missing", ["egg"], ["a", "b"]),
        idea("Slow, complete", ["egg", "rice"], [], minutes=50),
        idea("Fast, complete", ["egg", "rice"], [], minutes=10),
    ], user)
    assert [r.idea.title for r in ranked] == ["Fast, complete", "Slow, complete", "Two missing", "Satay"]
    assert ranked[-1].conflicts and not ranked[0].conflicts
    assert (ranked[2].have, ranked[2].total) == (1, 3)


def test_taste_order_keeps_the_ai_order_with_conflicts_last():
    from app.models import User
    from app.services.recommend import rank_ideas

    def idea(title, missing):
        return DishIdea(title=title, blurb="", minutes=20, difficulty="easy", cuisine="", uses=[], missing=missing)

    user = User(username="x", password_hash="x", allergies=["peanut"], diets=[])
    ranked = rank_ideas([idea("Satay", ["peanuts"]), idea("Laksa", ["a", "b", "c"]), idea("Bubur", ["rice"])],
                        user, by_kitchen=False)
    assert [r.idea.title for r in ranked] == ["Laksa", "Bubur", "Satay"]


def test_cook_options_keep_known_dish_types_and_old_stored_options():
    from app.services.recommend import CookOptions

    assert CookOptions(dish_type="pizza").dish_type == ""
    assert CookOptions(dish_type="soup", craving="  warm   and  soft ").craving == "warm and soft"
    old = CookOptions.model_validate({"ingredients": ["Eggs"], "minutes": 15, "cuisine": "", "meal": "",
                                      "servings": 2, "extras_ok": True})
    assert (old.dish_type, old.craving, old.answers) == ("", "", [])


def test_prompts_carry_the_dish_type_craving_answers_and_taste():
    from app.ai import prompts
    from app.ai.base import CookContext

    ctx = CookContext(
        ingredients=["Eggs (6)"], dish_type="a soup", craving="something warm", answers=["Clear or creamy? → Clear"],
        likes="laksa", usual_dish_types=["a noodle dish"], disliked_titles=["Bitter gourd stir-fry"],
    )
    text = prompts.suggest_prompt(ctx, 5)
    for part in ("a soup", '"something warm"', "Clear or creamy? → Clear", "laksa", "a noodle dish",
                 "Bitter gourd stir-fry", "up to 3 ingredients"):
        assert part in text, part
    assert "a soup" in prompts.questions_prompt(ctx) and "laksa" in prompts.questions_prompt(ctx)

    today = prompts.suggest_prompt(CookContext(ingredients=[], likes="laksa", today=True), 5)
    assert "not from what is in their kitchen" in today and "laksa" in today
    assert "up to 3 ingredients" not in today and "(nothing listed)" in today


def test_ai_schemas_have_no_refs_or_defaults():
    for model in (Detection, IdeaList, QuestionList, FullRecipe):
        text = str(json_schema(model))
        assert "$ref" not in text and "$defs" not in text and "'default'" not in text


def test_ai_schemas_keep_every_required_field():
    from app.ai.openai_compat import strict_schema

    def objects(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                yield node
            for value in node.values():
                yield from objects(value)
        elif isinstance(node, list):
            for item in node:
                yield from objects(item)

    for model in (Detection, IdeaList, QuestionList, FullRecipe):
        for schema in (json_schema(model), strict_schema(json_schema(model))):
            for obj in objects(schema):
                assert set(obj["required"]) == set(obj["properties"]), model.__name__
    assert "title" in json_schema(FullRecipe)["properties"]  # a field called "title" survives
    assert strict_schema(json_schema(IdeaList))["properties"]["ideas"]["items"]["additionalProperties"] is False


def test_translations_cover_both_languages_and_plurals():
    for key, (english, chinese) in i18n.STRINGS.items():
        assert english, key
        assert chinese or key.endswith("_one"), key
    assert i18n.t("en", "scan.chosen", n=1) == "1 photo chosen"
    assert i18n.t("en", "scan.chosen", n=3) == "3 photos chosen"
    assert i18n.t("zh", "scan.chosen", n=1) == "已选 1 张"
    assert i18n.t("en", "no.such.key") == "no.such.key"


def test_a_dish_title_only_adds_a_rule_its_ingredients_do_not_show():
    found = dish_conflicts("Egg fried rice", ["Eggs", "Rice"], ["egg"], [])
    assert [(c.ingredient, c.rule) for c in found] == [("Eggs", "egg")]
    found = dish_conflicts("Peanut noodles", ["Noodles"], ["peanut"], [])
    assert [(c.ingredient, c.rule) for c in found] == [("Peanut noodles", "peanut")]
