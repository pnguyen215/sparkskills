---
name: python
description: 'Enforces modern enterprise Python — 3.14 baseline, pyproject.toml, uv/pip workflows, type hints validated by mypy, ruff lint/format, and packaging standards. Trigger with any "write/review/refactor Python code" request.'
---

# Python Engineering Standard

## Purpose

Define the rules every Python file must satisfy on the current stable baseline
(Python 3.14; 3.15 is the latest release line for new projects) — project layout,
typing, dependency management, linting, and packaging — so Python services are as
operable as their compiled cousins.

## When to Use / When NOT to Use

Use when:

- Writing, reviewing, or refactoring any `.py` file or `pyproject.toml`.
- Setting up a new Python service or library (layout, tooling, CI).
- Deciding typing, async, or dependency-injection patterns.

Do NOT use when:

- The task is Go or Java — use `language-specific/golang` / `language-specific/java`.
- The request is notebook-only data exploration with no repo artifact; apply PEP 8
  basics and move on.

## Prerequisites & Assumptions

- Python 3.14+ declared in `pyproject.toml` (`requires-python = ">=3.14"`).
- `pyproject.toml` is the single source of truth (PEP 621 metadata); `uv` or pip
  with lockfile for reproducible installs; no `setup.py`-only projects.
- `ruff` (lint + format), `mypy` (strict for new code), `pytest` per
  `testing/unit-testing`.

## Step-by-Step Workflow

1. **Scaffold** — `src/<package>/` layout, `pyproject.toml` with PEP 621 metadata,
   ruff + mypy + pytest configured (configs below), lockfile committed.
2. **Type everything** — full annotations on public functions; `mypy --strict`
   passing on new modules; `X | None` unions (PEP 604), built-in generics
   (`list[str]`, PEP 585).
3. **Handle failures** — custom exception classes per domain; never bare `except:`;
   catch narrow, wrap with context (`raise ServiceError(...) from exc`).
4. **Structure** — dataclasses/Pydantic models for structured data; protocols
   (PEP 544) for consumer-side interfaces; dependency injection via constructor
   arguments, not module-level singletons.
5. **Verify** — `ruff check`, `ruff format --check`, `mypy`, `pytest` green; then
   package build (`python -m build`) for libraries.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** declare all metadata and dependencies in `pyproject.toml` and commit a
  lockfile; unpinned floating installs are forbidden in CI.
- **MUST** fully type-hint public APIs; run `mypy` in CI (`strict = true` for new
  packages; document exclusions).
- **MUST** use `ruff` for lint and formatting (one formatter, no flake8/isort/
  black mix); rule selection follows `static-analysis`.
- **MUST** raise narrow, domain-specific exceptions and chain causes
  (`raise X from exc`); the generic `Exception` is never raised or caught.
- **MUST** use f-strings for interpolation and `pathlib.Path` over `os.path`.
- **SHOULD** use dataclasses (or Pydantic where validation is a requirement) over
  ad-hoc dicts for structured data crossing boundaries.
- **SHOULD** prefer `async`/`await` with `anyio`/`asyncio` for I/O concurrency;
  never mix blocking calls into async paths without `run_in_executor`.
- **SHOULD** manage secrets via environment/secrets manager (see `security`); never
  in code, tests, or config files.
- **MUST NOT** ship `print()` debugging; use the `logging` module (structured
  formatting per `observability`).
- **MUST NOT** use mutable default arguments (`def f(x=[])`) or module-level
  mutable singletons in libraries.
- **MUST NOT** pin dependencies with loose ranges in production (`requests` not
  `requests>=2,<3` without a lockfile).

## Examples

Good — typed, validated, injectable (Python 3.12+ syntax, runs on 3.14):

```python
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol


class OrderStore(Protocol):
    def find(self, order_id: str) -> dict[str, object]: ...


class OrderNotFoundError(Exception):
    """Raised when an order id is not visible to the caller."""


@dataclass(frozen=True, slots=True)
class OrderService:
    store: OrderStore
    logger: logging.Logger = field(compare=False)

    def cancel(self, order_id: str) -> None:
        try:
            record = self.store.find(order_id)
        except KeyError as exc:
            raise OrderNotFoundError(f"order {order_id!r} not found") from exc
        self.logger.info("order cancelled", extra={"order_id": order_id})
        _ = record  # domain-specific transition follows
```

Bad — the classic violations:

```python
def cancel(id, store, logger, retry=True, cache=None):  # untyped, mutable default
    try:
        store.find(id)
    except:  # bare except hides every failure
        pass
    print("cancelled " + id)  # print instead of logging
```

Why it fails: no types, silent failure swallowing, `print` instead of structured
logging, and the mutable default is a latent shared-state bug.

Tooling config (good, `pyproject.toml`):

```toml
[project]
requires-python = ">=3.14"

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S", "SIM"]

[tool.mypy]
strict = true
python_version = "3.14"
```

## Checklist

- [ ] `pyproject.toml` complete (PEP 621) with lockfile committed.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] `mypy` passes at the agreed strictness level.
- [ ] No bare `except`; every raise chains a cause where one exists.
- [ ] No `print()` in library/production code; logging configured.
- [ ] Public functions fully annotated; `Protocol`s define consumer-side interfaces.
- [ ] `pytest` green per `testing/unit-testing` standards.

## Common Pitfalls

- **Mutable defaults** — `def add(item, bucket=[])` shares state across calls; use
  `None` + create inside.
- **Requests without timeouts** — `requests.get(url)` hangs forever; always pass
  `timeout=` and handle it.
- **`except Exception` at module top level** — hides bugs from ops; catch at the
  boundary (`api-design` error model) with logging.
- **Pip freeze everywhere** — full freeze for apps is fine; libraries need range
  constraints plus tested minimums.

## References

- Python 3.14 release notes: https://docs.python.org/3.14/whatsnew/3.14.html
- PEP 621 — pyproject metadata: https://peps.python.org/pep-0621/
- Ruff documentation: https://docs.astral.sh/ruff/
- mypy strict mode: https://mypy.readthedocs.io/en/stable/strict_mode.html
