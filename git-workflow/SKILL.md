---
name: git-workflow
description: 'Governs branches, Conventional Commits, and pull-request discipline — trunk-based flow, commit hygiene, and PR standards. Trigger with "write the commit message", "how should we branch", or "clean up this PR before review".'
---

# Git Workflow

## Purpose

Keep repository history readable and automation-friendly: trunk-based branches,
Conventional Commits that drive versioning and release notes (`ci-cd` consumes
them), and pull requests small enough to review honestly.

## When to Use / When NOT to Use

Use when:

- Committing changes ("write the commit message", "split this into commits").
- Opening, structuring, or cleaning up a pull request.
- Deciding branching strategy for a repo or a release train.

Do NOT use when:

- The commit content itself needs review — that is `code-quality/code-review`
  (this skill governs the shape of history, not the code in it).
- An incident fix must bypass normal flow — the emergency path in `incident-response`
  still uses Conventional Commits, just with expedited review.

## Prerequisites & Assumptions

- Trunk-based development: `main` is always releasable; branches live < 2 days;
  feature flags hide unfinished work.
- Conventional Commits types: `feat`, `fix`, `docs`, `refactor`, `test`,
  `chore`, `ci`, `perf`, `build`, `revert` — with optional scopes
  (`feat(orders):`).
- Semantic versioning is derived from commits by release automation (`ci-cd`).

## Step-by-Step Workflow

1. **Branch from main** — name `feat/<ticket>-short-slug`, `fix/<ticket>-slug`,
   or `chore/<slug>`; one logical change per branch.
2. **Commit in logical units** — each commit compiles and passes tests; message
   per the format below; split mixed changes (refactor vs feature) into separate
   commits.
3. **Open the PR early and small** — target ≤ 400 changed lines; description
   states what/why, test evidence, and risk; link the issue.
4. **Keep it green and current** — rebase onto main regularly; resolve conflicts
   as the author; never merge a red pipeline (`ci-cd` gates).
5. **Merge** — squash-merge for features (history reads as one logical change
   with the Conventional Commit title), merge commits only for release trains;
   delete the branch.
6. **Revert, don't bury** — a bad change is reverted with
   `revert: <original subject>`; history is never rewritten after push.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** use Conventional Commits:
  `<type>(<scope>): <imperative summary ≤72 chars>` + body explaining _why_ +
  `BREAKING CHANGE:` footer when APIs break; drives SemVer automation.
- **MUST** keep `main` releasable at all times; every commit on it passes the
  full gate.
- **MUST** squash-merge feature branches so history is one logical change.
- **MUST** keep PRs ≤ 400 changed lines (split with stacked PRs if larger) and
  short-lived (< 2 days).
- **SHOULD** write commit bodies for anything non-obvious: context, trade-offs,
  and the reason it is safe.
- **SHOULD** sign commits (`gpg`/`ssh` signing) where the org requires
  provenance.
- **MUST NOT** rewrite published history on shared branches.
- **MUST NOT** commit secrets, large binaries, or generated artifacts (use the
  artifact store and `security` secret rules).
- **MUST NOT** merge with unresolved review threads or bypass a failing gate.

## Examples

Good — Conventional Commit with body and breaking-change footer:

```text
feat(orders): make cancel idempotent

Clients retry cancels on flaky networks and were double-cancelling.
Cancel now accepts an Idempotency-Key header and returns the original
result for replays within 24h.

BREAKING CHANGE: Cancel without an Idempotency-Key returns 400.
```

Bad — the useless message:

```text
fixed stuff
```

## Checklist

- [ ] Branch named by type + ticket, branched from latest main.
- [ ] Each commit compiles, passes tests, and follows Conventional Commits.
- [ ] PR ≤ 400 changed lines, description has what/why/test evidence.
- [ ] Pipeline green; review threads resolved before merge.
- [ ] Squash-merge applied; branch deleted.
- [ ] Breaking changes carry a `BREAKING CHANGE:` footer and a version bump.

## Common Pitfalls

- **The 3,000-line PR** — unreviewable, ships defects; stack small PRs instead.
- **"WIP" branches aging into cheese** — weeks-old branches full of conflicts;
  branch < 2 days and flag unfinished work.
- **Merge-commit soup** — interleaving merge commits on feature branches; rebase
  locally, squash on merge.
- **`git push --force` on shared branches** — destroys teammates' work; force
  only on your own unmerged branch, with `--force-with-lease`.

## References

- Conventional Commits: https://www.conventionalcommits.org/
- Semantic Versioning: https://semver.org/
- Trunk-Based Development: https://trunkbaseddevelopment.com/
- GitHub — squashing commits: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges
