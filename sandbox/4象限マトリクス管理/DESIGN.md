# Design System: Dual-Persona Architecture

## 1. Overview & Creative North Star
The North Star for this design system is **"The Kinetic Archive."** 

This system rejects the static, "flat-box" nature of traditional productivity tools. Instead, it treats the interface as a living environment that shifts based on the user's psychological state. We move between two distinct emotional poles: 
- **The Curator (Normal Mode):** A high-end editorial experience defined by "Atmospheric Precision." It uses expansive white space and tonal layering to reduce cognitive load.
- **The Operator (Survival Mode):** A high-stakes "Digital Brutalism" experience. It is loud, high-contrast, and tactile, designed to trigger urgency through scan-line textures and neon signals.

We break the "template" look by utilizing **intentional asymmetry**. Primary navigation or critical data metrics should not always be centered; they should be anchored to the edges of the grid, creating an editorial flow that feels custom-built rather than generated.

---

## 2. Colors: Tonal Depth & The Survival Shift

### The Normal Mode Palette (Atmospheric Precision)
We utilize a sophisticated Material Design-inspired scale. The goal is to create a hierarchy of focus through background shifts rather than structural lines.

| Token | Hex | Role |
| :--- | :--- | :--- |
| `surface` | #f9f9f6 | The canvas. A warm, paper-like neutral. |
| `surface-container-low` | #f3f4f0 | Secondary sections/Sidebars. |
| `surface-container-lowest` | #ffffff | Primary content cards (The focal point). |
| `primary` | #5f5e5e | Functional elements and primary iconography. |
| `secondary` | #1a6d3f | "Important/Not Urgent" (Q2) – Focus on growth. |
| `tertiary` | #b5272b | "Important/Urgent" (Q1) – Immediate action. |

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders (`#e5e5e0`) to section content in Normal Mode. Boundaries must be defined by **Surface Hierarchy & Nesting**. Place a `surface-container-lowest` card (Pure White) onto a `surface` background (#f9f9f6). The 2-degree shift in luminance is sufficient for the eye to perceive a boundary without the visual "noise" of a line.

### Survival Mode (The Operator)
When Survival Mode is toggled, the system flips to a high-contrast dark state:
- **Background:** `#050505`
- **Neon Accents:** `#ff2d4a` (Urgency), `#ffe347` (Warning), `#3df0ff` (Data).
- **The "Glass & Gradient" Rule:** Use `backdrop-blur` (20px) on survival overlays to allow the "Normal" world to peek through the chaos, creating a sense of a digital "hud" layered over reality.

---

## 3. Typography: Editorial Authority

We use a tri-font strategy to differentiate between narrative, data, and action.

*   **Display & Headline (Manrope):** Chosen for its geometric purity. Use `display-lg` (3.5rem) with tight letter-spacing (-0.02em) for "Mode" headers to create an editorial, high-fashion impact.
*   **Body (Inter):** The workhorse. Use `body-md` (0.875rem) for task descriptions. Its high x-height ensures readability against the `surface` background.
*   **Data & Numbers (Space Grotesk / JetBrains Mono):** For countdowns and task counts, switch to `Space Grotesk` or `JetBrains Mono`. This signals to the user that they are looking at "hard data" vs. "soft content."

---

## 4. Elevation & Depth: Tonal Layering

Rather than using shadows to mimic a physical light source, we use **Tonal Layering** to create a sense of digital "stacking."

*   **The Layering Principle:** 
    1. Base: `surface`
    2. Grouping Container: `surface-container`
    3. Interactive Element: `surface-container-lowest` (Highest perceived elevation).
*   **Ambient Shadows:** If a card requires a floating state (e.g., a dragged task), use a custom shadow: `0px 24px 48px -12px rgba(46, 52, 48, 0.08)`. It must be tinted with the `on-surface` color (#2e3430) to feel integrated.
*   **The "Ghost Border" Fallback:** In Survival Mode, use the `outline-variant` at 20% opacity. This creates a "flickering" electronic feel without closing off the layout entirely.

---

## 5. Components: Refined Interaction

### Cards & Lists
*   **Normal Mode:** `border-radius: 14px`. No dividers. Separate tasks with `16px` of vertical whitespace.
*   **Survival Mode:** `border-radius: 4px`. Add a 1px `outline` using `neon-red` for overdue tasks. Apply a `linear-gradient(rgba(255,255,255,0.05) 50%, transparent 50%)` with a `background-size: 100% 4px` to create the "Scan line" texture.

### Buttons (The "Kinetic" CTA)
*   **Primary:** Uses a subtle gradient from `primary` to `primary_dim`. High-end buttons should feel like "milled aluminum" rather than flat plastic.
*   **Tertiary (Text-only):** Must use `Space Grotesk` in all caps with `0.1em` letter spacing to distinguish from body text.

### Inputs
Avoid the "boxed" look. Use a `surface-container-high` background with a `bottom-border` only that animates from `outline-variant` to `secondary` on focus. This maintains the "Kinetic Archive" aesthetic.

### Survival Countdown Timer
A massive, screen-filling component using `Orbitron` or `Manrope-Bold`. The timer should utilize a `text-shadow` effect: `0 0 10px #ff2d4a` to simulate CRT glow.

---

## 6. Do's and Don'ts

### Do:
*   **Embrace Asymmetry:** Align high-level stats to the right while titles are on the left.
*   **Use Redundant Indicators:** For Q1-Q4 tasks, use both color AND a symbol (e.g., ◈ for Q1, ◇ for Q4) to ensure accessibility for color-blind users.
*   **Prioritize Breathing Room:** If a layout feels "crowded," remove lines before you reduce font size.

### Don't:
*   **Don't use 100% Black for Text:** Use `on-surface` (#2e3430) in Normal Mode to avoid harsh visual vibration against the warm background.
*   **Don't use Standard Shadows:** Never use `rgba(0,0,0,0.5)`. Shadows must be large, soft, and tinted.
*   **Don't mix Corner Radii:** Keep the 14px (Normal) and 4px (Survival) separate. Mixing them breaks the "Persona" logic of the app.