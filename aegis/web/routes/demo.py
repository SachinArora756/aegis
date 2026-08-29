"""Demo mode routes — WebSocket streaming of pipeline execution."""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from aegis.web.app import templates, is_demo_mode

router = APIRouter()


@router.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    return templates.TemplateResponse(request, "demo.html", {
        "demo_mode": is_demo_mode(),
        "active_page": "demo",
    })


async def _send(ws: WebSocket, style: str, text: str, **extra):
    """Send a terminal line event. Format matches what demo.js handleEvent expects."""
    msg = {"type": "line", "text": text, "style": style, **extra}
    await ws.send_json(msg)
    await asyncio.sleep(0.02)


async def _send_phase(ws: WebSocket, name: str, phase: int):
    await ws.send_json({"type": "phase", "name": name, "text": name, "phase": phase})
    await asyncio.sleep(0.02)


async def _send_highlight(ws: WebSocket, node: str, state: str):
    await ws.send_json({"type": "highlight", "node": node, "state": state})
    await asyncio.sleep(0.02)


async def _send_box(ws: WebSocket, lines: list[str]):
    await ws.send_json({"type": "box", "lines": lines})
    await asyncio.sleep(0.02)


async def _stream_sbom(ws: WebSocket, fast: bool):
    delay = 0.1 if fast else 0.6
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    await _send(ws, "header", "SIDE A: SBOM / SCA Pipeline — Scanning: checkout-service")
    await asyncio.sleep(delay)

    await _send(ws, "step", "[1/6] Running Cartograph scan (wraps syft)...")
    await _send(ws, "detail", "    Target: ./checkout-service")
    await _send(ws, "detail", "    Format: CycloneDX JSON")
    await asyncio.sleep(delay * 1.5)
    await _send(ws, "ok", "  ✓ Cartograph found 142 components (0.8s)")

    await _send(ws, "step", "[2/6] Running Auditor scan (wraps trivy)...")
    await _send(ws, "detail", "    Target: ./checkout-service")
    await _send(ws, "detail", "    Scanners: license")
    await asyncio.sleep(delay * 1.5)
    await _send(ws, "ok", "  ✓ Auditor found 138 components with 96 licenses (1.2s)")

    await _send(ws, "step", "[3/6] Fusing SBOMs (union by PURL)...")
    await _send(ws, "detail", "    Cartograph: 142 | Auditor: 138 | Overlap: 134")
    await asyncio.sleep(delay)
    await _send(ws, "ok", "  ✓ Merged SBOM: 146 unique components")

    await _send(ws, "step", "[4/6] Running Sentinel vulnerability scan (wraps grype)...")
    await _send(ws, "detail", "    Input: merged SBOM (146 components)")
    await _send(ws, "detail", "    Databases: NVD, GitHub Advisories, distro feeds")
    await asyncio.sleep(delay * 2)
    await _send(ws, "ok", "  ✓ Found 4 vulnerabilities")
    await _send(ws, "alert", "    CRITICAL   axios@1.14.1          — Backdoored release (CVE-2026-40112)")
    await _send(ws, "warn", "    HIGH       jsonwebtoken@9.0.1    — JWT signature bypass (CVE-2025-33101)")
    await _send(ws, "warn", "    MEDIUM     lodash@4.17.21        — Prototype pollution (CVE-2024-28863)")
    await _send(ws, "detail", "    LOW        express@4.18.2        — Open redirect (CVE-2024-43796)")

    await _send(ws, "step", "[5/6] Running Licenser enrichment...")
    await asyncio.sleep(delay)
    await _send(ws, "detail", "    Tier 1 — Pattern rules:     12 resolved")
    await _send(ws, "detail", "    Tier 2 — deps.dev API:      118 resolved")
    await _send(ws, "detail", "    Tier 3 — GitHub API:        9 resolved")
    await _send(ws, "detail", "    Tier 4 — Unsupported:       7 remaining")
    await _send(ws, "ok", "  ✓ License coverage: 139/146 (95.2%)")

    await _send(ws, "step", "[6/6] Uploading results...")
    await _send(ws, "detail", f"    → S3: s3://aegis-sboms/checkout-service/{today}.json")
    await _send(ws, "detail", "    → Postgres: 146 rows upserted to aegis_sbom")
    await asyncio.sleep(delay)
    await _send(ws, "ok", "  ✓ Upload complete")

    await _send(ws, "info", "")
    await _send(ws, "info", "  SBOM Summary: 146 components, 4 vulnerabilities (1C/1H/1M/1L), 95.2% license coverage")


