"""Tests for aegis.sbom.purl — Package URL parsing and construction."""

import pytest

from aegis.sbom.purl import build_purl, normalize_ecosystem, parse_purl


# ---------------------------------------------------------------------------
# parse_purl
# ---------------------------------------------------------------------------

class TestParsePurl:
    def test_npm_simple(self):
        result = parse_purl("pkg:npm/axios@1.7.3")
        assert result["type"] == "npm"
        assert result["name"] == "axios"
        assert result["version"] == "1.7.3"
        assert result["namespace"] is None

    def test_npm_scoped(self):
        result = parse_purl("pkg:npm/%40angular/core@16.2.0")
        assert result["type"] == "npm"
        assert result["namespace"] == "@angular"
        assert result["name"] == "core"
        assert result["version"] == "16.2.0"

    def test_npm_scoped_unencoded(self):
        result = parse_purl("pkg:npm/@babel/core@7.23.0")
        assert result["namespace"] == "@babel"
        assert result["name"] == "core"

    def test_golang(self):
        result = parse_purl("pkg:golang/github.com/gin-gonic/gin@1.9.1")
        assert result["type"] == "golang"
        assert result["namespace"] == "github.com/gin-gonic"
        assert result["name"] == "gin"
        assert result["version"] == "1.9.1"

    def test_maven(self):
        result = parse_purl("pkg:maven/org.apache.logging.log4j/log4j-core@2.17.0")
        assert result["type"] == "maven"
        assert result["namespace"] == "org.apache.logging.log4j"
        assert result["name"] == "log4j-core"
        assert result["version"] == "2.17.0"

    def test_pypi(self):
        result = parse_purl("pkg:pypi/langchain-core@0.3.20")
        assert result["type"] == "pypi"
        assert result["name"] == "langchain-core"
        assert result["version"] == "0.3.20"

    def test_cargo(self):
        result = parse_purl("pkg:cargo/serde@1.0.195")
        assert result["type"] == "cargo"
        assert result["name"] == "serde"
        assert result["version"] == "1.0.195"

    def test_no_version(self):
        result = parse_purl("pkg:npm/express")
        assert result["type"] == "npm"
        assert result["name"] == "express"
        assert result["version"] is None

    def test_with_qualifiers(self):
        result = parse_purl("pkg:npm/foo@1.0.0?vcs_url=https://github.com/foo/bar")
        assert result["type"] == "npm"
        assert result["name"] == "foo"
        assert result["version"] == "1.0.0"

    def test_with_subpath(self):
        result = parse_purl("pkg:npm/foo@1.0.0#sub/path")
        assert result["name"] == "foo"
        assert result["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# build_purl
# ---------------------------------------------------------------------------

class TestBuildPurl:
    def test_npm_simple(self):
        assert build_purl("npm", "axios", "1.7.3") == "pkg:npm/axios@1.7.3"

    def test_maven_with_namespace(self):
        result = build_purl("maven", "log4j-core", "2.17.0", namespace="org.apache.logging.log4j")
        assert result == "pkg:maven/org.apache.logging.log4j/log4j-core@2.17.0"

    def test_pypi(self):
        assert build_purl("pypi", "requests", "2.31.0") == "pkg:pypi/requests@2.31.0"

    def test_golang_with_namespace(self):
        result = build_purl("golang", "gin", "1.9.1", namespace="github.com/gin-gonic")
        assert result == "pkg:golang/github.com/gin-gonic/gin@1.9.1"

    def test_no_version(self):
        assert build_purl("npm", "express", None) == "pkg:npm/express"

    def test_empty_version(self):
        assert build_purl("npm", "express", "") == "pkg:npm/express"


# ---------------------------------------------------------------------------
# normalize_ecosystem
# ---------------------------------------------------------------------------

class TestNormalizeEcosystem:
    def test_npm(self):
        assert normalize_ecosystem("npm") == "npm"

    def test_pypi_variants(self):
        assert normalize_ecosystem("pypi") == "pypi"
        assert normalize_ecosystem("pip") == "pypi"
        assert normalize_ecosystem("python") == "pypi"

    def test_golang_variants(self):
        assert normalize_ecosystem("golang") == "golang"
        assert normalize_ecosystem("go") == "golang"

    def test_maven(self):
        assert normalize_ecosystem("maven") == "maven"
        assert normalize_ecosystem("java") == "maven"

    def test_cargo_variants(self):
        assert normalize_ecosystem("cargo") == "cargo"
        assert normalize_ecosystem("crates.io") == "cargo"
        assert normalize_ecosystem("rust") == "cargo"

    def test_rubygems(self):
        assert normalize_ecosystem("rubygems") == "rubygems"
        assert normalize_ecosystem("gem") == "rubygems"
        assert normalize_ecosystem("ruby") == "rubygems"

    def test_nuget(self):
        assert normalize_ecosystem("nuget") == "nuget"
        assert normalize_ecosystem("dotnet") == "nuget"

    def test_case_insensitive(self):
        assert normalize_ecosystem("NPM") == "npm"
        assert normalize_ecosystem("PyPI") == "pypi"

    def test_unknown_passthrough(self):
        assert normalize_ecosystem("unknown-eco") == "unknown-eco"
