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

建议附 `branch_clean`(bool)、`arch_compliance`(bool)。

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
