---
name: zentao-bug-reporter
description: 在禅道 Purchase 项目下创建 bug、查询 bug 列表、修改 bug、关闭 bug、删除 bug。当用户说"记bug"、"提bug"、"创建bug"、"记一个bug"、"帮我记bug"、"bug记录"、"查bug"、"查我的bug"、"我的bug"、"今天的bug"、"未解决的bug"、"修改bug"、"改bug"、"关闭bug"、"关掉bug"、"close bug"、"删除bug"、"删掉bug"，或描述某个功能异常并附带 OP 编号、平台时使用。
---

# 禅道 Bug 操作

通过 Python 脚本操作禅道 Purchase 项目（product_id=11）。

## 产品路由规则

根据 OP 号自动选择目标产品，无需手动指定：

| OP 号 | 目标产品 | product_id |
|-------|---------|-----------|
| OP-34696 | 加拿大仓 6.15 | 21 |
| OP-36037 | 加拿大仓 6.15 | 21 |
| OP-36840 | 加拿大仓 6.15 | 21 |
| OP-36993 | 加拿大仓 6.15 | 21 |
| OP-37140 | 加拿大仓 6.15 | 21 |
| 无 OP | Purchase | 11 |
| 其他有 OP | Purchase | 11 |

## 脚本位置

所有脚本位于 `scripts/` 目录下：
- `create_bug.py`  创建 bug
- `list_bugs.py`  查询 bug 列表
- `update_bug.py`  修改 bug
- `close_bug.py`  关闭 bug
- `delete_bug.py`  删除 bug
- `zentao_client.py`  API 客户端（被其他脚本引用）

## 环境变量

脚本需要以下环境变量（已在系统中配置）：
- `ZENTAO_BASE_URL`  禅道地址
- `ZENTAO_ACCOUNT`  禅道账号
- `ZENTAO_PASSWORD`  禅道密码

---

## 一、记 Bug

### 解析用户输入
| 字段 | 说明 | 默认值 |
|------|------|--------|
| `title` | bug 描述，不含标题前缀 | 必填 |
| `op_number` | OP 编号，如 `OP-3310` | **空（绝对不沿用上次，用户没说就不填）** |
| `platform` | 见平台映射表 | 沿用上次 |
| `assigned_to` | 禅道账号 | 沿用上次 |
| `image_paths` | 明文图片路径，逗号分隔 | 空 |

### ⚠️ 图片处理规则

当用户消息中包含图片（prompt 中有 base64 图片数据）时：

**截图中箭头的含义（重要，不要搞错）：**
> 截图中用箭头标注的内容，表示的是**正确的、期望的效果**，而不是 bug 本身。
> 即：箭头指向的是"应该长这样"，没有箭头的部分才是"实际出现问题的地方"。
> 在填写复现步骤的"期望结果"和"实际结果"时，必须按此逻辑判断。

**必须执行以下步骤：**
1. 用 `execute_bash` 将图片 base64 数据写入临时文件（每张图片一个文件）：
```bash
echo "<base64数据>" | python -c "import base64,sys; open('/tmp/bug_img_1.png','wb').write(base64.b64decode(sys.stdin.read().strip()))"
```
或者用 `fs_write` 工具先写一个包含 base64 的文本文件，再用 python 解码：
```bash
python -c "import base64; open('/tmp/bug_img_1.png','wb').write(base64.b64decode(open('/tmp/bug_img_1.b64').read()))"
```

2. 将所有图片路径用逗号拼接，传给 `--image_paths` 参数：
```bash
python scripts/create_bug.py --title "..." --steps "..." --assigned_to "..." --image_paths "/tmp/bug_img_1.png,/tmp/bug_img_2.png"
```

**简化方案（推荐）：** 如果图片已保存到 `{WORK_DIR}/sessions/{chatId}/images/` 目录，直接用 `--image_count N` 参数取最新 N 张图：
```bash
python scripts/create_bug.py --title "..." --steps "..." --assigned_to "..." --image_count 1
```

