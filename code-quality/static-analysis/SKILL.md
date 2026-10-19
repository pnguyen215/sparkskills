---
name: static-analysis
description: 'Configures and enforces static analysis — linters, SAST, and complexity or duplication gates — in local development and CI. Trigger with "set up linting", "the lint gate is failing", or "add SAST to the pipeline".'
---

# Static Analysis

## Purpose

Make code-quality enforcement automatic instead of review-based. The skill defines the
toolchain per language, the exact quality gates (complexity, duplication, coverage of
security hotspots), and how to wire them into CI so findings block merges instead of
piling up in a backlog.

## When to Use / When NOT to Use

Use when:

- Setting up linting, formatting, SAST, or complexity gates for a repository.
- A lint or SAST gate fails and findings must be triaged or fixed.
- A new language is added to a polyglot repository and needs its analyzer set.

Do NOT use when:

- The request is a human code review — use `code-quality/code-review`.
- You need a security _audit_ with CVSS scoring — use `security`; this skill only runs
  the automated subset.
- The code does not compile; analyzers assume a buildable tree.

## Prerequisites & Assumptions

- Go 1.26+ with `golangci-lint` v2, Java 21/25 with Checkstyle/SpotBugs, Python 3.14+
  with `ruff` and `mypy` — or the equivalents adopted by the repository.
- CI can run at least one of: GitHub Actions, GitLab CI, or an equivalent.
- Pin analyzer versions in version control; un-pinned analyzers break builds.

## Step-by-Step Workflow

1. **Inventory** — list languages and package managers in the repo.
2. **Select tools** — one formatter + one linter per language (never two formatters
   fighting); add a SAST engine (Semgrep or CodeQL) for anything internet-facing.
3. **Configure** — commit configs at the repo root (examples below). Start from the
   default ruleset; disable individual rules with a written justification in the config.
4. **Gate** — add lint + SAST to the CI pipeline as _blocking_; local pre-commit hooks
   are a convenience, CI is the enforcement point.
5. **Baseline legacy findings** — for existing code, record current findings as a
   baseline file and fail only on _new_ findings; schedule baseline burn-down.
6. **Maintain** — review analyzer updates monthly; rule changes are PRs, not silent
   config edits.

## Enterprise Rules & Standards (MUST / SHOULD / MUST NOT)

- **MUST** run linters and SAST as blocking CI checks on every PR.
- **MUST** pin tool versions (e.g. `golangci-lint v2.x`, `ruff`, `Checkstyle`) in the
  config or lockfile.
- **MUST** justify every disabled rule inline in the config (`// disabled: reason`).
- **MUST** fail the build on new findings versus baseline; existing findings live in the
  baseline until burned down.
- **SHOULD** enforce measurable complexity limits: cyclomatic complexity ≤ 15 per
  function (warn at 10), files ≤ 400 lines, duplication ≤ 5% per package/module.
- **SHOULD** run SAST on the diff for speed and the full tree nightly.
- **MUST NOT** merge with `nolint`/`noinspection`/`# noqa` suppressions lacking a
  justification comment and an issue link.
- **MUST NOT** treat `gofmt`-level formatting as a review topic — formatters own it.

## Examples

Good — `.golangci.yml` (v2 format, current toolchain):

```yaml
version: "2"
linters:
  enable:
    - errcheck # unchecked errors
    - govet # vet suites
    - staticcheck # core static checks
    - contextcheck # lost context propagation
    - sloglint # structured-logging consistency
    - misspell
    - unconvert
    - copyloopvar
formatters:
  enable:
    - gofmt
    - goimports
```

Good — `ruff` for Python:

```toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S"]  # S = flake8-bandit security rules
```

Good — Semgrep SAST step (CI):

```yaml
semgrep-sast:
  script: semgrep ci --config p/default --error
```

Bad practice:

```text
"temporarily" disabling the linter for the release branch, no issue tracked.
```

Why it fails: disabled gates never come back on; use the baseline mechanism instead.

## Checklist

- [ ] One formatter and one linter per language, versions pinned, configs committed.
- [ ] `lint` and SAST are blocking CI jobs.
- [ ] Every suppressed rule has an inline reason and issue link.
- [ ] Complexity/duplication limits configured and passing (≤15 cyclomatic, ≤5% dup).
- [ ] Legacy findings baselined with a burn-down issue.
- [ ] `make lint` runs locally in under a minute (caching enabled).

## Common Pitfalls

- **Noisy start** — enabling every linter on day one drowns real findings; start with
  defaults, add rule sets incrementally.
- **Suppression creep** — blanket `nolint:all` files; require targeted suppressions.
- **Formatter wars** — two formatters with conflicting settings; pick one per language.
- **Nightly-only SAST** — vulnerabilities found days late; diff-scanning on PR catches
  them at review time.

## References

- golangci-lint v2 documentation: https://golangci-lint.run/
- Ruff (Python linter/formatter): https://docs.astral.sh/ruff/
- Semgrep: https://semgrep.dev/docs/
- OWASP Source Code Analysis Tools list: https://owasp.org/www-community/Source_Code_Analysis_Tools
