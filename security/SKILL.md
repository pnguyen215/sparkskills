---
name: security
description: 'Audits and hardens code against the OWASP Top 10 — input validation, authn/authz, secrets management, cryptography, and dependency scanning with CWE mapping. Trigger with "security review", "is this endpoint secure", "scan our dependencies", or "where do we store this secret".'
---

# Security

## Purpose

Find and fix vulnerability classes before attackers do, and keep secrets and
dependencies under control. The skill condenses the legacy audit taxonomy into a
repeatable pass: classify findings by CWE/OWASP category, fix in priority order, and
enforce secure-by-default patterns (validation at boundaries, no hardcoded secrets,
scanned dependencies).

## When to Use / When NOT to Use

Use when:

- A security review is requested for code, an endpoint, or a service ("is this
  secure?", "security review before launch").
- Handling secrets, tokens, credentials, or PII in any component.
- A CVE appears in a dependency and triage is needed.

Do NOT use when:

- The request is a general correctness review — use `code-quality/code-review`.
- The request is SAST tooling setup — use `static-analysis` (this skill consumes its
  findings).
- An incident is already running — switch to `incident-response` immediately.

## Prerequisites & Assumptions

- `govulncheck` (Go), `pip-audit`/`uv audit` (Python), OWASP dependency-check or
  `nancy` (Java/Gradle) run in CI.
- Secrets are managed via environment/secrets manager (Vault, cloud secret store);
  CI uses OIDC federation over long-lived keys.
- CVSS v3.1 severity bands: Critical ≥ 9.0, High ≥ 7.0, Medium ≥ 4.0, Low < 4.0.

## Step-by-Step Workflow

1. **Enumerate the surface** — list entry points (HTTP handlers, RPC methods,
   CLI flags, file parsers) and trust boundaries; every entry point is untrusted
   until validated.
2. **Scan the taxonomy** — check each OWASP category below against the surface;
   record findings as `| file | CWE | OWASP | severity | description |`.
3. **Rank and fix in priority order** — RCE > data breach > auth bypass >
   information disclosure > DoS; one fix per change, each with a regression test.
4. **Run the dependency pass** — `govulncheck ./...` / `pip-audit` /
   dependency-check; upgrade to the minimum safe version, pin, and record the CVE
   in the changelog.
5. **Verify** — re-run SAST and the scanners; confirm zero new findings and that
   fixes did not break the threat model (e.g. authorization still enforced).

### Vulnerability taxonomy (OWASP 2021 → check items)

| #   | Category                | Key checks                                                                                                    |
| --- | ----------------------- | ------------------------------------------------------------------------------------------------------------- |
| A01 | Broken access control   | Per-object authz (IDOR), path traversal, missing role checks                                                  |
| A02 | Cryptographic failures  | No MD5/SHA-1/DES, AES-GCM or ChaCha20-Poly1305, Argon2id/bcrypt (cost ≥ 12) for passwords, `crypto/rand` only |
| A03 | Injection               | Parameterized SQL, no `exec.Command` with user input, template auto-escape, log injection                     |
| A05 | Misconfiguration        | CORS not `*` on authed routes, debug/pprof off in prod, security headers, TLS 1.2+                            |
| A06 | Vulnerable dependencies | Scanners in CI, CVE burn-down, transitive deps audited                                                        |
| A07 | Authn failures          | No hardcoded creds, CSRF on state changes, rate limiting/lockout, JWT `alg` pinned                            |
| A08 | Data integrity          | Bounded deserialization, `http.MaxBytesReader`, no untyped JSON into domain objects                           |
| A09 | Logging failures        | No secrets/PII in logs, audit events for auth/authz/data changes, errors not leaked to clients                |
| A10 | SSRF                    | Allowlist egress URLs, block metadata/file schemes, no blind redirects                                        |

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** validate and normalize all external input at the boundary; reject by
  default (allowlists over denylists).
- **MUST** source secrets from environment or a secrets manager; scan repos with
  gitleaks/trufflehog in CI; a leaked credential is revoked immediately, not just
  removed.
- **MUST** enforce authorization per object (ownership checks), not just per route.
- **MUST** use parameterized queries and prepared statements everywhere.
- **MUST** use `crypto/rand` for security values and Argon2id or bcrypt (cost ≥ 12)
  for passwords; AES-GCM/ChaCha20-Poly1305 for encryption.
- **MUST** run dependency scanners as blocking CI gates; Critical/High CVEs block
  release.
- **MUST NOT** use `math/rand` for tokens, `InsecureSkipVerify: true` in production,
  or return internal error details (stack traces, SQL) to clients.
- **MUST NOT** log secrets, full tokens, or PII; redact at the logging layer (see
  `observability`).

## Examples

Good — parameterized query + per-object authz (Go):

```go
func (s *Store) Order(ctx context.Context, userID, orderID string) (Order, error) {
	row := s.db.QueryRowContext(ctx,
		`SELECT id, total, status FROM orders WHERE id = $1 AND user_id = $2`,
		orderID, userID) // parameterized + ownership in the query
	var o Order
	if err := row.Scan(&o.ID, &o.Total, &o.Status); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return Order{}, ErrOrderNotFound // sanitized: no existence leak to others
		}
		return Order{}, fmt.Errorf("store order: %w", err)
	}
	return o, nil
}
```

Bad — string-built SQL and missing ownership check:

```go
q := fmt.Sprintf("SELECT * FROM orders WHERE id = '%s'", r.URL.Query().Get("id"))
rows, _ := db.Query(q) // SQL injection + IDOR + swallowed error
```

Why it fails: CWE-89 injection via the `id` parameter, CWE-639 IDOR because any
authenticated user can read any order, and the ignored error hides both.

Dependency triage (good):

```text
CVE-2026-1234 (CVSS 8.1) in github.com/golang-jwt/jwt/v4 < 4.5.2
→ upgrade to v4.5.2 (go get github.com/golang-jwt/jwt/v4@v4.5.2), pin, note in changelog.
```

## Checklist

- [ ] Every entry point validates input against an allowlist schema.
- [ ] Per-object authorization enforced; IDOR probes included in tests.
- [ ] No secrets in code, config files, or logs; scanner (gitleaks) passes.
- [ ] `crypto/rand` only; password hashing Argon2id/bcrypt ≥ cost 12.
- [ ] Dependency scanners green; no open Critical/High CVEs.
- [ ] Security headers and TLS 1.2+ verified on all HTTP endpoints.
- [ ] Error responses sanitized; audit events emitted for auth/authz/data changes.

## Common Pitfalls

- **Route-level authz confusion** — "the router checks the token" ≠ "the user owns
  the object"; always check both layers.
- **Secrets in test fixtures** — real credentials copied into tests; rotate and use
  synthetic values.
- **Scanner fatigue** — ignoring reports until they're wallpaper; baseline +
  burn-down (see `static-analysis`) keeps signal high.
- **Crypto DIY** — rolling custom MAC/encryption; use the standard library
  constructions only.

## References

- OWASP Top 10 (2021): https://owasp.org/www-project-top-ten/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- CWE Top 25: https://cwe.mitre.org/top25/
- govulncheck: https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
- NIST SP 800-53 Rev. 5: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
