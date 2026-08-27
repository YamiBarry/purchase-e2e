---
inclusion: manual
---

# Impeccable Design Laws

> Source: https://github.com/pbakaus/impeccable (v3.0.7)
> Last synced: 2026-05-10

---

## Shared Design Laws

Apply to every design. Match implementation complexity to the aesthetic vision: maximalism needs elaborate code, minimalism needs precision.

### Color

- Use OKLCH. Reduce chroma as lightness approaches 0 or 100; high chroma at extremes looks garish.
- Never use `#000` or `#fff`. Tint every neutral toward the brand hue (chroma 0.005–0.01 is enough).
- Pick a **color strategy** before picking colors:
  - **Restrained**: tinted neutrals + one accent ≤10%. Product default; brand minimalism.
  - **Committed**: one saturated color carries 30–60% of the surface. Brand default for identity-driven pages.
  - **Full palette**: 3–4 named roles, each used deliberately. Brand campaigns; product data viz.
  - **Drenched**: the surface IS the color. Brand heroes, campaign pages.
- The "one accent ≤10%" rule is Restrained only. Committed / Full palette / Drenched exceed it on purpose.

### Theme

Dark vs. light is never a default. Before choosing, write one sentence of physical scene: who uses this, where, under what ambient light, in what mood. If the sentence doesn't force the answer, add detail until it does.

### Typography

- Cap body line length at 65–75ch (EN) or 25–40ch (CJK).
- Hierarchy through scale + weight contrast (≥1.25 ratio between steps). Avoid flat scales.

### Layout

- Vary spacing for rhythm. Same padding everywhere is monotony.
- Cards are the lazy answer. Use them only when they're truly the best affordance. Nested cards are always wrong.
- Don't wrap everything in a container. Most things don't need one.

### Motion

- Don't animate CSS layout properties (width, height, top, left).
- Ease out with exponential curves (ease-out-quart / quint / expo). No bounce, no elastic.

### Absolute Bans

Match-and-refuse. If you're about to write any of these, rewrite the element with different structure.

- **Side-stripe borders.** `border-left` or `border-right` greater than 1px as a colored accent on cards, list items, callouts, or alerts. Rewrite with full borders, background tints, leading numbers/icons, or nothing.
- **Gradient text.** `background-clip: text` combined with a gradient background. Use a single solid color. Emphasis via weight or size.
- **Glassmorphism as default.** Blurs and glass cards used decoratively. Rare and purposeful, or nothing.
- **The hero-metric template.** Big number, small label, supporting stats, gradient accent. SaaS cliché.
- **Identical card grids.** Same-sized cards with icon + heading + text, repeated endlessly.
- **Modal as first thought.** Modals are usually laziness. Exhaust inline / progressive alternatives first.

### Copy

- Every word earns its place. No restated headings, no intros that repeat the title.
- **No em dashes.** Use commas, colons, semicolons, periods, or parentheses.

### The AI Slop Test

If someone could look at this interface and say "AI made that" without doubt, it's failed.

**Category-reflex check (two altitudes):**

- **First-order:** if someone could guess the theme + palette from the category alone ("observability → dark blue", "healthcare → white + teal"), it's the first training-data reflex. Rework until the answer isn't obvious from the domain.
- **Second-order:** if someone could guess the aesthetic family from category-plus-anti-references, it's the trap one tier deeper. Rework until both answers are not obvious.

---

## Commands Reference

| Command | Category | Description |
|---|---|---|
| `craft` | Build | Shape, then build a feature end-to-end |
| `shape` | Build | Plan UX/UI before writing code |
| `critique` | Evaluate | UX design review with heuristic scoring |
| `audit` | Evaluate | Technical quality checks (a11y, perf, responsive) |
| `polish` | Refine | Final quality pass before shipping |
| `bolder` | Refine | Amplify safe or bland designs |
| `quieter` | Refine | Tone down aggressive or overstimulating designs |
| `distill` | Refine | Strip to essence, remove complexity |
| `harden` | Refine | Production-ready: errors, i18n, edge cases |
| `animate` | Enhance | Add purposeful animations and motion |
| `colorize` | Enhance | Add strategic color to monochromatic UIs |
| `typeset` | Enhance | Improve typography hierarchy and fonts |
| `layout` | Enhance | Fix spacing, rhythm, and visual hierarchy |
| `delight` | Enhance | Add personality and memorable touches |
| `clarify` | Fix | Improve UX copy, labels, and error messages |
| `adapt` | Fix | Adapt for different devices and screen sizes |
| `optimize` | Fix | Diagnose and fix UI performance |
