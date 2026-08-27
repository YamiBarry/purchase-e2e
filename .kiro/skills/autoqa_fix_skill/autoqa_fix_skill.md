# 自动化测试修复经验总结

## 一、分析报告流程

### 整批报告分析（机房跑完后）

**触发时机**：用户说「分析报告」并告知报告路径时执行。

**第一步：运行分析脚本**
```cmd
cd D:\workspace\yami-code-master\IntegrationTesting
venv\Scripts\python.exe D:\workspace\skills\autoqa_fix_skill\analyze_reports.py 报告路径.html
```
脚本自动完成：
- 提取所有 FAIL/ERROR 用例
- 从报告同目录的 `_files` 文件夹复制截图到 `D:\workspace\skills\autoqa_fix_skill\screenshots\`
- 输出用例列表和关键日志

**截图目录规律（重要）**：
报告路径去掉 `.html` 加 `_files` 即为截图目录，用户给报告路径时截图已经在本地：
```
ios1.html      →  ios1_files/
android1.html  →  android1_files/
```
脚本会自动从 `_files` 目录复制截图，**不需要下载**。

**第二步：读截图（按策略）**

脚本为每个失败用例复制最后3张截图（`test_xxx_last3.jpg`、`test_xxx_last2.jpg`、`test_xxx_last1.jpg`），命名规则：数字越大越靠后，`last1` 是最后一张。

**读截图策略：**
- **默认只读最后1张**（`last1`）— 失败时的页面状态，通常足够定位问题
- **需要时追加读 last2、last3** — 以下情况需要往前看：
  - 错误是 `Session does not exist`（最后一张可能是崩溃后空白页）
  - 最后一张看起来是正常页面，看不出失败原因
  - 需要了解失败前的操作路径

**不读所有截图**：一个用例可能有几十张截图，全读效率极低，按需读取。

**第三步：补充关键日志**
从 html 报告里 grep 具体的错误信息，补全截图看不出来的细节：
```cmd
# 在报告里搜索错误信息
grep 关键词 报告.html
```

**第四步：归类分析**
结合截图 + 日志，按根因归类：

| 根因分类 | 典型表现 |
|---------|---------|
| 账号数据污染 | 地址/信用卡残留，页面流程不符合预期 |
| Session 崩溃连锁失败 | `Session does not exist` + `KeyError: 'language'` |
| 元素找不到 | xpath 错误 / 键盘遮挡 / content-desc 精确匹配失败 |
| NoneType 错误 | `'NoneType' object has no attribute 'get_attribute'` |
| 断言失败 | 业务逻辑验证不通过 |
| 业务逻辑问题 | 页面 UI 变化、账号状态不满足前提条件 |

**第五步：输出修复列表**
格式：
```
【分类名】(N 个)
| 用例 | 错误信息 | 截图现象 | 根因 |
不主动修复，等用户确认后再动手
```

### 分析注意事项
- 截图是用例最后一张，反映失败时的页面状态，结合日志里最后一个 ERROR Action 定位根因
- Session 崩溃类的错误（`Session does not exist`）通常是设备/Appium 问题，不是代码 bug，重跑可能通过
- `KeyError: 'language'` 今天已修复（改为 `.get()`），这类错误重跑验证即可
- 报告里截图是本地相对路径（`./ios1_files/xxx.webp`），需要 `ios1_files` 文件夹在同目录

### 分类原则
需要修复类（按根因分类）：

| 根因 | 典型用例 |
|------|---------|
| 元素 xpath 错误 | 所有用 resource-id/content-desc 定位的元素 |
| 元素未找到（页面状态问题）| add_address、edit_address、delete_address |
| 键盘遮挡元素 | 所有表单页面的保存/删除按钮 |
| 文案/断言失效 | 登录流程的文案断言 |
| DB 查询问题 | verify_order_sn、verify_order_info |
| 账号数据污染 | 需要干净账号的用例 |

---

## 二、Flutter APP 元素定位规则（核心经验）

### Android 元素属性规律
| 情况 | content-desc | resource-id | text |
|------|-------------|------------|------|
| 有 autoqa id 的 View | `id + 额外文字`（如 `order_reorder_btn 再来一单`） | 纯 id | 空 |
| EditText 输入框 | 空 | 纯 id | 输入的文字 |
| 联想列表项 | `id + 地址内容` | 纯 id | 空 |

**结论：Android 用 `@resource-id` 定位，不用 `@content-desc` 精确匹配**

```python
# 错误写法（content-desc 包含额外文字，精确匹配失败）
AndroidXpath: "(//*[@content-desc='order_reorder_btn'])[{}]"

