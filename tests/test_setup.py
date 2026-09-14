import os
import unittest
from pathlib import Path

class TestSetup(unittest.TestCase):
    def test_project_structure(self):
        """Verify that essential project configuration files and directories exist."""
        base_dir = Path(__file__).parent.parent
        
        self.assertTrue((base_dir / ".gitignore").is_file())
        self.assertTrue((base_dir / ".env.example").is_file())
        self.assertTrue((base_dir / "requirements.txt").is_file())
        self.assertTrue((base_dir / "README.md").is_file())
        self.assertTrue((base_dir / "PRD.md").is_file())
        self.assertTrue((base_dir / "src").is_dir())
        self.assertTrue((base_dir / "data" / "raw").is_dir())
        self.assertTrue((base_dir / "data" / "processed").is_dir())
        self.assertTrue((base_dir / "data" / "exports").is_dir())

    def test_env_example_keys(self):
        """Verify that .env.example contains essential environment variable keys."""
        base_dir = Path(__file__).parent.parent
        env_content = (base_dir / ".env.example").read_text()
        
        required_keys = [
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "DEEPSEEK_API_KEY",
            "GITHUB_TOKEN",
            "DATABASE_URL",
            "MAX_CONCURRENCY",
            "REQUEST_TIMEOUT",
            "MAX_RETRIES",
        ]
        
        for key in required_keys:
            self.assertIn(key, env_content, f"Missing key {key} in .env.example")

if __name__ == "__main__":
    unittest.main()

