---
name: What's Cooking
description: Tonight's dish as a leaf torn from the kitchen-wall almanac, numbered by how much of it is already in the house.
colors:
  almanac-red: "#c81e28"
  almanac-red-deep: "#9e161e"
  red-wash: "#fbe9e9"
  almanac-green: "#1d6b3a"
  green-wash: "#e3efe6"
  almanac-black: "#161616"
  ink-soft: "#3a3a36"
  mute: "#55554f"
  rule-grey: "#cdcdc5"
  wall-grey: "#e6e6e0"
  newsprint-leaf: "#fbfbf8"
  on-ink: "#ffffff"
  on-ink-mute: "#b8b8b0"
typography:
  numeral-display:
    fontFamily: "Barlow Condensed, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "clamp(5rem, min(32vw, 16svh), 8rem)"
    fontWeight: 800
    lineHeight: 0.8
    letterSpacing: "-0.02em"
    fontFeature: "tnum, lnum"
  numeral:
    fontFamily: "Barlow Condensed, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "4.5rem"
    fontWeight: 800
    lineHeight: 0.8
    letterSpacing: "-0.02em"
    fontFeature: "tnum, lnum"
  headline:
    fontFamily: "Barlow, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.1
  title:
    fontFamily: "Barlow, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.15
  title-large:
    fontFamily: "Barlow, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.12
  leaf-head:
    fontFamily: "Barlow Condensed, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.08em"
  section-head:
    fontFamily: "Barlow Condensed, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "0.08em"
  body:
    fontFamily: "Barlow, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "tnum"
  body-small:
    fontFamily: "Barlow, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.45
  button:
    fontFamily: "Barlow, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.15
  label:
    fontFamily: "Barlow Condensed, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
  tag:
    fontFamily: "Barlow Condensed, PingFang SC, Hiragino Sans GB, Noto Sans SC, Noto Sans CJK SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.08em"
rounded:
  square: "0px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  section: "40px"
  tap: "3.5rem"
  field: "52px"
  tabbar: "4rem"
  measure: "38rem"
components:
  button-primary:
    backgroundColor: "{colors.almanac-black}"
    textColor: "{colors.on-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.square}"
    padding: "8px 16px"
    height: "{spacing.tap}"
    width: "100%"
  button-primary-hover:
    backgroundColor: "{colors.ink-soft}"
    textColor: "{colors.on-ink}"
  button-secondary:
    backgroundColor: "{colors.newsprint-leaf}"
    textColor: "{colors.almanac-black}"
    typography: "{typography.button}"
    rounded: "{rounded.square}"
    padding: "8px 16px"
    height: "{spacing.tap}"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.almanac-black}"
    typography: "{typography.button}"
    rounded: "{rounded.square}"
    padding: "8px 16px"
    height: "{spacing.tap}"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.almanac-red-deep}"
    typography: "{typography.button}"
    rounded: "{rounded.square}"
    padding: "8px 16px"
    height: "{spacing.tap}"
  button-danger-hover:
    backgroundColor: "{colors.red-wash}"
  input:
    backgroundColor: "{colors.newsprint-leaf}"
    textColor: "{colors.almanac-black}"
    typography: "{typography.body}"
    rounded: "{rounded.square}"
    padding: "0 12px"
    height: "{spacing.field}"
  chip:
    backgroundColor: "{colors.newsprint-leaf}"
    textColor: "{colors.almanac-black}"
    rounded: "{rounded.square}"
    padding: "6px 16px"
    height: "48px"
  chip-selected:
    backgroundColor: "{colors.almanac-black}"
    textColor: "{colors.on-ink}"
  masthead:
    backgroundColor: "{colors.almanac-black}"
    textColor: "{colors.on-ink}"
    height: "60px"
  tab:
    backgroundColor: "{colors.newsprint-leaf}"
    textColor: "{colors.mute}"
    typography: "{typography.label}"
    height: "{spacing.tabbar}"
  tab-active:
    textColor: "{colors.almanac-red}"
  leaf:
    backgroundColor: "{colors.newsprint-leaf}"
    textColor: "{colors.almanac-black}"
    rounded: "{rounded.square}"
    padding: "18px 16px 16px"
  notice-ok:
    backgroundColor: "{colors.green-wash}"
    textColor: "{colors.almanac-green}"
    typography: "{typography.body-small}"
    padding: "12px 14px"
  notice-error:
    backgroundColor: "{colors.red-wash}"
    textColor: "{colors.almanac-red-deep}"
    typography: "{typography.body-small}"
    padding: "12px 14px"
  tag-inked:
    backgroundColor: "{colors.almanac-black}"
    textColor: "{colors.on-ink}"
    typography: "{typography.tag}"
    padding: "4px 8px"
