"""News feed pages and API endpoints."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

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


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request):
    demo = is_demo_mode()
    articles = _enriched_articles() if demo else []

    return templates.TemplateResponse(request, "news.html", {
        "demo_mode": demo,
        "articles": articles,
        "feeds": DEMO_FEED_NAMES if demo else [],
        "active_page": "news",
    })


@router.get("/news/{idx}", response_class=HTMLResponse)
async def news_detail(request: Request, idx: int):
    demo = is_demo_mode()
    articles = _enriched_articles() if demo else []

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
    if not is_demo_mode():
        return {"articles": [], "total": 0}

    articles = _enriched_articles()
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
