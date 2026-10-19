# Skills

Enterprise-grade [Claude agent skills](https://code.claude.com/docs/en/skills) for
software engineering: code quality, design, documentation, language standards,
testing, security, delivery, and operations.

Each skill is a folder with a single `SKILL.md` (plus optional `references/`,
`examples/`, `templates/`, `scripts/` subfolders) that Claude loads on demand when
your request matches the skill's trigger phrases.

## Structure

```
.
├── api-design/            REST/gRPC conventions, versioning, error models
├── ci-cd/                 Pipelines, release management, quality gates
├── code-quality/          code-review · refactoring · static-analysis
├── database/              Schema design, migrations, query optimization
├── design/                design-pattern · design-system
├── documentation/         api-documentation · readme-generator · technical-writing
├── git-workflow/          Branching, Conventional Commits, PR discipline
├── incident-response/     Severity triage, stabilization, postmortems
├── language-specific/     golang · java · python
├── observability/         Logging, metrics, tracing, SLOs
├── performance/           Profiling, benchmarking, p99 latency
├── security/              OWASP audits, secrets, dependency scanning
├── testing/               unit-testing · test-strategy · test-coverage
├── scripts/               validate.py (repository validator)
└── templates/             SKILL.template.md (scaffold source)
```

## Using skills

Skills are discovered by trigger phrases in the `description` frontmatter. Ask
naturally:

- _"Review this PR"_ → `code-quality/code-review`
- _"This query is slow"_ → `database`, with `performance` if profiling is needed
- _"Write an ADR for this decision"_ → `documentation/technical-writing`
- _"Is this idiomatic Go?"_ → `language-specific/golang`

With the Claude Code CLI you can also invoke skills directly:

```sh
claude /code-review            # if exposed as a command in your setup
```

or reference the skill folder by path in your project's skills directory
(`.claude/skills/`):

```sh
git clone https://github.com/pnguyen215/sparkskills ~/.claude/skills/pnguyen215
```

## Naming conventions

- Folders and skills are `kebab-case`, one skill per folder, mirrored by the
  `name:` frontmatter.
- Skill names: ≤ 64 chars, lowercase letters, digits, hyphens.
- `description:` frontmatter: 20–1024 chars, states **what** the skill does and
  **when** to trigger it with concrete phrases.

## Validation

Every SKILL.md is machine-validated (frontmatter, name/description limits,
required sections, no placeholders). Run locally:

```sh
make help        # list targets
make check       # lint + validate (CI quality gate)
make tree        # print the structure
make new-skill NAME=testing/contract-testing   # scaffold a new skill
make clean
```

CI runs `make check` on every PR; a PR that adds or edits a skill must pass it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: scaffold with
`make new-skill`, fill every required section with concrete and verifiable rules,
keep SKILL.md under 500 lines (bulk goes to `references/`), and open a PR with a
Conventional Commit.

## License

MIT — see [LICENSE](LICENSE).
