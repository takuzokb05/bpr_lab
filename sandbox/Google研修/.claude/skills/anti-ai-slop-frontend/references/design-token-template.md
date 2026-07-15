# Design Token Template

Copy this template to your project root as `design-system.md` and fill in the values
during the initial design phase. Include this file in context for all subsequent
UI generation tasks to maintain consistency.

The purpose of this file is not documentation — it's a **constraint mechanism**.
With these values in context, the LLM can't drift to its defaults because explicit
values override statistical tendencies.

---

```markdown
# Design System

## Direction

**Personality**: [chosen tone, e.g., "brutally-minimal", "editorial-magazine"]
**Foundation**: [warm / cool / neutral] based on [specific reference, e.g., "Tokyo Night IDE theme"]
**Depth strategy**: [shadows / borders-only / elevation / flat]
**Key differentiator**: [the one thing users will remember]

## Color Tokens

### Surfaces
| Token | Value | Usage |
|-------|-------|-------|
| --surface-0 | hsl(_, _, _%) | Page background |
| --surface-1 | hsl(_, _, _%) | Card / panel |
| --surface-2 | hsl(_, _, _%) | Hover / active |
| --surface-3 | hsl(_, _, _%) | Elevated element |
| --surface-4 | hsl(_, _, _%) | Highest elevation |

### Text
| Token | Value | Usage |
|-------|-------|-------|
| --text-0 | hsl(_, _, _%) | Primary content |
| --text-1 | hsl(_, _, _%) | Secondary / supporting |
| --text-2 | hsl(_, _, _%) | Placeholder / disabled |

### Accent
| Token | Value | Usage |
|-------|-------|-------|
| --accent | hsl(_, _, _%) | Primary accent (CTAs, links, active states) |
| --accent-hover | hsl(_, _, _%) | Accent hover state |
| --accent-subtle | hsla(_, _, _%, 0.1) | Accent background tint |

### Borders
| Token | Value |
|-------|-------|
| --border-default | hsl(_, _, _%, 0.06) |
| --border-strong | hsl(_, _, _%, 0.12) |

### Semantic
| Token | Value |
|-------|-------|
| --success | hsl(_, _, _%) |
| --warning | hsl(_, _, _%) |
| --error | hsl(_, _, _%) |

## Typography

| Role | Font family | Fallback |
|------|------------|----------|
| Display / Heading | [specific font] | sans-serif / serif |
| Body | [specific font] | sans-serif |
| Mono / Code | [specific font] | monospace |

### Scale
| Level | Size | Weight | Line-height | Letter-spacing |
|-------|------|--------|-------------|---------------|
| Display XL | _px | _ | _ | _em |
| H1 | _px | _ | _ | _em |
| H2 | _px | _ | _ | _em |
| H3 | _px | _ | _ | _em |
| Body | _px | _ | _ | normal |
| Small | _px | _ | _ | normal |
| Mono | _px | _ | _ | _em |

## Spacing

**Base unit**: _px
**Scale**: [list values, e.g., 4, 8, 12, 16, 24, 32, 48, 64, 96]

| Token | Value | Usage |
|-------|-------|-------|
| --space-xs | _px | Tight gaps within components |
| --space-sm | _px | Component internal padding |
| --space-md | _px | Standard component padding |
| --space-lg | _px | Between related components |
| --space-xl | _px | Between sections |
| --space-2xl | _px | Major section breaks |
| --space-3xl | _px | Page-level breathing room |

## Borders & Radius

| Token | Value | Usage |
|-------|-------|-------|
| --radius-sm | _px | Small elements (badges, chips) |
| --radius-md | _px | Standard elements (inputs, buttons) |
| --radius-lg | _px | Large containers (cards, modals) |
| --radius-full | 9999px | Pills, avatars |

## Motion

| Token | Value | Usage |
|-------|-------|-------|
| --transition-fast | _ms ease-out | Hover, focus, micro-interactions |
| --transition-base | _ms ease-out | State changes, reveals |
| --transition-slow | _ms ease-out | Page transitions, large reveals |

**Entrance strategy**: [describe, e.g., "stagger from bottom, 60ms delay between items"]
**Hover strategy**: [describe, e.g., "translateY(-2px) + shadow enhancement"]

## Component Patterns

Record recurring patterns as they're established. Add to this section
whenever a new component is built.

### Button Primary
- Height: _px
- Padding: _px _px
- Radius: var(--radius-_)
- Background: var(--accent)
- Hover: var(--accent-hover) + [describe transformation]

### Card Default
- Border: var(--border-default)
- Padding: var(--space-_)
- Radius: var(--radius-_)
- Background: var(--surface-1)
- Hover: [describe or "none"]

### [Add more as they emerge]

## Background Treatment

**Technique**: [gradient mesh / noise / dot grid / flat / etc.]
**Implementation**: [brief CSS description or reference to background-snippets.md]
```

---

## Usage Notes

- **Create early**: Fill this out during the first component build, not after
- **Include always**: Add this file to context for every UI generation prompt
- **Evolve incrementally**: Add new component patterns as they're built
- **Values over descriptions**: Concrete values (`hsl(220, 15%, 8%)`) constrain the model;
  vague descriptions ("dark blue") leave room for drift
- **Review periodically**: If the UI starts feeling inconsistent, the token file
  may have gaps that the model is filling with defaults
