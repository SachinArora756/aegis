"""Tests for aegis.news.filter — relevance keyword + blocklist filtering."""

import pytest

from aegis.news.filter import filter_article


class TestRelevanceKeywords:
    def test_supply_chain_keyword_passes(self):
        passes, kw = filter_article(
            "Malicious package found on npm registry",
            "A typosquatting attack was discovered targeting the popular requests library.",
        )
        assert passes is True
        assert len(kw) > 0

    def test_ecosystem_keyword_passes(self):
        passes, kw = filter_article(
            "New advisory for PyPI package",
            "A critical vulnerability has been disclosed in a widely-used PyPI package.",
        )
        assert passes is True

    def test_severity_keyword_passes(self):
        passes, kw = filter_article(
            "CVE-2026-12345: Critical RCE in popular library",
            "CVSS 9.8 — actively exploited zero-day allows remote code execution.",
        )
        assert passes is True

    def test_no_relevant_keywords_rejected(self):
        passes, kw = filter_article(
            "Company announces new office in London",
            "The cybersecurity firm is expanding its European operations with a new headquarters.",
        )
        assert passes is False
        assert kw == []

    def test_case_insensitivity(self):
        passes, _ = filter_article(
            "MALICIOUS PACKAGE found on NPM",
            "TYPOSQUATTING attack discovered.",
        )
        assert passes is True


class TestVendorBlocklist:
    def test_blocklisted_vendor_rejected(self):
        passes, _ = filter_article(
            "Citrix NetScaler vulnerability allows privilege escalation",
            "A new CVE in Citrix NetScaler Gateway has been disclosed. Patch immediately.",
        )
        assert passes is False

    def test_blocklisted_vendor_with_override_survives(self):
        """A Fortinet article that also mentions npm tokens should survive."""
        passes, kw = filter_article(
            "Fortinet breach leaks npm tokens for thousands of packages",
            "Attackers exfiltrated npm authentication tokens from a Fortinet appliance, "
            "potentially allowing supply chain attacks on the npm ecosystem.",
        )
        assert passes is True

    def test_another_blocklisted_vendor(self):
        passes, _ = filter_article(
            "SonicWall firewall zero-day actively exploited",
            "SonicWall has released patches for a critical vulnerability in SMA appliances.",
        )
        assert passes is False

    def test_wordpress_only_rejected(self):
        passes, _ = filter_article(
            "WordPress plugin vulnerability exposes millions of sites",
            "A popular WordPress plugin has a stored XSS flaw.",
        )
        assert passes is False


class TestEdgeCases:
    def test_empty_title_and_summary(self):
        passes, kw = filter_article("", "")
        assert passes is False
        assert kw == []

    def test_none_safe(self):
        """filter_article should handle None gracefully if passed."""
        passes, kw = filter_article(None, None)
        assert passes is False

    def test_mixed_blocklist_and_relevant(self):
        """Article about a blocklisted vendor BUT with a cross-ecosystem term."""
        passes, kw = filter_article(
            "Ivanti VPN flaw used to deploy malicious PyPI packages",
            "Threat actors leveraged an Ivanti zero-day to compromise a PyPI maintainer account.",
        )
        assert passes is True
