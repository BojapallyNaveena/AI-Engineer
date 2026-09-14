import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 AI-Engineer-Crawler/1.0"
)


class HTTPClient:
    """Asynchronous HTTP client with retry, exponential backoff, jitter, and 429 handling."""

    def __init__(
        self,
        request_timeout: float = 30.0,
        max_retries: int = 4,
        base_backoff: float = 1.0,
        max_backoff: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.user_agent = user_agent
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create the underlying aiohttp.ClientSession."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            headers = {"User-Agent": self.user_agent}
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _calculate_backoff(self, attempt: int, retry_after: Optional[str] = None) -> float:
        """Calculate exponential backoff with full jitter, respecting Retry-After header if set."""
        if retry_after:
            try:
                parsed_delay = float(retry_after)
                if parsed_delay > 0:
                    return min(parsed_delay, self.max_backoff)
            except ValueError:
                pass

        # Exponential backoff: base * (2 ^ attempt) + full jitter
        exponential = self.base_backoff * (2 ** attempt)
        jittered = random.uniform(0, exponential)
        return min(jittered, self.max_backoff)

    async def fetch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        allow_redirects: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch a URL asynchronously with retry, backoff, and detailed error tracking.

        Returns dict with keys: url, status_code, content, headers, error, elapsed_seconds
        """
        session = await self.get_session()
        start_time = time.monotonic()

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Requesting URL (attempt {attempt + 1}): {url}")
                async with session.get(url, headers=headers, allow_redirects=allow_redirects) as response:
                    status = response.status
                    elapsed = time.monotonic() - start_time

                    if status == 200:
                        content = await response.text(errors="replace")
                        logger.info(f"Request successful [200]: {url} ({elapsed:.2f}s)")
                        return {
                            "url": url,
                            "status_code": status,
                            "content": content,
                            "headers": dict(response.headers),
                            "error": None,
                            "elapsed_seconds": elapsed,
                        }

                    elif status == 429:
                        retry_after = response.headers.get("Retry-After")
                        logger.warning(f"429 received for {url}. Retry-After: {retry_after}")
                        if attempt < self.max_retries:
                            delay = self._calculate_backoff(attempt, retry_after)
                            logger.info(f"Retry scheduled in {delay:.2f}s for {url} (attempt {attempt + 1}/{self.max_retries})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return {
                                "url": url,
                                "status_code": status,
                                "content": None,
                                "headers": dict(response.headers),
                                "error": f"HTTP 429: Too Many Requests (exceeded {self.max_retries} retries)",
                                "elapsed_seconds": elapsed,
                            }

                    elif status == 413:
                        logger.warning(f"413 detected (Payload Too Large) for {url}")
                        return {
                            "url": url,
                            "status_code": status,
                            "content": None,
                            "headers": dict(response.headers),
                            "error": "HTTP 413: Payload Too Large",
                            "elapsed_seconds": elapsed,
                        }

                    elif 500 <= status < 600:
                        logger.warning(f"Server error [{status}] for {url}")
                        if attempt < self.max_retries:
                            delay = self._calculate_backoff(attempt)
                            logger.info(f"Retry scheduled in {delay:.2f}s for {url}")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return {
                                "url": url,
                                "status_code": status,
                                "content": None,
                                "headers": dict(response.headers),
                                "error": f"HTTP {status} server error",
                                "elapsed_seconds": elapsed,
                            }

                    else:
                        logger.warning(f"Request returned HTTP {status}: {url}")
                        return {
                            "url": url,
                            "status_code": status,
                            "content": None,
                            "headers": dict(response.headers),
                            "error": f"HTTP status {status}",
                            "elapsed_seconds": elapsed,
                        }

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                elapsed = time.monotonic() - start_time
                error_msg = f"{type(exc).__name__}: {str(exc)}"
                logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {error_msg}")

                if attempt < self.max_retries:
                    delay = self._calculate_backoff(attempt)
                    logger.info(f"Retry scheduled in {delay:.2f}s for {url}")
                    await asyncio.sleep(delay)
                else:
                    return {
                        "url": url,
                        "status_code": None,
                        "content": None,
                        "headers": {},
                        "error": error_msg,
                        "elapsed_seconds": elapsed,
                    }

        elapsed = time.monotonic() - start_time
        return {
            "url": url,
            "status_code": None,
            "content": None,
            "headers": {},
            "error": "Max retries exceeded",
            "elapsed_seconds": elapsed,
        }
