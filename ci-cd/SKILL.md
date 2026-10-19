---
name: ci-cd
description: 'Designs delivery pipelines — quality-gated build, test, release, and deployment stages with SemVer automation, artifact provenance, and rollback. Trigger with "set up CI", "our pipeline is slow", "cut a release", or "add a quality gate".'
---

# CI/CD

## Purpose

Turn every merge into a releasable, traceable artifact. The skill defines the
pipeline stages, the blocking quality gates, versioning automation (SemVer +
Conventional Commits), environment promotion, and rollback — so releases are routine
instead of heroic.

## When to Use / When NOT to Use

Use when:

- Creating or refactoring a CI/CD pipeline for a repository.
- Cutting a release, hotfix, or rollback ("cut a release", "ship version x").
- A pipeline stage is flaky, slow, or bypassed and needs redesign.

Do NOT use when:

- Writing the tests that run in the pipeline — see the `testing/*` skills.
- Responding to a production incident — use `incident-response`; pipeline changes
  wait until the incident closes.

## Prerequisites & Assumptions

- Trunk-based development with short-lived branches (see `git-workflow`).
- Conventional Commits + SemVer; release automation derives the next version from
  commit types (feat → minor, fix → patch, `BREAKING CHANGE:` → major).
- CI has least-privilege access: OIDC federation to cloud, no long-lived static
  credentials.

## Step-by-Step Workflow

1. **Define stages** — lint → unit → build → integration → security scan →
   package → deploy (staging) → e2e → promote (prod). PR runs the fast prefix;
   post-merge runs the rest.
2. **Set gates** — every stage is blocking; only documented, time-boxed waivers
   (issue-linked) bypass a gate.
3. **Automate versioning** — on merge to main, compute the next SemVer from
   Conventional Commits, tag, build the artifact, generate release notes from
   commits.
4. **Promote, don't rebuild** — the exact artifact tested in staging is the one
   deployed to production (immutable artifact promotion); never rebuild per env.
5. **Deploy safely** — rolling or canary with health checks; automated rollback on
   failed health checks or SLO burn (rollback target = previous artifact).
6. **Provenance** — sign artifacts (Sigstore/cosign for containers); record commit
   SHA → artifact digest mapping in the release notes.

## Enterprise Rules & Standards (MUST / MUST NOT)

- **MUST** keep the PR gate < 10 minutes; all slower stages run post-merge.
- **MUST** make every quality gate blocking; green-to-red transitions require the
  change owner to fix or waive with an issue link.
- **MUST** version every release with SemVer; tag format `vMAJOR.MINOR.PATCH`;
  release notes generated from Conventional Commits.
- **MUST** promote the identical artifact through environments (digest, not rebuild).
- **MUST** support one-command rollback to the previous artifact, tested quarterly.
- **MUST** use ephemeral, least-privilege CI credentials (OIDC); no secrets in
  pipeline logs (masked and audited).
- **SHOULD** deploy during business hours with monitoring on-call aware — fast
  rollbacks beat midnight deploys.
- **SHOULD** cache dependencies aggressively (module/content caches) with a weekly
  cache-bust job to detect upstream rot.
- **MUST NOT** deploy from a developer workstation; deploys only from CI.
- **MUST NOT** mark a release green while any scanner gate fails.

## Examples

Good — pipeline skeleton (GitHub Actions sketch):

```yaml
jobs:
  lint:
    {
      runs-on: ubuntu-latest,
      steps: [uses: actions/checkout@v4, run: make lint],
    }
  unit: { needs: lint, steps: [run: make test-unit] } # <10 min gate
  build: { needs: unit, steps: [run: make build, upload-artifact] }
  scan: { needs: build, steps: [run: make scan] } # govulncheck, SAST
  staging:
    {
      needs: [build, scan],
      environment: staging,
      steps: [run: make deploy ENV=staging],
    }
  prod: { needs: staging, environment: production, steps: [run: make promote] } # same digest
```

Bad — the snowflake release:

```text
A release is: someone runs `git tag` on their laptop, pushes a Docker build
from their machine, and pastes the tag into the deploy script by hand.
```

Why it fails: no reproducibility, no provenance, no rollback target, and the
laptop is a single point of failure.

Rollback (good):

```sh
make release-rollback VERSION=v1.8.2   # re-points traffic to the previous
                                       # immutable artifact + verifies health
```

## Checklist

- [ ] Stages ordered lint → unit → build → scan → package → staging → prod.
- [ ] PR gate < 10 min; all gates blocking with waiver policy.
- [ ] Version + tag + release notes automated from Conventional Commits.
- [ ] Artifact digest promoted (no per-env rebuilds).
- [ ] Rollback command exists, is documented, and was tested this quarter.
- [ ] CI credentials are OIDC/ephemeral; secrets masked in logs.
- [ ] Artifacts signed; commit-to-digest provenance recorded in release notes.

## Common Pitfalls

- **Flaky pipeline syndrome** — the "rerun until green" pipeline; a red rerun must
  be explainable, otherwise the stage is deleted or fixed.
- **Config drift between envs** — env differences belong in config values, not
  different build outputs.
- **Manual hotfix branches** — bypassing the pipeline under pressure; hotfixes use
  the same pipeline with an expedited path, never a side door.
- **Caching forever** — a cached broken dependency for months; schedule busts.

## References

- Semantic Versioning: https://semver.org/
- Conventional Commits: https://www.conventionalcommits.org/
- Trunk-Based Development: https://trunkbaseddevelopment.com/
- Sigstore artifact signing: https://docs.sigstore.dev/
