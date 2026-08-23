# Security

Plugins execute arbitrary code with the installing user's privileges —
see [structuring-domain-repos](skills/structuring-domain-repos/SKILL.md).

## Scope

In scope: a skill's bundled `scripts/`/`references/` containing commands
that could cause unintended harm, or accidentally including sensitive
data.

Out of scope: vulnerabilities in Claude Code itself, or in tools a skill
merely references without bundling.

## Reporting

This repo doesn't have a dedicated private-advisory channel yet — open a
GitHub issue. If something shouldn't be public before a fix ships, say so
in the issue title without detail and ask for a private follow-up.