async def _stream_news(ws: WebSocket, fast: bool):
    delay = 0.1 if fast else 0.5

    await _send(ws, "header", "SIDE B: News Ingestion Agent — Cycle starting...")
    await asyncio.sleep(delay)

    await _send(ws, "step", "[1/7] Fetching 22 sources (20 RSS + 2 APIs)...")
    tiers = [
        ("Tier 1", "Socket.dev  StepSecurity  Aikido  GitGuardian  Snyk  Datadog"),
        ("Tier 2", "Wiz  Unit42  Sonatype  CrowdStrike  Aqua  Semgrep"),
        ("Tier 3", "CISA Advisories  CISA News  cvefeed.io  cvedaily.com"),
        ("Tier 4", "The Hacker News  BleepingComputer  HelpNetSecurity  SecurityWeek"),
    ]
    for tier, sources in tiers:
        await _send(ws, "detail", f"    {tier}: {sources}")
        await asyncio.sleep(delay * 0.3)
    await _send(ws, "detail", "    APIs: NVD (critical, last 12h) ✓  CVE Crowd (trending) ✓")
    await _send(ws, "ok", "  ✓ Fetched 8 new articles")

    await _send(ws, "step", "[2/7] Relevance filter (keywords + vendor blocklist)...")
    await asyncio.sleep(delay)
    await _send(ws, "pass", '    ✓ PASS  "Axios npm Package Compromised..." [npm, compromised, hijacked]')
    await _send(ws, "pass", '    ✓ PASS  "Malicious PyPI Package \'reqeusts\'..." [pypi, malicious, typosquatting]')
    await _send(ws, "pass", '    ✓ PASS  "Critical Grafana RCE..." [critical, rce, cvss 9]')
    await _send(ws, "pass", '    ✓ PASS  "Kubernetes API Server SSRF..." [kubernetes, critical]')
    await _send(ws, "pass", '    ✓ PASS  "CISA Releases Updated SBOM Guidance..." [sbom]')
    await _send(ws, "block", '    ✗ BLOCK "Critical Citrix ADC Vulnerability..." [vendor blocklist: citrix]')
    await _send(ws, "block", '    ✗ BLOCK "FortiGate VPN Flaw Allows..." [vendor blocklist: fortinet]')
    await _send(ws, "pass", '    ✓ PASS  "npm Package axios Backdoored..." [npm, backdoor]')
    await _send(ws, "ok", "  ✓ After filter: 6 / 8 articles (2 blocked by vendor blocklist)")

    await _send(ws, "step", "[3/7] Deduplication (3 phases)...")
    await asyncio.sleep(delay)
    await _send(ws, "detail", "    Phase 1 — Exact URL match: 6 candidates, 0 duplicates")
    await _send(ws, "detail", '    Phase 2 — Fuzzy title: "npm Package axios Backdoored..." ↔ "Axios npm Package Compromised..."')
    await _send(ws, "warn", "    ⚠ Jaccard similarity: 0.73 (threshold: 0.70) → DUPLICATE")
    await _send(ws, "detail", "    Phase 3 — LLM semantic dedup: Sending 5 candidates to Claude...")
    await asyncio.sleep(delay * 1.5)
    await _send(ws, "detail", "    All 5 are unique incidents. Scores: 9, 8, 7, 6, 3")
    await _send(ws, "ok", "  ✓ After dedup: 5 / 6 articles (1 duplicate removed)")

    await _send(ws, "step", "[4/7] LLM enrichment via Claude...")
    await asyncio.sleep(delay)
    enrichments = [
        ('"Axios npm Package Compromised..."', "supply_chain_vuln", "axios (npm) 1.14.1,0.30.4", "9/10"),
        ('"Malicious PyPI Package \'reqeusts\'..."', "supply_chain_vuln", 'reqeusts (pypi) "all"', "8/10"),
        ('"Critical Grafana RCE..."', "threat_intel", None, "7/10"),
        ('"Kubernetes API Server SSRF..."', "threat_intel", None, "6/10"),
        ('"CISA Releases Updated SBOM Guidance..."', "general_info", None, "3/10"),
    ]
    for title, cls, pkgs, score in enrichments:
        line = f"    {title} → {cls}"
        if pkgs:
            line += f" | packages: {pkgs}"
        line += f" | impact: {score}"
        style = "alert" if cls == "supply_chain_vuln" else ("warn" if cls == "threat_intel" else "detail")
        await _send(ws, style, line)
        await asyncio.sleep(delay * 0.5)
    await _send(ws, "ok", "  ✓ Enriched: 5 articles (2 supply_chain_vuln, 2 threat_intel, 1 general_info)")

    await _send(ws, "step", "[5/7] Version recovery check...")
    await _send(ws, "detail", '    "reqeusts" has vulnerable_versions="all" — confirmed typosquat, "all" is valid')
    await _send(ws, "ok", "  ✓ No version recovery needed")

    await _send(ws, "step", "[6/7] Inserting into database...")
    await asyncio.sleep(delay)
    await _send(ws, "detail", "    → aegis_news: 5 rows upserted")
    await _send(ws, "ok", "  ✓ Database updated")

    await _send(ws, "step", "[7/7] Slack notifications...")
    await asyncio.sleep(delay)
    await _send_box(ws, [
        "🔴 Axios npm Package Compromised — Hijacked Maintainer",
        "   Account Deploys Cross-Platform RAT",
        "",
        "   Source: Socket.dev | Type: supply_chain_vuln | Impact: 9/10",
        "   Affected: axios (npm) — versions: 1.14.1,0.30.4",
    ])
    await _send_box(ws, [
        "🟡 Malicious PyPI Package 'reqeusts' — Typosquat",
        "",
        "   Source: Snyk | Type: supply_chain_vuln | Impact: 8/10",
        '   Affected: reqeusts (pypi) — versions: all (typosquat)',
    ])
    await _send(ws, "ok", "  ✓ Slack alerts posted (2 supply_chain_vuln, 2 threat_intel, 1 general_info)")

    await _send(ws, "info", "")
    await _send(ws, "info", "  News Summary: 8 fetched, 6 filtered, 5 deduped, 5 enriched")


