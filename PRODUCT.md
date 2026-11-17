# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python: FastAPI, server-rendered Jinja2 templates, one plain CSS file and one small plain JavaScript file. No Node, no build step, no front-end framework. SQLite for storage. Google Gemini for photo analysis and recipe writing. Deployed as a Docker (Compose) service on the user's own server. Chosen by the user from offered options.

## Users

A household of 2–3 people in Malaysia, each with their own account. They use the app mainly on a phone while standing in the kitchen — at the fridge, the counter or the stove — often one-handed and sometimes with wet or busy hands. A laptop is secondary.

Their job: decide what to cook with what is already in the house, and then cook it.

## Product Purpose

What's Cooking turns the ingredients a household already has into a meal decision.

- A user photographs their fridge, counter or groceries; the app lists the ingredients it sees and the user corrects the list.
- The app recommends dishes that fit those ingredients, the user's diet and allergies, the time they have, the cuisine they feel like and their skill.
- The app writes the full recipe for the dish they pick.

Success is a user going from "what do we have?" to cooking a dish they are happy with, without typing an ingredient list or searching recipe sites.

## Positioning

It starts from the user's real kitchen, not from a recipe catalogue: the photo and the saved pantry are the input, and every suggestion says how much of it the user already has and what is missing. It is private to one household and runs on their own server.

## Operating Context

- Used in a kitchen: variable light, phone held at arm's length or propped up, attention split with cooking.
- Photos come straight from the phone camera or the photo library.
- AI calls take several seconds; the user is waiting on their feet.
- AI output can be wrong: ingredients may be misread, and a recipe may not respect an allergy. The user reviews detected ingredients before they are used, and allergy conflicts are flagged.
- Each user keeps their own pantry, preferences, saved recipes and cooking history.

## Capabilities and Constraints

- Ingredient detection from one or more photos, with an editable review step.
- Per-user pantry, added to by scanning or by hand.
- Recommendations that consider ingredients on hand, diet and allergies, time, cuisine, skill, and saved pantry and cooking history.
- Before suggesting, the user picks the kind of dish, can say in their own words what they feel like, and answers up to three tap-to-answer questions written by the AI for that request.
- Per-user taste: typed favourite foods, plus dish types, cravings, answers and ratings learned over time. Shown on the profile, where the learned part can be cleared.
- "Today for you": dishes chosen from the user's taste alone, still marked with what the kitchen already has.
- Full recipe generation; save a recipe; mark it cooked and rate it.
- Username and password sign-in. Accounts are created by an administrator command; there is no public sign-up.
- Languages: English and Simplified Chinese. Each user picks one in their profile; screens and generated recipes follow that choice.
- Photos are sent to Google Gemini for analysis and are not stored by the app.
- Without a Gemini API key the app runs in a demo mode with sample responses, and says so on screen.

## Brand Commitments

- Name: **What's Cooking** (chosen by the user). The folder name `recipie` is only a working directory name.
- No existing logo, colours or other brand assets.

## Evidence on Hand

- No real user photos, recipes, testimonials or usage data exist yet. Do not fabricate any.
- Sample ingredients and recipes shown in demo mode are placeholders and must be labelled as such.

## Product Principles

1. Start from what is in the kitchen. The user's ingredients drive the Cook tab; the app never opens with a blank recipe search. "Today for you" is the one place that starts from taste instead, and it still shows what is in hand.
2. The user has the last word. Detected ingredients are a draft the user corrects, and AI recipes are suggestions that carry a visible caution where allergies are involved.
3. Built for a busy pair of hands. Every core step works one-handed on a phone, with few taps and little typing.
4. Say what is missing. A suggestion always shows what the user has and what they would still need.
5. Each person's kitchen is their own. Preferences, pantry and history are per user and never mix.

## Accessibility & Inclusion

- Readable at arm's length in poor kitchen light: generous text size and strong contrast.
- Large touch targets for wet or occupied hands.
- Full support for Simplified Chinese text alongside English, including fonts and line height that suit both.
