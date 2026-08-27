---
inclusion: manual
---

# Component: Product Card
> Load only when the task requires displaying product listings or grids.
> Depends on: design-core.md (price-md, strike-md, border/default, radius/lg, elevation-200-raised-surface, badge tokens)

---

## Types — Always Use Latest Versions

| Type | Platform | Version | Description |
|---|---|---|---|
| `Mobile Vertical` | Mobile | V7 ✅ | Vertical card — latest |
| `PC Vertical` | PC | V6 ✅ | Vertical card, multi-layout |
| `Horizontal` | Both | V6 ✅ | Horizontal card |
| `Mobile Mini` | Mobile | V5 ✅ | Compact card |
| `Product List / Grid` | Mobile | — | Grid layout wrapper |

Never use deprecated versions.

---

## PC Card Variants

- **Info:** Default / Mini Info / Price + Add to Cart / Only Price / Only Image / Mini Info Vertical
- **Style:** Card / List-1 / List-2
- **Page context:** Homepage / List page / Default

---

## Add to Cart Button States

| State | Description |
|---|---|
| `Add to cart` | Default, purchasable |
| `Sold Out` | Out of stock |
| `Get Restock Alerts` | Notify when back in stock |
| `Add to cart - Edit` | Editing quantity |
| `Add to cart - Done` | Successfully added |

---

## Styling Rules

- Sale price: `price-md` (20px, 500) or `price-sm` (16px, 500)
- Original price: `strike-md` or `strike-sm` (strikethrough)
- Badge overlay: supported on product image area — use badge tokens from design-core.md
- Card shadow: none at rest; `elevation-200-raised-surface` on hover
- Card border: 1px `border/default`
- Card radius: `radius/lg` (12px)
- Never use deprecated card versions (Mobile V6 and below, PC V5 and below)
