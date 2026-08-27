# Phase arch

制定实现方案：改哪些文件、复用哪些公共工具、DB 与配置怎么变。coder 会严格照做。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。

## 产出契约

`outputs/phase-arch.json` 必填字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `arch_path` | string | 架构规范全文路径，如 `outputs/architecture.md` |
| `services` | array | 涉及的服务 |
| `db_changes` | array | 无变更时填 `[]`；有变更时每项含 `type`(ddl/dml) `target` `script_path` `rollback_path` |
| `config_changes` | array | 无变更时填 `[]`；有变更时每项含 `type`(apollo/cms) `key` `value` |

选填：`modules`、`files_new`、`files_modified`、`tools_reused`、`deploy_order`、`complexity`。

`outputs/phase-arch.md`：架构规范全文，需包含修改范围、复用的公共工具、类设计、DB 变更、配置变更、编码约束。

## 硬要求

- `db_changes` 里的 DDL/DML，字段类型和 NOT NULL 约束必须用 `SHOW FULL COLUMNS` 核对过
- DML 的 `WHERE` 要能精确定位（生产库同一业务 key 可能按 `site_code` 等维度多行）
- 配置类变更如果目标 value 是整段内容，方案必须写明**增量修改**而非整段覆盖
- 有 DDL 时必须在 `deploy_order` 说明「DDL 先于代码部署」

## 路由

产出合法后完成本阶段 → `arch_review`。