**禁止忽略用户发送的图片。** 只要 prompt 中有图片，就必须上传到 bug 中。

---

## ⚠️ 【强制规则】指派人映射

**用户说"指给 xxx"或"指派给 xxx"时，必须执行以下步骤：**

1. **必须查下方映射表**，根据用户输入的昵称找到对应的禅道账号
2. **禁止直接使用用户输入的昵称**作为 assigned_to 参数
3. **必须使用映射表中的"禅道账号"列的值**传给脚本

**示例：**
- 用户说"指给 todd"  查表得到禅道账号 `todd_zhu`  传 `--assigned_to todd_zhu`
- 用户说"指给 phoebe"  查表得到禅道账号 `Phoebe_Song`  传 `--assigned_to Phoebe_Song`
- 用户说"指给 alan"  查表得到禅道账号 `Alan_Li`  传 `--assigned_to Alan_Li`

**用户映射表（昵称  禅道账号）：**

| 企微账号 | 昵称 | 禅道账号 | 可作为创建人 |
|---------|------|----------|-------------|
| Alan.Li | alan | Alan_Li | ✓ |
| LiFengSheng | barry | LiFengSheng | |
| damon-LiTao | damon | damon-LiTao | |
| erin.lin | erin | erin_lin | ✓ |
| Gavin. | gavin | Gavin_ | |
| Hank_Zhao | hank | Hank_Zhao | |
| ZuoJiaXing | jaxson | ZuoJiaXing | |
| Kara_Han | kara | Kara_Han | |
| YangBoShen | logan | YangBoShen | |
| ZhaoXingPing | lucky | ZhaoXingPing | |
| WangPeng | miles | WangPeng | |
| Phoebe.Song | phoebe | Phoebe_Song | ✓ |
| renee.zhang | 我 | renee_zhang | ✓ |
| NanXiaoTong | stone | NanXiaoTong | |
| todd_zhu | todd | todd_zhu | |
| Tracy_Bai | tracy | Tracy_Bai | |
| Vanessa_Wang | vanessa | Vanessa_Wang | |
| WangXiaoYong | roger | WangXiaoYong | |
| ZhuTong | samuel | ZhuTong | |
| JiangShan | jessie | JiangShan | |
| ZhangTao | jeremy | ZhangTao | |

---

**创建人逻辑：**
- **每次调用 `create_bug.py` 时必须传 `--chat_id {当前chatId}`**（从上下文中的"当前会话 chatId"获取）
- 脚本内部会自动根据 chatId 确定 `opened_by`，无需 AI 手动查表
- 如果需要覆盖创建人，可以额外传 `--opened_by`（显式传入的优先级更高）
- 指派人（assigned_to）默认是私聊的这个用户的禅道账号

**默认值记忆：** 用户没说平台、指派人时，从记忆文件读取上次的值：

记忆文件路径：`sessions/{chatId}/last_bug_context.json`（`{chatId}` 取自上下文注入的"当前会话 chatId"，如 `dm_erin.lin`）

```json
{"op_number": "OP-3310", "platform": "app", "assigned_to": "renee_zhang", "opened_by": "erin_lin"}
```

- 每次记 bug 前：读取记忆文件，用户未提供的字段用记忆值填充
- 每次记 bug 后：将本次的 platform、assigned_to、opened_by、last_bug_id 写回记忆文件（**禁止写入 op_number，避免下次误用**）
- 记忆文件不存在时不报错，当作没有默认值处理（platform 兜底用 `app`，assigned_to 兜底用 `renee_zhang`，opened_by 按创建人逻辑推断）

> ⚠️ **【强制规则】OP 号绝对不沿用上次：**
> - 用户本次消息中**没有提到任何 OP 号**时，`op_number` 必须为空字符串 `""`，**禁止从记忆文件读取 op_number**
> - 记忆文件中的 `op_number` 字段在记 bug 时**完全忽略，不得使用**
> - 只有用户在本次消息中明确说了 OP 号（如"OP-3310"、"36037"），才传 `--op_number`
> - 违反此规则会导致 bug 记录到错误的产品下

