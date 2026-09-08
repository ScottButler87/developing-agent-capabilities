#!/usr/bin/env python3
"""Check and sync a skill's REUSE compliance and frontmatter `license:` field.

One script covers both halves of "is this skill's licensing correct,"
so an agent (or CI) only has to run one thing:

1. Per-file REUSE compliance, scoped to just the target file(s) (`reuse
   lint-file`) -- does it have copyright/license info at all, and does
   the license it claims actually have a text file in LICENSES/. This
   catches gaps `reuse spdx` alone doesn't: a file can have a
   SPDX-License-Identifier that "concludes" a license just fine even
   when that license's LICENSES/*.txt is missing entirely -- only
   lint-file checks that the text actually exists.
2. Frontmatter sync (the original job): REUSE.toml stays the single
   source of truth for which license applies to which file. This script
   never parses REUSE.toml itself -- for files that pass step 1, it
   asks `reuse spdx` what license it concludes for each one, and
   rewrites that file's frontmatter `license:` line to match. That
   keeps the two in sync by construction instead of by someone
   remembering to hand-type the same string twice.

Deliberately does NOT replace whole-repo `reuse lint` in CI: that still
covers every other file in the repo (manifests, scripts, etc.) this
script never looks at. This is the skill-licensing-specific piece of
that job, run standalone so a single skill can be checked without
needing the rest of the repo to also be clean.

Concurrency: safe to run from multiple processes at once, including
against different files in the same run. Each target file is written via
write-to-temp-then-atomic-rename in its own directory, so a write is
never observed half-done and concurrent runs touching *different* files
never interfere with each other. Two runs racing on the *same* file still
race like any other concurrent edit to that file (last rename wins) --
nothing here makes that case safe, so avoid it, same as you'd avoid two
agents editing one file at once for any other reason.

Usage:
    sync-skill-license.py FILE [FILE ...]
    sync-skill-license.py --all             # every SKILL.md under the repo root
    sync-skill-license.py --check FILE ...  # report drift, write nothing; exit 1 if any found

Requires the `reuse` CLI on PATH and a REUSE.toml above the target file(s).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LICENSE_LINE_RE = re.compile(r"^(license:[ \t]*)(.+)$", re.MULTILINE)


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    if p.is_file():
        p = p.parent
    while True:
        if (p / "REUSE.toml").is_file():
            return p
        if p.parent == p:
            raise SystemExit(f"error: no REUSE.toml found above {start}")
        p = p.parent


def _run_reuse(args: list[str], repo_root: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["reuse", *args], cwd=repo_root, capture_output=True, text=True)
    except FileNotFoundError:
        raise SystemExit("error: `reuse` CLI not found on PATH -- install it first (pip install reuse)")


def get_license_map(repo_root: Path) -> dict[str, str]:
    """Ask `reuse` for the concluded license of every file it tracks."""
    result = _run_reuse(
        ["spdx", "--add-license-concluded", "--creator-person", "sync-skill-license.py"],
        repo_root,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, "reuse spdx", result.stdout, result.stderr)
    licenses: dict[str, str] = {}
    current_file = None
    for line in result.stdout.splitlines():
        if line.startswith("FileName:"):
            current_file = line[len("FileName:") :].strip()
            if current_file.startswith("./"):
                current_file = current_file[2:]
        elif line.startswith("LicenseConcluded:") and current_file:
            licenses[current_file] = line[len("LicenseConcluded:") :].strip()
            current_file = None
    return licenses


def lint_files(paths: list[Path], repo_root: Path) -> dict[str, str]:
    """Runs `reuse lint-file` once across all paths (batched, not per-file).

    Returns {rel_path: issue_text} for files reuse flags -- e.g. no
    copyright/license annotation at all, or a license text missing from
    LICENSES/. Files not in the returned dict are clean. Scoped to just
    `paths`, so an unrelated pre-existing problem elsewhere in the repo
    never blocks checking the files actually being synced.
    """
    if not paths:
        return {}
    result = _run_reuse(["lint-file", *[str(p) for p in paths]], repo_root)
    if result.returncode == 0:
        return {}
    if result.returncode != 1:
        # 1 means "some files have findings" (safe to parse below). Anything
        # else (reuse's CLI uses 2 for a usage error, e.g. a target outside
        # the project root) means reuse never actually checked any file --
        # parsing that output for per-file matches would silently return {}
        # (a false "clean"), which is worse than failing loudly here.
        raise SystemExit(
            f"error: `reuse lint-file` failed unexpectedly (exit {result.returncode}):\n"
            f"{(result.stdout + result.stderr).strip()}"
        )
    output = result.stdout + result.stderr
    issues: dict[str, str] = {}
    for p in paths:
        abs_str = str(p.resolve())
        matches = [line.strip() for line in output.splitlines() if line.startswith(abs_str)]
        if matches:
            reasons = "; ".join(line.split(":", 1)[1].strip() for line in matches)
            try:
                key = p.resolve().relative_to(repo_root).as_posix()
            except ValueError:
                key = abs_str  # outside repo_root -- main()'s own per-file handling reports this
            issues[key] = reasons
    return issues


def compute_new_text(text: str, license_expr: str) -> tuple[str | None, str | None]:
    """Returns (new_text_or_None, error_or_None). new_text is None if already in sync."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "no YAML frontmatter"
    body = m.group(1)
    new_body, n = LICENSE_LINE_RE.subn(rf"\g<1>{license_expr}", body, count=1)
    if n == 0:
        return None, "no license: key in frontmatter"
    if new_body == body:
        return None, None
    return text[: m.start(1)] + new_body + text[m.end(1) :], None


