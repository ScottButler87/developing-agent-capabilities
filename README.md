# developing-ai-capabilities

Conventions for organizing Claude Code skills into git repos: one repo per
domain, one plugin per subdomain, self-contained skills, local-first
iteration, and optional public discovery. Domains are separate repos
deliberately, so each can eventually be owned by its own community of
contributors, independent of any other domain's. Not affiliated with or
endorsed by Anthropic.

Example: a `satisfactory` domain repo might grow into `plugins/game-knowledge/`
and `plugins/save-file-tooling/` as two subdomains, each its own plugin.

Persistent install, no marketplace needed: symlink this repo into your
skills directory:

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
load with the skills-directory symlink or `--plugin-dir`. Not actively
promoted, but `CONTRIBUTING.md` exists anyway — per this system's own
"cheap now, expensive to retrofit" rule — so it's ready if that changes. A
genuine domain repo (see structuring-domain-repos) needs more than
Deferred to be community-installable; this one doesn't need to be, yet.

## License

Dual-licensed for the two different kinds of contribution this repo holds
— code under **AGPL-3.0-or-later**, prose under **CC-BY-SA-4.0** — see
[structuring-domain-repos](skills/structuring-domain-repos/SKILL.md) for
why. Declared per-file via [REUSE](https://reuse.software/) in
`REUSE.toml`; full license texts in `LICENSES/`.
