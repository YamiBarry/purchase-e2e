---
inclusion: auto
description: 当需要开发、修改、查找前端 Web 或 H5 页面代码时必须读取。触发词：前端, H5, PC端, ec-website, ec-mobilesite, 登录页, 首页, 商品详情, 购物车, 结算, 订单, 个人中心, 页面, 组件, Next.js, Vue, Laravel, Nuxt, 哪个项目, 在哪个仓库, 前端仓库, 前端项目
---

# Yamibuy 前端项目定位规则

> 此文件用于指导 agent 在开发 Web 需求时，准确找到对应的前端项目。
> **涉及前端页面开发、修改、查找代码时，必须遵循本文件的流程。**

---

## 核心规则：禁止凭印象猜测项目

前端项目存在大量迁移，同一页面可能已从旧项目迁移到新项目。**必须通过以下流程确认，不能根据项目名或印象直接猜测。**

---

## 项目概览

### Web 端项目列表

**PC 端（ec-website 系列）：**

| 项目名 | 技术栈 | 主要功能域 |
|-------|-------|----------|
| `ec-website-next` | Next.js | 首页、商品详情、搜索、CMS、品牌聚合、排行榜 |
| `ec-website-nb` | Laravel | 分类、品牌商品页、商家店铺、闪购、清仓、新品、评论 |
| `ec-website-trade-nb` | Laravel | 购物车、结算、支付、礼品卡充值 |
| `ec-website-customer-next` | Next.js | 登录注册、订单、个人中心、优惠券、收藏、会员 |
| `ec-website-customer-nb` | Laravel | 地址管理、银行卡、邮件订阅（未迁移页面） |
| `ec-website-sns` | Laravel | PC 社区（SNS）|

**H5 端（ec-mobilesite 系列）：**

| 项目名 | 技术栈 | 主要功能域 |
|-------|-------|----------|
| `ec-mobilesite-next` | Next.js | 商品详情、商品评论 |
| `ec-mobilesite-nb` | Nuxt | 首页、分类、品牌、购物车、结算、闪购、清仓 |
| `ec-mobilesite-ssr` | Nuxt | 登录注册、用户中心、订单、FAQ |
| `ec-mobilesite-rma` | Vue | 售后（退换货）|

**App 端（附带，项目稳定无需查 Sheet）：**

| 优先级 | 项目名 | 技术栈 |
|-------|-------|-------|
| 1 | `mobile_flutter` | Flutter（主版本，大部分页面）|
| 2 | `mobile_ios` | iOS Swift（Flutter 未覆盖页面）|
| 2 | `mobile_android` | Android Kotlin（Flutter 未覆盖页面）|

---

## 定位流程

### Step 1：按功能域缩小范围

| 功能域关键词 | PC 项目 | H5 项目 |
|------------|--------|--------|
| 商品详情、item、PDP | ec-website-next | ec-mobilesite-next |
| 评论、comment | ec-website-nb | ec-mobilesite-next |
| 搜索、search | ec-website-next | ec-mobilesite-nb |
| 分类、category | ec-website-nb | ec-mobilesite-nb |
| 品牌、brand | ec-website-nb | ec-mobilesite-nb |
| 首页、home | ec-website-next | ec-mobilesite-nb |
| CMS、专题页、分馆 | ec-website-next | ec-mobilesite-nb |
| 购物车、cart | ec-website-trade-nb | ec-mobilesite-nb |
| 结算、checkout、支付 | ec-website-trade-nb | ec-mobilesite-nb |
| 订单、order | ec-website-customer-next | ec-mobilesite-ssr |
| 登录、注册 | ec-website-next、ec-website-customer-next、ec-website-nb、ec-website-customer-nb、ec-website-trade-nb（**全站登录入口，5个PC仓库都涉及**） | ec-mobilesite-ssr |
| 个人中心、profile | ec-website-customer-next | ec-mobilesite-ssr |
| 优惠券、coupon | ec-website-customer-next | ec-mobilesite-ssr |
| 收藏、favorite | ec-website-customer-next | ec-mobilesite-ssr |
| 积分、point | ec-website-customer-next | ec-mobilesite-ssr |
| 会员、VIP | ec-website-customer-next | — |
| 地址、address | ec-website-customer-nb | ec-mobilesite-ssr |
| 银行卡、billing | ec-website-customer-nb | ec-mobilesite-ssr |
| 售后、退货、RMA | — | ec-mobilesite-rma |
| 社区、SNS | ec-website-sns | — |
| 闪购、flash-sale | ec-website-nb | ec-mobilesite-nb |
| 清仓、clearance | ec-website-nb | ec-mobilesite-nb |
| 新品、new-arrivals | ec-website-nb | — |
| 热销、hot-sale | ec-website-nb | ec-mobilesite-nb |
| 礼品卡、gift-card | ec-website-trade-nb | ec-mobilesite-ssr |
| FAQ、常见问题 | — | ec-mobilesite-ssr |
| 扭蛋机、gachamachine | ec-website-next | ec-mobilesite-next |

