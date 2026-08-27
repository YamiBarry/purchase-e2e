---
inclusion: always
---

# Purchase PM Agent — 需求路由规则

## 路由判断

收到业务方需求后，第一步判断路由路径：

| 路由 | 触发条件 | 处理方式 |
|------|---------|---------|
| Route A | 营销类、转化提升类、信息展示类、活动配置类、支付体验类、购物车体验类、订单/售后体验类、登录注册类、系统能力类 | 完整分析流（见 pm-agent-analysis.md） |
| Route B | Bug/异常类 | 轻量确认后生成 Bug Report，直接分发给 Coding Agent |
| Route C | 埋点/数据类 | 确认后生成 Tracking Spec |
| Route D | 非 Purchase Team 职责 | 告知正确团队，不做分析 |

## 关键判断：异常 ≠ Bug

"异常"这个词需要结合上下文判断：

- **走 Route B（Bug）**：异常 + 系统故障词（不能用、访问不了、用不了、失败了、一直报错、一直崩）
  - 例：「结算页一直报错，用不了」→ Route B
  - 例：「支付失败了，用户反馈无法下单」→ Route B

- **走 Route A（正常需求）**：异常 = 业务场景描述
  - 例：「物流异常提示展示优化」→ Route A
  - 例：「订单异常状态的处理流程」→ Route A
  - 例：「异常订单的退款逻辑」→ Route A

## Purchase Team 职责范围

**负责的模块**：购物车（Cart）、结算页（Checkout）、支付（Payment）、订单（Order）、个人中心（Profile/Account）、会员系统（Membership）、用户系统（User System）、登录注册（Login/Registration）、售后系统（After-sales/RMA）、二维码系统（QR Code）、消息中心（Message Center）

**不负责的模块**（Route D 转交）：
- 主站首页、分馆页、分类页、活动页、商品详情页、及这些页面内榜单、Best seller、优惠券等功能组件、CMS等营销活动配置后台→ Pre-Purchase Team
- 搜索算法、推荐算法、数据中心、数据集群、数据清洗 → Bigdata Team
- 营销类 Email、App Push（trigger/blast）→ Customer Success Team（Purchase 只负责订单/物流通知类 Email）
- 供应链、仓储、物流、履约、进出货系统 → Operations Team
- 财务对账、发票 → Finance Team
- 第三方商家平台、商家系统、商家商品上下架、进出货 → SSS Team
- 自营商品系统、商品属性、商品维护 → Category Team

## Route D 转交格式

```
该需求可能属于 [团队名称] 团队的职责范围，建议联系对应负责人。
原因：[简短说明为什么不属于 Purchase]
```
