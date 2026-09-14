import unittest
from pathlib import Path
import tempfile
from src.storage.database import init_db
from src.storage.repository import Repository
from src.exporters.csv_exporter import CSVExporter


class TestCSVExporter(unittest.TestCase):
    def setUp(self):
        self.engine = init_db("sqlite:///:memory:")
        self.repo = Repository()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_all_creates_files(self):
        # Insert sample records
        self.repo.insert_research_paper({
            "paper_url": "https://arxiv.org/abs/1706.03762",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani"],
        })
        self.repo.insert_startup({
            "schemaVersion": "1.0",
            "recordType": "STARTUP",
            "content": {"entityName": "OpenAI", "data": {"employeeCount": 500}},
            "source": {"name": "Y Combinator", "url": "https://ycombinator.com/openai"},
        })
        self.repo.insert_product({
            "schemaVersion": "1.0",
            "recordType": "PRODUCT",
            "content": {"startupName": "OpenAI", "pricingModel": "FREEMIUM"},
            "source": {"name": "ProductHunt", "url": "https://producthunt.com/chatgpt"},
        })

        exporter = CSVExporter()
        export_files = exporter.export_all(export_dir=self.temp_dir.name)

        self.assertIn("research_papers", export_files)
        self.assertIn("startups", export_files)
        self.assertIn("products", export_files)
        self.assertIn("jobs", export_files)
        self.assertIn("news", export_files)
        self.assertIn("entity_mappings", export_files)

        for name, filepath in export_files.items():
            self.assertTrue(Path(filepath).is_file())


if __name__ == "__main__":
    unittest.main()
