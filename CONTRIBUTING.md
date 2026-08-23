# Contributing

Skill-authoring, placement, and licensing conventions here apply to any
domain repo built on this system — another repo's CONTRIBUTING.md can
point here for these rather than repeating them, and only needs to state
what's specific to its own domain.

This particular repo is itself single-subdomain — see
[structuring-domain-repos](skills/structuring-domain-repos/SKILL.md) for
what that means.

## Adding or changing a skill

1. Decide whether this is a new skill or belongs in an existing one — see
   [placing-new-skills](skills/placing-new-skills/SKILL.md), specifically
   "New skill or extend an existing one?".
2. Create `skills/<name>/SKILL.md`. Don't guess the frontmatter fields or
   naming/trigger conventions — [authoring-domain-skills](skills/authoring-domain-skills/SKILL.md)
   is the source of truth for both.
3. Adding a supporting file (`scripts/`, `references/`) that isn't
   obviously `.md`? See [licensing-new-files](skills/licensing-new-files/SKILL.md)
   for how it should be categorized in `REUSE.toml`.
4. PR title: `Add skill: <name>` (or `Update skill: <name>` for changes).

## Before opening a PR

- `claude plugin validate --strict .`
- `reuse lint`

## Licensing your contribution

By submitting a PR, your contribution is licensed under the terms declared
in `REUSE.toml` for whichever files you touch (full texts in `LICENSES/`).
No separate agreement.

## Response time

Presently maintained by one person alongside other work — no committed
review turnaround. Slower than a funded project, but every PR gets read.
