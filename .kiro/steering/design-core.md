---
inclusion: manual
---

# Yami Design System — Core
> **Always injected on every UI task.**
> Contains: global tokens, layout rules, and all common components.
> Figma: https://www.figma.com/design/6oOAy72DBff4P6NzJYc2hi/YAMI-UI-UX-Guidelines
>
> **Only one additional file may be loaded:** `components/product-card.md`
> Load it only when the task requires displaying product listings or grids.

---

## 0. Token Usage Rule — Read First

UI components must only reference **Semantic Tokens** (Section 3).
Primitive tokens (`red/*`, `neutral/*`, etc.) are definition references only — never use them directly in component CSS.
If no semantic token fits, use the closest primitive and document the reason in the design reasoning log.

---

## 1. Visual Theme

Warm-commercial and trust-forward. Clean white canvases with generous breathing room. Yami Red anchors every CTA. Density: **medium-airy**. Every decision serves clarity and conversion — nothing decorative without purpose.

**Key attributes:** Clean, confident, warm, structured, bilingual-ready.

---

## 2. Primitive Color Scales (Definition Reference Only)

### Brand
| Token | Hex | Role |
|---|---|---|
| `brand/primary` | `#FF0000` | Logo, marketing only — never in UI |
| `brand/secondary` | `#222222` | Dark surfaces |
| `brand/tertiary` | `#FBF1EF` | Brand tinted background |
| `brand/inverse` | `#FFFFFF` | Brand on dark |

### Red & Neutral (Key Values)
| Token | Hex | Token | Hex |
|---|---|---|---|
| `red/50` | `#FBF1EF` | `neutral/50` | `#FAFAFA` |
| `red/100` | `#F7DBD6` | `neutral/100` | `#F5F5F5` |
| `red/300` | `#F3867C` | `neutral/200` | `#EBEBEB` |
| `red/400` | `#F8564F` | `neutral/300` | `#D4D4D4` |
| `red/500` | `#E00000` | `neutral/400` | `#B4B4B4` |
| `red/600` | `#C40009` | `neutral/600` | `#727272` |
| `red/700` | `#9B000D` | `neutral/900` | `#222222` |
| `red/950` | `#3D000C` | `neutral/950` | `#0A0A0A` |

### Extended (Key Values)
| Color | /50 | /500 | /600 | /700 |
|---|---|---|---|---|
| Amber | `#FEF7E6` | `#FA8005` | `#D26204` | `#9E4303` |
| Yellow | `#FEFDE6` | `#FABD05` | `#D29604` | `#AA7203` |
| Emerald | `#ECF9F0` | `#3DC24F` | `#33A33D` | `#27812B` |
| Blue | `#F0F3FA` | `#3383FF` | `#0066EB` | `#005CC2` |
| Purple | `#F7F0FF` | `#8B51FF` | `#6C30F7` | `#531EE3` |

---

## 3. Semantic Tokens — Use These in UI

### Background & Surface
| Token | Value | Usage |
|---|---|---|
| `background/primary` | `#FFFFFF` | Page background |
| `background/secondary` | `#F5F5F5` | Secondary page background |
| `surface/primary` | `#FFFFFF` | Cards, panels |
| `surface/secondary` | `#F5F5F5` | Nested areas |
| `surface/inverse` | `#222222` | Dark surfaces |

### Text
| Token | Value | Usage |
|---|---|---|
| `text/primary` | `rgba(0,0,0,0.87)` | Primary body, headlines |
| `text/secondary` | `rgba(0,0,0,0.55)` | Descriptions, secondary labels |
| `text/disabled` | `rgba(0,0,0,0.29)` | Disabled text |
| `text/primary-inverse` | `#FFFFFF` | Text on dark/colored bg |
| `text/secondary-inverse` | `rgba(255,255,255,0.55)` | Secondary on dark |
| `text/disabled-inverse` | `rgba(255,255,255,0.29)` | Disabled on dark |
| `text/emphasis` | `#E00000` | Brand emphasis, key callouts |
| `text/emphasis-inverse` | `#F8564F` | Emphasis on dark |
| `text/error` | `#E00000` | Error messages |
| `text/success` | `#27812B` | Success messages |
| `text/warning` | `#D29604` | Warning messages |
| `text/info` | `#3383FF` | Info messages |

