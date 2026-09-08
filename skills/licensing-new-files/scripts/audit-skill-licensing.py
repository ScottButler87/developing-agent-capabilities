#!/usr/bin/env python3
"""Audit every skill's REUSE compliance and frontmatter `license:` field.

CI-facing: read-only, always. There is no flag that makes this write --
that's a deliberate difference from the sibling script
sync-skill-license.py (agent-facing, defaults to writing), not an
oversight. A CI job that could silently rewrite the repo it's supposed
to be gating is a bigger risk than the licensing drift it's checking
for, so this entry point simply never calls the write path at all.

Checks, for each target:
1. `reuse lint-file`, scoped to just the files given -- does it have
   copyright/license info at all, and does the license it claims
   actually have a text file in LICENSES/ (a gap `reuse spdx` alone
   wouldn't catch: a file can "conclude" a license just fine even when
   that license's text is missing entirely).
2. For files that pass that: does its frontmatter `license:` field
   already match what `reuse spdx` concludes from REUSE.toml.

Exits 1 if anything's uncovered or out of sync.

Usage:
    audit-skill-licensing.py               # every SKILL.md under the repo root
    audit-skill-licensing.py FILE [FILE ...]  # just these

Requires the `reuse` CLI on PATH and a REUSE.toml above the target(s).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _skill_license_lib import find_repo_root, run


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="specific SKILL.md paths; default is every one in the repo")
    args = ap.parse_args()

    anchor = args.files[0] if args.files else Path.cwd()
    repo_root = find_repo_root(anchor)
    targets = args.files if args.files else sorted(repo_root.rglob("SKILL.md"))

    sys.exit(run(targets, repo_root, check_only=True))


if __name__ == "__main__":
    main()
