from fastapi.testclient import TestClient

from app.main import app, cached_page
from app.scraper import QuotesScraper

class FakeResponse:
    status_code = 200
    text = open("tests/fixtures/page1.html", encoding="utf-8").read()

class FakeSession:
    def get(self, *args, **kwargs):
        return FakeResponse()

def test_parser_and_retry_safe_client():
    scraper = QuotesScraper()
    scraper.session = FakeSession()
    items, has_next = scraper.list_quotes(1)
    assert len(items) == 2
    assert items[0]["author"] == "Alice Example"
    assert "testing" in items[0]["tags"]
    assert has_next is True

def test_list_endpoint(monkeypatch):
    cached_page.cache_clear()
    monkeypatch.setattr("app.main.scraper.list_quotes", lambda page: ([
        {"id":"abc123","text":"Hello","author":"Alice","tags":["x"],"source_url":"fixture"},
        {"id":"def456","text":"World","author":"Bob","tags":["y"],"source_url":"fixture"},
    ], False))
    client = TestClient(app)
    response = client.get("/api/quotes?limit=1&author=Alice")
    assert response.status_code == 200
    assert response.json()["items"][0]["author"] == "Alice"
    cached_page.cache_clear()
