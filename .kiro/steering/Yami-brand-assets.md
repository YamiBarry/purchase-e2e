---
inclusion: manual
---

# YAMI Brand Assets

> 放入 `.kiro/steering/` 目录。Agent 生成任何包含 Logo 或 Icon 的 UI 时，必须引用此文件。

---

## 1. YAMI Logo SVG

### 1.1 Logo Icon（红圈 + Y 标志）
用途：Favicon、App Icon、小尺寸场景、Chat Widget 角标

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Red circle background -->
  <circle cx="32" cy="32" r="32" fill="#FF0000"/>
  <!-- Y mark (white) -->
  <path fill-rule="evenodd" clip-rule="evenodd"
    d="M40.23 39.65C41.81 38.08 44.36 38.08 45.93 39.65L46.09 39.81C47.51 41.39 47.46 43.83 45.93 45.35C44.36 46.92 41.81 46.92 40.23 45.35C38.66 43.78 38.66 41.22 40.23 39.65ZM42.10 16.36L47.14 21.38L42.10 26.41L37.05 31.44L32.00 36.47L26.95 41.50L21.90 46.52L16.86 41.50L26.95 31.44L21.90 26.41L16.86 21.38L21.90 16.36L26.95 21.38L32.00 26.41L37.05 21.38L42.10 16.36Z"
    fill="white"/>
</svg>
```

### 1.2 Logo Horizontal（图标 + YAMI 文字）
用途：导航栏、页头、页脚、登录页

```svg
<svg width="120" height="32" viewBox="0 0 120 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Icon -->
  <circle cx="16" cy="16" r="16" fill="#FF0000"/>
  <path fill-rule="evenodd" clip-rule="evenodd"
    d="M20.12 19.82C20.91 19.04 22.18 19.04 22.97 19.82L23.05 19.91C23.78 20.69 23.75 21.91 22.97 22.68C22.18 23.46 20.91 23.46 20.12 22.68C19.33 21.89 19.33 20.61 20.12 19.82ZM21.05 8.18L23.57 10.69L21.05 13.21L18.52 15.72L16.00 18.24L13.48 20.75L10.95 23.26L8.43 20.75L13.48 15.72L10.95 13.21L8.43 10.69L10.95 8.18L13.48 10.69L16.00 13.21L18.52 10.69L21.05 8.18Z"
    fill="white"/>
  <!-- YAMI wordmark -->
  <path fill-rule="evenodd" clip-rule="evenodd"
    d="M41.39 7.39H38.11L39.74 3.94L36.5 -1.43H39.97L41.92 2.25L43.60 -1.43H47.08L41.39 7.39Z
       M52.56 7.39L52.21 6.23H48.95L48.60 7.39H46.34L49.61 -1.43H51.56L54.89 7.39H52.56Z
       M50.58 1.28L49.44 5.00H51.70L50.58 1.28Z
       M65.51 7.39H63.44V1.71L61.47 7.39H59.90L57.86 1.71V7.39H55.79V-1.43H58.24L60.69 5.00L63.14 -1.43H65.51V7.39Z
       M67.52 7.39V-1.43H69.67V7.39H67.52Z"
    fill="#222222" transform="translate(38, 12) scale(0.7)"/>
</svg>
```

### 1.3 Logo Inverse（白色，用于深色背景）
用途：深色 Banner、深色 Footer、`surface/inverse` (#222222) 背景上

```svg
<!-- 与 1.2 相同结构，wordmark 颜色改为 #FFFFFF -->
<svg width="120" height="32" viewBox="0 0 120 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="16" cy="16" r="16" fill="#FF0000"/>
  <path fill-rule="evenodd" clip-rule="evenodd"
    d="M20.12 19.82C20.91 19.04 22.18 19.04 22.97 19.82L23.05 19.91C23.78 20.69 23.75 21.91 22.97 22.68C22.18 23.46 20.91 23.46 20.12 22.68C19.33 21.89 19.33 20.61 20.12 19.82ZM21.05 8.18L23.57 10.69L21.05 13.21L18.52 15.72L16.00 18.24L13.48 20.75L10.95 23.26L8.43 20.75L13.48 15.72L10.95 13.21L8.43 10.69L10.95 8.18L13.48 10.69L16.00 13.21L18.52 10.69L21.05 8.18Z"
    fill="white"/>
  <!-- Wordmark white version -->
  <text x="38" y="21" font-family="-apple-system, BlinkMacSystemFont, sans-serif"
    font-size="14" font-weight="600" fill="#FFFFFF" letter-spacing="0.5">YAMI</text>
