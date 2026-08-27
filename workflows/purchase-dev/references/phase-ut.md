# Phase ut

给 coder 的实现补单元测试，跑通后提交到同一分支。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。

## 产出契约

`outputs/phase-ut.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `test_files` | array | 测试文件路径 |
| `test_status` | string | `pass` / `fail`；`fail` 不允许推进，先修 |
| `case_count` | number | 用例数 |
| `coverage_note` | string | 覆盖了哪些场景；项目既有的失败测试在此说明 |

选填：`commits`、`framework`。

`outputs/phase-ut.md`：测试说明。

## 硬要求

- 在 coder 用的**同一个 worktree、同一个分支**上工作，不要新开分支
- 测试框架跟项目走（Java=Spock+Groovy，Next.js=Vitest，Vue2 项目看它现有的 runner），不要引入新框架
- 发现实现 bug 时**不要改业务代码**，写进 `coverage_note` 让 code_review 处理
- 提交后推到远端

## 路由

产出合法后完成本阶段 → `code_review`。
