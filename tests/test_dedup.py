"""Tests for aegis.news.dedup — three-phase deduplication."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aegis.news.dedup import (
    extract_cve_ids,
    fuzzy_title_cve_match,
    normalize_title,
)


# ---------------------------------------------------------------------------
# normalize_title
# ---------------------------------------------------------------------------

class TestNormalizeTitle:
    def test_lowercases(self):
        result = normalize_title("CRITICAL Vulnerability Found")
        assert all(w == w.lower() for w in result)

    def test_strips_stopwords(self):
        result = normalize_title("a the an in of for and or but is to")
        assert len(result) == 0 or all(w not in {"a", "the", "an", "in", "of", "for", "and", "or", "but", "is", "to"} for w in result)

    def test_splits_hyphens(self):
        result = normalize_title("supply-chain attack on open-source")
        assert "supply" in result
        assert "chain" in result

    def test_empty_string(self):
        result = normalize_title("")
        assert result == set() or result == frozenset()

    def test_real_title(self):
        result = normalize_title("Malicious npm Package Targets Developers with SSH Backdoor")
        assert "malicious" in result
        assert "npm" in result
        assert "package" in result
        assert "backdoor" in result


# ---------------------------------------------------------------------------
# extract_cve_ids
# ---------------------------------------------------------------------------

class TestExtractCveIds:
    def test_single_cve(self):
        ids = extract_cve_ids("CVE-2026-12345 found in popular library")
        assert "CVE-2026-12345" in ids

    def test_multiple_cves(self):
        ids = extract_cve_ids("CVE-2026-12345 and CVE-2025-99999 both critical")
        assert "CVE-2026-12345" in ids
        assert "CVE-2025-99999" in ids

    def test_no_cve(self):
        ids = extract_cve_ids("Malicious npm package discovered")
        assert len(ids) == 0

    def test_cve_in_url_still_extracted(self):
        ids = extract_cve_ids("Details at https://nvd.nist.gov/vuln/detail/CVE-2026-54321")
        assert "CVE-2026-54321" in ids

    def test_four_digit_year(self):
        ids = extract_cve_ids("CVE-2024-1234 is old")
        assert "CVE-2024-1234" in ids


# ---------------------------------------------------------------------------
# fuzzy_title_cve_match
# ---------------------------------------------------------------------------

class TestFuzzyTitleCveMatch:
    def test_high_overlap_is_duplicate(self):
        existing = [
            "Malicious npm package steals credentials from developers",
        ]
        is_dup = fuzzy_title_cve_match(
            "Malicious npm package stealing developer credentials",
            existing_titles=existing,
            existing_cves=[],
        )
        assert is_dup is True

    def test_low_overlap_not_duplicate(self):
        existing = [
            "Malicious npm package steals credentials from developers",
        ]
        is_dup = fuzzy_title_cve_match(
            "Critical Kubernetes vulnerability allows container escape",
            existing_titles=existing,
            existing_cves=[],
        )
        assert is_dup is False

    def test_same_cve_is_duplicate(self):
        is_dup = fuzzy_title_cve_match(
            "New analysis of CVE-2026-12345 impact",
            existing_titles=["Something completely different"],
            existing_cves=["CVE-2026-12345"],
        )
        assert is_dup is True

    def test_different_cve_not_duplicate(self):
        is_dup = fuzzy_title_cve_match(
            "Details on CVE-2026-99999",
            existing_titles=[],
            existing_cves=["CVE-2026-12345"],
        )
        assert is_dup is False

    def test_empty_existing(self):
        is_dup = fuzzy_title_cve_match(
            "Brand new vulnerability discovered",
            existing_titles=[],
            existing_cves=[],
        )
        assert is_dup is False

    def test_identical_title(self):
        title = "axios npm package compromised via hijacked maintainer"
        is_dup = fuzzy_title_cve_match(
            title,
            existing_titles=[title],
            existing_cves=[],
        )
        assert is_dup is True
