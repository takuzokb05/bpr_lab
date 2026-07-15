---
name: anti-ai-slop-frontend
description: |
  Generate distinctive, production-grade frontend UI that avoids the "AI slop" aesthetic —
  the generic Inter-font, purple-gradient, white-background look that LLMs converge on by default.
  Use this skill whenever building web UIs, components, pages, dashboards, landing pages,
  React/Vue/HTML artifacts, or any visual frontend work. Also trigger when the user says
  "make it look good", "beautify", "polish the UI", "redesign", "style this", or asks for
  any kind of frontend aesthetic improvement — even if they don't explicitly mention design quality.
  If the output will be visible to humans in a browser, this skill applies.
---

# Anti-AI-Slop Frontend Design

This skill breaks the pattern where LLMs generate the same generic UI every time.

The root cause is **distributional convergence**: LLMs predict tokens from training data,
and the most common web patterns (Tailwind demos used `purple-600`, tutorials default to
Inter, every SaaS template has three icon-cards in a row) become the statistical path of
least resistance. Without specific guidance, you'll get that path every time.

The fix is to inject specific constraints along each design axis, shifting the sampling
space away from the median. Each section below explains not just *what* to do, but *why*
it works against convergence.

---

## Phase 0: Context Anchoring (before writing any code)

Skip this and the model falls back to the statistical center. Every field here narrows the
probability space, making generic output harder to produce.

Ask yourself (or the user) five things:

1. **Purpose** — What problem does this UI solve, and for whom?
   Without this, the model has no basis for choosing one aesthetic over another,
   so it picks the safest option (which is the most generic one).

2. **Tone** — Commit to one extreme direction from the palette below.
   "Modern and clean" is the prompt that produces purple gradients. Specificity is the antidote.

   ```
   brutally-minimal     maximalist-chaos      retro-futuristic
   organic-natural      luxury-refined         playful-toy-like
   editorial-magazine   brutalist-raw          art-deco-geometric
   soft-pastel          industrial-utilitarian  cyberpunk-terminal
   japanese-wabi-sabi   swiss-international    memphis-postmodern
   scandinavian-hygge   bauhaus-functional     vapor-wave-nostalgia
   ```

3. **Differentiator** — If a user remembers one thing about this UI, what is it?
   This forces a focal point. Without it, every element gets equal (mediocre) attention.

4. **Anti-reference** — Name a UI you do *not* want to look like.
   Negative constraints are disproportionately effective for LLMs because they cut off
   entire regions of the output space.

5. **Constraints** — Framework, performance budget, accessibility requirements.
   Constraints breed creativity; they're features, not limitations.

---

## Phase 1: Typography

Typography is the single highest-ROI design lever. Anthropic's own A/B testing showed that
swapping the font alone transforms the perceived quality of AI-generated UI. The reason:
fonts like Inter and Roboto appear in the vast majority of training examples, so using them
is the clearest possible signal that a machine chose the design.

### Fonts to avoid

Inter, Roboto, Open Sans, Lato, Arial, Helvetica Neue, system-ui, -apple-system, Segoe UI.

These aren't bad fonts — they're overrepresented in training data, which makes them
the default path for any LLM. Avoiding them forces the model into less-traveled territory.

### Choosing alternatives

Pick fonts that match your tone. See `references/font-pairings.md` for a curated matrix
organized by aesthetic direction, with reasoning for each pairing.

### Key principles

- **Extreme weight contrast** — Pair 200-weight headings with 800-weight accents, or vice versa.
  The model defaults to 400 vs 600 because that's the safe middle. Pushing to extremes
  creates visual tension that reads as intentional design.

- **Dramatic size jumps** — Headings should be 3x+ the body size, not 1.5x.
  Small jumps look "auto-generated"; large jumps look "art-directed".

- **Deliberate letter-spacing** — Tighten headings (`-0.02em` to `-0.05em`), loosen
  small caps or labels (`0.05em` to `0.1em`). Default tracking reads as undesigned.

- **Intentional line-height** — Body text at 1.6–1.8, headings at 0.9–1.1.
  Tight heading line-height creates visual density that signals editorial quality.

Load from Google Fonts with `display=swap` for performance.

---

## Phase 2: Color & Theme

The model converges on Tailwind's default palette because that's what dominates its training
data. Specifying a color system from a different source (IDE themes, cultural aesthetics,
natural phenomena) pulls from an entirely different region of the probability space.

