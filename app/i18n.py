"""Screen text in English and Simplified Chinese.

Each entry is (English, Chinese). Use {name} placeholders for values. A key
ending in "_one" is used automatically when n == 1 (English needs it; Chinese
does not, so its second value can be None to fall back to the plain key).
"""

from datetime import datetime
from typing import Any

LANGS: tuple[str, ...] = ("en", "zh")

STRINGS: dict[str, tuple[str, str | None]] = {
    # navigation
    "nav.skip": ("Skip to content", "跳到正文"),
    "nav.label": ("Main", "主导航"),
    "nav.kitchen": ("Kitchen", "厨房"),
    "nav.scan": ("Scan", "扫描"),
    "nav.cook": ("Cook", "做菜"),
    "nav.saved": ("Saved", "收藏"),
    "nav.profile": ("Profile and settings", "个人资料与设置"),
    "lang.switch": ("Switch to Chinese", "切换到英文"),
    "demo.tag": ("Demo", "演示"),
    "demo.banner": ("Demo mode: no AI key is set, so ingredients and recipes are samples.",
                    "演示模式：尚未设置 AI 密钥，食材和食谱均为示例。"),
    # sign in
    "login.title": ("Sign in", "登录"),
    "login.username": ("Username", "用户名"),
    "login.password": ("Password", "密码"),
    "login.submit": ("Sign in", "登录"),
    "login.wrong": ("That username and password don't match. Check both and try again.",
                    "用户名或密码不正确，请检查后再试。"),
    "login.locked": ("Too many wrong attempts. Wait 5 minutes, then try again.", "错误次数过多，请 5 分钟后再试。"),
    "login.help": ("Accounts are created by whoever runs this server.", "账号由服务器管理员创建。"),
    # kitchen
    "kitchen.tonight": ("Tonight", "今晚"),
    "kitchen.best_from": ("Best match from {n} ingredients", "从 {n} 种食材里选出的最佳搭配"),
    "kitchen.best_from_one": ("Best match from 1 ingredient", None),
    "kitchen.none_yet": ("No dish picked yet. Ask for dishes that fit what you have.", "还没选菜。看看现有食材能做什么。"),
    "kitchen.title": ("In your kitchen", "你的厨房"),
    "kitchen.empty_title": ("Your kitchen is empty", "厨房里还没有食材"),
    "kitchen.empty_body": ("Take a photo of your fridge or shelf and the ingredients are listed for you. "
                           "You can also add them by hand below.",
                           "拍一张冰箱或橱柜的照片，就能自动列出食材；也可以在下面手动添加。"),
    "kitchen.edit_hint": ("Tap an ingredient to change or remove it.", "点一下食材即可修改或移除。"),
    "kitchen.add_title": ("Add by hand", "手动添加"),
    "kitchen.last_cooked": ("Last cooked, {day}", "上次做菜：{day}"),
    "action.cook": ("What should I cook?", "今天煮什么？"),
    "action.cook_this": ("Cook this", "就做这个"),
    "action.other_dishes": ("Other dishes", "看其他菜"),
    "leaf.in_hand": ("{have} / {total} in hand", "已有 {have} / {total}"),
    "leaf.of": ("/ {total}", "/ {total}"),
    "leaf.in_hand_label": ("in hand", "已有"),
    "leaf.written": ("Written {day}", "{day} 写成"),
    "leaf.rank": ("{n} of {total}", "第 {n} / {total}"),
    "leaf.cooked": ("Cooked {day}", "{day} 已做"),
    "action.scan": ("Scan ingredients", "扫描食材"),
    "action.add": ("Add", "添加"),
    "action.save": ("Save", "保存"),
    "action.remove": ("Remove from kitchen", "从厨房移除"),
    "action.back_kitchen": ("Back to kitchen", "返回厨房"),
    "action.retry": ("Try again", "再试一次"),
    "field.ingredient": ("Ingredient", "食材"),
    "field.amount": ("Amount", "数量"),
    "field.quantity": ("Amount (optional)", "数量（可不填）"),
    "field.category": ("Type", "类别"),
    "pantry.need_name": ("Type an ingredient name first.", "请先输入食材名称。"),
    "pantry.added_one": ("Added {name}.", "已添加{name}。"),
    "pantry.updated_one": ("{name} was already there; its amount is updated.", "{name}已在厨房里，已更新数量。"),
    "pantry.duplicate": ("You already have {name}. Edit that one instead.", "厨房里已有{name}，请直接修改那一项。"),
    "pantry.saved": ("Saved {name}.", "已保存{name}。"),
    "pantry.removed": ("Removed {name}.", "已移除{name}。"),
    "pantry.edit_title": ("Edit ingredient", "修改食材"),
    "cat.produce": ("Vegetables and fruit", "蔬果"),
    "cat.protein": ("Meat, fish, tofu", "肉类、海鲜、豆制品"),
    "cat.dairy_egg": ("Dairy and eggs", "蛋奶"),
    "cat.grain": ("Rice, noodles, bread", "米面主食"),
    "cat.sauce_spice": ("Sauces and spices", "酱料与香料"),
    "cat.other": ("Other", "其他"),
    # scan
    "scan.title": ("Scan ingredients", "扫描食材"),
    "scan.lead": ("Photograph your fridge, shelf or shopping. Up to {n} photos, {mb} MB each.",
                  "拍下冰箱、橱柜或买回来的菜。最多 {n} 张，每张不超过 {mb} MB。"),
    "scan.take": ("Take photo", "拍照"),
    "scan.choose": ("Choose photos", "从相册选择"),
    "scan.remove": ("Remove photo {n}", "删除第 {n} 张照片"),
    "scan.full": ("{n} photos chosen, the most for one scan.", "已选 {n} 张，一次最多就这么多。"),
    "scan.chosen": ("{n} photos chosen", "已选 {n} 张"),
    "scan.chosen_one": ("1 photo chosen", None),
    "scan.submit": ("Find ingredients", "识别食材"),
    "scan.busy": ("Looking at your photos. This takes up to half a minute.", "正在查看照片，最多需要半分钟。"),
    "scan.tips_title": ("For a better result", "拍得更准的小贴士"),
    "scan.tip1": ("Open the door wide and switch on a light.", "把门开大，把灯打开。"),
    "scan.tip2": ("Turn labels towards the camera.", "让标签朝向镜头。"),
    "scan.tip3": ("One shelf per photo beats one photo of everything.", "一层拍一张，比一张拍全部更准。"),
    "scan.privacy": ("Photos are sent to {service} to be read and are not kept by this app.",
                     "照片会发送给 {service} 识别，本应用不会保存。"),
    "scan.no_photo": ("Choose at least one photo first.", "请先选择至少一张照片。"),
    "scan.too_many": ("That's more than {n} photos. Choose {n} or fewer.", "超过 {n} 张了，请选择不多于 {n} 张。"),
    "scan.too_big": ("One photo is over {mb} MB. Choose a smaller one or retake it.",
                     "有照片超过 {mb} MB，请换一张或重新拍摄。"),
    "scan.not_image": ("{name} isn't a photo this app can read. Use JPEG, PNG, WebP or HEIC.",
                       "无法读取 {name}。请使用 JPEG、PNG、WebP 或 HEIC 格式的照片。"),
    "scan.nothing_found": ("No ingredients could be seen in that photo. Try a closer, brighter shot.",
                           "照片里没有识别到食材。请靠近一些、光线亮一些再拍。"),
    "scan.review_title": ("Check the list", "核对清单"),
    "scan.review_lead": ("Found {n} ingredients. Fix names and amounts, and untick anything that's wrong.",
                         "识别到 {n} 种食材。请改正名称和数量，并取消勾选不对的项目。"),
    "scan.review_lead_one": ("Found 1 ingredient. Fix its name and amount, or untick it if it's wrong.", None),
    "scan.photo_alt": ("Photo {n}, with a numbered box around each ingredient found", "第 {n} 张照片，识别到的食材已用编号方框标出"),
    "scan.boxes_hint": ("The numbers on the photo match the list below. Red boxes are guesses.", "照片上的编号与下面的清单对应，红框表示不确定。"),
    "scan.unsure": ("Not sure", "不确定"),
    "scan.keep": ("Keep {name}", "保留{name}"),
    "scan.keep_new": ("Keep added ingredient {n}", "保留新增食材 {n}"),
    "scan.add_missed": ("Anything missed? Add it here.", "有漏掉的吗？在这里补上。"),
    "scan.save": ("Add to my kitchen", "加入我的厨房"),
    "scan.cook_now": ("Cook with just these", "只用这些来做菜"),
    "scan.none_kept": ("Nothing was ticked, so nothing was added. Scan again and tick the items to keep.",
                       "没有勾选任何食材，所以没有添加。请重新扫描，并勾选要保留的项目。"),
    "scan.saved": ("Added to your kitchen: {added} new, {updated} updated.", "已加入厨房：新增 {added} 种，更新 {updated} 种。"),
    "scan.rescan": ("Scan again", "重新扫描"),
    # cook
    "cook.title": ("What should I cook?", "今天煮什么？"),
    "cook.source": ("Cook from", "用哪些食材"),
    "cook.source_pantry": ("My kitchen ({n} ingredients)", "我的厨房（{n} 种食材）"),
    "cook.source_pantry_one": ("My kitchen (1 ingredient)", None),
    "cook.source_custom": ("A list I type", "我自己输入"),
    "cook.custom_label": ("Ingredients, one per line", "食材，每行一种"),
    "cook.time": ("Time I have", "可用时间"),
    "cook.minutes": ("{n} min", "{n} 分钟"),
    "cook.any_time": ("No rush", "不赶时间"),
    "cook.cuisine": ("Cuisine", "菜系"),
    "cook.any": ("Anything", "都可以"),
    "cook.meal": ("Meal", "哪一餐"),
    "cook.servings": ("Servings", "几人份"),
    "cook.extras": ("It's fine if I need to buy a few things", "需要再买几样也可以"),
    "cook.submit": ("Suggest dishes", "推荐菜式"),
    "cook.busy": ("Thinking about what suits your kitchen. This takes up to half a minute.",
                  "正在根据你的食材想菜式，最多需要半分钟。"),
    "cook.empty_pantry": ("Your kitchen has no ingredients yet. Scan a photo, add some by hand, or type a list here.",
                          "厨房里还没有食材。请先扫描、手动添加，或在这里输入清单。"),
    "cook.empty_custom": ("Type at least one ingredient, one per line.", "请至少输入一种食材，每行一种。"),
    "cook.no_ideas": ("No dishes came back this time. Loosen the time or cuisine and try again.",
                      "这次没有得到推荐。放宽时间或菜系后再试一次。"),
    "cook.following": ("Following your profile: {rules}.", "已按你的资料遵守：{rules}。"),
    "cook.no_rules": ("No diet or allergies set.", "尚未设置饮食习惯或过敏。"),
    "cook.change_rules": ("Change in profile", "到个人资料修改"),
    "cuisine.malaysian": ("Malaysian", "马来西亚菜"),
    "cuisine.chinese": ("Chinese", "中餐"),
    "cuisine.indian": ("Indian", "印度菜"),
    "cuisine.thai": ("Thai", "泰国菜"),
    "cuisine.japanese": ("Japanese", "日本料理"),
    "cuisine.korean": ("Korean", "韩国料理"),
    "cuisine.western": ("Western", "西餐"),
    "cuisine.italian": ("Italian", "意大利菜"),
    "meal.breakfast": ("Breakfast", "早餐"),
    "meal.lunch": ("Lunch", "午餐"),
    "meal.dinner": ("Dinner", "晚餐"),
    "meal.snack": ("Snack", "小吃"),
    # ideas
    "ideas.title": ("Dishes for your kitchen", "适合你厨房的菜式"),
    "ideas.lead": ("{n} ideas, closest match first.", "{n} 个主意，最匹配的排在前面。"),
    "ideas.lead_one": ("1 idea came back.", None),
    "ideas.best": ("Best match", "最匹配"),
    "ideas.have": ("have", "已有"),
    "ideas.get_recipe": ("Get the recipe", "查看做法"),
    "ideas.busy": ("Writing the recipe. This takes up to half a minute.", "正在写做法，最多需要半分钟。"),
    "ideas.change": ("Change my choices", "修改条件"),
    "ideas.more": ("Suggest different dishes", "换一批"),
    "difficulty.easy": ("Easy", "简单"),
    "difficulty.medium": ("Medium", "中等"),
    "difficulty.hard": ("Hard", "较难"),
    # warnings
    "warn.title": ("Check before cooking", "下锅前请确认"),
    "warn.line": ("{ingredient} may not fit: {rule}", "{ingredient}可能不符合：{rule}"),
    "warn.footer": ("This check can miss things. Always read labels if you have an allergy.",
                    "这项检查可能有遗漏。如有过敏，请务必查看食品标签。"),
    "allergen.peanut": ("Peanuts", "花生"),
    "allergen.tree_nut": ("Tree nuts", "坚果"),
    "allergen.shellfish": ("Shellfish", "甲壳与贝类"),
    "allergen.fish": ("Fish", "鱼类"),
    "allergen.egg": ("Eggs", "蛋类"),
    "allergen.dairy": ("Dairy", "奶制品"),
    "allergen.soy": ("Soy", "大豆"),
    "allergen.gluten": ("Gluten", "麸质"),
    "allergen.sesame": ("Sesame", "芝麻"),
    "diet.halal": ("Halal", "清真"),
    "diet.no_pork": ("No pork", "不吃猪肉"),
    "diet.no_beef": ("No beef", "不吃牛肉"),
    "diet.vegetarian": ("Vegetarian", "素食（可蛋奶）"),
    "diet.vegan": ("Vegan", "纯素"),
    "diet.pescatarian": ("Pescatarian", "鱼素"),
    # recipe
    "recipe.servings": ("Serves {n}", "{n} 人份"),
    "recipe.ingredients": ("Ingredients", "食材"),
    "recipe.need": ("to buy", "要买"),
    "recipe.steps": ("Method", "做法"),
    "recipe.tips": ("Tips", "小贴士"),
    "recipe.subs": ("If you're missing something", "缺食材时的替代"),
    "recipe.save": ("Save recipe", "收藏食谱"),
    "recipe.unsave": ("Remove from saved", "取消收藏"),
    "recipe.saved": ("Recipe saved.", "已收藏。"),
    "recipe.unsaved": ("Removed from saved.", "已取消收藏。"),
    "recipe.cooked_title": ("I cooked this", "我做了这道菜"),
    "recipe.rating": ("How was it? 1 is not again, 5 is loved it.", "味道如何？1 是不会再做，5 是非常喜欢。"),
    "recipe.no_rating": ("Skip", "不评分"),
    "recipe.used_up": ("Used in this dish. Ticked ingredients are removed from your kitchen; untick anything you still have.",
                       "这道菜用到的食材。勾选的会从厨房移除；还有剩的请取消勾选。"),
    "recipe.log": ("Log as cooked", "记录为已做"),
    "recipe.cooked_plain": ("Logged as cooked.", "已记录。"),
    "recipe.cooked_removed": ("Logged as cooked. {n} ingredients removed from your kitchen.", "已记录，并从厨房移除 {n} 种食材。"),
    "recipe.cooked_removed_one": ("Logged as cooked. 1 ingredient removed from your kitchen.", None),
    "recipe.times_cooked": ("Cooked {n} times", "做过 {n} 次"),
    "recipe.times_cooked_one": ("Cooked once", None),
    "recipe.delete": ("Delete recipe", "删除食谱"),
    "recipe.deleted": ("Recipe deleted.", "食谱已删除。"),
    "recipe.bad_request": ("That dish couldn't be opened. Ask for suggestions again.", "无法打开这道菜，请重新获取推荐。"),
    "recipe.ai_note": ("Written by AI. Check cooking times and labels yourself.", "由 AI 生成，烹调时间与食品标签请自行确认。"),
    "recipe.error_title": ("The recipe couldn't be written", "这次没写出做法"),
    # saved
    "saved.title": ("Saved recipes", "收藏的食谱"),
    "saved.empty": ("Nothing saved yet. Open a recipe and choose Save recipe to keep it here.",
                    "还没有收藏。打开食谱并点“收藏食谱”，就会出现在这里。"),
    "saved.history": ("Cooking history", "做菜记录"),
    "saved.history_empty": ("When you log a dish as cooked, it shows up here and shapes later suggestions.",
                            "记录做过的菜后会显示在这里，并用于之后的推荐。"),
    "saved.rated": ("Rated {n} of 5", "评分 {n}/5"),
    # profile
    "profile.title": ("Profile", "个人资料"),
    "profile.signed_in": ("Signed in as {name}", "当前账号：{name}"),
    "profile.language": ("Language", "语言"),
    "profile.diet": ("Diet", "饮食习惯"),
    "profile.allergies": ("Allergies", "过敏"),
    "profile.other_allergies": ("Other allergies, separated by commas", "其他过敏原，用逗号分隔"),
    "profile.allergy_note": ("The AI is told to avoid these, and recipes are checked again afterwards. "
                             "Neither is a guarantee.",
                             "AI 会被要求避开这些食材，生成后还会再检查一次，但两者都无法保证万无一失。"),
    "profile.dislikes": ("Foods I don't like", "不喜欢的食物"),
    "profile.cuisines": ("Cuisines I enjoy", "喜欢的菜系"),
    "profile.skill": ("Cooking skill", "厨艺"),
    "skill.beginner": ("Beginner", "新手"),
    "skill.home": ("Home cook", "家常水平"),
    "skill.confident": ("Confident", "得心应手"),
    "profile.save": ("Save profile", "保存资料"),
    "profile.saved": ("Profile saved.", "资料已保存。"),
    "profile.password_title": ("Change password", "修改密码"),
    "profile.current_password": ("Current password", "当前密码"),
    "profile.new_password": ("New password (at least {n} characters)", "新密码（至少 {n} 位）"),
    "profile.change_password": ("Change password", "修改密码"),
    "profile.wrong_password": ("The current password isn't right. Nothing was changed.", "当前密码不正确，未作修改。"),
    "profile.short_password": ("The new password needs at least {n} characters.", "新密码至少需要 {n} 位。"),
    "profile.password_changed": ("Password changed. Other devices have been signed out.", "密码已修改，其他设备已退出登录。"),
    "profile.sign_out": ("Sign out", "退出登录"),
    # AI errors
    "ai.busy": ("The AI service is busy or took too long. Wait a moment and try again.",
                "AI 服务繁忙或响应超时，请稍等片刻再试。"),
    "ai.config": ("The AI service rejected the request. Ask whoever runs the server to check the Gemini key "
                  "and model name.", "AI 服务拒绝了请求。请让服务器管理员检查 Gemini 密钥和模型名称。"),
    "ai.blocked": ("The AI gave no answer for that. Try a different photo or different choices.",
                   "AI 没有给出回答，请换一张照片或调整条件再试。"),
    "ai.failed": ("Something went wrong talking to the AI. Try again.", "与 AI 通讯时出错，请再试一次。"),
    # not found
    "notfound.title": ("That page isn't here", "找不到这个页面"),
    "notfound.body": ("It may have been deleted, or the link is wrong.", "它可能已被删除，或链接有误。"),
}