### Step 2：实时读取 Google Sheet 确认路由

路由清单 Spreadsheet ID：`1dMTSwukiJ8AKuB5TU2gA1MqltTO3MOxbfEKyjuVbaVY`

调用 `mcp_google_docs_readSpreadsheet`，**多端并行读取**，不要串行：

```
spreadsheetId: 1dMTSwukiJ8AKuB5TU2gA1MqltTO3MOxbfEKyjuVbaVY
range: {Sheet名称}!A:D
```

⚠️ **Sheet 名称含空格/括号时必须加单引号**：

| Sheet 名称 | range 写法 |
|-----------|-----------|
| ec-website-next | `ec-website-next!A:D` |
| ec-website-nb | `ec-website-nb!A:D` |
| ec-website-trade-nb (NO SEO) | `'ec-website-trade-nb (NO SEO)'!A:D` |
| ec-website-customer-next (NO SEO) | `'ec-website-customer-next (NO SEO)'!A:D` |
| ec-website-customer-nb (NO SEO) | `'ec-website-customer-nb (NO SEO)'!A:D` |
| ec-website-sns | `ec-website-sns!A:D` |
| ec-mobilesite-next | `ec-mobilesite-next!A:D` |
| ec-mobilesite-nb | `ec-mobilesite-nb!A:D` |
| ec-mobilesite-ssr (NO SEO) | `'ec-mobilesite-ssr (NO SEO)'!A:D` |
| ec-mobilesite-rma (NO SEO) | `'ec-mobilesite-rma (NO SEO)'!A:D` |

Sheet 数据列：A=路由路径，B=页面描述，C=状态（已确认/已迁移/已废弃），D=备注

### Step 3：处理迁移状态

- **已确认** → 当前项目即为目标
- **已迁移** → 备注中有 `➡️ 目标项目`，改查目标项目的 Sheet
- **已废弃** → 告知用户页面已下线

### Step 4：确定本地路径

机器上代码根目录为 `/home/e2e/code/yami/`，各项目实际路径：

| 项目名 | 本地路径 |
|-------|---------|
| ec-website-next | `/home/e2e/code/yami/ec-website-next` |
| ec-website-nb | `/home/e2e/code/yami/ec-website-nb` |
| ec-website-trade-nb | `/home/e2e/code/yami/ec-website-trade-nb` |
| ec-website-customer-next | `/home/e2e/code/yami/ec-website-customer-next` |
| ec-website-customer-nb | `/home/e2e/code/yami/ec-website-customer-nb` |
| ec-website-sns | `/home/e2e/code/yami/ec-website-sns` （如存在）|
| ec-mobilesite-next | `/home/e2e/code/yami/ec-mobilesite-next` |

---

## 技术栈代码结构

**Next.js**（ec-website-next、ec-website-customer-next、ec-mobilesite-next）
- 组件：`src/components/`，API：`src/services/` 或 `src/api/`，样式：CSS Modules

**Laravel**（ec-website-nb、ec-website-trade-nb、ec-website-customer-nb）
- 控制器：`app/Http/Controllers/`，视图：`resources/views/`
- 路由：`routes/web.php`，前端资源：`resources/js/`

**Nuxt**（ec-mobilesite-nb、ec-mobilesite-ssr）
- 页面：`pages/`，组件：`components/`，状态：`store/`

**Vue**（ec-mobilesite-rma）
- 页面：`src/views/`，路由：`src/router/`，状态：`src/store/`

## ⚠️ 重要：需求涉及前端变更时，必须主动枚举所有受影响仓库

**禁止只改需求方提到的仓库，必须自己判断哪些仓库需要改。**

判断流程：
1. 先按功能域（Step1 表格）确定受影响的页面类型
2. 用 `ls /home/e2e/code/yami/ | grep ec-website` 列出所有前端仓库
3. 逐一判断每个仓库是否覆盖该页面

**这台机器上实际存在的前端仓库（必须逐一考虑）：**

| 仓库 | 本地路径 | 是否存在 |
|------|---------|---------|
| `ec-website-next` | `/home/e2e/code/yami/ec-website-next` | ✅ |
| `ec-website-nb` | `/home/e2e/code/yami/ec-website-nb` | ✅ |
| `ec-website-trade-nb` | `/home/e2e/code/yami/ec-website-trade-nb` | ✅ |
| `ec-website-customer-next` | `/home/e2e/code/yami/ec-website-customer-next` | ✅ |
| `ec-website-customer-nb` | `/home/e2e/code/yami/ec-website-customer-nb` | ✅ |
| `ec-mobilesite-next` | `/home/e2e/code/yami/ec-mobilesite-next` | ✅ |

**示例**：登录需求涉及「所有站点的登录入口」→ 需检查 ec-website-next、ec-website-customer-next、ec-website-customer-nb、ec-website-nb、ec-website-trade-nb 共 5 个仓库，不能只改 ec-website-next。