# 正确写法（resource-id 是纯 id，精确匹配有效）
AndroidXpath: "(//*[@resource-id='order_reorder_btn'])[{}]"
```

**适用范围**：所有 `AccessId` 为空、只配了 `AndroidXpath` 的元素，xpath 里一律用 `@resource-id` 而不是 `@content-desc`。

**iOS 不受影响**：iOS 的 `IOSXpath` 用 `@name`，`@name` 是纯 id，精确匹配有效，不需要改。

### iOS 元素属性规律
- `@name` 对应 Flutter 的 autoqa id，是纯 id，精确匹配有效
- iOS 的 `@name` 不会包含额外文字

### 验证方法
**需要确认元素属性时，让用户手动操作到目标页面，然后给以下命令 dump XML：**
```cmd
D:\platform-tools\platform-tools-latest-windows\platform-tools\adb.exe shell uiautomator dump /sdcard/ui.xml && D:\platform-tools\platform-tools-latest-windows\platform-tools\adb.exe pull /sdcard/ui.xml C:\Users\17564\Desktop\ui.xml
```
然后让用户把 ui.xml 内容复制给你，在 XML 里搜索目标元素，看真实的 `resource-id`、`content-desc`、`text`。

---

## 三、Flutter APP 键盘处理规则（核心经验）

### 各种关闭键盘方式的效果

| 方式 | 效果 |
|------|------|
| `driver.hide_keyboard()` | 对 Flutter EditText **无效** |
| `press_keycode(111)` ESC | 会**关闭 Flutter 弹窗**，不能用于表单页面 |
| `press_keycode(4)` Back | 会**退出页面**，不能用 |
| 点击键盘"完成"按钮 | **有效且安全**，收起键盘不关闭弹窗 |
| 点击页面标题区域 | 有效，但要确认坐标不在弹窗外 |

**结论：Android Flutter 表单页面，用点击"完成"按钮收起键盘**
```python
done_btn = driver.find_element('xpath', '//*[@content-desc="完成" or @content-desc="Done"]')
done_btn.click()
```

### 键盘遮挡规律
- Flutter 表单弹窗高度被键盘压缩，键盘弹出时底部按钮（保存、删除）**不在 DOM 里**
- 必须先收起键盘，底部按钮才会出现在 DOM 中
- 判断方法：dump XML，如果找不到预期按钮，先收起键盘再 dump

---

## 四、Flutter EditText 输入规则

| 方式 | 效果 |
|------|------|
| `element.clear()` | 可能无效，清空后会失焦 |
| `element.send_keys(text)` | 追加内容（不清空原有内容） |
| `send_keys_to_element(element, text, clear=True)` | 用退格键清空后输入，但 ActionChains 可能不触发 onChange |
| `element.click()` + `element.send_keys(text)` | 追加，不清空 |

**结论：追加内容能验证"编辑"功能即可，完整替换较复杂，不必强求**

---

## 五、页面流程确认规则

修复用例前，**先手动跑一遍，在每个关键节点 dump XML**：
1. 执行完上一步后，当前停在哪个页面
2. 目标元素的 `resource-id` 是什么
3. 目标按钮是否在可视区域（有没有被键盘遮挡）

**绝对不能靠猜测推断页面状态，必须用 XML 确认。**

---

## 六、修复工作流

```
1. 运行报告分析脚本，提取失败用例列表
2. 分类（忽略/需修复）
3. 更新 failed_cases 目录（python copy_failed_cases.py）
4. 对每个需要修复的用例：
   a. 手动操作 APP 到失败位置
   b. dump XML 确认元素属性
   c. 修改代码（优先 resource-id 定位）
   d. 本地运行验证（venv\Scripts\python.exe test\mob\failed_cases\test_xxx.py）
   e. 通过后 commit & push
5. 通知测试机 git pull，重跑全部 failed_cases
```

---

## 七、常见错误模式及修复

### 错误1：找不到联想地址
```
元素未找到: data_qa_item_suggestion_{}
```
**根因**：用 `@content-desc` 精确匹配，但值包含地址文字
**修复**：改用 `@resource-id='data_qa_item_suggestion_{}'`

### 错误2：找不到保存/删除按钮
```
未找到保存按钮 address_edit_save_btn
未找到删除按钮 address_edit_delete_btn
```
**根因**：键盘遮挡，按钮不在 DOM 里
**修复**：先点击"完成"按钮收起键盘

### 错误3：ESC 关闭弹窗
```
# 进入编辑页后立刻返回
```
**根因**：`_dismiss_keyboard` 用了 `press_keycode(111)` (ESC)
**修复**：只在 delete/save 操作前用"完成"按钮，不在表单输入过程中用

### 错误4：NoneType 直接 click
```
click_element: 传入的元素为 None，无法点击
```
**根因**：find_element 返回 None 没有判断
**修复**：加 None 判断 + 明确异常信息

### 错误5：订单号查不到
```
UnboundLocalError: order_status_db
```
**根因**：变量未初始化，25次重试全部失败后引用未赋值变量
**修复**：循环前初始化变量为 None

---

## 八、工具命令速查

```bash
# 查看连接设备
adb devices

