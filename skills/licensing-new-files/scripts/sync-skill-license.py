#!/usr/bin/env python3
"""Fix one or more skills' REUSE compliance and frontmatter `license:` field.

Agent-facing: run this right after drafting or editing a skill whose
license isn't the repo's plain default (e.g. content synthesized from a
copyleft source). Defaults to *writing* the fix -- that's the point, you
already know you want it applied. Only takes explicit file paths, no
--all: this is a per-skill fixup step, not a repo-wide audit. For that,
see the sibling script audit-skill-licensing.py (CI-facing, read-only,
defaults to every skill in the repo).

For each file given:
1. Checks it against `reuse lint-file`, scoped to just the files given
   (so an unrelated pre-existing issue elsewhere in the repo can't
   block this) -- catches a gap `reuse spdx` alone would miss: a file
   can "conclude" a license just fine even when that license's
   LICENSES/*.txt is missing entirely.
2. For files that pass that, asks `reuse spdx` what license it
   concludes for the file and rewrites its frontmatter `license:` line
   to match REUSE.toml -- the actual source of truth. This script never
   parses REUSE.toml itself.

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
    sync-skill-license.py --check FILE [FILE ...]  # preview without writing

Requires the `reuse` CLI on PATH and a REUSE.toml above the target file(s).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _skill_license_lib import find_repo_root, run


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path, help="one or more SKILL.md paths to fix")
    ap.add_argument("--check", action="store_true", help="report drift without writing; exit 1 if any found")
    args = ap.parse_args()

    repo_root = find_repo_root(args.files[0])
    sys.exit(run(args.files, repo_root, args.check))


if __name__ == "__main__":
    main()