async def _stream_match(ws: WebSocket, fast: bool):
    delay = 0.1 if fast else 0.5

    await _send(ws, "header", "BRIDGE: Match Engine — Matching supply_chain_vuln against SBOM inventory")
    await asyncio.sleep(delay)

    await _send(ws, "step", "Processing: axios (npm) — vulnerable versions: 1.14.1,0.30.4")
    await _send(ws, "step", "  [1/4] Exact PURL lookup (scoped to npm)...")
    await _send(ws, "detail", "    Query: SELECT * FROM aegis_sbom WHERE component_name='axios' AND ecosystem='npm'")
    await asyncio.sleep(delay)
    await _send(ws, "ok", "  ✓ Found 40 repos using axios")

    await _send(ws, "step", "  [2/4] Version comparison...")
    await asyncio.sleep(delay)
    vuln_repos = [
        ("checkout-service", "1.14.1", True),
        ("payments-web", "1.14.1", True),
        ("admin-portal", "0.30.4", True),
        ("api-gateway", "1.7.3", False),
        ("user-service", "1.6.8", False),
    ]
    for repo, ver, is_vuln in vuln_repos:
        status = "🚨 VULNERABLE" if is_vuln else "✓ safe"
        style = "alert" if is_vuln else "ok"
        await _send(ws, style, f"    {repo:<20} — axios@{ver:<10} vs 1.14.1,0.30.4 → {status}")
        await asyncio.sleep(delay * 0.15)
    await _send(ws, "detail", "    ... (35 more repos using safe versions)")

    await _send(ws, "step", "  [3/4] Posting results to Slack thread...")
    await asyncio.sleep(delay)
    await _send_box(ws, [
        "🚨 3 potentially vulnerable usages found:",
        "",
        "  • checkout-service  — axios@1.14.1",
        "  • payments-web      — axios@1.14.1",
        "  • admin-portal      — axios@0.30.4",
        "",
        "  37 other repos use axios at non-vulnerable versions.",
    ])

    await _send(ws, "step", "")
    await _send(ws, "step", "Processing: reqeusts (pypi) — vulnerable versions: all (typosquat)")
    await _send(ws, "step", "  [1/4] Exact PURL lookup (scoped to pypi)...")
    await asyncio.sleep(delay)
    await _send(ws, "ok", "  ✓ Not found in any SBOM — reqeusts is safe (not used)")

    await _send(ws, "info", "")
    await _send(ws, "info", "  Match Summary: axios found in 3 vulnerable repos, reqeusts not found (safe)")


async def _stream_validator(ws: WebSocket, fast: bool):
    delay = 0.1 if fast else 0.8

    await _send(ws, "header", "VALIDATOR: Reachability Analysis — ECS Fargate")
    await asyncio.sleep(delay)

    await _send(ws, "step", "[4/4] Spawning validators (ECS Fargate)...")
    tasks = [
        ("checkout-service", "axios@1.14.1", "abc123"),
        ("payments-web", "axios@1.14.1", "def456"),
        ("admin-portal", "axios@0.30.4", "ghi789"),
    ]
    for repo, pkg, task_id in tasks:
        await _send(ws, "detail", f"    Task: {repo:<20} ({pkg})  → arn:aws:ecs:.../{task_id}")
        await asyncio.sleep(delay * 0.3)

    await _send(ws, "step", "  Running reachability analysis...")
    await asyncio.sleep(delay * 2)

    await _send(ws, "alert", "  🚨 checkout-service: REACHABLE — axios.post() called in src/api/payment.js:42")
    await asyncio.sleep(delay * 0.5)
    await _send(ws, "alert", "  🚨 payments-web: REACHABLE — axios.get() called in src/hooks/useApi.ts:18")
    await asyncio.sleep(delay * 0.5)
    await _send(ws, "ok", "  ✅ admin-portal: NOT REACHABLE — axios imported but not called in any code path")

    await _send(ws, "step", "  Posting validator results to Slack thread...")
    await asyncio.sleep(delay)
    await _send_box(ws, [
        "🚨 REACHABLE — checkout-service",
        "   axios.post() called in src/api/payment.js:42",
        "",
        "🚨 REACHABLE — payments-web",
        "   axios.get() called in src/hooks/useApi.ts:18",
        "",
        "✅ Not reachable — admin-portal",
        "   Vulnerable module present but not exercised.",
    ])

    await _send(ws, "info", "")
    await _send(ws, "info", "  Validation Summary: 2 repos with reachable paths, 1 safe")


