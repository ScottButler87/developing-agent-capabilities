---
name: auditing-domain-skills
license: CC-BY-SA-4.0
description: A catalog of failure modes that make it into domain-knowledge skills — unverified claims, unvalidated heuristics, silent-failure decoders and invariants, stale snapshot statistics, narrative residue, quietly narrowed rules, instance-only fixes, scope creep inside verification checks, uncorrected mechanical edit errors, unverified tooling-capability claims, cross-skill contradictions between two skills that each check out individually, and completeness claims that under-report real coverage — plus the mindset for checking a skill against them and a standardized, actionable report format. Use whenever a domain skill's reference docs, scripts, or canonical data need a quality check, whether that's a one-off review, a repeated audit pass, or an independent-agent step another procedure delegates to.
---

# Auditing domain skills

## Stance

Treat every claim in the target content as unverified until
independently re-derived from its primary source — including any
explanation of *why* a claim is correct, if one is given alongside it.
This holds regardless of how much context you have on how the content
was produced: familiarity with the reasoning behind a claim is not the
same as having checked the claim, and shouldn't substitute for it.

Independently re-derive every checkable claim — field presence, record
counts, cross-reference/join resolution, decoded values, a script's
actual output — directly from the primary source (raw data, the actual
running tool, the actual codebase) rather than trusting the content's
own description of what's there. A claim you didn't personally
re-derive is a claim you haven't audited.

