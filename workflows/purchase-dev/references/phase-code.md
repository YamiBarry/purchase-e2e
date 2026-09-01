# Phase code

按架构方案实现代码，编译通过后 commit、推分支、建 PR。

本阶段在 `phase-pm.json` 的 `need_code == "no"` 时自动跳过。被 `code_review` 或 `qa` 打回时，逐条修 issue/failures，不要顺手改别的。

## 产出契约

`outputs/phase-code.json` 必填字段：

| 字段 | 类型 | 取值 / 说明 |
|---|---|---|
| `branches` | array | 每项含 `repo` `branch` `worktree` |
| `changed_files` | array | 变更文件路径 |
| `build_status` | string | `pass` / `skip`；worktree 无 node_modules 时用 `skip` + build_note 说明，不允许因此 block |
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

## worktree 创建规则（强制）

**创建 worktree 前必须检查 arch 产出的 `existing_branches` 字段**：

### 情况1：无已有分支 或 标记为 `rebuild_from_master`
```bash
# 从最新 master 创建干净分支
git fetch origin
git worktree add /home/e2e/code/yami/worktrees/${repo}--OP-XXXXX -b OP-XXXXX origin/master
```

### 情况2：有已有分支且标记为「可复用」（落后 ≤20 commits）
```bash
# 可以基于 feat 分支创建
git worktree add /home/e2e/code/yami/worktrees/${repo}--OP-XXXXX -b OP-XXXXX origin/feat/xxx
```

### 情况3：有已有分支但标记为「过时」（落后 >20 commits）
```bash
# 1. 必须从 master 创建干净分支
git fetch origin
git worktree add /home/e2e/code/yami/worktrees/${repo}--OP-XXXXX -b OP-XXXXX origin/master

# 2. 进入 worktree，从旧 feat 分支 cherry-pick 有效文件（按 arch 文档列出的文件路径）
cd /home/e2e/code/yami/worktrees/${repo}--OP-XXXXX
git checkout origin/feat/xxx -- src/features/本需求目录/
git checkout origin/feat/xxx -- path/to/other/relevant/file.ts
# 只 checkout 本需求相关的文件，不要 checkout 无关文件

# 3. 提交 cherry-pick 的文件
git add .
git commit -m "feat(OP-XXXXX): 从 feat/xxx 迁移本需求相关代码"

# 4. 继续开发新功能
```

**禁止**：
- ❌ 不检查 `existing_branches` 新鲜度标记就创建 worktree
- ❌ feat 分支过时时直接 `git worktree add ... -b OP-xxx origin/feat/xxx`
- ❌ cherry-pick 时 checkout 整个 feat 分支（会带入无关文件）

## ⚠️ 基于 feat 分支建 OP 分支时的特殊处理

如果 OP 分支是基于 `feat/xxx` 建的（而不是 master），`git diff origin/master HEAD` 会包含 feat 分支的全部改动，其中可能混有其他需求的文件。

**必须执行以下步骤确保分支干净：**

```bash
# 1. 从 master 重建干净的 OP 分支
git checkout origin/master -b OP-XXXXX-clean

# 2. 只 cherry-pick 本需求相关的文件（不是整个 commit）
git checkout feat/xxx -- src/features/本需求目录/
git checkout feat/xxx -- 本需求涉及的其他文件

# 3. 提交干净的改动
git add .
git commit -m "feat(OP-XXXXX): 本需求描述"

# 4. 替换原来的 OP 分支
git branch -D OP-XXXXX
git branch -m OP-XXXXX
git push origin OP-XXXXX --force
```

**判断文件是否属于本任务**：看文件路径是否与本需求功能模块相关，如果是 cms/search/other-feature 等明显无关的目录，直接排除。

**PR** — body 末尾必须有 `ai_coverage=X.X`。不要 push 到 master，不要 force push。

## 编译验证降级规则（worktree 环境）

**worktree 新建后无 node_modules 是已知限制，不允许因此 block。** 按以下顺序降级：

1. **有 node_modules** → 跑完整构建（`pnpm build` / `npx mix`），`build_status=pass`
2. **无 node_modules，Next.js** → 跑 `npx tsc --noEmit`（只需 TypeScript 编译器，无需全部依赖），或 `node --check` 语法验证，`build_status=skip`，build_note 说明
3. **无 node_modules，Laravel/JS** → 跑 `node --check` 对关键 JS 文件做语法验证，`build_status=skip`，build_note 说明
4. **任何情况下都不允许因「无法编译」而 block** — 代码写完就 commit + push，`build_status=skip` 推进，QA 阶段部署时会做真实构建验证

**block 的正确场景**：代码逻辑错误、语法错误（node --check 报错）、架构偏差。
**不能 block 的场景**：缺少 node_modules、缺少环境变量、网络问题。

## 需要人工裁定时用 pause，不用 block

遇到需要人工决策的情况（如：仓库实际状态与预期不符、分支策略需确认、工作量超出单次 phase 范围），**必须用 pause 而不是 block**：

```bash
python3 complete-phase.py "<instance-dir>" pause "需人工裁定：[具体问题描述和需要确认的选项]"
```

- `pause` = 等待人工 resume，**不触发重试机制**
- `block` = 系统认为遇到了无法自动恢复的错误，**会触发最多3次重试后放弃**

判断原则：
- 代码/逻辑问题 → `block`（可能下次重试能解决）
- 需要人工决策 → `pause`（重试没有意义，等人回答）

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


---

## 🔄 Loop-back 场景处理（从 code_review 或 qa 打回时）

**当你从 code_review 或 qa 阶段被 loop-back 回来时，必须按以下流程操作：**

### Step 1：读取上游打回的 issues

```bash
# 读取 code_review 的问题列表
cat outputs/phase-code_review.json | jq .issues

# 或读取 qa 的失败项
cat outputs/phase-qa.json | jq .failures
```

**必须逐条阅读问题**，理解每个 issue 的：
- `severity`：high 必须修，medium 应该修，low 可选
- `target`：问题出在哪个文件哪一行
- `problem`：具体问题描述
- `suggestion`：建议的修复方式

### Step 2：逐条修复问题

**只修复 issues 列出的问题，不要顺手改别的代码。**

每修复一个 issue，commit message 必须引用问题：
```bash
git commit -m "fix(OP-XXXXX): 修复 code_review issue#1 - 使用 axios 替代裸 XMLHttpRequest"
```

### Step 3：验证修复

```bash
# 编译检查
pnpm build 2>&1 | tail -20

# 确认所有 issues 都已修复
# 对照 phase-code_review.json 的 issues 列表逐条确认
```

### Step 4：推送并完成阶段（⚠️ 必须执行）

```bash
# 推送代码
git push

# ⚠️ 必须调用 complete-phase.py 推进流程
python3 ~/workspace/purchase/workflows/.scripts/complete-phase.py "<instance-dir>" code
```

### ⛔ 常见错误

- ❌ **只修代码不调 complete-phase.py** → 流程卡住，retry 耗尽后 blocked
- ❌ **不看 issues 就重新实现** → 可能重复犯同样的错误
- ❌ **顺手改不相关的代码** → 引入新问题，再次被打回
- ❌ **跳过 high severity 的 issue** → review 会再次打回

### Loop-back 的 phase-code.json 更新

loop-back 后的 `phase-code.json` 需要更新：
```json
{
  "loop_back_from": "code_review",
  "issues_fixed": ["issue#1: 使用 axios", "issue#2: 补全 token 处理"],
  "commits": [{"sha": "xxx", "message": "fix: ..."}],
  // ... 其他字段保持或更新
}
```
