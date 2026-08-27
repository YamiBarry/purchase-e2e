# purchase-e2e workspace

Purchase Team 的 AI Agent 工作空间配置，运行在 `purchase.e2e.ai` 服务器上，基于 [yami-agent](https://github.com/yamibuy/yami-agent) 驱动。

## 架构概览

```
企微用户发消息
    ↓
yami-agent（:8900）
    ↓
kiro-cli 进程池（6个）
    ↓
purchase-pm-agent（默认入口）
    ↓
用户确认需求后 → 触发 purchase-dev workflow → 各专用 Agent 自动推进
```

## 目录说明

```
.kiro/
├── agents/          # Agent 定义（prompt + 工具权限 + 资源）
├── steering/        # 全局规则文档（所有 Agent 共享）
├── skills/          # 可复用能力模块（Agent 动态加载）
└── hooks/           # 自动触发钩子

workflows/
├── purchase-dev/
│   ├── workflow.json          # 流程 DAG 定义
│   └── references/            # 每个 phase 的执行指南
└── .scripts/
    ├── complete-phase.py      # Phase 推进脚本
    └── get-phase-guide.py     # Phase 指南读取脚本

config/                        # 测试环境配置
bin/                           # 工具脚本
mcp-servers/                   # MCP 服务器源码
```

## Agents

| Agent | 职责 | workflow phase |
|-------|------|----------------|
| `purchase-pm-agent` | 需求分析、产出 PRD，**默认对话入口** | pm |
| `purchase-pm-review-agent` | PRD 审计 | pm_review |
| `purchase-design-agent` | HTML 设计稿 | design |
| `purchase-design-review-agent` | 设计审查 | design_review |
| `api-designer-agent` | 接口契约设计 | api |
| `architect-agent` | 架构规范 | arch |
| `reviewer-agent` | 架构/代码审查 | arch_review, code_review |
| `coder-agent` | 编码实现、提交 PR | code |
| `ut-generator` | 单元测试（Spock） | ut |
| `purchase-qa-agent` | 集成测试调度 | qa |
| `doc-engineer-agent` | 交付文档生成 | doc |

## workflow：purchase-dev

从需求到 PR 的全自动流水线，DAG 流程：

```
pm → pm_review ⇄ pm（打回）
    ↓
design → design_review ⇄ design（skipIf: need_design=no）
    ↓
api → arch → arch_review ⇄ arch（打回）（skipIf: need_code=no）
    ↓
code → ut → code_review ⇄ code（打回）
    ↓
qa ⇄ code（测试失败回修）
    ↓
doc
```

### 触发方式（企微）

在企微对 purchase-agent 说需求，PM Agent 分析完成后自动创建 OP 工单，用户确认后自动触发 workflow。

## 部署环境

- **服务器**：`purchase.e2e.ai`（AWS t3.medium，2C4G）
- **Admin 面板**：`http://44.254.245.48:3000`（需 token）
- **yami-agent 端口**：`:8900`（HTTP）
- **systemd 服务**：`yami-agent`

```bash
# 查看状态
sudo systemctl status yami-agent

# 查看日志
tail -f ~/logs/yami-agent.log

# 重启（配置变更后）
sudo systemctl restart yami-agent
```

## 配置说明

| 文件 | 说明 |
|------|------|
| `.env` | 环境变量（**不入库**，参考 `.env.example`） |
| `config.json` | 企微 Bot 配置（**不入库**，参考 `config.example.json`） |
| `.kiro/settings/mcp.json` | MCP 工具连接配置（**不入库**，含各服务 token） |

## 不在此仓库的内容

- `sessions/` — 用户对话历史
- `workflow-instances/` — workflow 运行产物
- `requirements/` — 需求文档（PM Agent 产出）
- `deliverables/` — 旧版需求文档

---

> 维护：Purchase Team E2E
