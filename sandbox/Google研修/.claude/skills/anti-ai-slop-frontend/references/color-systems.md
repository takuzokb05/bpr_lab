# Color Systems Reference

CSS variable templates and palette strategies for breaking out of the Tailwind default space.

---

## Base Template (Dark)

```css
:root {
  /* Surface scale — 5 steps from deepest to lightest */
  --surface-0: hsl(220, 15%, 6%);    /* page background */
  --surface-1: hsl(220, 12%, 10%);   /* card / panel */
  --surface-2: hsl(220, 10%, 14%);   /* hover / active */
  --surface-3: hsl(220, 8%, 18%);    /* elevated element */
  --surface-4: hsl(220, 6%, 24%);    /* highest elevation */

  /* Text scale */
  --text-0: hsl(40, 10%, 92%);       /* primary text */
  --text-1: hsl(40, 5%, 65%);        /* secondary text */
  --text-2: hsl(40, 3%, 40%);        /* placeholder / disabled */

  /* Accent — one color, three intensities */
  --accent: hsl(340, 75%, 55%);
  --accent-hover: hsl(340, 75%, 62%);
  --accent-subtle: hsl(340, 75%, 55%, 0.1);

  /* Borders */
  --border-default: hsl(0, 0%, 100%, 0.06);
  --border-strong: hsl(0, 0%, 100%, 0.12);

  /* Semantic */
  --success: hsl(145, 60%, 45%);
  --warning: hsl(35, 90%, 55%);
  --error: hsl(0, 72%, 55%);
}
```

## Base Template (Light)

```css
:root {
  --surface-0: hsl(40, 20%, 97%);    /* warm off-white, not #FFF */
  --surface-1: hsl(40, 15%, 94%);
  --surface-2: hsl(40, 10%, 90%);
  --surface-3: hsl(40, 8%, 86%);
  --surface-4: hsl(40, 5%, 80%);

  --text-0: hsl(220, 20%, 12%);
  --text-1: hsl(220, 10%, 35%);
  --text-2: hsl(220, 5%, 55%);

  --accent: hsl(15, 85%, 50%);       /* warm orange instead of blue */
  --accent-hover: hsl(15, 85%, 42%);
  --accent-subtle: hsl(15, 85%, 50%, 0.08);

  --border-default: hsl(0, 0%, 0%, 0.06);
  --border-strong: hsl(0, 0%, 0%, 0.12);
}
```

---

## IDE-Inspired Palettes

These work because IDE themes are designed for long viewing sessions — they're
inherently comfortable, distinctive, and well-tested on screens.

### Catppuccin Mocha (adapted)
```css
--surface-0: hsl(240, 21%, 12%);   /* base */
--surface-1: hsl(240, 21%, 15%);   /* mantle */
--text-0: hsl(227, 68%, 88%);      /* text */
--accent: hsl(316, 72%, 86%);      /* pink */
/* Why: Warm-tinted dark with pastel accents. Distinctive and easy on the eyes. */
```

### Tokyo Night (adapted)
```css
--surface-0: hsl(235, 20%, 12%);
--surface-1: hsl(235, 18%, 16%);
--text-0: hsl(220, 30%, 78%);
--accent: hsl(200, 80%, 65%);      /* cool cyan */
/* Why: Blue-shifted dark with high-contrast cyan. Feels futuristic and calm. */
```

### Gruvbox Dark (adapted)
```css
--surface-0: hsl(0, 0%, 16%);
--surface-1: hsl(20, 5%, 20%);
--text-0: hsl(45, 35%, 80%);
--accent: hsl(30, 85%, 55%);       /* warm orange */
/* Why: Warm-neutral with earthy tones. Feels analog and handcrafted. */
```

### Nord (adapted)
```css
--surface-0: hsl(220, 16%, 16%);
--surface-1: hsl(220, 17%, 20%);
--text-0: hsl(219, 28%, 88%);
--accent: hsl(193, 43%, 67%);      /* frost blue */
/* Why: Cool and restrained. Scandinavian design sensibility in code form. */
```

---

## Nature-Inspired Palettes

### Desert
```css
--surface-0: hsl(30, 25%, 92%);    /* sand */
--surface-1: hsl(30, 20%, 87%);
--text-0: hsl(15, 30%, 18%);       /* dark earth */
--accent: hsl(15, 75%, 45%);       /* terracotta */
```

### Deep Ocean
```css
--surface-0: hsl(210, 30%, 8%);    /* abyss */
--surface-1: hsl(210, 25%, 12%);
--text-0: hsl(180, 15%, 80%);      /* seafoam */
--accent: hsl(170, 65%, 50%);      /* bioluminescence */
```

### Moss Forest
```css
--surface-0: hsl(100, 8%, 10%);
--surface-1: hsl(100, 10%, 14%);
--text-0: hsl(80, 10%, 82%);
--accent: hsl(90, 50%, 45%);       /* moss green */
```

---

## The 60-30-10 Rule in Practice

```
60% — Dominant surface color (--surface-0 and --surface-1)
      This is the canvas. It should be quiet.

30% — Supporting elements (--text-1, --surface-3, --border-default)
      These provide structure and hierarchy.

10% — Accent (--accent)
      This is the memory hook. One color, used sparingly:
      CTAs, active states, links, key data points.
      The smaller the accent area, the more impact it has.
```

The most common AI-generated mistake is giving every color equal weight, creating
a "paintball" effect where nothing stands out because everything does.

---

## What to Avoid and Why

| Pattern | Why it's AI-signaling |
|---------|----------------------|
| `purple-500` → `purple-700` gradient | Tailwind's demo default from 2019, propagated through thousands of tutorials |
| `blue-500` + `gray-50` body | The shadcn/ui and Next.js starter default |
| `bg-white` (#FFFFFF) | Too clinical; warm off-white reads as intentional |
| Rainbow category colors | LLM distributes colors "fairly"; real designers use 2-3 max |
| `bg-gradient-to-r from-X to-Y` | Tailwind gradient utility is so easy that LLMs always reach for it |
