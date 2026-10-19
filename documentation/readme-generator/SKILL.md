---
name: readme-generator
description: 'Generates a complete README.md (and GETTING_STARTED.md on request) for a project from its actual code and configuration. Trigger with "write a README for this repo", "our README is outdated", or "create a getting-started guide".'
---

# README Generator

## Purpose

Produce a README that a new developer can go from clone to running code with, and keep
it truthful by deriving every claim from the repository's real files. For Go libraries
and services it can additionally produce a GETTING_STARTED.md tutorial.

## When to Use / When NOT to Use

Use when:

- Creating a README for a new repository, or rewriting a stale one.
- Someone asks "write a getting-started guide" or "our README doesn't match reality".
- A project is being open-sourced or handed to another team.

Do NOT use when:

- The request is API reference material — use `api-documentation`.
- The request is ADRs, runbooks, or deep-dive articles — use `technical-writing`.
- The repository has no runnable artifact yet; document after the quickstart works.

## Prerequisites & Assumptions

- Repository access is available; every claim must be derived from the actual code,
  manifests (`go.mod`, `pom.xml`, `pyproject.toml`), and CI configuration.
- The README is written in Markdown, English, with a working Quick Start that is
  executed to verify before delivery.
- Code samples compile and run; error handling is shown, never swallowed with `_`.

## Step-by-Step Workflow

1. **Scan the repository** — read the manifest, entry points, Makefile targets, CI
   config, and LICENSE. List features from code, not from aspiration.
2. **Verify the quickstart** — run the install + minimal usage commands yourself; the
   Quick Start is only done when it exits successfully.
3. **Draft the README** using the structure below, filling every section from evidence.
4. **Add usage examples** — 3–5 modular scenarios covering normal operations, each with
   expected output as a comment.
5. **Self-review** — check badges match reality, commands match the Makefile, versions
   match the manifest, and no placeholder text remains.
6. **Maintain** — README updates ship in the same PR as the change that invalidates
   them (new flag, renamed target, changed install).

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** verify every command in the README by running it before delivery.
- **MUST** keep the Quick Start under ~10 lines and runnable as-is.
- **MUST** derive features and compatibility claims from code/manifests; mark anything
  unverified explicitly.
- **MUST** state language/tool minimums exactly as enforced (e.g. `go 1.26` from
  `go.mod`, `python 3.14` from `pyproject.toml`).
- **SHOULD** include: badges (build, release, license), a table of configuration
  options, and a Contributing link.
- **MUST NOT** include placeholder text, unrunnable snippets, or instructions that
  contradict the Makefile/CI.
- **MUST NOT** claim tests/coverage/status the repo does not have.

### README structure

```text
1. Title + one-paragraph value proposition
2. Badges (CI, release, license)
3. Features (bulleted, from code)
4. Installation (prerequisites + command)
5. Quick Start (minimal runnable snippet + expected output)
6. Usage Examples (3–5 scenarios)
7. Configuration / API highlights (table)
8. Testing & Development (make targets)
9. Contributing (link to CONTRIBUTING.md) & License
```

## Examples

Good — Quick Start with verified output:

````markdown
```go
package main

import (
	"fmt"
	"log"

	"github.com/example/orderlint"
)

func main() {
	findings, err := orderlint.CheckFile("order.json")
	if err != nil {
		log.Fatalf("check failed: %v", err)
	}
	for _, f := range findings {
		fmt.Printf("%s: %s\n", f.Rule, f.Message)
	}
}
```

Expected output: `MISSING_TAX_ID: field taxId is required for region EU`
````

Bad — untested snippet:

```markdown
## Quick Start

Just run the tool, it's easy! (no command, no output, unverifiable)
```

Why it fails: "just run" is not a command; a new user cannot reproduce anything.

## Checklist

- [ ] Install and Quick Start commands executed successfully before delivery.
- [ ] Every feature listed is visible in the code or manifest.
- [ ] Versions/prerequisites match `go.mod` / `pom.xml` / `pyproject.toml`.
- [ ] Make targets referenced exist in the Makefile.
- [ ] Code samples handle errors; none swallow errors with `_`.
- [ ] No unfilled template markers or filler text anywhere in the document.

## Common Pitfalls

- **Aspirational features** — listing capabilities the code does not have yet.
- **Bit-rot commands** — install steps referencing old package managers; CI can check
  README commands in a nightly job.
- **Wall of text** — burying the Quick Start below philosophy paragraphs; lead with
  running code.
- **Duplicate tutorials** — README duplicating GETTING_STARTED content; the README
  links to it and stays lean.

## References

- Make a README: https://www.makeareadme.com/
- Standard Readme spec: https://github.com/RichardLitt/standard-readme
- Go doc comments (for example style): https://go.dev/doc/comment
