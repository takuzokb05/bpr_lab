# Component Patterns Reference

The same data can take radically different visual forms. LLMs default to the most common
expression because that's what they've seen most. This matrix maps common data types to
alternative representations, helping you choose the expression that fits your context
instead of the one the model would pick by default.

---

## Numeric Metrics

The default: icon-left, big number, small label, in a card. This is *the* AI dashboard pattern.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Hero number** | Single KPI that matters most | Giant font, minimal context, commands attention |
| **Inline stat** | Metrics within narrative text | Flows with content, not separated into a "dashboard" |
| **Sparkline** | Trend matters more than current value | Tiny chart beside the number shows direction |
| **Gauge / radial** | Progress toward a goal | Circular fill communicates completion |
| **Comparison delta** | Change over time | "↑ 12.4%" with color-coded direction |
| **Trend badge** | Status in a list/table | Compact pill: number + arrow, fits in tight spaces |
| **Large monospace counter** | Real-time / live data | Fixed-width digits prevent layout shift, feel technical |
| **Stacked bar context** | Part of a whole | Number atop a proportional bar shows ratio |

---

## Cards

The default: `rounded-lg shadow-sm p-6 bg-white` with uniform everything.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Border-only** | Dense interfaces, data-heavy contexts | Clean, technical, no visual noise from shadows |
| **Multi-layer shadow** | Hero content, featured items | 3-4 shadow layers create depth that feels physical |
| **Flush / surface-diff** | Minimal aesthetic | No border or shadow; only background color shift separates |
| **Accent border** | Categorized content | Left or top border in category color = instant visual sorting |
| **Glass / blur** | Over images or gradients | `backdrop-filter: blur()` + semi-transparent background |
| **Inset** | Settings, secondary content | `inset` shadow or recessed background = content feels embedded |
| **Outlined with gap** | Editorial layouts | Thin border with generous internal padding = magazine feel |

---

## Navigation

The default: horizontal top bar with logo-left, links-center, CTA-right.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Side rail** | Complex apps with many sections | Narrow icon rail (48-64px) that expands on hover |
| **Bottom tab bar** | Mobile-first, ≤5 sections | iOS/Android pattern, familiar but often missed on web |
| **Contextual breadcrumb** | Deep hierarchies | Shows path, not all options — progressive disclosure |
| **Command palette** | Power users, keyboard-first | `Cmd+K` modal with search — Linear, Raycast style |
| **Mega menu** | Content-rich sites | Full-width dropdown with organized sections |
| **Floating pill** | Minimal sites, few sections | Fixed position pill with 3-4 items, subtle and modern |
| **Split nav** | Two distinct user journeys | Different nav for different user types |

---

## Data Tables

The default: basic HTML table with alternating row colors.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Bordered grid** | Financial / spreadsheet data | Every cell bordered, high density, Excel-like precision |
| **Row-focused** | Scannable lists | No vertical borders, row hover highlights entire row |
| **Card list** | Mobile-responsive data | Each row becomes a card on small screens |
| **Dense terminal** | Developer tools, logs | Monospace, tight spacing, dark background |
| **Expandable rows** | Detail-on-demand | Click to reveal nested content without page change |
| **Kanban transform** | Status-based data | Same data, displayed as columns by status |

---

## Forms

The default: stacked labels with rounded inputs and a blue submit button.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Floating labels** | Compact forms | Label moves into the border on focus — Material style |
| **Inline editing** | Settings, profiles | Content is the form; click to edit in place |
| **Conversational** | Onboarding, surveys | One question at a time, full-screen, typeform-like |
| **Side-by-side** | Desktop forms with context | Form on one side, preview/help on the other |
| **Segmented steps** | Complex multi-step forms | Visual progress bar with step indicators |
| **Command-line style** | Developer tools | Input prompt with auto-complete, terminal aesthetic |

---

## Loading States

The default: spinning circle or "Loading..." text.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Skeleton screens** | Content layout is known | Gray shapes matching content layout — perceived speed |
| **Shimmer** | Cards, images | Animated gradient sweep across placeholder |
| **Progressive reveal** | Data-heavy pages | Real content appears section by section |
| **Branded animation** | Brand-conscious apps | Custom micro-animation related to the product |
| **Blur-to-sharp** | Image-heavy content | Blurred placeholder sharpens as content loads |
| **Content-first** | Text content | Show text immediately, images load progressively |

---

## Empty States

The default: centered icon + "No data" text + "Create new" button.

| Expression | Best for | Visual character |
|-----------|----------|-----------------|
| **Illustration + guidance** | First-time users | Custom illustration with specific next-step instructions |
| **Template suggestions** | Creative tools | Show starter templates they can begin from |
| **Minimal prompt** | Dense UIs | Single line of text with inline CTA, no illustration |
| **Interactive tutorial** | Complex features | Step-by-step onboarding embedded in the empty state |
| **Social proof** | Collaborative tools | Show what others have created to inspire action |

---

## Selection Principle

Before coding any component, ask three questions:

1. **What is the user's primary task with this data?**
   Reading → optimize for scan. Comparing → optimize for juxtaposition. Acting → optimize for interaction.

2. **What is the information density requirement?**
   High density → borders, monospace, tight spacing. Low density → generous space, large type.

3. **What is the emotional register?**
   Professional → restrained, border-focused. Playful → shadows, color, motion. Urgent → high contrast, red accents.

The answers should eliminate most options, leaving 2-3 candidates. Choose the one
that best serves the specific context — not the one you've used most recently.
