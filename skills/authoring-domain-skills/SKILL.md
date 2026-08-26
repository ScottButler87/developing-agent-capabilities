---
name: authoring-domain-skills
license: CC-BY-SA-4.0
description: Naming, trigger-writing, and frontmatter conventions for an individual SKILL.md — a two-lane naming rule (gerund-verb for procedures vs. noun-phrase for background/orientation knowledge), why cross-skill routing belongs in the body and not the description, a ban on scaffolded "when to use" text, where custom frontmatter fields belong, the quality tenets a trustworthy skill embodies, and when/how to run a quality audit before shipping. Use when reviewing an existing skill's quality, writing a skill's name/description/frontmatter, or deciding whether a skill's content is ready to ship.
---

# Authoring domain skills

## Quality tenets

Six principles, distilled from [auditing-domain-skills](../auditing-domain-skills/SKILL.md)'s
failure-mode catalog, that separate a skill worth trusting from one that
only looks trustworthy. Internalize these while writing; the audit
procedure below exists to catch violations of them.

- **Ground every claim in verification, not plausibility.** A claim's
  authority comes from being checked against the primary source, not
  from how plausible it sounds — and nothing about a claim's *phrasing*
  signals whether that check happened. An unverified claim that turns
  out wrong doesn't just cost one wrong answer; it teaches the reader
  that the skill's claims in general can't be fully trusted. State only
  what's been traced to an actual lookup or tool run; where something
  can't be verified yet, say so rather than asserting it plainly, and
  treat a derived or heuristic value as unconfirmed until it's checked
  against independent evidence.
