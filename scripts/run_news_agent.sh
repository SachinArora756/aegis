#!/usr/bin/env bash
# Aegis — run a single news ingestion cycle.
# Usage: ./run_news_agent.sh
# Intended for cron: */30 * * * * /opt/aegis/scripts/run_news_agent.sh
set -euo pipefail

echo "[$(date -u +%FT%TZ)] Aegis news ingestion starting ..."

if aegis news run; then
    echo "[$(date -u +%FT%TZ)] News ingestion complete."
else
    echo "[$(date -u +%FT%TZ)] News ingestion FAILED." >&2
    exit 1
fi
