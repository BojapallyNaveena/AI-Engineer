import json
import logging
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .date_parser import parse_date, is_within_24_hours

logger = logging.getLogger(__name__)


class NewsParser:
    """Deterministic parser for news articles extracting OpenGraph metadata, JSON-LD, and 24-hour freshness."""

    def parse(self, html_content: str, source_url: str, source_name: str = "AI News") -> Dict[str, Any]:
        if not html_content:
            logger.warning(f"Empty HTML content for news URL: {source_url}")
            return self._empty_record(source_url, source_name)

        soup = BeautifulSoup(html_content, 'html.parser')

        title = self._extract_title(soup)
        summary = self._extract_summary(soup)
        pub_date = self._extract_published_date(soup)

        is_fresh = False
        if pub_date:
            is_fresh = is_within_24_hours(pub_date)
            logger.info(f"News article '{title}' published date: {pub_date} | Fresh (<24h): {is_fresh}")
        else:
            logger.info(f"News article '{title}' publication date unestablished. Marking is_fresh=False for provenance.")

        return {
            "schemaVersion": "1.0",
            "recordType": "NEWS",
            "title": title or "Untitled News",
            "content_summary": summary,
            "source": {
                "name": source_name,
                "url": source_url,
            },
            "published_date": pub_date,
            "is_fresh": is_fresh,
        }

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. OpenGraph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        # 2. JSON-LD headline/name
        json_ld_data = self._parse_json_ld(soup)
        for item in json_ld_data:
            if item.get('headline'):
                return item['headline'].strip()
            if item.get('name'):
                return item['name'].strip()

        # 3. HTML h1 element
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        # 4. Fallback page title tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        return None

    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. OpenGraph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()

        # 2. Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()

        # 3. JSON-LD description
        json_ld_data = self._parse_json_ld(soup)
        for item in json_ld_data:
            if item.get('description'):
                return item['description'].strip()

        return None

    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. OpenGraph / article published time
        for prop in ['article:published_time', 'og:article:published_time', 'pubdate']:
            meta_date = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
            if meta_date and meta_date.get('content'):
                parsed = parse_date(meta_date['content'])
                if parsed:
                    return parsed

        # 2. JSON-LD datePublished or dateCreated
        json_ld_data = self._parse_json_ld(soup)
        for item in json_ld_data:
            for key in ['datePublished', 'dateCreated']:
                if item.get(key):
                    parsed = parse_date(str(item[key]))
                    if parsed:
                        return parsed

        # 3. HTML <time datetime="..."> element
        time_elem = soup.find('time', attrs={'datetime': True})
        if time_elem:
            parsed = parse_date(time_elem['datetime'])
            if parsed:
                return parsed

        return None

    def _parse_json_ld(self, soup: BeautifulSoup) -> list:
        results = []
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string:
                try:
                    data = json.loads(script.string.strip())
                    if isinstance(data, dict):
                        results.append(data)
                    elif isinstance(data, list):
                        results.extend([x for x in data if isinstance(x, dict)])
                except Exception:
                    continue
        return results

    def _empty_record(self, source_url: str, source_name: str) -> Dict[str, Any]:
        return {
            "schemaVersion": "1.0",
            "recordType": "NEWS",
            "title": "Untitled News",
            "content_summary": None,
            "source": {
                "name": source_name,
                "url": source_url,
            },
            "published_date": None,
            "is_fresh": False,
        }
