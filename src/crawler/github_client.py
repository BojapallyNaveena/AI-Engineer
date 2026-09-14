import os
import re
import logging
from typing import Optional, Tuple
import aiohttp

logger = logging.getLogger(__name__)

GITHUB_REPO_PATTERN = re.compile(
    r'https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',
    re.IGNORECASE
)


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Extract (owner, repo) from a GitHub URL.
    Handles URLs with trailing .git, trailing slashes, or subpaths like /tree/main.
    """
    if not url or not isinstance(url, str):
        return None

    match = GITHUB_REPO_PATTERN.search(url.strip())
    if not match:
        return None

    owner = match.group(1)
    repo = match.group(2)

    # Clean repo name
    if repo.endswith('.git'):
        repo = repo[:-4]
    repo = repo.rstrip('/')

    return owner, repo


class GitHubClient:
    """Asynchronous client for interacting with the official GitHub REST API."""

    def __init__(self, github_token: Optional[str] = None, timeout_seconds: float = 10.0):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.timeout_seconds = timeout_seconds
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "AI-Engineer-Crawler/1.0",
            }
            if self.github_token:
                headers["Authorization"] = f"Bearer {self.github_token}"
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_repo_stars(self, github_url: Optional[str]) -> Tuple[Optional[str], Optional[int]]:
        """
        Verify GitHub repository existence and retrieve star count (stargazers_count).
        
        Returns:
            Tuple[Optional[str], Optional[int]]: (canonical_github_url, stargazers_count)
            Returns (github_url, None) if repo cannot be verified or request fails.
        """
        if not github_url:
            return None, None

        parsed = parse_github_url(github_url)
        if not parsed:
            logger.warning(f"Invalid GitHub URL format: {github_url}")
            return github_url, None

        owner, repo = parsed
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        canonical_url = f"https://github.com/{owner}/{repo}"

        session = await self.get_session()
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    stars = data.get("stargazers_count")
                    logger.info(f"GitHub API verified {canonical_url} - Stars: {stars}")
                    return canonical_url, stars
                elif response.status == 404:
                    logger.warning(f"GitHub repository not found [404]: {canonical_url}")
                    return canonical_url, None
                else:
                    logger.warning(f"GitHub API returned HTTP {response.status} for {canonical_url}")
                    return canonical_url, None
        except Exception as e:
            logger.warning(f"Error querying GitHub API for {canonical_url}: {e}")
            return canonical_url, None
