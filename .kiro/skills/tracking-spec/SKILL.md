---
inclusion: auto
description: 当需要设计埋点方案、新增埋点事件、实现埋点代码时使用。触发词：埋点, tracking, 事件, event, analytics, 曝光, 点击, impression, click, 上报, AnalyticsEventNameMap
---

# Tracking Spec — 埋点设计与实现

## 触发判断

**只在需求明确涉及埋点时执行本 skill。** 判断标准：
- PRD 中有「埋点」「tracking」「上报」「曝光」「点击事件」等字样 → 执行
- 纯后端/配置变更、无用户交互的需求 → 跳过本 skill

---

## Arch 阶段：设计埋点定义

### Step 1：读取现有埋点 Sheet 了解格式

埋点定义 Sheet ID：`1R8tlpst84cTV7d327ogg7Hib3lNobfGYzv0pedKZkGE`

调用 `@google-sheets` 读取「埋点定义模板」sheet 了解列格式：
```
spreadsheetId: 1R8tlpst84cTV7d327ogg7Hib3lNobfGYzv0pedKZkGE
range: 埋点定义模板!A:Z
```

如果需要参考已有功能的实现，读取最近的 OP sheet（如 `OP-36986 CA站预热二期迭代 - US站推广增强`）作为格式参考。

### Step 2：设计新事件定义

按「埋点定义模板」的列格式，为本需求设计每个新事件。

**命名规范：**
- 格式：`{站点}_{功能模块}_{动作}`，全小写下划线
- 站点前缀：CA 站用 `ca_`，全站用无前缀或 `global_`
- 常见动作：`impression`（曝光）、`click`（点击）、`login_success`（登录成功）、`dismiss`（关闭）
- Sensor/Yamidata：下划线格式，如 `ca_google_onetap_impression`
- Ymb：将下划线替换为点号，如 `ca_google_onetap.impression`

**禁止：**
- ❌ 在需求文档中已有事件名定义时，自己改名
- ❌ Sensor/Yamidata 用点号、Ymb 用下划线（格式搞反）

### Step 3：在 Sheet 新增 sheet 页记录定义

调用 `@google-sheets` 的 `addSheet` 在 Sheet 里新增一个 tab，命名为 OP 号 + 需求名（如 `OP-38663 Google One Tap`），然后按「埋点定义模板」的列格式填写每个事件。

**操作方式：**
```
工具：addSheet（google-sheets MCP）
spreadsheetId: 1R8tlpst84cTV7d327ogg7Hib3lNobfGYzv0pedKZkGE
sheetTitle: OP-XXXXX 需求简称
```

然后调用 `writeSpreadsheet` 或 `appendRows` 按模板格式填写事件定义。

### Step 4：在架构文档里输出埋点方案

架构文档必须包含「埋点方案」章节，格式：

```markdown
## 埋点方案

Sheet 页：OP-XXXXX 需求简称（已在埋点 Sheet 新增）

| 事件常量 | Sensor/Yamidata 事件名 | Ymb 事件名 | 触发时机 | 主要参数 |
|---------|----------------------|-----------|---------|---------|
| EVENT_XX_IMPRESSION | xx_impression | xx.impression | 组件首次展示 | exposure_note |
| EVENT_XX_CLICK | xx_click | xx.click | 用户点击 | click_note |
```

---

## Code 阶段：实现埋点代码

**必须基于 arch 阶段输出的埋点方案实现，不允许自己发明或修改事件名。**

### ec-website-next / ec-website-customer-next（Next.js）

参考文件路径（先读懂再改）：
```
src/features/analytics/mapEventName.ts     # 事件名常量
src/features/analytics/dto.ts              # 事件类型定义
src/features/analytics/adapterYamidata.ts  # Yamidata 适配器（下划线格式）
src/features/analytics/adapterSensor.ts   # Sensor 适配器（下划线格式）
src/features/analytics/adapterYmb.ts      # Ymb 适配器（点号格式）
```

**实现步骤：**

**1. 在 `mapEventName.ts` 新增事件常量**
```typescript
export const AnalyticsEventNameMap = {
  // ... 已有事件
  /** 新事件描述 */
  EVENT_XX_IMPRESSION: 'EVENT_XX_IMPRESSION',
  EVENT_XX_CLICK: 'EVENT_XX_CLICK',
} as const;
```

**2. 在 `dto.ts` 新增事件类型**
```typescript
export type XxImpressionEventDTO = AnalyticsEventDTO<
  (typeof AnalyticsEventNameMap)['EVENT_XX_IMPRESSION'],
  { exposure_note: string }
>;
// 加到 WebEventDTO 联合类型
export type WebEventDTO = ... | XxImpressionEventDTO;
```

**3. 在各 Adapter 的 track 方法中添加 case**
```typescript
// adapterYamidata.ts 和 adapterSensor.ts（下划线）
case AnalyticsEventNameMap.EVENT_XX_IMPRESSION:
  this.yamidataCommonTrack('xx_impression', event.properties);
  break;

// adapterYmb.ts（点号）
case AnalyticsEventNameMap.EVENT_XX_IMPRESSION:
  this.track('xx.impression', event.properties);
  break;
```

**4. 在业务组件中调用**
```typescript
import { analytics, AnalyticsEventNameMap } from '@/features/analytics';

analytics.track({
  name: AnalyticsEventNameMap.EVENT_XX_IMPRESSION,
  memo: '页面描述-事件说明',   // 仅 Ymb 使用，其他 SDK 忽略
  properties: { exposure_note: 'xx_displayed' },
});
```

### Laravel 仓库（ec-website-nb / ec-website-trade-nb / ec-website-customer-nb）

先读取各仓库已有埋点文件确认格式，再按格式新增：

```bash
# 找到埋点相关文件
find ~/code/yami/{仓库名}/resources/assets/js -name "*track*" -o -name "enum.js" 2>/dev/null
```

通常结构：
- `enum.js`：定义事件名常量
- `common-track.js`：Sensor/Yamidata 事件处理
- `yamidata-track.js`：Yamidata 事件处理
- `mixpanel-track.js`：Ymb（Mixpanel）事件处理

**实现步骤：**
1. 在 `enum.js` 新增事件常量（参考已有格式）
2. 在 `common-track.js`/`yamidata-track.js` 新增事件监听和上报（下划线格式）
3. 在 `mixpanel-track.js` 新增事件监听和上报（点号格式）

---

## 边界说明

| 职责 | 谁做 |
|------|------|
| 判断需不需要埋点 | PM Agent（PRD 里明确） |
| 设计事件名和参数 | Architect Agent（arch 阶段） |
| 在 Sheet 新增定义 | Architect Agent（arch 阶段） |
| 写入代码 | Coder Agent（code 阶段） |
| 验证埋点是否上报 | QA Agent（qa 阶段，用 athena-tracking-query） |

---

## 禁止行为

- ❌ **禁止修改已有 sheet 页** — 每个需求必须新增独立 sheet 页，绝对不能修改其他 OP 的 sheet 或「埋点定义模板」，即使是修正错误也不行
- ❌ 不查 Sheet 就自己定义事件名
- ❌ 绕过 `AnalyticsEventNameMap`，在业务组件里直接写字符串事件名
- ❌ Sensor/Yamidata 用点号、Ymb 用下划线（格式搞反）
- ❌ arch 阶段不写埋点方案，把事件名设计扔给 coder 自己决定
- ❌ 新增 sheet 页前不看「埋点定义模板」列格式
- ❌ 需求不含埋点时也去执行本 skill（浪费时间）
