"""Match engine results pages and API endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from aegis.web.app import templates, is_demo_mode
from aegis.demo.data import (
    MOCK_MATCH_RESULTS,
    MOCK_RSS_ARTICLES,
    MOCK_ENRICHMENT_RESULTS,
)

router = APIRouter()


def _build_match_incidents() -> list[dict]:
    incidents = []
    for article in MOCK_RSS_ARTICLES:
        enrichment = MOCK_ENRICHMENT_RESULTS.get(article["url"], {})
        if enrichment.get("classification") != "supply_chain_vuln":
            continue

        affected = enrichment.get("affected_packages", [])
        packages = []
        for pkg in affected:
            name = pkg["name"]
            result = MOCK_MATCH_RESULTS.get(name, {})
            packages.append({
                "name": name,
                "ecosystem": pkg.get("ecosystem", ""),
                "vulnerable_versions": pkg.get("vulnerable_versions", ""),
                "status": result.get("status", "not_found"),
                "total_repos_using": result.get("total_repos_using", 0),
                "safe_repos_count": result.get("safe_repos_count", 0),
                "vulnerable_repos": result.get("vulnerable_repos", []),
                "safe_repos_sample": result.get("safe_repos_sample", []),
                "validator_status": None,
            })

        severity = "critical" if enrichment.get("impact_score", 0) >= 8 else (
            "high" if enrichment.get("impact_score", 0) >= 6 else "medium"
        )

        incidents.append({
            "title": article["title"],
            "source": article["source"],
            "published": article["published"],
            "impact_score": enrichment.get("impact_score", 0),
            "severity": severity,
            "packages": packages,
        })
    return incidents


@router.get("/match", response_class=HTMLResponse)
async def match_page(request: Request):
    demo = is_demo_mode()
    incidents = _build_match_incidents() if demo else []

    vulnerable_count = sum(
        1 for inc in incidents for pkg in inc.get("packages", [])
        if pkg.get("status") == "found_vulnerable"
    )
    safe_count = sum(
        pkg.get("safe_repos_count", 0) for inc in incidents for pkg in inc.get("packages", [])
    )
    not_found_count = sum(
        1 for inc in incidents for pkg in inc.get("packages", [])
        if pkg.get("status") == "not_found"
    )

    return templates.TemplateResponse(request, "match.html", {
        "demo_mode": demo,
        "incidents": incidents,
        "vulnerable_count": vulnerable_count,
        "safe_count": safe_count,
        "not_found_count": not_found_count,
        "active_page": "match",
    })


@router.get("/api/match/results")
async def api_match_results():
    if not is_demo_mode():
        return {"results": {}, "total": 0}
    return {"results": MOCK_MATCH_RESULTS, "total": len(MOCK_MATCH_RESULTS)}


@router.get("/api/match/incidents")
async def api_match_incidents():
    if not is_demo_mode():
        return {"incidents": []}
    return {"incidents": _build_match_incidents()}