### Patterns to avoid

- Purple-to-blue gradients on white backgrounds (the single most recognizable AI pattern)
- `blue-500` + `gray-100` (the "SaaS starter kit" look)
- Evenly distributed 5-color palettes where each color gets equal weight
- Pure `#FFFFFF` backgrounds or pure `#000000` — use off-whites like `#FAFAF9`
  or near-blacks like `#0A0A0B` instead (the slight warmth reads as considered)

### Building a palette

Use the **60-30-10 rule**: one dominant color (60% of visual area), one supporting color (30%),
and one accent (10%). The accent becomes the user's memory hook.

Draw inspiration from outside the web design corpus:
- IDE themes (Dracula, Catppuccin, Nord, Tokyo Night, Gruvbox)
- Art and culture (ukiyo-e palettes, Bauhaus primaries, Scandinavian muted tones)
- Nature (desert sand, deep ocean, moss green, twilight gradients)

Manage all colors through CSS custom properties. This isn't just organization —
it forces consistency across components, which is one of the strongest signals of
a designed (vs generated) interface.

### Dark vs light

Default to dark mode roughly half the time. Nearly all AI-generated UIs are light,
so a dark default is instant differentiation. When building dark themes, avoid the
"black screen with white text" trap — use warm near-blacks (`hsl(30, 10%, 8%)`) with
a nuanced surface scale (5+ steps from background to foreground).

See `references/color-systems.md` for complete CSS variable templates and palette examples.

---

## Phase 3: Layout & Composition

The model's most common layout is: hero section → three equal-width cards → CTA → footer.
This pattern dominates because it's the structure of thousands of Tailwind/Bootstrap templates
in the training data. Break it.

### Breaking the grid

- **Asymmetric columns** — Use `1fr 2fr` or `2fr 1fr 1fr` instead of `repeat(3, 1fr)`.
  Equal division is the path of least resistance; asymmetry requires intention.

- **Overlap and layering** — Let elements overlap with negative margins or `position: relative`.
  The model avoids overlap because it's "risky"; that's exactly why it looks designed.

- **Bento grids** — Mix cell sizes (`span 2` on some items). Same data, more visual interest.

- **Deliberate whitespace asymmetry** — Push content to one side, leave the other open.
  Generous, intentional negative space is the hallmark of editorial design.

- **Grid breaks** — Let one element escape the grid entirely. A single element
  that breaks alignment creates a focal point and disrupts the template feel.

### Spacing system

Define a spacing scale (e.g., 4, 8, 12, 16, 24, 32, 48, 64, 96 based on an 8px unit)
and apply it consistently via CSS custom properties. The model tends to pick `p-4`, `p-6`,
`p-8` arbitrarily; a defined scale creates visual rhythm that reads as systematic.

Make inter-section spacing generous (25–40% of viewport height). This "breathing room"
is the most visible difference between template-assembled and designed layouts.

### Component diversity

The same data can take many forms. A number metric could be a hero number, inline stat,
sparkline, gauge, comparison delta, or trend badge. A card could be border-only, elevated,
glass, flush, or accent-bordered. Before coding, explicitly consider at least three
representations and choose the one that fits the context.

See `references/component-patterns.md` for a matrix of common data types mapped to
their possible UI expressions.

---

## Phase 4: Motion & Animation

The model's instinct when asked for "animation" is to add `fadeInUp` to everything.
This creates visual noise rather than delight. The core principle: **every animation
needs a reason you can articulate**. If you can't say why something moves, it shouldn't.

### Valid motion purposes

- **Entrance orientation** — "This content just arrived" (card slide-in)
- **Stagger disambiguation** — Prevents the "wall of content" effect when multiple items load
- **Interactivity confirmation** — Hover lift says "this is clickable"
- **Tactile feedback** — Button press micro-interaction
- **Spatial continuity** — Page transitions that maintain user orientation

### Implementation

- Prefer CSS-only (`@keyframes` + `animation-delay`) for HTML. Use Framer Motion / Motion
  for React when available.
- Keep durations between 150–300ms. Shorter feels broken, longer feels sluggish.
- Use `ease-out` for entrances, `ease-in` for exits. `cubic-bezier` for personality.
- For page load: one orchestrated stagger sequence (50–100ms delays) is better
  than scattered effects. Think "opening sequence", not "everything bouncing".
