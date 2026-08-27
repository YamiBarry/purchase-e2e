---
inclusion: manual
---

# Purchase PM Agent — 交付物规范

业务方确认需求后，生成以下交付物。C7+ 复杂度只生成 Analysis Brief + SRD，不生成完整交付物。

## 交付物生成前置步骤（必须执行）

生成 PRD 和 UIH 之前，必须先回溯本次 session 的完整对话历史，逐轮提取业务方确认过的所有细节，形成"已确认事实清单"。提取维度包括但不限于：

- 目标用户 / 用户筛选条件
- 展示页面 / 具体位置
- 触发条件 / 展示时机
- 频控规则（展示窗口、关闭行为、过期逻辑）
- 交互行为（点击跳转、关闭、展开/收起）
- 文案内容 / 文案风格要求
- 平台范围 / 国家范围 / 语言范围
- 优惠逻辑（金额、门槛、叠加规则、自动/手动）
- AB 实验要求（分流方式、周期、指标）
- 业务方明确否决的方案或细节
- 业务方未回答的问题（标注"业务方未明确，暂不纳入"）

**规则：对话中业务方确认过的任何细节，都必须体现在 PRD 对应章节中，不允许压缩或遗漏。PRD 是开发和 QA 的唯一基础材料，丢失细节会导致交付问题。**

**额外产出：conversation 文件**

生成交付物的同时，必须将本次 session 的完整对话记录保存为 `conversation-{id}.md`，放在同一个 deliverables 目录下。格式：

```markdown
# 对话记录

## 第 1 轮
**[业务方]** {消息内容}
**[PM Agent]** {回复内容}

## 第 2 轮
...
```

此文件供 PM Review Agent 作为 ground truth 使用，用于对照检查 PRD 是否完整覆盖了对话中确认的所有细节。

## Review 回调修正规则

当 PM Agent 被编排平台回调修正时（Review Agent 返回 FAIL）：

1. 读取 deliverables/{id}/ 目录下最新的 review 文件，提取所有 issues
2. 逐条修正 PRD 和 UIH（原地更新，不起新编号）
3. 修正完成后，节点完成，等待编排平台再次调 Review Agent 验证

**注意：Review 修正不起新文件夹编号。** 同一个需求的 review 循环始终在同一个目录下操作。

## 终版确认后的交付物生成

当 Review Agent 返回 PASS（`Status: CONFIRMED`）后，PM Agent 被编排平台调用执行最终推送：

1. 基于终版 PRD 重新生成其他交付物（SRD、Copy Package、Tracking Spec、QA Criteria、AB Brief、Task Package）
2. 推送所有交付物到 Google Doc
3. 创建 OP 工单

**其他交付物在 review PASS 后才生成**，确保它们基于终版 PRD 内容，不会出现 PRD 改了但其他交付物没同步的问题。

---

## PRD（给开发/测试/UI Agent）

章节结构（必须完整，不能缺章节）：

1. **文档信息**：需求ID、名称、需求类型（11种之一）、开放程度（L1-L4）、复杂度（C几 + 预估周期 + 工作项概述）、Owner（Purchase PM Agent）、状态（Draft）、版本（v1.0）、日期
2. **Problem Framing**：按 Full Template 格式输出 Customer、Problem、Job（Job Story 格式）、Company Benefit、Success Metrics、Solution 概述、Feedback Loops
3. **User Story**：基于 Problem Framing 推导，格式"作为[用户]，当我[场景]，我希望[功能]，从而[价值]"
4. **目标**：用户目标、业务目标、Primary Metric、Secondary Metrics、Guardrail Metrics
4. **需求范围**：In Scope、Out of Scope、国家、平台、语言、用户范围
5. **功能方案**：推荐方案详述、展示规则、交互规则、频控规则、用户分群规则、异常状态处理
6. **交付形式**：新页面（含路由路径）或现有页面新增（说明嵌入位置）
7. **页面体验说明**：已有元素盘点、冲突检查结果、采用当前方案的原因
8. **多语言文案**：引用 Copy Package，列出各语言文案
9. **埋点需求**：曝光事件、点击事件、转化事件，每个事件含触发条件、参数列表
10. **AB 实验**（如需要）：实验假设（If/Then/Because）、分组说明（V0对照/V1实验）、Primary/Secondary/Guardrail Metrics、Trigger 分流时机、建议周期
11. **风险**：业务风险、UI风险、技术风险、数据风险、合规风险
12. **验收标准**：功能验收、UI验收、多语言验收、国家/站点验收、用户分群验收、埋点验收、AB分组验收、异常状态验收
13. **上线策略**：灰度方案、回滚方案、上线后监控指标

