---
name: unit-testing
description: 'Writes fast, isolated unit tests — table-driven cases, error paths, edge-case discovery, concurrency tests, benchmarks, and fuzzing — using each language''s standard test stack. Trigger with "write tests for this function", "increase coverage", or "this bug needs a regression test".'
---

# Unit Testing

## Purpose

Produce unit tests that actually catch regressions: fast, isolated, deterministic, and
complete over error paths and edge cases — not just the happy path. The skill encodes
the discovery taxonomy for edge cases, the required test structure per language, and
the performance-test hooks (benchmarks, fuzzing, race detection).

## When to Use / When NOT to Use

Use when:

- Writing tests for new or changed functions ("write tests for this function").
- A bug was fixed and a regression test is required.
- Reviewing whether a test suite meaningfully covers behavior.

Do NOT use when:

- The question is which tests belong at which layer (integration/E2E) — use
  `testing/test-strategy`.
- You need coverage measurement and thresholds — use `testing/test-coverage`.
- The code is not yet designed for testability; refactor seams first
  (`code-quality/refactoring`).

## Prerequisites & Assumptions

- Go: standard library only — `testing`, `reflect`, `sync` (preserved legacy rule;
  no assertion libraries), `go test -race` available.
- Java: JUnit 5 + AssertJ; Python: `pytest` + `unittest.mock`.
- Tests run in seconds, no network/database/filesystem dependencies — collaborators
  are injected interfaces faked in the test.

## Step-by-Step Workflow

1. **Enumerate cases before writing code** — cover the five discovery dimensions:
   (1) boundary values (zero, min, max, ±1, overflow, NaN/Inf, empty, nil),
   (2) concurrency and timing (races, cancellation mid-operation, deadline expiry),
   (3) domain-specific real-world failures (≥5 production scenarios for core logic),
   (4) input mutation and aliasing (caller mutates a passed slice/map),
   (5) error paths (every unhandled or swallowed branch, partial failures).
2. **Name tests by behavior** — Go `TestCancel_ExpiredOrder`, Java
   `cancel_expiredOrder_throws`, Python `test_cancel_expired_order_raises`.
3. **Write table-driven cases** — one case table per function; each row: name, input,
   want, wantErr. See example below.
4. **Test error contracts** — assert with `errors.Is` (Go), exception types + message
   (JUnit), `pytest.raises` matchers — never assert only "returned an error".
5. **Add the performance hooks** — a `Benchmark*`/`@Benchmark`/`pytest-benchmark` for
   hot paths and a fuzz target for parsers (`go test -fuzz`, JUnit jqwik, hypothesis).
6. **Verify** — run the suite with race detector/strict warnings; confirm each new
   test fails when the implementation is broken (mutate once, watch it fail).

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** use table-driven/subtest structure for functions with >2 input scenarios.
- **MUST** cover every error branch and every boundary of the function under test.
- **MUST** keep tests deterministic: freeze time, seed randomness, no real network;
  flaky tests are quarantined with an issue within 24h (see `test-strategy`).
- **MUST** test concurrent code with the race detector enabled (`go test -race`);
  untested concurrency is unshipped concurrency.
- **MUST** give a bug fix a regression test in the same change.
- **SHOULD** share assertion helpers through one `helpers_test.go`/fixture module
  (`assertEqual`, `assertErrorIs`, `requireNoError`) instead of hand-rolled checks.
- **SHOULD** keep each test under ~40 lines; extract builders for long arrangements.
- **MUST NOT** test through mocks of the thing under test; mock only injected
  collaborators at their interfaces.
- **MUST NOT** write tests that pass regardless of implementation (assert-on-mock
  theater); assert observable outputs and state.
- **MUST NOT** use `time.Sleep` for synchronization — use channels, sync
  primitives, or awaitables.

## Examples

Good — table-driven Go test with error contract (compiles, stdlib only):

```go
func TestParseRetry(t *testing.T) {
	tests := []struct {
		name    string
		in      string
		want    RetryPolicy
		wantErr bool
	}{
		{name: "valid never", in: "never", want: RetryNever},
		{name: "valid always", in: "always", want: RetryAlways},
		{name: "empty string", in: "", wantErr: true},
		{name: "unknown value", in: "sometimes", wantErr: true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			got, err := parseRetry(RetryPolicy(tt.in))
			if tt.wantErr {
				if err == nil {
					t.Fatalf("parseRetry(%q) = %v, want error", tt.in, got)
				}
				return
			}
			if err != nil {
				t.Fatalf("parseRetry(%q) unexpected error: %v", tt.in, err)
			}
			if got != tt.want {
				t.Errorf("parseRetry(%q) = %v, want %v", tt.in, got, tt.want)
			}
		})
	}
}
```

Bad — testing only the happy path:

```go
func TestParseRetry(t *testing.T) {
	p, _ := parseRetry("always") // ignores the error value
	if p != RetryAlways {
		t.Fatal("wrong")
	}
}
```

Why it fails: the blank error hides regressions in error handling, and one input
proves almost nothing about a parser.

## Checklist

- [ ] All five edge-case dimensions enumerated for the function under test.
- [ ] Table-driven structure with named cases; error cases assert error identity
      (`errors.Is` / exception type), not just presence.
- [ ] Regression test added for every bug fix in the change.
- [ ] Race detector (Go) or strict warnings (Java/Python) pass locally.
- [ ] Benchmarks exist for hot paths; fuzz target exists for parsers.
- [ ] No real network, filesystem, or sleeps in the test; suite runs in seconds.

## Common Pitfalls

- **Coverage theater** — tests that execute lines but assert nothing; every test
  must assert an outcome.
- **Test interdependence** — shared mutable fixtures across tests; build fresh state
  per test.
- **Mock proliferation** — mocking value types and pure functions; mock only I/O
  collaborators.
- **Assertion libraries as a crutch (Go)** — the stdlib rule keeps builds lean; the
  helper file gives the ergonomics.

## References

- testing package docs (Go): https://pkg.go.dev/testing
- Go fuzzing: https://go.dev/doc/fuzz
- JUnit 5 user guide: https://junit.org/junit5/docs/current/user-guide/
- pytest — parametrized tests: https://docs.pytest.org/en/stable/how-to/parametrize.html
