import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from src.crawler.github_client import GitHubClient, parse_github_url


class TestGitHubURLParser(unittest.TestCase):
    def test_parse_valid_urls(self):
        self.assertEqual(parse_github_url("https://github.com/tensorflow/tensor2tensor"), ("tensorflow", "tensor2tensor"))
        self.assertEqual(parse_github_url("http://github.com/openai/gpt-2.git"), ("openai", "gpt-2"))
        self.assertEqual(parse_github_url("https://github.com/meta-llama/llama/tree/main"), ("meta-llama", "llama"))

    def test_parse_invalid_urls(self):
        self.assertIsNone(parse_github_url("https://arxiv.org/abs/1706.03762"))
        self.assertIsNone(parse_github_url(None))
        self.assertIsNone(parse_github_url(""))


class TestGitHubClient(unittest.IsolatedAsyncioTestCase):
    async def test_get_repo_stars_success(self):
        client = GitHubClient(github_token="fake_token_123")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"stargazers_count": 12345})
        
        # aiohttp session.get returns a context manager whose __aenter__ returns response
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get.return_value = mock_cm
        
        with patch.object(client, "get_session", new_callable=AsyncMock, return_value=mock_session):
            url, stars = await client.get_repo_stars("https://github.com/tensorflow/tensor2tensor")
            self.assertEqual(url, "https://github.com/tensorflow/tensor2tensor")
            self.assertEqual(stars, 12345)
            
        await client.close()

    async def test_get_repo_stars_not_found(self):
        client = GitHubClient()
        
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get.return_value = mock_cm
        
        with patch.object(client, "get_session", new_callable=AsyncMock, return_value=mock_session):
            url, stars = await client.get_repo_stars("https://github.com/nonexistent/repo")
            self.assertEqual(url, "https://github.com/nonexistent/repo")
            self.assertIsNone(stars)
            
        await client.close()



if __name__ == "__main__":
    unittest.main()
