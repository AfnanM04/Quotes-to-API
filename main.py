from collections import Counter
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query

from .models import Quote, QuoteList, TagCount
from .scraper import QuotesScraper, UpstreamError

app = FastAPI(title="Quotes to Scrape API", version="1.0.0")
scraper = QuotesScraper()

@lru_cache(maxsize=32)
def cached_page(page: int):
    return scraper.list_quotes(page)

def safe_page(page: int):
    try:
        return cached_page(page)
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

def filtered_quotes(page: int, author: str | None, tag: str | None):
    items, has_next = safe_page(page)
    if author:
        items = [q for q in items if q["author"].lower() == author.lower()]
    if tag:
        items = [q for q in items if tag.lower() in {t.lower() for t in q["tags"]}]
    return items, has_next

@app.get("/health")
def health():
    return {"status": "ok", "upstream": "quotes.toscrape.com"}

@app.get("/api/quotes", response_model=QuoteList)
def list_quotes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=10),
    author: str | None = None,
    tag: str | None = None,
):
    items, has_next = filtered_quotes(page, author, tag)
    return QuoteList(items=[Quote(**q) for q in items[:limit]], page=page, limit=limit, has_next=has_next)

@app.get("/api/quotes/{quote_id}", response_model=Quote)
def get_quote(quote_id: str):
    for page in range(1, 11):
        items, _ = safe_page(page)
        for item in items:
            if item["id"] == quote_id:
                return Quote(**item)
    raise HTTPException(status_code=404, detail="Quote not found")

@app.get("/api/authors/{author}/quotes", response_model=QuoteList)
def author_quotes(author: str, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=10)):
    items, has_next = filtered_quotes(page, author, None)
    return QuoteList(items=[Quote(**q) for q in items[:limit]], page=page, limit=limit, has_next=has_next)

@app.get("/api/tags", response_model=list[TagCount])
def tags():
    all_items = []
    for page in range(1, 11):
        items, has_next = safe_page(page)
        all_items.extend(items)
        if not has_next:
            break
    counts = Counter(tag for item in all_items for tag in item["tags"])
    return [TagCount(tag=t, count=c) for t, c in sorted(counts.items())]
