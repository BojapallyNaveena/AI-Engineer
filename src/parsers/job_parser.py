import json
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .date_parser import parse_date, is_within_24_hours

logger = logging.getLogger(__name__)


class JobParser:
    """Deterministic parser for job postings using JSON-LD JobPosting schema and HTML metadata."""

    def parse(self, html_content: str, source_url: str, source_name: str = "AI Jobs") -> Dict[str, Any]:
        if not html_content:
            logger.warning(f"Empty HTML content for job URL: {source_url}")
            return self._empty_record(source_url, source_name)

        soup = BeautifulSoup(html_content, 'html.parser')

        company_name, job_title, date_posted = self._extract_job_posting_json_ld(soup)

        # Fallbacks if JSON-LD is absent
        if not job_title:
            job_title = self._extract_html_title(soup)
        if not company_name:
            company_name = self._extract_html_company(soup)
        if not date_posted:
            date_posted = self._extract_html_date(soup)

        is_fresh = False
        if date_posted:
            is_fresh = is_within_24_hours(date_posted)
            logger.info(f"Job posting '{job_title}' at '{company_name}' posted: {date_posted} | Fresh (<24h): {is_fresh}")
        else:
            logger.info(f"Job posting '{job_title}' date unestablished. Marking is_fresh=False for provenance.")

        return {
            "schemaVersion": "1.0",
            "recordType": "JOB",
            "company_name": company_name or "Unknown Company",
            "title": job_title or "Unknown Title",
            "source": {
                "name": source_name,
                "url": source_url,
            },
            "published_date": date_posted,
            "is_fresh": is_fresh,
        }

    def _extract_job_posting_json_ld(self, soup: BeautifulSoup) -> tuple:
        company_name = None
        job_title = None
        date_posted = None

        for script in soup.find_all('script', type='application/ld+json'):
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                        job_title = item.get('title')
                        if isinstance(item.get('hiringOrganization'), dict):
                            company_name = item['hiringOrganization'].get('name')
                        elif isinstance(item.get('hiringOrganization'), str):
                            company_name = item['hiringOrganization']
                        if item.get('datePosted'):
                            date_posted = parse_date(str(item['datePosted']))
                        break
            except Exception:
                continue

        return company_name, job_title, date_posted

    def _extract_html_title(self, soup: BeautifulSoup) -> Optional[str]:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        return None

    def _extract_html_company(self, soup: BeautifulSoup) -> Optional[str]:
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name and og_site_name.get('content'):
            return og_site_name['content'].strip()

        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()

        return None

    def _extract_html_date(self, soup: BeautifulSoup) -> Optional[str]:
        time_elem = soup.find('time', attrs={'datetime': True})
        if time_elem:
            return parse_date(time_elem['datetime'])

        meta_date = soup.find('meta', attrs={'name': 'datePosted'}) or soup.find('meta', property='article:published_time')
        if meta_date and meta_date.get('content'):
            return parse_date(meta_date['content'])

        return None

    def _empty_record(self, source_url: str, source_name: str) -> Dict[str, Any]:
        return {
            "schemaVersion": "1.0",
            "recordType": "JOB",
            "company_name": "Unknown Company",
            "title": "Unknown Title",
            "source": {
                "name": source_name,
                "url": source_url,
            },
            "published_date": None,
            "is_fresh": False,
        }
