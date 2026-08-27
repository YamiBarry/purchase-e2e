# Phase api

设计接口契约，首要任务是判断是否真的需要新增接口。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。

## 产出契约

`outputs/phase-api.json` 必填字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `contract_path` | string | OpenAPI YAML 路径；无新增接口时填 `""` |
| `endpoints` | array | 每项含 `method` `path` `status`(`new`/`reused`/`extended`) |
| `services` | array | 涉及的服务名 |

选填：`need_new_endpoint`(`yes`/`no`)、`entities_reused`、`entities_new`、`error_codes`、`db_fields_verified`、`evidence`。

`outputs/phase-api.md`：契约说明 + 复用判断的代码依据（贴出关键代码位置）。

## 硬要求

- 「是否需要新增接口」的结论必须有代码依据，写进 `evidence`
- 涉及数据库字段时，用 `SHOW FULL COLUMNS` 查过真实结构，结果写进 `db_fields_verified`
- 新增错误码要确认号段无冲突

## 路由

产出合法后完成本阶段 → `arch`。
