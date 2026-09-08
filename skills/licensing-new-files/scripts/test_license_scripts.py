#!/usr/bin/env python3
"""Black-box tests for sync-skill-license.py and audit-skill-licensing.py.

Deliberately doesn't trust `reuse` or `claude` to be correct -- that's
upstream's concern, covered by their own test suites. This only tests
*our* logic, by running the real scripts as subprocesses against small
synthetic fixture repos (real REUSE.toml + real `reuse` CLI, not mocked)
and asserting on exit code, stdout, and actual file content afterward.

The two scripts share their core checking/parsing logic (see
_skill_license_lib.py), so most tests here run against sync-skill-
license.py, which exercises both its write and --check modes; only
entry-point-specific behavior (default scope, whether a write is even
possible) gets its own tests per script.

Run with: python3 -m unittest test_license_scripts -v
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
SYNC_SCRIPT = SCRIPTS_DIR / "sync-skill-license.py"
AUDIT_SCRIPT = SCRIPTS_DIR / "audit-skill-licensing.py"


def run_sync(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), *[str(a) for a in args]],
        cwd=cwd, capture_output=True, text=True,
    )


def run_audit(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), *[str(a) for a in args]],
        cwd=cwd, capture_output=True, text=True,
    )


class FixtureRepo:
    """A throwaway directory with a REUSE.toml and some SKILL.md files.

    `licenses` creates a placeholder LICENSES/<id>.txt for each id given --
    `reuse lint-file` requires the text to actually exist, unlike `reuse
    spdx`, which will happily conclude a license whose text is missing.
    """

    def __init__(self, reuse_toml: str, licenses: tuple[str, ...] = ()):
        self.root = Path(tempfile.mkdtemp(prefix="skill-license-test-"))
        (self.root / "REUSE.toml").write_text(reuse_toml)
        if licenses:
            licenses_dir = self.root / "LICENSES"
            licenses_dir.mkdir()
            for lic in licenses:
                (licenses_dir / f"{lic}.txt").write_text("placeholder license text\n")

    def write_skill(self, rel_path: str, content: str) -> Path:
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def read(self, rel_path: str) -> str:
        return (self.root / rel_path).read_text()

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


DEFAULT_REUSE_TOML = """\
version = 1
SPDX-PackageName = "fixture"

