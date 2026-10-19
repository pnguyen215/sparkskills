---
name: golang
description: 'Enforces modern enterprise Go — Go 1.26+ modules and generics, context propagation, error wrapping with %w, slog structured logging, and concurrency safety. Trigger with any "write/review/refactor Go code" request or "is this idiomatic Go".'
---

# Go Engineering Standard

## Purpose

Define the rules every Go file in this organization must satisfy — project layout,
error handling, concurrency, logging, and API style — so that Go written by different
teams is indistinguishable in quality. The skill encodes the current stable toolchain
(Go 1.26+; the 1.27 line is current upstream) and modern idioms: modules, generics,
`slog`, `context`, and error wrapping.

## When to Use / When NOT to Use

Use when:

- Writing, reviewing, or refactoring any `.go` file, `go.mod`, or Go CI job.
- Designing a Go library API (options, interfaces, error values).
- Onboarding a service to the shared logging/concurrency standards.

Do NOT use when:

- The task is Java or Python — use `language-specific/java` or `language-specific/python`.
- The task is cross-language (REST shape, pipelines) — use the owning category skill;
  this skill covers Go-specific expression of those rules only.

## Prerequisites & Assumptions

- Go 1.26+ (module `go` directive may state the minimum supported version; CI tests
  the two most recent minor releases).
- `golangci-lint` v2 per `static-analysis`; `govulncheck` in CI per `security`.
- Standard layout assumed: `cmd/<binary>/`, `internal/`, `pkg/` (only for truly
  public libraries), `api/` for proto/OpenAPI assets.

## Step-by-Step Workflow

1. **Scaffold** — `go mod init`, create `cmd/` + `internal/`, add `.golangci.yml`
   (from `static-analysis`), add `Makefile` targets `build/test/lint/vet`.
2. **Design packages** — small packages named by what they provide (`package throttle`
   not `package util`); consumer-side interfaces; constructors return fully valid
   values.
3. **Write functions** — `context.Context` first parameter for I/O paths; guard
   clauses; errors wrapped with `%w` and lowercase, punctuation-free messages.
4. **Handle concurrency** — share memory by communicating; every goroutine has an
   owner that guarantees termination (context, done channel, or WaitGroup).
5. **Log observably** — `log/slog` with typed attributes; no `fmt.Println` debugging
   residue (rule details in `observability`).
6. **Verify** — `go vet`, `golangci-lint run`, `go test -race ./...`, table-driven
   tests per `testing/unit-testing`, `go build ./...` green.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** wrap errors with context: `fmt.Errorf("parse config: %w", err)`; sentinel
  errors (`var ErrNotFound = errors.New(...)`) or typed errors for caller decisions;
  `errors.Is`/`errors.As` at boundaries. Never compare error strings.
- **MUST** pass `context.Context` as the first parameter of any function performing
  I/O, and never store contexts in structs except for request-scoped types.
- **MUST** use `log/slog` with typed key-value attributes for logging; the `context`
  variant (`slog.InfoContext`) in request paths.
- **MUST** make every goroutine terminable: launch with an owner-tracked
  `context.Context`, `done` channel, or `WaitGroup`; `go test -race` is a required
  gate for concurrent code.
- **MUST** validate inputs at package boundaries; return `(T, error)`, never panics,
  for expected failures. Panic only for programmer bugs (impossible states).
- **MUST** keep `go.mod` tidy: minimal direct dependencies, `go mod tidy` clean, no
  `replace` directives in published modules.
- **SHOULD** use generics for type-safe containers/helpers; do not force generics
  where an interface or concrete type is simpler.
- **SHOULD** prefer `any` over `interface{}` (Go 1.18+), `min`/`max` builtins
  (1.21+), loop-var semantics of 1.22+ (no `v := v` copies), and `for range int`
  (1.22+) for counted loops.
