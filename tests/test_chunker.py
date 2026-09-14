import unittest
from src.llm.chunker import ContentChunker

SAMPLE_HTML_BOILERPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script>var x = 10;</script>
    <style>body { color: red; }</style>
</head>
<body>
    <header>Nav Header</header>
    <main>
        <h1>Main AI Article Title</h1>
        <p>First paragraph detailing artificial intelligence research.</p>
        <p>Second paragraph detailing model architecture performance.</p>
    </main>
    <footer>Footer Links</footer>
</body>
</html>
"""


class TestContentChunker(unittest.TestCase):
    def test_clean_text_strips_boilerplate(self):
        cleaned = ContentChunker.clean_text(SAMPLE_HTML_BOILERPLATE)
        self.assertNotIn("var x = 10", cleaned)
        self.assertNotIn("color: red", cleaned)
        self.assertNotIn("Footer Links", cleaned)
        self.assertIn("Main AI Article Title", cleaned)
        self.assertIn("First paragraph", cleaned)

    def test_chunk_text_small_content(self):
        chunks = ContentChunker.chunk_text("Short content text.", max_chunk_chars=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "Short content text.")

    def test_chunk_text_large_content(self):
        large_text = ("Sentence one about neural networks. " * 100)
        chunks = ContentChunker.chunk_text(large_text, max_chunk_chars=200, overlap_chars=20)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 250)


if __name__ == "__main__":
    unittest.main()
