# AGENTS

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively.

How to use skills:
- Invoke: `yami-ai-cli read <skill-name>` (run in your shell)
  - For multiple: `yami-ai-cli read skill-one,skill-two`
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

<skill>
<name>api-test</name>
<description>对 Yamibuy 微服务进行 HTTP 接口测试。支持 UAT、DEV、GQC 多环境切换，自动携带 token 和 headers。当用户需要测试接口、验证 API 返回、调试服务时使用。</description>
</skill>

<skill>
<name>athena-tracking-query</name>
<description>当需要查询亚米埋点数据、查看用户行为事件、验证埋点是否正确上报时使用。触发词：埋点, tracking, 事件, event, visitor_id, athena, 行为数据, 埋点验证, 星辰埋点, sensors_device_id, dwd_track_log, device_id, uv_signal, 用户行为, 页面停留, page_duration, navigation, 神策, sa.gif, sensorsdatacollect, base64</description>
</skill>

<skill>
<name>autoqa-build-feature-knowledge</name>
<description>当需要分析功能需求、建设功能知识库、沉淀业务知识文档、理解功能上下文和依赖关系时使用。</description>
</skill>

<skill>
<name>autoqa-code-helper</name>
<description>当需要基于测试用例文档和操作录制文档生成自动化测试脚本、创建 Selenium action 和 case、自动化测试代码生成时使用。</description>
</skill>

<skill>
<name>autoqa-fix-failed-test</name>
<description>当需要分析自动化测试报告、修复失败用例、定位测试脚本错误、排查测试失败原因时使用。</description>
</skill>

<skill>
<name>autoqa-flutter-qa-attributes-tagger</name>
<description>当需要为 Flutter 代码添加 autoQaId 测试属性、识别按钮文本和可点击元素、方便自动化测试定位元素时使用。</description>
</skill>

<skill>
<name>autoqa-generate-appium-scripts</name>
<description>当 App 端验证全部通过、需要基于录制文档生成 Appium 自动化测试脚本、执行验证并提交 PR 时使用。</description>
</skill>

<skill>
<name>autoqa-generate-playwright-scripts</name>
<description>当验证全部通过、需要基于技术录制文档（JSON）生成 Playwright 自动化测试脚本、执行验证并提交 PR 时使用。</description>
</skill>

<skill>
<name>autoqa-generate-testcase-doc</name>
<description>当需要基于知识库文档生成结构化测试用例、设计测试用例、写入 Google Sheet 时使用。</description>
</skill>

<skill>
<name>autoqa-pipeline</name>
<description>当需要执行自动化测试全流程（知识建设→测试用例→探索式验证→脚本生成）时使用。</description>
</skill>

<skill>
<name>autoqa-react-qa-attributes-tagger</name>
<description>当需要为 React 代码添加 data-qa-* 测试属性、识别按钮文本和可点击元素、方便自动化测试定位元素时使用。</description>
</skill>

<skill>
<name>autoqa-verify-and-record-testcase</name>
<description>当测试用例已确认、需要通过浏览器验证功能并录制操作路径、生成增强版技术录制文档时使用。</description>
</skill>

<skill>
<name>autoqa-verify-and-record-testcase-mob</name>
<description>当测试用例已确认、需要通过 Appium MCP 在真机上探索式验证 App 功能并录制操作路径时使用。</description>
</skill>

<skill>
<name>cdn-upload</name>
<description>cdn-upload</description>
</skill>

<skill>
<name>code-branch-diff</name>
<description>当需要对比分支代码差异、查看代码变更、分析提交记录、生成 diff 报告时使用。触发词：diff, 代码对比, 分支差异, git diff, 代码变更</description>
</skill>

<skill>
<name>code-module-analyzer</name>
<description>当需要分析代码模块、理解代码结构、追踪调用链、生成代码文档时使用。触发词：这段代码, 帮我看看, 分析一下, 这个模块, 什么意思, 怎么实现的, 代码分析</description>
</skill>