KNOWN_RULES: frozenset[str] = frozenset(
    key.split(".", 1)[1] for key in STRINGS if key.startswith(("allergen.", "diet."))
)

_WEEKDAYS_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_WEEKDAYS_ZH = "一二三四五六日"


def t(lang: str, key: str, **values: Any) -> str:
    """Translate a key. Unknown keys come back as the key itself."""
    index = 1 if lang == "zh" else 0
    entry = STRINGS.get(key)
    if entry is None:
        return key
    if values.get("n") == 1:
        single = STRINGS.get(f"{key}_one")
        if single is not None and single[index] is not None:
            entry = single
    text = entry[index] or entry[0]
    return text.format(**values) if values else text


def rule_label(lang: str, rule: str, custom: bool = False) -> str:
    """Display name for an allergy or diet rule."""
    if custom:
        return rule
    for prefix in ("allergen", "diet"):
        if f"{prefix}.{rule}" in STRINGS:
            return t(lang, f"{prefix}.{rule}")
    return rule


def format_day(moment: datetime, lang: str) -> str:
    if lang == "zh":
        return f"{moment.month}月{moment.day}日 周{_WEEKDAYS_ZH[moment.weekday()]}"
    return f"{_WEEKDAYS_EN[moment.weekday()]} {moment.day} {_MONTHS_EN[moment.month - 1]}"