---

## UIH（给 UI Agent，按 Yami Design Agent 规范 v2.0）

格式：Markdown 文档，包含以下必填 6 项 + 选填项 + 设计参考建议。

### 必填 6 项（只描述业务目标，不做设计决策）

1. **Problem Framing**：Customer（谁）+ Problem（什么问题）+ Job（想完成什么进展，Job Story 格式）
2. **触发场景**：触发条件 + 时间延迟（立即/X秒后）+ 频率限制
3. **目标用户**：包含哪些用户（具体）+ 排除哪些用户
4. **核心内容**：实际文案草稿（不是描述）+ 优惠信息/数据 + 视觉素材需求
5. **用户操作路径**：主操作（按钮文案 → 点击后行为）+ 次要操作（如有）+ 最终目标
6. **交付形式**：新页面（含路由路径）或现有页面新增（说明具体页面）

### 选填项
- 覆盖端（Desktop/Mobile/两者）
- 边界状态需求
- 语言版本
- 参考案例链接

### 设计参考建议（单独章节，明确标注"仅供参考"）
- 展示位置参考
- 视觉基调参考（不指定颜色，描述感觉：正向/成功感/警示等）
- 交互方式参考（静态/动态/可关闭等）
- 与现有元素优先级参考
- 竞品/行业参考

**注意**：必填项绝对不能包含设计决策（不指定组件类型、不指定颜色值、不指定动画效果）。设计决策全部放在"设计参考建议"章节，且明确标注"仅供参考，Design Agent 可自行判断是否采用"。

---

## SRD（给业务方，简化版）

面向业务方，不含技术细节：
- 需求背景
- 业务目标
- 核心指标（Primary Metric）
- 目标用户
- 推荐方向（方案名称 + 一句话描述）
- 预期效果
- 复杂度估算（C几，大概周期）
- 风险提示（业务层面）

---

## Copy Package（5语言文案包）

格式：JSON，每条文案包含：
- copy_id：文案唯一标识
- usage_scene：使用场景描述
- component：所在组件
- max_length：最大字符数
- translations：zh-CN、zh-TW、en-US、ja-JP、ko-KR 五种语言

**要求**：
- 英文文案必须符合北美电商语境，不是中文直译
- 每种语言文案长度不超过 max_length
- 同一文案的不同语言版本语义等价，但允许本地化表达

---

## AB Test Brief

包含：
- 实验假设（If [变量] Then [结果] Because [原因]）
- 影响变量描述
- 核心变量关系（Pros/Cons）
- 预期日均用户数（基于页面 UV 数据估算）
- 实验受众（用户分群 + 平台 + 国家）
- 分组说明：V0（对照组，保持现状）/ V1（实验组，含变更内容）
- 分流时机（用户在什么时刻进入实验）
- Primary Metric / Secondary Metrics / Guardrail Metrics
- 建议运行周期
- 最小样本量
- 上线/停止规则（显著性阈值 + Guardrail 触发条件）

---

## Tracking Spec

每个埋点事件包含：
- event_name：命名规范 `{page}_{component}_{action}`，如 `checkout_incentive_banner_impression`
- trigger：触发时机描述
- page：所在页面
- component：所在组件
- user_segment：目标用户分群（可选）
- parameters：参数列表（key: 描述）
- is_exposure / is_click / is_conversion：事件类型标记
- used_for_ab：是否用于 AB 实验数据分析
- reuse_existing：如果复用已有事件，填写已有事件名称；新增则填 null

**要求**：先检查代码索引中已有的埋点事件，能复用的优先复用，不要重复新增。每个需求至少包含：曝光事件 + 转化事件（与 Primary Metric 直接关联）。

---

## QA Criteria（验收标准）

每个维度至少 3 条具体验收项：

