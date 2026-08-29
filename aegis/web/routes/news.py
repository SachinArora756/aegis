"""News feed pages and API endpoints."""

import json

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from aegis.web.app import templates, is_demo_mode
from aegis.demo.data import (
    MOCK_RSS_ARTICLES,
    MOCK_ENRICHMENT_RESULTS,
    MOCK_MATCH_RESULTS,
    DEMO_FEED_NAMES,
)

router = APIRouter()


def _enriched_articles() -> list[dict]:
    articles = []
    for article in MOCK_RSS_ARTICLES:
        enrichment = MOCK_ENRICHMENT_RESULTS.get(article["url"], {})
        articles.append({
            **article,
            "classification": enrichment.get("classification", "unknown"),
            "impact_score": enrichment.get("impact_score", 0),
            "enriched_summary": enrichment.get("summary", article["summary"]),
            "affected_packages": enrichment.get("affected_packages", []),
            "enrichment": enrichment if enrichment else None,
        })
    return articles


async def _prod_articles() -> list[dict]:
    from aegis.db.engine import get_session

    async with get_session() as session:
        rows = await session.execute(
            text(
                "SELECT id, title, url, source, summary, classification, "
                "impact_score, affected_packages, created_at "
                "FROM aegis_news ORDER BY created_at DESC LIMIT 200"
            )
        )
        articles = []
        for r in rows:
            pkgs = r[7]
            if isinstance(pkgs, str):
                try:
                    pkgs = json.loads(pkgs)
                except (json.JSONDecodeError, TypeError):
                    pkgs = []
            articles.append({
                "title": r[1],
                "url": r[2],
                "source": r[3],
                "summary": r[4] or "",
                "classification": r[5] or "unknown",
                "impact_score": r[6] or 0,
                "affected_packages": pkgs or [],
                "published": str(r[8]) if r[8] else "",
                "enriched_summary": r[4] or "",
            })
    return articles


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request):
    demo = is_demo_mode()
    if demo:
        articles = _enriched_articles()
        feeds = DEMO_FEED_NAMES
    else:
        articles = await _prod_articles()
        feeds = sorted(set(a["source"] for a in articles))

    return templates.TemplateResponse(request, "news.html", {
        "demo_mode": demo,
        "articles": articles,
        "feeds": feeds,
        "active_page": "news",
    })


@router.get("/news/{idx}", response_class=HTMLResponse)
async def news_detail(request: Request, idx: int):
    demo = is_demo_mode()
    articles = _enriched_articles() if demo else await _prod_articles()

    if idx < 0 or idx >= len(articles):
        return templates.TemplateResponse(request, "news_detail.html", {
            "demo_mode": demo,
            "article": None,
            "match_results": None,
            "active_page": "news",
        })

    article = articles[idx]
    match_results = {}
    if demo and article.get("affected_packages"):
        for pkg in article["affected_packages"]:
            name = pkg["name"]
            if name in MOCK_MATCH_RESULTS:
                match_results[name] = MOCK_MATCH_RESULTS[name]

    return templates.TemplateResponse(request, "news_detail.html", {
        "demo_mode": demo,
        "article": article,
        "match_results": match_results,
        "active_page": "news",
    })


@router.get("/api/news/articles")
async def api_news_articles(
    classification: str | None = Query(None),
    search: str | None = Query(None),
):
    if is_demo_mode():
        articles = _enriched_articles()
    else:
        articles = await _prod_articles()

    if classification and classification != "all":
        articles = [a for a in articles if a["classification"] == classification]
    if search:
        q = search.lower()
        articles = [a for a in articles if q in a["title"].lower() or q in a.get("summary", "").lower()]
    return {"articles": articles, "total": len(articles)}


@router.get("/api/news/feeds")
async def api_news_feeds():
    if not is_demo_mode():
        return {"feeds": []}
    return {"feeds": DEMO_FEED_NAMES}
