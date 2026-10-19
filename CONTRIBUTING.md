# Contributing

Thanks for improving the skills library. This repository holds production-grade
agent skills, so contributions follow the same enterprise rules the skills
themselves teach.

## Ground rules

- One skill per folder, folder name in `kebab-case`, matching the `name:` field.
- English only; active voice; no unfilled template markers (`{{...}}`,
  `REPLACE:`) or filler text may survive in a merged PR.
- Concrete and verifiable over vague: every rule must be checkable by review,
  tooling, or a test.
- SKILL.md stays under 500 lines; move bulk material (long tables, extended
  examples) into `references/` or `examples/`.
- Do not duplicate rules across skills: state a rule once in its owning skill and
  cross-reference it from others.

## Adding a new skill

1. Check the [README structure table](README.md#structure) for the right
   category; if none fits, propose a new top-level category in your issue and
   justify it in one or two sentences.
2. Scaffold:

   ```sh
   make new-skill NAME=<category>/<skill-name>
   ```

3. Fill every section of the generated `SKILL.md`. The required sections are:
   Purpose, When to Use / When NOT to Use, Prerequisites & Assumptions,
   Step-by-Step Workflow, Enterprise Rules & Standards (MUST / SHOULD /
   MUST NOT), Examples, Checklist, Common Pitfalls, References.
4. Make the `description` frontmatter state concrete trigger phrases — this is
   how the agent decides to load your skill.
5. Validate locally:

   ```sh
   make check
   ```

6. Open a pull request titled with a Conventional Commit type, e.g.
   `feat(testing): add contract-testing skill`.

## Editing an existing skill

- Keep the change minimal and in one skill; cross-reference instead of copying.
- If a rule moves between skills, update every referencing skill in the same PR.
- Version examples to current stable toolchains (Go 1.26+, Java 21/25 LTS,
  Python 3.14+); outdated examples are bugs — fix them like code.

## Commit and PR rules

- Conventional Commits: `feat`, `fix`, `docs`, `refactor`, `test`, `chore` with
  an optional scope (`feat(golang): ...`).
- PRs ≤ 400 changed lines; larger contributions are split.
- `make check` must pass in CI; the PR description lists what you validated by
  hand.

## Local validation

```sh
make help      # targets
make lint      # markdown style (markdownlint when installed, fallback included)
make validate  # SKILL.md structure/frontmatter/placeholders
make tree      # repo structure
```

## Reporting issues

Open an issue with: the skill (or gap) involved, the concrete scenario where the
guidance failed or is missing, and — if possible — the rule/checklist line you
expected to exist.