[[annotations]]
path = ["**.md"]
SPDX-FileCopyrightText = "Test"
SPDX-License-Identifier = "CC-BY-SA-4.0"
"""

COMBINED_REUSE_TOML = DEFAULT_REUSE_TOML + """
[[annotations]]
path = ["skills/special/SKILL.md"]
SPDX-FileCopyrightText = "Test AND Third Party"
SPDX-License-Identifier = "GPL-3.0-or-later AND CC-BY-SA-4.0"
"""

VALID_SKILL = """\
---
name: foo
license: {license}
---
body text
"""


class SharedCheckingLogicTests(unittest.TestCase):
    """Core logic in _skill_license_lib.py, exercised via sync-skill-license.py
    since it can run in both write and --check mode."""

    def setUp(self):
        self.repo = FixtureRepo(DEFAULT_REUSE_TOML, licenses=("CC-BY-SA-4.0",))
        self.addCleanup(self.repo.cleanup)

    def test_already_in_sync_reports_ok_and_does_not_write(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        before = skill.stat().st_mtime_ns
        result = run_sync(skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)
        self.assertEqual(skill.stat().st_mtime_ns, before)

    def test_drift_is_fixed_in_write_mode(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="MIT-wrong"))
        result = run_sync(skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SET", result.stdout)
        self.assertIn("license: CC-BY-SA-4.0", self.repo.read("skills/foo/SKILL.md"))
        self.assertNotIn("MIT-wrong", self.repo.read("skills/foo/SKILL.md"))

    def test_check_mode_reports_drift_but_never_writes(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="MIT-wrong"))
        original = skill.read_text()
        result = run_sync("--check", skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("DRIFT", result.stdout)
        self.assertEqual(skill.read_text(), original, "check mode must never modify the file")

    def test_combined_license_expression_is_written_in_full(self):
        repo = FixtureRepo(COMBINED_REUSE_TOML, licenses=("CC-BY-SA-4.0", "GPL-3.0-or-later"))
        self.addCleanup(repo.cleanup)
        skill = repo.write_skill("skills/special/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        result = run_sync(skill)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        content = repo.read("skills/special/SKILL.md")
        self.assertIn("GPL-3.0-or-later", content)
        self.assertIn("CC-BY-SA-4.0", content)

    def test_missing_frontmatter_is_skipped_not_crashed(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", "# just a heading, no frontmatter\n")
        result = run_sync(skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("SKIP", result.stdout)
        self.assertIn("no YAML frontmatter", result.stdout)

    def test_frontmatter_without_license_key_is_skipped(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", "---\nname: foo\n---\nbody\n")
        result = run_sync(skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("SKIP", result.stdout)
        self.assertIn("no license: key", result.stdout)

    def test_file_not_covered_by_any_reuse_annotation_is_skipped(self):
        repo = FixtureRepo("version = 1\nSPDX-PackageName = \"fixture\"\n")  # no annotations at all
        self.addCleanup(repo.cleanup)
        skill = repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        result = run_sync(skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("SKIP", result.stdout)
        self.assertIn("reuse lint-file failed", result.stdout)
        self.assertEqual(skill.read_text(), VALID_SKILL.format(license="CC-BY-SA-4.0"))

    def test_missing_license_text_is_caught_even_though_spdx_still_concludes_a_license(self):
        # reuse spdx alone would happily conclude CC-BY-SA-4.0 here (it
        # doesn't check that LICENSES/ actually has the text) -- this is
        # exactly the gap folding in lint-file closes.
        repo = FixtureRepo(DEFAULT_REUSE_TOML)  # note: no licenses=(...) -- LICENSES/ is empty
        self.addCleanup(repo.cleanup)
        original = VALID_SKILL.format(license="wrong-value")
        skill = repo.write_skill("skills/foo/SKILL.md", original)
        result = run_sync(skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("SKIP", result.stdout)
        self.assertIn("reuse lint-file failed", result.stdout)
        self.assertEqual(skill.read_text(), original, "must not sync a license whose text file doesn't exist")

    def test_quoted_value_is_treated_as_different_from_unquoted(self):
        # Documents actual behavior: the comparison is a raw string match,
        # so a pre-existing quoted value is (correctly) flagged as drift
        # even though it's semantically the same license.
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license='"CC-BY-SA-4.0"'))
        result = run_sync("--check", skill)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("DRIFT", result.stdout)

    def test_lint_failure_on_one_file_does_not_block_a_clean_sibling_in_the_same_batch(self):
        # Only skills/good is covered by REUSE.toml -- skills/bad is a
        # genuine reuse lint-file failure (no annotation matches it at all).
        repo = FixtureRepo(
            "version = 1\nSPDX-PackageName = \"fixture\"\n"
            "[[annotations]]\npath = [\"skills/good/**\"]\n"
            "SPDX-FileCopyrightText = \"Test\"\nSPDX-License-Identifier = \"CC-BY-SA-4.0\"\n",
            licenses=("CC-BY-SA-4.0",),
        )
        self.addCleanup(repo.cleanup)
        repo.write_skill("skills/bad/SKILL.md", VALID_SKILL.format(license="whatever"))
        repo.write_skill("skills/good/SKILL.md", VALID_SKILL.format(license="wrong"))
        result = run_sync(repo.root / "skills/bad/SKILL.md", repo.root / "skills/good/SKILL.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)  # bad file makes the run fail...
        self.assertIn("SKIP", result.stdout)
        self.assertIn("reuse lint-file failed", result.stdout)
        self.assertIn("SET", result.stdout)  # ...but the good one still got processed
        self.assertIn("license: CC-BY-SA-4.0", repo.read("skills/good/SKILL.md"))

    def test_one_target_outside_repo_root_does_not_abort_the_rest_of_the_batch(self):
        good = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="wrong"))
        other_repo = FixtureRepo(DEFAULT_REUSE_TOML, licenses=("CC-BY-SA-4.0",))
        self.addCleanup(other_repo.cleanup)
        outside = other_repo.write_skill("skills/bar/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        result = run_sync(good, outside)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)  # outside file errors
        self.assertIn("SET", result.stdout)  # but the good one still got processed
        self.assertIn("license: CC-BY-SA-4.0", self.repo.read("skills/foo/SKILL.md"))

    def test_malformed_reuse_toml_gives_clean_error_not_a_traceback(self):
        repo = FixtureRepo("this is not valid toml [[[")
        self.addCleanup(repo.cleanup)
        skill = repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        result = run_sync(skill)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertIn("reuse spdx", result.stdout + result.stderr)

    def test_no_reuse_toml_above_target_gives_clean_error(self):
        orphan_dir = Path(tempfile.mkdtemp(prefix="no-reuse-toml-"))
        self.addCleanup(lambda: shutil.rmtree(orphan_dir, ignore_errors=True))
        skill = orphan_dir / "SKILL.md"
        skill.write_text(VALID_SKILL.format(license="CC-BY-SA-4.0"))
        result = run_sync(skill)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no REUSE.toml found", result.stdout + result.stderr)

    def test_successful_write_leaves_no_tmp_file_behind(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="wrong"))
        run_sync(skill)
        leftovers = list(skill.parent.glob(".*.tmp"))
        self.assertEqual(leftovers, [])

    def test_concurrent_runs_against_different_files_all_succeed(self):
        import concurrent.futures

        skills = [
            self.repo.write_skill(f"skills/s{i}/SKILL.md", VALID_SKILL.format(license="wrong"))
            for i in range(8)
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda s: run_sync(s), skills))
        for r in results:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for i in range(8):
            self.assertIn("license: CC-BY-SA-4.0", self.repo.read(f"skills/s{i}/SKILL.md"))


class SyncSkillLicenseCliTests(unittest.TestCase):
    """Entry-point-specific behavior: agent-facing, write-by-default, explicit files only."""

    def setUp(self):
        self.repo = FixtureRepo(DEFAULT_REUSE_TOML, licenses=("CC-BY-SA-4.0",))
        self.addCleanup(self.repo.cleanup)

    def test_no_files_is_a_usage_error(self):
        result = run_sync(cwd=self.repo.root)
        self.assertNotEqual(result.returncode, 0)

    def test_there_is_no_all_flag(self):
        # A repo-wide sweep is audit-skill-licensing.py's job, not this
        # script's -- --all shouldn't exist here at all.
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        result = run_sync("--all", skill, cwd=self.repo.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_default_mode_without_check_flag_writes(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="wrong"))
        result = run_sync(skill)  # no --check
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("license: CC-BY-SA-4.0", self.repo.read("skills/foo/SKILL.md"))


class AuditSkillLicensingCliTests(unittest.TestCase):
    """Entry-point-specific behavior: CI-facing, read-only always, whole-repo by default."""

    def setUp(self):
        self.repo = FixtureRepo(DEFAULT_REUSE_TOML, licenses=("CC-BY-SA-4.0",))
        self.addCleanup(self.repo.cleanup)

    def test_no_args_audits_every_skill_md_under_repo_root(self):
        self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="wrong-a"))
        self.repo.write_skill("skills/bar/SKILL.md", VALID_SKILL.format(license="wrong-b"))
        result = run_audit(cwd=self.repo.root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)  # both drifted
        self.assertIn("skills/foo/SKILL.md", result.stdout)
        self.assertIn("skills/bar/SKILL.md", result.stdout)

    def test_never_writes_even_though_there_is_no_check_flag_to_forget(self):
        skill = self.repo.write_skill("skills/foo/SKILL.md", VALID_SKILL.format(license="wrong"))
        original = skill.read_text()
        result = run_audit(cwd=self.repo.root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("DRIFT", result.stdout)
        self.assertEqual(skill.read_text(), original, "audit must never write, with or without a flag")

    def test_explicit_files_scope_to_just_those_not_the_whole_repo(self):
        clean = self.repo.write_skill("skills/clean/SKILL.md", VALID_SKILL.format(license="CC-BY-SA-4.0"))
        self.repo.write_skill("skills/untouched-and-broken/SKILL.md", "no frontmatter\n")
        result = run_audit(clean)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("untouched-and-broken", result.stdout)

    def test_there_is_no_check_flag(self):
        result = run_audit("--check", cwd=self.repo.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)


if __name__ == "__main__":
    unittest.main()