- **SHOULD** use `t.Context()` in tests (Go 1.24+) for cancellation-aware test code.
- **MUST NOT** use `interface{}`/`any` to dodge type safety in exported APIs.
- **MUST NOT** use `math/rand` for security values (`crypto/rand`), or MD5/SHA-1 for
  integrity — see `security`.
- **MUST NOT** ignore errors with `_` in production code paths.
- **MUST NOT** call `os.Exit` or `log.Fatal` inside libraries; return errors and let
  `main` decide.

## Examples

Good — idiomatic service call chain (compiles under Go 1.26):

```go
package orders

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"
)

var ErrOrderNotFound = errors.New("order not found")

type Order struct {
	ID     string
	Status string
}

// Cancel marks a confirmed order as cancelled; other statuses are rejected.
func (o *Order) Cancel() error {
	if o.Status != "confirmed" {
		return fmt.Errorf("cancel order %s: status %q is not cancellable", o.ID, o.Status)
	}
	o.Status = "cancelled"
	return nil
}

type Store interface {
	FindOrder(ctx context.Context, id string) (Order, error)
}

type Service struct {
	store  Store
	logger *slog.Logger
}

func NewService(store Store, logger *slog.Logger) *Service {
	return &Service{store: store, logger: logger}
}

// Cancel cancels the order with the given id before its cutoff time.
func (s *Service) Cancel(ctx context.Context, id string) error {
	const op = "orders.Cancel"

	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	order, err := s.store.FindOrder(ctx, id)
	switch {
	case errors.Is(err, ErrOrderNotFound):
		return fmt.Errorf("%s: %w", op, err)
	case err != nil:
		return fmt.Errorf("%s: find order: %w", op, err)
	}

	if err := order.Cancel(); err != nil {
		return fmt.Errorf("%s: cancel order %s: %w", op, id, err)
	}

	s.logger.InfoContext(ctx, "order cancelled",
		slog.String("order_id", id))
	return nil
}
```

Bad — the classic violations, all in one function:

```go
func (s *Service) Cancel(id string) error {
	order, _ := s.store.FindOrder(nil, id) // ignored error, nil context
	if order.ID == "" {                    // sentinel check by field, not error
		fmt.Println("not found")           // fmt instead of slog
	}
	go s.notify(id)                        // unowned goroutine, race-prone
	return nil
}
```

Why it fails: swallowed error breaks `errors.Is` handling upstream; `nil` context
panics in store implementations; `fmt.Println` is not structured; the goroutine can
outlive the request and races on shared state.

## Checklist

- [ ] `go vet ./...` and `golangci-lint run` clean.
- [ ] `go test -race ./...` green for all packages.
- [ ] All errors wrapped with `%w`; sentinels/typed errors for caller decisions.
- [ ] `context.Context` flows through every I/O call; none stored in long-lived structs.
- [ ] Logging via `slog` with typed attributes; no `fmt.Println`/`log.Printf`.
- [ ] Every goroutine owned and terminable; channels documented sender→receiver.
- [ ] `govulncheck ./...` passes (see `security`).
- [ ] `go mod tidy` leaves no diff.

## Common Pitfalls

- **Nil-context calls** — `context.Background()` with a wiring comment is the
  honest stand-in when no caller context exists yet; `nil` never is.
- **Loop-variable paranoia on modern Go** — `v := v` copies are unnecessary since
  Go 1.22; remove them, keep them only in generics weirdness with proof.
- **time.After in loops/selects** — leaks timers until fire; use `time.NewTimer`
  with `Reset` for recurring waits.
- **Error-message capitalization** — Go errors read as sentences mid-flow;
  `"Parse config: ..."` and trailing punctuation are wrong.
- **init() abuse** — implicit wiring hides dependencies; construct explicitly.

## References

- Effective Go: https://go.dev/doc/effective_go
- Go documentation — doc comments: https://go.dev/doc/comment
- log/slog package docs: https://pkg.go.dev/log/slog
- Go Code Review Comments (official): https://go.dev/wiki/CodeReviewComments
- Go 1.26 release notes: https://go.dev/doc/go1.26
