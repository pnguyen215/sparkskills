---
name: incident-response
description: 'Runs production incident response — severity triage, stabilization before root-causing, structured communication, and blameless postmortems with tracked actions. Trigger with "we have an incident", "write the postmortem", or "the pager just fired".'
---

# Incident Response

## Purpose

Restore service fast, communicate clearly while doing it, and convert every incident
into durable fixes. The skill covers severity classification, the stabilize-first
playbook, the communication cadence, and the blameless postmortem with tracked
corrective actions.

## When to Use / When NOT to Use

Use when:

- Production is degraded, down, or breaching SLOs ("the pager just fired", "we
  have an incident").
- A postmortem is needed after an incident or severe near-miss.
- An emergency code fix must ship with a fast-track review.

Do NOT use when:

- The problem is pre-production only (CI broken, staging flaky) — fix via
  `ci-cd`; save the incident process for production.
- You are adding telemetry _after_ an incident as a general improvement — that is
  `observability`; the postmortem action items reference it.

## Prerequisites & Assumptions

- On-call rotation exists with escalation paths and a paging tool.
- SLOs and dashboards exist per service (`observability`); without them,
  severity is judged by user impact alone.
- The postmortem is blameless by policy: systems and process fail, people do not
  get blamed for system behavior.

## Step-by-Step Workflow

1. **Triage** — classify severity on impact: S1 = full outage or data
   loss/corruption risk; S2 = major degradation (SLO burning fast); S3 = minor,
   workaround exists. When unsure, classify high and downgrade later.
2. **Declare and staff** — open the incident channel, assign Incident Commander
   (IC), Communications Lead, and Operations Lead; the IC coordinates, responders
   execute — the person fixing should not also be the one writing updates.
3. **Stabilize before root-causing** — fastest safe mitigation first: rollback
   (`ci-cd` rollback path), feature-flag off, failover, shed load. Root cause
   hunting happens after user impact stops growing.
4. **Communicate on cadence** — internal updates every 30 min (S1/S2) with
   status, impact, next check-in time; external status page updates for S1.
5. **Resolve** — declare mitigated when impact stops (error budget stops
   burning), resolved when service is normal; verify with the same metrics that
   detected the incident.
6. **Postmortem within 5 business days** — timeline from logs/metrics, impact
   quantified, root cause + contributing factors, action items each with an owner
   and a due date; blameless tone; reviewed in a meeting, not just a document.
7. **Track actions to done** — every action item is an issue in the backlog;
   the postmortem is closed only when actions land or are consciously accepted.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** mitigate before diagnosing; restoring service outranks explanation.
- **MUST** assign a single Incident Commander per incident; command and
  execution roles are separate.
- **MUST** write the postmortem for every S1/S2 within 5 business days,
  blameless, with quantified impact (duration, requests affected, SLO budget
  burned).
- **MUST** attach an owner and due date to every action item; unowned actions
  are deleted, not filed for decoration.
- **MUST** test rollback paths quarterly so mitigation is real when needed.
- **SHOULD** use a standard timeline format (UTC timestamps, detection →
  mitigation → resolution) so multiple incidents aggregate.
- **MUST NOT** blame individuals in postmortems; "why did the system allow
  this" replaces "who did this".
- **MUST NOT** treat emergency fixes as gate-exempt — the fast path still
  includes tests and review, just shorter (`git-workflow`).
- **MUST NOT** declare resolution without verifying recovery on the detecting
  dashboards.

## Examples

Good — postmortem skeleton:

```markdown
# Postmortem 2026-10-14: Order API 5xx spike (S2)

Impact: 41 minutes, p99 4.2s→9.8s, 0.7% of requests failed,
22% of monthly error budget burned.
Timeline (UTC): 09:12 deploy v1.9.0 · 09:26 alert fired ·
09:31 IC declared · 09:44 rollback started · 09:53 mitigated · 10:11 resolved.
Root cause: connection-pool migration exhausted Postgres connections
under retry storm (see contributing factors: no pool alert, retries unbounded).
Actions:

- [ ] Add pool saturation alert (owner: @ana, due 2026-10-21)
- [ ] Bound client retries with backoff+jitter (owner: @raj, due 2026-10-28)
```

Bad — the blame game:

```markdown
Root cause: Ana deployed on Friday without telling anyone. She will be more
careful. No action items needed.
```

Why it fails: blames a person, misses the two system fixes (pool alerting,
retry bounds), and guarantees the same failure recurs with a different name in
the report.

## Checklist

- [ ] Severity assigned on impact; incident channel + IC named.
- [ ] Mitigation applied before root-cause work; mitigation type recorded
      (rollback/flag/failover).
- [ ] Updates sent on cadence with next-update time; status page updated for S1.
- [ ] Resolution verified on the dashboards that detected the incident.
- [ ] Postmortem written ≤ 5 business days, blameless, impact quantified.
- [ ] Every action item has an owner, due date, and issue link.

## Common Pitfalls

- **Hero mode** — one engineer doing IC + comms + fixes; roles exist precisely
  to prevent this.
- **Root-cause rabbit holes** — debugging while users bleed; stabilize first.
- **Heroic postmortems** — "we fixed it, no actions needed"; every S1/S2 yields
  at least one systemic action item.
- **Action-item graveyard** — actions filed and forgotten; review closure at
  ops reviews.

## References

- Google SRE — Incident Management: https://sre.google/sre-book/managing-incidents/
- Google SRE — Postmortems: https://sre.google/sre-book/postmortem-culture/
- PagerDuty Incident Response Guide: https://response.pagerduty.com/
