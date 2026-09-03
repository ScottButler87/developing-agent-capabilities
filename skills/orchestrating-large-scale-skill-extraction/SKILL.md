---
name: orchestrating-large-scale-skill-extraction
license: CC-BY-SA-4.0
description: Running a fan-out/fan-in pipeline that turns one large documentation source (a whole doc site or doc-tree section) into many small skills -- clustering pages into skill-sized units before any drafting, batching parallel draft-and-audit agents, and the specific operational gotchas (spend-limit interruptions, a validation command's exit code getting masked by a pipe, a recurring frontmatter bug, cross-skill contradictions an audit needs to actively look for) that only surface at this scale. Use when a single source is large enough that one skill per source page would produce dozens of skills, and the boundaries between skills aren't obvious from the source's own table of contents.
metadata:
  derived-from-session: "satisfactory-agent-capabilities modding plugin, 2026-09, ~40 skills from docs.ficsit.app"
---

# Orchestrating large-scale skill extraction

This is about the *process* of turning one large source into many skills,
not about what makes an individual `SKILL.md` good -- see
[authoring-domain-skills](../authoring-domain-skills/SKILL.md) and
[auditing-domain-skills](../auditing-domain-skills/SKILL.md) for that.
This skill is for the layer above: how to partition the source, how to
run dozens of drafting/auditing agents without losing track of any of
them, and the specific failure modes that only show up once the scale
passes "a handful of skills."

## Cluster before drafting, and do the clustering itself as fan-out/fan-in

Don't map source pages to skills 1:1, and don't decide the skill
boundaries yourself by skimming a table of contents -- a doc site's own
folder structure is not the same thing as where an agent's task actually
needs to land, and a single page can span multiple genuinely distinct
entry points (or several thin pages can be one entry point). Run the
clustering itself as a fan-out/fan-in pass, symmetric with the drafting
pass that follows it:

1. **Fan out**: split the source into balanced slices (by folder, by
   page count, whatever's convenient) and give each slice to a separate
   agent whose only job is to propose skill boundaries *within its
   slice* -- explicitly tell it to test boundaries by entry point
   (concrete task/situation), not by topic-label similarity, and to flag
   (not silently resolve) anything that looks like it belongs with
   content outside its own slice.
2. **Fan in**: with full context of every slice's proposal at once,
   reconcile them yourself (or in a dedicated consolidation pass) rather
   than shipping each slice's proposal independently. This is the step
   that catches fragmentation no single fan-out agent could see: in one
   run, two agents working on completely different parts of the doc tree
   each independently proposed folding the *same* underlying "which
   implementation approach" content into a new skill -- from two
   different source pages that used different words for the same
   decision. Neither agent could have caught this alone; only a pass
   with visibility into both proposals could.
3. **Checkpoint before spending the drafting budget.** Present the
   consolidated map to whoever's directing the work, and name the
   non-obvious judgment calls explicitly (merges, drops, boundary calls
   that could reasonably go the other way) rather than only the final
   count. Drafting and auditing dozens of skills is the expensive part
   of this pipeline; a wrong cluster boundary caught before that starts
   costs one conversation turn, caught after costs a rewrite.

## The per-skill pipeline: draft, then an independently-derived audit, then fix, then commit

For each skill in the consolidated map:

1. **A drafting agent writes the skill**, fetching the primary source
   itself (don't hand it pre-summarized text if you can avoid it -- see
   below) and grounding every claim in what it actually reads. Tell it
   explicitly **not** to audit its own work and **not** to commit --
   both are a separate step, by a separate actor.
2. **A fresh audit agent, with no memory of the drafting conversation,**
   re-fetches the same primary source independently and checks the
   draft's claims against it -- per
   [auditing-domain-skills](../auditing-domain-skills/SKILL.md). The
   independence is the entire point: an agent re-reading its own recent
   reasoning mostly re-confirms it, because it already believes its own
   reasoning was sound. A genuinely fresh agent has no such bias.
3. **The orchestrator (not the drafting or auditing agent) applies the
   audit's findings and commits.** This keeps a human-legible record of
   what was found and fixed in the commit message, and stops an agent
   from silently absorbing a correction it wrote for itself into a
   commit whose message no longer says why the change was made.

Batch this in groups of roughly five agents running in parallel per
wave. That's large enough to make real throughput progress, and small
enough that: one spend-limit interruption (see below) doesn't stall the
whole pipeline waiting on a resume, and the orchestrator can actually
track and react to each individual result rather than losing the thread
across twenty simultaneous notifications.

## Point verification at ground truth beyond the rendered docs, when it exists

Rendered documentation for a live, evolving system goes stale in ways
the docs' own authors don't always catch. If an independently-checkable
ground truth exists -- a local source-code checkout, a running tool, an
API you can actually call -- tell drafting and auditing agents
explicitly that it exists and when to reach for it, rather than assuming
prose-vs-prose comparison is the ceiling of what's checkable. Checking
claims against an actual local source checkout (not just the rendered
docs site) can surface real defects invisible to prose-vs-prose
comparison: a documented C++ macro name that didn't exist in the actual
header (the *official docs* had it wrong, not just the drafted skill),
a draft's own claim about a function's behavior reversed after tracing
an actual fall-through code path the docs never mentioned, and a
struct's real field list differing from what the docs page enumerated.
None of these would have surfaced from re-reading the doc page more
carefully, because the doc page itself was the thing that was wrong.

## Failure modes specific to this scale

These either don't come up at all when writing one or two skills by
hand, or are too rare there to be worth a standing warning -- at dozens
of skills drafted across many agent turns, each of these recurred enough
to be worth naming explicitly.

- **A validation command piped into something else silently loses its
  own exit code.** `some_validate_command | tail -20 && git commit ...`
  gates the commit on `tail`'s exit status, not the validator's -- `tail`
  almost always succeeds even when the thing it's displaying failed, so
  a broken commit can slip through this kind of gate undetected. Run the
  validation step un-piped, or capture and check `$?` immediately after
  it, before letting anything gate a commit on its result.
- **An unquoted colon-followed-by-a-space inside a YAML frontmatter
  string breaks the parse, and it's easy to reintroduce.** A `description:`
  field written as free-flowing prose will eventually contain "word:
  word" somewhere in the sentence, which YAML reads as a nested mapping
  key rather than plain text -- the frontmatter fails to parse and the
  skill silently loads with none of its metadata at runtime. This isn't
  a one-time mistake to fix and forget: the same skill directory can trip
  it more than once, including from the very fix meant to correct the
  first occurrence. Treat every
  frontmatter edit as a candidate for this bug, not just the first draft
  -- a strict validator (this repo's convention is
  `claude plugin validate --strict`) catches it, but only if actually
  run, un-piped, after *every* edit to a `description` field, not just
  after the initial draft.
- **Two skills can each check out fine individually and still
  contradict each other.** Single-skill fact-checking (is this claim
  true against the source?) doesn't catch two skills asserting
  incompatible mechanisms for a fact they both touch -- e.g. one skill
  claiming a file "isn't included in the package without step X" while
  a sibling it cross-references had already established (via deeper
  verification) that the file *is* included either way, and step X
  changes a different property of it. When a skill cross-references a
  sibling for a mechanism, explicitly instruct its auditor to open that
  sibling and check for exactly this, not just to confirm the link
  target resolves.
- **A skill's own completeness claim needs the same scrutiny as its
  factual claims, and isn't caught by checking the claims that are
  there.** A scope statement like "here's what this doc-tree section
  covers" can silently under-report real sibling pages that exist and
  are simply out of this particular skill's scope -- nothing about
  fact-checking the content that *is* present catches a hole in what's
  claimed to have been surveyed. An auditor needs to independently walk
  the actual source (a live nav tree, a directory listing) and diff it
  against the skill's own completeness claim, not just verify each
  individual fact in isolation.
- **A background agent's own resumability is the resume path for a
  spend-limit interruption, not a fresh restart.** When an agent's task
  notification reports an API spend-limit error mid-task, its own
  transcript already holds whatever partial work it did -- send it a
  short "you were interrupted, not failed; the limit should be reset
  now, please continue" message addressed to its own agent id/name
  rather than launching a brand-new agent with the same prompt,
  which redoes completed work and burns more of the same limit that
  just tripped. No need to poll for the reset window; the interruption
  message states when it resets, and sending the resume message after
  that point just works.

## Decide the attribution/licensing posture up front, not as a final cleanup pass

If the source carries its own license (a copyleft documentation site, a
third-party wiki), decide before drafting starts -- not after 40 skills
already exist -- what attribution each derived skill needs and how the
repo's own license metadata should reflect it. See
[licensing-new-files](../licensing-new-files/SKILL.md) for the general
per-file categorization mechanics; the specific wrinkle here is that
retrofitting accurate per-file source attribution across dozens of
already-written skills means reconstructing which source page(s) each
one actually drew from after the fact, which is far more error-prone
and expensive than recording it as each skill is drafted. If a
clustering map already exists (see above), it's the natural place to
carry the source-page mapping forward into the drafting step.

## Preserve the clustering artifacts and audit findings somewhere durable

A session's scratchpad directory doesn't survive past that session. The
consolidated cluster map is a genuinely useful project-tracking record
on its own -- what's covered, what's deliberately deferred, why a
boundary was drawn where it was -- and is worth committing into the
target repo (even as a plain markdown file, not a skill itself) if the
extraction spans more than one sitting or might need a retrospective
later. The same applies to audit findings: they exist only in whichever
conversation produced them unless something explicitly persists them.
If a later retrospective, a written-up set of lessons, or a compliance
audit trail is a plausible future need, save each audit's findings to a
file as it comes back rather than relying on conversational memory
staying intact and in-context indefinitely.
