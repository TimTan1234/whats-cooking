# What's Cooking

A private recipe app for one household. Photograph your fridge or shopping, correct the ingredient list, and get dishes you can cook with what you have, written as full recipes.

- **Scan**: one or more photos become an editable ingredient list.
- **Kitchen**: each person keeps their own pantry, added to by scanning or by hand.
- **Cook**: suggestions ranked by how much you already have, following your diet, allergies, time, cuisine and skill, and shaped by what you have saved and cooked before.
- **Recipes**: full method, what to buy, substitutions; save a recipe, log it as cooked, rate it.
- English and Simplified Chinese, chosen per person.
- Username and password sign-in for a handful of accounts. No public sign-up.

Built with Python (FastAPI, Jinja2, SQLite) and Google Gemini, called through the Coarena Model API or Google's own API. Runs as one Docker container.

## Run it

Requires Docker with Compose.

```bash
cp .env.example .env          # then put your Coarena key in AI_API_KEY
docker compose up -d --build
docker compose exec app python -m app.cli create-user mei
```

Open `http://<server>:8000` and sign in. Repeat `create-user` for each person (`--lang zh` starts them in Chinese).

The AI runs through any OpenAI-compatible endpoint (`AI_BASE_URL` and `AI_API_KEY`); the example settings point at the [Coarena Model API](https://coarena.ai), whose free tier includes Gemini 3.8 Flash. To call Google directly instead, leave `AI_BASE_URL` empty and set `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/). With no key the app runs in demo mode: every page says so, and ingredients and recipes are fixed samples.

## Accounts

```bash
docker compose exec app python -m app.cli list-users
docker compose exec app python -m app.cli reset-password mei
docker compose exec app python -m app.cli delete-user mei
```

People change their own password, language, diet and allergies under their name at the top right. Changing a password signs out that person's other devices. Five wrong passwords lock a username for five minutes.

## Settings

All settings are environment variables, read from `.env`.

| Variable | Default | Meaning |
|---|---|---|
| `AI_BASE_URL` | empty | OpenAI-compatible endpoint, e.g. `https://coarena.ai/api/v1`. Empty means Google's Gemini API. |
| `AI_API_KEY` | empty | Key for `AI_BASE_URL`. |
| `GEMINI_API_KEY` | empty | Key for Google's Gemini API, used when `AI_BASE_URL` is empty. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Model for suggestions and recipes (`gemini-3-8-flash` on Coarena). |
| `GEMINI_VISION_MODEL` | `gemini-4-hydrogen` | Model that reads the photos. Empty uses `GEMINI_MODEL`. The example settings use `gemini-3-8-flash`. |
| `GEMINI_VISION_THINKING` | empty | Thinking effort for photos: `low`, `medium` or `high`. Empty uses the model's default. The example settings use `high`. |
| `PORT` | `8000` | Port on the host. |
| `COOKIE_SECURE` | `0` | Set to `1` when served over HTTPS. |
| `SECRET_KEY` | generated | Session signing key. Generated on first start and kept in the data volume. |
| `TIMEZONE` | `Asia/Kuala_Lumpur` | Time zone for dates on screen. |
| `MAX_PHOTOS` / `MAX_UPLOAD_MB` | `4` / `10` | Photo limits per scan. |
| `AI_MOCK` | `0` | `1` forces demo mode. |

## Photo accuracy

Each photo is read on its own by the photo model, which returns a name, an amount, a confidence, what it saw, and a box around each ingredient. The review screen shows every photo with numbered boxes that match the list, so a wrong or missed item is quick to spot. Guesses are boxed in red and start unticked.

What improves the result, in order of effect:

1. One shelf or area per photo, in good light, with labels facing the camera.
2. `GEMINI_VISION_THINKING=high` (the example setting): it also picks up unlabelled items, for a few seconds more per photo.
3. A stronger photo model: `GEMINI_VISION_MODEL=gemini-4-carbon`, which needs paid credits on Coarena.

To compare settings on your own photos without changing anything:

```bash
docker compose run --rm -v "$PWD/photos:/photos:ro" app \
  python -m app.cli scan-test /photos/fridge.jpg --model gemini-4-carbon --thinking high
```

It prints each ingredient found with its confidence and the reason, and how long the scan took.

## The leaf numeral

Every dish leaf (tonight, the ideas, the recipe) leads with how many of its ingredients are already in the kitchen. Basics such as salt, pepper, sugar, cooking oil and water are assumed to be there: they are never counted and never shown as "to buy", so the same dish shows the same count on every screen. When an ingredient is used up after the ideas were made, tonight's leaf and the ideas move it to "to buy" and the count drops.

## Using up ingredients

Logging a dish as cooked lists the kitchen ingredients it used, and takes that dish off tonight's leaf. Fresh items are ticked for removal; rice, noodles, sauces and spices are listed unticked because they usually outlast one dish. Untick anything you still have, or tick a staple you finished.

## Data and backups

Everything lives in the `whatscooking-data` volume: the SQLite database `recipie.db` and the session key. Photos are sent to the AI service (Coarena, which passes them to Google) for reading and are not stored by the app.

```bash
docker compose cp app:/data/recipie.db ./recipie-backup.db
```

## Putting it on the internet

On a home network, plain `http://` works, including taking photos from a phone. If the server is reachable from outside, put it behind an HTTPS reverse proxy (Caddy, nginx, Traefik), set `COOKIE_SECURE=1`, and let the proxy cap request bodies at about 45 MB. The proxy must pass the original `Host` header (or set `X-Forwarded-Host`); form posts from a different origin are refused.

## Tests

```bash
docker compose run --rm app pytest
```

Tests use the demo AI and a temporary database, so they need no key and no network.

## Layout

```
app/
  main.py        application factory, middleware, error pages
  config.py      settings
  models.py      tables: User, PantryItem, Recipe, CookLog, IdeaSet
  auth.py        passwords, sign-in, lockout
  cli.py         account commands
  i18n.py        all screen text, English and Chinese
  ai/            OpenAI-compatible and Google Gemini clients, prompts, demo provider
  services/      photos, pantry, recommendations, allergy and diet check
  routers/       one module per tab
  templates/     Jinja2 pages
  static/        app.css, app.js, font, icon
tests/
```

Prompts are in `app/ai/prompts.py`. Screen text is in `app/i18n.py`.

## Limitations

- Recipes are written by an AI. Diet and allergy rules are sent with every request and each recipe is scanned again for common problem ingredients, with a warning on the page when one is found. That scan can miss things; anyone with an allergy still needs to read labels.
- Ingredient detection is an estimate. The review step exists so the list can be corrected before it is used. Each photo is one request to the photo model, so four photos cost four requests.
- Screen text is translated; ingredient names stay in whatever language they were entered or detected in.
- The login lockout is kept in memory and resets when the container restarts.
- The database schema is created on start. There is no migration tool, so a later change to an existing table needs a manual step.
