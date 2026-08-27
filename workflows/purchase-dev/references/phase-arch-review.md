# Phase arch_review

审查架构方案的需求覆盖度与技术合理性，coder 之前的最后一道闸门。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。

## 产出契约

`outputs/phase-arch_review.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `conclusion` | string | **只能是 `pass` 或 `fail`** ← 路由字段 |
| `loop_count` | number | 从 `status.json` 取本 phase 的 `loopCount`（首轮填 0） |
| `issues` | array | `fail` 时必须非空；每项含 `severity` `target` `problem` `evidence` `suggestion` |

建议附 `requirements_coverage`：逐条列 PRD 的 FR/AC 编号 + `covered`(bool) + `where`。

`pass` 的条件：无 `severity: high` 且 `requirements_coverage` 里无 `covered: false`。

`outputs/phase-arch_review.md`：审查报告，写清实地核对了哪些代码、查了哪些表。

## 硬要求

issue 里的 `evidence` 必须是你**实地验证的结果**（grep 到的代码位置、SQL 查询结果），不能只凭方案描述判断。方案说要复用的类和方法，必须去 `{CODE_DIR}` 确认真实存在。

## 回环上限

```
loop_count <  params.max_retry  →  可输出 fail
loop_count >= params.max_retry  →  禁止 fail，改为：
    python3 <complete-phase.py> "<instance-dir>" block "架构审查已打回 N 次仍不通过：<分歧>。需人工判断：<方向>"
```

## 路由

```
conclusion = fail  →  回 arch 重做
conclusion = pass  →  code
```
