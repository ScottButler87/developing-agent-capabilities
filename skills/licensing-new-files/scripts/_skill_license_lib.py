#!/usr/bin/env python3
"""Shared logic for sync-skill-license.py and audit-skill-licensing.py.

Not a CLI entry point itself (leading underscore) -- both scripts import
from here so the actual checking/parsing logic exists exactly once. See
either script's own docstring for which one to run and when; the split
exists because an agent fixing up the one skill it just wrote and CI
auditing the whole repo, read-only, are different callers with
different safe defaults, not because the underlying logic differs.
"""
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
        ["spdx", "--add-license-concluded", "--creator-person", "skill-license-scripts"],
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
                key = abs_str  # outside repo_root -- callers filter these out beforehand
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


def run(targets: list[Path], repo_root: Path, check_only: bool) -> int:
    """Runs the full check/sync loop over `targets`. Returns the process exit code."""
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
            message, is_problem = sync_one(f, license_map, repo_root, check_only)
            print(message)
            if is_problem:
                exit_code = 1
        except Exception as e:
            print(f"ERROR {f}: {e}")
            exit_code = 1
    return exit_code