---

# Design System: What's Cooking

## Overview

**Creative North Star: "The Tear-off Almanac"**

Every dish is a leaf torn from the day-by-day almanac that hangs on a kitchen wall. Newsprint-white leaves sit on a flat grey wall; almanac black carries the text, the rules and the primary button; almanac red is rationed to the date-sized numeral, the leaf's head rule, the active tab and state that demands action. The numeral is not a date: it is how many of the dish's ingredients are already in the house, set huge in red condensed figures with "/ 6 in hand" beside it.

The system is printed matter, not app chrome. Corners are square, structure is drawn with 1.5px black rules rather than boxes and shadows, ingredient lists are small print in newspaper columns, and every heading that is not a dish name is condensed caps. It is built for a phone held at arm's length in a kitchen: body text starts at 17px, touch targets at 56px, the tab bar sits at the thumb, and contrast stays high on both the wall and the leaf. English and Simplified Chinese share the same leaves; CJK falls back to the platform's own sans faces with looser tracking and line height.

It refuses the photo-card recipe feed and the cute cooking app. There is no food photography on leaves, no illustration, no rounded softness and no decorative motion; the one authored movement is the leaf tearing off when a dish is logged as cooked.

**Key Characteristics:**
- Newsprint leaves on a grey wall, square everywhere.
- A 6px red head rule and a perforation row crown every leaf.
- The leaf numeral: red Barlow Condensed 800 figures counting what is in hand.
- Black 1.5px rules for structure, 1px grey rules between list lines.
- Condensed uppercase for heads, meta lines, tabs and labels; Barlow sentence case for dish titles and reading text.
- Red means act on this; green means it is done.

## Colors

A three-ink almanac on paper: black does the work, red marks what needs a hand, green confirms, and two greys hold the paper and the wall apart.

### Primary
- **Almanac Red** (`almanac-red`): the leaf numeral, the 6px head rule on every leaf and the scan picker, the active tab (text and its 4px bar), ingredient lines still to buy, the "cooked" stamp, the review flag for unsure detections, the danger button's border and the text caret. Also drawn as the box colour around unsure items on scan previews.
- **Almanac Red Deep** (`almanac-red-deep`): red text on a red wash, where plain red would lose contrast: error notices, allergy warnings, the danger button label.
- **Red Wash** (`red-wash`): the ground of error notices, allergy warnings and the danger button's pressed and hover state.

### Secondary
- **Almanac Green** (`almanac-green`): confirmation text and border, used only on flash notices of level "ok".
- **Green Wash** (`green-wash`): the ground of those confirmation notices.

### Neutral
- **Almanac Black** (`almanac-black`): all text, the masthead, the primary button, 1.5px structural rules, input borders, the selected chip, the checked checkbox, focus outlines, list bullets, inked tags and the box colour around confident detections on scan previews. Also the browser theme colour.
- **Ink Soft** (`ink-soft`): pressed and hover state of black surfaces, the desktop tab rule inside the masthead, the scrollbar thumb.
- **Mute** (`mute`): secondary text: leads, hints, leaf date and rank, the leaf foot meta line, counts, row meta, quantities, placeholders, inactive tabs on the phone tab bar.
- **Rule Grey** (`rule-grey`): 1px separators between list lines, the unfilled track of the busy line, disabled chip borders.
- **Wall Grey** (`wall-grey`): the page ground; also the perforation dots punched through the leaf and the pressed state of outline buttons and tabs.
- **Newsprint Leaf** (`newsprint-leaf`): leaves, inputs, chips, the secondary button, the phone tab bar, the scan picker.
- **On Ink** (`on-ink`): text on black: masthead, primary button, selected chip, inked tags, text selection.
- **On Ink Mute** (`on-ink-mute`): inactive tabs and the language button border inside the black masthead on wide screens.

### Named Rules
**The Rationed Red Rule.** Red appears only where the almanac would print it: the numeral, the head rule, the active tab, and state the cook must act on (to buy, allergy warning, error, cooked, unsure). Never as decoration, never as a large fill.

**The Green Means Done Rule.** Green is reserved for confirmations (flash notices of level "ok"). Meta lines, times and difficulty stay muted grey, including the leaf foot line.

## Typography

**Display Font:** Barlow Condensed 600 / 800 (with PingFang SC, Hiragino Sans GB, Noto Sans SC, Microsoft YaHei, system-ui)
**Body Font:** Barlow 400 / 600 / 700 (same CJK and system fallbacks)

