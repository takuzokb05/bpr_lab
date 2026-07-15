---
name: ui-design-review
description: |
  Audit existing frontend code for visual "AI slop" — the convergence patterns that make UI look
  machine-generated (Inter font, purple gradients, three-column card grids, uniform spacing).
  Produces a severity-ranked report in Japanese (technical terms in English) with concrete fix code.
---

# UI Design Review — Visual Convergence Audit

This skill examines existing frontend code for signs of distributional convergence — the
predictable visual patterns that emerge when LLMs generate UI from the statistical center
of their training data.

The goal is not to enforce a particular aesthetic. The goal is to detect where design decisions
were made by statistical probability rather than by intention, and to offer alternatives that
reintroduce intentionality.

---

## Review Process

### Step 1: Detect project type

Read the target. Classify automatically:
- **Single HTML file**: Review inline styles, `<style>` blocks, and any framework classes.
- **React/Vue directory**: Identify the design token source, then audit token values plus overrides.

### Step 2: Run the six convergence axes

#### Axis 1: Typography Convergence
- **Font family** — Inter, Roboto, Open Sans, system-ui? These dominate LLM outputs.
- **Weight range** — Only 400 and 600–700? Intentional design uses the full spectrum.
- **Size hierarchy** — Heading-to-body ratio less than 2x? AI tends toward conservative scaling.
- **Letter-spacing and line-height** — All defaults? Custom tracking is an intentionality signal.

#### Axis 2: Color & Palette Convergence
- **Palette source** — Tailwind defaults? Custom palettes break convergence.
- **Background** — Pure `#FFFFFF`/`#000000`, or off-whites and warm near-blacks?
- **Gradient patterns** — Purple-to-blue linear gradients?
- **Color distribution** — Equal weight, or 60-30-10 hierarchy?

#### Axis 3: Layout & Grid Convergence
- **Column structure** — `repeat(3, 1fr)` or asymmetric grids?
- **Content rhythm** — Same section pattern repeated, or varied structure?
- **Whitespace** — Uniform spacing or relationship-based variation?
- **Spacing scale** — Defined system (4, 8, 16, 24, 32...) or ad-hoc?

#### Axis 4: Component Uniformity
- **Border-radius** — Same everywhere, or semantically varied?
- **Shadow usage** — Single shadow or nuanced scale?
- **Hover states** — `opacity: 0.8` everywhere, or diverse interactions?
- **Button hierarchy** — Single style or primary/secondary/ghost/destructive?

#### Axis 5: Motion & Animation Quality
- **Variety** — Same animation on every element?
- **Timing** — Default `duration-300 ease-in-out` everywhere?
- **Reduced motion** — `prefers-reduced-motion` respected?

#### Axis 6: Visual Identity & Distinctiveness
- **Template test** — Can you name a specific template this resembles?
- **Signature element** — One memorable visual element?
- **Personality** — Does the UI express a clear point of view?

### Step 3: Classify findings

| Level | Meaning | Urgency |
|-------|---------|---------|
| **Strong signal** | Immediately recognizable as AI-generated | Fix first |
| **Moderate signal** | Recognizable as generic by designers/tech users | Fix second |
| **Weak signal** | Subtle pattern contributing to template feel | Polish phase |
| **Intentional** | Pattern exists but is clearly deliberate | No action |

### Step 4: Generate the report

```markdown
# UIデザインレビュー — ビジュアル収束監査

**対象**: <ファイルパス>
**日付**: <current date>

## サマリー

| 評価軸 | スコア | 判定 |
|--------|--------|------|
| Typography | X/10 | 独自性あり / 部分的に収束 / 強い収束 |
| Color & Palette | X/10 | ... |
| Layout & Grid | X/10 | ... |
| Component Uniformity | X/10 | ... |
| Motion & Animation | X/10 | ... |
| Visual Identity | X/10 | ... |

**総合スコア**: XX/60

## 強い収束シグナル（最優先で対応）
### 1. [Axis名] 問題タイトル
- **場所**: `file:line`
- **現在のコード**: ...
- **修正案**: ...

## 中程度の収束シグナル
## 弱い収束シグナル
## 良い点
## 推奨アクション
```

## What This Review Cannot Do

- **Subjective taste** — Detects convergence, not whether design is "good"
- **Brand alignment** — Needs context this skill doesn't have
- **Performance** — Custom fonts/animations affect load time; suggest Lighthouse
- **User perception** — Whether users perceive "AI-generated" requires user research

## Gotchas

- 「AI生成感の検出」が目的であり、デザインの良し悪しの総合評価ではない。スコープを守る
- スクリーンショットなしでのレビューは精度が大幅に下がる。必ず視覚的な入力を求める
- 修正コード提示時、既存のデザインシステムとの整合性を確認する
