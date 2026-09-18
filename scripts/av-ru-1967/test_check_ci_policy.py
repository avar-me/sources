#!/usr/bin/env python3
"""Unit tests for check_ci_policy.py (av-ru-1967-review-batch-5-2026-09-18.md,
P0 "Переделать monotonic baseline CI policy", requirement 4: "Добавить
negative CI tests"). Pure stdlib `unittest` — no pytest dependency to add
to requirements.txt.

Covers the 5 scenarios batch-5 names explicitly:
1. PR base doesn't contain baselines.json -> falls back to branch history.
2. A metric was removed several commits before HEAD -> only ok with a
   matching baseline_migrations.json entry, still fails without one.
3. Two metrics regressed, only one approved -> the other still fails.
4. A baseline was lowered but the build metric doesn't match it -> already
   `baseline.py`'s job (build_all.sh fails before this script even runs);
   documented here as a non-goal of this script, not silently assumed ok.
5. A committed generated artifact changed after the build -> covered by
   `check_reproducibility.sh` / the CI workflow's `git diff --exit-code`
   step, not this script; documented here as a non-goal too.

Run: python3 scripts/av-ru-1967/test_check_ci_policy.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_ci_policy import (  # noqa: E402
    compare_baselines,
    find_comparison_baselines,
    load_migrations,
    parse_approvals,
)


class ComparBaselinesTests(unittest.TestCase):
    """Scenario 2 and 3 — pure logic, no git needed."""

    def test_unchanged_and_improved_pass(self):
        current = {"a": 5, "b": 3}
        base = {"a": 5, "b": 4}
        failures = compare_baselines(current, base, approvals={}, migrations={})
        self.assertEqual(failures, [])

    def test_regression_without_approval_fails(self):
        current = {"a": 10}
        base = {"a": 5}
        failures = compare_baselines(current, base, approvals={}, migrations={})
        self.assertEqual(len(failures), 1)
        self.assertIn("a baseline increased 5 -> 10", failures[0])

    def test_regression_with_matching_approval_passes(self):
        current = {"a": 10}
        base = {"a": 5}
        approvals = {"a": (5, 10, "documented reason")}
        failures = compare_baselines(current, base, approvals, migrations={})
        self.assertEqual(failures, [])

    def test_two_regressions_only_one_approved__other_still_fails(self):
        """Scenario 3: a single unscoped trailer must NOT approve every
        regressed metric — only the metric it explicitly names."""
        current = {"a": 10, "b": 20}
        base = {"a": 5, "b": 5}
        approvals = {"a": (5, 10, "approved this one")}
        failures = compare_baselines(current, base, approvals, migrations={})
        self.assertEqual(len(failures), 1)
        self.assertIn("b baseline increased 5 -> 20", failures[0])

    def test_approval_for_wrong_value_does_not_apply(self):
        """An approval trailer's old/new values must match exactly — an
        approval for a DIFFERENT transition of the same metric name must
        not silently cover this one."""
        current = {"a": 11}
        base = {"a": 5}
        approvals = {"a": (5, 10, "approved a different jump")}
        failures = compare_baselines(current, base, approvals, migrations={})
        self.assertEqual(len(failures), 1)

    def test_metric_removed_without_migration_fails(self):
        """Scenario 2 (part 1): a metric missing from HEAD must fail
        unless a migration entry documents its removal."""
        current: dict[str, int] = {}
        base = {"page_ledger.unexplained_drops": 105}
        failures = compare_baselines(current, base, approvals={}, migrations={})
        self.assertEqual(len(failures), 1)
        self.assertIn("missing from HEAD", failures[0])

    def test_metric_removed_with_migration_passes(self):
        """Scenario 2 (part 2): the same removal is fine once documented,
        regardless of how far back `base` is — this is what makes
        comparing against an arbitrarily old --base-ref safe."""
        current: dict[str, int] = {}
        base = {"page_ledger.unexplained_drops": 105}
        migrations = {
            "page_ledger.unexplained_drops": {
                "metric": "page_ledger.unexplained_drops",
                "removed_at_commit": "deadbeef",
                "reason": "replaced by hard gates",
            }
        }
        failures = compare_baselines(current, base, approvals={}, migrations=migrations)
        self.assertEqual(failures, [])

    def test_new_metric_with_no_prior_baseline_passes(self):
        current = {"a": 5, "brand_new": 0}
        base = {"a": 5}
        failures = compare_baselines(current, base, approvals={}, migrations={})
        self.assertEqual(failures, [])


class ParseApprovalsTests(unittest.TestCase):
    def test_parses_per_metric_trailer(self):
        msg = "some commit\n\nbaseline-regression-approved: check_accepted.oversized_spans 7->12 reason: legit new large entries\n"
        approvals = parse_approvals(msg)
        self.assertEqual(approvals, {"check_accepted.oversized_spans": (7, 12, "legit new large entries")})

    def test_multiple_trailers(self):
        msg = (
            "baseline-regression-approved: a 1->2 reason: r1\n"
            "baseline-regression-approved: b 3->4 reason: r2\n"
        )
        approvals = parse_approvals(msg)
        self.assertEqual(set(approvals), {"a", "b"})

    def test_no_trailer_returns_empty(self):
        self.assertEqual(parse_approvals("just a normal commit message"), {})


class LoadMigrationsTests(unittest.TestCase):
    def test_missing_file_returns_empty(self):
        self.assertEqual(load_migrations("/nonexistent/path.json"), {})

    def test_loads_real_migrations_file(self):
        migrations = load_migrations(str(Path(__file__).parent / "baseline_migrations.json"))
        self.assertIn("page_ledger.unexplained_drops", migrations)


class GitBackedTests(unittest.TestCase):
    """Scenario 1 — needs a real (throwaway) git repo to exercise
    find_comparison_baselines()'s history-walking fallback."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmpdir.name)
        self._run("git", "init", "-q")
        self._run("git", "config", "user.email", "test@example.com")
        self._run("git", "config", "user.name", "Test")

    def tearDown(self):
        self.tmpdir.cleanup()

    def _run(self, *args: str) -> str:
        return subprocess.run(args, cwd=self.repo, capture_output=True, text=True, check=True).stdout

    def _commit(self, baselines_content: str | None, message: str = "commit") -> str:
        if baselines_content is not None:
            (self.repo / "baselines.json").write_text(baselines_content, encoding="utf-8")
            self._run("git", "add", "baselines.json")
        else:
            (self.repo / "placeholder.txt").write_text(message, encoding="utf-8")
            self._run("git", "add", "placeholder.txt")
        self._run("git", "commit", "-q", "-m", message, "--allow-empty")
        return self._run("git", "rev-parse", "HEAD").strip()

    def test_fallback_to_branch_history_when_base_ref_lacks_file(self):
        """Scenario 1: the nominal base ref (simulating `main`, which has
        never had baselines.json) must not silently skip validation —
        it should fall back to the current branch's own most recent
        commit that DOES have the file."""
        main_tip = self._commit(None, "main tip, never had baselines.json")
        self._commit('{"a": 5}', "feature commit 1, introduces baselines.json")
        self._commit('{"a": 5}', "feature commit 2, unchanged")

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(self.repo)
            result = find_comparison_baselines(main_tip, "baselines.json")
        finally:
            os.chdir(old_cwd)

        self.assertIsNotNone(result)
        used_ref, baselines = result
        self.assertNotEqual(used_ref, main_tip)
        self.assertEqual(baselines, {"a": 5})

    def test_direct_ref_used_when_it_has_the_file(self):
        first = self._commit('{"a": 5}', "first")
        self._commit('{"a": 3}', "second, improved")

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(self.repo)
            result = find_comparison_baselines(first, "baselines.json")
        finally:
            os.chdir(old_cwd)

        self.assertIsNotNone(result)
        used_ref, baselines = result
        self.assertEqual(used_ref, first)
        self.assertEqual(baselines, {"a": 5})

    def test_no_history_has_the_file_returns_none(self):
        self._commit(None, "no baselines.json ever")

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(self.repo)
            result = find_comparison_baselines("HEAD", "baselines.json")
        finally:
            os.chdir(old_cwd)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
