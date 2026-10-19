---
name: technical-writing
description: 'Produces structured engineering documents — Architecture Decision Records, runbooks, and deep-dive explainers — using standardized templates. Trigger with "write an ADR", "we need a runbook for this service", or "document this design decision".'
---

# Technical Writing

## Purpose

Capture engineering knowledge in durable, structured documents: ADRs for decisions,
runbooks for operations, and deep dives for complex concepts. Good documents are
findable, dated, and honest about rejected alternatives — this skill enforces that
shape so readers can trust and navigate them.

## When to Use / When NOT to Use

Use when:

- A significant technical decision needs recording ("write an ADR", "why did we pick
  X?", "document this design decision").
- A service needs an operational runbook (alerts, failure modes, recovery steps).
- A complex concept needs a deep-dive explainer for onboarding or reviews.

Do NOT use when:

- The deliverable is API reference — use `api-documentation`.
- The deliverable is a project README — use `readme-generator`.
- The "decision" is a style preference already covered by a rule in this repository;
  point to the rule instead of writing a new document.

## Prerequisites & Assumptions

- Documents live in version control next to code (default: `docs/adr/NNNN-*.md`,
  `docs/runbooks/`).
- ADRs are immutable once accepted: changes are new ADRs that supersede old ones.
- Runbooks state facts verified against the running system; unverified steps are
  marked as such, never invented.

## Step-by-Step Workflow

1. **Classify the document** — decision (ADR), operations (runbook), or concept
   (deep dive); pick the template below.
2. **Gather evidence** — for ADRs: options considered with real trade-offs; for
   runbooks: alerts, dashboards, and commands, verified against a live or staged
   system; for deep dives: sources and diagrams.
3. **Draft with the template** — every section filled; write "not applicable —
   reason" rather than deleting sections.
4. **Record rejected alternatives** — an ADR without alternatives is a decision log
   entry, not a record; reviewers must ask "what else did we consider?".
5. **Review and accept** — ADRs are reviewed like code; acceptance flips status from
   `Proposed` to `Accepted` with a date.
6. **Maintain** — superseded ADRs link forward; runbooks are re-verified quarterly
   and after every incident that touches them (`incident-response`).

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** use the numbered ADR format (`NNNN-title-kebab-case.md`) with status,
  context, decision, and consequences sections.
- **MUST** document at least one rejected alternative and the reason it lost.
- **MUST** keep ADRs immutable after acceptance; changes via superseding ADRs.
- **MUST** write runbooks so an on-call engineer unfamiliar with the service can act:
  symptom → diagnosis → action → verification, with real commands and alert names.
- **SHOULD** time-box a deep dive to one concept and target one audience level.
- **SHOULD** use Mermaid or ASCII diagrams with a caption stating what the diagram
  shows.
- **MUST NOT** edit accepted ADR content (status transitions aside) or delete
  superseded ADRs.
- **MUST NOT** put secrets, customer data, or unredacted credentials in any document.

## Examples

Good — ADR skeleton:

```markdown
# ADR-0014: Adopt slog for structured logging

Status: Accepted (2026-10-18)
Supersedes: ADR-0009

## Context

Our log pipeline requires JSON; the stdlib log lacks levels/attributes.

## Decision

Use log/slog with JSONHandler as the only approved handler in services.

## Consequences

- Correlated fields, cheaper ingestion, stdlib support since Go 1.21.
  − Logrus adapters must be wrapped during migration (tracked in #882).

## Alternatives considered

- zerolog: faster, but adds a dependency for marginal gain at our volume. Rejected.
- Keep text logs and parse at the edge: brittle parsers, rejected.
```

Bad — decision with no alternatives:

```markdown
# ADR-0007: Use Kafka

Decision: we will use Kafka.
```

Why it fails: no context, no alternatives, no consequences — the next team cannot
re-evaluate the decision when constraints change.

Runbook fragment (good):

```markdown
## Alert: OrderLatencyHigh (SLO burn 2% in 1h)

1. Check dashboard `orders-latency` panel p99 (link).
2. `kubectl -n orders get pods -l app=orders` — look for restarts.
3. If restarts: `kubectl -n orders logs deploy/orders --previous | tail -200`
4. Roll back: `make release-rollback VERSION=<previous>` (verified 2026-10-02).
```

## Checklist

- [ ] Document type and template selected (ADR / runbook / deep dive).
- [ ] ADR has status, date, context, decision, consequences, and ≥1 rejected
      alternative.
- [ ] Runbook commands verified against a real system; verification date noted.
- [ ] Diagrams have captions; acronyms expanded on first use.
- [ ] No secrets or personal data in the document.
- [ ] Filed under `docs/` with the correct numbering/naming convention.

## Common Pitfalls

- **Decision amnesia** — choices made in chat threads with no ADR; write the record
  the same week.
- **Museum runbooks** — steps referencing decommissioned dashboards; quarterly
  re-verification keeps them alive.
- **Novel syndrome** — 20-page deep dives nobody reads; one concept per document.
- **Living ADRs** — silently editing accepted decisions; supersede instead.

## References

- Architecture Decision Records: https://adr.github.io/
- Google SRE — Postmortem & operational docs culture: https://sre.google/sre-book/postmortem-culture/
- Mermaid diagram syntax: https://mermaid.js.org/intro/
