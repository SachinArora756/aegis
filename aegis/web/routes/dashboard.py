"""Dashboard page — main landing page showing pipeline overview."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

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


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    demo = is_demo_mode()
    if demo:
        stats = _build_demo_stats()
        alerts = _build_demo_alerts()
        pipelines = _build_demo_pipelines()
    else:
        stats = {
            "repos_scanned": 0, "total_components": 0,
            "active_vulns": 0, "articles_today": 0,
        }
        alerts = []
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
    return {"repos_scanned": 0, "total_components": 0, "active_vulns": 0, "articles_today": 0}
