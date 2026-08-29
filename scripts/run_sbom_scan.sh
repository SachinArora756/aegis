#!/usr/bin/env bash
# Aegis — run SBOM scan on every repo in a directory.
# Usage: ./run_sbom_scan.sh /path/to/repos
# Intended for cron: 0 2 * * * /opt/aegis/scripts/run_sbom_scan.sh /srv/repos
set -euo pipefail

REPOS_DIR="${1:?Usage: $0 /path/to/repos}"
FAILED=0
SCANNED=0

echo "[$(date -u +%FT%TZ)] Aegis SBOM scan starting — target: ${REPOS_DIR}"

for repo in "${REPOS_DIR}"/*/; do
    [ -d "$repo" ] || continue
    repo_name="$(basename "$repo")"
    echo "[$(date -u +%FT%TZ)] Scanning ${repo_name} ..."
    if aegis sbom scan "$repo" --repo-name "$repo_name"; then
        SCANNED=$((SCANNED + 1))
    else
        echo "WARN: scan failed for ${repo_name}" >&2
        FAILED=$((FAILED + 1))
    fi
done

echo "[$(date -u +%FT%TZ)] Done — ${SCANNED} scanned, ${FAILED} failed."
exit $((FAILED > 0 ? 1 : 0))
