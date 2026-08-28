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

## 强制前置步骤：搜索已有实现（不可跳过）

**在做任何架构设计之前，必须先搜索是否已有同类功能的实现。**

```bash
# 按功能关键词搜索
grep -rn "{功能关键词}" ~/code/yami/ --include="*.ts" --include="*.tsx" --include="*.js" \
  --include="*.java" -l 2>/dev/null | grep -v node_modules | grep -v dist | head -20
```

找到参考实现后必须：
1. 读懂参考实现的核心逻辑（组件挂载位置、判断条件、数据流）
2. 明确新实现与参考实现的**相同点和差异点**
3. 优先复用参考实现的模式，不重新发明

**参考实现优先级**：
- 同一仓库已有实现 > 其他仓库已有实现 > 全新设计
- 复用现有埋点方式（`analytics.track` + `AnalyticsEventNameMap`），不自造事件名格式

**架构文档必须包含**：
- 是否有参考实现（有则列出文件路径）
- 与参考实现的关键差异及原因
