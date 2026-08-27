# Phase doc

产出接口文档和测试发布文档，流程最后一步。

## 产出契约

`outputs/phase-doc.json` 必填字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `api_doc_path` | string | 接口文档路径，如 `outputs/api-doc.md` |
| `test_doc_path` | string | 测试发布文档路径 |
| `deliverables` | array | 每项含 `type`(branch/pr/db/config/design) `value`；无变更的类型填 `"无"` |

选填：`api_doc_url`、`test_doc_url`（Google Doc 链接）、`sheet_filled`(yes/no)。

`outputs/phase-doc.md`：交付总结，一页读完。

## 硬要求

**接口文档的字段从实际代码读**，不是抄 API 契约 —— 契约是设计意图，代码是事实。

**测试发布文档面向测试同学**，后端变更要反向追踪到前端页面操作：

| ❌ | ✅ |
|---|---|
| `queryOrderLog` 查询正常 | 后台 → 订单管理 → 订单详情 → 查看操作日志，验证显示正常 |

追踪方法：接口路径 → `grep` 哪个前端项目在调 → 定位页面 → 写成用户操作路径。

**配置变更和 DB 变更即使为空也要明确写「无」**，不能省略。有 DDL 时必须写明发布顺序（DDL 先于代码）。

## 路由

本阶段无出边，完成后流程结束（`status = completed`），自动推企微通知。