Both families are self-hosted Latin subsets with `font-display: swap`; Barlow 400 and Barlow Condensed 800 are preloaded. Chinese text renders in the platform's CJK sans.

**Character:** a printer's pairing from one family: the condensed cut speaks in caps like an almanac's dateline and numerals, the regular cut reads plainly at kitchen distance. Figures are tabular everywhere.

### Hierarchy
- **Numeral Display** (800, clamp(5rem, min(32vw, 16svh), 8rem), 0.8): tonight's leaf numeral on the kitchen screen; it gives up height on short phones so the dish title stays on the first screen. The "/ total" beside it is 800 at 2rem.
- **Numeral** (800, 4.5rem, 0.8): the numeral on idea and recipe leaves; "/ total" at 1.75rem, the "in hand" label in condensed 600 caps, muted, wrapped to 3.5em.
- **Headline** (Barlow 700, 2rem, 1.1, balanced): page titles outside a leaf.
- **Title** (Barlow 700, 1.5rem, 1.15, balanced): dish titles under the leaf's black rule on idea leaves.
- **Title Large** (Barlow 700, 1.75rem, 1.12, balanced): the dish title on tonight's leaf and on the recipe leaf.
- **Leaf Head** (Condensed 800, 1.375rem, caps): the leaf's own heading ("Tonight") and the brand in the masthead.
- **Section Head** (Condensed 800, 1.25rem, caps, 1.5px black rule beneath): section titles below the leaf. Sub-heads inside leaves and h3 drop to 1rem and 0.9375rem in the same style.
- **Body** (Barlow 400, 1.0625rem, 1.45): reading text. Method steps run at 1.125rem / 1.5; leaf leads at 1.125rem. Lists hold to 68ch.
- **Button** (Barlow 600, 1.125rem, 1.15): button labels in sentence case.
- **Label** (Condensed 600, 0.9375rem, caps, 0.08em): field labels, leaf date and rank, the leaf foot meta line, back links, tabs (1.0625rem on the tab bar).
- **Tag** (Condensed 800, 0.8125rem, caps): inked tags (demo, best match). Two state notes the cook must read at arm's length, in Chinese too, step up to 0.9375rem: the "to buy" note on ingredient lines (Condensed 600) and the "Not sure, tick to keep" flag on scan review rows (Condensed 800, red).

### Named Rules
**The Condensed Caps Rule.** Everything that labels, dates or counts is Barlow Condensed in caps tracked 0.08em; everything that names a dish or is read through is Barlow in sentence case. In Simplified Chinese, tracking drops to 0.02em and body line height rises to 1.65.

## Layout

A single column on a 38rem measure (plus 16px gutters), centred, used identically on phone and laptop. Pages are a leaf followed by ruled sections 40px apart; inside a leaf the rhythm is 10–16px. Action buttons sit in a two-column grid with 10px gaps, a full-width button spanning both columns.

On the phone the four text tabs are a fixed bar at the bottom (4rem plus the safe-area inset) and the masthead is 60px. At 760px and wider the tabs move into the black masthead as an inline row with a 4px red underline on the active tab, the masthead grows to 64px, leaves open to 22px / 24px padding, ingredient lines run in three columns instead of two, and action buttons collapse into one row of equal widths.

Lists are rows on rules rather than cards: pantry, saved recipes and history are 52px-minimum rows separated by 1px grey lines, name left, meta right. Ingredient lines are small print in newspaper columns (2 on phone, 3 wide); amounts are name-left, quantity-right rows; method steps carry a condensed 800 step number in a 2.25rem gutter.

**The Thumb Reach Rule.** Every control is at least 44px tall and every primary control 56px (the `tap` step); fields are 52px; chips and toggles 48px. On phones, a leaf's main actions (Get the recipe, Other dishes, the Cook tab's Find dishes) dock on a wall-grey band directly above the tab bar until the page scrolls to them, so the primary action is always within reach.

## Elevation & Depth

Flat. Nothing casts a shadow. Depth is the difference between the grey wall and the white leaf, and every boundary is a drawn rule. `box-shadow` appears only as an inset rule: the active tab's 4px red bar and the 1.5px inner ring that thickens an outline button's border on hover and press.

**The Flat Leaf Rule.** Leaves are paper on a wall, not cards on a table. Separate surfaces with the wall colour and with rules, never with a drop shadow or a blur.

## Shapes

