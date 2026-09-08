---
name: licensing-new-files
license: CC-BY-SA-4.0
description: Categorizes an individual file's license (AGPL vs CC-BY-SA) and fixes a failing `reuse lint`/CI license check — the REUSE.toml mechanics, the pitfalls (never a catch-all, glob by location not extension for ambiguous formats like JSON/YAML, use `**/` not root-anchored paths, verify with real file content), and what to do when a new file type doesn't match any existing annotation. Use when adding a file that isn't obviously covered by the existing REUSE.toml — a skill's reference file, extracted data, a new script — or when `reuse lint`/CI fails on a license check.
---

# Licensing new files

## A `reuse lint` failure is the system working, not a bug to silence

A file that doesn't match any `REUSE.toml` annotation isn't "unprotected" — it reverts to ordinary default copyright (all rights reserved), which is *more* restrictive than intended, not a permissive gap. `reuse lint` failing on it is exactly the signal that a real categorization decision is needed. **Never fix this by adding a catch-all** (`path = ["**"]`): a catch-all makes every file compliant by definition, which means `reuse lint` can never again flag a new file type that needs a real decision — it silently inherits whatever the catch-all says, correct or not. An earlier draft of this repo's own `REUSE.toml` had a catch-all, added to make a local `reuse lint` check pass quickly — caught and removed before ever being committed, and wrong for exactly this reason.

## Deciding a file's category

Ask what the file *is*, not what format it's serialized in. File extension is not a reliable proxy for code vs. content — JSON, YAML, and TOML can each encode either a structural manifest (`plugin.json`, a CI workflow) or pure domain data (an extracted `DocsItems.json`-style dump). A blanket `path = ["**.json"]` → AGPL glob would wrongly sweep the latter into a code license.

- **Structural manifests and repo tooling** (plugin/marketplace config, CI, issue forms, scripts): AGPL-3.0-or-later. Glob these by *location* (`.claude-plugin/**`, `scripts/**`, `.github/**`, named files like `REUSE.toml`), not by extension — location is unambiguous where extension isn't. Extension-based globs are fine only for languages never used to encode plain data (`.py`, `.sh`, `.js`, `.ts`).
- **Prose and skill content**: CC-BY-SA-4.0, globbed by `**.md`.
- **Extracted or third-party-derived data** (game stats, near-verbatim descriptions pulled from a game or other external source): pause before assigning either license. Bare facts generally aren't copyrightable at all, and near-verbatim text belongs to whoever holds rights to the original source, not to this repo — a license here can only cover original curatorial/organizational choices (the schema, the joins, any original prose written about the data), not the underlying facts or copied text. If this comes up, treat it as its own decision rather than defaulting to either bucket.

## Glob syntax pitfalls, both found by actually testing rather than assuming

- **Location globs must use `**/` and not be root-anchored.** `.claude-plugin/**` only matches at the repo root; it silently misses `plugins/<subdomain>/.claude-plugin/plugin.json` — this system's own standard multi-plugin layout. Write `**/.claude-plugin/**`.
- **Verify with real file content, not empty files.** `reuse lint` silently exempts 0-byte files from needing license coverage, so a `touch`-created test fixture can make a broken config look compliant. Write actual content into test files before trusting a lint result.

## Fixing a failure

1. Run `reuse lint` and read which specific file(s) it names.
2. Decide the file's category per the section above.
3. Add it to the matching `REUSE.toml` annotation block (by location or, only if unambiguous, by extension) — or start a new block if nothing existing fits.
4. Re-run `reuse lint` to confirm, with real file content if this is a test.

This repo's own [`REUSE.toml`](../../REUSE.toml) is the current worked example.

## A skill's own `license:` frontmatter field must match REUSE.toml — sync it with the script, don't hand-type it

`REUSE.toml` is the authoritative record for this repo, but it doesn't
travel if a skill folder is copied out onto another platform — the
[agent skills spec](https://agentskills.io/specification) gives skills
their own `license:` frontmatter field precisely for that case. Don't
maintain it as a second, independently-typed copy of the categorization
decision in step 3 above — that's exactly the kind of two-places-with-one-
fact setup that drifts silently. Instead, after changing `REUSE.toml` (a
new annotation block, or adding a path to an existing one), run
[`scripts/sync-skill-license.py`](scripts/sync-skill-license.py) against
the affected skill(s). One script covers the whole per-skill licensing
job, so there's only one thing to run: it first checks the file itself
against `reuse lint-file` (catches a gap `reuse spdx` alone would miss —
a file can "conclude" a license just fine even when that license's text
is missing from `LICENSES/`), and only for files that pass that, asks
`reuse spdx` what license each one concludes to (not a hand-rolled glob
matcher, so it can't disagree with what whole-repo `reuse lint` checks)
and rewrites the frontmatter `license:` line to match:

```
sync-skill-license.py path/to/skills/some-skill/SKILL.md   # sync one skill
sync-skill-license.py --all                                # sync every SKILL.md in the repo
sync-skill-license.py --all --check                        # report drift only, write nothing, exit 1 if any found
```

It's safe to run from multiple agents at once, including against
different files in the same wave: each target file is written via a
write-temp-then-atomic-rename in its own directory, so a concurrent run
touching a *different* file never interferes. Run `--check` as a gate
alongside `claude plugin validate --strict` and `reuse lint` before
committing any skill whose license isn't the repo's plain default.
