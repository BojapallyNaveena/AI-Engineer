import unittest
from datetime import datetime, timezone, timedelta
from src.parsers.job_parser import JobParser

SAMPLE_JOB_JSON_LD = """
<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Senior AI Research Scientist",
        "hiringOrganization": {{
            "@type": "Organization",
            "name": "Anthropic"
        }},
        "datePosted": "{pub_time}"
    }}
    </script>
</head>
<body>
</body>
</html>
"""


class TestJobParser(unittest.TestCase):
    def test_parse_fresh_job_posting(self):
        now_dt = datetime.now(timezone.utc)
        fresh_time = (now_dt - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        html = SAMPLE_JOB_JSON_LD.format(pub_time=fresh_time)

        parser = JobParser()
        record = parser.parse(html, source_url="https://jobs.lever.co/anthropic/123", source_name="Lever")

        self.assertEqual(record["recordType"], "JOB")
        self.assertEqual(record["company_name"], "Anthropic")
        self.assertEqual(record["title"], "Senior AI Research Scientist")
        self.assertEqual(record["published_date"], fresh_time)
        self.assertTrue(record["is_fresh"])

    def test_parse_old_job_posting(self):
        now_dt = datetime.now(timezone.utc)
        old_time = (now_dt - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        html = SAMPLE_JOB_JSON_LD.format(pub_time=old_time)

        parser = JobParser()
        record = parser.parse(html, source_url="https://jobs.lever.co/anthropic/old")

        self.assertEqual(record["company_name"], "Anthropic")
        self.assertEqual(record["published_date"], old_time)
        self.assertFalse(record["is_fresh"])


if __name__ == "__main__":
    unittest.main()
