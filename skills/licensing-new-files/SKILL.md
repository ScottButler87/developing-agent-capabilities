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

## A skill's own `license:` frontmatter field must match REUSE.toml — sync it with a script, don't hand-type it

`REUSE.toml` is the authoritative record for this repo, but it doesn't
travel if a skill folder is copied out onto another platform — the
[agent skills spec](https://agentskills.io/specification) gives skills
their own `license:` frontmatter field precisely for that case. Don't
maintain it as a second, independently-typed copy of the categorization
decision in step 3 above — that's exactly the kind of two-places-with-one-
fact setup that drifts silently.

Two scripts share this job, deliberately split by caller rather than one
script trying to serve both: an agent that just wrote or edited a skill
wants it *fixed*, now; CI auditing the whole repo must never write
anything on its own. Both check the same thing per file — `reuse
lint-file` first (catches a gap `reuse spdx` alone would miss: a file
can "conclude" a license just fine even when that license's text is
missing from `LICENSES/`), then whether the frontmatter already matches
what `reuse spdx` concludes from `REUSE.toml` — they only differ in
scope and whether a fix gets written.

- **[`scripts/sync-skill-license.py`](scripts/sync-skill-license.py)** —
  agent-facing. Run this against the skill(s) you just touched, right
  after changing `REUSE.toml` (a new annotation block, or a path added
  to an existing one). Defaults to writing the fix; `--check` previews
  without writing. Takes explicit file paths only — no `--all`, this
  isn't a repo-wide sweep:
  ```
  sync-skill-license.py path/to/skills/some-skill/SKILL.md
  sync-skill-license.py --check path/to/skills/some-skill/SKILL.md
  ```
- **[`scripts/audit-skill-licensing.py`](scripts/audit-skill-licensing.py)**
  — CI-facing. Read-only with no flag that changes that — there's no
  write path to accidentally trigger. Defaults to every `SKILL.md` under
  the repo root:
  ```
  audit-skill-licensing.py
  ```

Both are safe to run from multiple agents at once, including against
different files in the same wave: each target file `sync-skill-license.py`
writes goes through a write-temp-then-atomic-rename in its own directory,
so a concurrent run touching a *different* file never interferes. Wire
`audit-skill-licensing.py` into CI alongside `claude plugin validate
--strict` and `reuse lint`.
