---
name: performance
description: 'Profiles and optimizes system performance — CPU/memory profiling, benchmark methodology, allocation analysis, and p99 latency work with measurement-first discipline. Trigger with "this is slow", "profile this service", "optimize this hot path", or "benchmark before merging".'
---

# Performance

## Purpose

Turn "it feels slow" into a measured, fixed, and regression-guarded engineering task.
The skill fixes the methodology (profile before optimizing), the toolchain per
language, the benchmark hygiene rules, and the latency-analysis workflow for p99/p999
work.

## When to Use / When NOT to Use

Use when:

- A service or function is slow and the cause is unknown ("this is slow", "CPU is
  pegged", "p99 regressed").
- A hot path needs optimization with proof ("optimize this loop", "cut
  allocations").
- Adding a performance regression gate for a critical component.

Do NOT use when:

- The problem is missing observability (you cannot see what is slow) — set up
  `observability` first; profiling needs a target.
- The slowness is a capacity/planning issue (traffic doubled, needs scaling) —
  that is architecture and SRE planning, not code optimization.

## Prerequisites & Assumptions

- Go: built-in `testing`, `pprof`, `benchstat`; Java: JFR + async-profiler,
  JMH for benchmarks; Python: cProfile/py-spy, pytest-benchmark, `timeit`.
- Benchmarks run on quiet machines/CI runners with controlled resources;
  comparisons use statistical tooling (`benchstat`), never single runs.
- Representative workload or trace exists to profile against.

## Step-by-Step Workflow

1. **Measure first** — capture a baseline: CPU profile, memory profile, and
   allocation profile (Go) or flame graph (Java/Python) under realistic load.
   No baseline, no optimization.
2. **Localize** — identify the top cost centers; state the expected win of fixing
   each ("froto — 30% of CPU in JSON marshaling").
3. **Hypothesize and fix one thing** — one optimization per change: pre-allocation,
   buffer reuse, algorithm change, batched I/O. Keep it behavior-preserving
   (`code-quality/refactoring`).
4. **Re-measure** — rerun the same benchmark/profile; `benchstat` the before/after
   with enough iterations (≥10 runs); report the delta with variance.
5. **Guard the win** — keep the benchmark in the repo (`testing/unit-testing`
   benchmark hooks) and add it to the CI comparison for critical paths.
6. **Document** — record what was tried and rejected (ADR if architectural; the
   change log line otherwise).

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** profile before optimizing; unmeasured "optimizations" are rejected in
  review regardless of plausibility.
- **MUST** compare benchmarks statistically (benchstat or ≥10-run medians with
  variance), never single-run numbers.
- **MUST** keep benchmarks representative: real data shapes and sizes, not
  microbenchmarks of synthetic strings.
- **MUST** verify behavior is unchanged after optimization (tests green,
  outputs identical).
- **SHOULD** target allocations first in Go hot paths (escape analysis,
  pre-sized slices/maps, `sync.Pool` for reusable buffers with measured wins).
- **SHOULD** measure tail latency (p99/p999), not just the mean; means hide
  queueing and GC pauses.
- **MUST NOT** optimize without a regression guard — an unmeasured win
  disappears with the next refactor.
- **MUST NOT** trade correctness or security for speed (unvalidated caching,
  disabling TLS) without an explicit, documented decision.

## Examples

Good — benchmark with representative input (Go, compiles):

```go
var orderJSON = []byte(`{"id":"o-123","total":4200,"items":[{"sku":"A-1","qty":2}]}`)

func BenchmarkParseOrder(b *testing.B) {
	b.ReportAllocs()
	for b.Loop() { // Go 1.24+: b.Loop replaces the classic range loop
		if _, err := ParseOrder(orderJSON); err != nil {
			b.Fatal(err)
		}
	}
}
```

```sh
go test -bench=ParseOrder -benchmem -count=10 ./... | benchstat - old.txt new.txt
```

Bad — the single-run microbenchmark "proving" the rewrite:

```text
Ran the loop once on my laptop while a build was running: 1.2ms vs 1.5ms,
rewrote everything to unsafe pointer tricks.
```

Why it fails: one noisy run, unrepresentative input, and a correctness hazard —
none of which would survive a benchstat comparison.

## Checklist

- [ ] Baseline profile captured and attached to the task.
- [ ] Top cost centers named with expected win percentages.
- [ ] One optimization per change; tests green after each.
- [ ] Before/after compared with `benchstat` (or ≥10-run medians).
- [ ] Benchmark committed and wired into CI comparison for critical paths.
- [ ] No security or correctness trade-offs without a documented decision.

## Common Pitfalls

- **Premature micro-optimization** — rewriting clean code for imagined wins; the
  profile usually points elsewhere.
- **Benchmarker's bias** — optimizing what is easy to benchmark, not what is slow
  in production; profile with real traces.
- **GC whack-a-mole (Go)** — "fixing" allocations with `sync.Pool` everywhere
  before checking the GC pause share of the profile.
- **Ignoring the tails** — optimizing median latency while p99 (the pager) is
  dominated by lock contention.

## References

- Go pprof documentation: https://pkg.go.dev/net/http/pprof
- benchstat: https://pkg.go.dev/golang.org/x/perf/cmd/benchstat
- JMH (Java Microbenchmark Harness): https://github.com/openjdk/jmh
- Python profiling: https://docs.python.org/3/library/profile.html
