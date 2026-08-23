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

No GitHub repo exists for this project yet (see the Discovery posture in
`README.md`), so there's no private-advisory mechanism to report through.
Once one does, this file will name it.
