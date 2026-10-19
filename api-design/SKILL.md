---
name: api-design
description: 'Designs HTTP and gRPC APIs — resource modeling, versioning, pagination, idempotency, and a RFC 9457 error model. Trigger with "design this endpoint", "is this API breaking", "how should we version this", or "review this API contract".'
---

# API Design

## Purpose

Design service interfaces that stay stable as the product evolves: resource-oriented
HTTP (or proto-first gRPC), explicit versioning and compatibility rules, uniform
pagination, idempotency for unsafe methods, and a machine-readable error model
(RFC 9457 problem details) that clients can program against.

## When to Use / When NOT to Use

Use when:

- Designing or reviewing REST endpoints, gRPC services, or their contracts.
- Deciding if a change is breaking and needs a new version.
- Standardizing pagination, filtering, error payloads, or idempotency keys.

Do NOT use when:

- The task is documenting an existing API — use `api-documentation` (design first,
  then document).
- The interface is purely internal to one binary (function signatures) — use
  `design/design-pattern` and the language skills.

## Prerequisites & Assumptions

- HTTP APIs use JSON; the error model is RFC 9457 `application/problem+json`.
- gRPC uses proto3 with package versioning and buf lint/breaking checks.
- Contracts are versioned in the repo (`api/openapi.yaml`, `proto/`) and enforced
  by contract tests (`testing/test-strategy`).

## Step-by-Step Workflow

1. **Model resources, not actions** — nouns with stable identities
   (`/v1/orders/{id}`); verbs are HTTP methods; exceptions (search, cancel) get
   documented subresources or controller resources.
2. **Define the compatibility contract** — additive changes (new optional fields,
   new endpoints) are non-breaking; removing/renaming fields, narrowing types,
   or tightening validation is breaking → new major version (URI major:
   `/v2/...`).
3. **Specify the error model** — every non-2xx returns problem details with a
   stable `type` URI, human `title`, and a service-specific `code` (see example);
   never leak internals.
4. **Design collections** — cursor pagination (`page[size]`, `page[cursor]`),
   bounded page size (default 50, max 200), stable sort, and filtering by
   explicit query params.
5. **Make unsafe methods idempotent** — POST-with-idempotency-key (clients send
   `Idempotency-Key`), PUT is fully idempotent; retries are safe by design.
6. **Validate the contract** — run contract tests and `buf breaking`/oasdiff in
   CI so compatibility is machine-checked, not remembered.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** use plural resource nouns, HTTP-method semantics (GET is safe,
  PUT/DELETE idempotent, POST creates), and correct status codes
  (201+Location for creation, 204 for deletes, 4xx for caller faults, 5xx never
  for validation failures).
- **MUST** version only in the path major (`/v1`); everything else evolves
  additively; deprecations are announced with a `Deprecation`/`Sunset` header and
  a removal date before breaking changes.
- **MUST** return RFC 9457 problem details with a stable, documented `code` for
  every error.
- **MUST** make POSTs retry-safe via idempotency keys on any endpoint that moves
  money or state.
- **MUST** bound every list endpoint with cursor pagination and a max page size.
- **SHOULD** accept and return timestamps as RFC 3339 UTC; identifiers as opaque
  strings (never expose internal DB sequences).
- **SHOULD** use `PUT` for full replace, `PATCH` (JSON Merge Patch) for partial
  updates.
- **MUST NOT** change a field's type or semantics in place, remove response
  fields, or add required request fields within a major version.
- **MUST NOT** return `200 OK` with an error body — status codes are the contract.

## Examples

Good — error model (problem details, compiles as JSON):

```json
{
  "type": "https://api.example.com/problems/order-not-cancellable",
  "title": "Order cannot be cancelled",
  "status": 409,
  "code": "ORDER_NOT_CANCELLABLE",
  "detail": "Order o-123 has already shipped and cannot be cancelled.",
  "instance": "/v1/orders/o-123"
}
```

Bad — stringly-typed failure:

```json
{ "success": false, "error": "Error: duplicate key value violates
constraint \"orders_pkey\" on line 42 of orders_repo.go" }
```

Why it fails: leaks internals (table/constraint/file), no stable code to program
against, and the implicit 200 hides the failure from every standard HTTP client.

Good — pagination contract:

```text
GET /v1/orders?page[size]=50&page[cursor]=eyJpZCI6Im8tMTIzIn0
→ { "data": [...], "next_cursor": "eyJpZCI6Im8tMTczIn0", "has_more": true }
```

## Checklist

- [ ] Endpoints are resource-oriented with correct methods and status codes.
- [ ] Compatibility rules applied: the change is additive or a new major version.
- [ ] Every error path returns problem details with a stable `code`.
- [ ] Collections paginate with cursors and a bounded page size.
- [ ] Unsafe methods accept idempotency keys; retries tested.
- [ ] `buf breaking` / oasdiff runs in CI against the last released contract.
- [ ] Deprecations have `Sunset` headers and a documented removal date.

## Common Pitfalls

- **Breaking "just a little"** — tightening validation or removing a field for a
  "minor cleanup" breaks clients silently; additive-only within a major.
- **Chatty APIs** — one endpoint per UI screen; model resources, compose on the
  client (or add a documented BFF explicitly).
- **Verb URLs** — `/getOrderById` fights HTTP caching, semantics, and tooling.
- **Cursor amnesia** — page numbers over mutable collections skip/duplicate
  rows; cursors are the default for anything concurrent.

## References

- RFC 9457 — Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457
- Microsoft REST API Guidelines: https://github.com/microsoft/api-guidelines
- Google API Design Guide (AIP): https://google.aip.dev/general
- buf breaking (Protobuf): https://buf.build/docs/breaking/overview/
