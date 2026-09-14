import unittest
from src.parsers.paper_parser import ArxivPaperParser

SAMPLE_ARXIV_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="citation_title" content="Attention Is All You Need"/>
    <meta name="citation_author" content="Ashish Vaswani"/>
    <meta name="citation_author" content="Noam Shazeer"/>
    <meta name="citation_author" content="Niki Parmar"/>
    <meta name="citation_date" content="2017/06/12"/>
    <title>[1706.03762] Attention Is All You Need</title>
</head>
<body>
    <div id="content">
        <h1 class="title mathjax"><span class="descriptor">Title:</span>Attention Is All You Need</h1>
        <div class="authors">
            <span class="descriptor">Authors:</span>
            <a href="https://arxiv.org/search/cs?searchtype=author&query=Vaswani%2C+A">Ashish Vaswani</a>,
            <a href="https://arxiv.org/search/cs?searchtype=author&query=Shazeer%2C+N">Noam Shazeer</a>
        </div>
        <blockquote class="abstract mathjax">
            <span class="descriptor">Abstract:</span>
            The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.
            Code is available at <a href="https://github.com/tensorflow/tensor2tensor">https://github.com/tensorflow/tensor2tensor</a>.
        </blockquote>
    </div>
</body>
</html>
"""

SAMPLE_ARXIV_HTML_NO_GITHUB = """
<!DOCTYPE html>
<html>
<head>
    <meta name="citation_title" content="Sample AI Paper Without GitHub"/>
    <meta name="citation_author" content="Jane Doe"/>
    <meta name="citation_date" content="2024-02-01"/>
</head>
<body>
    <h1 class="title">Sample AI Paper Without GitHub</h1>
</body>
</html>
"""


class TestArxivPaperParser(unittest.TestCase):
    def test_parse_arxiv_with_github(self):
        parser = ArxivPaperParser()
        url = "https://arxiv.org/abs/1706.03762"
        record = parser.parse(SAMPLE_ARXIV_HTML, source_url=url)
        
        self.assertEqual(record["schemaVersion"], "1.0")
        self.assertEqual(record["recordType"], "RESEARCH_PAPER")
        self.assertEqual(record["title"], "Attention Is All You Need")
        self.assertEqual(record["authors"], ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"])
        self.assertEqual(record["paper_url"], url)
        self.assertEqual(record["github_url"], "https://github.com/tensorflow/tensor2tensor")
        self.assertIsNone(record["github_stars"])
        self.assertEqual(record["published_date"], "2017-06-12T00:00:00Z")

    def test_parse_arxiv_without_github(self):
        parser = ArxivPaperParser()
        url = "https://arxiv.org/abs/2402.99999"
        record = parser.parse(SAMPLE_ARXIV_HTML_NO_GITHUB, source_url=url)
        
        self.assertEqual(record["title"], "Sample AI Paper Without GitHub")
        self.assertEqual(record["authors"], ["Jane Doe"])
        self.assertIsNone(record["github_url"])
        self.assertIsNone(record["github_stars"])
        self.assertEqual(record["published_date"], "2024-02-01T00:00:00Z")

    def test_parse_empty_content(self):
        parser = ArxivPaperParser()
        url = "https://arxiv.org/abs/0000.0000"
        record = parser.parse("", source_url=url)
        
        self.assertEqual(record["paper_url"], url)
        self.assertIsNone(record["title"])
        self.assertEqual(record["authors"], [])
        self.assertIsNone(record["github_url"])


if __name__ == "__main__":
    unittest.main()
