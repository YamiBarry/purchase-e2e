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
| `tracking_spec_path` | string | 埋点方案路径（need_tracking=yes 时必填），如 `requirements/OP-XXXXX/tracking-spec.md` |

选填：`modules`、`files_new`、`files_modified`、`tools_reused`、`deploy_order`、`complexity`。

`outputs/phase-arch.md`：架构规范全文，需包含修改范围、复用的公共工具、类设计、DB 变更、配置变更、编码约束。

## 硬要求
## 前端项目识别（涉及前端需求时强制执行）

**Arch 阶段是 services 列表的最终决策者。** `params.repos` 和 PM 阶段的 services 仅作参考，Arch 必须自主验证。

### 强制执行步骤

1. **读取项目路由规则**：
   ```bash
   cat ~/.kiro/steering/ec-web-project-locator.md
   ```

2. **按功能域查表**，确定应涉及哪些仓库（不能只看 params.repos）

3. **逐仓库验证**，确认本地存在：
   ```bash
   ls /home/e2e/code/yami/ | grep ec-website
   ```

4. **输出完整 services 列表**，覆盖上游的不完整列表

### 功能域 → 仓库映射（常用）

| 功能域 | 必须包含的仓库 |
|--------|---------------|
| 登录/注册/联合登录 | ec-website-next, ec-website-nb, ec-website-customer-next, ec-website-customer-nb, ec-website-trade-nb（共 5 个） |
| 购物车/结算/支付 | ec-website-trade-nb |
| 订单/个人中心 | ec-website-customer-next, ec-website-customer-nb |
| 商品详情/首页/搜索 | ec-website-next |
| 分类/品牌/闪购 | ec-website-nb |

### ⛔ 禁止行为

- ❌ 直接沿用 `params.repos` 不做验证
- ❌ 只改需求方提到的仓库，不自主判断
- ❌ 登录类需求只涉及 3 个仓库（必须 5 个）


- `db_changes` 里的 DDL/DML，字段类型和 NOT NULL 约束必须用 `SHOW FULL COLUMNS` 核对过
- DML 的 `WHERE` 要能精确定位（生产库同一业务 key 可能按 `site_code` 等维度多行）
- 配置类变更如果目标 value 是整段内容，方案必须写明**增量修改**而非整段覆盖
- 有 DDL 时必须在 `deploy_order` 说明「DDL 先于代码部署」
- **前端需求必须 `git fetch --all` 核实每个涉及仓库的远程分支实际状态**，不能凭 params 描述推断，arch 文档里必须如实写出每个仓库的「已有分支 / 无分支」状态

## 路由

产出合法后完成本阶段 → `arch_review`。

## feat 分支新鲜度检查（强制）

发现已有 feat 分支时，**必须检查它与 master 的新鲜度**：

```bash
# 检查 feat 分支落后 master 多少 commits
git fetch origin
merge_base=$(git merge-base origin/master origin/feat/xxx)
behind_count=$(git rev-list --count $merge_base..origin/master)
echo "feat 分支落后 master: $behind_count commits"
```

**判定规则**：
- `behind_count ≤ 20`：feat 分支可用，在 `existing_branches` 标记 `(可复用,落后${behind_count}commits)`
- `behind_count > 20`：feat 分支**过时**，必须在 `existing_branches` 标记 `(过时,落后${behind_count}commits,需从master重建)`

**过时分支的处理**：
- arch 文档必须明确写出「feat 分支过时，code 阶段需从 origin/master 新建 OP 分支」
- 在 `existing_branches` 中标记 `branch_strategy: "rebuild_from_master"`
- 列出需要从旧 feat 分支 cherry-pick 的**具体文件路径**（只 pick 本需求相关的文件）

**禁止**：不检查新鲜度就复用 feat 分支

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

## 埋点方案设计（phase-pm.json 的 need_tracking=yes 时必须执行）

**arch 阶段负责完整的埋点技术方案，完成后必须同步回需求产物目录。**

### 前置检查（强制）

进入埋点设计前，**必须先检查 PM 阶段是否产出了业务层埋点需求**：

```bash
# 检查 tracking-spec.md 是否存在
ls ~/workspace/purchase/requirements/OP-XXXXX/tracking-spec.md
```

- **存在** → 读取内容，基于业务需求设计技术方案
- **不存在但 need_tracking=yes** → 必须 `pause` 并要求 PM 补充：
  ```bash
  python3 complete-phase.py "<instance-dir>" pause "需 PM 补充：requirements/OP-XXXXX/tracking-spec.md 不存在，无法设计埋点技术方案"
  ```

**禁止**：need_tracking=yes 但不检查 PM 产出就自己编造埋点需求

### 执行步骤

1. 读取 PM 产出的 `requirements/OP-XXXXX/tracking-spec.md`，了解业务层埋点需求（要哪些事件、参数）
2. 按 `tracking-spec` skill 执行埋点设计（查 Sheet → 设计事件名 → 新增 sheet 页）
3. **将完整技术埋点方案写回** `requirements/OP-XXXXX/tracking-spec.md`，覆盖 PM 的业务层版本

### 写回后的 tracking-spec.md 必须包含

- 每个事件的 `AnalyticsEventNameMap` 常量名
- Sensor/Yamidata 事件名（下划线格式）
- Ymb 事件名（点号格式）
- 触发时机和主要参数
- 埋点 Sheet 的 tab 名称（供 QA 验证时查阅）

### phase-arch.json 必须填写

```json
{
  "tracking_spec_path": "requirements/OP-XXXXX/tracking-spec.md",
  "tracking_sheet_url": "https://docs.google.com/spreadsheets/d/1R8.../edit#gid=123456789",
  "tracking_sheet_tab": "OP-XXXXX 需求简称",
  "tracking_events": [
    {"name": "EVENT_XX_IMPRESSION", "sensor_name": "xx_impression", "trigger": "组件展示"}
  ]
}
```

**⚠️ tracking_sheet_url 必须包含 #gid=**，这是调用 add_sheet_tab 后返回的完整 URL。

**禁止**：
- ❌ 只填 tracking_sheet_tab 名字但不调用 add_sheet_tab 获取 URL
- ❌ tracking_sheet_url 没有 #gid=（说明没有实际创建 tab）
- ❌ 只在架构文档里写埋点方案，不更新 requirements 目录
- ❌ need_tracking=yes 但 phase-arch.json 没有 tracking_spec_path
- ❌ 不在 Sheet 里新增 tab 就设计事件名


---

## 埋点技术方案（need_tracking=yes 时强制执行）

当上游 PM 标记 `need_tracking: yes` 时，**必须**完成以下步骤：

### 强制执行步骤

1. **读取埋点 Sheet 模板** - 调用 @google-workspace read_sheet
2. **读取历史参考** - 了解填写风格
3. **在 Sheet 新增 tab** - 调用 add_sheet_tab，获取 sheetId
4. **写入事件定义** - 调用 write_sheet
5. **拼接完整 URL** - `https://...#gid={sheetId}`

### 必填字段

| 字段 | 类型 | 验证规则 |
|------|------|---------|
| `tracking_spec_path` | string | 文件必须存在 |
| `tracking_sheet_url` | string | 必须包含 #gid= |
| `tracking_sheet_tab` | string | - |
| `tracking_events` | array | 每项必须有 name, sensor_name, trigger |

### 🚫 禁止行为

- ❌ **只填 tracking_sheet_tab 字符串但不调用 add_sheet_tab** → URL 验证失败
- ❌ **tracking_sheet_url 没有 #gid=** → 必须实际创建 tab 获取 gid
