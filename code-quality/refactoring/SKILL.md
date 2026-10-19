---
name: refactoring
description: 'Plans and executes behavior-preserving refactors — dead-code removal, cohesion tightening, declaration ordering, encapsulation, and function optimization. Trigger with "refactor this package", "remove dead code", or "make this function readable".'
---

# Refactoring

## Purpose

Improve the internal structure of code without changing observable behavior. The skill
covers the four moves that matter most in enterprise codebases: eliminating dead and
duplicate code, tightening cohesion, restoring readability (ordering, guard clauses,
named conditions), and optimizing functions — each verified by tests and tooling.

## When to Use / When NOT to Use

Use when:

- Someone asks to "refactor", "clean up", "remove dead code", "declutter", or
  "optimize this function" while behavior must stay identical.
- A module has grown mixed responsibilities, orphaned helpers, or unreadable nesting.
- A library migration (upgrade or replacement) must preserve its public contract.

Do NOT use when:

- Behavior is allowed to change — that is feature work; plan it as such.
- The problem is missing tests entirely; stabilize with `testing/unit-testing` first.
- You only need style fixes the linter can apply — use `static-analysis`.

## Prerequisites & Assumptions

- A green test suite exists before the first change; if not, write
  characterization tests per `testing/unit-testing`.
- Language rules for Go, Java, or Python come from `language-specific/*`.
- No behavior change, no public-signature change, no dependency additions without
  explicit approval.

## Step-by-Step Workflow

1. **Pin behavior** — run the full test suite and record results; add tests for any
   untested behavior you are about to touch.
2. **Audit** — build a caller/callee map of the target scope and produce two tables:
   dead-code candidates (categories below) and cohesion violations (dimensions below).
3. **Order the work** — smallest, safest changes first: dead code → duplicates →
   cohesion moves → readability → performance. One concern per commit
   (see `git-workflow` for commit hygiene).
4. **Execute in steps** — after every step re-run tests; never stack unverified moves.
5. **Optimize last** — only with a benchmark before/after (`performance` owns the
   method); optimization without measurement is out of scope here.
6. **Report** — deliver the audit tables, the list of behavior checks performed, and
   confirmation that exported APIs are unchanged (or list approved exceptions).

### Dead-code categories and protections

| Category                                  | Example                                      | Rule                                                            |
| ----------------------------------------- | -------------------------------------------- | --------------------------------------------------------------- |
| Unreachable                               | Code after an unconditional `return`         | Delete                                                          |
| Orphaned                                  | Function with zero callers in repo and tests | Delete                                                          |
| Superseded                                | `parseV1` kept after `parseV2` shipped       | Delete                                                          |
| Redundant condition                       | Check provably always false/true             | Delete                                                          |
| Commented-out code                        | `// result = legacyProcess(x)`               | Delete — Git history is the archive                             |
| Dead constant/variable                    | Never read                                   | Delete                                                          |
| Exported symbol, external callers unknown | Any public API item                          | Mark `SUSPECTED_DEAD`, do NOT delete — needs human confirmation |
| Test-only helper                          | Used only by `_test.go` / test fixtures      | Keep, mark as intentional                                       |
| Interface no-op stub                      | `func (n *nopLogger) Log(...) {}`            | Keep, mark "no-op: satisfies <Interface>"                       |

### Cohesion dimensions (audit each file against these)

| Dimension       | Question                                    | Red flag                                            |
| --------------- | ------------------------------------------- | --------------------------------------------------- |
| Functional      | One responsibility per file?                | Parsing + I/O + business rules mixed                |
| Sequential      | Clear pipeline of dependent steps?          | Steps invoked from unrelated places                 |
| Communicational | Code operating on the same data co-located? | One struct mutated from 3+ files                    |
| Logical         | Same-category functions grouped?            | Validators scattered everywhere                     |
| Temporal        | Lifecycle-adjacent calls grouped?           | Init split across `init()` and distant constructors |

### Readability standards applied during the refactor

- **Guard clauses**: validate and return early; the happy path is the last, unindented
  block. Nesting deeper than 2 levels is a finding.
