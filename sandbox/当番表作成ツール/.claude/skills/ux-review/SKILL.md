---
name: ux-review
description: |
  Perform comprehensive UX reviews on frontend code, components, pages, or entire directories.
  Combines accessibility auditing (WCAG 2.2 AA), usability heuristic evaluation (Nielsen's 10),
  microcopy quality analysis, and AI-specific UX anti-pattern detection into a single integrated report.
  Use this skill whenever the user asks to "review UX", "audit accessibility", "check usability",
  "improve the user experience", "review this component/page", or mentions "a11y", "WCAG", "ARIA",
  "microcopy", "UX audit", "heuristic evaluation", or "usability check". Also trigger when the user
  says "this feels off" or "something's wrong with the flow" about any UI — those are UX review requests.
---

# UX Review — Comprehensive UX Audit Skill

This skill runs a structured UX review across four dimensions: accessibility, usability heuristics,
microcopy quality, and AI-generated UI anti-patterns. It produces a severity-ranked report with
concrete fix code for every issue found.

## Why a structured review matters

LLM-generated frontends tend to *look* correct while being *functionally* broken for real users.
The code compiles, the layout renders, but: screen readers can't parse it, keyboard users can't
navigate it, error messages say "Something went wrong" without guidance, and loading states are
missing entirely. These aren't edge cases — they're the statistical default when UI is generated
without explicit UX constraints. This skill provides those constraints as a review framework.

---

## Review Process

### Step 1: Scope the review

Read the target files. For a single component, review it in isolation. For a directory, identify
the primary user flows (entry points, forms, navigation, error paths) and focus the review there.
Don't try to audit everything in a large codebase — prioritize the paths users actually travel.

### Step 2: Run the four review dimensions

#### Dimension A: Accessibility (WCAG 2.2 AA)

Focus on these high-impact areas:

1. **Semantic HTML** — Is `<div>` used where `<button>`, `<nav>`, `<main>`, `<section>` should be?
2. **Keyboard navigation** — Can every interactive element be reached with Tab and activated with Enter/Space?
3. **Color contrast** — Do text/background combinations meet 4.5:1 for normal text and 3:1 for large text?
4. **ARIA correctness** — No ARIA is better than bad ARIA.
5. **Form accessibility** — Every input needs a visible `<label>`. Error messages via `aria-describedby`.
6. **Target size** — Interactive targets are at least 24x24px (WCAG 2.2 SC 2.5.8).

#### Dimension B: Usability Heuristics (Nielsen's 10)

1. **Visibility of system status** — Missing loading states, no progress indicators?
2. **Match between system and real world** — Technical jargon in user-facing text?
3. **User control and freedom** — Can users undo, go back, escape?
4. **Consistency and standards** — Mixed patterns across the interface?
5. **Error prevention** — No input validation until submit?
6. **Recognition rather than recall** — Form fields without context?
7. **Flexibility and efficiency** — Keyboard shortcuts, bulk actions?
8. **Aesthetic and minimalist design** — Every element necessary?
9. **Help users recover from errors** — Generic "Something went wrong"?
10. **Help and documentation** — Tooltips, onboarding hints, empty state guidance?

#### Dimension C: Microcopy Quality

Evaluate against five principles:
1. **Specific over generic** — "Submit" vs "Create my account"
2. **User-perspective** — "You're all set!" vs "The form has been submitted"
3. **Concise** — Cut words without losing meaning
4. **Action-oriented** — CTAs describe the outcome, not the mechanism
5. **Tone-consistent** — Voice matches across all states

#### Dimension D: AI-Generated UI Anti-Patterns

1. **Missing states** — Only happy path implemented
2. **Phantom interactivity** — Elements that look clickable but aren't
3. **Fake responsiveness** — Layout breaks at non-tested breakpoints
4. **Copy-paste data** — Placeholder data left in code
5. **Single-interaction design** — First click works, repeat breaks
6. **Invisible hierarchy** — All elements have equal visual weight

### Step 3: Classify and rank findings

| Severity | Criteria | Action |
|----------|----------|--------|
| **Critical** | Blocks users or violates WCAG A/AA | Fix before shipping |
| **High** | Significant usability degradation | Fix this sprint |
| **Medium** | Best practice violation | Fix next iteration |
| **Low** | Enhancement opportunity | Backlog |

### Step 4: Generate the report

```markdown
# UX Review Report

**Target**: <file path or directory>
**Date**: <current date>
**Scope**: <what was reviewed and what was excluded>

---

## Summary

| Dimension | Score | Status |
|-----------|-------|--------|
| Accessibility (WCAG 2.2 AA) | X/10 | Good / Needs work / Failing |
| Usability (Nielsen's 10) | X/10 | Good / Needs work / Failing |
| Microcopy | X/10 | Good / Needs work / Failing |
| AI Anti-Patterns | X/10 | Good / Needs work / Failing |

**Overall**: XX/40

---

## Critical Issues
### 1. [WCAG X.X.X] Issue title
- **Location**: `file:line`
- **Impact**: Who is affected and how
- **Fix**: concrete code

## High Priority Issues
[same format]

## Passing Items
[what's already done well]

## Recommended Actions
[ordered list by priority]
```

## What This Review Cannot Do

- **Screen reader testing** requires actual AT (NVDA, VoiceOver, JAWS)
- **Cognitive walkthrough** requires understanding of user's mental model
- **Performance UX** requires runtime measurement
- **Emotional design** requires user research

## Gotchas

- WCAG基準の機械的チェックだけで終わらない。実際のユーザーフロー（タスク完遂率）の視点で評価する
- マイクロコピーは文言の「正しさ」より「ユーザーの次の行動を導けるか」を重視する
- モバイルとデスクトップで異なるUX課題がある。レビュー対象のデバイスを最初に確認する
