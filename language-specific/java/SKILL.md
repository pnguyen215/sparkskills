---
name: java
description: 'Enforces modern enterprise Java — Java 21/25 LTS records, sealed types, streams, text blocks, virtual threads, and immutable-by-default design with Maven/Gradle. Trigger with any "write/review/refactor Java code" request.'
---

# Java Engineering Standard

## Purpose

Define the rules every Java file must satisfy on the current LTS baseline (Java 25
LTS; Java 21 LTS remains the supported minimum) — modern language features,
immutability-first API design, exception discipline, and build/tooling conventions
for Maven and Gradle.

## When to Use / When NOT to Use

Use when:

- Writing, reviewing, or refactoring any `.java` file, `pom.xml`, or `build.gradle`.
- Choosing between Java idioms on the LTS baseline (records vs. Lombok, exceptions
  vs. result types, virtual threads vs. pools).
- Migrating an older service toward the LTS baseline.

Do NOT use when:

- The task is Go or Python — use `language-specific/golang` / `language-specific/python`.
- The task is framework-specific (Spring conventions) beyond the language rules here;
  apply those framework guides on top of this baseline.

## Prerequisites & Assumptions

- Java 21 LTS minimum, Java 25 LTS target; `--release` set accordingly in the build.
- One build tool per repository: Maven (preferred for enterprise consistency) or
  Gradle with version catalogs; toolchains pin the JDK.
- Checkstyle/SpotBugs configured per `static-analysis`; JUnit 5 for tests.

## Step-by-Step Workflow

1. **Scaffold** — set `<maven.compiler.release>21</maven.compiler.release>` (or the
   Gradle `toolchain`), enable strict warnings (`-Werror` equivalent), add the
   formatter and SpotBugs plugins.
2. **Model data** — records for DTOs/value objects; sealed interfaces for closed
   type hierarchies; builder pattern (hand-rolled or records with compact
   constructors validating invariants).
3. **Handle failures** — checked exceptions only at recoverable domain boundaries;
   unchecked (`IllegalArgumentException`, custom `RuntimeException`) for programmer
   errors; never swallow; wrap with context and cause.
4. **Write concurrent code** — prefer virtual threads (Java 21+) for I/O-bound
   concurrency (`Executors.newVirtualThreadPerTaskExecutor()`); structured scopes
   where available; immutable state wherever possible.
5. **Verify** — `mvn verify` (or `gradle check`) green: compile, Checkstyle,
   SpotBugs, unit tests, and Javadoc lint.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** target the LTS baseline in the build (`--release 21` or `25`) and keep
  dependencies managed (BOM/versions catalog); no version ranges.
- **MUST** use records for data carriers and sealed interfaces + pattern-matching
  `switch` for closed hierarchies; classes with mutable state must document their
  thread-safety explicitly in Javadoc.
- **MUST** make value objects immutable: `final` fields, no setters, defensive
  copies for collections and dates in and out.
- **MUST** handle or declare every checked exception; never `catch (Exception e) {}`
  or `printStackTrace()`; wrap with context: `throw new OrderException("cancel " + id,
cause)`.
- **MUST** close resources with try-with-resources (or `AutoCloseable` ownership).
- **MUST** use `java.util.Optional<T>` for possibly-absent return values in APIs
  (not for fields/parameters), and `var` for obvious local types only.
- **SHOULD** prefer streams for transformation pipelines; fall back to loops when
  the stream is less clear (deeply nested flatMaps).
- **SHOULD** use text blocks for multi-line strings (SQL, JSON fixtures).
- **MUST NOT** use `null` as a domain value (Optional/typed sentinels instead);
  `@Nullable` annotations where null is forced by an external contract.
- **MUST NOT** use reflection or `sun.*`/internal APIs in application code.
- **MUST NOT** log passwords, tokens, or PII — redact via accessor design (see
  `observability`).

## Examples

Good — modern, immutable, exception-safe (Java 21+, compiles):

```java
package com.example.orders;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public record Order(String id, Instant createdAt, List<Item> items) {
    public Order {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("id must not be blank");
        }
        items = List.copyOf(items); // defensive, immutable copy
    }

    public Optional<Item> findItem(String sku) {
        return items.stream()
            .filter(i -> i.sku().equals(sku))
            .findFirst();
    }
}

sealed interface OrderEvent permits OrderCreated, OrderCancelled {}

record OrderCreated(String orderId, Instant at) implements OrderEvent {}

record OrderCancelled(String orderId, Instant at, String reason) implements OrderEvent {}
```

Bad — mutable bean with swallowed failure:

```java
public class Order {
    private String id;               // mutable DTO, no validation
    private List<Item> items;        // leaks internal list
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public List<Item> getItems() { return items; }
}

try {
    orderService.cancel(id);
} catch (Exception e) {
    e.printStackTrace();             // swallowed, no context, no rethrow
}
```

Why it fails: the bean invites invalid states and external mutation; the catch block
hides the failure and provides no cause chain or recovery.

## Checklist

- [ ] `--release` / toolchain pinned to an LTS (21 or 25); build green with strict
      warnings.
- [ ] Records/sealed types used for data and closed hierarchies; no Lombok-only
      beans for new code.
- [ ] No swallowed exceptions; every throw carries context and cause.
- [ ] Resources in try-with-resources; no manual `close()` in `finally` leftovers.
- [ ] Public APIs return `Optional` for absent values; no `null` returns.
- [ ] Checkstyle + SpotBugs pass per `static-analysis`.
- [ ] Javadoc present on every public type/method (see `documentation/api-documentation`).

## Common Pitfalls

- **Streams for side effects** — `forEach` mutating external state; use a loop or
  redesign as a pure transformation.
- **Optional parameters** — `Optional` in arguments burdens callers; overload or
  use a builder.
- **equals/hashCode drift** — hand-writing both on mutable classes; records
  generate correct ones, prefer them.
- **Virtual threads for CPU work** — they help I/O-bound tasks only; CPU-bound
  work still needs sized pools with measurements (`performance`).

## References

- Java SE 25 (LTS) documentation: https://docs.oracle.com/en/java/javase/25/
- Java version history / LTS roadmap: https://en.wikipedia.org/wiki/Java_version_history
- Javadoc tool conventions: https://www.oracle.com/technical-resources/articles/java/javadoc-tool.html
- Java records (JEP 395) and sealed classes (JEP 409): https://openjdk.org/jeps/409