<skill>
<name>code-simplifier</name>
<description>当需要简化代码、重构代码、优化代码结构、提升代码可读性、清理冗余代码时使用。触发词：simplify, refactor, clean code, 代码简化, 重构, 代码优化</description>
</skill>

<skill>
<name>control-browser</name>
<description>当需要使用浏览器、操作网页、验证前端效果、截图测试时使用。触发词：浏览器, 打开网页, 截图, 页面验证, playwright, chrome</description>
</skill>

<skill>
<name>deep-research-agent</name>
<description>当需要进行深度研究、生成研究报告、文献调研、信息综合、系统性分析某个主题时使用。触发词：research, 深度研究, 报告生成, 研究项目, 文献调研</description>
</skill>

<skill>
<name>deploy-idp-service</name>
<description>当需要部署服务到 IDP 环境、查看部署状态、排查部署失败、查询可部署服务列表、查看构建日志时使用。</description>
</skill>

<skill>
<name>figma-plugin-architect</name>
<description>开发 Figma 插件时使用。生成 manifest.json、code.ts、ui.html 标准架构代码，包含 Variables API、双线程通信、类型安全最佳实践。</description>
</skill>

<skill>
<name>find-skills</name>
<description>Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.</description>
</skill>

<skill>
<name>sql-query</name>
<description>当需要查询数据库、查看表结构、确认代码枚举值是否正确、搜索知识图谱时使用。触发词：sql, 数据库, 查询, mysql, 枚举, yamibuy, 业务数据</description>
</skill>

<skill>
<name>zentao-bug-reporter</name>
<description>在禅道创建 bug、查询 bug 列表、修改 bug、关闭 bug、删除 bug。当用户说"记bug"、"提bug"、"创建bug"、"查bug"、"查我的bug"、"修改bug"、"关闭bug"、"删除bug"，或描述功能异常并附带 OP 编号时使用。</description>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>

---

# AutoQA Memory 协议

所有 autoqa 相关流程执行时，必须遵循以下 Memory 读写协议，实现经验的自动积累和复用。

## Memory 文档信息

- 存储位置：Outline Auto-QA 集合
- 文档标题：`AutoQA Memory`
- 文档 ID：`35e04abe-c0cf-47fd-92f5-2e7ec96985f4`
- 本地缓存路径：`.kiro/autoqa-memory.md`
- Fallback：如果按 ID 读取失败，通过 `outline_search_documents` 按标题 "AutoQA Memory" 搜索

## 流程开始时

1. 通过 Outline MCP 读取 "AutoQA Memory" 文档（ID: `b38fdcf1-c109-4203-a1bd-d22af7164793`）
2. 将内容保存到本地 `.kiro/autoqa-memory.md`
3. 参考其中的经验规则指导当前工作

## 执行过程中

遇到以下情况时，更新本地 `.kiro/autoqa-memory.md`：
- 发现了一个通用性强的技巧或解决方案
- 踩了一个坑，且该坑可能在其他场景重现
- 找到了比现有规则更好的做法（更新已有规则）

**不记录的内容：**
- 特定于某个页面/功能的临时问题
- 一次性的环境问题（如某次网络超时）
- 已经在 skill 正文中明确说明的规则

## 流程结束时

1. 重新读取 Outline "AutoQA Memory" 文档的最新内容
2. 对比本地版本与线上版本，识别差异：
   - 线上有而本地没有的 → 保留（别人新增的）
   - 本地有而线上没有的 → 新增（自己的经验）
   - 两边都有但表述不同 → 合并为更完善的版本
3. 去重：含义相同的规则只保留一条
4. 将合并后的完整内容写回 Outline（覆盖更新）

> **并发安全说明**：本协议采用最终一致性设计。极端情况下两个 Agent 同时写回可能导致后者覆盖前者的新增内容，但丢失的经验会在后续执行中被重新发现并补充。这是可接受的 trade-off，无需引入锁机制。

