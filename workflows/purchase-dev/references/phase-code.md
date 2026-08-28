# Phase code

按架构方案实现代码，编译通过后 commit、推分支、建 PR。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。被 `code_review` 或 `qa` 打回时，逐条修 issue/failures，不要顺手改别的。

## 产出契约

`outputs/phase-code.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `branches` | array | 每项含 `repo` `branch` `worktree` |
| `changed_files` | array | 变更文件路径 |
| `build_status` | string | `pass` / `fail`；`fail` 不允许推进 |
| `pushed` | string | `yes` / `no`；`no` 时必须在 `build_note` 说明原因 |
| `pr_urls` | array | PR 链接；为空时必须在 `build_note` 说明原因 |

选填：`commits`（每项 `sha` `message`）、`build_note`。

`outputs/phase-code.md`：实现说明。

## 硬要求

**分支隔离** — 提交前用这两条命令确认每个文件都属于本任务，发现其他 OP 号的文件直接跳过不提交：

```bash
git log origin/master..HEAD --oneline      # 本分支新增的 commit
git diff --name-only origin/master HEAD    # 与 master 的文件差异
```

不要用不带 range 的 `git log` 判断 —— 它会列出已合并到 master 的祖先 commit，会误判分支不干净。

**PR** — body 末尾必须有 `ai_coverage=X.X`。不要 push 到 master，不要 force push。

## 路由

产出合法后完成本阶段 → `ut`。

## 埋点规范（强制）

**涉及埋点的需求，代码实现前必须：**

1. 查阅埋点定义 Sheet：`https://docs.google.com/spreadsheets/d/1R8tlpst84cTV7d327ogg7Hib3lNobfGYzv0pedKZkGE/`
2. 在 Sheet 里新增对应的 sheet 页（格式参考其他 sheet）
3. 代码里使用项目统一埋点方式（`analytics.track()` + `AnalyticsEventNameMap`），不自造格式

**严禁**：
- ❌ 绕过 `AnalyticsEventNameMap` 直接用字符串事件名
- ❌ 不查 Sheet 就自定义事件名格式
