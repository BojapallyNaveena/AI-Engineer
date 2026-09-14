import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urlunparse

from .http_client import HTTPClient
from .playwright_client import PlaywrightClient

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Dataclass holding structured crawl result for data provenance."""
    url: str
    normalized_url: str
    status_code: Optional[int]
    content: Optional[str]
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    elapsed_seconds: float = 0.0
    is_playwright: bool = False


def normalize_url(url: str) -> str:
    """
    Deterministically normalize a URL for deduplication.
    - Strips query tracking parameters (utm_*, ref, etc.)
    - Lowercases scheme and netloc
    - Strips trailing slash
    """
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/') if parsed.path != '/' else ''

    # Filter out common analytics/tracking query params
    query_pairs = []
    if parsed.query:
        for pair in parsed.query.split('&'):
            if not pair:
                continue
            key = pair.split('=')[0].lower()
            if not key.startswith('utm_') and key not in ('ref', 'source', 'fbclid'):
                query_pairs.append(pair)

    clean_query = '&'.join(sorted(query_pairs))
    return urlunparse((scheme, netloc, path, parsed.params, clean_query, ''))


class AsyncCrawler:
    """High-level asynchronous web crawler with rate limiting, concurrency control, and deduplication."""

    def __init__(
        self,
        max_concurrency: int = 10,
        request_timeout: float = 30.0,
        max_retries: int = 4,
        domain_delay: float = 0.5,
    ):
        self.max_concurrency = max_concurrency
        self.domain_delay = domain_delay
        self.http_client = HTTPClient(
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
        self.playwright_client: Optional[PlaywrightClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._visited_urls: Set[str] = set()
        self._domain_last_request: Dict[str, float] = {}
        self._domain_locks: Dict[str, asyncio.Lock] = {}

    def _get_domain_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    async def _rate_limit_domain(self, domain: str) -> None:
        """Enforce per-domain minimum delay between requests."""
        if self.domain_delay <= 0:
            return

        lock = self._get_domain_lock(domain)
        async with lock:
            now = asyncio.get_event_loop().time()
            last_req = self._domain_last_request.get(domain, 0.0)
            elapsed = now - last_req

            if elapsed < self.domain_delay:
                sleep_time = self.domain_delay - elapsed
                logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

            self._domain_last_request[domain] = asyncio.get_event_loop().time()

    async def crawl_url(
        self,
        url: str,
        use_playwright: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> CrawlResult:
        """Crawl a single URL respecting concurrency limits and deduplication."""
        norm_url = normalize_url(url)
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        async with self._semaphore:
            if norm_url in self._visited_urls:
                logger.info(f"Duplicate URL skipped: {url} (normalized: {norm_url})")
                return CrawlResult(
                    url=url,
                    normalized_url=norm_url,
                    status_code=None,
                    content=None,
                    error="Duplicate URL",
                )

            self._visited_urls.add(norm_url)
            await self._rate_limit_domain(domain)

            if use_playwright:
                if self.playwright_client is None:
                    self.playwright_client = PlaywrightClient()
                logger.info(f"Crawling with Playwright: {url}")
                raw_res = await self.playwright_client.fetch(url)
                return CrawlResult(
                    url=url,
                    normalized_url=norm_url,
                    status_code=raw_res["status_code"],
                    content=raw_res["content"],
                    headers=raw_res["headers"],
                    error=raw_res["error"],
                    elapsed_seconds=raw_res["elapsed_seconds"],
                    is_playwright=True,
                )
            else:
                logger.info(f"Crawling with HTTPClient: {url}")
                raw_res = await self.http_client.fetch(url, headers=headers)
                return CrawlResult(
                    url=url,
                    normalized_url=norm_url,
                    status_code=raw_res["status_code"],
                    content=raw_res["content"],
                    headers=raw_res["headers"],
                    error=raw_res["error"],
                    elapsed_seconds=raw_res["elapsed_seconds"],
                    is_playwright=False,
                )

    async def crawl_urls(
        self,
        urls: List[str],
        use_playwright: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[CrawlResult]:
        """Crawl multiple URLs concurrently."""
        logger.info(f"Crawler started processing {len(urls)} URLs")
        tasks = [
            self.crawl_url(url, use_playwright=use_playwright, headers=headers)
            for url in urls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        logger.info(f"Crawler completed {len(results)} URLs")
        return list(results)

    async def close(self) -> None:
        """Clean up HTTP and Playwright client resources."""
        await self.http_client.close()
        if self.playwright_client:
            await self.playwright_client.close()