- **Prefer loud, visible failure over silent, plausible-looking
  failure.** Both content and the tooling that produces it degrade as
  the underlying domain changes — the only question is whether that
  degradation announces itself. Silent failure (a decoder defaulting
  instead of erroring, an invariant that's only ever been true in prose)
  looks identical to correct behavior, so it survives far longer before
  anyone notices, by which point bad data has already propagated.
  Prefer parsing/checking logic that raises on the unexpected, and back
  any stated guarantee with a runtime check that can actually fail.
- **Separate what's permanently true from what's a snapshot of today.**
  Domain data drifts independently of the skill's own content, and an
  author has no way to keep a written number correct after the moment
  they wrote it. A stale count reads as confidently correct with no
  signal that it might have drifted — worse than no number at all.
  Reserve literal numbers in prose for things that are genuinely fixed
  (constants, specific named examples); for anything describing "how
  much/how many" of a changeable dataset, point at how to recompute it
  live instead of asserting a value.
- **Write for the reader's next action, not the author's memory.** Every
  sentence should be something a future reader — human or agent — can
  act on; the story of how the content was discovered serves only the
  person who already lived through it. (This is why session narrative
  belongs in commit messages, not skill content — see "Write current
  fact, not session narrative" below.) Narrative and self-referential
  commentary cost every future reader the same attention on every read,
  for a benefit only the original author gets once.
- **Corrections fix the rule, not just the instance.** A correction is
  evidence of a systemic issue, not a one-off — treating it as the
  latter means the same class of mistake resurfaces anywhere the same
  reasoning was applied. When something's flagged wrong, ask what
  general rule was actually violated before deciding on a fix; if an
  exception to a stated rule is genuinely needed, write down why it's
  justified by the rule's own rationale, not left as an unexplained
  carve-out.
- **Verification — automated or manual — must actually verify, not just
  run.** A checker exists to catch defects — if the checker itself is
  unscoped or unverified, its output inherits false authority (it looks
  like a legitimate finding) while being wrong, which is worse than
  having no checker, because it's trusted more. The same applies to a
  human or agent's own edit-verification: a tool reporting success only
  confirms the mechanical operation happened, not that the result is
  coherent. Keep a check's scope exactly matched to the one claim it
  verifies, and re-read the actual rendered result of a content edit
  before treating it as finished.

## Naming: two lanes, not one

- **Procedural skills** (the majority — a skill that performs or guides an action): gerund-verb-phrase, e.g. `extracting-game-phase-data`, `parsing-save-files`.
- **Knowledge/orientation skills** (background, context, vocabulary that inform other work rather than being an action themselves): descriptive noun phrase, e.g. `gameplay-loop-orientation`, `progression-system-overview`. Forcing these into gerund form produces a padded, performative name (`orienting-to-the-gameplay-loop`) — don't.

The test: if the honest answer to "what does this skill do" is a verb, gerund it. If the honest answer is "it's context," name it as what it is.

## Cross-skill routing belongs in the body, not the description

Don't put "do not use for X, see sibling-skill" clauses in a `description`. There's no evidence this pattern earns its keep, and good reason to think it doesn't: [the official best-practices doc](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) never uses it, its prescribed fix for selection ambiguity is "be specific and include key terms" (a positive-content fix, not a negation), and it states plainly that *all* installed skills' `name`+`description` are pre-loaded into the system prompt together, permanently, for every session — "the context window is a public good," every token there competes forever, whether or not the disambiguation it's buying ever actually mattered.

A redirect belongs inline, at the specific point in the body where the need for it actually arises — a step that hands off to a sibling skill's territory — not in a centralized summary near the top: an inline pointer earns its place by corresponding to a real step in the procedure; if no such step exists, the pointer doesn't belong in this skill's body at all — the sibling's own `description` is already enough for whoever's task actually needs it to find it. If a genuine selection-time misfire ever turns up — observed, not speculated, per [the best-practices doc](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)'s own evaluation-driven approach — fix it by sharpening the *positive* language in the `description` first.

## Forbidden: scaffolded trigger text

Never generate a "when to use" section by grammatically stuffing the skill's own name into a template sentence ("When deploying or configuring **extracting game phase data** capabilities..."). That says nothing and occupies the exact field Claude matches against for discovery. A skill with a stub trigger is worse than no skill — write the real answer or don't ship the skill yet.

## Write current fact, not session narrative

A skill's body should read as what's true right now — what to use, what
to avoid, and the specific reason a claim is trustworthy — not the story
of how it was discovered. Investigation narrative, corrected-mistake
retrospectives ("an earlier version of this claimed X; that was wrong"),
and the results of a specific validation run ("an agent tested this and
it worked") belong in the commit that made the change, not in the file
itself: a future maintainer reviewing history gets real value from that
context, while a consuming agent loading the skill gets none — it pays
the token cost on every load for information that helps it do nothing.
The test to apply: would removing a given sentence change what a
consuming agent does? If not, it belongs in the commit message instead.

## Custom frontmatter goes under `metadata:`

The [agentskills.io](https://agentskills.io/specification) open standard defines exactly six frontmatter fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. `claude plugin validate --strict` does not currently reject an unknown top-level key (verified — it passes silently), so this is a discipline to follow, not something the pre-PR check catches for you. Every skill here should set `license` (`CC-BY-SA-4.0` for a normal skill) — it's the one piece of licensing information that survives a skill directory being copied out of its plugin wrapper onto another platform; `REUSE.toml` only covers files that stay inside this repo. If a skill's own supporting files (`references/`, `scripts/`) need their own categorization beyond this, see [licensing-new-files](../licensing-new-files/SKILL.md). Anything else this system wants to track (game version, patch number, source-wiki link) nests under `metadata:` as an arbitrary string map, not as a new top-level key. Free to get right from the start; expensive to retrofit across many files later.

If a `metadata:` field is meant to be structured/machine-checked (an ID from an external taxonomy, a version range), CI must validate it against a canonical list, or it shouldn't be a structured field at all — an unvalidated structured field is worse than prose, because it looks machine-readable and gets trusted downstream without actually being checked.

## Bundle a script only when the skill actually needs one

Don't add `scripts/`/`references/` to a skill by default just because the format allows it. An unused or stub script sitting in a skill's directory drifts out of sync with the skill's own body over time and adds nothing a human or agent can act on — add supporting files only once the skill has a concrete, current reason for one.

## Audit before shipping

Once a skill's content is written or substantially changed, audit it
before it ships — a large content/data addition, a rewrite of an
existing skill's claims, or periodically for a skill that's accumulated
changes over time. Don't audit your own work from inside the same
context that wrote it: you already believe your own reasoning for why
each claim is true, so re-reading it yourself mostly re-confirms it
rather than checking it.

This is a **content-verification pass** — are the claims, data, and
prose in this skill trustworthy — not a check of the structural
conventions above (naming lane, frontmatter shape, scaffolded trigger
text, routing placement). Confirm those against this file's own sections
yourself before or alongside delegating; they're mechanical enough that
the author is already positioned to get them right while writing, unlike
factual/data trustworthiness, which benefits from independent distance.

Delegate to an independent reviewer instead — a fresh subagent with no
memory of this conversation is the usual way to get that independence,
but the requirement is independence from the reasoning that produced the
content, not any specific mechanism:

- Give it the target content and the primary source(s) to check it
  against, not your explanation of why the content is right.
- Point it at [auditing-domain-skills](../auditing-domain-skills/SKILL.md)
  as its full instructions — what to look for, the independent-
  verification stance to hold, and how to report back.

Act on what comes back per its stated verdict: treat **Confirmed wrong**
findings as blocking — fix before shipping. Treat **Suspected wrong**
findings as needing your own follow-up verification before deciding
either way, not as something to dismiss because the audit itself
couldn't fully confirm it. A report of "no issues found" is only as
strong as what the audit actually covered — check its stated scope
before treating it as a clean bill of health for the whole skill.

## A `SKILL.md`'s folder is the portable unit; the plugin around it isn't

A skill written to this spec is already loadable by any compatible agent platform (Claude Code, Copilot, Cursor, Codex CLI, Gemini CLI, and more) — but skills here live inside a plugin (`skills/<name>/SKILL.md` for a single-plugin domain, or `plugins/<subdomain>/skills/<name>/SKILL.md` once it's promoted to multiple), and the plugin/marketplace wrapper is Claude-Code-specific. A user on another platform consumes the skill directory directly (clone the repo, copy or symlink the folder out) rather than installing the plugin — some manual step, not zero, but the skill's own content needs no rewriting for that to work. Claude Code's own optional frontmatter extensions (e.g. `disable-model-invocation`) aren't part of the six-field spec; a skill using them is already off-spec for other platforms. Don't also maintain a separate, platform-specific instructions file (e.g. a `.github/copilot-instructions.md`) alongside this — a second file restating the same conventions for a different tool has nothing keeping it in sync with the `SKILL.md` it duplicates, and will drift from it. The shared `SKILL.md` format is what's meant to be maintained; write it once.
