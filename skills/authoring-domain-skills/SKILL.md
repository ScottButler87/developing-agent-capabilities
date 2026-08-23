---
name: authoring-domain-skills
license: CC-BY-SA-4.0
description: Naming, trigger-writing, and frontmatter conventions for an individual SKILL.md — a two-lane naming rule (gerund-verb for procedures vs. noun-phrase for background/orientation knowledge), a required negative-trigger clause, a ban on scaffolded "when to use" text, and where custom frontmatter fields belong. Use when reviewing an existing skill's quality, or once a skill's placement is already settled and it's time to write its name, description, or frontmatter. Do not use for deciding where a new skill belongs (see placing-new-skills), how the repo/plugin/marketplace is structured (see structuring-domain-repos), or categorizing a supporting file's license (see licensing-new-files).
---

# Authoring domain skills

Scope: conventions specific to this system, layered on top of — not duplicating — [the Skill authoring best practices doc](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), which stays the primary reference for progressive disclosure, degrees of freedom, evaluations, and everything else about writing a good skill. This skill covers only what that doc doesn't, learned from comparing against a real, large, community-contributed reference implementation ([mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills)).

## Naming: two lanes, not one

- **Procedural skills** (the majority — a skill that performs or guides an action): gerund-verb-phrase, e.g. `extracting-game-phase-data`, `parsing-save-files`.
- **Knowledge/orientation skills** (background, context, vocabulary that inform other work rather than being an action themselves): descriptive noun phrase, e.g. `gameplay-loop-orientation`, `progression-system-overview`. Forcing these into gerund form produces a padded, performative name (`orienting-to-the-gameplay-loop`) — don't.

The test: if the honest answer to "what does this skill do" is a verb, gerund it. If the honest answer is "it's context," name it as what it is.

## Required: a negative-trigger clause in the description

Every skill's `description` states what it's *not* for and which sibling skill to use instead — e.g. "Do not use for save-file analysis; use `parsing-save-files` instead." The description, not the body, is what Claude matches against for discovery, so that's where the negative trigger has to live to do its job. This is the cheapest available fix for skill misfire, and it doubles as machine-readable routing between sibling skills, which matters more once skills are split across plugin boundaries. This skill's own description is the worked example.

## Forbidden: scaffolded trigger text

Never generate a "when to use" section by grammatically stuffing the skill's own name into a template sentence ("When deploying or configuring **extracting game phase data** capabilities..."). That says nothing and occupies the exact field Claude matches against for discovery. A skill with a stub trigger is worse than no skill — write the real answer or don't ship the skill yet.

## Custom frontmatter goes under `metadata:`

The [agentskills.io](https://agentskills.io/specification) open standard defines exactly six frontmatter fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Every skill here should set `license` (`CC-BY-SA-4.0` for a normal skill) — it's the one piece of licensing information that survives a skill directory being copied out of its plugin wrapper onto another platform; `REUSE.toml` only covers files that stay inside this repo. If a skill's own supporting files (`references/`, `scripts/`) need their own categorization beyond this, see [licensing-new-files](../licensing-new-files/SKILL.md). Anything else this system wants to track (game version, patch number, source-wiki link) nests under `metadata:` as an arbitrary string map, not as a new top-level key. Free to get right from the start; expensive to retrofit across many files later.

If a `metadata:` field is meant to be structured/machine-checked (an ID from an external taxonomy, a version range), CI must validate it against a canonical list, or it shouldn't be a structured field at all — an unvalidated structured field is worse than prose, because it looks machine-readable and gets trusted downstream without actually being checked.

## Bundle a script only when the skill actually needs one

Don't add `scripts/`/`references/` to a skill by default just because the format allows it. An unused or stub script sitting in a skill's directory drifts out of sync with the skill's own body over time and adds nothing a human or agent can act on — add supporting files only once the skill has a concrete, current reason for one.

## A `SKILL.md`'s folder is the portable unit; the plugin around it isn't

A skill written to this spec is already loadable by any compatible agent platform (Claude Code, Copilot, Cursor, Codex CLI, Gemini CLI, and more) — but skills here live nested inside a plugin (`plugins/<subdomain>/skills/<name>/SKILL.md`), and the plugin/marketplace wrapper is Claude-Code-specific. A user on another platform consumes the skill directory directly (clone the repo, copy or symlink the folder out) rather than installing the plugin — some manual step, not zero, but the skill's own content needs no rewriting for that to work. Claude Code's own optional frontmatter extensions (e.g. `disable-model-invocation`) aren't part of the six-field spec; a skill using them is already off-spec for other platforms. Don't also maintain a separate, platform-specific instructions file (e.g. a `.github/copilot-instructions.md`) alongside this — a second file restating the same conventions for a different tool has nothing keeping it in sync with the `SKILL.md` it duplicates, and will drift from it. The shared `SKILL.md` format is what's meant to be maintained; write it once.
