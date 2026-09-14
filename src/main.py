import asyncio
import logging
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from src.crawler.crawler import AsyncCrawler
from src.crawler.github_client import GitHubClient
from src.parsers.paper_parser import ArxivPaperParser
from src.parsers.news_parser import NewsParser
from src.parsers.job_parser import JobParser
from src.resolver.entity_resolver import EntityResolver
from src.validation.validators import RecordValidator
from src.storage.database import init_db
from src.storage.repository import Repository
from src.exporters.csv_exporter import CSVExporter

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

SAMPLE_PAPER_URLS = [
    "https://arxiv.org/abs/1706.03762",  # Attention Is All You Need
    "https://arxiv.org/abs/2303.08774",  # GPT-4 Technical Report
]


async def run_pipeline():
    logger.info("Initializing SQLite database storage...")
    db_path = Path(__file__).parent.parent / "data" / "app.db"
    init_db(f"sqlite:///{db_path}")
    repo = Repository()

    crawler = AsyncCrawler(max_concurrency=2, domain_delay=0.5)
    paper_parser = ArxivPaperParser()
    news_parser = NewsParser()
    job_parser = JobParser()
    github_client = GitHubClient()
    resolver = EntityResolver()

    try:
        # 1. Process Research Papers
        logger.info(f"Crawling {len(SAMPLE_PAPER_URLS)} research paper sources...")
        paper_results = await crawler.crawl_urls(SAMPLE_PAPER_URLS)

        for crawl_res in paper_results:
            if crawl_res.error:
                logger.error(f"Failed to crawl paper {crawl_res.url}: {crawl_res.error}")
                continue

            paper_data = paper_parser.parse(crawl_res.content, crawl_res.url)

            if paper_data.get("github_url"):
                gh_url, stars = await github_client.get_repo_stars(paper_data["github_url"])
                paper_data["github_url"] = gh_url
                paper_data["github_stars"] = stars

            # Validate record before database insertion
            RecordValidator.validate_research_paper(paper_data)
            stored = repo.insert_research_paper(paper_data)
            logger.info(f"Successfully validated & stored research paper ID {stored.id}: '{stored.title}'")

        # 2. Process Startup & Entity Resolution
        raw_startup_data = {
            "schemaVersion": "1.0",
            "recordType": "STARTUP",
            "content": {
                "entityName": "Open AI, Inc.",
                "data": {"employeeCount": 1500}
            },
            "source": {
                "name": "Public Press Release",
                "url": "https://openai.com/about"
            }
        }
        RecordValidator.validate_startup(raw_startup_data)
        
        # Resolve canonical entity name
        res = resolver.resolve(
            raw_name=raw_startup_data["content"]["entityName"],
            entity_type="STARTUP",
            known_canonical_names=["OpenAI", "Google DeepMind", "Anthropic"],
            source_url=raw_startup_data["source"]["url"]
        )
        # Store entity resolution log
        repo.insert_entity_mapping(res.to_dict())

        # Update startup record with canonical name
        raw_startup_data["content"]["entityName"] = res.canonical_name
        stored_startup = repo.insert_startup(raw_startup_data)
        logger.info(f"Successfully validated & stored canonical startup ID {stored_startup.id}: '{stored_startup.entity_name}'")

        # 3. Process Product Record
        sample_product_data = {
            "schemaVersion": "1.0",
            "recordType": "PRODUCT",
            "content": {
                "startupName": stored_startup.entity_name,
                "pricingModel": "FREEMIUM"
            },
            "source": {
                "name": "Official Product Site",
                "url": "https://openai.com/chatgpt"
            }
        }
        RecordValidator.validate_product(sample_product_data)
        stored_product = repo.insert_product(sample_product_data)
        logger.info(f"Successfully validated & stored product ID {stored_product.id}: '{stored_product.startup_name}' ({stored_product.pricing_model})")

        # 4. Process AI News Record
        sample_news_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="DeepMind Unveils Next-Gen AI System"/>
            <meta property="og:description" content="State of the art performance across multi-modal reasoning benchmarks."/>
            <meta property="article:published_time" content="2026-09-10T12:00:00Z"/>
        </head>
        <body><h1>DeepMind Unveils Next-Gen AI System</h1></body>
        </html>
        """
        news_data = news_parser.parse(
            sample_news_html,
            source_url="https://deepmind.google/discover/blog/next-gen-ai",
            source_name="Google DeepMind Blog"
        )
        RecordValidator.validate_news(news_data)
        stored_news = repo.insert_news(news_data)
        logger.info(f"Successfully validated & stored news ID {stored_news.id}: '{stored_news.title}' | Fresh (<24h): {stored_news.is_fresh}")

        # 5. Process AI Job Record
        sample_job_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "title": "Staff AI Research Engineer",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Google DeepMind"
                },
                "datePosted": "2026-09-10T08:30:00Z"
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        job_data = job_parser.parse(
            sample_job_html,
            source_url="https://careers.google.com/jobs/results/staff-ai-research-engineer",
            source_name="Google Careers"
        )
        RecordValidator.validate_job(job_data)
        stored_job = repo.insert_job(job_data)
        logger.info(f"Successfully validated & stored job ID {stored_job.id}: '{stored_job.title}' at '{stored_job.company_name}' | Fresh (<24h): {stored_job.is_fresh}")

        # 6. Generate CSV Exports
        exporter = CSVExporter()
        export_files = exporter.export_all()

        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION & CSV EXPORT SUMMARY:")
        print("=" * 60)
        for entity_name, filepath in export_files.items():
            print(f"  • {entity_name.upper():<20} -> {filepath}")
        print("=" * 60 + "\n")
        return export_files

    finally:
        await crawler.close()
        await github_client.close()


# Vercel Serverless Function HTTP Handler
class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function entry point."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_data = {
            "status": "success",
            "message": "AI Data Intelligence Pipeline API is online.",
            "pipeline": "AI Engineer Demo Pipeline",
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
        return


# Vercel WSGI/ASGI Top-Level Application Entry Point
def app(environ, start_response):
    """WSGI application entry point for Vercel Python runtime."""
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    start_response(status, headers)
    response_data = {
        "status": "success",
        "message": "AI Data Intelligence Pipeline API is online.",
        "pipeline": "AI Engineer Demo Pipeline",
    }
    return [json.dumps(response_data).encode('utf-8')]


# Alias for Vercel WSGI runner
application = app

if __name__ == "__main__":
    asyncio.run(run_pipeline())
