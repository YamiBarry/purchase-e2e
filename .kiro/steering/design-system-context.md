---
inclusion: manual
---

# YAMI Design System Context

**Source of truth for AI-assisted UI generation.**
Ensures every screen, component, and page follows the same visual rules.

> **Figma:** [YAMI UI/UX Guidelines](https://www.figma.com/design/6oOAy72DBff4P6NzJYc2hi/YAMI-UI-UX-Guidelines)
> **Usage:** Place in `.kiro/steering/` — Kiro Agent will auto-inject on every UI generation task.

---

## 1. Visual Theme & Atmosphere

Warm-commercial and trust-forward. Yami's aesthetic bridges consumer-facing vibrancy with B2B professionalism — approachable yet authoritative, like a well-curated marketplace showroom. Clean white canvases provide generous breathing room, while the signature Yami Red anchors every call-to-action with urgency and brand recognition.

The overall density is **medium-airy**: generous section padding prevents cognitive overload, guiding the eye through a deliberate narrative arc. Every design decision serves clarity and conversion — nothing decorative without purpose.

**Key attributes:** Clean, confident, warm, structured, bilingual-ready.

---

## 2. Color System

### 2.1 Brand Color — Dual Anchor Strategy

Yami uses a **dual-anchor** approach: a pure brand red for identity/marketing, and a slightly adjusted UI red for interface elements that meets WCAG AA contrast requirements.

| Token | Hex | Role |
|---|---|---|
| `brand/primary` | `#FF0000` | Logo, advertising key visuals, marketing collateral. **Do not use** for body text or large UI backgrounds. |
| `brand/secondary` | `#222222` | Secondary brand color, dark surfaces |
| `brand/tertiary` | `#FBF1EF` | Brand tinted background |
| `brand/inverse` | `#FFFFFF` | Brand on dark background |

### 2.2 UI Red Scale (Primitives)

| Token | Hex | Usage |
|---|---|---|
| `red/50` | `#FBF1EF` | Error/alert background fills, hover tint on light surfaces |
| `red/100` | `#F7DBD6` | Subtle highlight backgrounds, selected row tint |
| `red/200` | `#F4B7AE` | Light accent borders, progress bar tracks |
| `red/300` | `#F3867C` | Decorative accents, illustration fills |
| `red/400` | `#F8564F` | Hover state for primary buttons, secondary emphasis |
| `red/500` | `#E00000` | **UI Primary** — buttons, active links, key CTAs (WCAG AA ≥4.5:1) |
| `red/600` | `#C40009` | Pressed/active state for primary buttons |
| `red/700` | `#9B000D` | Dark emphasis, high-contrast text |
| `red/800` | `#7A0010` | Reserved for extreme emphasis |
| `red/900` | `#57000F` | Deep tones for dark-theme surfaces |
| `red/950` | `#3D000C` | Deepest red — use sparingly |

### 2.3 Neutral Scale (Primitives)

| Token | Hex | Usage |
|---|---|---|
| `neutral/50` | `#FAFAFA` | Page background, alternating section tint |
| `neutral/100` | `#F5F5F5` | Card backgrounds, input fills, sidebar surfaces |
| `neutral/200` | `#EBEBEB` | Dividers, subtle borders, disabled input backgrounds |
| `neutral/300` | `#D4D4D4` | Border default, separator lines |
| `neutral/400` | `#B4B4B4` | Placeholder text, inactive icons |
| `neutral/500` | `#949494` | Secondary icons, helper text |
| `neutral/600` | `#727272` | Tertiary text, captions, metadata |
| `neutral/700` | `#525252` | Secondary body text |
| `neutral/800` | `#393939` | Primary body text alternative |
| `neutral/900` | `#222222` | Headlines, high-emphasis text |
| `neutral/950` | `#0A0A0A` | Near-black, maximum contrast |

### 2.4 Extended Color Scales (Primitives)

| Color | 50 | 500 | 600 | 700 | Usage |
|---|---|---|---|---|---|
| **Amber** | `#FEF7E6` | `#FA8005` | `#D26204` | `#9E4303` | Warnings, promotional highlights, price callouts |
| **Yellow** | `#FEFDE6` | `#FABD05` | `#D29604` | `#AA7203` | Highlights, badges |
| **Emerald** | `#ECF9F0` | `#3DC24F` | `#33A33D` | `#27812B` | Success states, positive metrics |
| **Blue** | `#F0F3FA` | `#3383FF` | `#0066EB` | `#005CC2` | Informational messages (use sparingly — Red is primary) |
| **Purple** | `#F7F0FF` | `#8B51FF` | `#6C30F7` | `#531EE3` | Special promotions, loyalty/VIP tiers |

### 2.5 Semantic Colors (Use These in UI)

#### Background & Surface
| Token | Value | Usage |
|---|---|---|
| `background/primary` | `#FFFFFF` | Page main background |
| `background/secondary` | `#F5F5F5` | Secondary page background |
| `surface/primary` | `#FFFFFF` | Cards, panels |
| `surface/secondary` | `#F5F5F5` | Nested areas |
| `surface/inverse` | `#222222` | Dark background surfaces |

#### Text — Alpha-Based for Consistency Across Backgrounds
| Token | Value | Usage |
|---|---|---|
| `text/primary` | `#000000DE` (87% black) | Primary body text, headlines |
| `text/secondary` | `#0000008C` (55% black) | Descriptions, secondary labels |
| `text/disabled` | `#0000004A` (29% black) | Disabled text, inactive labels |
| `text/primary-inverse` | `#FFFFFF` | Text on dark/colored backgrounds |
| `text/secondary-inverse` | `#FFFFFF` (55% opacity) | Secondary text on dark backgrounds |
| `text/disabled-inverse` | `#FFFFFF` (29% opacity) | Disabled text on dark backgrounds |
| `text/emphasis` | `#E00000` | Brand emphasis, key callouts |
| `text/emphasis-inverse` | `#F8564F` | Emphasis on dark background |
| `text/error` | `#E00000` | Error messages |
| `text/success` | `#27812B` | Success messages |
| `text/warning` | `#D29604` | Warning messages |
| `text/info` | `#3383FF` | Info messages |

#### Border
| Token | Value | Usage |
|---|---|---|
| `border/default` | `#00000014` (8% black) | Card borders, dividers, input strokes |
| `border/focus` | `#000000` | Focus ring on interactive elements |
| `border/focus-inverse` | `#FFFFFF` | Focus ring on dark backgrounds |
| `border/attention` | `#E00000` | Error state borders |
| `border/default-inverse` | `#FFFFFF` | Borders on dark backgrounds |

#### Fill
| Token | Hex | Usage |
|---|---|---|
| `fill/primary` | `#FFFFFF` | Primary fill |
| `fill/secondary` | `#F5F5F5` | Secondary fill |
| `fill/tertiary` | `#FAFAFA` | Subtle background |
| `fill/inverse` | `#222222` | Dark fill |
| `fill/disabled` | `#D4D4D4` | Disabled state fill |
| `fill/warning-primary` | `#FABD05` | Warning fill |
| `fill/warning-secondary` | `#FEF7E6` | Warning light fill |
| `fill/success-primary` | `#3DC24F` | Success fill |
| `fill/success-secondary` | `#ECF9F0` | Success light fill |
| `fill/error-primary` | `#E00000` | Error fill |
| `fill/error-secondary` | `#FBF1EF` | Error light fill |
| `fill/info-primary` | `#3383FF` | Info fill |
| `fill/info-secondary` | `#F0F3FA` | Info light fill |
| `fill/promotion-primary` | `#E00000` | Promotion fill |
| `fill/promotion-secondary` | `#FBF1EF` | Promotion light fill |
| `fill/highlight` | `#FABD05` | Highlight/callout fill |
| `fill/skeleton` | `#000000` (10% opacity) | Loading skeleton |

#### Button Tokens
| Token | Hex | Usage |
|---|---|---|
| `button/emphasis` | `#E00000` | Emphasis button background |
| `button/emphasis-active` | `#C40009` | Emphasis button pressed |
| `button/primary` | `#000000` | Primary button background |
| `button/secondary` | `#000000` | Secondary button border |
| `button/tertiary` | `#FFFFFF` | Tertiary button background |
| `button/tertiary-active` | `#F5F5F5` | Tertiary button pressed |
| `button/disabled` | `#EBEBEB` | Disabled button background |

#### Divider
| Token | Usage |
|---|---|
| `divider/default` | Default divider (8% black) |
| `divider/subtle` | Subtle divider (4% black) |
| `divider/emphasis` | Strong divider (20% black) |
| `divider/default-inverse` | Divider on dark (8% white) |

#### Overlay
| Token | Usage |
|---|---|
| `overlay/scrim` | Modal backdrop (`#000000` at 50% opacity) |

#### Badge Color Tokens
| Token | Hex | Usage |
|---|---|---|
| `badge/bg-primary-neutral` | `#000000` | Dark neutral badge |
| `badge/bg-secondary-neutral` | `#FFFFFF` | Light neutral badge |
| `badge/bg-tertiary-neutral` | `#F5F5F5` | Subtle neutral badge |
| `badge/bg-primary-red` | `#E00000` | Sale / promo badge |
| `badge/bg-primary-yellow` | `#D26204` | Price badge |
| `badge/bg-primary-blue` | `#0066EB` | Info badge |
| `badge/bg-primary-green` | `#33A33D` | Success badge |
| `badge/bg-primary-purple` | `#6C30F7` | VIP / exclusive badge |
| `badge/bg-secondary-green` | `#ECF9F0` | Light success badge |
| `badge/bg-secondary-blue` | `#F0F3FA` | Light info badge |
| `badge/bg-secondary-purple` | `#F7F0FF` | Light VIP badge |
| `badge/bg-secondary-yellow` | `#FEF7E6` | Light price badge |
| `badge/bg-secondary-red` | `#FBF1EF` | Light promo badge |
| `badge/fg-primary-red` | `#FFFFFF` | Text on red badge |
| `badge/fg-secondary-red` | `#9B000D` | Text on light red badge |
| `badge/fg-secondary-blue` | `#005CC2` | Text on light blue badge |
| `badge/fg-secondary-green` | `#27812B` | Text on light green badge |
| `badge/fg-secondary-purple` | `#531EE3` | Text on light purple badge |
| `badge/fg-secondary-yellow` | `#9E4303` | Text on light yellow badge |

---

## 3. Typography

### 3.1 Font Families — Per Language

| Language | Font Family | Fallback Stack |
|---|---|---|
| **English** | `GT Walsheim` | `"GT Walsheim", -apple-system, BlinkMacSystemFont, sans-serif` |
| **简体中文** | `PingFang SC` | `"PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif` |
| **繁體中文** | `PingFang TC` | `"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif` |
| **日本語** | `Hiragino Sans` | `"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif` |
| **한국어** | `Apple SD Gothic Neo` | `"Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif` |

**Rules:** Always use GT Walsheim for EN display/brand text. Use locale-specific CJK font for body text and UI labels. Never mix — GT Walsheim for CJK or PingFang for EN headlines.

### 3.2 Type Scale (Figma Tokens)

| Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `display-xl` | 32px | Regular (400) | 40px | Large display titles |
| `display-md` | 28px | Regular (400) | 36px | Display titles |
| `display-sm` | 24px | Regular (400) | 32px | Section titles, hero sub-headlines |
| `heading-4xl` | 32px | Medium (500) | 40px | H1 |
| `heading-3xl` | 28px | Medium (500) | 36px | H2 |
| `heading-2xl` | 24px | Regular (400) | 32px | H3 |
| `heading-xl` | 20px | Medium (500) | 28px | H4, card group titles, modal headers |
| `heading-md` | 18px | Medium (500) | 24px | H5 |
| `heading-sm` | 16px | Medium (500) | 20px | H6, card titles, step labels |
| `body-xl` | 16px | Regular (400) | 20px | Primary body text, descriptions |
| `body-md` | 14px | Regular (400) | 20px | Standard body text |
| `caption-md` | 12px | Regular (400) | 16px | Helper text, timestamps, footnotes |
| `caption-sm` | 10px | Regular (400) | 14px | Smallest text |
| `link-xl` | 16px | Regular (400) | 20px | Large links |
| `link-md` | 14px | Regular (400) | 20px | Standard links |
| `link-sm` | 12px | Regular (400) | 16px | Small links |
| `strike-md` | 14px | Regular (400) | 20px | Strikethrough — original price |
| `strike-sm` | 12px | Regular (400) | 16px | Small strikethrough |
| `price-md` | 20px | Medium (500) | 28px | Price display |
| `price-sm` | 16px | Medium (500) | 20px | Small price display |

### 3.3 Large Display Sizes (Landing Page / Hero)

| Element | Desktop | Mobile | Weight |
|---|---|---|---|
| Hero Headline | 48–56px | 28–32px | Bold (700) |
| Hero Subheadline | 20–24px | 16–18px | Regular (400) |
| Eyebrow Label | 14px | 12px | Medium (500), uppercase, letter-spacing +0.08em |
| Section Title | 32–36px | 24–28px | Bold (700) |
| CTA Button Text | 16–18px | 16px | Semi-Bold (600) |

### 3.4 Typography Guidelines

- **CJK line-height:** 1.6–1.8x for body text (characters need more vertical room than Latin)
- **Headlines line-height:** 1.2–1.3x for display/heading sizes
- **Letter-spacing:** 0 for body; +0.02–0.08em for eyebrow/label; -0.01em for large display
- **Paragraph spacing:** 4px between consecutive paragraphs
- **Line length:** 60–80 characters (EN) or 25–40 characters (CJK) per line

---

## 4. Spacing

8px-based scale. All spacing must snap to these tokens.

| Token | Value | Common Use |
|---|---|---|
| `space/space-0` | 0px | Reset |
| `space/space-025` | 2px | Micro-adjustments, icon-to-text gap |
| `space/space-050` | 4px | Tight internal padding, tag padding-y |
| `space/space-100` | 8px | Small gaps, compact spacing |
| `space/space-150` | 12px | Medium-small gaps |
| `space/space-200` | 16px | Standard internal padding, element gaps |
| `space/space-250` | 20px | Medium gaps |
| `space/space-300` | 24px | Card padding, section sub-gaps |
| `space/space-400` | 32px | Section internal padding |
| `space/space-500` | 40px | Large gaps |
| `space/space-600` | 48px | Section separation (mobile) |
| `space/space-800` | 64px | Large section separation |
| `space/space-1000` | 80px | Maximum spacing |

**Landing page section padding:** 80–100px vertical (desktop), 48–64px (mobile). Generous whitespace is non-negotiable.

---

## 5. Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius/none` | 0px | Table cells, full-bleed sections |
| `radius/sm` | 4px | Buttons, input fields, small elements |
| `radius/md` | 8px | Standard components |
| `radius/lg` | 12px | Cards, modals, large containers |
| `radius/xl` | 16px | Large rounded containers |
| `radius/full` | 9999px | Tags, badges, pill buttons, avatar containers |

### Component Radius Mapping
| Component | Token |
|---|---|
| Emphasis / Primary Button | `radius/full` (pill shape) |
| Tags / Badges | `radius/full` |
| Cards | `radius/lg` (12px) |
| Input Fields | `radius/sm` (4px) |
| Modals | `radius/lg` (12px) |

---

## 6. Elevation & Shadows

| Token | Shadow | Usage |
|---|---|---|
| `elevation-100-canvas` | `0 1px 2px rgba(0,0,0,0.04)` | Page canvas base |
| `elevation-200-raised-surface` | `0 2px 4px rgba(0,0,0,0.08)` | Raised cards, sticky nav |
| `elevation-300-tooltip` | `0 4px 8px rgba(0,0,0,0.12)` | Tooltips |
| `elevation-400-menu-panel` | `0 4px 12px rgba(0,0,0,0.16)` | Dropdowns, menus, panels |
| `elevation-500-modal-window` | `0 8px 16px rgba(0,0,0,0.24)` | Modals, popovers |

**Philosophy:** Flat-first — shadows appear only on interaction (hover, focus) or for floating overlays. No drop shadows at rest on most elements.

---

## 7. Stroke

| Token | Value |
|---|---|
| `stroke/none` | 0px |
| `stroke/default` | 1px |
| `stroke/thick` | 2px |

---

## 8. Responsive Breakpoints

| Token | Value | Behavior |
|---|---|---|
| `breakpoints/mobile` | 402px | Single column, hamburger menu, stacked layout |
| `breakpoints/tablet` | 768px | 2-column grids, nav stays full-width |
| `breakpoints/desktop` | 1024px | Full layout, 12-col grid, all sections side-by-side |
| `breakpoints/desktop-lg` | 1440px | Large desktop |
| `breakpoints/desktop-xl` | 1920px | Extra-large screen |

---

## 9. Layout Principles

- **Max content width:** 1200px, horizontally centered
- **Grid:** 12-column desktop, 16px gutter
- **Hero:** Full viewport width, content constrained to max-width
- **Category cards:** 4×2 grid (desktop) → 2-column (tablet) → 1–2 column (mobile)
- **Section rhythm:** Alternate backgrounds between `#FFFFFF` and `neutral/50` (`#FAFAFA`) for visual separation without heavy dividers

---

## 10. Core Components

> All components have **Mobile v2** and **PC v2** versions. Always specify platform. Never use `[Deprecated]` versions.

### 10.1 Button 按钮

#### Component Types
| Type | Description |
|---|---|
| `Full` | Full-width button with text (primary action) |
| `Inline` | Inline button, content-width |
| `Icon` | Icon-only button |

#### Variants
| Property | Mobile v2 | PC v2 |
|---|---|---|
| **Type** | Emphasis / Primary / Secondary / Tertiary / Link | Same |
| **Size (Full)** | Large / Medium | Large / Medium |
| **Size (Inline)** | Medium / Small / XSmall | Large / Medium / Small |
| **State** | Default / Active / Disabled / Loading | Default / Hover·Active / Disabled / Loading |

#### Type Usage Rules
| Type | Color | Scene |
|---|---|---|
| `Emphasis` | `button/emphasis` `#E00000` | Most important action — max 1 per screen (e.g. "Add to Cart") |
| `Primary` | `button/primary` `#000000` | Main action (e.g. "Confirm", "Submit") |
| `Secondary` | `button/secondary` `#000000` outline | Secondary action (e.g. "Cancel", "Back") |
| `Tertiary` | `button/tertiary` `#FFFFFF` no border | Weak action (e.g. "View Details") |
| `Link` | `text/emphasis` `#E00000` | Text link |

#### Styling
| Variant | Background | Text | Border | Radius | Height |
|---|---|---|---|---|---|
| Emphasis | `#E00000` | `#FFFFFF` | None | `radius/full` | 48px (L) / 40px (M) |
| Primary | `#000000` | `#FFFFFF` | None | `radius/full` | 48px (L) / 40px (M) |
| Secondary | `transparent` | `#000000` | 1px `#000000` | `radius/full` | 48px (L) / 40px (M) |
| Tertiary | `transparent` | `#000000` | None | `radius/full` | 48px (L) / 40px (M) |

#### Rules
- Emphasis appears max 1 time per CTA area
- Button text starts with a verb (Add, Confirm, Submit, Cancel)
- Disabled: `button/disabled` `#EBEBEB` background + `text/disabled`
- Loading: replace icon with spinner, non-interactive
- Inverse versions (on `surface/inverse`): add `-Inverse` suffix variant

---

### 10.2 Tabs 选项卡

#### Variants
| Property | Values |
|---|---|
| **Style** | Secondary (underline) / Tertiary (filled background) |
| **Theme** | Default (light) / Inverse (dark background) |
| **TabList State** | Default / Skeleton screen |
| **TabItem State** | Default / Selected |

#### Rules
- Secondary (underline): page-level navigation
- Tertiary (filled): content filtering / switching
- Skeleton screen for loading placeholder

---

### 10.3 Filter 筛选

#### Types
| Type | Description |
|---|---|
| `Multi-select Filter` | Multi-select expandable filter |
| `Toggle Filter` | Single-select toggle switch |

#### Variants
**Multi-select Button:** State (Default / Active) × Icon (Left / Right / None / Only Icon)
**Toggle Button:** State (OFF / ON)

#### Rules
- Active state = filter condition applied, must be visually distinct

---

### 10.4 Badge 徽章

#### Types
| Type | Description |
|---|---|
| `Badge / Mobile` | Mobile product label |
| `Badge / PC` | PC product label |
| `Top Seller` | Bestseller marker — Official / Gold / Silver |
| `Membership / tag` | Member tier tag — Ruby / Ruby-0 / Silver / Gold |
| `Badge / icon` | Icon badge — Number / VVIP / Sale |

#### Badge Type Values
`Best Sellers` / `Sale` / `New` / `Low price` / `Hot` / `Exclusive` / `Choice` / `Price` / `Discount`

#### Styling
- **Shape:** Pill (`border-radius: 9999px`)
- **Padding:** 4px 12px
- **Text:** `caption-md` (12px), Medium (500)

#### Color Selection
| Scene | Background Token | Foreground Token |
|---|---|---|
| Neutral dark | `badge/bg-primary-neutral` | `badge/fg-default-inverse` |
| Sale / Promo | `badge/bg-primary-red` | `badge/fg-primary-red` |
| Info | `badge/bg-primary-blue` | `#FFFFFF` |
| Success | `badge/bg-primary-green` | `#FFFFFF` |
| Price highlight | `badge/bg-primary-yellow` | `#FFFFFF` |
| VIP / Exclusive | `badge/bg-primary-purple` | `#FFFFFF` |
| Light variants | `badge/bg-secondary-*` | `badge/fg-secondary-*` |

---

### 10.5 Heading 标题区块

#### Types & Variants
| Type | Size Variants | Style Variants |
|---|---|---|
| `Heading / Light` | Large / Medium | Default / Title with tab / Only tab |
| `Heading / Dark` | Large / Medium | Default / Title with tab / Only tab |
| `Heading / Skeleton screen` | Large / Medium | — |

#### Rules
- `Title with tab`: section title with tabs on the right
- `Only tab`: tabs only, no title text
- Always use skeleton variant during data load

---

### 10.6 Navigation 导航 (PC v2)

| Component | Variants |
|---|---|
| `Entrance Item` | State: Default / Hover |
| `Cart` | State: Empty / Default / Hover |
| `Account` | Login: Default / Logged in; State: Default / Hover |
| `Search` | State: Default / Filled / Typing |
| `Pill Button` | Type: Zipcode / Language; State: Default / Hover |
| `Header` | State: Default / Slide (sticky); Size: ≥1440px / <1440px |

#### Sticky Navigation Specs
- Background: `#FFFFFF` + bottom border 1px `border/default`
- Height: 64px (desktop) / 56px (mobile)
- Z-index: 100
- Scroll behavior: Header Slide state on scroll

---

### 10.7 Product Card 商品卡片

#### Component Types (Use Latest Versions)
| Type | Platform | Description |
|---|---|---|
| `Mobile Vertical V7` | Mobile | Vertical card, latest version ✅ |
| `PC Vertical V6` | PC | Vertical card, multi-layout ✅ |
| `Horizontal V6` | Both | Horizontal card |
| `Mobile Mini V5` | Mobile | Mini card |
| `Product List / Grid` | Mobile | Grid layout |

#### PC Card Variants
- **Info:** Default / Mini Info / Price + Add to Cart / Only Price / Only Image / Mini Info Vertical
- **Style:** Card / List-1 / List-2
- **Page:** Homepage / List page / Default

#### Add to Cart Button States
| State | Description |
|---|---|
| `Add to cart` | Default, purchasable |
| `Sold Out` | Out of stock |
| `Get Restock Alerts` | Notify when back |
| `Add to cart - Edit` | Editing quantity |
| `Add to cart - Done` | Added to cart |

#### Rules
- Price: `price-md` / `price-sm` for sale price + `strike-md` / `strike-sm` for original price
- Badge overlay supported on product image area
- Mobile uses V7, PC uses V6 — never use deprecated versions

---

### 10.8 Forms 表单输入

#### State Rules
| State | Border | Fill | Text |
|---|---|---|---|
| Default | `border/default` | `fill/primary` | `text/primary` |
| Focus | `border/focus` `#000000` 2px | `fill/primary` | `text/primary` |
| Error | `border/attention` `#E00000` | `fill/primary` | `text/error` |
| Disabled | `border/default` | `fill/disabled` `#D4D4D4` | `text/disabled` |

#### Rules
- Required fields: red `*` marker
- Label: `body-md` or `heading-sm`; Input: `body-md`
- Error message below field: `caption-md` + `text/error`

---

### 10.9 Modal 弹窗

#### Types
| Type | Usage |
|---|---|
| `Bottom Sheet` — Dismissible | Mobile primary modal, dismissible |
| `Bottom Sheet` — Collapsible | Mobile, collapsible/expandable |
| `Dialog / Alert Dialog` | Desktop centered dialog |
| `Corner Dialog` | Desktop non-intrusive floating dialog |

#### Header Variants: Navigation / Drop down / Handle

#### PC 弹窗场景选择

根据业务场景选择合适的弹窗形式：

| 场景 | 弹窗类型 | 位置 | 蒙版 | 适用场景示例 |
|------|---------|------|------|-------------|
| **低打扰** | Corner Dialog | 右下角悬浮 | ❌ 无蒙版 | NPS 评分、客服满意度、非紧急通知、引导提示 |
| **强关注** | Centered Dialog | 页面居中 | ✅ 黑色透明蒙版 | 确认操作、错误提示、重要公告、登录/注册 |

**低打扰场景（Corner Dialog）规格：**
- 位置：`position: fixed; right: 48px; bottom: 48px;`
- 蒙版：无（用户可继续浏览页面）
- 阴影：`elevation-500-modal-window`
- 圆角：`radius/lg` (12px)
- 动画：fade-in + translateY(16px→0), 300ms ease

**强关注场景（Centered Dialog）规格：**
- 位置：页面垂直水平居中
- 蒙版：`overlay/scrim` (`#000000` at 50% opacity)
- 阴影：`elevation-500-modal-window`
- 圆角：`radius/lg` (12px)
- 动画：scale(0.95→1) + opacity(0→1), 300ms ease

#### Mobile 弹窗规则

Mobile 端统一使用 Bottom Sheet 形式：

| 属性 | 规格 |
|------|------|
| 位置 | 底部吸附，全宽 |
| 蒙版 | ✅ 必须使用 `overlay/scrim` (`#000000` at 50% opacity) |
| 圆角 | 顶部 `radius/lg` (12px)，底部 0 |
| 动画 | translateY(100%→0), 300ms ease |
| Handle | 顶部居中显示拖拽条（可选） |
| Safe Area | 底部需考虑 `env(safe-area-inset-bottom)` |

#### Rules
- Mobile: 统一使用 Bottom Sheet + 黑色透明蒙版
- Desktop 低打扰: 使用 Corner Dialog，右下角悬浮，无蒙版
- Desktop 强关注: 使用 Centered Dialog，居中 + 黑色透明蒙版
- Shadow: `elevation-500-modal-window`
- Animation: 300ms ease

---

### 10.10 Tooltip 提示

#### Variants
| Property | Values |
|---|---|
| Close button | Off (default) / On |
| Placement | Top / Bottom |

#### Rules
- Shadow: `elevation-300-tooltip`
- Max 2 lines of content
- Placement auto-selects based on available space

---

### 10.11 Cards (General)

| Variant | Background | Border | Radius | Shadow | Padding |
|---|---|---|---|---|---|
| Content Card | `#FFFFFF` | 1px `border/default` | `radius/lg` 12px | None at rest; `elevation-200` on hover | 24px |
| Category Card | `neutral/50` | None | `radius/lg` 12px | None | 20–24px |
| Comparison Card | `#FFFFFF` | 1px `border/default` | `radius/lg` 12px | `elevation-100` | 24–32px |

---

## 11. Component Universal Rules

- **Platform:** Always use `Mobile v2` or `PC v2` — never `[Deprecated]` versions
- **States:** All interactive components require 4 states: Default / Hover·Active / Disabled / Loading (where applicable)
- **Inverse:** Use `-Inverse` variant on `surface/inverse` (`#222222`) backgrounds
- **Skeleton:** Use skeleton variants during data load; color: `fill/skeleton` (10% black)
- **Language:** Components support `EN` and `CN` variants — account for text width differences (CN is 30–50% shorter than EN)

---

## 11.5 Design Decision Rules (设计决策规则)

以下规则用于指导 AI Agent 在生成设计时的决策，确保输出符合 Yami 设计语言。

### 11.5.1 Banner 背景色与文字规则

**Banner 背景可使用色彩库中任意颜色，但必须确保文字可读性符合 WCAG AA 标准。**

#### 文字颜色规则
- Banner 上的文字统一使用 `text/primary`（`rgba(0,0,0,0.87)`）
- 背景色必须与 `text/primary` 形成 ≥4.5:1 的对比度（WCAG AA 标准）

#### 推荐背景色（已验证对比度）

以下颜色与 `text/primary` 的对比度均 ≥4.5:1，可直接使用：

| 背景色 | Token | Hex | 对比度 | 适用场景 |
|---|---|---|---|---|
| 品牌浅红 | `red/50` | `#FBF1EF` | ~12:1 | 促销、活动、品牌相关 Banner |
| 品牌浅红 | `brand/tertiary` | `#FBF1EF` | ~12:1 | 品牌相关 Banner |
| 琥珀浅色 | `amber/50` | `#FEF7E6` | ~12:1 | 警告、价格相关 Banner |
| 黄色浅色 | `yellow/50` | `#FEFDE6` | ~12:1 | 高亮、促销 Banner |
| 翡翠浅色 | `emerald/50` | `#ECF9F0` | ~12:1 | 成功、正向信息 Banner |
| 蓝色浅色 | `blue/50` | `#F0F3FA` | ~12:1 | 信息提示 Banner |
| 紫色浅色 | `purple/50` | `#F7F0FF` | ~12:1 | VIP、会员专属 Banner |
| 中性浅色 | `neutral/50` | `#FAFAFA` | ~13:1 | 通用、低调 Banner |
| 中性色 | `neutral/100` | `#F5F5F5` | ~12:1 | 次级 Banner |
| 纯白 | `background/primary` | `#FFFFFF` | ~13:1 | 需要与页面背景区分时慎用 |

#### 禁止使用的背景色

以下颜色与 `text/primary` 对比度不足，**禁止**用于 Banner 背景：

| 禁止背景色 | Token | Hex | 原因 |
|---|---|---|---|
| 中等红色 | `red/300` ~ `red/600` | `#F3867C` ~ `#C40009` | 对比度不足，文字难以辨认 |
| 中等琥珀色 | `amber/300` ~ `amber/600` | — | 对比度不足 |
| 深色背景 | `neutral/700` ~ `neutral/950` | — | 需改用 `text/primary-inverse` |
| 高饱和度颜色 | 任意 500+ 色阶 | — | 对比度不足或视觉刺激过强 |

#### 深色背景 Banner 例外

如需使用深色背景（如 `surface/inverse` `#222222`），文字必须改用 `text/primary-inverse`（`#FFFFFF`）：

| 深色背景 | Token | Hex | 文字色 |
|---|---|---|---|
| 深色表面 | `surface/inverse` | `#222222` | `text/primary-inverse` `#FFFFFF` |
| 品牌深色 | `brand/secondary` | `#222222` | `text/primary-inverse` `#FFFFFF` |

#### 对比度验证方法

设计时可使用以下工具验证对比度：
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Coolors Contrast Checker](https://coolors.co/contrast-checker)
- 浏览器开发者工具（Chrome DevTools 会自动显示对比度）

### 11.5.2 阴影与描边规则

**非浮层/弹窗组件不应添加额外的阴影和描边。**

| 组件类型 | 阴影 | 描边 |
|---|---|---|
| **浮层类**（Modal、Tooltip、Dropdown、Bottom Sheet） | ✅ 使用对应 elevation token | ✅ 可选 |
| **卡片类**（Product Card、Content Card） | ❌ 默认无阴影，hover 时可加 `elevation-200` | ✅ 使用 `border/default` |
| **Banner 类**（内嵌 Banner、通知条） | ❌ 不加阴影 | ❌ 不加描边，使用背景色区分 |
| **表单类**（Input、Select） | ❌ 不加阴影 | ✅ 使用 `border/default` |
| **按钮类**（Button） | ❌ 默认无阴影，hover 时可加轻微阴影 | 根据按钮类型决定 |

**原则：** Yami 采用 flat-first 设计语言，阴影仅用于表示层级关系（浮层高于页面），不用于装饰。

### 11.5.3 按钮颜色规则

**按钮颜色必须使用 Button 语义 Token，禁止随意使用其他颜色。**

| 按钮类型 | 背景色 Token | 文字色 | 使用场景 |
|---|---|---|---|
| **Emphasis** | `button/emphasis` `#E00000` | `#FFFFFF` | 最重要的操作，每屏最多 1 个 |
| **Primary** | `button/primary` `#000000` | `#FFFFFF` | 主要操作 |
| **Secondary** | `transparent` + `button/secondary` 描边 | `#000000` | 次要操作 |
| **Tertiary** | `button/tertiary` `#FFFFFF` | `#000000` | 弱操作 |
| **Disabled** | `button/disabled` `#EBEBEB` | `text/disabled` | 禁用状态 |

**禁止：**
- 使用 `neutral/900` 或其他中性色作为按钮背景（应使用 `button/primary`）
- 使用 `red/500` 作为按钮背景（应使用 `button/emphasis`）
- 自定义按钮颜色（如蓝色、绿色按钮）

**例外：** 特殊场景（如 App Store 下载按钮）可使用黑色 `button/primary`，但需在设计推导日志中说明理由。

---

## 12. Iconography

- **Style:** Outlined, 1.5–2px stroke, geometric — consistent with GT Walsheim character
- **Sizes:** 16px (inline) / 20px (buttons, nav) / 24px (cards) / 48–64px (feature, category)
- **Category icons:** Filled or duotone at 64–80px for visual impact
- **Image format:** WebP + JPEG fallback; lazy-load below fold

---

## 13. Motion & Interaction

- **Default transition:** `200ms ease` — color, background, shadow, transform
- **Accordion / Bottom Sheet:** `300ms ease` on max-height / transform
- **Scroll reveal:** Staggered fade-up on section enter, `400ms ease-out`, 100ms delay per element
- **Button hover:** `translateY(-2px)` + shadow transition
- **Reduced motion:** Respect `prefers-reduced-motion: reduce` — disable transforms, keep instant color transitions

---

## 14. Accessibility

- **Contrast:** All text WCAG AA (≥4.5:1 normal text, ≥3:1 large text). `#E00000` on white meets AA.
- **Focus indicator:** 2px solid `#3383FF` outline with 2px offset on all interactive elements
- **Keyboard:** All CTAs, accordions, modals operable via Tab / Enter / Space / Escape
- **Semantics:** Use `<nav>`, `<main>`, `<section>`, `<h1>`–`<h3>`, ARIA labels on icon-only buttons, `aria-expanded` on accordion triggers
- **Touch targets:** Minimum 44×44px on mobile

---

## 15. Multilingual Design

- **Text expansion:** CN is 30–50% shorter than EN — allow flexible container width for EN strings
- **Font loading:** GT Walsheim as primary web font. CJK fonts are system fonts (no extra download). Use Noto Sans as cross-platform fallback.
- **Language switcher:** Always in sticky nav, display in native script: English, 简体中文, 繁體中文, 日本語, 한국어
- **RTL:** Not currently required, keep layout logic direction-agnostic
