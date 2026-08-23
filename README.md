# developing-ai-capabilities

Conventions for organizing Claude Code skills into git repos: one repo per
domain, one plugin per subdomain, self-contained skills, local-first
iteration, and optional public discovery. Domains are separate repos
deliberately, so each can eventually be owned by its own community of
contributors, independent of any other domain's.

Example: a `satisfactory` domain repo might grow into `plugins/game-knowledge/`
and `plugins/save-file-tooling/` as two subdomains, each its own plugin.

Persistent install, no marketplace needed: symlink this repo into your
skills directory (or scaffold a new one with `claude plugin init`):

```
ln -s <path-to-this-repo> ~/.claude/skills/developing-ai-capabilities
```

It then loads automatically in every session as
`developing-ai-capabilities@skills-dir`. For a one-off session without
touching `~/.claude/skills/`, use `claude --plugin-dir <path-to-this-repo>`
instead.

See `skills/*/SKILL.md` for what's here — each skill's own `description`
says what it does and when to use it; that's also the exact field Claude
matches against for discovery, so it's kept accurate deliberately and isn't
re-summarized here. Skills follow the open
[agentskills.io](https://agentskills.io/specification) format, so they're
already portable to any compatible agent platform, not just Claude Code —
the plugin/marketplace layer on top is Claude-Code-specific.

Discovery posture for *this* repo: **Deferred.** No `marketplace.json` yet;
load with the skills-directory symlink or `--plugin-dir`. This repo is
personal/meta-scoped rather than aimed at outside contribution, so Deferred
fits — unlike a genuine domain repo (see structuring-domain-repos), which
needs more than this to be community-installable.

## License

Dual-licensed for the two different kinds of contribution this repo holds.
Code under **AGPL-3.0-or-later**: its network clause matters because this
is tooling meant to be run by AI agents, so it stops someone hosting a
modified version of a bundled script or server behind a remote service
without sharing changes back (that clause only covers code actually
licensed AGPL, not the skill content). Prose (SKILL.md content, docs) under
**CC-BY-SA-4.0**, so the domain knowledge itself stays in the commons:
anyone who redistributes or adapts it keeps their version open too.
Declared per-file via [REUSE](https://reuse.software/) in `REUSE.toml`;
full license texts in `LICENSES/`.
