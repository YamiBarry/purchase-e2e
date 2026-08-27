---
inclusion: manual
---

# Component Context Matching Rules

> Design Agent 在接到需求时，必须先识别需求所影响的现有组件，找到代码库中的实际实现，然后基于现有组件结构输出带上下文的完整设计。

---

## 1. 核心原则

**Design Agent 不是凭空创造组件，而是在现有产品的组件体系中"增量设计"。**

每个需求都有一个"宿主组件"（Host Component）——即需求最终要嵌入或修改的那个现有组件。Design Agent 必须：

1. 识别宿主组件是什么
2. 在代码库中找到宿主组件的实际代码
3. 理解宿主组件的现有结构（HTML 层级、CSS 类名、数据字段）
4. 输出时包含宿主组件的上下文，而不是只输出新增的片段

---

## 2. 宿主组件识别流程（在需求校验通过后、设计推导前执行）

```
收到需求
   ↓
从 PRD 中提取关键词：
  - 页面名称（Checkout、Address Management、Cart、Order Detail...）
  - 组件名称（地址卡片、商品卡片、订单卡片、支付方式...）
  - 位置描述（"在 XX 下方"、"XX 内部"、"XX 旁边"）
   ↓
确定宿主组件：
  - 需求说"在地址卡片内展示" → 宿主 = 地址卡片组件
  - 需求说"在商品卡片上增加标签" → 宿主 = 商品卡片组件
  - 需求说"在结算按钮上方" → 宿主 = 结算页 CTA 区域
  - 需求说"新增一个弹窗" → 宿主 = 无（独立组件）
   ↓
在代码库中搜索宿主组件：
  - 使用 grepSearch / fileSearch 在 all-projects/ 下搜索
  - 优先搜索：组件名关键词、页面路由、CSS 类名
  - 找到后读取组件代码，提取结构信息
   ↓
记录宿主组件信息到设计推导日志
```

---

## 3. 代码库搜索策略

### 3.1 搜索优先级

```
1. PC 端 Web（Laravel + Vue）:
   all-projects/yamibuy-ec-website-trade-nb-*/resources/views/     → Checkout 相关
   all-projects/yamibuy-ec-website-customer-nb-*/resources/views/  → 用户中心相关
   all-projects/yamibuy-ec-website-customer-nb-*/resources/assets/ → JS/CSS

2. Mobile 端 Web（Nuxt SSR）:
   all-projects/yamibuy-ec-mobilesite-nb-*/components/pages/       → 页面组件
   all-projects/yamibuy-ec-mobilesite-ssr-*/pages/                 → 页面路由
   all-projects/yamibuy-ec-mobilesite-ssr-*/components/            → 通用组件

3. iOS（Swift）:
   all-projects/mobile_ios-master/Yamibuy/Domain/                  → 业务模块

4. Next.js（新站）:
   all-projects/yamibuy-ec-website-next-*/src/components/          → 通用组件
   all-projects/yamibuy-ec-website-next-*/src/features/            → 业务功能
```

### 3.2 搜索关键词映射

| PRD 中的描述 | 搜索关键词 |
|---|---|
| 地址卡片 / 地址管理 | `address`, `address__item`, `address-info`, `AddressCard` |
| 商品卡片 | `product-card`, `ProductCard`, `goods-item` |
| 购物车 | `cart`, `shopping-cart`, `CartItem` |
| 结算页 | `checkout`, `section-address`, `section-payment` |
| 订单详情 | `order-detail`, `OrderDetail` |
| RMA / 售后 | `rma`, `after-sale`, `refund` |
| 弹窗 / Modal | `modal`, `popup`, `dialog`, `bottom-sheet` |
| 导航 | `header`, `nav`, `navigation` |

---

## 4. 宿主组件结构提取

找到宿主组件代码后，提取以下信息：

```
宿主组件结构：
├── 组件文件路径：[path]
├── HTML 层级结构：
│   ├── 根元素：[class name / tag]
│   ├── 子元素列表：[按顺序列出]
│   └── 新增内容应插入的位置：[具体位置描述]
├── CSS 类名命名规范：[BEM / 其他]
├── 数据字段：[组件使用的数据结构]
└── 现有状态：[组件已有的状态变体]
```

