# AI Engineer Data Intelligence Pipeline

An asynchronous, fault-tolerant, and traceable data intelligence pipeline built in Python 3.11 for crawling, parsing, extracting, validating, and structuring AI domain knowledge (**Startups, Products, Research Papers, News, and Jobs**).

---

## Key Development Principles & Provenance Guarantees

1. **Source-of-Truth Principle**: The source webpage is the single source of truth. The system extracts real information from legitimate public sources and preserves source URLs for data provenance.
2. **Zero Data Hallucination**: The system NEVER fabricates, guesses, or hallucinates data (names, dates, employee counts, GitHub stars, or URLs). Missing fields default strictly to `null` (`None`).
3. **Deterministic First**: HTML metadata, JSON-LD, OpenGraph, and official APIs (e.g. GitHub REST API for star counts) are preferred over LLM calls. LLMs are used solely for semantic extraction.
4. **Resilient Asynchronous Crawling**: Built on `asyncio` and `aiohttp` with Playwright fallback for JS-rendered pages. Features per-domain rate limiting, bounded concurrency (`Semaphore`), exponential backoff with full jitter on HTTP 429 status codes, and smart HTML payload chunking on HTTP 413.
5. **Freshness Guarantee**: News and Job records enforce a strict 24-hour freshness rule (`current_time - publication_time <= 24 hours`). Missing publication dates evaluate `is_fresh` to `False` without guessing.
6. **Entity Resolution & Deduplication**: Canonical entity mapping with corporate suffix removal (`Inc`, `LLC`, `Corp`, `Ltd`), alias lookups, and fuzzy ratio scoring with audit logging for low-confidence matches.

---

## Repository Architecture

```text
AI_Engineer_Task/
│
├── .github/
│   └── copilot-instructions.md       # Development rules & project context
│
├── src/
│   ├── crawler/
│   │   ├── __init__.py               # Package exports
│   │   ├── http_client.py            # Async HTTP client (retries, backoff, jitter, 429/413 handling)
│   │   ├── playwright_client.py      # Async Playwright browser wrapper (lazy launch)
│   │   ├── github_client.py          # GitHub REST API client (stargazers_count extraction)
│   │   └── crawler.py                # High-level crawler (concurrency, domain rate limits, deduplication)
│   │
│   ├── parsers/
│   │   ├── __init__.py               # Package exports
│   │   ├── date_parser.py            # ISO normalization & 24-hour freshness engine
│   │   ├── paper_parser.py           # Deterministic arXiv paper HTML parser
│   │   ├── news_parser.py            # OpenGraph & JSON-LD news parser
│   │   └── job_parser.py             # Schema.org JobPosting parser
│   │
│   ├── llm/
│   │   ├── __init__.py               # Package exports
│   │   ├── base_provider.py          # Abstract LLMProvider interface & JSON cleaner
│   │   ├── gemini_provider.py        # Primary LLM provider (google-genai SDK)
│   │   ├── groq_provider.py          # 1st fallback provider (groq SDK)
│   │   ├── deepseek_provider.py      # 2nd fallback provider (openai SDK / DeepSeek endpoint)
│   │   ├── orchestrator.py           # Fallback chain orchestrator (Gemini -> Groq -> DeepSeek)
│   │   └── chunker.py                # HTML boilerplate stripper & semantic text chunker (413 handling)
│   │
│   ├── resolver/
│   │   ├── __init__.py               # Package exports
│   │   └── entity_resolver.py        # Entity normalization, alias matching & fuzzy resolution
│   │
│   ├── storage/
│   │   ├── __init__.py               # Package exports
│   │   ├── database.py               # SQLAlchemy engine & session factory
│   │   ├── models.py                 # Declarative ORM models for all entities
│   │   └── repository.py             # Database CRUD & unique URL deduplication
│   │
│   ├── validation/
│   │   ├── __init__.py               # Package exports
│   │   └── validators.py             # Record schema validator & pricing enum checker
│   │
│   ├── exporters/
│   │   ├── __init__.py               # Package exports
│   │   └── csv_exporter.py           # Pandas CSV export engine
│   │
│   └── main.py                       # Pipeline execution entry point
│
├── data/
│   ├── raw/                          # Raw crawled content cache
│   ├── processed/                    # Intermediate processed JSON artifacts
│   ├── exports/                      # Generated CSV exports
│   └── app.db                        # SQLite database file
│
├── tests/                            # Comprehensive unittest suite (46+ tests)
│   ├── test_setup.py
│   ├── test_crawler.py
│   ├── test_date_parser.py
│   ├── test_paper_parser.py
│   ├── test_storage.py
│   ├── test_github_client.py
│   ├── test_news_parser.py
│   ├── test_job_parser.py
│   ├── test_llm_orchestrator.py
│   ├── test_chunker.py
│   ├── test_entity_resolver.py
│   ├── test_validators.py
│   └── test_csv_exporter.py
│
├── .env.example                      # Configuration template
├── .gitignore                        # Git exclusion rules
├── requirements.txt                  # Python dependencies
├── README.md                         # Technical documentation
└── PRD.md                            # Product Requirements Document
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.11+ installed.

### 2. Clone & Environment Setup
```bash
git clone <repository_url>
cd AI_Engineer_Task

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
Example `.env`:
```ini
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GITHUB_TOKEN=your_github_personal_token
DATABASE_URL=sqlite:///data/app.db
MAX_CONCURRENCY=10
REQUEST_TIMEOUT=30
MAX_RETRIES=4
```

