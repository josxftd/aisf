# AISF (ai safety funds)

Where money for AI safety flows, sorted into ~13x research areas, so underfunded spots show.

- **Site:** `index.html`, served by GitHub Pages.
- **Data:** `data/aisf.json`, one record per grant. See `llms.txt` for the schema and codes.
- **Raw sources:** `data/raw/`, refreshed every Sunday by `.github/workflows/fetch-sources.yml`.

## How it updates

1. Sunday evening: a GitHub Action downloads the Coefficient Giving and EA Funds grant files into `data/raw/`.
2. Monday morning: a scheduled Claude task compares the raw files, SFF announcements and Manifund against `data/aisf.json`, classifies new AI-safety grants, and commits the updated file.
3. The site reads `data/aisf.json` on every visit, so it shows the new data as soon as the commit lands.

## Coverage

Coefficient Giving, EA Funds (LTFF, EAIF), Survival and Flourishing Fund, Manifund. Not currently covered: frontier lab internal spending, venture capital, government funding, private donors.