### Border
| Token | Value | Usage |
|---|---|---|
| `border/default` | `rgba(0,0,0,0.08)` | Card borders, dividers, input strokes |
| `border/focus` | `#000000` | Focus ring |
| `border/focus-inverse` | `#FFFFFF` | Focus ring on dark |
| `border/attention` | `#E00000` | Error state borders |
| `border/default-inverse` | `#FFFFFF` | Borders on dark |

### Fill
| Token | Hex | Usage |
|---|---|---|
| `fill/primary` | `#FFFFFF` | Primary fill |
| `fill/secondary` | `#F5F5F5` | Secondary fill |
| `fill/tertiary` | `#FAFAFA` | Subtle background |
| `fill/inverse` | `#222222` | Dark fill |
| `fill/disabled` | `#D4D4D4` | Disabled state |
| `fill/error-primary` | `#E00000` | Error fill |
| `fill/error-secondary` | `#FBF1EF` | Error light fill |
| `fill/success-primary` | `#3DC24F` | Success fill |
| `fill/success-secondary` | `#ECF9F0` | Success light fill |
| `fill/warning-primary` | `#FABD05` | Warning fill |
| `fill/warning-secondary` | `#FEF7E6` | Warning light fill |
| `fill/info-primary` | `#3383FF` | Info fill |
| `fill/info-secondary` | `#F0F3FA` | Info light fill |
| `fill/promotion-primary` | `#E00000` | Promotion fill |
| `fill/promotion-secondary` | `#FBF1EF` | Promotion light fill |
| `fill/highlight` | `#FABD05` | Highlight/callout fill |
| `fill/skeleton` | `rgba(0,0,0,0.10)` | Loading skeleton |

### Button
| Token | Hex | Usage |
|---|---|---|
| `button/emphasis` | `#E00000` | Emphasis button background |
| `button/emphasis-active` | `#C40009` | Emphasis pressed |
| `button/primary` | `#000000` | Primary button background |
| `button/secondary` | `#000000` | Secondary button border |
| `button/tertiary` | `#FFFFFF` | Tertiary button background |
| `button/tertiary-active` | `#F5F5F5` | Tertiary pressed |
| `button/disabled` | `#EBEBEB` | Disabled background |

### Divider & Overlay
| Token | Value |
|---|---|
| `divider/default` | `rgba(0,0,0,0.08)` |
| `divider/subtle` | `rgba(0,0,0,0.04)` |
| `divider/emphasis` | `rgba(0,0,0,0.20)` |
| `divider/default-inverse` | `rgba(255,255,255,0.08)` |
| `overlay/scrim` | `rgba(0,0,0,0.50)` |

### Badge
| Token | Hex | Token | Hex |
|---|---|---|---|
| `badge/bg-primary-neutral` | `#000000` | `badge/bg-secondary-neutral` | `#FFFFFF` |
| `badge/bg-primary-red` | `#E00000` | `badge/bg-secondary-red` | `#FBF1EF` |
| `badge/bg-primary-blue` | `#0066EB` | `badge/bg-secondary-blue` | `#F0F3FA` |
| `badge/bg-primary-green` | `#33A33D` | `badge/bg-secondary-green` | `#ECF9F0` |
| `badge/bg-primary-purple` | `#6C30F7` | `badge/bg-secondary-purple` | `#F7F0FF` |
| `badge/bg-primary-yellow` | `#D26204` | `badge/bg-secondary-yellow` | `#FEF7E6` |
| `badge/fg-primary-red` | `#FFFFFF` | `badge/fg-secondary-red` | `#9B000D` |
| `badge/fg-secondary-blue` | `#005CC2` | `badge/fg-secondary-green` | `#27812B` |
| `badge/fg-secondary-purple` | `#531EE3` | `badge/fg-secondary-yellow` | `#9E4303` |

---

## 4. Typography

