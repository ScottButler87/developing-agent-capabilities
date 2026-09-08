---
name: structuring-domain-repos
license: CC-BY-SA-4.0
description: Structures and publishes git repos of Claude Code skills — one repo per domain, one plugin per subdomain, plugin.json and marketplace.json layout, plugins/ subdirectories, cross-plugin dependencies, and discovery via a self-hosted or Anthropic's community marketplace. Use when creating a repo for a new domain (e.g. a new game), splitting a repo into multiple plugins, wiring up plugin.json or marketplace.json, or deciding how a plugin should be installable by others.
---

# Structuring domain repos

## The model

- **Domain = one git repo, deliberately.** A distinct subject (a specific game, a specific project area) gets its own repo, because independent community ownership requires it: git has no sub-repo permission boundary, so "the Satisfactory community governs Satisfactory knowledge, with no authority over Doom Eternal knowledge" can only be expressed as separate repos. It also bounds blast radius — plugins execute arbitrary code with the installing user's privileges, so a contributor trusted in one domain's repo has no reach into another's.
- **Subdomain = one plugin.** A coherent slice of a domain (e.g. "game knowledge," "mod development," "data extraction" within a Satisfactory domain) is one plugin. Multiple subdomains in one domain are organized under a self-hosted `marketplace.json` at the repo root, each subdomain in its own `plugins/<name>/` — or, without moving any files, as several marketplace entries that all share `"source": "./"` and cherry-pick their own `skills` subdirectories out of one shared `skills/` folder. The `plugins/` layout is tidier for more than a couple of subdomains; the shared-root form avoids a promotion/rename step for two.
- **Skill = one focused capability**, at `skills/<name>/SKILL.md` inside the subdomain plugin it belongs to.
- **Git is the source of truth; author local-first, push once developed** — commit as you go, push to the public remote once a skill actually works. Run `claude plugin validate .` before the first commit.

## Cross-subdomain sharing: don't duplicate

If a skill turns out to be genuinely needed by more than one subdomain, don't copy it into both. Two ways to avoid that:

- **Symlink** a plugin's own `skills/<name>` entry to the canonical copy living in a sibling plugin. Claude Code dereferences it at packaging time — no third plugin, no marketplace dependency, no versioning. Reasonable while a domain repo is solo-maintained; reconsider once other contributors are involved, since a symlink is an invisible coupling — someone editing `plugins/subdomain-a/skills/foo` may not realize they're also changing `subdomain-b`.
- **Extract** it into its own small standalone plugin and have each subdomain that needs it declare it as an unversioned `dependencies` entry, instead of placing it in either one — `dependencies` only resolves at plugin granularity, not per-skill. The coupling is explicit and reviewable in a diff, which matters more once a domain has multiple contributors. Extract *reactively*, only once a real second use case exists, not speculatively — this is about deduplicating one skill's *content* across sibling subdomains, a different decision from whether a documentation topic needs its own skill file (see [placing-new-skills](../placing-new-skills/SKILL.md) for that test). Not every plugin in a domain is strictly a subdomain as a result; an extracted shared plugin is a legitimate exception to that.

This applies **within one domain only** — extracted or symlinked plugins are shared by sibling subdomains in the same repo/marketplace. Sharing a skill *across* domains (different repos) needs cross-marketplace dependencies (`allowCrossMarketplaceDependenciesOn`), and is deliberately out of scope by default:

- The allowlist lives on the *installing* domain's own `marketplace.json`, so depending on another community's plugin is an explicit, reviewable trust declaration made by the community that bears the risk — good, don't shortcut it.
- An unresolved cross-marketplace dependency leaves an installer stuck adding a second marketplace by hand, real friction for something meant to be an easily-consumed nugget of context.
- Before reaching for a cross-domain dependency at all, consider whether the shared capability is better off as its own domain — a standalone, independently-useful repo either domain can install on its own, no dependency edge required. Publishing a standalone plugin, rather than declaring a dependency edge, is generally how the ecosystem handles shared capability across independent publishers.

Extraction (within one domain) needs a `dependencies` entry to resolve through a marketplace — but that marketplace doesn't need to be published. `/plugin marketplace add ./path/to/repo` works against a local, unpublished folder, enough to make a same-repo dependency resolve. Only making the repo public is the decision that needs the stop-and-ask below — adding a marketplace purely so a local dependency resolves doesn't.