> **冲突兜底**：写回前如果检测到线上版本与流程开始时下载的版本不同（说明有人在此期间更新过），且合并后发现本地新增的规则无法确认是否与线上新增的重复，将本次未成功合并的内容追加到本地 `.kiro/autoqa-memory-pending.md`，下次流程开始时优先检查此文件并尝试合并。

## 记录格式

每条规则遵循以下格式：

```markdown
- [分类标签] 具体可执行的规则描述
```

分类标签包括：
- `[等待策略]` — 页面加载、元素等待相关
- `[环境配置]` — 环境差异、超时设置相关
- `[元素定位]` — 选择器、定位策略相关
- `[数据准备]` — 测试数据、前置条件相关
- `[脚本结构]` — 代码组织、设计模式相关
- `[调试技巧]` — 排错、日志、截图相关
- `[其他]` — 不属于以上分类的通用经验

---

# 通用禁止行为清单

以下行为严格禁止，适用于所有项目类型（前端、后端、全栈），任何情况下都不得违反。

---

## 工作流程
1. **禁止在 master/main 分支直接修改代码** — 必须创建 OP，拿到 OP 号创建分支再提交
2. **禁止使用 MCP、shell 直接读取或编辑代码** — 必须通过 `switch-workspace` 技能动态加载项目到工作区
3. **禁止通过 MCP 读取代码** — 必须通过 readCode 工具分析读取代码，无法读取请确认项目已加入工作区
4. **禁止本地生成脚本文件执行命令** — 直接运行命令
5. **禁止任务完成后输出总结性文档** — 除非用户明确要求
6. **禁止在 main-agent 处理复杂且与主任务相干性不大的子任务** — 使用 sub-agent 处理

## 安全
> **例外**：造数据工具（data-factory）操作的是测试环境，其输出的 token/密码/用户信息必须完整展示给用户，不受以下规则限制。所有用户均可使用造数据工具的全部功能。

7. **禁止在代码、配置、日志中暴露密钥/密码** — 敏感信息必须脱敏处理，使用环境变量或密钥管理服务
8. **禁止硬编码魔法数字/字符串** — 必须定义为命名常量或枚举
9. **禁止信任用户输入** — 所有外部输入必须校验、转义或参数化，防止注入攻击（SQL/XSS/命令注入）
10. **禁止在客户端存储敏感数据** — 不得将密码、密钥存入 localStorage/sessionStorage/Cookie（httpOnly 除外）
11. **禁止使用已知不安全的加密算法** — 不得使用 MD5/SHA1 做密码哈希，使用 bcrypt/scrypt/Argon2；对称加密使用 AES-256-GCM，禁用 DES/3DES/ECB 模式
12. **禁止在 URL 或查询参数中传递敏感信息** — Token/密码/身份信息必须通过请求头或请求体传递，URL 会被日志和浏览器历史记录
13. **禁止关闭 CORS 限制或设置 Access-Control-Allow-Origin: \*** — 生产环境必须配置白名单域名
14. **禁止在错误响应中暴露系统内部信息** — 堆栈、文件路径、数据库结构等不得返回给客户端，统一返回业务错误码
15. **禁止使用 eval/exec/Function 构造器执行动态代码** — 防止代码注入，使用安全的替代方案
16. **禁止不设置请求超时** — 所有 HTTP 请求、数据库连接、外部服务调用必须设置合理超时，防止资源耗尽
17. **禁止在日志中记录完整的请求/响应体** — 只记录关键字段，脱敏处理手机号、身份证、银行卡等 PII 数据


## 代码质量
18. **禁止空 catch 块吞掉异常** — 必须记录日志或向上抛出，不得静默忽略
19. **禁止提交 console.log/print 调试代码** — 提交前清理所有调试输出，使用正式日志框架
20. **禁止注释掉代码后提交** — 无用代码直接删除，Git 有历史记录
21. **禁止复制粘贴超过 10 行的重复代码** — 必须抽取为公共方法/组件/工具函数
22. **禁止单个函数/方法超过 120 行** — 拆分为职责单一的小函数
23. **禁止单个文件超过 800 行** — 按职责拆分模块
24. **禁止忽略编译器/Lint 警告** — 警告即隐患，必须修复或有明确理由标注 suppress