### Font Families
| Language | Primary | Fallback Stack |
|---|---|---|
| English | `GT Walsheim` | `"GT Walsheim", -apple-system, BlinkMacSystemFont, sans-serif` |
| 简体中文 | `PingFang SC` | `"PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif` |
| 繁體中文 | `PingFang TC` | `"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif` |
| 日本語 | `Hiragino Sans` | `"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif` |
| 한국어 | `Apple SD Gothic Neo` | `"Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif` |

Rule: GT Walsheim for EN display/brand text only. CJK font for CJK body/labels. Never mix.

### Type Scale
| Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `display-xl` | 32px | 400 | 40px | Large display |
| `display-sm` | 24px | 400 | 32px | Section titles |
| `heading-4xl` | 32px | 500 | 40px | H1 |
| `heading-3xl` | 28px | 500 | 36px | H2 |
| `heading-2xl` | 24px | 400 | 32px | H3 |
| `heading-xl` | 20px | 500 | 28px | H4, modal headers |
| `heading-md` | 18px | 500 | 24px | H5 |
| `heading-sm` | 16px | 500 | 20px | H6, card titles |
| `body-xl` | 16px | 400 | 20px | Primary body |
| `body-md` | 14px | 400 | 20px | Standard body |
| `caption-md` | 12px | 400 | 16px | Helper text, timestamps |
| `caption-sm` | 10px | 400 | 14px | Smallest text |
| `link-md` | 14px | 400 | 20px | Links |
| `strike-md` | 14px | 400 | 20px | Original price |
| `strike-sm` | 12px | 400 | 16px | Small strikethrough |
| `price-md` | 20px | 500 | 28px | Price display |
| `price-sm` | 16px | 500 | 20px | Small price |

### Hero / Landing Display Sizes
| Element | Desktop | Mobile | Weight |
|---|---|---|---|
| Hero Headline | 48–56px | 28–32px | 700 |
| Hero Subheadline | 20–24px | 16–18px | 400 |
| Eyebrow Label | 14px | 12px | 500, uppercase, +0.08em letter-spacing |
| Section Title | 32–36px | 24–28px | 700 |
| CTA Button Text | 16–18px | 16px | 600 |

### Typography Rules
- CJK body line-height: 1.6–1.8x
- Headlines line-height: 1.2–1.3x
- Letter-spacing: 0 body; +0.02–0.08em eyebrow; -0.01em large display
- Paragraph spacing: 4px
- Line length: 60–80 chars (EN), 25–40 chars (CJK)

---

## 5. Spacing

8px-based. All spacing must snap to these tokens.

| Token | Value | Token | Value |
|---|---|---|---|
| `space/space-0` | 0px | `space/space-300` | 24px |
| `space/space-025` | 2px | `space/space-400` | 32px |
| `space/space-050` | 4px | `space/space-500` | 40px |
| `space/space-100` | 8px | `space/space-600` | 48px |
| `space/space-150` | 12px | `space/space-800` | 64px |
| `space/space-200` | 16px | `space/space-1000` | 80px |
| `space/space-250` | 20px | | |

Landing page section padding: 80–100px vertical (desktop), 48–64px (mobile).

---

## 6. Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius/none` | 0px | Table cells, full-bleed |
| `radius/sm` | 4px | Input fields |
| `radius/md` | 8px | Full Buttons |
| `radius/lg` | 12px | Cards, modals, large containers |
| `radius/xl` | 16px | Large rounded containers |
| `radius/full` | 9999px | Inline/Icon buttons, tags, badges |

### Component Radius Mapping
| Component | Token | Notes |
|---|---|---|
| Full Button | `radius/md` (8px) | All hierarchy variants |
| Inline Button | `radius/full` | Pill |
| Icon Button | `radius/full` | Circular |
| Tags / Badges | `radius/full` | Pill |
| Cards | `radius/lg` | All card types |
| Input Fields | `radius/sm` | Form inputs |
| Modals / Bottom Sheets | `radius/lg` | Top corners only for Bottom Sheet |

---

## 7. Elevation & Shadows

