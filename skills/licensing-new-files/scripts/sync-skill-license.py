#!/usr/bin/env python3
"""Sync a skill's frontmatter `license:` field from REUSE.toml.

REUSE.toml stays the single source of truth for which license applies to
which file. This script never parses REUSE.toml itself -- it asks the
`reuse` CLI (the same tool `reuse lint` uses) what license it concludes
for each target file, and rewrites that file's frontmatter `license:`
line to match. That keeps the two in sync by construction instead of by
someone remembering to hand-type the same string twice.

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


def get_license_map(repo_root: Path) -> dict[str, str]:
    """Ask `reuse` for the concluded license of every file it tracks."""
    result = subprocess.run(
        [
            "reuse",
            "spdx",
            "--add-license-concluded",
            "--creator-person",
            "sync-skill-license.py",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
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

    targets = args.files if args.files else sorted(repo_root.rglob("SKILL.md"))

    try:
        license_map = get_license_map(repo_root)
    except subprocess.CalledProcessError as e:
        sys.exit(f"error: `reuse spdx` failed (exit {e.returncode}):\n{e.stderr}")

    exit_code = 0
    for f in targets:
        try:
            message, is_problem = sync_one(Path(f), license_map, repo_root, args.check)
            print(message)
            if is_problem:
                exit_code = 1
        except Exception as e:
            print(f"ERROR {f}: {e}")
            exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
