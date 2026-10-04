# Quotes to Scrape → JSON API

A small, read-only API layer built over the public **Quotes to Scrape** website. The target exposes quote data as HTML pages rather than a developer-facing JSON API. This project observes that public page structure and provides a stable JSON interface for clients.

Target: https://quotes.toscrape.com/

## Why this target

Quotes to Scrape is a public scraping-practice site. The implementation only requests publicly accessible pages, performs read-only GETs, and uses no authentication, private data, access-control bypass, CAPTCHA solving, proxy rotation, or other evasion techniques.

The page structure observed during development contains quote text, author, tags, and a next-page link. See the public page at https://quotes.toscrape.com/page/1/.

## What I built

FastAPI service exposing:

- `GET /health` — service health
- `GET /api/quotes?page=1&limit=10` — paginated quotes
- `GET /api/quotes?page=1&author=Albert%20Einstein` — filter by author
- `GET /api/quotes?page=1&tag=life` — filter by tag
- `GET /api/quotes/{id}` — retrieve one quote by deterministic ID
- `GET /api/authors/{author}/quotes` — author-specific retrieval
- `GET /api/tags` — tag counts across available pages

Interactive API documentation is available at `/docs` when the server is running.

## Architecture

`Client → FastAPI → validation/filtering → in-process cache → scraper → public HTML → parser → JSON response`

The scraper includes:

- conservative request pacing
- request timeouts
- exponential backoff for transient errors (`429`, `5xx`)
- bounded retries
- a descriptive `502` when the upstream site cannot be reached
- deterministic IDs derived from quote content rather than exposing internal site state

## Setup

Python 3.11+ recommended.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

## Test

```bash
pytest -q
```

The tests use a local HTML fixture for the parser and a mocked upstream response for the API layer, so tests do not depend on live internet access.

## Example requests

```bash
curl "http://127.0.0.1:8000/api/quotes?limit=5"
curl "http://127.0.0.1:8000/api/quotes?author=Albert%20Einstein"
curl "http://127.0.0.1:8000/api/quotes?tag=life"
```

## Guardrails / responsible use

1. Read-only GET requests only.
2. Public pages only; no login or private records.
3. No attempts to defeat rate limits, bot checks, CAPTCHA, or access controls.
4. Conservative request pacing and bounded retries.
5. No credentials or cookies stored in the repository.
6. Test fixtures contain synthetic values.

## Limitations

The API is a wrapper over an **undocumented HTML structure**, not a contractual upstream API. If the site's HTML classes or pagination change, the parser can break. The in-memory cache is also process-local and resets when the service restarts. The implementation intentionally limits author/quote lookup to the first ten pages to keep the demo bounded.

## Long-term fix

The correct production solution would be to obtain an **official API, export, or explicit data-access agreement** from the site owner and depend on a versioned contract instead of reverse-engineering presentation HTML. A production service would also use a shared cache, observability, circuit breaking, schema/version monitoring, and a documented data-retention policy.

## Interview talking points

- I chose a safe, public, read-only target rather than trying to bypass a protected system.
- I separated the scraper from the API layer so the upstream integration can be replaced later.
- I added validation, retries, backoff, request pacing, caching, and tests.
- I deliberately documented the limitation: HTML is not a stable API contract.
- The long-term fix is an official/versioned API or data agreement, not increasingly aggressive scraping.