| Token | Shadow | Usage |
|---|---|---|
| `elevation-100-canvas` | `0 1px 2px rgba(0,0,0,0.04)` | Page canvas |
| `elevation-200-raised-surface` | `0 2px 4px rgba(0,0,0,0.08)` | Cards hover, sticky nav |
| `elevation-300-tooltip` | `0 4px 8px rgba(0,0,0,0.12)` | Tooltips |
| `elevation-400-menu-panel` | `0 4px 12px rgba(0,0,0,0.16)` | Dropdowns, menus |
| `elevation-500-modal-window` | `0 8px 16px rgba(0,0,0,0.24)` | Modals, popovers |

Flat-first: shadows only on interaction or floating overlays. No decorative shadows at rest.

---

## 8. Stroke & Breakpoints

### Stroke
| Token | Value |
|---|---|
| `stroke/none` | 0px |
| `stroke/default` | 1px |
| `stroke/thick` | 2px |

### Responsive Breakpoints
| Token | Value | Behavior |
|---|---|---|
| `breakpoints/mobile` | 402px | Single column, hamburger |
| `breakpoints/tablet` | 768px | 2-column grids |
| `breakpoints/desktop` | 1024px | Full 12-col layout |
| `breakpoints/desktop-lg` | 1440px | Large desktop |
| `breakpoints/desktop-xl` | 1920px | Extra-large |

---

## 9. Layout

- Max content width: 1200px, horizontally centered
- Grid: 12-column desktop, 16px gutter
- Section rhythm: alternate backgrounds `background/primary` ↔ `neutral/50`
- z-index scale: sticky nav = 100 / modals = 200

---

## 10. Components

> All components have Mobile v2 and PC v2 versions. Never use `[Deprecated]` versions.
> All interactive components require: Default / Hover·Active / Disabled / Loading states.
> Inverse variants: use on `surface/inverse` (`#222222`) backgrounds.

---

### 10.1 Button

#### Types
| Type | Shape | Radius | Description |
|---|---|---|---|
| `Full Button` | Rounded rect | `radius/md` (8px) | Full-width. CTA areas, form submit. |
| `Inline Button` | Pill | `radius/full` | Content-width. Actions within content. |
| `Icon Button` | Circle | `radius/full` | Icon-only. Toolbars, compact scenes. |

#### Hierarchy Styling
| Hierarchy | Background | Text | Border | Limit |
|---|---|---|---|---|
| `Emphasis` | `button/emphasis` `#E00000` | `#FFFFFF` | None | Max 1 per screen |
| `Primary` | `button/primary` `#000000` | `#FFFFFF` | None | — |
| `Secondary` | `transparent` | `#000000` | 1px `button/secondary` | — |
| `Tertiary` | `button/tertiary` `#FFFFFF` | `#000000` | None | — |
| `Link` | — | `text/emphasis` `#E00000` | None | Inline only |

#### Sizes
| Type | Mobile | PC |
|---|---|---|
| Full Button | Large 48px / Medium 40px | Large / Medium |
| Inline Button | Large / Medium / Small | Large / Medium / Small |
| Icon Button | Medium 40px / Small 32px / XSmall 24px | Medium / Small / XSmall |

#### States
| State | Style |
|---|---|
| Hover (PC) | `translateY(-2px)` + light shadow |
| Active | `button/emphasis-active` or darker shade |
| Disabled | `button/disabled` `#EBEBEB` + `text/disabled`, no pointer events |
| Loading | Spinner replaces label — non-interactive |

#### Rules
- Button text starts with a verb: Add, Confirm, Submit, View, Cancel
- Full Button: full container width only — never inline
- Inline Button: content-width only — never stretch
- Prohibited: `neutral/900`, `red/500`, or custom colors as button background

#### Text Link Rules (文字链接规则)

当操作以文字链接形式呈现（非按钮）时：

| 重要程度 | 颜色 | 样式 |
|---------|------|------|
| 高重要度（主操作、核心跳转） | `text/emphasis` `#E00000` | 带下划线 |
| 普通重要度（辅助操作、次要跳转） | `text/primary` `rgba(0,0,0,0.87)` | 带下划线 |