async def _stream_full(ws: WebSocket, fast: bool):
    delay = 0.1 if fast else 0.5

    await _send(ws, "header", "╔═══════════════════════════════════════════════════════╗")
    await _send(ws, "header", "║     AEGIS — Supply Chain Risk Tracker                 ║")
    await _send(ws, "header", "║              Full Pipeline Demo                       ║")
    await _send(ws, "header", "╚═══════════════════════════════════════════════════════╝")
    await _send(ws, "info", "  Simulating: axios npm package compromise flowing through Aegis")
    await _send(ws, "detail", "  No API keys, database, or external tools required.")
    await asyncio.sleep(delay)

    await _send_phase(ws, "Phase 1: SBOM/SCA Pipeline", 1)
    await _send_highlight(ws, "sbom", "active")
    await _stream_sbom(ws, fast)
    await _send_highlight(ws, "sbom", "done")
    await asyncio.sleep(delay)

    await _send_phase(ws, "Phase 2: News Ingestion", 2)
    await _send_highlight(ws, "news", "active")
    await _stream_news(ws, fast)
    await _send_highlight(ws, "news", "done")
    await asyncio.sleep(delay)

    await _send_phase(ws, "Phase 3: Match Engine", 3)
    await _send_highlight(ws, "match", "active")
    await _stream_match(ws, fast)
    await _send_highlight(ws, "match", "done")
    await asyncio.sleep(delay)

    await _send_phase(ws, "Phase 4: Validator", 4)
    await _send_highlight(ws, "validator", "active")
    await _stream_validator(ws, fast)
    await _send_highlight(ws, "validator", "done")

    await _send(ws, "step", "")
    await _send(ws, "header", "═" * 55)
    await _send(ws, "ok", "  DEMO COMPLETE")
    await _send(ws, "header", "═" * 55)
    await _send(ws, "step", "")
    await _send(ws, "info", "  Incident: Axios npm package compromised (CVE-2026-40112)")
    await _send(ws, "info", "  Source: Socket.dev RSS → detected within 30 minutes")
    await _send(ws, "alert", "  SBOM match: 40 repos scanned, 3 vulnerable, 37 safe")
    await _send(ws, "alert", "  Reachability: 2 repos actively calling vulnerable code paths")
    await _send(ws, "info", "  Action: Slack alerts sent, validators confirmed blast radius")


@router.websocket("/api/demo/stream/{section}")
async def ws_demo(websocket: WebSocket, section: str):
    await websocket.accept()
    try:
        handlers = {
            "full": _stream_full,
            "sbom": _stream_sbom,
            "news": _stream_news,
            "match": _stream_match,
            "validator": _stream_validator,
        }
        handler = handlers.get(section)
        if handler is None:
            await websocket.send_json({"type": "line", "text": f"Unknown section: {section}", "style": "alert"})
            await websocket.close()
            return

        fast = True
        try:
            init = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
            import json
            data = json.loads(init)
            fast = data.get("fast", True)
        except (asyncio.TimeoutError, Exception):
            pass

        await handler(websocket, fast)
        await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "line", "text": str(e), "style": "alert"})
        except Exception:
            pass


@router.post("/api/demo/{section}")
async def api_demo_run(section: str):
    sections = {
        "full": {
            "sbom": {"components": 146, "vulnerabilities": 4, "license_coverage": "95.2%"},
            "news": {"fetched": 8, "filtered": 6, "deduped": 5, "enriched": 5},
            "match": {"total_repos": 40, "vulnerable": 3, "safe": 37},
            "validator": {"reachable": 2, "not_reachable": 1},
        },
        "sbom": {"components": 146, "vulnerabilities": 4, "license_coverage": "95.2%"},
        "news": {"fetched": 8, "filtered": 6, "deduped": 5, "enriched": 5},
        "match": {"total_repos": 40, "vulnerable": 3, "safe": 37},
    }
    result = sections.get(section)
    if result is None:
        return {"error": f"Unknown section: {section}"}
    return {"section": section, "results": result}
