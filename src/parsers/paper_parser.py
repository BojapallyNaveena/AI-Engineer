import logging
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from .date_parser import parse_date

logger = logging.getLogger(__name__)

GITHUB_REPO_REGEX = re.compile(
    r'https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',
    re.IGNORECASE
)


class ArxivPaperParser:
    """Parser for arXiv research paper pages using deterministic HTML metadata and content extraction."""

    def parse(self, html_content: str, source_url: str) -> Dict[str, Any]:
        """
        Parse arXiv HTML and return structured RESEARCH_PAPER record.
        Strictly preserves source URLs and returns None for missing values without hallucination.
        """
        if not html_content:
            logger.warning(f"Empty HTML content provided for {source_url}")
            return self._empty_record(source_url)

        soup = BeautifulSoup(html_content, 'html.parser')

        title = self._extract_title(soup)
        authors = self._extract_authors(soup)
        published_date = self._extract_published_date(soup)
        github_url = self._extract_github_url(soup, html_content)

        record = {
            "schemaVersion": "1.0",
            "recordType": "RESEARCH_PAPER",
            "title": title,
            "authors": authors,
            "paper_url": source_url,
            "github_url": github_url,
            "github_stars": None,
            "published_date": published_date,
        }

        logger.info(f"Successfully parsed research paper: {title} (URL: {source_url})")
        return record

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. Try citation_title meta tag
        meta_title = soup.find('meta', attrs={'name': 'citation_title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()

        # 2. Try h1 element with class 'title'
        h1_title = soup.find('h1', class_=re.compile(r'title', re.I))
        if h1_title:
            text = h1_title.get_text(strip=True)
            # Strip prefix "Title:" if present
            if text.lower().startswith('title:'):
                text = text[6:].strip()
            return text

        # 3. Fallback to page title tag
        if soup.title and soup.title.string:
            text = soup.title.string.strip()
            if text.lower().startswith('title:'):
                text = text[6:].strip()
            return text

        return None

    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        authors = []
        # 1. Try citation_author meta tags
        meta_authors = soup.find_all('meta', attrs={'name': 'citation_author'})
        for meta in meta_authors:
            if meta.get('content'):
                authors.append(meta['content'].strip())

        if authors:
            return authors

        # 2. Try div with class 'authors'
        authors_div = soup.find('div', class_=re.compile(r'authors', re.I))
        if authors_div:
            author_links = authors_div.find_all('a')
            for a in author_links:
                name = a.get_text(strip=True)
                if name:
                    authors.append(name)

        return authors

    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. Try citation_date or citation_online_date meta tag
        for meta_name in ['citation_date', 'citation_online_date', 'citation_publication_date']:
            meta_date = soup.find('meta', attrs={'name': meta_name})
            if meta_date and meta_date.get('content'):
                parsed = parse_date(meta_date['content'])
                if parsed:
                    return parsed

        # 2. Try dateline div text (e.g., "[Submitted on 15 Jan 2024]")
        dateline = soup.find('div', class_=re.compile(r'dateline', re.I))
        if dateline:
            text = dateline.get_text()
            match = re.search(r'Submitted on\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})', text, re.I)
            if match:
                parsed = parse_date(match.group(1))
                if parsed:
                    return parsed

        return None

    def _extract_github_url(self, soup: BeautifulSoup, raw_html: str) -> Optional[str]:
        # Search for github.com links in abstract or page anchors
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            match = GITHUB_REPO_REGEX.search(href)
            if match:
                # Reconstruct clean https://github.com/user/repo URL without trailing .git or query params
                user, repo = match.group(1), match.group(2)
                repo = repo.rstrip('.git').rstrip('/')
                return f"https://github.com/{user}/{repo}"

        # Fallback regex search on full raw HTML/abstract text
        match = GITHUB_REPO_REGEX.search(raw_html)
        if match:
            user, repo = match.group(1), match.group(2)
            repo = repo.rstrip('.git').rstrip('/')
            return f"https://github.com/{user}/{repo}"

        return None

    def _empty_record(self, source_url: str) -> Dict[str, Any]:
        return {
            "schemaVersion": "1.0",
            "recordType": "RESEARCH_PAPER",
            "title": None,
            "authors": [],
            "paper_url": source_url,
            "github_url": None,
            "github_stars": None,
            "published_date": None,
        }