</svg>
```

---

## 2. Logo 使用规则

| 规则 | 说明 |
|------|------|
| **最小尺寸** | Icon: 24px / Horizontal: 80px 宽 |
| **安全间距** | Logo 四周留白 ≥ Icon 直径的 50% |
| **背景** | 白色背景用标准版；深色背景用 Inverse 版 |
| **禁止** | 拉伸变形、修改颜色、添加投影、放在繁杂背景上 |
| **红圈颜色** | 永远使用 `#FF0000`（品牌红），不得改为 UI Red `#E00000` |

---

## 3. Icon Library 规范

### 3.1 品牌 / 社交 Icon → Simple Icons

**CDN:** `https://cdn.simpleicons.org/{slug}/{hex-color}`

生成 HTML 时，品牌 icon 统一用此 CDN，不要手写 SVG path。

| 平台 | Slug | 推荐颜色 |
|------|------|---------|
| Google Play | `googleplay` | `#414141` |
| App Store | `appstore` | `#000000` |
| Pinterest | `pinterest` | `#E60023` |
| Instagram | `instagram` | `#E4405F` |
| Facebook | `facebook` | `#1877F2` |
| Twitter / X | `x` | `#000000` |
| WeChat | `wechat` | `#07C160` |
| Line | `line` | `#00C300` |
| YouTube | `youtube` | `#FF0000` |
| TikTok | `tiktok` | `#000000` |
| WhatsApp | `whatsapp` | `#25D366` |
| Visa | `visa` | `#1A1F71` |
| Mastercard | `mastercard` | `#EB001B` |
| PayPal | `paypal` | `#00457C` |
| Alipay | `alipay` | `#1677FF` |
| WeChat Pay | `wechatpay` | `#07C160` |

**用法示例：**
```html
<!-- Google Play icon, 24px, 默认色 -->
<img src="https://cdn.simpleicons.org/googleplay/414141" width="24" height="24" alt="Google Play" />

<!-- Pinterest icon, 自定义尺寸 -->
<img src="https://cdn.simpleicons.org/pinterest/E60023" width="20" height="20" alt="Pinterest" />
```

### 3.2 UI 操作 Icon → Lucide Icons

用于界面功能性图标（关闭、搜索、购物车、箭头等）。

**CDN:** `https://unpkg.com/lucide-static@latest/icons/{name}.svg`

| 场景 | Icon Name | 用法 |
|------|-----------|------|
| 关闭 | `x` | Modal、Tag 删除 |
| 搜索 | `search` | Search bar |
| 购物车 | `shopping-cart` | Nav Cart |
| 用户 | `user` | Account |
| 心形 | `heart` | Wishlist |
| 分享 | `share-2` | Share |
| 箭头右 | `chevron-right` | List item |
| 箭头左 | `chevron-left` | Back |
| 筛选 | `sliders-horizontal` | Filter |
| 星星 | `star` | Rating |
| 定位 | `map-pin` | Zipcode |
| 语言 | `globe` | Language switch |
| 菜单 | `menu` | Hamburger |
| 加号 | `plus` | Add |
| 减号 | `minus` | Decrease qty |
| 勾选 | `check` | Confirm / Done |
| 警告 | `alert-circle` | Error / Warning |
| 信息 | `info` | Info tooltip |

**用法示例：**
```html
<!-- 内联 SVG 方式（推荐，可控制颜色） -->
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
  stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <!-- Lucide search path -->
  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
</svg>
```

### 3.3 Icon 尺寸规范

| 场景 | 尺寸 |
|------|------|
| 文字行内 icon | 16px |
| 按钮、导航 icon | 20px |
| 卡片功能 icon | 24px |
| 空状态、分类展示 | 48–64px |

### 3.4 Icon 颜色规范

| 场景 | 颜色 Token | Hex |
|------|-----------|-----|
| 默认 / 功能 | `text/primary` | `rgba(0,0,0,0.87)` |
| 次要 / 辅助 | `text/secondary` | `rgba(0,0,0,0.55)` |
| 禁用 | `text/disabled` | `rgba(0,0,0,0.29)` |
| 品牌强调 | `text/emphasis` | `#E00000` |
| 成功 | `text/success` | `#27812B` |
| 深色背景 | `text/primary-inverse` | `#FFFFFF` |

---

## 4. Agent 使用规则

生成任何 HTML / 组件时，遵守以下规则：

```
1. 需要 YAMI Logo？
   → 直接复制上方 SVG 代码，不要用文字替代，不要用占位符

2. 需要品牌 icon（Google Play、Pinterest 等）？
   → 使用 Simple Icons CDN，slug 查上方表格

3. 需要 UI icon（关闭、搜索、箭头等）？
   → 使用 Lucide 内联 SVG，不要用 emoji 或文字符号

4. 不确定用哪个 icon？
   → 优先查上方表格，找不到再用 Lucide icon search
```