Square corners on everything: buttons, inputs, selects, chips, checkboxes, leaves, notices, tags, photos. The form language is the printed rule: 6px red across the top of a leaf, 1.5px black under a section head or above a dish title, 1px grey between lines, 4px across the top of a warning. A row of wall-grey perforation dots (9 × 6px pitch) is punched just under each leaf's red head rule. Icons are drawn on a 24px grid with one 2px stroke, square caps and mitred joins, coloured by the text around them. Bullets in plain lists are short 1.5px black dashes.

**The Square Corner Rule.** Radius is zero. A rounded corner anywhere breaks the paper.

## Components

### Buttons
Full-width, square, sentence-case slabs sized for a wet hand.
- **Shape:** square (0px), 1.5px black border, minimum 56px tall, 8px 16px padding, icon and label gapped 10px.
- **Primary:** almanac black with white label. One per screen: Get the recipe, Find dishes, Log it. On the ideas page it goes only to the best match; a dish that may clash with the profile never gets it.
- **Secondary:** newsprint leaf fill with black label, for the paired alternative (Other dishes, Save).
- **Outline:** transparent on the wall with black label, for routes such as Scan ingredients and the icon-only add button (56px square).
- **Danger:** red border, deep red label; red wash on hover and press.
- **Hover / Press:** background changes over 120ms on the system ease. Primary moves to ink soft; secondary and outline gain an inset 1.5px ring (press also drops to the wall colour). Hover styles apply only on hover-capable devices.
- **Busy:** a disabled button drops to 55% opacity with a progress cursor, and a 3px line runs along the foot of the form (black segment sweeping a grey track, 1.4s linear) above a muted status line while the AI works. Only one such request runs at a time: the other waiting buttons on the page are held until it ends.

### Chips
- **Style:** square segments 48px tall, 1.5px black border, leaf fill, Barlow 600. The rating row uses condensed 800 numerals, 48px wide.
- **Dish kind:** Anything and the four common kinds show first, followed by a plain "+ More" chip that opens the rest and then reads "− Fewer", staying in the row so focus is kept; only the chosen kind is ever inked, and a chosen rarer kind opens them on load.
- **State:** the chosen chip is inked in (black fill, white text); disabled chips lose their fill and turn grey.

### Inputs / Fields
- **Style:** 52px tall, 1.5px black border, leaf fill, square, body-size text; textareas start at 8rem; the typed ingredient list on the Cook tab starts at 6.5rem and grows with its lines up to 11rem. Selects carry a black chevron. Labels sit above in condensed caps.
- **Focus:** a 3px black outline flush to the border. Elsewhere focus is a 3px black outline offset 3px (white inside the masthead).
- **Checkbox:** a 28px square with a 2px black border; checked fills black with a white tick.

### Navigation
- **Masthead:** a black band with the brand in condensed 800 caps, a language switch and the account name as square outlined condensed-caps buttons; the account inverts to white when its page is open.
- **Tabs:** four text tabs, condensed caps, no icons. On the phone they sit on a leaf-white bar at the bottom under a black rule; the active tab turns red, goes to 800 weight and carries a 4px red bar along its top. Wide screens move them into the masthead, muted on black, the active one white with a 4px red underline.
- **Back link:** condensed caps with a stroked arrow, 44px tall.

### Notices
- **Confirmation (ok):** green text and 1.5px border on green wash.
- **Error:** deep red on red wash.
- **Field error:** a problem with one field is said at that field: deep red 600 small text with the alert icon under it, a red border on the field, and the field focused and described by the message.
- **Allergy warning:** deep red on red wash with a 4px top border, a condensed caps title with the alert icon, the conflicting ingredients in 600 weight, and the line that the check can miss things. When every idea clashes, one page warning above the leaves names the rules, carries that line and offers different dishes; each leaf then keeps only its title and ingredient lines.
- **Demo banner:** a black-ruled leaf strip led by an inked "demo" tag, shown whenever the app runs without an AI key.

### The Leaf (signature)
The unit every dish is printed on: tonight's dish, each idea, each recipe, the Cook tab's order leaf, and the blank and form leaves.
- **Build:** leaf fill, 6px red head rule, perforation row, 18px 16px 16px padding (22px 24px wide).
- **Head:** the leaf's name or rank on the left, the date or a badge on the right, all in condensed caps; "best match" is an inked tag, "cooked" is a 2px red outlined stamp.
- **Numeral:** the red count in hand, then "/ total" in black, then the muted "in hand" label, bottom-aligned. On idea leaves a black condensed-caps tally at 0.9375rem sits under it ("Nothing to buy", "2 to buy"), the measure the ideas are ranked by.
- **Body:** the dish title under a 1.5px black rule, ingredient lines with the ones to buy in red 600 and a "need" note, then the foot meta line (time · difficulty · cuisine) in muted condensed caps.
- **Tear:** logging a dish as cooked tears the leaf: a copy of the leaf rotates away down-left and fades over 900ms on the system ease, and the cooked stamp lands at 520ms over 360ms. With reduced motion the tear is removed and all animation is cut to 1ms.

