# Contributing

This is a single-subdomain domain repo (see
[structuring-domain-repos](skills/structuring-domain-repos/SKILL.md)) — one
plugin, one place new skills go: `skills/<name>/SKILL.md`.

## Adding or changing a skill

1. Decide whether this is a new skill or belongs in an existing one — see
   [placing-new-skills](skills/placing-new-skills/SKILL.md), specifically
   "New skill or extend an existing one?".
2. Create `skills/<name>/SKILL.md` with frontmatter: `name`, `license:
   CC-BY-SA-4.0`, and a `description` that states what it does, when to use
   it, and what *not* to use it for.
3. Follow the naming, negative-trigger, and no-scaffolded-trigger
   conventions in [authoring-domain-skills](skills/authoring-domain-skills/SKILL.md).
4. Adding a supporting file (`scripts/`, `references/`) that isn't
   obviously `.md`? See [licensing-new-files](skills/licensing-new-files/SKILL.md)
   for how it should be categorized in `REUSE.toml`.
5. PR title: `Add skill: <name>` (or `Update skill: <name>` for changes).

## Before opening a PR

- `claude plugin validate --strict .`
- `reuse lint`

## Licensing your contribution

By submitting a PR, your contribution is licensed under this repo's
existing terms — AGPL-3.0-or-later for code, CC-BY-SA-4.0 for skill
content — see `LICENSES/` and `REUSE.toml`. No separate agreement.

## Response time

Presently maintained by one person alongside other work — no committed
review turnaround. Slower than a funded project, but every PR gets read.
