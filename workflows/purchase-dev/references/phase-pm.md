# Phase pm

结构化分析需求，产出 PRD/UIH，判定后续阶段路由。

## 产出契约

`outputs/phase-pm.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `task_type` | string | `feature` / `bug` / `config` / `data` |
| `need_design` | string | `yes` / `no` ← **控制 design 阶段是否跳过** |
| `need_code` | string | `yes` / `no` ← **控制 api/arch/code/ut/review/qa 是否跳过** |
| `need_tracking` | string | `yes` / `no` ← **控制是否需要埋点设计** |
| `summary` | string | 一句话说清做什么，下游所有阶段都会读 |
| `prd_path` | string | 相对 instance-dir 的路径，如 `outputs/prd.md` |

选填但建议：`uih_path`、`srd_path`、`op_number`、`services`(array)、`acceptance`(array)、`prd_doc_url`。

`outputs/phase-pm.md`：PRD 正文。

## 两个开关的取值规则

- `params.need_design` 是 `yes`/`no` 时直接沿用；是 `auto` 时自行判定（有视觉变更填 `yes`）
- 判 `need_code: no` 前必须实地查过代码或表结构，不能凭需求描述推断
- `need_tracking` 判定规则：PRD 或需求描述中有「埋点」「tracking」「上报」「曝光」「点击事件」「AB实验」等字样 → `yes`

## 埋点需求产出（need_tracking=yes 时必须执行）

当判定 `need_tracking: yes` 时，**PM 阶段必须产出业务层埋点需求文档**：

### 产出路径
`requirements/OP-XXXXX/tracking-spec.md`

### 必须包含内容
1. **事件列表**：列出本需求涉及的所有埋点事件
2. **每个事件必须说明**：
   - 事件名称（业务语义，如「弹窗曝光」「登录成功」）
   - 触发时机（用户做什么操作时触发）
   - 主要参数（需要上报哪些业务参数）
   - 用途说明（用于什么分析/AB实验）

### 示例格式
```markdown
# Tracking Spec - 需求名称

> 需求ID：OP-XXXXX

## 事件列表

### 1. 曝光事件
- 事件名称：功能模块曝光
- 触发时机：组件首次进入视口时触发一次
- 主要参数：site, language, user_segment
- 用途：统计功能曝光量

### 2. 点击事件
- 事件名称：功能按钮点击
- 触发时机：用户点击按钮时触发
- 主要参数：site, button_type
- 用途：统计用户互动率
```

**禁止**：
- ❌ `need_tracking: yes` 但不产出 tracking-spec.md
- ❌ 只在 PRD 里写埋点需求，不单独产出 tracking-spec.md（arch 阶段需要读取）

## 信息不足时

不要脑补，暂停等需求方回复（回复会注入下轮 prompt 的 § 0）：

```bash
python3 <complete-phase.py> "<instance-dir>" pause "需确认：1) xxx 2) xxx"
```

## 路由

产出合法后完成本阶段 → `pm_review`。


---

## 埋点需求产出（need_tracking=yes 时强制执行）

当判定 `need_tracking: yes` 时，**必须**完成以下产出，否则 `complete-phase.py` 会拒绝推进：

### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `tracking_events_count` | number | 本需求涉及的埋点事件数量（必须 > 0） |
| `tracking_spec_path` | string | 埋点需求文档路径，如 `requirements/OP-38713/tracking-spec.md` |

### 必须创建的文件

**路径**：`requirements/OP-XXXXX/tracking-spec.md`

### ⛔ 验证规则

`complete-phase.py` 会自动检查：

1. ✅ `tracking_events_count` 必须 > 0
2. ✅ `tracking_spec_path` 指向的文件必须真实存在
3. ❌ 只在 PRD 里写埋点需求、不单独产出 tracking-spec.md → 拒绝推进
4. ❌ tracking_spec_path 填了但文件不存在 → 拒绝推进