---

## 5. 输出规则：带上下文的完整组件

### 5.1 当需求是"在现有组件内新增内容"时

**必须输出包含宿主组件上下文的完整状态，而不是只输出新增的片段。**

❌ 错误做法（只输出新增片段）：
```html
<!-- 只输出了提示条，没有上下文 -->
<div class="canada-guidance">
  <p>Shipping to Canada?...</p>
  <a>Shop Canada Site</a>
</div>
```

✅ 正确做法（输出带宿主组件上下文的完整状态）：
```html
<!-- 输出完整的地址卡片，包含新增的提示条 -->
<div class="address__item address__item--canada">
  <p class="address__item__name">John Doe</p>
  <p class="address__item__info">123 Maple Street, Toronto, ON M5V 2T6</p>
  <p class="address__item__info">+1 (416) 555-0123</p>
  
  <!-- ▼ 新增内容 START ▼ -->
  <div class="address__item__guidance">
    <p>Shipping to Canada? Please complete your order on our Canada site.</p>
    <a>Shop Canada Site →</a>
  </div>
  <!-- ▲ 新增内容 END ▲ -->
  
  <div class="address__item__tag">Default</div>
  <button class="address__item__edit">Edit</button>
</div>
```

### 5.2 CSS 类名规则

新增内容的 CSS 类名必须遵循宿主组件的命名规范：

```
宿主组件使用 BEM：.address__item__name
  → 新增内容：.address__item__guidance

宿主组件使用 kebab-case：.address-info__main
  → 新增内容：.address-info__guidance

宿主组件使用 camelCase：.addressCard
  → 新增内容：.addressCardGuidance
```

### 5.3 输出状态对比

必须同时输出：
1. **对照状态**：宿主组件的原始状态（无新增内容），用于对比
2. **新增状态**：宿主组件 + 新增内容的完整状态
3. **边界状态**：新增内容不展示时的宿主组件状态（如条件不满足）

---

## 6. 设计推导日志补充格式

在设计推导日志中新增「宿主组件」区块：

```
── 宿主组件 ──
宿主识别：[组件名称]
代码位置：
  - PC: [文件路径]
  - Mobile: [文件路径]
HTML 结构：
  [简化的层级结构]
CSS 命名规范：[BEM / kebab-case / 其他]
新增内容插入位置：[具体描述，如"地址详情之后、操作按钮之前"]
类名决策：[新增内容使用的 CSS 类名及命名依据]
```

---

## 7. 特殊情况处理

### 7.1 宿主组件在代码库中找不到

```
搜索失败时：
1. 扩大搜索范围（尝试不同关键词）
2. 如果确实找不到，在日志中标注"宿主组件未在代码库中找到"
3. 退化为 Level 3 自创模式，但仍需输出带模拟上下文的完整组件
4. 模拟上下文基于 PRD 中描述的页面结构
```

### 7.2 需求是独立新组件（无宿主）

```
以下情况无需搜索宿主组件：
- 需求明确是"新页面"
- 需求是独立弹窗（Modal / Bottom Sheet）
- 需求是全局组件（Toast / Notification）
- 需求与任何现有组件无嵌套关系
```

### 7.3 宿主组件跨多个平台

```
当 PC 和 Mobile 的宿主组件结构不同时：
- 分别搜索两个平台的组件代码
- 输出时分平台标记：
  <!-- ▼▼▼ COMPONENT: [名称] / PC — COPY FROM HERE ▼▼▼ -->
  <!-- ▼▼▼ COMPONENT: [名称] / Mobile — COPY FROM HERE ▼▼▼ -->
- 每个平台的输出都包含各自宿主组件的上下文
```

---

## 8. 执行时机

此流程在以下时间点执行：

```
需求校验通过（Step 1 完成）
   ↓
【Step 1.5 — 组件匹配决策】
   ├── 场景识别
   ├── 宿主组件识别 ← 本文件定义的流程
   ├── 代码库搜索
   ├── 结构提取
   └── 匹配级别判定
   ↓
设计推导（Step 2）
```
