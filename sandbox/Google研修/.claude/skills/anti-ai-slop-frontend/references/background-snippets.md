# Background Snippets Reference

Copy-paste CSS implementations for background depth techniques.
Each snippet is self-contained and can be combined with others.

---

## Gradient Mesh

Creates an organic, multi-color ambient background. Works on dark or light themes.

```css
/* Dark theme gradient mesh */
.bg-mesh-dark {
  background:
    radial-gradient(ellipse at 20% 50%, hsla(210, 80%, 60%, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, hsla(340, 70%, 50%, 0.10) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, hsla(170, 60%, 40%, 0.10) 0%, transparent 50%),
    hsl(220, 15%, 8%);
}

/* Light theme gradient mesh */
.bg-mesh-light {
  background:
    radial-gradient(ellipse at 15% 30%, hsla(210, 70%, 70%, 0.12) 0%, transparent 45%),
    radial-gradient(ellipse at 85% 60%, hsla(30, 80%, 65%, 0.08) 0%, transparent 40%),
    radial-gradient(ellipse at 50% 90%, hsla(280, 50%, 70%, 0.06) 0%, transparent 50%),
    hsl(40, 20%, 97%);
}

/* Animated gradient mesh (subtle drift) */
.bg-mesh-animated {
  background:
    radial-gradient(ellipse at var(--x1, 20%) var(--y1, 50%), hsla(210, 80%, 60%, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at var(--x2, 80%) var(--y2, 20%), hsla(340, 70%, 50%, 0.10) 0%, transparent 50%),
    hsl(220, 15%, 8%);
  animation: mesh-drift 20s ease-in-out infinite alternate;
}

@keyframes mesh-drift {
  0%   { --x1: 20%; --y1: 50%; --x2: 80%; --y2: 20%; }
  100% { --x1: 40%; --y1: 30%; --x2: 60%; --y2: 70%; }
}
```

---

## Film Grain / Noise

Adds tactile texture. The opacity should be barely visible (3-5%).

```css
/* SVG-based noise (inline, no external file needed) */
.bg-noise {
  position: relative;
}
.bg-noise::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 1;
}

/* Alternative: CSS-only grain using multiple gradients */
.bg-grain {
  background-image:
    repeating-radial-gradient(circle at 17% 32%, hsl(0 0% 50% / 0.02) 0px, transparent 1px),
    repeating-radial-gradient(circle at 62% 78%, hsl(0 0% 50% / 0.02) 0px, transparent 1px),
    repeating-radial-gradient(circle at 89% 14%, hsl(0 0% 50% / 0.02) 0px, transparent 1px);
  background-size: 3px 3px, 4px 4px, 5px 5px;
}
```

---

## Dot Grid

Subtle structural scaffolding. Great for dashboards and tool interfaces.

```css
/* Standard dot grid */
.bg-dots {
  background-image: radial-gradient(circle, hsla(0, 0%, 50%, 0.15) 1px, transparent 1px);
  background-size: 24px 24px;
}

/* Finer dot grid */
.bg-dots-fine {
  background-image: radial-gradient(circle, hsla(0, 0%, 50%, 0.10) 0.5px, transparent 0.5px);
  background-size: 16px 16px;
}

/* Dot grid with fade at edges */
.bg-dots-fade {
  background-image: radial-gradient(circle, hsla(0, 0%, 50%, 0.15) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 40%, transparent 70%);
}
```

---

## Line Grid

Architectural, blueprint feel. Works well with brutalist or technical aesthetics.

```css
/* Horizontal + vertical lines */
.bg-grid {
  background-image:
    linear-gradient(hsla(0, 0%, 50%, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, hsla(0, 0%, 50%, 0.06) 1px, transparent 1px);
  background-size: 48px 48px;
}

/* Grid with accent lines every 4th */
.bg-grid-accent {
  background-image:
    linear-gradient(hsla(0, 0%, 50%, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, hsla(0, 0%, 50%, 0.04) 1px, transparent 1px),
    linear-gradient(hsla(0, 0%, 50%, 0.10) 1px, transparent 1px),
    linear-gradient(90deg, hsla(0, 0%, 50%, 0.10) 1px, transparent 1px);
  background-size: 16px 16px, 16px 16px, 64px 64px, 64px 64px;
}
```

---

## Blur Layers (Glassmorphism)

Creates depth separation between foreground and background elements.

```css
/* Glass card over a background */
.glass-card {
  background: hsla(0, 0%, 100%, 0.05);
  backdrop-filter: blur(12px) saturate(1.2);
  -webkit-backdrop-filter: blur(12px) saturate(1.2);
  border: 1px solid hsla(0, 0%, 100%, 0.08);
  border-radius: 12px;
}

/* Frosted sidebar */
.glass-sidebar {
  background: hsla(220, 15%, 8%, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid hsla(0, 0%, 100%, 0.06);
}
```

---

## Geometric Patterns

Structured, repeating backgrounds for branding or section differentiation.

```css
/* Diagonal stripes */
.bg-stripes {
  background-image: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 10px,
    hsla(0, 0%, 50%, 0.03) 10px,
    hsla(0, 0%, 50%, 0.03) 20px
  );
}

/* Chevron pattern */
.bg-chevron {
  background-image:
    linear-gradient(135deg, hsla(0,0%,50%,0.04) 25%, transparent 25%),
    linear-gradient(225deg, hsla(0,0%,50%,0.04) 25%, transparent 25%),
    linear-gradient(315deg, hsla(0,0%,50%,0.04) 25%, transparent 25%),
    linear-gradient(45deg, hsla(0,0%,50%,0.04) 25%, transparent 25%);
  background-size: 40px 40px;
  background-position: 0 0, 0 0, 20px 0, 20px 0;
}

/* Cross-hatch */
.bg-crosshatch {
  background-image:
    linear-gradient(45deg, hsla(0,0%,50%,0.03) 25%, transparent 25%, transparent 75%, hsla(0,0%,50%,0.03) 75%),
    linear-gradient(-45deg, hsla(0,0%,50%,0.03) 25%, transparent 25%, transparent 75%, hsla(0,0%,50%,0.03) 75%);
  background-size: 30px 30px;
}
```

---

## Combining Techniques

Layer techniques for richer depth. Order matters — list from top (foreground) to bottom.

```css
/* Gradient mesh + noise + dot grid */
.bg-rich {
  position: relative;
  background:
    radial-gradient(ellipse at 20% 50%, hsla(210, 80%, 60%, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 30%, hsla(340, 70%, 50%, 0.08) 0%, transparent 50%),
    hsl(220, 15%, 8%);
}
.bg-rich::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, hsla(0, 0%, 50%, 0.08) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
}
.bg-rich::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
}
```

---

## Performance Notes

- `backdrop-filter` can be expensive — use sparingly (1-2 elements per viewport)
- SVG noise filters render once and are cached; performance cost is minimal
- Prefer CSS gradients over images for background patterns
- Use `will-change: transform` on animated backgrounds, but remove it when animation ends
- Test on mobile — some background techniques are GPU-intensive on older devices