---

## Running the Pipeline

To run the end-to-end pipeline (crawling, deterministic parsing, entity resolution, validation, database insertion, and CSV exports):

```bash
python -m src.main
```

### Generated CSV Artifacts
After running `src/main.py`, CSV files are exported under `data/exports/`:
- `data/exports/research_papers.csv`
- `data/exports/startups.csv`
- `data/exports/products.csv`
- `data/exports/jobs.csv`
- `data/exports/news.csv`
- `data/exports/entity_mappings.csv`

---

## Running Tests

The test suite covers deterministic parsing, URL normalization, crawler backoff math, database deduplication, GitHub API mocking, LLM failover, content chunking, and CSV exports. **Unit tests mock external API calls and require zero paid LLM credits.**

```bash
python -m unittest discover -s tests
```

---

## LLM Provider Fallback Architecture

When semantic extraction is required, `LLMOrchestrator` executes an automated fallback chain:

```text
       Gemini (Primary: google-genai)
                  ↓ failure / no key
         Groq (Fallback 1: groq)
                  ↓ failure / no key
     DeepSeek (Fallback 2: openai SDK)
```

---

## Anti-Bot & Security Policy

- **No Bypass Attacks**: The system strictly respects anti-bot protections. It does NOT attempt illegal bypasses of CAPTCHA, Cloudflare, or authentication walls.
- **Official APIs & RSS**: Prefers official APIs (e.g. GitHub REST API) and public feeds.
- **Rate Limits & Jitter**: Enforces per-domain delays and exponential backoff with full jitter on HTTP 429.
- **Credential Protection**: API keys and tokens are loaded strictly via `.env` and never logged or committed.

---

## Scalability & Production Roadmap

For scaling from MVP (small datasets) to production scale (500,000+ records):

1. **Database Migration**: Switch `DATABASE_URL` from SQLite (`sqlite:///data/app.db`) to PostgreSQL (`postgresql://user:pass@localhost:5432/ai_intel`) via SQLAlchemy without changing application code.
2. **Distributed Crawling**: Introduce Redis + Celery/Temporal for distributed asynchronous task queues.
3. **Connection Pooling**: Use PgBouncer and `aiohttp.TCPConnector` connection pooling.
4. **Distributed LLM Rate-Limit Aware Schedulers**: Token bucket rate-limiter for LLM API calls across distributed worker pods.
