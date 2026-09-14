import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PlaywrightClient:
    """Asynchronous Playwright client for JavaScript-rendered web pages."""

    def __init__(self, timeout_ms: int = 30000, headless: bool = True):
        self.timeout_ms = timeout_ms
        self.headless = headless
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        """Lazily initialize Playwright browser instance."""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=self.headless)
                logger.info("Launched Playwright browser instance")
            except Exception as e:
                logger.error(f"Failed to launch Playwright browser: {e}")
                raise RuntimeError(
                    f"Playwright browser initialization failed: {e}. "
                    "Ensure playwright is installed and browser binaries are downloaded ('playwright install')."
                ) from e

    async def fetch(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Render a JS page using Playwright and return HTML content.

        Returns dict with keys: url, status_code, content, headers, error, elapsed_seconds
        """
        start_time = time.monotonic()
        try:
            await self._ensure_browser()
            page = await self._browser.new_page()
            response = await page.goto(url, wait_until=wait_until, timeout=self.timeout_ms)

            status = response.status if response else 200
            content = await page.content()
            headers = response.headers if response else {}
            await page.close()

            elapsed = time.monotonic() - start_time
            logger.info(f"Playwright fetch successful: {url} ({elapsed:.2f}s)")
            return {
                "url": url,
                "status_code": status,
                "content": content,
                "headers": headers,
                "error": None,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            elapsed = time.monotonic() - start_time
            error_msg = f"Playwright error: {str(e)}"
            logger.error(f"Playwright fetch failed for {url}: {error_msg}")
            return {
                "url": url,
                "status_code": None,
                "content": None,
                "headers": {},
                "error": error_msg,
                "elapsed_seconds": elapsed,
            }

    async def close(self) -> None:
        """Close browser and stop Playwright driver."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Closed Playwright browser instance")
