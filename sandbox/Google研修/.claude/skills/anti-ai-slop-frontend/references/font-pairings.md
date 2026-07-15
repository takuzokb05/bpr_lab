# Font Pairings Reference

Organized by aesthetic direction. Each pairing includes the reasoning for why it works.
All fonts are available on Google Fonts unless noted otherwise.

---

## Code / Technical

| Display | Body | Mono | Why it works |
|---------|------|------|-------------|
| Space Grotesk* | IBM Plex Sans | JetBrains Mono | Geometric display + humanist body creates "engineered but approachable" |
| Syne | Source Sans 3 | Fira Code | Syne's unusual geometry signals technical sophistication |
| Azeret Mono | Work Sans | — | All-monospace stack for maximum terminal aesthetic |

*Space Grotesk: use sparingly — it's becoming overused in AI-generated UIs.
If you've used it recently, substitute Outfit or General Sans.

---

## Editorial / Magazine

| Display | Body | Why it works |
|---------|------|-------------|
| Playfair Display | Crimson Pro | High-contrast serif pair: Display's dramatic strokes vs Crimson's refined readability |
| Fraunces | Newsreader | Fraunces' optical sizing + Newsreader's text optimization = actual editorial feel |
| Lora | Merriweather | Both optimized for screen; Lora's cursive stress adds editorial warmth |
| DM Serif Display | DM Sans | Same design family, serif/sans contrast creates instant hierarchy |

---

## Startup / Bold

| Display | Body | Why it works |
|---------|------|-------------|
| Clash Display | Satoshi | Geometric tension: Clash's angular cuts vs Satoshi's rounded terminals |
| Cabinet Grotesk | General Sans | Both geometric but at different densities — heading punches, body breathes |
| Plus Jakarta Sans | Nunito Sans | Jakarta's ink traps signal modernity; Nunito's openness is welcoming |
| Outfit | Red Hat Display | Outfit is versatile across weights; Red Hat adds brand-like distinction |

---

## Luxury / Refined

| Display | Body | Why it works |
|---------|------|-------------|
| Cormorant Garamond | EB Garamond | Ultra-thin display weight (300) reads as haute couture |
| Tenor Sans | Lora | Tenor's even stroke + Lora's elegance = understated luxury |
| Bodoni Moda | Libre Caslon Text | Bodoni's extreme thick-thin contrast is the classic luxury signal |

---

## Brutalist / Raw

| Display | Body | Why it works |
|---------|------|-------------|
| Space Mono | Work Sans | Monospace heading breaks every typographic convention — intentionally jarring |
| Azeret Mono | IBM Plex Mono | Full monospace stack communicates "we don't care about looking pretty" |
| Bebas Neue | Source Code Pro | All-caps condensed + code font = poster meets terminal |

---

## Playful / Friendly

| Display | Body | Why it works |
|---------|------|-------------|
| Bricolage Grotesque | Nunito | Bricolage's quirky inktraps + Nunito's roundness = personality without chaos |
| Fredoka | Quicksand | Both rounded, but Fredoka's weight range adds expressiveness |
| Baloo 2 | Poppins | Baloo's warmth in headings, Poppins' geometric clarity in body |

---

## Japanese-Mixed (和欧混植)

| Display (JP) | Display (Latin) | Body (JP) | Why it works |
|-------------|-----------------|-----------|-------------|
| Zen Kaku Gothic New | Outfit | Noto Sans JP | Zen Kaku's slightly narrower set width creates distinction from Noto |
| Shippori Mincho | Cormorant Garamond | Noto Serif JP | Mincho + Garamond share calligraphic DNA across cultures |
| M PLUS Rounded 1c | Nunito | M PLUS 1p | Rounded Japanese + rounded Latin for playful bilingual UIs |

---

## Pairing Principles

1. **Contrast over similarity** — Display + monospace, serif + geometric sans, variable-weight
   display + fixed-weight body. Contrast creates hierarchy; similarity creates monotony.

2. **Weight as a design tool** — Use the extreme ends of the weight range (100–200, 800–900).
   The middle range (400–600) is where every default lives. Avoid it for headings.

3. **One distinctive choice, executed decisively** — Pick *one* unusual font and use it
   as the anchor. The other fonts support it. Two unusual fonts compete; one commands.

4. **Size jumps tell the story** — For headings vs body, aim for 3x+ ratio minimum.
   A 48px heading with 16px body creates drama. A 24px heading with 16px body is invisible.

5. **Letter-spacing differentiates** — Tighten headings (-0.02em to -0.05em) and loosen
   labels/caps (0.05em to 0.1em). This single CSS property change signals design intent.
