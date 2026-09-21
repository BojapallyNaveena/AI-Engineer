# AI Engineer Data Intelligence Pipeline

An asynchronous, fault-tolerant, and traceable **Data Intelligence Pipeline** built with Python 3.11 for crawling, parsing, extracting, validating, resolving, and structuring AI-domain knowledge.

The pipeline collects and processes information related to:

- 🚀 Startups
- 📦 Products
- 📄 Research Papers
- 📰 News
- 💼 Jobs

---

## 1. What is this project?

This project is an **AI Data Intelligence Pipeline** designed to automatically collect and transform publicly available AI-domain information into structured and validated datasets.

The pipeline follows a complete data processing flow:

```text
Public Web Sources
       ↓
Async Web Crawling
       ↓
Deterministic Parsing
       ↓
LLM Semantic Extraction
       ↓
Entity Resolution
       ↓
Data Validation
       ↓
Database Storage
       ↓
CSV Export
The system is designed to be asynchronous, fault-tolerant, traceable, and scalable.

It supports multiple AI-related entities including startups, products, research papers, news articles, and job postings.

A major focus of the project is data provenance and accuracy. Source URLs are preserved so that extracted information can always be traced back to its original webpage.

2. Why did I build this project?

Large-scale AI ecosystems contain information spread across thousands of different websites and data sources.

Manually collecting information about startups, products, research papers, news, and jobs is:

Time-consuming
Difficult to maintain
Difficult to validate
Prone to duplicate records
Difficult to scale

This project was built to automate that process while maintaining strong data-quality guarantees.

Key development principles
Source-of-Truth Principle

The original webpage is treated as the source of truth.

The system extracts information from legitimate public sources and preserves the original source URL for provenance.

Zero Data Hallucination

The system does not fabricate or guess missing information.

If a value cannot be reliably extracted, it is stored as:

null / None

This applies to information such as:

Company names
Dates
Employee counts
GitHub stars
URLs
Pricing information
Deterministic First

The system prioritizes deterministic extraction techniques before using an LLM.

It first checks:

HTML metadata
JSON-LD
OpenGraph metadata
Official APIs
Structured webpage information

For example, GitHub star counts are obtained using the GitHub REST API instead of asking an LLM to estimate them.

Freshness Guarantee

News and job records follow a strict 24-hour freshness rule.

current_time - publication_time <= 24 hours

If the publication date is missing, the record is automatically considered:

is_fresh = False

The system never guesses the publication date.

3. How does the project work?

The pipeline consists of multiple independent modules that work together.

Step 1: Web Crawling

The crawler uses asynchronous HTTP requests to collect webpage content.

The system uses:

asyncio
aiohttp
Playwright fallback
Bounded concurrency
Per-domain rate limiting
Exponential backoff
Full jitter
HTTP 429 handling
HTTP 413 handling

For JavaScript-rendered websites, Playwright can be used as a fallback when normal HTTP requests are insufficient.

Step 2: Deterministic Parsing

Before using an LLM, the pipeline attempts to extract information using deterministic methods.

Examples include:

HTML Metadata
     ↓
JSON-LD
     ↓
OpenGraph
     ↓
Official API

Specialized parsers process different types of information:

Research paper parser
News parser
Job parser
Date parser

This reduces unnecessary LLM usage and improves consistency.

Step 3: Semantic Extraction Using LLMs

When deterministic extraction is insufficient, the pipeline uses an LLM for semantic extraction.

The LLM architecture contains multiple providers:

Gemini
   ↓ failure / unavailable
Groq
   ↓ failure / unavailable
DeepSeek

This provides automatic fallback when one provider fails or is unavailable.

The LLM is used for semantic extraction, not for inventing missing information.

Step 4: Content Chunking

Large webpages can exceed model context limits.

The pipeline therefore:

Removes unnecessary HTML boilerplate.
Extracts meaningful text.
Splits content into semantic chunks.
Sends manageable chunks to the LLM.

This helps handle large HTML payloads and HTTP 413/context-size problems.

Step 5: Entity Resolution

Different sources may refer to the same organization using different names.

For example:

OpenAI Inc.
OpenAI LLC
OpenAI

The entity resolver normalizes company names and attempts to identify whether they represent the same entity.

It supports:

Corporate suffix removal
Alias matching
Canonical entity mapping
Fuzzy matching
Confidence scoring
Audit logging

Low-confidence matches are logged for review instead of silently being treated as exact matches.

Step 6: Data Validation

Before storing records, the pipeline validates the extracted information.

Validation includes:

Record schema validation
Required-field checks
Data-type validation
Pricing enum validation
Freshness validation
URL validation

Invalid or incomplete records are prevented from silently entering the final dataset.

Step 7: Database Storage

Validated records are stored using:

SQLAlchemy
+
SQLite

The repository layer handles:

CRUD operations
Database sessions
Unique URL checks
Deduplication

The database can later be migrated from SQLite to PostgreSQL without changing the overall application architecture.

Step 8: CSV Export

After processing, structured datasets are exported using Pandas.

Generated files include:

research_papers.csv
startups.csv
products.csv
jobs.csv
news.csv
entity_mappings.csv
4. What technologies did I use?
Programming Language
Python 3.11+
Web Crawling
asyncio
aiohttp
Playwright
Data Parsing
HTML metadata
JSON-LD
OpenGraph
Schema.org
Custom Python parsers
AI / LLM
Google Gemini
Groq
DeepSeek
google-genai
groq
OpenAI-compatible SDK
Database
SQLite
SQLAlchemy
Data Processing
Pandas
JSON
CSV
APIs
GitHub REST API
Validation
Custom schema validators
Pricing enum validation
Freshness validation
Testing
Python unittest
Mocked external API calls
Development
Python Virtual Environment
Git
GitHub
.env configuration
5. What is the result?

The result is a modular AI Data Intelligence Pipeline capable of transforming public web information into structured, validated, and traceable datasets.

The project provides:

✅ Asynchronous web crawling
✅ Fault-tolerant HTTP requests
✅ 429 rate-limit handling
✅ 413 payload handling
✅ Playwright fallback
✅ Deterministic extraction
✅ LLM semantic extraction
✅ Multi-provider LLM fallback
✅ Entity resolution
✅ Deduplication
✅ 24-hour news/job freshness validation
✅ Database persistence
✅ CSV exports
✅ Source URL provenance
✅ Credential protection
✅ Comprehensive unit testing

The test suite contains 46+ tests covering:

Crawler behavior
Date parsing
URL normalization
Database deduplication
GitHub API mocking
News parsing
Job parsing
LLM failover
Content chunking
Entity resolution
Validation
CSV exporting

External API calls are mocked during testing, so the test suite does not require paid LLM credits.

Repository Architecture
AI_Engineer_Task/
│
├── .github/
│   └── copilot-instructions.md
│
├── src/
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── http_client.py
│   │   ├── playwright_client.py
│   │   ├── github_client.py
│   │   └── crawler.py
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── date_parser.py
│   │   ├── paper_parser.py
│   │   ├── news_parser.py
│   │   └── job_parser.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── gemini_provider.py
│   │   ├── groq_provider.py
│   │   ├── deepseek_provider.py
│   │   ├── orchestrator.py
│   │   └── chunker.py
│   │
│   ├── resolver/
│   │   ├── __init__.py
│   │   └── entity_resolver.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validators.py
│   │
│   ├── exporters/
│   │   ├── __init__.py
│   │   └── csv_exporter.py
│   │
│   └── main.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── exports/
│   └── app.db
│
├── tests/
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
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── PRD.md
LLM Provider Fallback Architecture

The project uses a fallback architecture to improve reliability during semantic extraction.

             Gemini
          Primary LLM
               │
               ▼
        Failure / No Key
               │
               ▼
             Groq
          Fallback 1
               │
               ▼
        Failure / No Key
               │
               ▼
           DeepSeek
          Fallback 2

This allows the pipeline to continue when the primary LLM provider is unavailable.

Anti-Bot & Security

The pipeline follows responsible crawling practices.

No Bypass Attacks

The system does not attempt to bypass:

CAPTCHA
Cloudflare protections
Authentication walls
Other access-control mechanisms
Official APIs

Whenever possible, the system prefers:

Official APIs
Public RSS feeds
Public webpages
Rate Limiting

The crawler implements:

Per-domain delays
Bounded concurrency
Exponential backoff
Full jitter
HTTP 429 handling
Credential Protection

API keys and tokens are loaded through environment variables.

Sensitive credentials are never intentionally logged or committed to the repository.

Setup & Installation
Prerequisites

Python 3.11 or higher.

Clone the Repository
git clone <repository_url>
cd AI_Engineer_Task
Create Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
macOS / Linux
python -m venv venv
source venv/bin/activate
Install Dependencies
pip install -r requirements.txt
Environment Configuration

Copy the example environment file:

cp .env.example .env

Configure the required credentials:

GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GITHUB_TOKEN=your_github_personal_token

DATABASE_URL=sqlite:///data/app.db

MAX_CONCURRENCY=10
REQUEST_TIMEOUT=30
MAX_RETRIES=4
Running the Pipeline

Run the complete pipeline using:

python -m src.main

The pipeline performs:

Crawling
   ↓
Parsing
   ↓
LLM Extraction
   ↓
Entity Resolution
   ↓
Validation
   ↓
Database Storage
   ↓
CSV Export
Generated CSV Files

After successful execution:

data/exports/
│
├── research_papers.csv
├── startups.csv
├── products.csv
├── jobs.csv
├── news.csv
└── entity_mappings.csv
Running Tests

Run the complete test suite:

python -m unittest discover -s tests

The tests cover:

Crawler
Date Parser
Paper Parser
News Parser
Job Parser
Storage
GitHub Client
LLM Orchestrator
Chunker
Entity Resolver
Validators
CSV Exporter

External APIs are mocked during testing, so paid LLM credits are not required.

Scalability & Production Roadmap

The current project is designed as an MVP but can be extended for large-scale data processing.

1. Database Migration

Move from:

SQLite

to:

PostgreSQL

using SQLAlchemy.

Example:

postgresql://user:password@localhost:5432/ai_intel

The application architecture can remain largely unchanged.

2. Distributed Crawling

Introduce distributed task processing using technologies such as:

Redis
+
Celery / Temporal

This would allow crawling workloads to be distributed across multiple workers.

3. Connection Pooling

Use:

PgBouncer
+
aiohttp.TCPConnector

to improve database and HTTP connection management.

4. Distributed LLM Rate-Limit Scheduling

Implement token-bucket based rate limiting across distributed workers to manage LLM API limits efficiently.

Project Summary
Question	Answer
What?	AI Data Intelligence Pipeline
Why?	Automate reliable collection and structuring of AI-domain information
How?	Async crawling → deterministic parsing → LLM extraction → entity resolution → validation → storage → CSV
Technologies?	Python, asyncio, aiohttp, Playwright, Gemini, Groq, DeepSeek, SQLAlchemy, SQLite, Pandas
Result?	Fault-tolerant, traceable, validated and scalable AI intelligence datasets
Key Learning Outcomes

Through this project, I worked with:

Asynchronous programming
Web crawling
API integration
LLM orchestration
Fault-tolerant systems
Rate-limit handling
Data validation
Entity resolution
Deduplication
Database architecture
CSV data pipelines
Unit testing
Security and credential management
Production scalability concepts
Author

Naveena Bojapally

CS (AI & ML) Student | AI Engineer | Full Stack Developer

Connect With Me
GitHub: https://github.com/BojapallyNaveena
LinkedIn: https://linkedin.com/in/bojapally-naveena-27b5bb34a
LeetCode: https://leetcode.com/u/naveena_37/
Open to Work 🚀

I am open to opportunities in:

AI Engineering
Software Development
Full Stack Development
Python Development
Data Engineering
Machine Learning