Leave dependency versions unconstrained (a bare plugin name) until an actual compatibility break gives a concrete reason to add a semver range and start tagging releases with `claude plugin tag`.

## Bootstrapping and growing a domain repo

Domains and subdomains are never created in advance — a new one exists only once new knowledge needs to be persisted and genuinely doesn't fit any existing domain or subdomain, including one someone else already maintains (see [placing-new-skills](../placing-new-skills/SKILL.md) for that decision, including how partitioning is expected to evolve over time).

A domain repo's shape is governed by two independent axes:

- **Plugin count.** One subdomain → a single plugin at the repo root. Two or more → each subdomain moves into its own `plugins/<name>/`, and `marketplace.json` becomes the only way to list more than one plugin.
- **Discoverability**, independent of plugin count — see "Discovery postures" below. Any public repo wants `marketplace.json` regardless of how many plugins it has.

**A brand-new domain starts minimal:**
```
<domain>/
  .claude-plugin/
    plugin.json
  skills/
    <skill-name>/
      SKILL.md
  LICENSES/
    AGPL-3.0-or-later.txt
    CC-BY-SA-4.0.txt
  REUSE.toml
  README.md
```
Minimal `plugin.json`:
```json
{
  "name": "<domain>",
  "description": "<what this plugin's skills cover>",
  "version": "0.1.0",
  "license": "AGPL-3.0-or-later AND CC-BY-SA-4.0"
}
```
Default license split: code under AGPL-3.0-or-later, skill/documentation prose under CC-BY-SA-4.0 — two different licenses because a domain repo genuinely holds two different kinds of contribution. AGPL's network clause matters specifically because this is tooling meant to be run by AI agents: it stops someone hosting a modified version of any bundled script or server behind a remote service (an MCP server, a bot) without sharing their changes back — note this only covers code actually licensed AGPL, not the skill content itself. CC-BY-SA's share-alike clause keeps the domain knowledge in the commons: anyone who redistributes or adapts it has to keep their version open too, the same mechanism that makes a community-PR-governed domain repo hold together as contributors join. Declared per-file with [REUSE](https://reuse.software/)'s `REUSE.toml` rather than a single blanket `LICENSE`, since a domain repo mixes both kinds of file. A domain repo meant to invite outside contribution isn't practically forkable or PR-able without a license — include one from the start.

**If any subdomain will synthesize skills from a licensed third-party source** (a copyleft doc site, a wiki with its own terms — see
[orchestrating-large-scale-skill-extraction](../orchestrating-large-scale-skill-extraction/SKILL.md)'s
"decide the attribution/licensing posture up front" for when this applies), decide that on day one, not after the first batch of skills exists: those skills' `REUSE.toml` annotation won't be the plain default above, it'll be a combined expression (e.g. `GPL-3.0-or-later AND CC-BY-SA-4.0`), and each such skill's own frontmatter `license:` field has to carry that same combined expression to survive being copied out of the repo. Don't hand-type that second copy — see [licensing-new-files](../licensing-new-files/SKILL.md)'s `sync-skill-license.py` (agent-facing, run against a skill after drafting it) and its sibling `audit-skill-licensing.py` (CI-facing, read-only), which both derive the frontmatter check from `REUSE.toml` instead. This was reinvented once already (found only after ~80 skills had already drifted from their own `REUSE.toml` entries); wire `audit-skill-licensing.py` into CI alongside `reuse lint` from the first skill that needs a non-default license, not retroactively.

**Promoting to multiple subdomains** moves the existing plugin's content into `plugins/<first-subdomain>/` and adds the new subdomain alongside it:
```
<domain>/
  .claude-plugin/
    marketplace.json
  plugins/
    <subdomain-a>/
      .claude-plugin/
        plugin.json
      skills/...
    <subdomain-b>/
      .claude-plugin/
        plugin.json
      skills/...
  LICENSES/
    AGPL-3.0-or-later.txt
    CC-BY-SA-4.0.txt
  REUSE.toml
  README.md
```
```json
{
  "name": "<domain>",
  "owner": { "name": "..." },
  "plugins": [
    { "name": "<subdomain-a>", "source": "./plugins/<subdomain-a>" },
    { "name": "<subdomain-b>", "source": "./plugins/<subdomain-b>" }
  ]
}
```
A marketplace entry's `name` is independent of both the directory and `plugin.json`'s own `name` field, so moving files into `plugins/` doesn't force a rename — keep the first entry named `<domain>` if anyone already installed it that way. If an entry's name is deliberately changed later and others already installed from it, add that change to `renames` so they migrate instead of hitting a not-found error; `renames` is append-only.

**Before making the repo public: stop and ask the user how they want *this specific repo's* discovery handled.** Present the postures below explicitly — this is a per-repo decision, not global, and isn't one-time. Committing and pushing to a private remote isn't itself a discovery decision.

## Discovery postures to present

`marketplace.json` is a hard prerequisite for `/plugin marketplace add <owner>/<repo>` — without it, a user has to clone the repo or use `--plugin-dir` no matter how they found it. So any public posture ships `marketplace.json`; the postures differ only in how actively the repo is promoted:

- **Deferred** — private, or not yet meant for anyone else. No `marketplace.json`. Still fully usable by the maintainer via a skills-directory symlink (persistent, no marketplace) or `--plugin-dir` (one-off) — see the README. Fits a personal or meta-scoped repo.
- **Published** — public, `marketplace.json` present, install commands documented:
  ```
  /plugin marketplace add <owner>/<repo>
  /plugin install <plugin-name>@<marketplace-name>
  ```
  `<marketplace-name>` is `marketplace.json`'s own `name` field, not `<owner>/<repo>` — the two commands use different identifiers on purpose. Cross-linking it from wherever the user keeps an index of domain repos is a promotion choice within this posture, not a separate posture.
- **Community submission** — additionally submit to Anthropic's community marketplace (`platform.claude.com/plugins/submit`) once stable. Requires `claude plugin validate --strict .` to pass first; pins the plugin to a commit SHA in `anthropics/claude-plugins-community`, auto-bumped on push; install afterward with `/plugin install <plugin-name>@claude-community`.

## Community-ready additions

A few pieces earn their cost quickly once a repo accepts outside contributions — cheap now, expensive to retrofit once contributors exist:

- **CONTRIBUTING.md**: point at the `developing-agent-capabilities` meta-plugin for anything generic (skill-authoring/placement/licensing conventions — the actual steps live there, not copied in here) rather than repeating it. Every session already has those skills loaded if the plugin's installed at user scope, so there's nothing to keep in sync; once that repo has a public URL, the same pointer works for human contributors who don't have it installed. Keep this file to what's genuinely specific to this domain, or an explicit exception to a general rule ("unlike the general convention, this repo..."). Don't publish a review-time commitment (e.g. "reviewed within 48 hours") a solo or small maintainer can't reliably hold — state responsiveness as an aspiration or omit it; a missed public commitment costs more contributor trust than none.
- **SECURITY.md** with an explicit in-scope list (skills containing commands/scripts that could cause unintended harm, sensitive data accidentally included) and a private-reporting path — relevant given plugins execute arbitrary code.
- **GitHub issue forms** (`.yml`, not `.md`) with closed dropdowns for category/type and `blank_issues_enabled: false`. Front-loads the taxonomy decision onto the contributor at filing time. Needs an actual GitHub repo to mean anything — add once one exists, not before.
- **CI on every PR**: validate frontmatter, reject duplicate skill names, post a per-subdomain skill count in the job summary, and run `reuse lint` — see [licensing-new-files](../licensing-new-files/SKILL.md) for what a failure means and how to fix it. If the repo has any skill on a non-default license (see above), also run `audit-skill-licensing.py` (read-only, whole-repo by default) so a skill's frontmatter can't merge out of sync with its own `REUSE.toml` entry. Add this on the first PR accepted from anyone, not before.
- **Version sync on release**: once versioning starts (per the deferral above), wire a release-triggered workflow that patches `version` in both `plugin.json` and `marketplace.json` from the git tag — version drift between a tag and two JSON files is a real, recurring bug once a repo has more than one plugin to keep in sync.
- **Don't hand-maintain content that duplicates a canonical source** — a skill roster in README prose, a coverage table restating what the skills themselves already say. It drifts the moment either copy changes without the other, and generating it with a script just relocates the same problem into brittle find-and-replace logic. Point at the canonical source instead of re-summarizing it; only automate a sync, like the version-sync above, when both copies are structurally required to exist independently.
- **Don't name a domain repo as if it's officially affiliated with the subject** (e.g. not `Satisfactory-Skills` reading as endorsed by the game's studio). Prefix with a handle or an explicit community marker, and put a "not affiliated with X" line in the README — trademark friction shows up exactly here.
