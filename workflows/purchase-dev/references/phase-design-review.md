# Phase design_review

审查设计稿是否符合设计系统与 PRD，通过后产出设计师评审包。

本阶段在 `phase-pm.json` 的 `need_design == "no"` 时自动跳过。

## 产出契约

`outputs/phase-design_review.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `conclusion` | string | **只能是 `pass` 或 `fail`** ← 路由字段 |
| `loop_count` | number | 从 `status.json` 取本 phase 的 `loopCount`（首轮填 0） |
| `issues` | array | `fail` 时必须非空；每项含 `severity` `target` `problem` `suggestion` |

`pass` 时不能有 `severity: high`，且需附 `review_package_url`（评审包的 Drive 链接）。

`outputs/phase-design_review.md`：审查报告。

## 必须 fail 的情形

发现设计方案在现有代码结构下**无法实现**时（例如 PRD 要求埋点，但该元素由 CMS 以 HTML 字符串整体渲染、无法绑定事件），必须 `fail` 并在 issue 中说明结构性冲突 —— 这类问题放到编码阶段才发现会导致整个方案返工。

## 回环上限

```
loop_count <  params.max_retry  →  可输出 fail
loop_count >= params.max_retry  →  禁止 fail，改为：
    python3 <complete-phase.py> "<instance-dir>" block "设计审查已打回 N 次仍不通过：<分歧>。需人工判断：<方向>"
```

## 路由

```
conclusion = fail  →  回 design 重做
conclusion = pass  →  api
```
