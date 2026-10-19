---
name: test-coverage
description: 'Measures and gates test coverage — per-language tooling, thresholds for total and changed code, and the difference between covered and tested. Trigger with "what is our coverage", "the coverage gate failed", or "raise coverage on this module".'
---

# Test Coverage

## Purpose

Use coverage as a floor and a change-detector, not a goal. The skill defines the
measurement tooling per language, the enterprise thresholds (overall and
changed-code), what legitimately gets excluded, and how to prevent coverage theater.

## When to Use / When NOT to Use

Use when:

- Configuring coverage collection and CI gates for a repository.
- A coverage gate fails or a module's coverage dropped.
- Deciding whether new code meets the changed-code threshold before merge.

Do NOT use when:

- Designing _which_ tests to write — use `testing/test-strategy`.
- Writing the tests — use `testing/unit-testing`.
- Someone claims "100% coverage = no bugs" — show them the pitfalls section.

## Prerequisites & Assumptions

- Go: `go test -cover -coverprofile`; Java: JaCoCo; Python: `coverage.py`/`pytest-cov`.
- CI publishes a coverage report per PR and blocks on the thresholds below.
- Exclusions are explicit and reviewed (generated code, `main()` wiring).

## Step-by-Step Workflow

1. **Measure** — generate the coverage profile per language (commands below) and
   publish an HTML report as a CI artifact.
2. **Gate the totals** — enforce: ≥ 80% statement coverage overall, ≥ 90% on
   packages marked critical (`payment`, `auth`, data-integrity), and ≥ 90% on
   changed lines in a PR (diff coverage). Libraries aiming at public release target
   ≥ 90% overall.
3. **Review quality alongside the number** — for any new test, verify it asserts
   outcomes (see `unit-testing`); coverage without assertion review is theater.
4. **Manage exclusions** — generated code, pure wiring (`main`), and build tags get
   explicit exclusion config with a comment; nothing else is excluded.
5. **Burn down gaps** — keep a ranked list of lowest-covered critical packages;
   attach it to quarterly planning instead of mandating blind "raise the number"
   drives.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** enforce diff coverage ≥ 90% on every PR; overall ≥ 80%; critical packages
  ≥ 90%.
- **MUST** publish the coverage report (HTML/summary) as a CI artifact on every PR.
- **MUST** treat 100% coverage as a per-function target only for critical error
  handling (parsers, money math, security checks) — never a repo-wide mandate that
  invites trivial tests.
- **MUST** justify every exclusion inline in config (generated/wiring only).
- **SHOULD** track coverage trend per package, not just the repo average; averages
  hide rotting modules.
- **MUST NOT** write assertion-free tests to raise the number; reviewers reject
  them as coverage theater.
- **MUST NOT** exclude files to pass the gate; exclusions are for generated code
  and wiring, and they are reviewed.

## Examples

Good — Go coverage with race detection and report:

```sh
go test -race -count=1 -coverprofile=coverage.out -covermode=atomic ./...
go tool cover -func=coverage.out | tail -1   # total: 84.6%
go tool cover -html=coverage.out -o coverage.html
```

Bad — chasing the number:

```go
func TestService_Cancel(t *testing.T) {
	s := NewService(nil, nil) // nil deps to reach the branch
	_ = s.Cancel(context.Background(), "")
}
```

Why it fails: it executes lines and asserts nothing; the coverage gate rises while
the regression protection stays zero.

Python equivalent:

```sh
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Checklist

- [ ] Coverage profile generated in CI and published as an artifact.
- [ ] Gates configured: overall ≥ 80%, diff ≥ 90%, critical packages ≥ 90%.
- [ ] Exclusions limited to generated code and wiring, each with a comment.
- [ ] New tests reviewed for assertions, not just execution.
- [ ] Low-coverage critical packages have a tracked burn-down issue.
- [ ] Coverage measured with `-race`/strict mode on (Go) so concurrency is included.

## Common Pitfalls

- **The 100% mandate** — drives worthless tests for getters and wiring; reserve 100%
  for critical functions.
- **Coverage ≠ correctness** — 100% covered code can still be wrong; pair the gate
  with `testing/test-strategy` layers and mutation-style spot checks.
- **Exclusion creep** — one "temporary" exclusion at a time until the metric lies;
  exclusions are reviewed in PRs like code.
- **Averaging away problems** — repo-level averages hide a 20% auth package;
  report per-package.

## References

- Go coverage: https://go.dev/blog/cover
- JaCoCo (Java): https://www.jacoco.org/jacoco/trunk/doc/
- coverage.py: https://coverage.readthedocs.io/