### The Order Leaf (Cook)
Step 1 of the Cook tab is a leaf titled "Tonight's order". Under the head sits the profile line, diets kept apart from allergies ("Diet: Halal · Avoiding: Eggs." / "饮食：清真 · 避开：蛋类。") with a Change in profile link, then the source as two chips: the kitchen count in condensed 800 figures with "in your kitchen", and "A list I type", which opens the list field. While the kitchen is the source, one muted line under the chips names its first five items ("… and 3 more.") with an "Edit in Kitchen" link to the pantry. An empty kitchen replaces the chips with a condensed-caps "empty" line and an outline Scan button. A 1.5px black rule leads to the kind-of-dish chips (two even columns on a phone, three from 560px) and the two-line craving field, which stays above the docked button at scroll 0 so the product's own question is never behind it. Time, cuisine, meal, servings and extras fold into one muted condensed-caps line below them ("No rush · Any cuisine · 2 people · Buying a few is fine") with a Change control that opens them in place,; they carry over from the last request, while dish and craving start fresh each time unless an order is still open (Back from the questions). "Not sure?" with an outline Pick for me button sits below the leaf and its docked button, with no explainer line, and a small underlined "Not sure? Pick for me" line at the end of the leaf head submits the same request, saying "Picking…" while it works; the count stays black, since the red numeral belongs to dishes.

When the AI asks questions, they continue on the same leaf: the same head with "Step 2 of 2" where the date was, then the **order stub**, one muted condensed-caps line of what was asked for (dish, the craving in quotes and in the user's own sentence case, the source count, time, cuisine, meal), a 1.5px black rule, a condensed sub-head ("2 quick questions") and the questions in sentence case, each question's answers followed by "Either is fine", pre-selected but drawn quietly (wall-grey fill with an inset rule) so only a real answer is inked. Find dishes stays docked below the leaf, and a "Change my choices" back link under it is the one way back to step 1. On step 1 the docked button reads Next. The ideas page repeats the same stub under its lead, with a Change link, with the answers added ("How spicy? A little"), between two 1px grey rules; dishes from Today for you have no stub.

### Scan Review
Photos sit in a horizontal snap strip on black, 15rem tall on phones and 20rem from 760px, each 85% of the column wide so the next one peeks in at the edge; with more than one photo, a muted condensed "1 / 3" count sits under each photo, clear of the numbered box tags. Each detection is drawn on the preview as a numbered box, black when confident and red when unsure, and the review list repeats those numbers in condensed 800 beside a checkbox, an editable name and quantity, and a red condensed-caps flag for unsure items. An unticked row stays editable but its fields turn muted and struck through until it is ticked again or focused. Below 560px each row stacks: the name takes the full width and the amount sits beneath it; from 560px, name and amount share one line.

## Do's and Don'ts

### Do:
- **Do** put every dish on a leaf with the red head rule, the perforation and the numeral of ingredients in hand.
- **Do** keep red to the numeral, the head rule, the active tab and actionable state; use deep red on red wash.
- **Do** keep green for confirmations only, and set meta lines in muted grey.
- **Do** draw structure with rules: 1.5px black for structure, 1px grey between lines.
- **Do** set labels, dates, tabs and counts in Barlow Condensed caps at 0.08em, and dish names and reading text in Barlow sentence case.
- **Do** keep primary controls at least 56px tall and body text at 1.0625rem or larger.
- **Do** keep the tear as the one authored motion, and honour reduced motion.

### Don't:
- **Don't** round a corner.
- **Don't** cast drop shadows or blur; inset box-shadow is only for drawn rules (the tab bar, the button ring).
- **Don't** put food photography or illustration on a leaf; the only photos are the user's own scans on the review screen.
- **Don't** use red as decoration or as a large fill.
- **Don't** use green for meta, tags or anything that is not a confirmation.
- **Don't** add icons to tabs or decorative glyphs to headings; icons are stroked SVGs used only beside an action or a warning.

## Known Issues

- The build has not been inspected as rendered: no browser was available in the build session, so every value here is read from source, not from computed styles or screenshots.
- The number tags on scan previews are drawn with Pillow's default font, not Barlow Condensed.
- `notice-info` and `notice-success` are styled green alongside `notice-ok`, but the app only emits the levels "ok" and "error".