def sync_one(path: Path, license_map: dict[str, str], repo_root: Path, check_only: bool) -> tuple[str, bool]:
    """Returns (message, is_drift_or_error)."""
    rel = path.resolve().relative_to(repo_root).as_posix()
    license_expr = license_map.get(rel)
    if not license_expr or license_expr in ("NOASSERTION", "NONE"):
        return f"SKIP {rel}: reuse reports no concluded license -- check REUSE.toml coverage", True

    text = path.read_text()
    new_text, err = compute_new_text(text, license_expr)
    if err:
        return f"SKIP {rel}: {err}", True
    if new_text is None:
        return f"OK   {rel}: already {license_expr}", False

    if check_only:
        return f"DRIFT {rel}: frontmatter out of sync, should be {license_expr}", True

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(new_text)
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise
    return f"SET  {rel}: -> {license_expr}", False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--all", action="store_true", help="sync every SKILL.md under the repo root")
    ap.add_argument("--check", action="store_true", help="report drift without writing; exit 1 if any found")
    args = ap.parse_args()

    if not args.files and not args.all:
        ap.error("give one or more SKILL.md paths, or --all")
    if args.files and args.all:
        ap.error("--all cannot be combined with explicit file paths")

    anchor = args.files[0] if args.files else Path.cwd()
    repo_root = find_repo_root(anchor)

    targets = [Path(f) for f in (args.files if args.files else sorted(repo_root.rglob("SKILL.md")))]

    try:
        license_map = get_license_map(repo_root)
    except subprocess.CalledProcessError as e:
        sys.exit(f"error: `reuse spdx` failed (exit {e.returncode}):\n{e.stderr}")

    # Resolve each target's repo-relative path up front, before the batched
    # lint-file call below: a target outside repo_root would otherwise poison
    # that whole batch call (reuse rejects it as a usage error covering all
    # paths given, not just the bad one) instead of failing just that file.
    exit_code = 0
    rel_by_target: dict[Path, str] = {}
    valid_targets: list[Path] = []
    for f in targets:
        try:
            rel_by_target[f] = f.resolve().relative_to(repo_root).as_posix()
            valid_targets.append(f)
        except ValueError as e:
            print(f"ERROR {f}: {e}")
            exit_code = 1

    lint_issues = lint_files(valid_targets, repo_root)

    for f in valid_targets:
        rel = rel_by_target[f]
        if rel in lint_issues:
            print(f"SKIP {rel}: reuse lint-file failed -- {lint_issues[rel]}")
            exit_code = 1
            continue
        try:
            message, is_problem = sync_one(f, license_map, repo_root, args.check)
            print(message)
            if is_problem:
                exit_code = 1
        except Exception as e:
            print(f"ERROR {f}: {e}")
            exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
