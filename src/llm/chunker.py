import re
import logging
from typing import List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentChunker:
    """Utility class for cleaning raw HTML and splitting large payloads into semantic chunks."""

    @staticmethod
    def clean_text(html_or_text: str) -> str:
        """
        Clean raw HTML by stripping boilerplate tags (<script>, <style>, <nav>, <footer>, etc.),
        HTML comments, and collapsing redundant whitespace.
        """
        if not html_or_text or not isinstance(html_or_text, str):
            return ""

        try:
            soup = BeautifulSoup(html_or_text, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                element.decompose()
            text = soup.get_text(separator=' ')
        except Exception:
            text = re.sub(r'<[^>]+>', ' ', html_or_text)

        # Replace non-breaking spaces and normalize whitespace
        text = text.replace('\xa0', ' ')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()

    @classmethod
    def chunk_text(
        cls,
        raw_content: str,
        max_chunk_chars: int = 4000,
        overlap_chars: int = 200,
    ) -> List[str]:
        """
        Clean content and split into semantic chunks bounded by max_chunk_chars.
        Preserves sentence boundaries where possible.
        """
        cleaned = cls.clean_text(raw_content)
        if not cleaned:
            return []

        if len(cleaned) <= max_chunk_chars:
            return [cleaned]

        logger.info(f"Oversized payload ({len(cleaned)} chars) detected. Chunking content...")
        chunks = []
        start = 0
        total_len = len(cleaned)

        while start < total_len:
            end = min(start + max_chunk_chars, total_len)

            # Try to break at paragraph or sentence boundary if not at end of text
            if end < total_len:
                boundary = max(
                    cleaned.rfind('\n\n', start, end),
                    cleaned.rfind('. ', start, end),
                    cleaned.rfind('\n', start, end),
                )
                if boundary > start + (max_chunk_chars // 2):
                    end = boundary + 1

            chunk_str = cleaned[start:end].strip()
            if chunk_str:
                chunks.append(chunk_str)

            if end >= total_len:
                break

            start = max(start + 1, end - overlap_chars)

        logger.info(f"Successfully chunked payload into {len(chunks)} semantic chunks.")
        return chunks