- **Named conditions**: extract multi-part booleans into well-named variables.
- **Step comments**: functions longer than ~40 lines get phase comments explaining why,
  not what. Comments that restate the code are deleted, not rewritten.
- **Declaration ordering** (per file): package doc → imports (stdlib, external, internal)
  → constants/vars → types → constructors → primary exported API → interface
  implementations (grouped, marked `// --- Implements <Interface> ---`) → secondary
  helpers → getters/setters (alphabetical) → unexported helpers (most-called first).
- **Reuse before rewrite**: search the codebase for an existing helper before writing a
  new one; duplicating an existing validation or conversion is a finding.
- **Style alignment**: the refactor must match the surrounding code's conventions —
  naming, error handling, receiver style — not introduce a second style.

### Legacy convention, opt-in

Some teams (the convention is preserved here from the legacy repository) consolidate Go
packages into `constant.go` / `type.go` / `errors.go` / `options.go` / `utilities.go`
with unexported fields, `FieldName()` getters, `SetFieldName()` setters, and `With*`
functional options. If the target repo adopts it, apply it consistently; otherwise
follow the idiomatic layout of the existing codebase. Do not mix the two styles in one
package.

## Enterprise Rules & Standards (MUST / SHOULD / MUST NOT)

- **MUST** keep every refactor behavior-preserving; observable outputs, error types, and
  public signatures stay identical unless an approved contract change is documented.
- **MUST** run tests after every step; a step is not done until green.
- **MUST** mark externally-visible dead code `SUSPECTED_DEAD` instead of deleting it.
- **MUST** delete commented-out code rather than "temporarily" keeping it.
- **SHOULD** split refactoring from feature work into separate changes; mixing them
  hides risk.
- **SHOULD** cap a single refactor PR at ~400 changed lines; split larger moves.
- **MUST NOT** rename or reorder exported identifiers as a side effect — that is an API
  change and needs its own review under `api-design` rules.
- **MUST NOT** introduce new dependencies during a refactor.

## Examples

Good — guard clauses and a named condition (Go):

```go
func (d *Diagram) compile() ([]byte, error) {
	// Step 1: reject empty diagrams — the DOT renderer panics on them.
	if len(d.nodes) == 0 {
		return nil, ErrEmptyDiagram
	}
	// Step 2: sort deterministically so snapshot tests are reproducible.
	sorted := d.sortedNodes()
	adj := buildAdjacency(sorted, d.edges)
	return d.renderer.Render(adj)
}
```

Bad — nesting hides the happy path:

```go
func process(input string) (string, error) {
	if input != "" {
		if len(input) < 256 {
			result, err := transform(input)
			if err == nil {
				return result, nil
			}
		}
	}
	return "", ErrInvalidInput
}
```

Why it fails: three nesting levels to reach the happy path, one error value for three
different failures, and no context in the error.

## Checklist

- [ ] Tests green before starting; characterization tests added for untested logic.
- [ ] Dead-code audit table produced, with `SUSPECTED_DEAD` marks where needed.
- [ ] Cohesion audit table produced with corrective actions.
- [ ] Each commit is behavior-preserving and single-purpose.
- [ ] Public API surface unchanged (verified by diffing exported symbols).
- [ ] Benchmarks run before/after for any performance-targeted change (`performance`).
- [ ] No new dependencies, no placeholder comments, no commented-out code left behind.

## Common Pitfalls

- **Big-bang refactors** — weeks-long branches that never merge; keep steps shippable.
- **Silent behavior drift** — "just cleaning up" that changes an error message a client
  matches on; treat messages and types as observable behavior.
- **Refactor-as-cover** — smuggling feature changes into a refactor PR; reviewers must
  reject mixed changes.
- **Deleting exported code** — an unused exported symbol in a library may have external
  callers; only `SUSPECTED_DEAD` marking is safe.

## References

- Fowler, _Refactoring_ (2nd ed.): https://martinfowler.com/books/refactoring.html
- Effective Go — reuse, composition, naming: https://go.dev/doc/effective_go
- Google Engineering Practices — code review: https://google.github.io/eng-practices/review/
