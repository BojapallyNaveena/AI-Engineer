# Product Requirements Document (PRD) — AI Data Intelligence Pipeline

## 1. System Vision & Objective
The AI Data Intelligence Pipeline is a traceable, production-minded system designed to crawl, parse, extract, normalize, validate, and store structured data about:
- **AI Startups**
- **AI Products**
- **AI Research Papers**
- **AI News**
- **AI Jobs**

## 2. Core Guarantees & Constraints
1. **Provenance & Source of Truth**: The source webpage is the single source of truth. Every record preserves `source.name`, `source.url`, and collection timestamps (`collectedAt`).
2. **Zero Data Hallucination**: Never invent startup names, product names, employee counts, publication dates, GitHub URLs, star counts, pricing models, or news content. Unavailable values MUST be set to `null` (`None`).
3. **Deterministic First**: HTML metadata, JSON-LD, OpenGraph, and official REST APIs (e.g. GitHub API for star counts) are preferred over LLM calls.
4. **Resilient Crawling**: Bounded concurrency (`Semaphore`), exponential backoff with full jitter on HTTP 429, `Retry-After` header parsing, HTML payload chunking on HTTP 413, and per-domain rate limiting.
5. **Freshness Filter**: News and Job records published within the last 24 hours (`current_time - publication_time <= 24 hours`) are flagged with `is_fresh = True`. Unestablished dates default to `is_fresh = False`.
6. **LLM Orchestration**: Primary provider **Gemini** -> 1st fallback **Groq** -> 2nd fallback **DeepSeek**.
7. **Entity Resolution**: Deterministic normalization (removing legal suffixes like `Inc`, `LLC`, `Corp`, `Ltd`), alias lookup mapping, and fuzzy sequence matching with audit logging for low-confidence resolutions.
8. **Validation & Storage**: Record schema validation (pricing model enum: `FREE`, `FREEMIUM`, `PAID`, `ENTERPRISE`, or `null`), SQLite ORM database storage, and pandas CSV exports.

## 3. Implementation Status (All 16 Phases Complete)
- [x] **Phase 1**: Project structure, `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `PRD.md`.
- [x] **Phase 2**: Asynchronous HTTP crawler (`http_client.py`, `playwright_client.py`, `crawler.py`).
- [x] **Phase 3**: Research paper deterministic HTML extraction (`paper_parser.py`, `date_parser.py`).
- [x] **Phase 4**: SQLite storage & ORM models (`database.py`, `models.py`, `repository.py`).
- [x] **Phase 5**: GitHub REST API repository & star extraction (`github_client.py`).
- [x] **Phase 6 & 7**: AI News & Job parsers with 24-hour freshness engine (`news_parser.py`, `job_parser.py`).
- [x] **Phase 8 & 9**: LLM provider interface & fallback orchestrator (`base_provider.py`, `gemini_provider.py`, `groq_provider.py`, `deepseek_provider.py`, `orchestrator.py`).
- [x] **Phase 10**: 413 Payload chunking (`chunker.py`).
- [x] **Phase 11**: 429 Retry & backoff math with jitter.
- [x] **Phase 12**: Entity resolution & normalization (`entity_resolver.py`).
- [x] **Phase 13**: Record schema validation (`validators.py`).
- [x] **Phase 14**: CSV exports engine (`csv_exporter.py`).
- [x] **Phase 15**: Test suite verification (46 unit tests passing).
- [x] **Phase 16**: Final technical documentation & architecture guide.
