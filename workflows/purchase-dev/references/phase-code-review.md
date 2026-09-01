# Phase code_review

审查实现与架构方案的一致性、代码质量、分支干净度。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。

## 产出契约

`outputs/phase-code_review.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `conclusion` | string | **只能是 `pass` 或 `fail`** ← 路由字段 |
| `loop_count` | number | 从 `status.json` 取本 phase 的 `loopCount`（首轮填 0） |
| `issues` | array | `fail` 时必须非空；每项含 `severity`(high/medium/low) `target`(文件:行号) `problem` `suggestion` |

建议附 `branch_clean`(bool)、`arch_compliance`(bool)、`tracking_compliance`(bool)。

`pass` 的条件：无 `severity: high` 且 `branch_clean` 为 true。`branch_clean: false` 时必须 `fail`。

`outputs/phase-code_review.md`：审查报告，写清审了哪些文件、核对了哪些表结构。

## 硬要求

**审查优先级**：会崩 > 会错 > 会慢 > 不好看。别在代码风格上耗时间而漏掉会报错的问题。

**分支隔离**用带 range 的命令判断，不要用不带 range 的 `git log`（会列出已合并到 master 的祖先 commit，历史上因此误判过干净分支）：

```bash
git log origin/master..HEAD --oneline
git diff --name-only origin/master HEAD
```

**数据库相关代码**要自己跑 `SHOW FULL COLUMNS` 核对 Entity 类型和枚举值，别信注释。

## 埋点代码实现检查（need_tracking=yes 时必须）

**当 `phase-pm.json` 的 `need_tracking == "yes"` 时，必须检查埋点代码实现：**

### 检查项

| 检查项 | 验证方法 | 不通过条件 |
|--------|----------|-----------|
| 事件常量已定义 | grep AnalyticsEventNameMap 或 enum.js | tracking-spec.md 中的事件未在代码中定义 |
| 事件名格式正确 | 对比 tracking-spec.md | Sensor/Yamidata 用点号、Ymb 用下划线（格式搞反） |
| 埋点调用存在 | grep analytics.track 或对应的 track 函数 | 定义了事件但没有调用 |

### 检查命令

```bash
# 读取 tracking-spec.md 获取事件列表
cat ~/workspace/purchase/requirements/OP-XXXXX/tracking-spec.md

# Next.js 仓库检查
grep -rn "AnalyticsEventNameMap" ~/code/yami/worktrees/ec-website-next--OP-XXXXX/src/
grep -rn "analytics.track" ~/code/yami/worktrees/ec-website-next--OP-XXXXX/src/features/

# Laravel 仓库检查
grep -rn "EVENT_" ~/code/yami/worktrees/ec-website-*-nb--OP-XXXXX/resources/assets/js/
```

### 不通过时的 issue 格式

```json
{
  "severity": "high",
  "target": "埋点实现",
  "problem": "tracking-spec.md 定义的事件 EVENT_XXX 未在代码中实现",
  "suggestion": "在 mapEventName.ts 新增事件常量，在各 adapter 添加 case，在业务组件调用 analytics.track"
}
```

## 回环上限

```
loop_count <  params.max_retry  →  可输出 fail
loop_count >= params.max_retry  →  禁止 fail，改为：
    python3 <complete-phase.py> "<instance-dir>" block "代码审查已打回 N 次仍不通过：<分歧>。需人工判断：<方向>"
```

## 路由

```
conclusion = fail  →  回 code 修复
conclusion = pass  →  qa
```


---

## 埋点实现审查（need_tracking=yes 时必须执行）

### 审查清单

| 检查项 | 严重级别 | 审查方法 |
|--------|---------|---------|
| **事件名一致性** | HIGH | 代码事件常量与 tracking_events.name 一致 |
| **格式正确性** | MEDIUM | Sensor/Yamidata 下划线，Ymb 点号 |
| **复用规范** | HIGH | 通过 AnalyticsEventNameMap 常量调用 |
| **参数完整性** | MEDIUM | 参数与 tracking_events.params 一致 |

不通过时记录 issue 并 loop-back 到 code 阶段。