1. **功能验收**：触发条件、展示逻辑、边界值（如金额临界）
2. **UI 验收**：样式、颜色、间距、响应式布局
3. **多语言验收**：各语言文案正确性、字符长度不超限
4. **国家/站点验收**：仅指定国家/站点展示，其他不展示
5. **用户分群验收**：目标用户可见，非目标用户不可见
6. **埋点验收**：事件触发正确，参数上报完整
7. **AB 分组验收**：分流逻辑正确，同设备始终在同一分组
8. **边界/异常状态**：网络异常、接口超时、数据为空时的降级处理
9. **回归范围**：不影响现有功能的正常使用
10. **线上监控点**：上线后需监控的关键指标和报警阈值

---

## Task Package（JSON，给下游 Agent）

```json
{
  "requirement_id": "order-detail-ai-detection-notice-20260514-001",
  "module": "页面/模块名称",
  "request_type": "需求类型",
  "business_goal": "业务目标描述",
  "primary_metric": "核心指标",
  "country_scope": ["US"],
  "platform_scope": ["App", "mWeb"],
  "language_scope": ["en-US", "zh-CN"],
  "target_users": ["non_customer"],
  "recommended_solution": "推荐方案描述",
  "complexity_score": 5,
  "risk_level": "medium",
  "ui_task": { "required": true, "handoff_ref": "UIH-order-detail-ai-detection-notice-20260514-001" },
  "coding_task": { "required": true, "prd_ref": "PRD-order-detail-ai-detection-notice-20260514-001" },
  "qa_task": { "required": true, "acceptance_ref": "QA-order-detail-ai-detection-notice-20260514-001" },
  "ab_test": { "required": true, "brief_ref": "AB-order-detail-ai-detection-notice-20260514-001" },
  "approval_required": ["business_direction_confirmation"]
}
```

---

## Google Doc 自动推送

每次生成以下交付物后，立即调用 google-workspace MCP 的 `create_doc` 工具：

| 交付物 | Google Doc 标题格式 | 内容格式 |
|--------|-------------------|---------|
| PRD | `[需求ID] PRD - [需求标题]` | Markdown 原文 |
| UIH | `[需求ID] UIH - [需求标题]` | Markdown 原文 |
| QA Criteria | `[需求ID] QA Criteria - [需求标题]` | Markdown 原文 |
| Copy Package | `[需求ID] Copy Package - [需求标题]` | JSON 转 Markdown 表格（每语言一列） |

推送完成后，在回复中统一列出链接：
```
📄 交付物已同步到 Google Doc：
- PRD：[链接]
- UIH：[链接]
- QA Criteria：[链接]
- Copy Package：[链接]
```

如果 Google Doc 创建失败，说明失败原因，不影响其他交付物的推送。

---

## OpenProject 工单自动创建（可选，不阻断主流程）

**优先级：最低。所有 Google Doc 和本地文件交付完成后，最后尝试创建 OP 工单。**

**规则：**
- 仅尝试一次，失败则静默跳过，不重试
- 失败时不告知业务方，不在回复中提及 OP 失败
- 成功时在交付物链接列表末尾追加 OP 链接
- OP 创建不影响其他任何交付物的生成和推送

生成 PRD 后，尝试调用 openproject MCP 的 `create_work_package` 工具：

**创建参数：**

| 参数 | 值 |
|------|-----|
| projectId | `tech-team` |
| subject | `[Purchase Agent] {需求标题}` |
| type | `6`（User Story） |
| description | PRD 摘要（前 2000 字符） |
| customFields | 见下方 |

**必填自定义字段（customFields 参数）：**

```json
{
  "customField9": {"href": "/api/v3/users/31"},
  "customField16": {"href": "/api/v3/users/19"},
  "customField1": [{"href": "/api/v3/custom_options/6"}],
  "customField54": {"href": "/api/v3/custom_options/246"},
  "customField89": {"href": "/api/v3/custom_options/1"}
}
```

字段说明：
- customField9 (PIC): logan yang (user 31)
- customField16 (Requestor): hank zhao (user 19)，如能获取企微发消息人则用对应用户
- customField1 (Channel): Purchase (option 6)
- customField54 (Theme): 营销类→Marketing efficiency / 转化增长类→Organic Growth / 其他→Improvement（默认用 option 246）
- customField89 (Requirement type): New Feature（默认 option 1），Bug 流程用 Bug Fix

**成功时输出格式：**

在交付物链接列表末尾追加：
```
📋 OP 工单：https://openproject.yamibuy.net/work_packages/{id}
```

**失败时：** 静默跳过，不输出任何关于 OP 的信息。
