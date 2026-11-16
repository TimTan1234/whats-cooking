"""A second check on AI recipes against the user's allergies and diet.

The AI is told about allergies and diet, but it can get things wrong. This
module scans ingredient names for well-known problem terms so the app can show
a visible warning. It is a safety net, not a guarantee: it over-warns on
purpose and can still miss things, so the page always tells users to check.
"""

import re
from dataclasses import dataclass

# Canonical allergen keys offered as checkboxes in the profile.
ALLERGENS: tuple[str, ...] = (
    "peanut", "tree_nut", "shellfish", "fish", "egg", "dairy", "soy", "gluten", "sesame",
)

# Canonical diet keys offered in the profile.
DIETS: tuple[str, ...] = ("halal", "no_pork", "no_beef", "vegetarian", "vegan", "pescatarian")

_PORK = ["pork", "bacon", "ham", "lard", "char siu", "chashu", "lap cheong", "pancetta", "prosciutto",
         "chorizo", "salami", "pepperoni", "猪", "培根", "火腿", "叉烧", "腊肠", "腊肉", "五花肉", "排骨", "肉松"]
_ALCOHOL = ["wine", "beer", "rum", "brandy", "whisky", "whiskey", "vodka", "sake", "mirin", "shaoxing",
            "cooking wine", "liqueur", "料酒", "米酒", "黄酒", "绍兴酒", "啤酒", "白酒", "红酒", "味醂", "酒"]
_BEEF = ["beef", "steak", "veal", "oxtail", "brisket", "牛肉", "牛排", "牛腩", "牛尾", "肥牛"]
_POULTRY_MEAT = ["chicken", "duck", "turkey", "goose", "lamb", "mutton", "goat", "meat", "sausage", "mince",
                 "鸡", "鸭", "鹅", "羊", "肉", "香肠"]
_SEAFOOD = ["fish", "anchovy", "anchovies", "ikan bilis", "salmon", "tuna", "mackerel", "sardine", "cod",
            "prawn", "shrimp", "crab", "lobster", "clam", "mussel", "oyster", "scallop", "squid", "cockle",
            "belacan", "fishcake", "fishball", "鱼", "虾", "蟹", "蛤", "蚝", "牡蛎", "扇贝", "干贝", "鱿鱼", "峇拉煎"]
_EGG = ["egg", "mayonnaise", "蛋"]
_DAIRY = ["milk", "butter", "cheese", "cream", "yogurt", "yoghurt", "ghee", "paneer",
          "奶", "芝士", "奶酪", "黄油", "牛油", "乳酪", "酸奶"]

TERMS: dict[str, list[str]] = {
    "peanut": ["peanut", "groundnut", "satay sauce", "花生"],
    "tree_nut": ["almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia", "candlenut",
                 "buah keras", "pine nut", "杏仁", "腰果", "核桃", "开心果", "榛子", "夏威夷果", "坚果", "松子"],
    "shellfish": ["prawn", "shrimp", "crab", "lobster", "clam", "mussel", "oyster", "scallop", "squid", "cockle",
                  "belacan", "虾", "蟹", "蛤", "蚝", "牡蛎", "扇贝", "干贝", "鱿鱼", "蚬", "峇拉煎"],
    "fish": ["fish", "fishcake", "fishball", "anchovy", "anchovies", "ikan bilis", "salmon", "tuna",
             "mackerel", "sardine", "cod", "鱼", "江鱼仔"],
    "egg": _EGG,
    "dairy": _DAIRY,
    "soy": ["soy", "soya", "tofu", "tauhu", "tempeh", "edamame", "miso", "taucu", "beancurd", "bean curd",
            "豆腐", "酱油", "生抽", "老抽", "豆豉", "味噌", "黄豆", "毛豆", "腐竹", "豆干", "豆浆", "豆奶"],
    "gluten": ["wheat", "flour", "bread", "pasta", "noodle", "spaghetti", "soy sauce", "breadcrumb", "seitan",
               "barley", "roti", "面", "酱油", "麦"],
    "sesame": ["sesame", "tahini", "芝麻", "麻油", "香油"],
    # diets
    "no_pork": _PORK,
    "halal": _PORK + _ALCOHOL,
    "no_beef": _BEEF,
    "vegetarian": _PORK + _BEEF + _POULTRY_MEAT + _SEAFOOD,
    "vegan": _PORK + _BEEF + _POULTRY_MEAT + _SEAFOOD + _EGG + _DAIRY + ["honey", "蜂蜜"],
    "pescatarian": _PORK + _BEEF + _POULTRY_MEAT,
}

