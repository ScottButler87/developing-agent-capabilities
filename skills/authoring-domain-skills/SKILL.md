---
name: authoring-domain-skills
license: CC-BY-SA-4.0
description: Naming, trigger-writing, and frontmatter conventions for an individual SKILL.md — a two-lane naming rule (gerund-verb for procedures vs. noun-phrase for background/orientation knowledge), why cross-skill routing belongs in the body and not the description, a ban on scaffolded "when to use" text, and where custom frontmatter fields belong. Use when reviewing an existing skill's quality, or once a skill's placement is already settled and it's time to write its name, description, or frontmatter.
---

# Authoring domain skills

## Naming: two lanes, not one

- **Procedural skills** (the majority — a skill that performs or guides an action): gerund-verb-phrase, e.g. `extracting-game-phase-data`, `parsing-save-files`.
- **Knowledge/orientation skills** (background, context, vocabulary that inform other work rather than being an action themselves): descriptive noun phrase, e.g. `gameplay-loop-orientation`, `progression-system-overview`. Forcing these into gerund form produces a padded, performative name (`orienting-to-the-gameplay-loop`) — don't.

The test: if the honest answer to "what does this skill do" is a verb, gerund it. If the honest answer is "it's context," name it as what it is.

## Cross-skill routing belongs in the body, not the description

Don't put "do not use for X, see sibling-skill" clauses in a `description`. There's no evidence this pattern earns its keep, and good reason to think it doesn't: [the official best-practices doc](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) never uses it, its prescribed fix for selection ambiguity is "be specific and include key terms" (a positive-content fix, not a negation), and it states plainly that *all* installed skills' `name`+`description` are pre-loaded into the system prompt together, permanently, for every session — "the context window is a public good," every token there competes forever, whether or not the disambiguation it's buying ever actually mattered.

A redirect belongs inline, at the specific point in the body where the need for it actually arises — a step that hands off to a sibling skill's territory — not in a centralized summary near the top. This system used to open every skill's body with a `Scope:` line restating its sibling pointers; checked against this repo's own four skills, that line was either a verbatim duplicate of a pointer already sitting inline at its real trigger point, or had no inline trigger point anywhere in the body at all — meaning nothing ever actually needed it, the same tell that killed the description-level version. Both cases are gone now: an inline pointer earns its place by corresponding to a real step in the procedure; if no such step exists, the pointer doesn't belong in this skill's body at all — the sibling's own `description` is already enough for whoever's task actually needs it to find it. If a genuine selection-time misfire ever turns up — observed, not speculated, per [the best-practices doc](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)'s own evaluation-driven approach — fix it by sharpening the *positive* language in the `description` first.

## Forbidden: scaffolded trigger text

Never generate a "when to use" section by grammatically stuffing the skill's own name into a template sentence ("When deploying or configuring **extracting game phase data** capabilities..."). That says nothing and occupies the exact field Claude matches against for discovery. A skill with a stub trigger is worse than no skill — write the real answer or don't ship the skill yet.

## Custom frontmatter goes under `metadata:`

The [agentskills.io](https://agentskills.io/specification) open standard defines exactly six frontmatter fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. `claude plugin validate --strict` does not currently reject an unknown top-level key (verified — it passes silently), so this is a discipline to follow, not something the pre-PR check catches for you. Every skill here should set `license` (`CC-BY-SA-4.0` for a normal skill) — it's the one piece of licensing information that survives a skill directory being copied out of its plugin wrapper onto another platform; `REUSE.toml` only covers files that stay inside this repo. If a skill's own supporting files (`references/`, `scripts/`) need their own categorization beyond this, see [licensing-new-files](../licensing-new-files/SKILL.md). Anything else this system wants to track (game version, patch number, source-wiki link) nests under `metadata:` as an arbitrary string map, not as a new top-level key. Free to get right from the start; expensive to retrofit across many files later.

If a `metadata:` field is meant to be structured/machine-checked (an ID from an external taxonomy, a version range), CI must validate it against a canonical list, or it shouldn't be a structured field at all — an unvalidated structured field is worse than prose, because it looks machine-readable and gets trusted downstream without actually being checked.

## Bundle a script only when the skill actually needs one

Don't add `scripts/`/`references/` to a skill by default just because the format allows it. An unused or stub script sitting in a skill's directory drifts out of sync with the skill's own body over time and adds nothing a human or agent can act on — add supporting files only once the skill has a concrete, current reason for one.

## A `SKILL.md`'s folder is the portable unit; the plugin around it isn't

A skill written to this spec is already loadable by any compatible agent platform (Claude Code, Copilot, Cursor, Codex CLI, Gemini CLI, and more) — but skills here live inside a plugin (`skills/<name>/SKILL.md` for a single-plugin domain, or `plugins/<subdomain>/skills/<name>/SKILL.md` once it's promoted to multiple), and the plugin/marketplace wrapper is Claude-Code-specific. A user on another platform consumes the skill directory directly (clone the repo, copy or symlink the folder out) rather than installing the plugin — some manual step, not zero, but the skill's own content needs no rewriting for that to work. Claude Code's own optional frontmatter extensions (e.g. `disable-model-invocation`) aren't part of the six-field spec; a skill using them is already off-spec for other platforms. Don't also maintain a separate, platform-specific instructions file (e.g. a `.github/copilot-instructions.md`) alongside this — a second file restating the same conventions for a different tool has nothing keeping it in sync with the `SKILL.md` it duplicates, and will drift from it. The shared `SKILL.md` format is what's meant to be maintained; write it once.
