---
inclusion: auto
description: 当需要设计埋点方案、新增埋点事件、实现埋点代码时使用。触发词：埋点, tracking, 事件, event, analytics, 曝光, 点击, impression, click, 上报, AnalyticsEventNameMap
---

# Tracking Spec — 埋点设计与实现

## 触发场景

需求涉及埋点时（arch 阶段设计 + code 阶段实现），必须按本 skill 执行。

---

## Arch 阶段：设计埋点定义

### Step 1：读取现有埋点 Sheet 了解格式

埋点定义 Sheet：`1R8tlpst84cTV7d327ogg7Hib3lNobfGYzv0pedKZkGE`

调用 `@google-workspace` 读取一个已有 sheet 作为格式参考（如 `event_login_social` 所在的 sheet）：
```
spreadsheetId: 1R8tlpst84cTV7d327ogg7Hib3lNobfGYzv0pedKZkGE
range: {已有Sheet名}!A:Z
```

记录字段格式（通常包含：事件名、触发时机、触发页面、参数列表、平台覆盖等）。

### Step 2：设计新事件定义（对照已有格式）

按已有 sheet 格式，为本需求设计每个新事件：

| 字段 | 说明 |
|------|------|
| 事件名（Sensor/Yamidata） | 下划线格式，如 `ca_google_onetap_impression` |
| 事件名（Ymb） | 点号格式，如 `ca_google_onetap.impression` |
| 触发时机 | 什么操作/场景触发 |
| 触发页面/功能 | 在哪个页面 |
| 参数 | 事件携带的 properties |
| 平台 | Sensor / Yamidata / Ymb / 全部 |

**命名规范**：
- 格式：`{站点}_{功能模块}_{动作}`，全小写下划线
- 示例：`ca_google_onetap_impression`（曝光）、`ca_google_onetap_click`（点击）
- Sensor/Yamidata 用下划线，Ymb 用点号（下划线替换为点）

### Step 3：在 Sheet 新增 sheet 页记录定义

调用 `@google-workspace` 在 Sheet 里新增一个 sheet 页，命名为需求 OP 号（如 `OP-38663`），按现有格式填写每个事件的定义。

### Step 4：在架构文档里输出埋点方案

架构文档中必须包含「埋点方案」章节：
```markdown
## 埋点方案

| 事件常量 | Sensor/Yamidata 事件名 | Ymb 事件名 | 触发时机 | 参数 |
|---------|----------------------|-----------|---------|------|
| EVENT_XX_IMPRESSION | xx_impression | xx.impression | 组件展示时 | exposure_note |
| EVENT_XX_CLICK | xx_click | xx.click | 用户点击时 | click_note |
```

---

## Code 阶段：实现埋点代码

**必须基于 arch 阶段的埋点方案实现，不允许自己发明事件名。**

### ec-website-next（Next.js）

#### 参考文件
```
src/features/analytics/mapEventName.ts   # 事件名常量
src/features/analytics/dto.ts            # 事件类型定义
src/features/analytics/adapterYamidata.ts  # Yamidata 适配器
src/features/analytics/adapterSensor.ts (如有)
src/features/analytics/adapterYmb.ts (如有)
```

#### 实现步骤

1. **在 `mapEventName.ts` 新增事件常量**
```typescript
export const AnalyticsEventNameMap = {
  // 已有事件...
  /** 新事件描述 */
  EVENT_XX_IMPRESSION: EVENT_XX_IMPRESSION,
  EVENT_XX_CLICK: EVENT_XX_CLICK,
} as const;
```

2. **在 `dto.ts` 新增事件类型**
```typescript
export type XxImpressionEventDTO = AnalyticsEventDTO<
  (typeof AnalyticsEventNameMap)[EVENT_XX_IMPRESSION],
  { exposure_note: string }
>;
export type WebEventDTO = ... | XxImpressionEventDTO; // 加到联合类型
```

3. **在各 Adapter 的 track 方法中添加 case**
```typescript
// adapterYamidata.ts / adapterSensor.ts — 下划线格式
case AnalyticsEventNameMap.EVENT_XX_IMPRESSION:
  this.track(xx_impression, event.properties);
  break;

// adapterYmb.ts — 点号格式
case AnalyticsEventNameMap.EVENT_XX_IMPRESSION:
  this.track(xx.impression, event.properties);
  break;
```

4. **在业务组件中调用**
```typescript
import { analytics, AnalyticsEventNameMap } from @/features/analytics;

analytics.track({
  name: AnalyticsEventNameMap.EVENT_XX_IMPRESSION,
  memo: 页面描述-事件说明,
  properties: { exposure_note: xx_displayed },
});
```

### Laravel 仓库（ec-website-nb / ec-website-trade-nb / ec-website-customer-nb）

参考各仓库已有埋点文件（通常在 `resources/assets/js/` 下的 `*-track.js` 或 `enum.js`），格式参考已有实现。

---

## 禁止行为

- ❌ 不查 Sheet 就自己定义事件名
- ❌ 绕过 `AnalyticsEventNameMap`，直接用字符串事件名
- ❌ Sensor/Yamidata 用点号、Ymb 用下划线（格式搞反）
- ❌ arch 阶段不写埋点方案，把埋点设计扔给 coder
- ❌ 新增 sheet 页前不看已有格式
