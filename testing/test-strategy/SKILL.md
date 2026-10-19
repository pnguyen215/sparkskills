---
name: test-strategy
description: 'Decides what to test at which layer — unit vs integration vs contract vs end-to-end — and designs the test portfolio for a service or repository. Trigger with "what tests do we need", "our E2E suite is too slow", or "design the test plan for this feature".'
---

# Test Strategy

## Purpose

Allocate testing effort where it catches the most defects per minute of CI time. The
skill maps the test pyramid onto a concrete portfolio per service, sets flaky-test and
quarantine policy, and decides when a layer is being abused (giant E2E suites, mock
pyramids, untested integration seams).

## When to Use / When NOT to Use

Use when:

- Planning tests for a new service, feature, or migration ("design the test plan").
- An existing suite is slow, flaky, or misses production defects.
- Deciding whether a behavior belongs in a unit, integration, contract, or E2E test.

Do NOT use when:

- Writing the tests themselves — use `testing/unit-testing` for the how.
- Setting coverage thresholds — use `testing/test-coverage`.
- Performance/load testing design — use `performance` for the method.

## Prerequisites & Assumptions

- The service architecture is known (modules, external dependencies, contracts).
- CI can run at least two stages (fast PR gate, deeper post-merge/nightly).
- Contract definitions exist (OpenAPI/proto) for service boundaries.

## Step-by-Step Workflow

1. **Inventory behaviors and risks** — list core business invariants, money/data
   paths, and integration seams. Risk ranks the portfolio, not habit.
2. **Assign layers** using the decision table below; write the allocation as one
   line per behavior.
3. **Define the CI split** — PR gate runs unit + affected integration (<10 min);
   post-merge runs full integration + contract; nightly runs E2E and load smoke.
4. **Set the flaky policy** — quarantine, diagnose within 24h, delete or fix within
   a week; a quarantined test still tracks an issue.
5. **Prepare test data rules** — synthetic fixtures in code, builders over shared
   mutable fixtures, seeded databases per run (containers), never production data.
6. **Review quarterly** — remove tests that duplicate lower layers, promote tests
   that caught real bugs, retire tests that never failed and guard nothing.

### Layer decision table

| Behavior                                   | Layer                            | Rationale                                      |
| ------------------------------------------ | -------------------------------- | ---------------------------------------------- |
| Pure logic, validation, mappers            | Unit                             | Fast, exhaustive edge cases                    |
| Service + real DB/cache/queue (containers) | Integration                      | Real SQL semantics, transactions, migrations   |
| Public API request/response shape          | Contract                         | Prevents breaking consumers; runs against spec |
| Critical user journeys across services     | E2E (few!)                       | Expensive, flaky — keep ≤ 10 journeys          |
| Failure modes (downstream down, timeouts)  | Integration with fault injection | Cannot be reproduced in unit tests honestly    |

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** keep the PR gate under 10 minutes; everything slower runs post-merge or
  nightly.
- **MUST** have contract tests for every public service API; a breaking change
  fails CI before review (see `api-design` versioning).
- **MUST** quarantine flaky tests with an issue within 24 hours; re-enabling without
  a fix is forbidden.
- **MUST** keep E2E suites ≤ 10 critical journeys; anything more belongs lower in
  the pyramid.
- **SHOULD** target roughly 70% unit / 20% integration / 10% E2E of test count and
  90/9/1 of execution time.
- **SHOULD** test failure modes explicitly (dependency timeout, 500, malformed
  input) at the integration layer with fault injection.
- **MUST NOT** use the production database or production data in any test.
- **MUST NOT** allow a test to depend on execution order or shared mutable state.

## Examples

Good — CI split (GitHub Actions sketch):

```yaml
jobs:
  unit: # PR gate, ~2 min
    script: go test -race -count=1 ./...
  integration: # post-merge, containers for pg/redis
    script: docker compose up -d && go test -tags=integration ./test/integration/...
  e2e: # nightly, staging deploy
    script: make deploy-staging && run-journeys
```

Bad — the inverted pyramid:

```text
One giant E2E suite (400 tests, 45 min) decides everything; unit tests exist
for trivial helpers only.
```

Why it fails: feedback is slow, failures are ambiguous ("which of 14 services
broke?"), and core logic is verified only through the whole system.

## Checklist

- [ ] Every behavior assigned to a layer with a one-line rationale.
- [ ] PR gate < 10 min; full suite split across post-merge/nightly stages.
- [ ] Contract tests cover all public service APIs.
- [ ] Flaky-test quarantine process exists and is enforced.
- [ ] Test data is synthetic, per-run, and never production-derived.
- [ ] Quarterly portfolio review scheduled (owner named).

## Common Pitfalls

- **E2E accumulation** — every new bug becomes "add an E2E test"; push coverage down
  the pyramid instead.
- **Mock pyramid** — thousands of unit tests asserting on mocks while seams rot;
  contract + integration tests own the seams.
- **Shared staging as test env** — cross-team interference; use ephemeral
  environments per run.
- **Flake normalization** — "just rerun it" culture; reruns hide real intermittent
  defects (races, clock issues).

## References

- Practical Test Pyramid (Hambrick): https://martinfowler.com/articles/practical-test-pyramid.html
- Google SRE — flaky tests chapter: https://sre.google/sre-book/addressing-cascading-failures/ (see also flaky test chapters)
- Pact contract testing: https://docs.pact.io/
