import unittest
from src.storage.database import init_db, Base
from src.storage.repository import Repository
from src.storage.models import ResearchPaperModel, EntityMappingModel


class TestStorageRepository(unittest.TestCase):
    def setUp(self):
        # Use isolated in-memory SQLite database for testing
        self.engine = init_db("sqlite:///:memory:")
        self.repo = Repository()

    def test_insert_and_get_research_paper(self):
        paper_data = {
            "schemaVersion": "1.0",
            "recordType": "RESEARCH_PAPER",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "paper_url": "https://arxiv.org/abs/1706.03762",
            "github_url": "https://github.com/tensorflow/tensor2tensor",
            "github_stars": None,
            "published_date": "2017-06-12T00:00:00Z",
        }
        
        record = self.repo.insert_research_paper(paper_data)
        self.assertIsNotNone(record.id)
        self.assertEqual(record.title, "Attention Is All You Need")
        self.assertEqual(record.authors, ["Ashish Vaswani", "Noam Shazeer"])
        
        # Test query by paper_url
        fetched = self.repo.get_research_paper_by_url("https://arxiv.org/abs/1706.03762")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, record.id)

    def test_research_paper_deduplication(self):
        paper_data_1 = {
            "paper_url": "https://arxiv.org/abs/1706.03762",
            "title": "Initial Title",
            "authors": ["Author One"],
        }
        record1 = self.repo.insert_research_paper(paper_data_1)
        
        paper_data_2 = {
            "paper_url": "https://arxiv.org/abs/1706.03762",
            "title": "Updated Title",
            "github_stars": 42000,
        }
        record2 = self.repo.insert_research_paper(paper_data_2)
        
        self.assertEqual(record1.id, record2.id)
        self.assertEqual(record2.title, "Updated Title")
        self.assertEqual(record2.github_stars, 42000)

    def test_insert_entity_mapping(self):
        mapping_data = {
            "raw_name": "Open AI",
            "canonical_name": "OpenAI",
            "entity_type": "STARTUP",
            "source_url": "https://openai.com",
            "resolution_method": "normalized",
            "confidence": 1.0,
        }
        record = self.repo.insert_entity_mapping(mapping_data)
        self.assertIsNotNone(record.id)
        self.assertEqual(record.raw_name, "Open AI")
        self.assertEqual(record.canonical_name, "OpenAI")
        self.assertEqual(record.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
