---
name: api-documentation
description: 'Writes and maintains API reference documentation — OpenAPI 3.1 specifications, GoDoc/Javadoc/docstring references, and error catalogs generated from code. Trigger with "document this endpoint", "the OpenAPI spec is out of date", or "generate API docs".'
---

# API Documentation

## Purpose

Keep API reference material accurate and generated from the source of truth. The skill
covers OpenAPI 3.1 authoring for HTTP APIs, language-native doc comments (GoDoc,
Javadoc, Python docstrings), and the error catalog that callers need to handle failures.

## When to Use / When NOT to Use

Use when:

- Documenting or updating REST/gRPC endpoints, request/response schemas, or errors.
- The OpenAPI file and the implementation have drifted and must be reconciled.
- Preparing an API for public consumption or a partner integration.

Do NOT use when:

- The request is prose documentation (README, tutorials) — use `readme-generator` or
  `technical-writing`.
- The API shape itself is wrong; fix it first under `api-design`, then document.
- You need operational documents (runbooks) — that is `technical-writing`.

## Prerequisites & Assumptions

- OpenAPI 3.1 is the HTTP specification format (JSON-Schema-compatible, latest stable
  line; 3.2 accepted where tooling supports it).
- Doc comments follow each language's official conventions (`go.dev/doc/comment`,
  Javadoc, PEP 257).
- Docs live next to code and are validated in CI (`ci-cd`).

## Step-by-Step Workflow

1. **Extract truth from code** — list routes/handlers (or proto services), methods,
   request/response types, and status/error codes from the implementation, not from
   memory or old docs.
2. **Author the OpenAPI file** — one `openapi.yaml` (or per-tag files bundled):
   info, servers, security schemes, paths, schemas, and a shared `Error` schema.
3. **Document every operation** — summary, description, all parameters, all response
   codes (success _and_ errors), and at least one example per schema.
4. **Build the error catalog** — one table per endpoint: HTTP code, error code, when it
   occurs, caller action.
5. **Generate and verify** — run doc generation and lint (`spectral lint`,
   `doc.go`/`javadoc`/`mkdocs` as applicable); redoc/Swagger render must succeed.
6. **Wire CI** — spec lint and a drift check (routes in code vs. spec) block merges.
7. **Publish** — render to the docs site; version docs with the API version.

## Enterprise Rules & Standards (MUST / SHOULD / MUST NOT)

- **MUST** document every operation with all parameters, all response codes, and at
  least one concrete example per request/response schema.
- **MUST** keep the spec in sync with code; the CI drift check blocks merges.
- **MUST** reuse named components (`components/schemas`) instead of inline object
  duplicates.
- **MUST** document the error model with stable machine-readable error codes (the
  problem-detail shape from `api-design`).
- **SHOULD** include a complete end-to-end example flow (authenticate → create → read).
- **SHOULD** mark deprecations with `deprecated: true` and a removal date.
- **MUST NOT** hand-write types that a generator can produce from code; generated docs
  are the default for doc comments.
- **MUST NOT** publish internal-only fields, secrets, or sample credentials.

## Examples

Good — OpenAPI 3.1 fragment with named schema and error responses:

```yaml
paths:
  /v1/orders/{id}:
    get:
      operationId: getOrder
      summary: Get an order by ID
      parameters:
        - $ref: "#/components/parameters/OrderId"
      responses:
        "200":
          description: The requested order.
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Order" }
        "404":
          description: No order with the given ID is visible to the caller.
          content:
            application/problem+json:
              schema: { $ref: "#/components/schemas/Error" }
```

Bad — undocumented error paths:

```yaml
responses:
  "200": { description: OK } # only success documented
```

Why it fails: callers discover 404/409/422 behavior in production; the error catalog
below is the contract for failure handling.

Error catalog row (good):

```text
| 404 | ORDER_NOT_FOUND | No order with this ID is visible to the caller | Verify the ID; do not retry |
```

## Checklist

- [ ] Every path, method, parameter, and response code is documented.
- [ ] `spectral lint openapi.yaml` passes; all `$ref` targets resolve.
- [ ] Every schema has at least one example; error catalog complete per endpoint.
- [ ] Spec drift check wired into CI and passing.
- [ ] No secrets or internal fields in examples.
- [ ] Generated doc comments (GoDoc/Javadoc/docstrings) render without warnings.

## Common Pitfalls

- **Docs as an afterthought** — written once at launch, then drift; the CI drift check
  is the fix, not good intentions.
- **Anonymous schemas** — inline objects everywhere; reuse named components.
- **Happy-path-only docs** — undocumented 4xx/5xx responses; callers need failure modes.
- **Example fiction** — examples that never ran; generate them from real fixtures.

## References

- OpenAPI Specification 3.1: https://spec.openapis.org/oas/v3.1.1.html
- Spectral (OpenAPI linter): https://docs.stoplight.io/docs/spectral
- Go doc comments: https://go.dev/doc/comment
- Javadoc style guide: https://www.oracle.com/technical-resources/articles/java/javadoc-tool.html
