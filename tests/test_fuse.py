"""Tests for aegis.sbom.fuse — SBOM merge (Cartograph + Auditor union by PURL)."""

import pytest

from aegis.sbom.fuse import fuse_sboms, merge_component_lists


def _make_sbom(components):
    """Build a minimal CycloneDX-shaped dict for testing."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {"component": {"name": "test-repo"}},
        "components": components,
    }


def _comp(purl, name="pkg", version="1.0.0", license_id=None):
    c = {
        "type": "library",
        "name": name,
        "version": version,
        "purl": purl,
    }
    if license_id:
        c["licenses"] = [{"license": {"id": license_id}}]
    return c


# ---------------------------------------------------------------------------
# merge_component_lists
# ---------------------------------------------------------------------------

class TestMergeComponentLists:
    def test_no_overlap_union(self):
        a = [_comp("pkg:npm/a@1.0.0", "a")]
        b = [_comp("pkg:npm/b@2.0.0", "b")]
        merged = merge_component_lists(a, b)
        purls = {c["purl"] for c in merged}
        assert purls == {"pkg:npm/a@1.0.0", "pkg:npm/b@2.0.0"}

    def test_overlap_prefers_licensed(self):
        a = [_comp("pkg:npm/x@1.0.0", "x")]  # no license
        b = [_comp("pkg:npm/x@1.0.0", "x", license_id="MIT")]
        merged = merge_component_lists(a, b)
        assert len(merged) == 1
        assert merged[0].get("licenses") is not None
        assert merged[0]["licenses"][0]["license"]["id"] == "MIT"

    def test_overlap_both_licensed_keeps_first(self):
        a = [_comp("pkg:npm/x@1.0.0", "x", license_id="Apache-2.0")]
        b = [_comp("pkg:npm/x@1.0.0", "x", license_id="MIT")]
        merged = merge_component_lists(a, b)
        assert len(merged) == 1
        assert merged[0]["licenses"][0]["license"]["id"] == "Apache-2.0"

    def test_empty_lists(self):
        assert merge_component_lists([], []) == []

    def test_one_empty(self):
        a = [_comp("pkg:npm/a@1.0.0", "a")]
        assert len(merge_component_lists(a, [])) == 1
        assert len(merge_component_lists([], a)) == 1

    def test_multiple_overlaps(self):
        a = [
            _comp("pkg:npm/a@1.0.0", "a"),
            _comp("pkg:npm/b@1.0.0", "b", license_id="MIT"),
        ]
        b = [
            _comp("pkg:npm/b@1.0.0", "b"),
            _comp("pkg:npm/c@1.0.0", "c"),
        ]
        merged = merge_component_lists(a, b)
        assert len(merged) == 3
        b_entry = [c for c in merged if c["purl"] == "pkg:npm/b@1.0.0"][0]
        assert b_entry["licenses"][0]["license"]["id"] == "MIT"


# ---------------------------------------------------------------------------
# fuse_sboms (full CycloneDX merge)
# ---------------------------------------------------------------------------

class TestFuseSboms:
    def test_disjoint_sboms(self):
        s1 = _make_sbom([_comp("pkg:npm/a@1.0.0", "a")])
        s2 = _make_sbom([_comp("pkg:npm/b@1.0.0", "b")])
        fused = fuse_sboms(s1, s2)
        assert len(fused["components"]) == 2

    def test_overlapping_sboms(self):
        s1 = _make_sbom([
            _comp("pkg:npm/a@1.0.0", "a"),
            _comp("pkg:npm/shared@2.0.0", "shared"),
        ])
        s2 = _make_sbom([
            _comp("pkg:npm/shared@2.0.0", "shared", license_id="MIT"),
            _comp("pkg:npm/b@3.0.0", "b"),
        ])
        fused = fuse_sboms(s1, s2)
        assert len(fused["components"]) == 3

    def test_empty_sboms(self):
        s1 = _make_sbom([])
        s2 = _make_sbom([])
        fused = fuse_sboms(s1, s2)
        assert fused["components"] == []

    def test_preserves_bom_format(self):
        s1 = _make_sbom([_comp("pkg:npm/a@1.0.0", "a")])
        s2 = _make_sbom([])
        fused = fuse_sboms(s1, s2)
        assert fused["bomFormat"] == "CycloneDX"
        assert fused["specVersion"] == "1.5"

    def test_metadata_from_first(self):
        s1 = _make_sbom([])
        s1["metadata"]["component"]["name"] = "repo-alpha"
        s2 = _make_sbom([])
        s2["metadata"]["component"]["name"] = "repo-beta"
        fused = fuse_sboms(s1, s2)
        assert fused["metadata"]["component"]["name"] == "repo-alpha"
