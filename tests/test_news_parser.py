import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from src.parsers.news_parser import NewsParser

SAMPLE_NEWS_OG = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="OpenAI Announces Next Generation Reasoning Model"/>
    <meta property="og:description" content="A breakthrough in autonomous reasoning and coding benchmarks."/>
    <meta property="article:published_time" content="{pub_time}"/>
</head>
<body>
    <h1>OpenAI Announces Next Generation Reasoning Model</h1>
</body>
</html>
"""

SAMPLE_NEWS_JSON_LD = """
<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": "New AI Startup Raises $50M",
        "description": "Funding round led by top VCs.",
        "datePublished": "{pub_time}"
    }}
    </script>
</head>
<body>
</body>
</html>
"""



class TestNewsParser(unittest.TestCase):
    def test_parse_fresh_news_og(self):
        # 2 hours ago from fixed reference
        now_dt = datetime.now(timezone.utc)
        fresh_time = (now_dt - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        html = SAMPLE_NEWS_OG.format(pub_time=fresh_time)

        parser = NewsParser()
        record = parser.parse(html, source_url="https://techcrunch.com/sample-news", source_name="TechCrunch")

        self.assertEqual(record["recordType"], "NEWS")
        self.assertEqual(record["title"], "OpenAI Announces Next Generation Reasoning Model")
        self.assertEqual(record["content_summary"], "A breakthrough in autonomous reasoning and coding benchmarks.")
        self.assertEqual(record["source"]["name"], "TechCrunch")
        self.assertEqual(record["published_date"], fresh_time)
        self.assertTrue(record["is_fresh"])

    def test_parse_old_news_json_ld(self):
        # 48 hours ago -> not fresh
        now_dt = datetime.now(timezone.utc)
        old_time = (now_dt - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        html = SAMPLE_NEWS_JSON_LD.format(pub_time=old_time)

        parser = NewsParser()
        record = parser.parse(html, source_url="https://news.ycombinator.com/item?id=123")

        self.assertEqual(record["title"], "New AI Startup Raises $50M")
        self.assertEqual(record["content_summary"], "Funding round led by top VCs.")
        self.assertEqual(record["published_date"], old_time)
        self.assertFalse(record["is_fresh"])

    def test_parse_news_without_date(self):
        html = "<html><head><title>Undated AI Story</title></head><body></body></html>"
        parser = NewsParser()
        record = parser.parse(html, source_url="https://example.com/undated")

        self.assertEqual(record["title"], "Undated AI Story")
        self.assertIsNone(record["published_date"])
        self.assertFalse(record["is_fresh"])


if __name__ == "__main__":
    unittest.main()