- Respect `prefers-reduced-motion` — always. Wrap motion in a media query.

---

## Phase 5: Backgrounds & Visual Depth

`background: white` occupies the largest area of most UIs. When it's an unmodified solid,
no amount of good typography or color saves the template feel. A single layer of texture
transforms "AI output" into "someone designed this."

### Techniques (choose based on tone)

- **Gradient mesh** — Multiple overlapping `radial-gradient` layers with low-opacity colors
- **Film grain** — SVG noise filter at 3–5% opacity for tactile texture
- **Dot grid** — Repeating `radial-gradient` circles as subtle scaffolding
- **Blur layers** — `backdrop-filter: blur()` for depth separation
- **Geometric patterns** — `repeating-linear-gradient` for structural backgrounds

See `references/background-snippets.md` for copy-paste CSS implementations of each.

The key insight: even a single barely-visible noise layer changes the perception of
the entire interface. The effort-to-impact ratio is extraordinarily high.

---

## Phase 6: Quality Checklist

After generating UI, run through this audit. Each item targets a specific convergence pattern:

**Anti-convergence checks:**
- [ ] No Inter/Roboto/Arial/system-ui in the font stack
- [ ] No purple-to-blue gradient anywhere
- [ ] No pure `#FFFFFF` or `#000000` backgrounds
- [ ] No three-equal-column card grid as the primary layout
- [ ] No uniform border-radius across all components
- [ ] Hover states do more than `opacity: 0.8`
- [ ] Font weights span beyond 400–600
- [ ] Spacing follows a defined scale, not ad-hoc values

**Production quality checks:**
- [ ] Colors managed through CSS custom properties
- [ ] `prefers-reduced-motion` respected
- [ ] Focus states visually distinct (not just browser default)
- [ ] Touch targets ≥ 44px
- [ ] Contrast ratio ≥ 4.5:1 (WCAG AA)
- [ ] Google Fonts loaded with `display=swap`

**The identity test:** Ask "which other website does this look like?"
If you can answer immediately, the design isn't distinctive enough.

---

## Phase 7: Design Token Persistence

LLMs treat each generation as independent, re-deciding fonts, colors, and spacing from
scratch every time. For multi-component projects, this creates inconsistency that
immediately breaks the "designed system" illusion.

The solution: create a `design-system.md` (or `.json`) at project root that captures
every decision — palette, typography, spacing scale, depth strategy, border conventions.
Include this file in context for all subsequent generations.

See `references/design-token-template.md` for the full template structure.

This isn't just organization. It's a constraint mechanism: with the token file in context,
the model can't drift to its defaults because the explicit values override them.

---

## Reference Files

This skill bundles detailed reference material. Read the relevant file when you need
specifics beyond what's covered in this core document:

| File | Contents | When to read |
|------|----------|-------------|
| `references/font-pairings.md` | Curated font combinations by aesthetic direction with rationale | Choosing typography |
| `references/color-systems.md` | CSS variable templates, palette examples, IDE theme adaptations | Building color palette |
| `references/component-patterns.md` | Data type → UI expression matrix for 30+ common patterns | Deciding component form |
| `references/background-snippets.md` | Copy-paste CSS for gradient mesh, noise, dots, blur, geometry | Adding background depth |
| `references/design-token-template.md` | Full design system file template for token persistence | Starting a multi-component project |

---

## Sources & Attribution

This skill synthesizes approaches from:

- **Anthropic frontend-design skill** — The ~400-token prompt that proved targeted guidance
  dramatically shifts LLM output quality. Core insight: naming the problem ("AI slop")
  makes the model self-aware of its convergence tendencies.
- **Dammyjay93/interface-design** — Pioneered design token persistence (`system.md`)
  and the philosophy that "defaults don't announce themselves."
- **carmahhawwari/ui-design-brain** — 60+ component best-practice database showing that
  the same data type can take radically different forms.
- **nextlevelbuilder/ui-ux-pro-max-skill** — Industry-specific anti-pattern filtering
  and design system generation reasoning engine.
- **Anthropic Cookbook (frontend aesthetics)** — Axis-isolated prompts proving that
  single-dimension improvements (typography alone, color alone) are independently effective.
- **Community analysis (prg.sh, paddo.dev, Deloughry.co.uk, Nick Porter/Medium)** —
  Root cause analysis of Tailwind purple convergence and JSONC design spec workflow.
