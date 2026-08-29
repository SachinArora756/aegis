"""Tests for aegis.news.enricher — LLM output parsing and validation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aegis.news.enricher import _validate_enrichment


# ---------------------------------------------------------------------------
# _validate_enrichment
# ---------------------------------------------------------------------------

class TestValidateEnrichment:
    def test_valid_supply_chain_vuln(self):
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Malicious axios versions published via hijacked maintainer account.",
            "impact_score": 9,
            "affected_packages": [
                {
                    "name": "axios",
                    "ecosystem": "npm",
                    "vulnerable_versions": "1.14.1,0.30.4",
                    "cve_id": None,
                }
            ],
        })
        assert result["classification"] == "supply_chain_vuln"
        assert len(result["affected_packages"]) == 1
        assert result["affected_packages"][0]["name"] == "axios"

    def test_supply_chain_vuln_missing_name_rejected(self):
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Some vulnerability.",
            "impact_score": 7,
            "affected_packages": [
                {
                    "name": "",
                    "ecosystem": "npm",
                    "vulnerable_versions": "1.0.0",
                    "cve_id": None,
                }
            ],
        })
        # Packages with no name should be dropped
        assert len(result.get("affected_packages", [])) == 0

    def test_unknown_versions_rejected(self):
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Some vuln.",
            "impact_score": 6,
            "affected_packages": [
                {
                    "name": "badpkg",
                    "ecosystem": "npm",
                    "vulnerable_versions": "unknown",
                    "cve_id": None,
                }
            ],
        })
        assert len(result.get("affected_packages", [])) == 0

    def test_unclear_versions_rejected(self):
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Some vuln.",
            "impact_score": 6,
            "affected_packages": [
                {
                    "name": "badpkg",
                    "ecosystem": "pypi",
                    "vulnerable_versions": "unclear",
                    "cve_id": None,
                }
            ],
        })
        assert len(result.get("affected_packages", [])) == 0

    def test_all_versions_flags_recovery(self):
        """'all' for a non-typosquat should set needs_fulltext_recovery."""
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Compromised maintainer account.",
            "impact_score": 8,
            "is_typosquat": False,
            "affected_packages": [
                {
                    "name": "popular-lib",
                    "ecosystem": "npm",
                    "vulnerable_versions": "all",
                    "cve_id": None,
                }
            ],
        })
        pkgs = result.get("affected_packages", [])
        assert len(pkgs) == 1
        assert pkgs[0].get("needs_fulltext_recovery") is True

    def test_all_versions_typosquat_no_recovery(self):
        """'all' for an actual typosquat is legitimate — no recovery needed."""
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Typosquat package published.",
            "impact_score": 7,
            "is_typosquat": True,
            "affected_packages": [
                {
                    "name": "req-uests",
                    "ecosystem": "pypi",
                    "vulnerable_versions": "all",
                    "cve_id": None,
                }
            ],
        })
        pkgs = result.get("affected_packages", [])
        assert len(pkgs) == 1
        assert pkgs[0].get("needs_fulltext_recovery", False) is False

    def test_threat_intel_no_packages_ok(self):
        result = _validate_enrichment({
            "classification": "threat_intel",
            "summary": "Grafana RCE disclosed.",
            "impact_score": 7,
            "affected_packages": [],
        })
        assert result["classification"] == "threat_intel"

    def test_threat_intel_missing_packages_key_ok(self):
        result = _validate_enrichment({
            "classification": "threat_intel",
            "summary": "Jenkins advisory.",
            "impact_score": 5,
        })
        assert result["classification"] == "threat_intel"

    def test_general_info_minimal(self):
        result = _validate_enrichment({
            "classification": "general_info",
            "summary": "CISA releases new guidance document.",
            "impact_score": 2,
        })
        assert result["classification"] == "general_info"

    def test_invalid_classification_defaults(self):
        result = _validate_enrichment({
            "classification": "not_a_real_type",
            "summary": "Something.",
            "impact_score": 3,
        })
        assert result["classification"] == "general_info"

    def test_impact_score_clamped(self):
        result = _validate_enrichment({
            "classification": "threat_intel",
            "summary": "Test.",
            "impact_score": 15,
        })
        assert result["impact_score"] <= 10

        result2 = _validate_enrichment({
            "classification": "threat_intel",
            "summary": "Test.",
            "impact_score": -3,
        })
        assert result2["impact_score"] >= 1

    def test_multiple_packages_partial_valid(self):
        """One valid package + one invalid → keep only the valid one."""
        result = _validate_enrichment({
            "classification": "supply_chain_vuln",
            "summary": "Two packages affected.",
            "impact_score": 8,
            "affected_packages": [
                {
                    "name": "good-pkg",
                    "ecosystem": "npm",
                    "vulnerable_versions": "1.2.3",
                    "cve_id": "CVE-2026-11111",
                },
                {
                    "name": "",
                    "ecosystem": "npm",
                    "vulnerable_versions": "unknown",
                    "cve_id": None,
                },
            ],
        })
        pkgs = result.get("affected_packages", [])
        assert len(pkgs) == 1
        assert pkgs[0]["name"] == "good-pkg"