**OP 号识别规则：**

用户可以只说数字，不用带 `OP-` 前缀：

| 用户输入示例 | 识别结果 |
|------------|---------|
| `OP-3310` | `OP-3310` |
| `3310` | `OP-3310` |
| `记bug 34242 xxx功能异常` | op_number=`OP-34242`，title=`xxx功能异常` |
| `记bug xxx功能异常` | op_number 沿用上次 |

识别规则：消息中"记bug"/"提bug"后面紧跟的纯数字（3位以上），视为 OP 号，自动补全为 `OP-{数字}`。用户说"无op"、"没有op"、"不带op"时，op_number 留空，不写 OP 前缀。

**平台映射：**

| 用户输入 | platform | title 处理 |
|---------|----------|-----------|
| `ios` | `app` | title 加前缀 `iOS `，如 `iOS 无法下单` |
| `android` | `app` | title 加前缀 `Android ` |
| `app`（未指定） | `app` | 不加前缀 |
| `H5` | `H5` | 不加前缀 |
| `PC` / `前端` | `PC` | 不加前缀 |
| `服务` / `后端` / `api` | `服务` | 不加前缀 |

**标题附加标签：**

用户说"线上bug"时，在整个标题最前面加 `【线上bug】`，位于 OP 号和平台前缀之前，例如：

| 用户输入 | 最终完整标题 |
|---------|-----------|
| `记线上bug，无op，api，购物车无法结算` | `【线上bug】【服务】购物车无法结算` |
| `线上bug，OP-3310，iOS 支付失败` | `【线上bug】【OP-3310】【app】iOS 支付失败` |

**steps 默认模板（用户未提供时）：**
```
复现步骤：
1. [根据 title 推断]

期望结果：[正常行为]
实际结果：[title 描述的异常]
```

### 调用脚本

```bash
python scripts/create_bug.py \
  --title "购物车页面点击结算按钮无响应" \
  --steps "复现步骤：\n1. 打开购物车\n2. 点击结算按钮\n\n期望结果：跳转到结算页\n实际结果：无响应" \
  --assigned_to "renee_zhang" \
  --op_number "OP-3310" \
  --platform "app" \
  --extra_prefix "线上bug" \
  --chat_id "dm_Phoebe.Song"
```

**参数说明：**
| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` | 是 | Bug 描述内容 |
| `--steps` | 是 | 复现步骤 |
| `--assigned_to` | 是 | 指派给谁（**必须是映射表中的禅道账号**） |
| `--op_number` | 否 | OP 编号 |
| `--platform` | 否 | 平台，默认 app |
| `--severity` | 否 | 严重程度，默认"一般" |
| `--priority` | 否 | 优先级，默认"中"，见下方映射表 |
| `--bug_type` | 否 | Bug 类型，默认"代码错误" |

**优先级映射（数字或中文都可以传）：**

| 用户输入 | --priority 参数值 | 禅道显示 |
|---------|-----------------|---------|
| 1 / 紧急 / P1 | 1 或 紧急 | 1 |
| 2 / 高 / P2 | 2 或 高 | 2 |
| 3 / 中 / P3（默认） | 3 或 中 | 3 |
| 4 / 低 / P4 | 4 或 低 | 4 |
| `--extra_prefix` | 否 | 额外标签，如"线上bug" |
| `--image_paths` | 否 | 图片路径，逗号分隔 |
| `--image_count` | 否 | 从企业微信取最新 N 张图 |
| `--chat_id` | 是 | 当前会话chatId，脚本自动确定创建人和图片目录 |
| `--opened_by` | 否 | 覆盖创建人禅道账号（一般不需要传，脚本自动处理） |

### 返回格式

```json
{
  "success": true,
  "bug_id": 7739,
  "title": "【OP-3310】【app】iOS 积分计算错误",
  "url": "https://bugs.yamibuy.tech/bug-view-7739.html",
  "message": "Bug #7739 创建成功，已指派给 renee_zhang",
  "images_count": 1
}
```

成功后回复用户：
```
Bug #7739 已创建 ✓
标题：【OP-3310】【app】iOS 积分计算错误
链接：https://bugs.yamibuy.tech/bug-view-7739.html
图片：1 张
```

⚠️ **【强制要求】回复时必须包含"链接"字段**，链接值来自脚本返回的 `url` 字段，禁止省略。

---

## 二、查询 Bug

### 查询指派给我的 bug

```bash
python scripts/list_bugs.py \
  --assigned_to "renee_zhang" \
  --status "all" \
  --assigned_date "2024-01-15"
