---
name: design-system
description: 'Establishes and enforces UI consistency rules — design tokens, component API contracts, accessibility, and versioned component libraries. Trigger with "create design tokens", "is this component consistent", or "audit our UI for a11y".'
---

# Design System

## Purpose

Keep user interfaces consistent by managing shared decisions — tokens (color, spacing,
typography), component contracts, and accessibility rules — as versioned code instead of
tribal knowledge. The skill defines the token architecture, the component API rules, and
the audit checklist that keeps third-party UI work on-system.

## When to Use / When NOT to Use

Use when:

- Creating or refactoring shared UI components, tokens, or themes.
- Onboarding a new surface to the design system, or auditing an existing one.
- Reviewing a UI PR for accessibility and consistency violations.

Do NOT use when:

- The work is one-off application code with no shared component involvement.
- The question is backend API shape — use `api-design`.
- A designer's visual decision is disputed and not encoded in tokens; escalate to the
  design owner instead of relitigating taste in code review.

## Prerequisites & Assumptions

- A component library or frontend codebase exists (React, Vue, Web Components, or
  server-rendered HTML).
- WCAG 2.2 AA is the accessibility floor.
- Tokens are exported as code (CSS variables, TypeScript objects, or theme packages)
  and consumed by reference — never re-declared in feature code.

## Step-by-Step Workflow

1. **Token audit** — inventory colors, spacing, radii, shadows, type sizes, and motion
   in the current UI; map each raw value to a semantic token.
2. **Define the token layers** — primitives (`color.blue.500`) → semantic
   (`color.action.primary`) → component-local aliases (`button.bg`). Features may use
   only the semantic layer.
3. **Contract components** — for every shared component, document props/variants, what
   it owns (spacing inside), and what it never does (fetching data, business logic).
4. **Accessibility pass** — keyboard paths, focus order, visible focus, contrast,
   names/roles for interactive elements.
5. **Version and publish** — SemVer for the component package; breaking component API
   changes require a deprecation release first (see `ci-cd` for release flow).
6. **Audit regularly** — run the checklist below on each new surface; reject one-off
   hex values and magic pixel numbers in review.

## Enterprise Rules & Standards (MUST / SHOULD / MUST NOT)

- **MUST** reference semantic tokens for color, spacing, typography, and motion; raw
  hex, px, or ms literals in feature code are violations.
- **MUST** meet WCAG 2.2 AA: 4.5:1 body-text contrast, full keyboard operability,
  visible focus indicators, and accessible names for all interactive elements.
- **MUST** version the component library with SemVer and deprecate before removing.
- **MUST** keep components presentation-only: no data fetching, no business rules, no
  direct service calls inside shared components.
- **SHOULD** support dark mode and reduced-motion via token themes, not component forks.
- **SHOULD** snapshot-test rendered variants of each component.
- **MUST NOT** copy another component's markup to "variant" it — extend the original or
  compose smaller primitives.

## Examples

Good — semantic token usage:

```css
.card {
  background: var(--color-surface-raised);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  transition: background var(--motion-fast) var(--ease-standard);
}
```

Bad — magic values:

```css
.card {
  background: #fafafa; /* one-off hex, breaks dark mode */
  padding: 13px; /* not on the spacing scale */
  transition: all 333ms; /* non-token duration, animates everything */
}
```

Why it fails: values drift per feature, dark mode breaks silently, and no reviewer can
trace which design decision a literal implements.

## Checklist

- [ ] No raw hex/px/ms literals in feature styles; tokens only from the semantic layer.
- [ ] Every shared component has a documented prop/variant contract.
- [ ] Keyboard-only operation verified for interactive flows.
- [ ] Contrast checked against WCAG 2.2 AA ratios.
- [ ] Component package version bumped correctly (major = breaking API).
- [ ] Deprecated components warn at runtime and in docs, with a migration path.

## Common Pitfalls

- **Token sprawl** — a token per screen; tokens encode decisions, not one-offs.
- **Wrapper sprawl** — "just a small wrapper" around a component that reimplements it;
  extend or compose instead.
- **A11y retrofit** — accessibility checked only before release; check per component.
- **Theme forks** — dark mode maintained by duplicating components; themes belong in
  token values, not markup.

## References

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Design tokens community spec: https://design-tokens.github.io/community-group/format/
- WAI-ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
