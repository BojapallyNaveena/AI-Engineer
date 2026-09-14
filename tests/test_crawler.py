import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from src.crawler.crawler import AsyncCrawler, CrawlResult, normalize_url
from src.crawler.http_client import HTTPClient


class TestURLNormalization(unittest.TestCase):
    def test_normalize_url(self):
        url1 = "HTTPS://EXAMPLE.COM/path/page?utm_source=twitter&id=123#fragment"
        url2 = "https://example.com/path/page?id=123"
        
        norm1 = normalize_url(url1)
        norm2 = normalize_url(url2)
        
        self.assertEqual(norm1, norm2)
        self.assertEqual(norm1, "https://example.com/path/page?id=123")

    def test_normalize_url_trailing_slash(self):
        url1 = "https://arxiv.org/abs/2401.12345/"
        url2 = "https://arxiv.org/abs/2401.12345"
        self.assertEqual(normalize_url(url1), normalize_url(url2))


class TestHTTPClientBackoff(unittest.TestCase):
    def test_calculate_backoff_retry_after(self):
        client = HTTPClient(base_backoff=1.0, max_backoff=60.0)
        delay = client._calculate_backoff(attempt=0, retry_after="15.5")
        self.assertEqual(delay, 15.5)

    def test_calculate_backoff_jitter(self):
        client = HTTPClient(base_backoff=1.0, max_backoff=60.0)
        delay = client._calculate_backoff(attempt=2)
        # Attempt 2 -> exponential = 1 * 2^2 = 4. Jitter is uniform(0, 4)
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, 4.0)


class TestAsyncCrawler(unittest.IsolatedAsyncioTestCase):
    async def test_duplicate_prevention(self):
        crawler = AsyncCrawler(max_concurrency=2, domain_delay=0.0)
        
        mock_fetch = AsyncMock(return_value={
            "url": "https://example.com/item",
            "status_code": 200,
            "content": "<html>Sample</html>",
            "headers": {},
            "error": None,
            "elapsed_seconds": 0.1,
        })
        
        with patch.object(crawler.http_client, "fetch", mock_fetch):
            urls = ["https://example.com/item", "https://example.com/item?utm_source=rss"]
            results = await crawler.crawl_urls(urls)
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].status_code, 200)
            self.assertIsNone(results[1].status_code)
            self.assertEqual(results[1].error, "Duplicate URL")
            self.assertEqual(mock_fetch.call_count, 1)
            
        await crawler.close()

    async def test_resiliency_on_single_url_failure(self):
        crawler = AsyncCrawler(max_concurrency=2, domain_delay=0.0)
        
        async def mock_fetch_side_effect(url, **kwargs):
            if "fail" in url:
                return {
                    "url": url,
                    "status_code": 500,
                    "content": None,
                    "headers": {},
                    "error": "HTTP 500 server error",
                    "elapsed_seconds": 0.1,
                }
            return {
                "url": url,
                "status_code": 200,
                "content": f"Content for {url}",
                "headers": {},
                "error": None,
                "elapsed_seconds": 0.1,
            }
            
        with patch.object(crawler.http_client, "fetch", side_effect=mock_fetch_side_effect):
            urls = ["https://site1.org/ok", "https://site2.org/fail", "https://site3.org/ok"]
            results = await crawler.crawl_urls(urls)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0].status_code, 200)
            self.assertEqual(results[1].status_code, 500)
            self.assertEqual(results[1].error, "HTTP 500 server error")
            self.assertEqual(results[2].status_code, 200)
            
        await crawler.close()


if __name__ == "__main__":
    unittest.main()
