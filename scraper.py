import hashlib
import time
from dataclasses import dataclass
from urllib.parse import quote as urlquote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com"

@dataclass
class ScraperConfig:
    min_interval_seconds: float = 0.5
    timeout_seconds: float = 10.0
    max_retries: int = 3

class UpstreamError(RuntimeError):
    pass

class QuotesScraper:
    def __init__(self, config: ScraperConfig | None = None, session=None):
        self.config = config or ScraperConfig()
        self.session = session or requests.Session()
        self._last_request = 0.0

    def _get(self, path: str):
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.config.min_interval_seconds:
            time.sleep(self.config.min_interval_seconds - elapsed)

        url = BASE_URL + path
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout_seconds,
                    headers={"User-Agent": "quotes-api-assignment/1.0 (read-only)"},
                )
                self._last_request = time.monotonic()
                if response.status_code == 200:
                    return response.text
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.config.max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                raise UpstreamError(f"Upstream returned HTTP {response.status_code}")
            except requests.RequestException as exc:
                if attempt >= self.config.max_retries:
                    raise UpstreamError(f"Upstream request failed: {exc}") from exc
                time.sleep(0.5 * (2 ** attempt))
        raise UpstreamError("Upstream request failed")

    @staticmethod
    def _parse(html: str, page: int) -> tuple[list[dict], bool]:
        soup = BeautifulSoup(html, "html.parser")
        quotes = []
        for node in soup.select("div.quote"):
            text = node.select_one("span.text").get_text(strip=True).strip('“”')
            author = node.select_one("small.author").get_text(strip=True)
            tags = [x.get_text(strip=True) for x in node.select("div.tags a.tag")]
            quote_id = hashlib.sha256(f"{author}\n{text}".encode()).hexdigest()[:12]
            quotes.append({
                "id": quote_id,
                "text": text,
                "author": author,
                "tags": tags,
                "source_url": f"{BASE_URL}/page/{page}/",
            })
        next_link = soup.select_one("li.next a")
        return quotes, next_link is not None

    def list_quotes(self, page: int = 1):
        html = self._get(f"/page/{page}/")
        return self._parse(html, page)

    def get_all_pages(self, max_pages: int = 10):
        out = []
        for page in range(1, max_pages + 1):
            items, has_next = self.list_quotes(page)
            out.extend(items)
            if not has_next:
                break
        return out
