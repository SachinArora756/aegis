"""Dashboard page — main landing page showing pipeline overview."""

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from aegis.web.app import templates, is_demo_mode
from aegis.demo.data import (
    MOCK_SBOM_COMPONENTS,
    MOCK_RSS_ARTICLES,
    MOCK_ENRICHMENT_RESULTS,
    MOCK_VULNERABILITIES,
    MOCK_MATCH_RESULTS,
)

router = APIRouter()


def _build_demo_stats() -> dict:
    repos = set(c["repo"] for c in MOCK_SBOM_COMPONENTS)
    vuln_articles = [
        a for a in MOCK_RSS_ARTICLES
        if MOCK_ENRICHMENT_RESULTS.get(a["url"], {}).get("classification") == "supply_chain_vuln"
    ]
    return {
        "repos_scanned": len(repos),
        "total_components": len(MOCK_SBOM_COMPONENTS),
        "active_vulns": len(MOCK_VULNERABILITIES),
        "articles_today": len(MOCK_RSS_ARTICLES),
    }


def _build_demo_alerts() -> list[dict]:
    alerts = []
    for article in MOCK_RSS_ARTICLES:
        enrichment = MOCK_ENRICHMENT_RESULTS.get(article["url"])
        if enrichment:
            alerts.append({
                "title": article["title"],
                "source": article["source"],
                "published": article["published"],
                "classification": enrichment["classification"],
                "impact_score": enrichment["impact_score"],
                "summary": enrichment["summary"],
                "affected_packages": enrichment.get("affected_packages", []),
            })
    alerts.sort(key=lambda a: a["impact_score"], reverse=True)
    return alerts[:10]


def _build_demo_pipelines() -> list[dict]:
    return [
        {
            "name": "SBOM Scan",
            "status": "success",
            "last_run": "2026-08-29 08:00 UTC",
            "run_url": "/demo",
        },
        {
            "name": "News Ingestion",
            "status": "success",
            "last_run": "2026-08-29 15:30 UTC",
            "run_url": "/demo",
        },
        {
            "name": "Match Engine",
            "status": "success",
            "last_run": "2026-08-29 15:35 UTC",
            "run_url": "/demo",
        },
    ]


async def _build_prod_stats() -> dict:
    from aegis.db.engine import get_session

    async with get_session() as session:
        repos = (await session.execute(
            text("SELECT COUNT(DISTINCT repo) FROM aegis_sbom")
        )).scalar() or 0
        components = (await session.execute(
            text("SELECT COUNT(*) FROM aegis_sbom")
        )).scalar() or 0
        articles = (await session.execute(
            text("SELECT COUNT(*) FROM aegis_news")
        )).scalar() or 0
        matches = (await session.execute(
            text("SELECT COUNT(*) FROM aegis_match_result WHERE is_vulnerable = true")
        )).scalar() or 0

    return {
        "repos_scanned": repos,
        "total_components": components,
        "active_vulns": matches,
        "articles_today": articles,
    }


async def _build_prod_alerts() -> list[dict]:
    from aegis.db.engine import get_session

    async with get_session() as session:
        rows = await session.execute(
            text(
                "SELECT title, source, classification, impact_score, summary "
                "FROM aegis_news ORDER BY created_at DESC LIMIT 10"
            )
        )
        alerts = []
        for row in rows:
            alerts.append({
                "title": row[0],
                "source": row[1],
                "published": "",
                "classification": row[2],
                "impact_score": row[3] or 0,
                "summary": row[4] or "",
                "affected_packages": [],
            })
    return alerts


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    demo = is_demo_mode()
    if demo:
        stats = _build_demo_stats()
        alerts = _build_demo_alerts()
        pipelines = _build_demo_pipelines()
    else:
        stats = await _build_prod_stats()
        alerts = await _build_prod_alerts()
        pipelines = []

    return templates.TemplateResponse(request, "dashboard.html", {
        "demo_mode": demo,
        "stats": stats,
        "alerts": alerts,
        "pipelines": pipelines,
        "active_page": "dashboard",
    })


@router.get("/api/stats")
async def api_stats():
    if is_demo_mode():
        return _build_demo_stats()
    return await _build_prod_stats()