**强制规则：**
- 文字链接必须带下划线（`text-decoration: underline`）
- 文字链接颜色只能是红色（`#E00000`）或黑色（`rgba(0,0,0,0.87)`）
- ❌ 禁止使用蓝色、灰色或其他颜色作为文字链接颜色

---

### 10.2 Modal

#### Types
| Type | Platform | Usage |
|---|---|---|
| `Bottom Sheet` — Dismissible | Mobile | Swipe or overlay tap to dismiss |
| `Bottom Sheet` — Collapsible | Mobile | Expandable/collapsible panel |
| `Centered Dialog` | Desktop | High-attention — requires user action |
| `Corner Dialog` | Desktop | Low-interruption — user can ignore |

#### Desktop: Which to Use

**Use Centered Dialog when ANY is true:**
- User must decide before continuing (confirm / cancel / choose)
- Action is irreversible (delete, submit order, cancel subscription)
- Error or critical warning requiring acknowledgment
- Authentication required (login, register)
- User intentionally triggered it (clicked a button)

**Use Corner Dialog when ALL are true:**
- No decision required — user can ignore and keep browsing
- Low-stakes, reversible
- System-initiated trigger (timer, scroll, page event)
- No negative consequence if dismissed without acting

#### Quick Reference
| Scenario | Type |
|---|---|
| Confirm delete / submit order | Centered Dialog |
| Login / Register | Centered Dialog |
| Important announcement | Centered Dialog |
| NPS survey / satisfaction rating | Corner Dialog |
| New feature announcement | Corner Dialog |
| Coupon offer — system-triggered | Corner Dialog |
| Coupon offer — user clicked | Centered Dialog |

#### Desktop Specs
**Corner Dialog:** `position: fixed; right: 48px; bottom: 48px;` · No overlay · `elevation-500-modal-window` · `radius/lg` · fade-in + `translateY(16px→0)` 300ms ease

**Centered Dialog:** Centered in viewport · `overlay/scrim` (50% black) · `elevation-500-modal-window` · `radius/lg` · `scale(0.95→1)` + `opacity(0→1)` 300ms ease

#### Mobile Specs
Always Bottom Sheet. Never Centered Dialog on mobile.

| Property | Spec |
|---|---|
| Position | Bottom-anchored, full width |
| Overlay | `overlay/scrim` — required |
| Radius | Top `radius/lg`, bottom 0 |
| Animation | `translateY(100%→0)` 300ms ease |
| Safe area | `env(safe-area-inset-bottom)` |

#### Rules
- z-index: 200 (above sticky nav at 100)
- Body scroll: lock on open, restore on close
- Close triggers: ✕ always present; overlay tap for Corner Dialog + dismissible Bottom Sheet; ESC for Centered Dialog

---

### 10.3 Cards

| Variant | Background | Border | Radius | Shadow | Padding |
|---|---|---|---|---|---|
| Content Card | `surface/primary` | 1px `border/default` | `radius/lg` | None at rest; `elevation-200` hover | `space/space-300` |
| Category Card | `neutral/50` | None | `radius/lg` | None | 20–24px |
| Comparison Card | `surface/primary` | 1px `border/default` | `radius/lg` | `elevation-100-canvas` | 24–32px |

Rules: No decorative shadows. Never hardcode `#FFFFFF` — use `surface/primary`.

---

### 10.4 Badge & Tag

- Shape: Pill — `radius/full`
- Padding: `space/space-050` `space/space-150` (4px 12px)
- Text: `caption-md` (12px), weight 500

| Scene | Background | Foreground |
|---|---|---|
| Neutral dark | `badge/bg-primary-neutral` | `#FFFFFF` |
| Sale / Promo | `badge/bg-primary-red` | `badge/fg-primary-red` |
| Info | `badge/bg-primary-blue` | `#FFFFFF` |
| Success | `badge/bg-primary-green` | `#FFFFFF` |
| Price | `badge/bg-primary-yellow` | `#FFFFFF` |
| VIP | `badge/bg-primary-purple` | `#FFFFFF` |
| Light variants | `badge/bg-secondary-*` | `badge/fg-secondary-*` |

---

