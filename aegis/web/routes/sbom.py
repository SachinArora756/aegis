"""SBOM inventory pages and API endpoints."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

from aegis.web.app import templates, is_demo_mode
from aegis.demo.data import (
    MOCK_SBOM_COMPONENTS,
    MOCK_SBOM_SCAN_RESULT,
    MOCK_VULNERABILITIES,
)

router = APIRouter()


def _build_components_with_vulns() -> list[dict]:
    vuln_map: dict[str, list[dict]] = {}
    for v in MOCK_VULNERABILITIES:
        key = f"{v['package_name']}@{v['package_version']}"
        vuln_map.setdefault(key, []).append(v)

    components = []
    for c in MOCK_SBOM_COMPONENTS:
        key = f"{c['component_name']}@{c['version']}"
        vulns = vuln_map.get(key, [])
        components.append({
            **c,
            "vuln_count": len(vulns),
            "vulns": vulns,
        })
    return components


@router.get("/sbom", response_class=HTMLResponse)
async def sbom_page(request: Request):
    demo = is_demo_mode()
    if demo:
        components = _build_components_with_vulns()
        repos = sorted(set(c["repo"] for c in MOCK_SBOM_COMPONENTS))
    else:
        components = []
        repos = []

    return templates.TemplateResponse(request, "sbom.html", {
        "demo_mode": demo,
        "components": components,
        "repos": repos,
        "repo_count": len(set(c["repo"] for c in components)) if components else 0,
        "component_count": len(components),
        "vuln_count": sum(1 for c in components if c.get("vuln_count", 0) > 0),
        "active_page": "sbom",
    })


@router.get("/api/sbom/components")
async def api_sbom_components(
    repo: str | None = Query(None),
    ecosystem: str | None = Query(None),
    search: str | None = Query(None),
):
    if not is_demo_mode():
        return {"components": [], "total": 0}

    components = list(MOCK_SBOM_COMPONENTS)
    if repo:
        components = [c for c in components if c["repo"] == repo]
    if ecosystem:
        components = [c for c in components if c["ecosystem"] == ecosystem]
    if search:
        q = search.lower()
        components = [
            c for c in components
            if q in c["component_name"].lower() or q in c.get("purl", "").lower()
        ]
    return {"components": components, "total": len(components)}


@router.get("/api/sbom/vulnerabilities")
async def api_sbom_vulnerabilities():
    if not is_demo_mode():
        return {"vulnerabilities": [], "total": 0}
    return {"vulnerabilities": MOCK_VULNERABILITIES, "total": len(MOCK_VULNERABILITIES)}


@router.get("/api/sbom/scan-result")
async def api_sbom_scan_result():
    if not is_demo_mode():
        return {"error": "No scan results available outside demo mode"}
    return MOCK_SBOM_SCAN_RESULT
