"""Tests for aegis.match.version — the semver-ish comparator."""

import pytest

from aegis.match.version import (
    compare_versions,
    is_version_vulnerable,
    parse_version,
    version_matches_constraint,
)


# ---------------------------------------------------------------------------
# parse_version
# ---------------------------------------------------------------------------

class TestParseVersion:
    def test_three_part(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_two_part(self):
        assert parse_version("1.2") == (1, 2, 0)

    def test_one_part(self):
        assert parse_version("7") == (7, 0, 0)

    def test_v_prefix_stripped(self):
        assert parse_version("v1.2.3") == (1, 2, 3)

    def test_V_prefix_stripped(self):
        assert parse_version("V2.0.0") == (2, 0, 0)

    def test_prerelease_suffix_stripped(self):
        assert parse_version("1.2.3-beta") == (1, 2, 3)

    def test_prerelease_plus_metadata(self):
        assert parse_version("1.2.3-rc.1+build.42") == (1, 2, 3)

    def test_four_part(self):
        assert parse_version("1.2.3.4") == (1, 2, 3, 4)

    def test_zero_version(self):
        assert parse_version("0.0.0") == (0, 0, 0)

    def test_large_numbers(self):
        assert parse_version("100.200.300") == (100, 200, 300)

    def test_whitespace_stripped(self):
        assert parse_version("  1.2.3  ") == (1, 2, 3)


# ---------------------------------------------------------------------------
# compare_versions
# ---------------------------------------------------------------------------

class TestCompareVersions:
    def test_equal(self):
        assert compare_versions((1, 2, 3), (1, 2, 3)) == 0

    def test_less_major(self):
        assert compare_versions((1, 0, 0), (2, 0, 0)) == -1

    def test_greater_major(self):
        assert compare_versions((3, 0, 0), (2, 0, 0)) == 1

    def test_less_minor(self):
        assert compare_versions((1, 2, 0), (1, 3, 0)) == -1

    def test_less_patch(self):
        assert compare_versions((1, 2, 3), (1, 2, 4)) == -1

    def test_different_lengths(self):
        assert compare_versions((1, 2), (1, 2, 0)) == 0
        assert compare_versions((1, 2, 0), (1, 2)) == 0
        assert compare_versions((1, 2), (1, 2, 1)) == -1


# ---------------------------------------------------------------------------
# version_matches_constraint (single constraint)
# ---------------------------------------------------------------------------

class TestVersionMatchesConstraint:
    # Less-than
    def test_lt_true(self):
        assert version_matches_constraint("4.19.0", "<4.19.1") is True

    def test_lt_boundary_false(self):
        assert version_matches_constraint("4.19.1", "<4.19.1") is False

    def test_lt_above_false(self):
        assert version_matches_constraint("4.20.0", "<4.19.1") is False

    def test_lt_well_below(self):
        assert version_matches_constraint("3.0.0", "<4.19.1") is True

    # Less-equal
    def test_le_boundary_true(self):
        assert version_matches_constraint("2.0.0", "<=2.0.0") is True

    def test_le_below_true(self):
        assert version_matches_constraint("1.9.9", "<=2.0.0") is True

    def test_le_above_false(self):
        assert version_matches_constraint("2.0.1", "<=2.0.0") is False

    # Greater-than
    def test_gt_true(self):
        assert version_matches_constraint("1.0.1", ">1.0.0") is True

    def test_gt_boundary_false(self):
        assert version_matches_constraint("1.0.0", ">1.0.0") is False

    def test_gt_below_false(self):
        assert version_matches_constraint("0.9.9", ">1.0.0") is False

    # Greater-equal
    def test_ge_boundary_true(self):
        assert version_matches_constraint("3.5.0", ">=3.5.0") is True

    def test_ge_above_true(self):
        assert version_matches_constraint("4.0.0", ">=3.5.0") is True

    def test_ge_below_false(self):
        assert version_matches_constraint("3.4.9", ">=3.5.0") is False

    # Exact (= prefix or bare version)
    def test_exact_eq_true(self):
        assert version_matches_constraint("1.2.3", "=1.2.3") is True

    def test_exact_eq_false(self):
        assert version_matches_constraint("1.2.4", "=1.2.3") is False

    def test_exact_bare_true(self):
        assert version_matches_constraint("1.2.3", "1.2.3") is True

    def test_exact_bare_false(self):
        assert version_matches_constraint("1.2.4", "1.2.3") is False


# ---------------------------------------------------------------------------
# is_version_vulnerable (full expression with OR / AND logic)
# ---------------------------------------------------------------------------

class TestIsVersionVulnerable:
    # "all"
    def test_all_matches_any_version(self):
        assert is_version_vulnerable("0.0.1", "all") is True
        assert is_version_vulnerable("99.99.99", "all") is True

    def test_all_case_insensitive(self):
        assert is_version_vulnerable("1.0.0", "ALL") is True
        assert is_version_vulnerable("1.0.0", "All") is True

    # Exact single version
    def test_exact_match(self):
        assert is_version_vulnerable("1.14.1", "1.14.1") is True

    def test_exact_no_match(self):
        assert is_version_vulnerable("1.14.2", "1.14.1") is False

    # Comma-separated exact versions (OR logic)
    def test_csv_first_matches(self):
        assert is_version_vulnerable("1.14.1", "1.14.1,0.30.4") is True

    def test_csv_second_matches(self):
        assert is_version_vulnerable("0.30.4", "1.14.1,0.30.4") is True

    def test_csv_neither_matches(self):
        assert is_version_vulnerable("1.14.2", "1.14.1,0.30.4") is False

    # Single operator constraint
    def test_single_lt(self):
        assert is_version_vulnerable("4.18.0", "<4.19.1") is True
        assert is_version_vulnerable("4.19.1", "<4.19.1") is False

    # AND range (all constraints must hold)
    def test_range_inside(self):
        assert is_version_vulnerable("2.0.0", ">=2.0.0,<2.3.1") is True
        assert is_version_vulnerable("2.3.0", ">=2.0.0,<2.3.1") is True

    def test_range_at_upper_boundary(self):
        assert is_version_vulnerable("2.3.1", ">=2.0.0,<2.3.1") is False

    def test_range_below(self):
        assert is_version_vulnerable("1.9.9", ">=2.0.0,<2.3.1") is False

    def test_range_above(self):
        assert is_version_vulnerable("2.4.0", ">=2.0.0,<2.3.1") is False

    # Whitespace tolerance
    def test_whitespace_around_parts(self):
        assert is_version_vulnerable("1.14.1", " 1.14.1 , 0.30.4 ") is True

    def test_whitespace_around_operator(self):
        assert is_version_vulnerable("1.0.0", " >= 1.0.0 ") is True

    # v-prefix in constraint
    def test_v_prefix_in_constraint(self):
        assert is_version_vulnerable("1.2.3", "v1.2.3") is True

    # Edge: empty vulnerable_versions
    def test_empty_string_never_vulnerable(self):
        assert is_version_vulnerable("1.0.0", "") is False

    # Mixed: exact versions + operator ranges in one expression
    # "1.14.1,0.30.4" — these are both exact, OR'd → tested above.
    # ">=2.0.0,<2.3.1" — both operators, AND'd → tested above.
    # A realistic mixed expression: "1.14.1,>=2.0.0" won't happen in practice
    # but the logic should still be: exact OR, operators AND among themselves.
    # For safety, we test the two groups independently.

    def test_three_exact_versions(self):
        assert is_version_vulnerable("0.30.4", "1.14.1,0.30.4,0.28.0") is True
        assert is_version_vulnerable("0.28.0", "1.14.1,0.30.4,0.28.0") is True
        assert is_version_vulnerable("0.29.0", "1.14.1,0.30.4,0.28.0") is False

    def test_le_range(self):
        assert is_version_vulnerable("1.0.0", "<=1.5.0") is True
        assert is_version_vulnerable("1.5.0", "<=1.5.0") is True
        assert is_version_vulnerable("1.5.1", "<=1.5.0") is False

    def test_complex_range(self):
        assert is_version_vulnerable("3.0.0", ">=2.0.0,<=4.0.0") is True
        assert is_version_vulnerable("4.0.1", ">=2.0.0,<=4.0.0") is False
        assert is_version_vulnerable("1.9.9", ">=2.0.0,<=4.0.0") is False