### 10.5 Form Inputs

| State | Border | Fill | Text |
|---|---|---|---|
| Default | `border/default` | `fill/primary` | `text/primary` |
| Focus | `border/focus` `#000000` 2px | `fill/primary` | `text/primary` |
| Error | `border/attention` `#E00000` | `fill/primary` | `text/error` |
| Disabled | `border/default` | `fill/disabled` | `text/disabled` |

- Radius: `radius/sm` (4px)
- Label: `body-md` or `heading-sm`; Input: `body-md`
- Required field: red `*` marker
- Error message: `caption-md` + `text/error`, below the field
- No shadow on form inputs

---

### 10.6 Navigation (Sticky Nav)

- Background: `surface/primary` + 1px `border/default` bottom
- Height: 64px desktop / 56px mobile
- z-index: 100
- Layout: Logo (left) → Language switcher → CTA button (right)
- Mobile: hamburger collapse, CTA remains visible
- Scroll: optional `backdrop-filter: blur(8px)` glass effect

---

### 10.7 Tabs & Filter

**Tabs:**
- Secondary (underline): page-level navigation
- Tertiary (filled): content filtering within a section
- States: Default / Selected / Skeleton (loading)

**Filter:**
- Multi-select: multiple options active simultaneously
- Toggle: single-select only
- Active state must be visually distinct from default

---

### 10.8 Tooltip

- Shadow: `elevation-300-tooltip`
- Max 2 lines of content
- Placement: Top (default) or Bottom — auto-selects based on space
- Close button: off by default, on when needed

---

### 10.9 Heading Block

| Type | Variants |
|---|---|
| `Heading / Light` | Large / Medium × Default / Title with tab / Only tab |
| `Heading / Dark` | Large / Medium × Default / Title with tab / Only tab |
| `Heading / Skeleton` | Large / Medium |

- Light: on `background/primary` or `neutral/50` sections
- Dark: on `surface/inverse` — text switches to `text/primary-inverse`
- Always use Skeleton during data load

---

## 11. Global Design Decision Rules

### 11.1 Shadow & Stroke

| Component | Shadow | Stroke |
|---|---|---|
| Overlay (Modal, Tooltip, Dropdown, Bottom Sheet) | ✅ Elevation token | ✅ Optional |
| Card | ❌ None at rest; `elevation-200` hover | ✅ `border/default` |
| Banner | ❌ None | ❌ None — use bg color |
| Form input | ❌ None | ✅ `border/default` |
| Button | ❌ None at rest; light shadow hover | By type |

### 11.2 Banner Background Rules

All Banner text: `text/primary`. Background must achieve ≥4.5:1 contrast.

**Approved:** `red/50`, `amber/50`, `yellow/50`, `emerald/50`, `blue/50`, `purple/50`, `neutral/50`, `neutral/100`, `background/primary`

**Prohibited:** `red/300`–`red/600`, `amber/300`–`amber/600`, any `neutral/700`+, any 500+ saturated shade

**Dark exception:** `surface/inverse` (`#222222`) → use `text/primary-inverse` (`#FFFFFF`)

---

## 12. Motion, Accessibility & Multilingual

### Motion
- Default: `200ms ease` (color, bg, shadow, transform)
- Accordion / Bottom Sheet: `300ms ease`
- Scroll reveal: `400ms ease-out`, 100ms stagger
- Button hover: `translateY(-2px)` + shadow
- Reduced motion: respect `prefers-reduced-motion: reduce`

### Accessibility
- Contrast: WCAG AA — ≥4.5:1 normal text, ≥3:1 large text
- Focus: 2px solid `border/focus` (`#000000`), 2px offset
- Keyboard: Tab / Enter / Space / Escape on all interactive elements
- Semantics: `<nav>`, `<main>`, `<section>`, `<h1>`–`<h3>`, ARIA labels, `aria-expanded`
- Touch targets: minimum 44×44px mobile

### Multilingual
- CN text 30–50% shorter than EN — allow flexible container width
- GT Walsheim: load as web font. CJK: system fonts, no download needed
- Language switcher: always in sticky nav, native script labels
