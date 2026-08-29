# Aegis

Supply-chain risk tracker that connects SBOM/SCA scanning with real-time threat intelligence to generate repo-specific vulnerability alerts.

## What It Does

Aegis runs two pipelines — **SBOM/SCA** and **News Ingestion** — connected by a **Match Engine** that turns generic threat intel into actionable, repo-specific alerts. A **RAG-powered chatbot** lets you ask natural-language questions about your supply chain security posture.

### Pipeline Overview

```
SBOM/SCA Pipeline          News Ingestion Agent
  Cartograph                   22 RSS feeds + APIs
  Auditor                      Relevance filter
  Fuse (PURL merge)            3-phase dedup
  Sentinel                     LLM enrichment (Claude)
  Licenser                     Version recovery
        \                    /
         --- Match Engine ---
               |
          Validator (ECS)
               |
         Ask Aegis (RAG)
               |
        Slack / Dashboard
```

### Key Features

- **SBOM Scanning**: Discovers dependencies via Cartograph, scans for vulnerabilities via Sentinel, resolves licenses via a 4-tier pipeline (pattern rules, deps.dev, GitHub, manual)
- **News Ingestion**: Monitors 22 security feeds (Socket.dev, Snyk, CISA, NVD, etc.), filters by relevance, deduplicates with fuzzy + LLM matching, enriches via Claude
- **Match Engine**: Cross-references news articles against your SBOM inventory, identifies vulnerable repos with semver comparison
- **Validator**: Spawns ECS Fargate tasks for reachability analysis — confirms if vulnerable code paths are actually exercised
- **Ask Aegis (RAG Chatbot)**: Natural-language Q&A about your supply chain — retrieves from SBOM, news, match results, and remediation guides
- **Remediation Engine**: Generates prioritized fix steps with per-repo commands when vulnerabilities are found
- **Web Dashboard**: Real-time overview of components, vulnerabilities, news feed, match results, and interactive chatbot

## Quick Start (Demo Mode)

Demo mode runs the full pipeline with mock data — no API keys, database, or external tools required.

```bash
# Clone and install
git clone https://github.com/SachinArora756/aegis.git
cd aegis
pip install -e .

# Run the web dashboard (demo mode)
aegis web --demo --port 3000

# Open http://localhost:3000 in your browser
```

### Demo CLI Commands

```bash
# Full pipeline demo in terminal
aegis demo full

# Individual stages
aegis demo sbom
aegis demo news
aegis demo match

# RAG chatbot demo
aegis demo chat

# Interactive chat session
aegis rag chat --demo
```

## Production Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (with pgvector extension for RAG)
- Docker (optional, for Postgres)
- Cartograph, Auditor, and Sentinel CLI tools (bundled)

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:

| Variable | Purpose | Cost |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Free (AWS RDS free tier) |
| `GEMINI_API_KEY` | Google Gemini for LLM enrichment + chat | Free (15 RPM) |
| `HF_API_KEY` | Hugging Face embeddings for RAG | Free |
| `SLACK_BOT_TOKEN` | Slack alerts | Free |
| `SLACK_CHANNEL_ID` | Target Slack channel | Free |

Get your free API keys:
- **Gemini**: https://aistudio.google.com/apikey
- **Hugging Face**: https://huggingface.co/settings/tokens

### 3. Initialize Database

```bash
aegis init-db
```

### 4. Run Pipelines

```bash
# Scan a repository
aegis sbom scan ./path/to/repo

# Run news ingestion
aegis news run

# Continuous monitoring
aegis news watch --interval 30

# Manual match
aegis match <news_id>

# Web dashboard
aegis web --port 3000

# Index knowledge base
aegis rag index
```

## Project Structure

```
aegis/
  cli.py              CLI entry point (Click)
  config.py           Pydantic Settings (env-based config)
  db/
    engine.py          Async SQLAlchemy engine
    models.py          ORM models (8 tables)
  sbom/
    scanner.py         SBOM/SCA pipeline orchestrator
    cartograph.py      SBOM generation
    auditor.py         License scanning
    fuse.py            PURL-based SBOM merge
    sentinel.py        Vulnerability scanning
    licenser.py        4-tier license resolution
  news/
    agent.py           News ingestion orchestrator
    fetcher.py         RSS + API fetcher (22 sources)
    filter.py          Keyword relevance filter
    dedup.py           3-phase deduplication
    enricher.py        Claude-based classification
  match/
    engine.py          SBOM x News cross-reference
  validator/
    dispatcher.py      ECS Fargate task spawner
  notify/
    slack.py           Slack alert formatting
  rag/
    embedder.py        Text embedding (Voyage AI / mock)
    store.py           Vector store (pgvector / in-memory)
    retriever.py       Context retrieval
    chat.py            Chat engine (Claude / mock)
    remediation.py     Fix recommendation engine
    knowledge.py       Static remediation guides
    ingest.py          Data indexing pipeline
  demo/
    runner.py          CLI demo runner
    data.py            Mock SBOM, news, match data
    rag_data.py        Mock chat, incidents, remediation data
  web/
    app.py             FastAPI application factory
    routes/            Route modules (dashboard, sbom, news, match, chat, demo)
    templates/         Jinja2 HTML templates
    static/            JS + CSS assets
```

## Web Dashboard Pages

| Page | URL | Description |
|---|---|---|
| Dashboard | `/` | Overview stats, severity breakdown, recent activity |
| SBOM Inventory | `/sbom` | Component browser, vulnerability list, scan results |
| News Feed | `/news` | Enriched security articles with classification |
| Match Results | `/match` | Cross-reference results grouped by incident |
| Ask Aegis | `/chat` | RAG-powered security chatbot |
| Live Demo | `/demo` | Interactive pipeline visualization with streaming |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy (async), Click
- **Database**: PostgreSQL 16 + pgvector
- **AI/ML**: Google Gemini (enrichment + chat, free tier), Hugging Face (embeddings, free tier)
- **Frontend**: Jinja2, Tailwind CSS, vanilla JS, WebSocket streaming
- **Scanning**: Cartograph (SBOM), Auditor (licenses), Sentinel (vulnerabilities)
- **Alerts**: Slack Bot API
- **Infra**: Docker Compose, AWS ECS Fargate (validator)

## License

MIT