# Phrases that contain a problem term but are not that thing. They are blanked
# out before matching the listed key.
_DAIRY_LOOKALIKES = ["coconut milk", "coconut cream", "soy milk", "soya milk", "oat milk", "almond milk",
                     "rice milk", "peanut butter", "cocoa butter", "butter bean", "butterhead", "butternut",
                     "cream of tartar", "椰奶", "椰浆", "豆奶", "豆浆", "花生酱", "牛油果", "奶白菜"]
_EGG_LOOKALIKES = ["eggplant"]
_MEAT_LOOKALIKES = ["coconut meat", "果肉", "椰肉", "肉桂", "肉豆蔻", "鸡蛋", "鸭蛋", "鱼腥草", "鸡精", "羊角豆",
                    "oyster mushroom", "蚝菇", "vegetarian oyster sauce", "素蚝油", "chicken of the woods"]
LOOKALIKES: dict[str, list[str]] = {
    "dairy": _DAIRY_LOOKALIKES,
    "egg": _EGG_LOOKALIKES,
    "fish": ["鱿鱼", "墨鱼", "章鱼", "鱼腥草"],
    "shellfish": ["oyster mushroom", "蚝菇"],
    "gluten": ["rice noodle", "glass noodle", "rice flour", "corn flour", "cornflour", "tapioca flour",
               "glutinous rice flour", "almond flour", "米粉", "河粉", "粿条", "冬粉", "粘米粉", "糯米粉",
               "玉米粉", "木薯粉", "面豉", "荞麦"],
    "halal": ["wine vinegar", "rice vinegar", "hamburger", "root beer", "ginger beer", "酒酿"],
    "no_pork": ["hamburger"],
    "vegetarian": _MEAT_LOOKALIKES,
    "pescatarian": _MEAT_LOOKALIKES,
    "vegan": _MEAT_LOOKALIKES + _DAIRY_LOOKALIKES + _EGG_LOOKALIKES,
}


@dataclass(frozen=True)
class Conflict:
    ingredient: str  # the ingredient as written in the recipe
    rule: str  # canonical key ("peanut", "halal", ...) or the user's own allergy text
    custom: bool  # True when `rule` is free text the user typed


def _matches(term: str, text: str) -> bool:
    term = term.casefold().strip()
    if not term:
        return False
    if term.isascii():
        # whole word, allowing a plural ending: "egg" matches "eggs" but not "eggplant"
        return re.search(rf"(?<![a-z]){re.escape(term)}(?:e?s)?(?![a-z])", text) is not None
    return term in text


def _hit(key: str, terms: list[str], text: str) -> bool:
    for phrase in LOOKALIKES.get(key, []):
        text = text.replace(phrase, " ")
    return any(_matches(term, text) for term in terms)


def find_conflicts(ingredients: list[str], allergies: list[str], diets: list[str]) -> list[Conflict]:
    """Ingredients that look like they break the user's allergies or diet."""
    found: list[Conflict] = []
    for ingredient in ingredients:
        text = ingredient.casefold()
        for rule in [*allergies, *diets]:
            if rule in TERMS:
                if _hit(rule, TERMS[rule], text):
                    found.append(Conflict(ingredient, rule, custom=False))
            elif rule in allergies and _matches(rule, text):
                found.append(Conflict(ingredient, rule, custom=True))
    return found
