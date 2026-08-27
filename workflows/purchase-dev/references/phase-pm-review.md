# Phase pm_review

审计 PM 交付物的完整性与一致性。

## 产出契约

`outputs/phase-pm_review.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `conclusion` | string | **只能是 `pass` 或 `fail`** ← 路由字段，其他值会导致路由失效 |
| `loop_count` | number | 从 `status.json` 取本 phase 的 `loopCount`（首轮无此字段则填 0） |
| `issues` | array | `fail` 时必须非空；每项含 `severity`(high/medium/low) `target` `problem` `suggestion` |

`pass` 时 `issues` 里不能有 `severity: high`。

`outputs/phase-pm_review.md`：审查报告。

## 回环上限（引擎无保护，必须自己判断）

```
loop_count <  params.max_retry  →  可输出 fail
loop_count >= params.max_retry  →  禁止输出 fail，改为转人工：
    python3 <complete-phase.py> "<instance-dir>" block "PRD 审计已打回 N 次仍不通过：<核心分歧>。需人工判断：<2-3 个方向>"
```

`block` 会自动推企微通知；人工回复后从本阶段继续，回复出现在下轮 prompt 的 § 0。

## 路由

```
conclusion = fail  →  回 pm 重做
conclusion = pass  →  design
```
