---
inclusion: always
---

# Purchase PM Agent — 业务领域知识

## 系统现状（Purchase Team 负责的模块）

| 模块 | 功能范围 |
|------|---------|
| 购物车（Cart） | 商品列表、稍后购买、失效列表、底部更多推荐、我的收藏 |
| 结算页（Checkout） | 新增地址、编辑地址、地址联想、配送方式选择、预计送达时间、支付方式选择、订单确认 |
| 支付（Payment） | Apple Pay、PayPal、信用卡、Venmo、Cash Pay、支付宝、微信支付、Google Pay |
| 订单（Order） | 订单详情/列表、物流追踪 |
| 个人中心（Profile） | 我的订单、礼品卡、优惠券/积分、我的收藏、邀请好友、商品评价、常买、底部更多推荐 |
| 会员系统（Membership） | 三级会员体系 |
| 售后（After-sales） | 目前仅支持退款（退货/换货尚未建设用户端功能，只能客服从内部后台发起） |
| 登录注册 | 邮箱注册、邮箱登录、Google联合登录、AppleID联合登录、Facebook联合登录、微信联合登录、账号管理 |

## 会员等级

| 等级 | 条件 | 说明 |
|------|------|------|
| Ruby | 免费注册即得 | 基础会员 |
| Silver | 180天内消费 $150 | 中级会员 |
| Gold | 180天内消费 $350 | 高级会员 |

## 用户分群字典

| 分群名称 | 定义 |
|---------|------|
| New Customer | 已注册已下单（首单用户） |
| Return Customer | 下过不止一单的老客户 |
| Non Customer | 未下过单的用户（含已注册未下单 + 访客 Visitor） |
| Visitor | 未注册的访客 |
| Non Chinese Site | 除简体中文站以外的所有语言平台 |
| Chinese Site | 简体中文站 |
| English Site | 英文站 |

## 页面流量数据（日均 UV）

### 分端汇总

| 页面 | iOS | Android | H5(mWeb) | PC(估算) | 全端合计 |
|------|-----|---------|----------|---------|---------|
| Cart | 215K | 20K | 53K | ~70K | 358K |
| Checkout | 129K | 10K | 19K | ~43K | 201K |
| Pay Success | 116K | 8K | 14K | ~39K | 177K |
| User Center | 169K | 17K | 16K | 12K | 214K |
| Order List | 95K | 7K | 6K | ~32K | 140K |
| Order Detail | 120K | 9K | 8K | ~40K | 177K |

> iOS 占全端流量 70%+，是绝对主力端。Android 约为 iOS 的 1/10。H5 流量主要来自英文站和中文站。PC 端埋点覆盖不完整，仅 User Center 有准确数据（12K），其他页面按 iOS 的 1/3 估算（如 Cart 约 70K、Checkout 约 43K、Order Detail 约 40K）。

### 分语言/站点（iOS 端，占比最大）

| 站点 | Cart UV | Checkout UV | Pay Success UV | 占比 |
|------|---------|-------------|----------------|------|
| 中文站(zh) | 170K | 109K | 99K | 79% |
| 英文站(en) | 38K | 17K | 14K | 13% |
| 繁体站(zht) | 5K | 3K | 2K | 4% |
| 韩文站(ko) | 1.1K | 0.4K | 0.4K | <1% |
| 日文站(ja) | 0.3K | 0.1K | 0.1K | <1% |

> 中文站占绝对主体。英文站是第二大站，但流量只有中文站的 1/5。非中文站 AB 实验需要更长周期积累样本。

### 核心转化漏斗

| 漏斗环节 | 全端转化率 | 计算方式 | 说明 |
|---------|-----------|---------|------|
| Cart → Checkout Click | ~55% | checkout_click_uv / cart_uv | 超过一半用户会点击去结算 |
| Checkout → Place Order | ~70% | place_order_uv / checkout_uv | 进入结算页后大部分会下单 |
| Cart → Place Order（端到端） | ~38% | place_order_uv / cart_uv | 整体购物车到下单转化 |

### 推荐模块数据（日均）

| 页面 | 推荐曝光 UV | 推荐加购 UV | 推荐加购率 |
|------|-----------|-----------|-----------|
| Cart | 64K | 11K | 17.2% |
| User Center | 19K | 1.3K | 6.8% |
| Order Detail | 11K | 0.9K | 8.2% |
| Pay Success | 4K | 1.3K | 32.5% |

> Cart 推荐模块流量最大但加购率中等；Pay Success 推荐加购率最高（用户刚完成支付，购买意愿强）。

### 数据使用指南

- 业务方说"先做 App" → iOS 为主，Android 流量只有 iOS 的 1/10
- 业务方说"英文站" → 流量基数约 38K（Cart），AB 实验建议 14-21 天
- 业务方说"全端" → iOS 占 70%+，优先保证 iOS 体验
- 推荐模块需求 → Pay Success 加购率最高，Cart 流量最大
- PC 端需求 → 埋点数据不完整，按 iOS 的 1/3 估算流量；User Center 有准确数据 12K

## 系统约束（已知，不需要问业务方）

- **AB 实验分流**：只支持 DID（设备 ID）分流，不支持 UID 分流
- **多语言**：支持 zh-CN、zh-TW、en-US、ja-JP、ko-KR 五种语言
- **结算页**：需登录，无 guest checkout
- **营销 Email**：trigger/blast 类归 Customer Success 团队；Purchase 只负责订单/物流通知类 Email
- **售后**：目前仅支持退款，退货/换货尚未建设用户端功能，只能客服从内部后台发起

## 常用转化指标

| 指标 | 计算方式 | 适用场景 |
|------|---------|---------|
| Checkout Rate | Checkout UV / Cart UV | 购物车到结算的转化 |
| Place Order Rate | Place Order UV / Checkout UV | 结算到下单的转化 |
| cash_pay_usage_rate | Cash Pay 支付次数 / 总支付次数 | Cash Pay 渗透率 |
| rec_addcart_rate | 推荐加购次数 / 推荐曝光次数 | 推荐模块效果 |
| new_user_checkout_completion_rate | 新用户下单 UV / 新用户 Checkout UV | 新用户转化 |

指标字典里没有的，根据需求方向灵活生成，不受字典限制。

## 常见需求类型与指标对应

| 需求类型 | 推荐 Primary Metric |
|---------|-------------------|
| 支付方式相关 | 该支付方式使用率 |
| 转化优化 | checkout_completion_rate 或 place_order_rate |
| 营销露出 | 点击率(ctr) 或带来的转化 GMV |
| 推荐模块 | 推荐加购率(rec_addcart_rate) |
| 优惠券 | 优惠券使用率 + 带来的 GMV |
| 会员权益 | 会员升级率 或 会员留存率 |
| 首单激励 | new_user_checkout_completion_rate |
