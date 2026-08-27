---
name: "e2e-test-agent"
description: >
  端到端测试 Agent，用于产研一体化流程中的自动化测试。
  由调度中心通过 Kiro CLI 调用，全流程无人工介入。
  触发词：e2e测试, 端到端测试, 自动化测试全流程, e2e-test-agent
  不适用：单独执行某个子 skill（直接调用对应 skill）
---

# E2E Test Agent

端到端测试 Agent。接收调度中心指令，自动完成从需求分析到自动化代码生成的全流程测试。

## 双 Agent 架构

| Agent | 配置文件 | 职责 | 执行指令 |
|-------|---------|------|---------|
| **Agent A**（purchase-qa-agent） | `.kiro/agents/purchase-qa-agent.json` | 需求分析、造数据、调度 Agent B、汇总报告、生成自动化代码 | `references/agent-a-instructions.md` |
| **Agent B**（browser-test-agent） | `.kiro/agents/browser-test-agent.json` | 操作浏览器执行测试用例 / 录制元素定位 | `references/agent-b-instructions.md` |

## 流程概览

```
阶段 1: 需求+代码分析 → 知识库 + 测试用例
阶段 2: 数据准备 → data-factory 造数
阶段 3: 第一轮测试 → Agent B 逐批执行，收集 Bug
阶段 4: Bug 修复验证 → 重跑失败用例（最多 5 轮）
阶段 5: 全量测试+录制 → Agent B 录制元素定位（最多 3 轮）
阶段 6: 自动化代码生成 → Playwright 脚本 + Git 推送
阶段 7: 最终报告 → 汇总上传 CDN
```

## 触发方式

调度中心写入 pipeline-context.json 的 trigger 字段后调用 Agent A：

| trigger | 含义 | Agent A 执行 |
|---------|------|-------------|
| `code_ready` | 代码提测 | 连续执行阶段 1→2→3 |
| `bug_fixed` | Bug 已修复 | 阶段 4 |
| `all_bugs_fixed` | Bug 全部修复 | 阶段 5 |
| `test_passed` | 测试通过 | 连续执行阶段 6→7 |

## 辅助脚本

| 脚本 | 用途 |
|------|------|
| `scripts/report_generator.py` | 生成 HTML 报告 |
| `scripts/state_manager.py` | 状态管理 |
| `scripts/cdn_upload.py` | 上传文件到 CDN |

## 关联 Skills

| Skill | 阶段 | 用途 | 加载方式 |
|-------|------|------|---------|
| `autoqa-build-feature-knowledge` | 1 | 生成知识库 | `yami-ai-cli read autoqa-build-feature-knowledge` |
| `autoqa-generate-testcase-doc` | 1 | 生成测试用例 | `yami-ai-cli read autoqa-generate-testcase-doc` |
| `autoqa-verify-and-record-testcase` | 3,4,5 | 浏览器测试+录制 | `yami-ai-cli read autoqa-verify-and-record-testcase` |
| `autoqa-generate-playwright-scripts` | 6 | 生成自动化脚本 | `yami-ai-cli read autoqa-generate-playwright-scripts` |
| `data-factory` | 2 | 造测试数据 | 本地：`.kiro/skills/data-factory/main.py` |
