"""Sample AI answers used in demo mode (no Gemini key) and in tests.

Nothing here is real analysis: photos are ignored and the same sample
ingredients come back every time. The app labels demo mode on every page.
"""

import re

from app.ai.base import CookContext
from app.schemas import Detection, DetectedIngredient, DishIdea, FullRecipe, RecipeIngredient

_SAMPLE = {
    "en": [("Kangkung", "1 bunch", "produce", "high"), ("Eggs", "6", "dairy_egg", "high"),
           ("Chicken thigh", "about 400 g", "protein", "high"), ("Firm tofu", "1 block", "protein", "medium"),
           ("Garlic", "1 bulb", "produce", "high"), ("Tomatoes", "3", "produce", "high"),
           ("Jasmine rice", "", "grain", "medium"), ("Light soy sauce", "half a bottle", "sauce_spice", "low")],
    "zh": [("空心菜", "1把", "produce", "high"), ("鸡蛋", "6个", "dairy_egg", "high"),
           ("鸡腿肉", "约400克", "protein", "high"), ("老豆腐", "1块", "protein", "medium"),
           ("蒜头", "1颗", "produce", "high"), ("番茄", "3个", "produce", "high"),
           ("香米", "", "grain", "medium"), ("生抽", "半瓶", "sauce_spice", "low")],
}

_STYLES = {
    "en": [("Quick stir-fried {a} with {b}", "A fast wok dish that lets the {a} stay crisp.", 15, "easy", "Chinese"),
           ("Braised {a} and {b}", "Slow, saucy and good over rice.", 40, "medium", "Malaysian"),
           ("{a} fried rice", "Day-old rice, high heat and plenty of {a}.", 20, "easy", "Malaysian"),
           ("{a} soup with {b}", "A light, clear soup for any night.", 30, "easy", "Chinese"),
           ("Pan-seared {a} with {b} salad", "Crisp outside, fresh on the side.", 25, "medium", "Western")],
    "zh": [("{a}快炒{b}", "大火快炒，{a}保持爽脆。", 15, "easy", "中餐"),
           ("红烧{a}配{b}", "慢火入味，汁多下饭。", 40, "medium", "马来西亚菜"),
           ("{a}炒饭", "隔夜饭配大火，{a}要多。", 20, "easy", "马来西亚菜"),
           ("{a}{b}汤", "清淡的家常汤，哪天喝都合适。", 30, "easy", "中餐"),
           ("香煎{a}配{b}沙拉", "外皮香脆，配菜清爽。", 25, "medium", "西餐")],
}

_EXTRA = {"en": ["Spring onion", "Ginger", "Chilli"], "zh": ["青葱", "姜", "辣椒"]}


def _bare(line: str) -> str:
    return re.sub(r"\s*\(.*\)\s*$", "", line).strip()


class MockAI:
    is_mock = True

    async def detect_ingredients(self, image: bytes, lang: str) -> Detection:
        rows = _SAMPLE.get(lang, _SAMPLE["en"])
        ingredients = []
        for index, (name, quantity, category, confidence) in enumerate(rows):
            top, left = 60 + 220 * (index // 4), 40 + 240 * (index % 4)  # a tidy grid of sample boxes
            ingredients.append(DetectedIngredient(
                name=name, quantity=quantity, category=category, confidence=confidence,
                evidence="演示数据" if lang == "zh" else "sample data",
                box_2d=[top, left, top + 180, left + 200],
            ))
        return Detection(ingredients=ingredients)

    async def suggest_dishes(self, ctx: CookContext, count: int = 5) -> list[DishIdea]:
        lang = ctx.lang if ctx.lang in _STYLES else "en"
        names = [_bare(line) for line in ctx.ingredients] or [row[0] for row in _SAMPLE[lang]]
        ideas: list[DishIdea] = []
        for index, (title, blurb, minutes, difficulty, cuisine) in enumerate(_STYLES[lang][:count]):
            first = names[index % len(names)]
            second = names[(index + 1) % len(names)]
            uses = list(dict.fromkeys([first, second, *names[:3]]))
            missing = _EXTRA[lang][: index % 3] if ctx.extras_ok else []
            ideas.append(DishIdea(
                title=title.format(a=first, b=second),
                blurb=blurb.format(a=first, b=second),
                minutes=min(minutes, ctx.minutes) if ctx.minutes else minutes,
                difficulty=difficulty,
                cuisine=ctx.cuisine or cuisine,
                uses=uses,
                missing=missing,
            ))
        return ideas

    async def write_recipe(self, ctx: CookContext, idea: DishIdea) -> FullRecipe:
        zh = ctx.lang == "zh"
        ingredients = [RecipeIngredient(name=name, amount="适量" if zh else "as needed", have=True) for name in idea.uses]
        ingredients += [RecipeIngredient(name=name, amount="少许" if zh else "a little", have=False) for name in idea.missing]
        if zh:
            steps = ["把所有食材洗净、切好。", "热锅下油，爆香蒜和辛香料。", "先下需要久煮的食材，再下易熟的。",
                     "调味，试味后再调整。", "盛盘，趁热上桌。"]
            tips = ["这是演示模式的示例食谱，并非真实的 AI 结果。"]
            subs = [f"没有{name}可以省略。" for name in idea.missing]
        else:
            steps = ["Wash and cut all the ingredients.", "Heat oil in a pan and fry the garlic and aromatics until fragrant.",
                     "Add the ingredients that take longest first, then the quick-cooking ones.",
                     "Season, taste and adjust.", "Plate up and serve hot."]
            tips = ["This is a sample recipe from demo mode, not a real AI answer."]
            subs = [f"Leave out the {name} if you do not have it." for name in idea.missing]
        return FullRecipe(
            title=idea.title, description=idea.blurb, cuisine=idea.cuisine, minutes=idea.minutes,
            servings=ctx.servings, difficulty=idea.difficulty, ingredients=ingredients,
            steps=steps, tips=tips, substitutions=subs,
        )