Not every line needs individual checking. Prioritize claims that are
checkable against a primary source at all (a number, a field name, a
cross-reference, a tool's claimed output) over prose that's inherently a
judgment call.

When the target content's own primary source is itself rendered
documentation for a live, evolving system, and a deeper ground truth
also exists — the actual source code, a running instance of the tool,
an API you can call — check against that deeper source rather than
stopping at "this matches what the docs say." Rendered docs go stale in
ways their own authors don't always catch; re-reading them more
carefully doesn't surface a case where the docs themselves are wrong.
Content faithfully transcribed from a wrong doc page is still wrong.

## Failure modes

Each entry states the fix and, more importantly, *why* it matters — the
"why" is what lets an audit extend this list to a case that doesn't
match any entry literally, and decide an ambiguous case by the same
reasoning the author should have used.

### Unverified factual claims

A specific fact — a field name, a value, a relationship — gets written
into a doc without anyone actually checking it against the primary
source at the time of writing. It's often anchored to something
genuinely true about the domain (a real mechanic, a plausible-sounding
name), which is exactly what makes it convincing rather than obviously
wrong.

- **Fix:** trace every specific, checkable claim back to an actual
  primary-source lookup before it goes in. "This is the kind of thing
  that would be true" is not verification.
- **Why it matters:** the doc is the thing a future reader — human or
  agent — takes as ground truth. Nothing about how an unverified claim
  reads distinguishes it from a verified one; the writer's discipline is
  the only thing protecting that trust.

### Unverified capability claims about tooling

A doc asserts that a script or tool computes or reports something
specific, without anyone confirming the actual implementation does
that — as opposed to something adjacent or similar-sounding.

- **Fix:** before writing "run X for the current value of Y," actually
  run X and confirm Y is what comes out. Don't infer a tool's capability
  from its name, its docstring, or its neighborhood in the file.
- **Why it matters:** a false capability claim is worse than no pointer
  at all — it costs whoever follows it a wasted round-trip before they
  discover the doc was wrong, and they may not think to question it a
  second time in the same session.

### Convenience-driven exceptions to a stated rule

An established scoping or inclusion rule gets quietly narrowed for
expedience ("there are a lot of these," "this is taking a while") rather
than because the exception is actually justified by the rule's own
reasoning.

- **Fix:** any deviation from a stated principle needs its own
  justification traceable to that principle's actual rationale, not to
  convenience. When unsure, apply the rule as stated and flag the
  tension rather than silently special-casing.
- **Why it matters:** an undocumented exception erodes the rule itself —
  the next person can't tell whether an exclusion was principled or just
  easier, so they can't safely extend the rule to a new case either.

### Unvalidated heuristics shipped as ground truth

A derived value — a naming-convention guess, a pattern-based
inference — gets presented with the same confidence as
directly-observed data, without confirming it actually holds across the
dataset it's applied to.

- **Fix:** validate a heuristic against independent evidence before
  trusting its output (a second, unrelated relationship that should
  agree with it). Where it can't be validated for a given case, omit the
  value rather than guess, and fail loudly — a warning, an error —
  instead of silently emitting a wrong-but-plausible answer.
- **Why it matters:** a heuristic that's right most of the time is
  indistinguishable, at the point of use, from one that's always right —
  until someone hits the exception, having already been fed a wrong
  answer with no signal anything was uncertain.

### Decoders applied without confirming the actual shape

A general-purpose parsing routine gets used against a field whose real
raw encoding doesn't match what that parser assumes, producing an empty
or default result that looks like legitimate data rather than an error.

- **Fix:** sample a field's actual raw value before picking how to
  decode it. Prefer parsing logic that raises on a shape it doesn't
  recognize over logic that silently defaults.
- **Why it matters:** a silently-wrong empty result is worse than a
  crash — it reads as "this field is just usually blank" rather than
  "the code is broken," so it survives far longer before anyone
  questions it.

### Invariants that live only in prose

A doc states a guarantee — "these two things never collide," "every X
has a Y" — that nothing in the actual code checks, so a future change to
the underlying data could quietly violate it with no signal at all.

- **Fix:** wherever a prose invariant is claimed, back it with an
  explicit runtime check that raises if it's ever violated, instead of
  leaving the guarantee to live only as a documentation claim.
- **Why it matters:** a prose-only invariant rots silently — the doc
  keeps asserting something long after it's stopped being true, and
  nothing about the doc's presentation signals that it was ever anything
  other than a checked fact.

### Stale snapshots presented as durable facts

A count, percentage, or "N of M" figure computed once gets written into
prose as if fixed, when it's actually a live property of the underlying
data that will drift as that data changes.

- **Fix:** replace the bare number with a pointer to whatever recomputes
  it live. Reserve literal numbers in prose for things that are
  genuinely fixed — constants, specific named examples — not for
  anything describing how much or how many of a changeable dataset.
- **Why it matters:** a stale number is worse than no number: it reads
  as confidently correct, and nothing about its presentation signals it
  might have already drifted.

### Narrative residue in durable content

Investigation process, discovery narrative, or a self-referential
comment calibrated to something that's since been removed (a warning
about a number that's no longer there) is left behind in content meant
to be read as current, standalone fact.

- **Fix:** durable content states current fact only — what's true, what
  to use, why it's trustworthy. Session and investigation narrative
  belongs in the commit message, where a maintainer reviewing history
  can actually use it.
- **Why it matters:** narrative costs every consuming reader the same
  tokens/attention on every load for zero benefit, and a dangling
  self-reference (a warning with nothing left to warn about) actively
  confuses a reader who has no session context to resolve it against.

### Fixing the instance instead of the pattern

When corrected on one specific wrong value, the fix replaces it with a
corrected-but-still-hardcoded value — addressing that one instance
without recognizing that asserting a hardcoded value at all was the
actual defect.

- **Fix:** when a correction arrives, ask what class of mistake it
  belongs to before applying a fix, not just what the right value is
  here. A correction is a symptom of a rule violation; fix the rule, not
  just the symptom in front of you.
- **Why it matters:** fixing only the visible instance guarantees the
  same mistake resurfaces elsewhere in the same content, or the next
  time content is added — the entire value of noticing a pattern is not
  paying for it repeatedly.

### Scope creep inside a verification check

A check written to validate one specific, narrowly-scoped claim silently
grows to cover more than it was meant to, corrupting the count or result
it reports and potentially misattributing a finding to the wrong place.

- **Fix:** keep a check's scope exactly matched to the specific claim it
  verifies. If two related-but-distinct things get bundled into one
  check, split them rather than merging.
- **Why it matters:** a verification tool is only as trustworthy as its
  own scoping discipline — once the checker itself drifts, it stops
  being a source of truth and starts manufacturing new errors that are
  harder to notice, because its output still looks like a legitimate
  finding.

### Mechanical edit errors not re-verified

A text edit — merging two sentences, restructuring a paragraph — leaves
behind a structural defect (an unbalanced parenthesis, a dangling
reference) that goes uncaught because the edit tool succeeding gets
mistaken for the edit being correct.

- **Fix:** re-read the actual rendered result of any non-trivial content
  edit before considering it finished. A tool reporting success only
  means the string replacement happened, not that the resulting content
  is coherent.
- **Why it matters:** this failure mode is purely mechanical and easy to
  introduce even when the substantive content is right — it's cheap to
  catch by re-reading and expensive to leave for a reader to trip over.

### Cross-skill contradiction

Two skills each check out fine individually against their own primary
source, yet assert incompatible mechanisms for a fact they both touch —
e.g. one skill's "the file isn't included in the package without step
X" versus a sibling it cross-references having already established,
with deeper verification, that the file is included either way and X
changes a different property of it. Single-skill fact-checking doesn't
surface this, because each half is independently true-to-its-own-source
in isolation; only comparing the two claims against each other does.

- **Fix:** whenever a skill cross-references a sibling for a mechanism
  rather than restating it, open that sibling and check its actual
  claim about the shared fact, not just that the link target resolves.
  Where the two disagree, trust whichever has the stronger verification
  (checked against source code, not just rendered docs; checked more
  recently; checked more specifically) and correct the other to match.
- **Why it matters:** cross-referencing instead of duplicating is the
  right instinct for avoiding drift, but it only works if the two ends
  of the reference actually agree — an unnoticed contradiction is worse
  than duplication, because a reader has no way to tell which of two
  disagreeing skills to trust, and the cross-reference itself implies
  they were checked against each other when they weren't.

### Completeness claims not matching actual coverage

A skill's own scope statement ("what this doc-tree section covers and
doesn't") silently under-reports real, on-topic material that exists
and is simply out of that skill's own scope — handled elsewhere, or
just missed. Fact-checking the claims that *are* present doesn't catch
this, because the gap is in what's absent from the claim, not in
anything stated incorrectly.

- **Fix:** independently walk the actual source structure the skill
  claims to summarize (a live nav tree, a directory listing, a table of
  contents) and diff it against the skill's own completeness claim,
  rather than only verifying each individual fact the skill does state.
- **Why it matters:** a reader relying on a skill's stated scope to
  decide whether they need to look further has no way to detect a
  silent gap themselves — that's exactly what the completeness claim
  was supposed to save them from checking.

## Writing the report

Structure findings so whoever receives the report can act without
re-deriving the work. For each finding:

- **Location** — file and line/section, precise enough to act on without
  re-searching.
- **Failure mode** — name the closest match from the catalog above, or
  describe the pattern in one line if none fit; new patterns are
  expected, not a sign the catalog was applied wrong.
- **Verdict** — **Confirmed wrong** (independently verified incorrect)
  or **Suspected wrong** (matches a failure mode but couldn't be fully
  verified against a primary source).
- **Claim vs. reality** — what the content currently asserts, and what
  checking the primary source actually found (or why it's suspect, for
  a Suspected finding).
- **Concrete failure scenario** — what a reader (human or agent)
  following this content would get wrong as a result, stated
  specifically — not "this is inaccurate" but what decision or output it
  would corrupt, and how.
- **Suggested fix** — one line, actionable.

Rank findings most-severe-first. After the findings, list what was
positively spot-checked and found correct — this tells the reader what
scope the audit actually covered, which matters because a clean report
is only as strong as what was checked. Give each entry a shape parallel
to a finding but without the failure-specific fields: **Location**,
**Claim** (what was checked), and **How it was checked** (against which
primary source). "No issues found in the scope checked" is a complete,
useful outcome on its own — don't manufacture findings to look thorough,
and don't pad this list with restated praise beyond what was actually
verified.