```

**参数说明：**
| 参数 | 必填 | 说明 |
|------|------|------|
| `--assigned_to` | 是 | 禅道账号 |
| `--status` | 否 | active/resolved/closed/all，默认 all |
| `--limit` | 否 | 返回数量，默认 20 |
| `--assigned_date` | 否 | 按指派日期过滤 YYYY-MM-DD |

### 查询我创建的 bug

```bash
python scripts/list_bugs.py \
  --opened_by "renee_zhang" \
  --opened_date "2024-01-15"
```

**参数说明：**
| 参数 | 必填 | 说明 |
|------|------|------|
| `--opened_by` | 是 | 创建人禅道账号 |
| `--opened_date` | 否 | 按创建日期过滤 |
| `--opened_date_start` | 否 | 创建日期范围起始 |
| `--opened_date_end` | 否 | 创建日期范围结束 |
| `--status` | 否 | 状态过滤 |

**查询规则：**

- "查bug"、"查我的bug"、"今天的bug"：先用 `mcp_Time_get_current_time(timezone="Asia/Shanghai")` 获取今天日期，传 `--assigned_to --assigned_date=今天`
- "未解决的bug"：传 `--status=active`，不加日期过滤
- "今天我创建的bug"、"我今天提的bug"：用 `--opened_by --opened_date=今天`
- "本周创建的bug"：用 `--opened_by --opened_date_start=本周一 --opened_date_end=今天`

---

## 三、修改 Bug

```bash
python scripts/update_bug.py \
  --bug_id 7739 \
  --priority "高" \
  --assigned_to "HuangMingBo"
```

**参数说明：**
| 参数 | 必填 | 说明 |
|------|------|------|
| `--bug_id` | 是 | Bug ID |
| `--title` | 否 | 新的描述 |
| `--steps` | 否 | 新的复现步骤 |
| `--assigned_to` | 否 | 重新指派（**必须是映射表中的禅道账号**） |
| `--op_number` | 否 | 新的 OP 号 |
| `--platform` | 否 | 新的平台 |
| `--severity` | 否 | 新的严重程度 |
| `--priority` | 否 | 新的优先级 |
| `--bug_type` | 否 | 新的类型 |

只传需要修改的字段，未传的字段保持不变。

成功后回复：
```
Bug #7739 已更新 ✓
链接：https://bugs.yamibuy.tech/bug-view-7739.html
修改字段：pri, assignedTo
```

---

## 四、关闭 Bug

```bash
python scripts/close_bug.py --bug_id 7739 --comment "已修复"
```

**参数说明：**
| 参数 | 必填 | 说明 |
|------|------|------|
| `--bug_id` | 是 | Bug ID |
| `--comment` | 否 | 关闭备注 |

成功后回复：
```
Bug #7739 已关闭 ✓
链接：https://bugs.yamibuy.tech/bug-view-7739.html
```

---

## 五、删除 Bug

```bash
python scripts/delete_bug.py --bug_id 7739
```

用户说"删除bug"但**没有说 bug 号**时，从记忆文件读取 `last_bug_id`，删除上一个操作的 bug。

成功后回复：
```
Bug #7739 已删除 ✓
```

---

## 注意事项

1. 脚本输出为 JSON 格式，解析后向用户展示友好信息
2. 图片上传在 bug 创建后自动处理
3. 所有脚本依赖 `httpx` 库，首次使用需安装：`pip install httpx`