## Git 规范
25. **禁止提交包含冲突标记的文件** — `<<<<<<<`、`=======`、`>>>>>>>` 必须解决后再提交
26. **禁止将 node_modules/dist/build/.env 等产物提交到仓库** — 必须在 .gitignore 中排除
27. **禁止单次 commit 包含不相关的多个变更** — 一个 commit 只做一件事

---

# 我是谁
1. 我是`主人`，我的角色是开发者

# 全局规则
1. 必须全程使用中文进行表述和回复，确保信息传递的准确性和一致性。
2. 生成Github提交信息，使用中文生成。
3. 在执行系统命令行操作时，根据当前操作系统选择终端：Windows 使用 PowerShell，macOS/Linux 使用 bash
4. 如果要获取当前时间，请一定使用shell脚本获取当前时间
5. 数据库时间字段设计请使用时间戳，单位秒
6. 快速了解项目的方式：阅读每个文件夹下，或者每个git项目下的README.md文件
7. 如果当前是git项目每个小任务结束，创建一个git commit提交
8. 所有生成的临时文件，都放在当前工作区根目录的docs目录下

---

## Skill 资源路径定位规则

当 `discloseContext` 返回 SKILL.md 正文后，如果正文中引用了 `scripts/`、`references/`、`examples/`、`assets/` 等相对路径资源，按以下规则定位实际文件。

### 定位步骤

已知 skill 名称为 `<name>`（即 `discloseContext` 的 `name` 参数），Skill 根目录按优先级查找：

1. `<workspace>/.kiro/skills/<name>/` — 工作区级别，优先使用
2. `~/.kiro/skills/<name>/` — 用户全局级别，工作区不存在时使用

找到存在的目录后，该目录即为 Skill 根目录，所有相对路径基于此目录解析。

### 路径模板

| 资源类型 | 相对路径 | 完整路径示例 (Windows) |
|----------|----------|----------------------|
| 参考文档 | `references/xxx.md` | `<skill-root>\references\xxx.md` |
| 脚本 | `scripts/xxx.py` | `<skill-root>\scripts\xxx.py` |
| 示例 | `examples/xxx.java` | `<skill-root>\examples\xxx.java` |
| 资产 | `assets/template.xlsx` | `<skill-root>\assets\template.xlsx` |

### 执行脚本时

```powershell
# <skill-root> = 找到的 Skill 根目录
python "<skill-root>\scripts\xxx.py" <args>
```

---

# 代理（Sub-Agent）使用选择指南

根据任务类型选择合适的代理，避免在主代理中处理复杂且相干性低的子任务：

| 代理名称 | 适用场景 | 何时使用 |
|---------|---------|---------|
| `context-gatherer` | 代码探索、文件定位、调用链梳理 | 不熟悉代码库时，先用它收集上下文，再动手改代码。每次会话最多调用一次 |
| `code-analyzer` | 模块架构分析、调用链追踪、SQL 链路映射 | 需要理解某个模块的完整架构和依赖关系时，指定模块路径即可自动生成文档 |
| `issue-investigator` | 线上问题排查、错误日志追踪、异常数据分析 | 排查线上问题时，描述现象（错误信息、订单号、服务名），自动执行排查流程 |
| `release-doc-generator` | 发布文档生成、多仓库代码变更扫描 | 准备上线文档、查看多仓库变更时使用 |
| `test-case-generator` | 前端测试用例生成 | 为前端功能生成浏览器测试计划时使用 |

选择原则：
1. 优先使用专用代理（如 `code-analyzer`、`issue-investigator`），而非通用代理
2. 复杂且与主任务相干性低的子任务，委派给 sub-agent 处理，不要阻塞主流程
3. `context-gatherer` 是探索未知代码的首选，但收集完上下文后应回到主代理继续工作
