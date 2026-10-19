---
name: design-pattern
description: 'Applies and refactors toward canonical design patterns — strategy, functional options, adapter, factory, observer — with language-idiomatic implementations. Trigger with "which pattern fits this", "apply the options pattern", or "this type does too much".'
---

# Design Pattern

## Purpose

Choose and implement the right pattern for the problem at hand, in the idiom of the
target language, and recognize when an existing codebase should be refactored toward a
pattern. Patterns are contracts for managing change — not decoration.

## When to Use / When NOT to Use

Use when:

- Designing a new component with known variation points (pluggable renderers, multiple
  storage backends, configurable clients).
- Refactoring toward a pattern: telescoping constructors, switch-on-type, or a god
  struct are the usual triggers.
- Reviewing a design where someone asks "is there a pattern for this?".

Do NOT use when:

- The variation is hypothetical ("we might need it someday") — patterns cost upfront.
- The problem is naming or cohesion, not extensibility — see `code-quality/refactoring`.
- A language built-in already solves it (interfaces + functions cover most Go cases).

## Prerequisites & Assumptions

- Target language idioms come from `language-specific/golang|java|python`.
- Public API changes also follow `api-design` rules.
- The team prefers composition over inheritance in all three target languages.

## Step-by-Step Workflow

1. **Name the pressure** — write one sentence: what varies, and who forces the change?
   If nothing varies yet, stop.
2. **Match the pattern** — use the decision table below; prefer the simplest match.
3. **Design the seam** — define the minimal interface/abstract contract the caller
   needs; consumers of an interface should declare it (consumer-side interfaces in Go).
4. **Implement idiomatically** — functional options and small interfaces in Go;
   records/sealed types/strategy via lambdas in Java; protocols/dataclasses in Python.
5. **Test the seam** — each pattern variant gets its own tests plus one test proving
   the default path still works (`testing/unit-testing`).
6. **Document the trade-off** — record why the pattern was chosen in an ADR
   (`documentation/technical-writing`).

### Decision table

| Pressure (what varies)                   | Pattern                                                                   | Idiomatic shape                                         |
| ---------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------- |
| Construction with many optional settings | Functional Options                                                        | `NewClient(WithTimeout(5*time.Second), WithRetries(3))` |
| Algorithm swapped at runtime             | Strategy                                                                  | Interface + implementations, injected at construction   |
| Incompatible third-party interface       | Adapter                                                                   | Wrapper type translating calls                          |
| Object creation across packages          | Factory / constructor function                                            | `New*` functions; keep types valid by construction      |
| One-to-many notifications                | Observer                                                                  | Callbacks/channels (Go), event listeners (Java/Python)  |
| Open/closed on a closed set of variants  | Sealed hierarchy (Java) / sum-type style (Go: interface + private marker) | Exhaustive `switch` handled by linters                  |

## Enterprise Rules & Standards (MUST / SHOULD / MUST NOT)

- **MUST** justify every pattern introduction with the specific variation it manages;
  an ADR reference is expected for anything beyond Factory/Options.
- **MUST** prefer composition over inheritance; deep hierarchies are a finding.
- **MUST** keep interfaces small (1–3 methods) and defined by the consumer.
- **SHOULD** make constructors leave the object fully valid — no "call Setup() after
  New()"; constructor completeness is a hard rule.
- **SHOULD** accept human-readable inputs in options (`"5s"`, `"debug"`) and translate
  them in unexported parse helpers backed by named typed constants.
- **MUST NOT** use Singleton as a global service locator; inject dependencies instead.
- **MUST NOT** implement a pattern "for flexibility" with a single implementation and no
  second use case on the roadmap.

## Examples

Good — functional options (Go, with typed constants and delegated parsing):

```go
type RetryPolicy string

const (
	RetryNever  RetryPolicy = "never"
	RetryAlways RetryPolicy = "always"
)

// WithRetry sets the retry policy; accepts the named constants from [RetryPolicy].
func WithRetry(p RetryPolicy) Option {
	return func(c *client) error {
		v, err := parseRetry(p) // unexported parser owns the translation
		if err != nil {
			return err
		}
		c.retry = v
		return nil
	}
}
```

Bad — telescoping constructor:

```go
func NewClient(addr string, timeout int, retries int, debug int, tls int) *Client
```

Why it fails: positional booleans/ints are unreadable at call sites, every new option
breaks callers, and zero values are indistinguishable from "unset".

## Checklist

- [ ] One-sentence variation statement exists before the pattern is applied.
- [ ] The chosen pattern is the simplest match from the decision table.
- [ ] Interfaces are consumer-defined and ≤ 3 methods.
- [ ] Constructors produce fully valid objects; options validated with errors, not panics.
- [ ] Each variant is tested, including the default path.
- [ ] An ADR records the decision and rejected alternatives.

## Common Pitfalls

- **Pattern-itis** — AbstractFactoryVisitorBuilder code; every layer must pay rent.
- **Java-shaped Go** — inheritance hierarchies and getter/setter beans; use interfaces,
  functions, and composition instead.
- **Interface hoarding** — producer-side "for future mocks" interfaces with one method
  used once; declare interfaces where they are consumed.
- **Singleton escape hatch** — global state sneaks back in; use explicit injection.

## References

- Design Patterns (GoF) — catalog reference: https://refactoring.guru/design-patterns
- Effective Go — embedding and interfaces: https://go.dev/doc/effective_go#embedding
- Functional options pattern (medium of record for Go APIs): https://go.dev/doc/effective_go#redeclaration
