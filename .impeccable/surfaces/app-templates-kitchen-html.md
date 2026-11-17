---
version: 1
slug: "app-templates-kitchen-html"
primary_target: "app/templates/kitchen.html"
related_targets: ["app/templates/base.html","app/static/app.css"]
---

# App shell and core screens (What's Cooking)

Scope: every signed-in screen plus sign-in. Mode: Operate. Mobile-first; phone in the kitchen.

Audience and job: a household cook deciding what to cook from what is in the house, then cooking it.
Tasks: scan photos and correct the list; keep a pantry; ask for dishes; open a recipe; save it; log it as cooked.
Constraints: server-rendered Jinja, one CSS file, a few lines of plain JS, strict CSP (no inline style or script), English and Simplified Chinese, self-hosted fonts. Screens may be restructured; every feature, route and form field stays. Must not feel playful.

## Direction contract

THESIS: Tonight is a leaf torn from the kitchen-wall almanac: the date-sized numeral is how much of the dish you already have. Refuses the photo-card recipe feed and the cute cooking app.

OWN-WORLD: Newsprint-white leaves on a grey wall ground, almanac black for text, rules and the primary button, almanac red rationed to the numeral, the active tab and state (to buy, allergy warnings, the cooked mark), almanac green for confirmations. Square corners, a red head-rule on every leaf, 1.5px black rules, small-print columns. Barlow for text, Barlow Condensed in caps for leaf heads, meta lines, tabs and numerals.

STORY: The cook sees tonight's dish and the count in hand at a glance, sees in red the one thing to buy, picks it, and cooks from the same leaf.

FIRST VIEWPORT: Black header with name and the account. Tonight's leaf: date and day line, a huge red condensed numeral "5" with "/ 6 in hand", dish title under a black rule, a two-column small-print ingredient list with the missing line in red, a meta foot line. Then Get the recipe and Other dishes side by side, Scan ingredients below, text tab bar at the thumb.

FORM: Chosen by the user from the decision round (the pick card, first on the grounded list). seed:44a4729c89392e0c. Signature interaction: the leaf numeral on every dish leaf (tonight, ideas, recipe); logging a dish as cooked tears the leaf, the one authored motion.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved

- Not yet inspected as rendered: the build session had no browser, Python packages or Docker access. Check 390 and 1440 widths, Chinese, the tear motion and the safe-area tab bar on a device.
- Chinese uses the platform's CJK fonts; only Latin Barlow files are self-hosted.