# dump 当前页面 XML（让用户手动操作到目标页面后执行）
D:\platform-tools\platform-tools-latest-windows\platform-tools\adb.exe shell uiautomator dump /sdcard/ui.xml && D:\platform-tools\platform-tools-latest-windows\platform-tools\adb.exe pull /sdcard/ui.xml C:\Users\17564\Desktop\ui.xml

# 启动 Appium Server（本地调试用）
set ANDROID_HOME=D:\platform-tools\platform-tools-latest-windows\platform-tools
appium -p 4733

# 本地运行单个用例
cd D:\workspace\yami-code-master\IntegrationTesting
set env=prd && set platform=android && set language=zh
set PATH=%PATH%;D:\platform-tools\platform-tools-latest-windows\platform-tools
venv\Scripts\python.exe test\mob\failed_cases\test_account_address.py

# 分析报告
python D:\workspace\temp\analyze_new3.py

# 更新失败用例目录
python copy_failed_cases.py
```


---

## 九、读取本地测试报告

### 两种场景区分

| 场景 | 触发词 | 报告位置 | 用途 |
|------|--------|---------|------|
| **单条验证** | 用户说「跑完了」「看下报告」 | `D:\workspace\yami-code-master\IntegrationTesting\reports\report.html` | 判断单条用例修复是否通过 |
| **整批分析** | 用户说「分析报告」并给出报告路径 | 用户指定路径（如 `D:\workspace\skills\autoqa_fix_skill\reports\ios1.html`） | 分析机房跑完的整批报告，输出修复列表 |

---

### 场景一：单条用例验证（用户说「跑完了」）

**第一步：运行脚本**
```cmd
cd D:\workspace\yami-code-master\IntegrationTesting
venv\Scripts\python.exe D:\workspace\skills\autoqa_fix_skill\read_report.py
```
脚本自动下载每个用例最后一张截图到 `D:\workspace\skills\autoqa_fix_skill\screenshots\`

**第二步：读截图**
用 Image 工具读取截图文件：
```
D:\workspace\skills\autoqa_fix_skill\screenshots\test_xxx_last.jpg
```

**第三步：给结论**
- 全部通过 → 告知用户通过，继续下一个任务
- 有失败/错误 → 结合日志+截图定位根因，修复代码，给验证命令

---

### 场景二：整批报告分析（用户说「分析报告」并给路径）

见第一章「整批报告分析」流程。



---

## 十、修复完成后的标准验证流程

每次修复完成后，给用户以下命令让其在本地 venv 环境验证：

```cmd
cd D:\workspace\yami-code-master\IntegrationTesting
venv\Scripts\python.exe test\mob\mob_1_ready\test_xxx.py
```

将 `test_xxx.py` 替换为对应的用例文件名。

---

## 十一、跳过用例的标准方式（参数文件清空法）

当某个用例在特定平台/语言下需要跳过时，**不改代码，只改参数文件**。

**原理**：`get_case_parameters` 返回空时，用例内部调用 `self.skipTest(...)` 自动跳过。

**操作**：在对应的 `parameters_xxx.json` 里将该用例的参数清空为 `{}`：

```json
"account_coupon": {},
```

**参数文件路径**：
```
D:\workspace\yami-code-master\IntegrationTesting\test\parameters\
├── parameters_android_zh.json   # Android 中文
├── parameters_android_en.json   # Android 英文
├── parameters_ios_zh.json       # iOS 中文
├── parameters_ios_en.json       # iOS 英文
```

**参数 key 命名规则**：类名转小写+下划线，例如：
- `AccountCoupon` → `account_coupon`
- `CheckoutWithoutAddressAndCreditCard` → `checkout_without_address_and_credit_card`

---

## 十二、测试账号污染问题及解决方案

**问题**：部分用例（如结算页添加地址/信用卡）使用固定账号，当用例中途失败时，地址/信用卡数据未被清理，下次运行时账号已有残留数据，导致页面流程与预期不符（如不弹出添加地址弹窗）。

**解决方案**：改用每次注册新账号模式。

**操作**：在参数文件的 `step_1` 里设置 `is_create_account: "True"`，清空 email，密码固定 `111111`：

```json
"step_1": {
  "email": "",
  "password": "111111",
  "is_create_account": "True",
  "use_device_account": "False",
  "target_tab": "home"
}
```

**原理**：`is_create_account=True` 时，框架调用 `get_email()` 自动生成随机邮箱注册新账号，每次都是干净账号，参数文件里的 email/password 不会被使用。

**适用场景**：需要无地址、无信用卡、无购物车等「干净状态」的用例。

---

## 十三、mob_app_info KeyError 防御性修复

**问题**：当 UiAutomator2 崩溃时，`get_uer_information_by_gpt()` 元素定位和 GPT 截图均失败，`mob_app_info` 字典中 `language` 等 key 未被写入，后续代码直接用 `[]` 取值时抛 `KeyError`。

**修复原则**：`mob_app_info` 的所有读取操作一律改用 `.get()` 而非 `[]`：

```python
# 错误写法
if self.case.mob_app_info["language"] != language:

# 正确写法
if self.case.mob_app_info.get("language") != language:
```

**涉及文件**：`ec_ui/mob/page/account_page.py`

**注意**：`.get()` 返回 `None` 时，`None != language` 为 True，会触发 `change_language`，属于合理兜底行为。

---

## 十四、参数来源优先级（避免踩坑）

**两套参数的区别**：

| 场景 | 参数来源 |
|------|---------|
| 直接运行用例文件 `python test_xxx.py` | 用例文件底部 `__main__` 里的 `params` |
| 通过 `case_normal.py` 批量运行 | `test/parameters/parameters_xxx.json` |

**坑**：用例文件 `__main__` 里的 email/password 和参数文件里的不一致时，本地调试通过，批量跑失败。

**排查方法**：看日志里 `login_from_account` 的传参，确认实际用的是哪个账号：
```
Action: login_from_account 开始执行, 传入参数:({'email': 'xxx@xxx.com', ...})
```

**结论**：修复参数配置问题时，以 `parameters_xxx.json` 为准，`__main__` 里的 params 只是本地调试用，不影响正式跑。

---

## 十五、测试设备映射表

设备信息定义在 `ec_ui/mob/device_map/device_mapping.py`，通过 udid 查找设备型号时参考此表。

### iOS 设备

| 设备名称 | 型号 | udid |
|---------|------|------|
| 14pro | iPhone 14 Pro | 00008120-00163D510AE0A01E |
| 14promax | iPhone 14 Pro Max | 00008120-001A18421E38201E |
| 15pro | iPhone 15 Pro | 00008130-00162DD00189001C |
| 16 | iPhone 16 | 00008140-001240A9116B001C |
| 16plus | iPhone 16 Plus | 00008140-000509111A30801C |
| 13pro | iPhone 13 Pro | 00008110-00084D880CC2801E |
| 15plus | iPhone 15 Plus | 00008120-0000783C22E2601E |
| 15 | iPhone 15 | 00008120-001661083A43A01E |
| 16pro | iPhone 16 Pro | 00008140-000E65413A08801C |
| 15promax | iPhone 15 Pro Max | 00008130-001211CA0AC3001C |
| xsmax | iPhone XS Max | 00008020-00182C693E3B002E |

### Android 设备

| 设备名称 | 型号 | udid |
|---------|------|------|
| samsung_fold | 三星折叠手机 | R5CT82LKF4Z |
| oneplus_13 | 一加13 | 224f08ce |
| xiaomi_10 | 小米10 | 4d4602b |
| google_phone | 谷歌手机 | 37252EFJG003LB |
| samsung_non_fold | 三星非折叠手机 | RFCXA0SNCGP |

### 设备配对（device_1 ~ device_5 是主要使用的配对组）

| 配对 | iOS 型号 | iOS udid | Android 型号 | Android udid |
|------|---------|----------|-------------|-------------|
| device_1 | 14pro | 00008120-00163D510AE0A01E | samsung_fold | R5CT82LKF4Z |
| device_2 | 14promax | 00008120-001A18421E38201E | oneplus_13 | 224f08ce |
| device_3 | 15pro | 00008130-00162DD00189001C | xiaomi_10 | 4d4602b |
| device_4 | 16 | 00008140-001240A9116B001C | google_phone | 37252EFJG003LB |
| device_5 | 16plus | 00008140-000509111A30801C | samsung_non_fold | RFCXA0SNCGP |
