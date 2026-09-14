# Copilot Instructions — AI Engineer Demo Task

## 1. Project context
This repository implements an AI Engineer demo task for a data intelligence pipeline.
The system collects and processes information about:
* AI startups
* AI products
* AI research papers
* AI news
* AI jobs

The system must extract real information from legitimate public sources and preserve source URLs for data provenance.
The system must never fabricate, guess, or hallucinate data.
If information is not available from the source, use `null` rather than inventing a value.

---

## 2. Primary development principle
Build the project incrementally. Do NOT generate the entire application at once.
For every requested feature:
1. Explain briefly what the feature does.
2. Identify the files that need to be created or modified.
3. Make the smallest reasonable implementation.
4. Keep existing working functionality unchanged.
5. Run or provide tests for the new functionality.
6. Fix errors before moving to the next feature.
7. Do not modify unrelated files.

Prefer simple, maintainable solutions over unnecessary complexity.

---

## 3. Technology requirements
* Python 3.11
* asyncio, aiohttp, BeautifulSoup, Playwright
* pandas, SQLAlchemy, SQLite, python-dotenv, pytest
* LLM providers: Gemini (primary) -> Groq (fallback 1) -> DeepSeek (fallback 2)
