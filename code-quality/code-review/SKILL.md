---
name: code-review
description: 'Performs an enterprise-grade pull-request review covering correctness, security, design, tests, and maintainability with severity-graded findings. Trigger with phrases like "review this PR", "review these changes before merge", or "is this diff ready to ship".'
---

# Code Review

## Purpose

Produce a consistent, evidence-based review verdict for a pull request or diff. The skill
replaces ad-hoc "looks good to me" reviews with a repeatable pass that classifies every
finding by severity, verifies the tests actually exercise the change, and blocks merges
that violate repository standards.

## When to Use / When NOT to Use

Use when:

- A reviewer is asked to "review this PR", "check this diff", or "approve before merge".
- A pre-merge audit is requested for a hotfix or release branch.
- A review is disputed and a second, standards-based opinion is needed.

Do NOT use when:

- The request is a full refactor or rewrite — use `code-quality/refactoring` instead.
- The request is a security-only audit — use `security` for the CWE-mapped process.
- The code cannot be built or tested at all; fix that first.

## Prerequisites & Assumptions

- The diff is available (PR URL, `git diff`, or pasted changes) and builds.
- CI status is visible or reproducible locally (`make check`, test command from README).
- Language-specific rules come from `language-specific/golang`, `language-specific/java`,
  or `language-specific/python`; commit/branch rules come from `git-workflow`.

## Step-by-Step Workflow

1. **Context** — read the PR description, linked issue, and the diff. Restate in one
   sentence what the change claims to do. If you cannot, the PR description fails review.
2. **Automated gates first** — confirm lint, tests, and SAST pass. Never review style
   findings a linter already catches; report them once and point to `static-analysis`.
3. **Correctness pass** — trace the happy path and every error branch. Classify defects
   with the defect taxonomy below.
4. **Design pass** — check boundaries, dependencies, and whether the change follows the
   existing architecture. Flag new abstractions that duplicate existing ones.
5. **Test pass** — verify new logic has tests that fail without the change; check error
   paths, not just happy paths. Coverage policy lives in `testing/test-coverage`.
6. **Security pass** — apply the fast checks from `security` (input validation, secrets,
   authz). Deep audits are out of scope for a normal review.
7. **Verdict** — post findings with severity and rationale, then Approve, Request
   Changes, or Block. Every Blocker or Major finding must have a concrete fix suggestion.

### Defect taxonomy (from the legacy audit skill)

| Category       | Examples                                                          |
| -------------- | ----------------------------------------------------------------- |
| Business logic | Off-by-one, wrong operator, violated invariant, silent truncation |
| Concurrency    | Data race, goroutine/executor leak, deadlock, wrong lock scope    |
| Error handling | Swallowed errors, broken error chains, panic on nil               |
| Resources      | Leaked files/connections/rows, cleanup deferred outside the loop  |
| API contract   | Breaking signature change, missing validation, wrong status code  |
| Security       | Injection, missing authz check, hardcoded secret                  |

### Severity rubric

| Severity | Meaning                                                        | Merge policy           |
| -------- | -------------------------------------------------------------- | ---------------------- |
| Blocker  | Data corruption, security hole, production outage risk         | Merge blocked          |
| Major    | Incorrect behavior in a realistic path, missing required tests | Merge blocked          |
| Minor    | Maintainability, naming, small gaps with a safe workaround     | Fix now or fast-follow |
| Nit      | Style and preference                                           | Optional, never blocks |

## Enterprise Rules & Standards (MUST / SHOULD / MUST NOT)

- **MUST** give every finding a severity, a file/line reference, and a reason grounded in
  a named standard (a rule in this repository, OWASP, or a language style guide).
- **MUST** verify tests exist for each new behavior and each bug fix; a fix without a
  regression test is a Major finding.
- **MUST** state the review verdict explicitly; silence is not approval.
- **SHOULD** limit one review round to at most ~20 findings; defer the rest to follow-up
  issues so the author can act.
- **SHOULD** ask questions before assuming intent when the diff is ambiguous.
- **MUST NOT** approve with failing CI, unresolved Blocker/Major findings, or secrets in
  the diff.
- **MUST NOT** review only the diff hunks in isolation when a hunk changes a public
  contract — read the callers.

## Examples

Good review comment (actionable, severity, rationale):

```text
[Major] api/handler.go:42 — The handler returns the raw database error text to the
client, which leaks schema details. Return a sanitized problem response per
api-design, and log the cause server-side (see observability for the log format).
```

Bad review comment:

```text
LGTM, but maybe consider refactoring this a bit? Also the naming feels off.
```

Why it fails: no severity, no location, no standard invoked, and two vague opinions the
author cannot act on.

## Checklist

- [ ] CI (lint, tests, SAST) is green, or failures are explained and unrelated.
- [ ] Every finding has severity + location + rationale.
- [ ] New behavior and error paths have tests that fail without the change.
- [ ] No secrets, tokens, or credentials in the diff.
- [ ] Public contracts (API, exported functions, schemas) are backward compatible or
      explicitly versioned (see `api-design` and `git-workflow`).
- [ ] Follow-up issues exist for accepted Minor findings.

## Common Pitfalls

- **Style archaeology** — hand-commenting formatting the linter owns; waste and noise.
  Route it to `static-analysis`.
- **Bike-shedding** — debating taste instead of correctness; park it as a Nit or an issue.
- **Approval inflation** — "LGTM" under deadline pressure; the severity rubric exists to
  keep Blockers non-negotiable.
- **Diff blindness** — approving a refactor without reading call sites; always check
  callers of changed public symbols.

## References

- Google Engineering Practices — Code Review Developer Guide: https://google.github.io/eng-practices/review/
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/
- Conventional Comments: https://conventionalcomments.org/
