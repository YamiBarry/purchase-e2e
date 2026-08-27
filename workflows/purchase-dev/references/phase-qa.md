# Phase qa

部署测试环境，跑接口与场景测试，逐条验证 PRD 的验收标准。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。

## 产出契约

`outputs/phase-qa.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `conclusion` | string | **只能是 `pass` 或 `fail`** ← 路由字段 |
| `loop_count` | number | 从 `status.json` 取本 phase 的 `loopCount`（首轮填 0） |
| `env` | string | 实际部署的环境，取自 `params.test_env` |
| `cases` | array | 每项含 `id`(对应 PRD 的 AC 编号) `desc` `result`(pass/fail) `evidence` |
| `failures` | array | `fail` 时必须非空；每项含 `case_id` `expected` `actual` `log` |

建议附 `deploy`（每项 `service` `branch` `related_id` `status`）、`screenshots`。

`pass` 的条件：`cases` 全部 `result: pass` 且 `failures` 为空。

`outputs/phase-qa.md`：测试报告。

## 硬要求

- PRD 的每条 AC 都要有对应用例，AC 没全过不能 `pass`
- 数据变更要用 SQL 验证真的落库，不能只看接口返回 200
- `failures` 的信息量要够 coder 定位问题（请求、响应、日志）

## 部署失败或环境问题

不要反复重试，转人工：

```bash
python3 <complete-phase.py> "<instance-dir>" block "IDP 部署失败 related_id=<id>：<错误>。需查看构建日志"
```

前端仓库（`ec-website-*`）不走 IDP，遇到前端变更直接 block 说明需人工部署。

## 回环上限

```
loop_count <  params.max_retry  →  可输出 fail（回 code 修复）
loop_count >= params.max_retry  →  禁止 fail，改为：
    python3 <complete-phase.py> "<instance-dir>" block "集成测试已失败 N 轮：<失败用例>。需人工判断是实现问题还是环境/用例问题"
```

## 路由

```
conclusion = fail  →  回 code 修复
conclusion = pass  →  doc
```
