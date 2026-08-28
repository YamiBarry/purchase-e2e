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
# 按功能关键词搜索（替换 {关键词}）
grep -rn "{关键词}" ~/code/yami/ --include="*.ts" --include="*.tsx" --include="*.js" \
  -l 2>/dev/null | grep -v node_modules | grep -v dist | head -20

# 登录/第三方登录类需求必搜
find ~/code/yami/ec-website-next/src -name "*.tsx" | \
  xargs grep -l "OneTap\|one.tap\|thirdLogin\|GoogleOneTap\|oauth\|socialLogin" 2>/dev/null

# 特别注意：ec-website-next 的 canada-v2 目录有多个已落地功能的参考实现
ls ~/code/yami/ec-website-next/src/app/\[lang\]/canada-v2/_compotents/
```

找到参考实现后必须：
1. **读完参考文件**，理解核心逻辑（组件挂载位置、判断条件、数据流、埋点方式）
2. **明确复用 vs 扩展 vs 新写**：
   - 能直接复用的模块 → 提取到通用位置，不重写
   - 需要扩展的逻辑 → 在原有基础上加，不另起炉灶
   - 真正没有的 → 才新写，且要参考已有模式（埋点、接口调用、错误处理）
3. **架构文档必须说明**：参考了哪个文件、复用了什么、扩展了什么、为什么新写

**参考实现优先级**：
- 同一仓库已有实现 > 其他仓库已有实现 > 全新设计
- 埋点必须复用 `analytics.track()` + `AnalyticsEventNameMap`，不自造事件名和格式

## 埋点方案设计（需求含埋点时必须执行）

**arch 阶段负责完整的埋点技术方案，完成后必须同步回需求产物目录。**

### 执行步骤

1. 读取 PM 产出的 `requirements/OP-XXXXX/tracking-spec.md`，了解业务层埋点需求（要哪些事件、参数）
2. 按 `tracking-spec` skill 执行埋点设计（查 Sheet → 设计事件名 → 新增 sheet 页）
3. **将完整技术埋点方案写回** `requirements/OP-XXXXX/tracking-spec.md`，覆盖 PM 的业务层版本

写回后的 tracking-spec.md 必须包含：
- 每个事件的 `AnalyticsEventNameMap` 常量名
- Sensor/Yamidata 事件名（下划线）
- Ymb 事件名（点号）
- 触发时机和主要参数
- 埋点 Sheet 的 tab 名称（供 QA 验证时查阅）

**禁止**：只在架构文档里写埋点方案，不更新 requirements 目录（会导致 coder 和 QA 看不到完整定义）
