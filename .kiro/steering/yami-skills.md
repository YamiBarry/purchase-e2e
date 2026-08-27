---
inclusion: always
---

# 可用 Skills

以下 skills 可通过 `yami-ai-cli read` 命令按需加载。当用户要求执行相关任务时，请使用对应的 skill。

## 使用方式

- 调用: `yami-ai-cli read <skill-name>`（在终端中运行）
  - 多个 skill: `yami-ai-cli read skill-one,skill-two`
- skill 内容会输出详细的任务指令
- 输出中包含 Base directory，用于解析 skill 附带的资源文件（references/、scripts/、assets/）

## 注意事项

- 仅使用下方列出的 skills
- 不要重复加载已在上下文中的 skill

## Skills 列表

- **api-test** — 对 Yamibuy 微服务进行 HTTP 接口测试。支持 UAT、DEV、GQC 多环境切换，自动携带 token 和 headers。当用户需要测试接口、验证 API 返回、调试服务时使用。
- **autoqa-build-feature-knowledge** — 当需要分析功能需求、建设功能知识库、沉淀业务知识文档、理解功能上下文和依赖关系时使用。
- **autoqa-code-helper** — 当需要基于测试用例文档和操作录制文档生成自动化测试脚本、创建 Selenium action 和 case、自动化测试代码生成时使用。
- **autoqa-fix-failed-test** — 当需要分析自动化测试报告、修复失败用例、定位测试脚本错误、排查测试失败原因时使用。
- **autoqa-flutter-qa-attributes-tagger** — 当需要为 Flutter 代码添加 autoQaId 测试属性、识别按钮文本和可点击元素、方便自动化测试定位元素时使用。
- **autoqa-generate-playwright-scripts** — 当验证全部通过、需要基于技术录制文档（JSON）生成 Playwright 自动化测试脚本、执行验证并提交 PR 时使用。
- **autoqa-generate-testcase-doc** — 当需要基于知识库文档生成结构化测试用例、设计测试用例、写入 Google Sheet 时使用。
- **autoqa-pipeline** — 当需要执行自动化测试全流程（知识建设→测试用例→探索式验证→脚本生成）时使用。
- **autoqa-react-qa-attributes-tagger** — 当需要为 React 代码添加 data-qa-* 测试属性、识别按钮文本和可点击元素、方便自动化测试定位元素时使用。
- **autoqa-verify-and-record-testcase** — 当测试用例已确认、需要通过浏览器验证功能并录制操作路径、生成增强版技术录制文档时使用。
- **cdn-upload** — 
- **code-branch-diff** — 当需要对比分支代码差异、查看代码变更、分析提交记录、生成 diff 报告时使用。触发词：diff, 代码对比, 分支差异, git diff, 代码变更
- **code-module-analyzer** — 当需要分析代码模块、理解代码结构、追踪调用链、生成代码文档时使用。触发词：这段代码, 帮我看看, 分析一下, 这个模块, 什么意思, 怎么实现的, 代码分析
- **code-simplifier** — 当需要简化代码、重构代码、优化代码结构、提升代码可读性、清理冗余代码时使用。触发词：simplify, refactor, clean code, 代码简化, 重构, 代码优化
- **control-browser** — 当需要使用浏览器、操作网页、验证前端效果、截图测试时使用。触发词：浏览器, 打开网页, 截图, 页面验证, playwright, chrome
- **docx** — Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents, performing find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a 'report', 'memo', 'letter', 'template', or similar deliverable as a Word or .docx file, use this skill. Do NOT use for PDFs, spreadsheets, Google Docs, or general coding tasks unrelated to document generation.
- **explore-design-ideas** — 当需要讨论方案、探讨设计思路、需求梳理、技术选型讨论时使用。触发词：讨论, 探讨, 设计方案, 需求讨论, 聊聊, 商量, discuss, 方案对比, 技术选型
- **explore-knowledge-graph** — 当用户提问时自动触发，从知识图谱中检索相关的业务规则、服务关系、配置约定、代码位置、业务枚举、业务术语，为回答提供上下文。触发词：业务规则, 服务关系, 配置约定, 代码位置, 业务枚举, 业务术语, 知识图谱
- **figma-plugin-architect** — 开发 Figma 插件时使用。生成 manifest.json、code.ts、ui.html 标准架构代码，包含 Variables API、双线程通信、类型安全最佳实践。
- **find-skills** — Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
- **manage-openproject** — 当需要查询 OP、创建 OP、更新 OP、查看项目工作包、管理工作包状态时使用。
- **manage-session-memory** — 当需要保存对话记忆、检索历史知识、查看决策记录、回忆踩坑经验、管理 LLM 记忆时使用。
- **review-code-changes** — 当需要对当前分支的 git 变更进行（PR Review）代码审查、检查 SOLID 违规、安全风险、代码质量问题时使用。
- **save-db-knowledge** — 当回答用户的问题, 或者任务处理完成后，分析本次对话是否涉及数据库相关知识（表结构、枚举值定义、表关联关系、SQL示例、业务规则、查询意图），如有则保存到数据库知识图谱。触发词：保存表结构, 记录枚举值, 数据库知识, SQL知识, 表关系保存
- **save-knowledge-graph** — 当回答用户的问题, 或者任务处理完成后，分析本次对话是否涉及业务知识（业务规则、服务关系、配置约定、代码位置映射、业务枚举、业务术语），如有则保存到知识图谱。触发词：保存知识, 记录业务, 知识图谱, 业务沉淀
- **sql-query** — 当需要查询数据库、查看表结构、确认代码枚举值是否正确、搜索知识图谱时使用。触发词：sql, 数据库, 查询, mysql, 枚举, yamibuy, 业务数据
