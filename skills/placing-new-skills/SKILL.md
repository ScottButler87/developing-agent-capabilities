---
name: placing-new-skills
license: CC-BY-SA-4.0
description: Decides where a new skill belongs before it's written — an existing plugin, a new plugin in the same repo, a new domain repo, a domain repo someone else already maintains, or a shared plugin two others depend on — and whether it should be a skill at all rather than CLAUDE.md or a project's own .claude/skills/. Use when the user wants to capture knowledge as a skill and hasn't yet settled which repo or plugin it belongs in, or when deciding whether new knowledge needs its own skill versus extending an existing one. Do not use once placement is already settled and the task is writing or reviewing the skill's actual content — see authoring-domain-skills.
---

# Placing new skills

Scope: the decision procedure for where a new skill goes, run before authoring it. For the underlying model (domain/subdomain/plugin/marketplace/dependency mechanics) and how to bootstrap or grow a domain repo once one is actually needed, see [structuring-domain-repos](../structuring-domain-repos/SKILL.md). Once placement is decided, for how to actually write it well see [authoring-domain-skills](../authoring-domain-skills/SKILL.md) and [the Skill authoring best practices doc](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

## Decision procedure

0. **Is this a skill at all?** A single fact or preference belongs in CLAUDE.md, not a skill. Knowledge specific to one codebase belongs in that project's own `.claude/skills/`, not a domain repo.
1. **Does an existing domain repo cover this subject — including one someone else already maintains?** If so, this belongs there: contribute it as a PR rather than starting a competing repo. Consolidating knowledge into the domain the wider community already looks to is the point; fragmenting it into a new personal repo works against that. Only bootstrap a new domain if genuinely nothing covers the subject.
2. **Which subdomain plugin covers this?**
   - An existing plugin covers it → add the skill there, or extend an existing skill instead of adding a new one — see "New skill or extend an existing one?" below for the test.
   - Two existing plugins both genuinely need it, for a use case that already exists (not speculative) → don't put it in either. Symlink or extract, per [structuring-domain-repos](../structuring-domain-repos/SKILL.md).
   - Nothing covers it → this is a new subdomain — create a new plugin for it in the domain's repo, promoting to a multi-plugin structure if this is the domain's second subdomain.

## New skill or extend an existing one?

Don't test this by topic ("is it the same capability, just more detail?") — a single topic can have multiple genuinely distinct entry points, and topic-similarity can't tell them apart. Test by entry point instead: list the concrete situations that should surface this knowledge, and check each one against every existing skill's own description. If every situation already falls inside one skill's stated scope, extend that skill. If even one doesn't — a genuinely distinct upstream task, not just more detail on the one already covered — give the knowledge its own skill, discoverable regardless of which task led there. A topic being singular doesn't make its trigger-moment singular; count entry points, not subject matter.

## Partitioning is revisable

Re-examine it as understanding grows, not just at creation — a subdomain boundary chosen earlier can stop fitting. Moving skills between plugins, or splitting/merging plugins, isn't a failure of the original decision.
