---
name: observability
description: 'Instruments services with structured logging (slog), metrics (RED/USE), and distributed tracing via OpenTelemetry — with PII redaction and SLO wiring. Trigger with "add logging", "we can not debug this in prod", or "set up tracing/metrics".'
---

# Observability

## Purpose

Make production behavior explainable from telemetry instead of guesswork. The skill
defines the three pillars concretely: structured logs with stable attributes, RED/USE
metrics wired to SLOs, and trace propagation across every hop — plus the redaction
rules that keep telemetry safe.

## When to Use / When NOT to Use

Use when:

- Adding or reviewing logging, metrics, or tracing in a service.
- Debugging requires correlating events across services ("we can't tell what
  happened to this request").
- Defining dashboards, SLOs, or alert rules for a new service.

Do NOT use when:

- An incident is active — use `incident-response`; instrument later with a
  postmortem action item.
- The question is local performance measurement — use `performance` (profiling
  owns that).

## Prerequisites & Assumptions

- Go services log via `log/slog` (JSON handler); Java via SLF4J+Logback JSON
  encoder; Python via `logging` with JSON formatting.
- OpenTelemetry SDK for metrics/traces; a collector backend exists (Prometheus/
  Grafana, Jaeger/Tempo or equivalent).
- Every service owns an SLO for its critical request path (availability or latency).

## Step-by-Step Workflow

1. **Log with structure** — one logger per component (injected, not global);
   constant keys (`order_id`, `user_id`, `attempt`), values as typed attributes;
   `Info` for state changes, `Warn` for degraded-but-handled, `Error` for
   operator-visible failures with `err` attribute.
2. **Propagate context** — pass `context.Context` (Go) / current span context
   through every layer; log with the context variant so trace/log IDs correlate.
3. **Instrument metrics** — RED for services (rate, errors, duration of requests),
   USE for resources (utilization, saturation, errors of DB pools, queues);
   standard attributes: `service`, `route`, `method`, `status`.
4. **Trace critical paths** — spans at service and dependency boundaries (HTTP
   server, DB call, queue publish); client spans inherit context; sample at 1–10%
   head-based or tail-based for errors.
5. **Define SLOs and burn alerts** — per critical path: target (e.g. 99.9% of
   requests < 300 ms), error budget, burn-rate alerts (fast + slow windows).
6. **Review quarterly** — delete unused metrics (cardinality audit), confirm
   redaction rules still hold, verify dashboards map to SLOs.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** use structured logging with constant, snake_case keys; no string-mangled
  messages, no `fmt.Println`/`print`.
- **MUST** redact secrets, tokens, and PII at the logging layer (redaction
  middleware or typed field wrappers); a token never appears even at DEBUG.
- **MUST** include the correlation keys (`trace_id`, `request_id`, `user_id` where
  lawful) in error logs.
- **MUST** propagate trace context across every process and queue boundary.
- **MUST** attach the underlying error to error logs (`slog.Any("err", err)` /
  exception field), never log-and-continue silently.
- **SHOULD** log state transitions ("order cancelled"), not method entries; entry/
  exit logs double volume for no insight.
- **SHOULD** bound metric cardinality: no unbounded labels (user IDs, URLs with
  IDs) — normalize routes.
- **MUST NOT** log at ERROR for expected business outcomes (validation failures
  are WARN/INFO with counters).
- **MUST NOT** create metrics with user-specific label values.

## Examples

Good — structured, correlated, redacted (Go, compiles):

```go
logger.InfoContext(ctx, "order cancelled",
	slog.String("order_id", id),
	slog.String("trace_id", trace.TraceIDFromContext(ctx)),
	slog.Int("item_count", len(order.Items)),
) // no customer name, no raw email, no token
```

Bad — the log line that leaks and explains nothing:

```go
log.Printf("user %s did something with order %v, err: %v", user, order, err)
```

Why it fails: unstructured (unqueryable), leaks user identity, vague action text,
and the error is printed but the operation continues as if nothing happened.

Metric naming (good):

```text
http_server_request_duration_seconds{service="orders",route="/v1/orders/:id",method="GET"}
```

## Checklist

- [ ] Logs are JSON with constant keys; no PII/secrets (redaction test exists).
- [ ] Every error log carries the error object and correlation IDs.
- [ ] RED metrics exist for every endpoint; USE metrics for DB pools/queues.
- [ ] Trace context propagates through HTTP clients, DB calls, and queues.
- [ ] SLO defined for the critical path with burn-rate alerts wired.
- [ ] Cardinality audit done: no unbounded label values.
- [ ] Log levels used correctly (no ERROR spam for expected outcomes).

## Common Pitfalls

- **Debug-by-printf in prod** — unstructured strings that no query can join;
  structure from day one.
- **Cardinality explosion** — a label per user/URL ID melts the metrics backend;
  normalize and bound.
- **Log-and-swallow** — logging an error and returning success; decide: handle, or
  propagate, never both-neither.
- **Dashboard sprawl** — 40 charts nobody reads; dashboards mirror the SLO and its
  dependencies only.

## References

- log/slog (Go): https://pkg.go.dev/log/slog
- OpenTelemetry concepts: https://opentelemetry.io/docs/concepts/
- RED method (Weave): https://www.weave.works/blog/the-red-method-key-metrics-for-microservices-architecture/
- Google SRE — implementing SLOs: https://sre.google/workbook/implementing-slos/
