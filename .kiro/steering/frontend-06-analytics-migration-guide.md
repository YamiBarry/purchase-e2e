---
inclusion: agent-requested
---

# 埋点迁移模板（按需加载）

> 本文件仅在执行埋点迁移任务时加载。架构师只需知道：使用适配器模式，事件注册在 `mapEventName.ts`，三平台（Sensor/Yamidata/Ymb）同步上报。

## 背景

需要将 Laravel 项目中的埋点事件迁移到 Next.js 项目中。两个项目使用不同的埋点架构：

- **Laravel**: 使用 PubSub 模式 + 全局方法
- **Next.js**: 使用统一的 analytics 管理器 + 适配器模式

## 埋点平台说明

项目中有三个埋点平台，需要同时迁移：

1. **Sensor (神策)**: 事件名格式为 `event_xxx_xxx` (下划线分隔)
2. **Yamidata (星辰)**: 事件名格式为 `event_xxx_xxx` (下划线分隔)
3. **Ymb (亚米)**: 事件名格式为 `event_xxx.xxx` (点号分隔)，需要额外的 `memo` 参数

## Laravel 项目埋点模式识别

### 1. Sensor 和 Yamidata 埋点

通过 PubSub 发送：

```javascript
// 发送事件
PubSub.publish(PUBSUB_TRACK.EVENT_XXX, params);

// 监听和处理在以下文件：
// - common-track.js (Sensor)
// - yamidata-track.js (Yamidata)
```

### 2. Ymb 埋点

有三种方式：

**方式一：全局方法 (最常见)**

```javascript
onMixpanelTrack('事件描述', 'event_xxx.xxx', parametersArray);
```

**方式二：PubSub 方式 (少量)**

```javascript
PubSub.publish(PUBSUB_TRACK.EVENT_XXX, params);
// 在 mixpanel-track.js 中监听处理
```

**方式三：Blade 模板内联 (需特别注意)**

```html
<button onclick="onMixpanelTrack('描述', 'event_xxx.xxx', [...])"></button>
```

### 3. 参数格式差异

- **Sensor/Yamidata**: 对象格式 `{ key: value }`
- **Ymb**: 数组格式 `[{ name: 'key', value: 'value' }]`

## Next.js 项目埋点架构

### 1. 事件定义流程

```typescript
// Step 1: 在 mapEventName.ts 添加事件常量
export const AnalyticsEventNameMap = {
  EVENT_XXX: 'EVENT_XXX',
} as const;

// Step 2: 在 dto.ts 定义事件类型
export type XxxEventDTO = AnalyticsEventDTO<
  typeof AnalyticsEventNameMap['EVENT_XXX'],
  string, // memo (仅 Ymb 使用)
  {
    // 事件参数 (包含所有平台需要的字段)
    param1: string;
    param2?: number;
  }
>;

// Step 3: 添加到联合类型
export type WebEventDTO = ... | XxxEventDTO;
```

### 2. 适配器处理

每个适配器的 `track()` 方法中添加 case 分支：

```typescript
// adapterSensor.ts
track(event: WebEventDTO): void {
  switch (event.name) {
    case AnalyticsEventNameMap.EVENT_XXX:
      this.commonTrack('event_xxx_xxx', event.properties);
      break;
  }
}

// adapterYamidata.ts (类似)
// adapterYmb.ts (注意使用 memo 参数)
```

### 3. 业务代码调用

```typescript
import { useAnalytics, AnalyticsEventNameMap } from '@/features/analytics';

const { track } = useAnalytics();

track({
  name: AnalyticsEventNameMap.EVENT_XXX,
  memo: '事件描述', // 仅 Ymb 需要
  properties: {
    param1: 'value1',
    param2: 123,
  },
});
```

## 迁移步骤

### 第一步：分析 Laravel 代码并确定实际上报事件

**⚠️ 重要：不要被 PubSub 常量名称误导！**

在 Laravel 业务代码中查找所有埋点调用：

1. 搜索 `PubSub.publish(PUBSUB_TRACK.EVENT_XXX`
2. 搜索 `onMixpanelTrack(`
3. 检查 Blade 模板中的内联埋点
4. 在 `enum.js` 中找到事件常量定义
5. **【关键步骤】在 `common-track.js`、`yamidata-track.js`、`mixpanel-track.js` 中找到事件处理逻辑，确定实际上报的事件名称**

记录以下信息：

- **实际上报的事件名称**（三个平台可能不同）- 以 track 文件中实际调用的事件名为准
- 事件参数（合并所有平台的参数）
- 触发时机和条件
- memo 描述（Ymb 专用）

#### 🔍 事件映射识别规则

**Laravel 项目中，PubSub 常量名称 ≠ 实际上报的事件名称！**

必须查看 track 文件中的监听处理逻辑，找到实际调用的事件名：

**示例 1：EVENT_CLICK_FEEDBACK → event_click**

```javascript
// 业务代码中
PubSub.publish(PUBSUB_TRACK.EVENT_CLICK_FEEDBACK, params);

// common-track.js 中
PubSub.subscribe(PUBSUB_TRACK.EVENT_CLICK_FEEDBACK, function (msg, data) {
  sensors.track('event_click', data); // ← 实际上报的是 event_click
});

// yamidata-track.js 中
PubSub.subscribe(PUBSUB_TRACK.EVENT_CLICK_FEEDBACK, function (msg, data) {
  yamidata.track('event_click', data); // ← 实际上报的是 event_click
});

// mixpanel-track.js 中
PubSub.subscribe(PUBSUB_TRACK.EVENT_CLICK_FEEDBACK, function (msg, data) {
  mixpanel.track('event_click', data); // ← 实际上报的是 event_click (注意 Ymb 是点号)
});
```

**结论**：虽然 PubSub 常量是 `EVENT_CLICK_FEEDBACK`，但实际上报的事件是 `event_click`，因此在 Next.js 中应该使用已有的 `EVENT_CLICK` 事件，而不是创建新的 `EVENT_CLICK_FEEDBACK`。

**示例 2：EVENT_SEARCH_RESULT → event_search_result / event_search.result**

```javascript
// 业务代码中
PubSub.publish(PUBSUB_TRACK.EVENT_SEARCH_RESULT, params);

// common-track.js 中
PubSub.subscribe(PUBSUB_TRACK.EVENT_SEARCH_RESULT, function (msg, data) {
  sensors.track('event_search_result', data); // ← Sensor 上报 event_search_result
});

// mixpanel-track.js 中
PubSub.subscribe(PUBSUB_TRACK.EVENT_SEARCH_RESULT, function (msg, data) {
  mixpanel.track('event_search.result', data); // ← Ymb 上报 event_search.result (点号)
});
```

**结论**：实际上报的事件名称是 `event_search_result` 和 `event_search.result`，这才是需要在 Next.js 中定义的事件。

### 第二步：检查 Next.js 中是否已存在该事件

**⚠️ 在创建新事件之前，必须先检查是否已存在相同的事件！**

#### 检查步骤：

1. **在 `mapEventName.ts` 中搜索事件常量**
   - 搜索实际上报的事件名称（如 `event_click`）
   - 查看是否已有对应的常量（如 `EVENT_CLICK`）

2. **在三个适配器中搜索事件名称**
   - 在 `adapterSensor.ts` 中搜索 `'event_xxx_xxx'`
   - 在 `adapterYamidata.ts` 中搜索 `'event_xxx_xxx'`
   - 在 `adapterYmb.ts` 中搜索 `'event_xxx.xxx'`

3. **在 `dto.ts` 中查看事件类型定义**
   - 查看已有事件的参数定义
   - 确认是否需要添加新参数

#### 决策规则：

**情况 A：事件已存在，参数完全匹配**

- ✅ 直接复用已有事件
- ✅ 在业务代码中调用已有的事件常量
- ❌ 不要创建新的事件常量
- ❌ 不要修改 DTO 和适配器

**情况 B：事件已存在，但需要新增参数**

- ✅ 复用已有事件常量
- ✅ 在 DTO 中添加新的可选参数
- ✅ 在注释中说明新参数的来源
- ❌ 不要创建新的事件常量
- ❌ 不要修改适配器（除非需要参数适配）

**情况 C：事件不存在**

- ✅ 创建新的事件常量
- ✅ 定义新的事件类型
- ✅ 在三个适配器中添加处理逻辑

#### 示例：复用已有事件

```typescript
// ❌ 错误做法：创建新事件
export const AnalyticsEventNameMap = {
  EVENT_CLICK: 'EVENT_CLICK',
  EVENT_CLICK_FEEDBACK: 'EVENT_CLICK_FEEDBACK', // ← 错误！实际上报的是 event_click
};

// ✅ 正确做法：复用已有事件
export const AnalyticsEventNameMap = {
  EVENT_CLICK: 'EVENT_CLICK', // ← 正确！复用已有事件
};

// 在 DTO 中添加新参数（如果需要）
export type ClickEventDTO = AnalyticsEventDTO<
  (typeof AnalyticsEventNameMap)['EVENT_CLICK'],
  string,
  {
    // 原有参数
    module_name: string;
    content: string;

    // 新增参数（来自 EVENT_CLICK_FEEDBACK 场景）
    feedback_type?: string; // 反馈类型
    feedback_value?: string; // 反馈值

    [key: string]: any;
  }
>;
```

### 第三步：在 Next.js 中定义或更新事件

#### 情况 A & B：复用已有事件（推荐）

如果事件已存在，只需要在业务代码中调用，或者在 DTO 中添加新参数：

```typescript
// 1. 不需要修改 mapEventName.ts（事件常量已存在）

// 2. 如果需要新参数，更新 dto.ts
/**
 * XXX事件参数
 *
 * 参考老PC：
 * - 神策埋点: common-track.js EVENT_XXX → event_xxx_xxx
 * - 星辰埋点: yamidata-track.js EVENT_XXX → event_xxx_xxx
 * - 亚米埋点: mixpanel-track.js EVENT_XXX → event_xxx.xxx
 * - 【新增】神策埋点: common-track.js EVENT_XXX_NEW → event_xxx_xxx (复用同一事件)
 */
export type XxxEventDTO = AnalyticsEventDTO<
  (typeof AnalyticsEventNameMap)['EVENT_XXX'],
  string, // memo
  {
    // 原有参数
    existing_param: string;

    // 新增参数（标注来源）
    new_param?: string; // 来自 EVENT_XXX_NEW 场景

    // 支持其他参数
    [key: string]: any;
  }
>;

// 3. 不需要修改适配器（已有处理逻辑）
```

#### 情况 C：创建新事件（仅当事件不存在时）

**⚠️ 只有在确认事件完全不存在时才执行以下步骤！**

##### 1. 添加事件常量 (mapEventName.ts)

```typescript
export const AnalyticsEventNameMap = {
  // 使用语义化的常量名，基于实际上报的事件名
  EVENT_XXX: 'EVENT_XXX', // 对应 event_xxx_xxx / event_xxx.xxx
} as const;
```

##### 2. 定义事件类型 (dto.ts)

```typescript
/**
 * XXX事件参数
 *
 * 参考老PC：
 * - 神策埋点: common-track.js EVENT_XXX → event_xxx_xxx
 * - 星辰埋点: yamidata-track.js EVENT_XXX → event_xxx_xxx
 * - 亚米埋点: mixpanel-track.js EVENT_XXX → event_xxx.xxx
 */
export type XxxEventDTO = AnalyticsEventDTO<
  typeof AnalyticsEventNameMap['EVENT_XXX'],
  string, // memo
  {
    // 必填参数
    required_param: string;

    // 可选参数
    optional_param?: number;

    // 支持其他参数
    [key: string]: any;
  }
>;

// 添加到联合类型
export type WebEventDTO =
  | ...
  | XxxEventDTO;
```

### 第四步：实现适配器逻辑（仅情况 C）

**⚠️ 如果复用已有事件（情况 A & B），跳过此步骤！**

#### 1. Sensor 适配器 (adapterSensor.ts)

```typescript
track(event: WebEventDTO): void {
  switch (event.name) {
    case AnalyticsEventNameMap.EVENT_XXX:
      // 如果需要参数适配，调用 adaptXxxParams
      const adaptedParams = this.adaptXxxParams(event.properties);
      this.commonTrack('event_xxx_xxx', adaptedParams);
      break;
  }
}

// 如果需要参数适配
private adaptXxxParams(params: any): any {
  return {
    // 映射和转换参数
    sensor_param: params.common_param,
  };
}
```

#### 2. Yamidata 适配器 (adapterYamidata.ts)

```typescript
track(event: WebEventDTO): void {
  switch (event.name) {
    case AnalyticsEventNameMap.EVENT_XXX:
      const adaptedParams = this.adaptXxxParams(event.properties);
      this.commonTrack('event_xxx_xxx', adaptedParams);
      break;
  }
}
```

#### 3. Ymb 适配器 (adapterYmb.ts)

```typescript
track(event: WebEventDTO & { memo: string }): void {
  switch (event.name) {
    case AnalyticsEventNameMap.EVENT_XXX:
      const adaptedParams = this.adaptXxxParams(event.properties);
      this.commonTrack(
        event.memo || '默认描述',
        'event_xxx.xxx', // 注意点号分隔
        adaptedParams
      );
      break;
  }
}
```

### 第五步：在业务代码中调用

在 Next.js 组件中：

```typescript
import { useAnalytics, AnalyticsEventNameMap } from '@/features/analytics';

const { track } = useAnalytics();

// 在合适的时机调用
const handleXxx = () => {
  track({
    name: AnalyticsEventNameMap.EVENT_XXX, // 使用已有的或新创建的事件常量
    memo: '事件描述', // 参考老PC的 onMixpanelTrack 第一个参数
    properties: {
      required_param: 'value',
      optional_param: 123,
    },
  });
};
```

## 注意事项

### 0. 事件复用原则（最重要）

**⚠️ 必须以实际上报的事件名为准，而不是 PubSub 常量名！**

- **错误示例**：看到 `EVENT_CLICK_FEEDBACK` 就创建新事件
- **正确做法**：查看 track 文件，发现实际上报的是 `event_click`，复用 `EVENT_CLICK`

**迁移前必须做的检查**：

1. 在 track 文件中找到实际上报的事件名（`sensors.track('event_xxx', ...)`）
2. 在 Next.js 的三个适配器中搜索该事件名
3. 如果找到，复用已有事件；如果没找到，才创建新事件

### 1. 事件名称映射

- **Sensor/Yamidata**: `event_xxx_xxx` (下划线)
- **Ymb**: `event_xxx.xxx` (点号)

### 2. 参数格式

- DTO 中使用对象格式 `{ key: value }`
- Ymb 适配器内部会自动转换为数组格式

### 3. memo 参数

- 仅 Ymb 使用
- 从老PC的 `onMixpanelTrack` 第一个参数获取

### 4. 参数适配

- 如果三个平台参数完全一致，直接传递
- 如果有差异，在各适配器中实现 `adaptXxxParams` 方法

### 5. 数据清洗

- 适配器的 `commonTrack` 方法会自动处理空值、类型转换等
- 无需在业务代码中手动清洗

### 6. Blade 模板埋点

- 如果在 Blade 中发现内联埋点，需要迁移到 React 组件的事件处理函数中

## 验证清单

### 第一步：事件识别（必须完成）

- [ ] 已在 track 文件中找到实际上报的事件名（不是 PubSub 常量名）
- [ ] 已在 Next.js 三个适配器中搜索该事件名，确认是否已存在
- [ ] 已确定是复用已有事件还是创建新事件

### 第二步：事件定义（根据情况选择）

**如果复用已有事件（情况 A & B）：**

- [ ] 已确认使用正确的事件常量（不创建新常量）
- [ ] 如需新参数，已在 DTO 中添加可选参数并标注来源
- [ ] 未修改适配器（除非需要参数适配）

**如果创建新事件（情况 C）：**

- [ ] 事件常量已添加到 `mapEventName.ts`
- [ ] 事件类型已定义在 `dto.ts` 并添加到 `WebEventDTO`
- [ ] 三个适配器都已实现事件处理逻辑

### 第三步：业务代码（所有情况）

- [ ] 业务代码中正确调用 `track()` 方法
- [ ] 参数包含所有平台需要的字段
- [ ] Ymb 的 `memo` 参数已正确设置
- [ ] 事件名称映射正确（下划线 vs 点号）
- [ ] 已检查 Blade 模板中的内联埋点

## 迁移示例：event_search_result

### Laravel 代码分析

**Sensor 埋点**:

```javascript
PubSub.publish(PUBSUB_TRACK.EVENT_SEARCH_RESULT, sensor_track_parameters);
```

**Ymb 埋点**:

```javascript
onMixpanelTrack(
  '搜索结果页各条件搜索',
  'event_search.result',
  this.objectToArray(sensor_track_parameters)
);
```

**参数结构**:

```javascript
sensor_track_parameters = {
  keyword: this.keywords,
  condition: this.getSortName(this.selectedSortOptionId),
  bu_type: getQueryParam(window.location.href, 'bu_type') || 'search',
  module_name: getQueryParam(window.location.href, 'module_name'),
  content: getQueryParam(window.location.href, 'content') || this.keywords,
  primary_condition: 'page', // 或 "sort"
  primary_condition_value: index, // 或 sortName
  action_type: 'add',
  result_number: this.page.total,
  source_flag: 'item_detail', // 可选
  index: _index, // 可选
  items: items, // 前3个商品的 item_number 数组
};
```

### Next.js 实现

#### 1. 定义事件类型 (dto.ts)

```typescript
/**
 * 搜索结果页事件参数
 *
 * 参考老PC：
 * - 神策埋点: search/index.js EVENT_SEARCH_RESULT → event_search_result
 * - 星辰埋点: search/index.js EVENT_SEARCH_RESULT → event_search_result
 * - 亚米埋点: search/index.js onMixpanelTrack("搜索结果页各条件搜索", "event_search.result")
 */
export type SearchResultEventDTO = AnalyticsEventDTO<
  (typeof AnalyticsEventNameMap)['EVENT_SEARCH_RESULT'],
  string,
  {
    // 必填参数
    keyword: string; // 搜索关键词
    condition: string; // 排序条件名称
    result_number: number; // 搜索结果数量
    bu_type: string; // 业务类型

    // 可选参数
    module_name?: string; // 模块名称
    content?: string; // 内容（通常与keyword相同）
    primary_condition?: string; // 主要筛选条件类型 (page/sort/category/brand等)
    primary_condition_value?: string | number; // 主要筛选条件值
    action_type?: string; // 操作类型 (add/clear等)
    source_flag?: string; // 来源标识
    index?: string | number; // 索引
    items?: string[]; // 前3个商品的item_number数组
    [key: string]: any; // 支持其他可选参数
  }
>;
```

#### 2. 适配器实现

**Sensor 适配器**:

```typescript
case AnalyticsEventNameMap.EVENT_SEARCH_RESULT:
  this.commonTrack('event_search_result', event.properties);
  break;
```

**Yamidata 适配器**:

```typescript
case AnalyticsEventNameMap.EVENT_SEARCH_RESULT:
  this.commonTrack('event_search_result', event.properties);
  break;
```

**Ymb 适配器**:

```typescript
case AnalyticsEventNameMap.EVENT_SEARCH_RESULT:
  this.commonTrack(
    event.memo || '搜索结果页各条件搜索',
    'event_search.result',
    event.properties
  );
  break;
```

#### 3. 业务代码调用

```typescript
// 辅助函数：获取排序名称
const getSortName = useCallback((sortId: string) => {
  const sortNameMap: Record<string, string> = {
    '0': 'newest',
    '1': 'most_reviews',
    '2': 'popularity',
    '3': 'most_relevant',
    '40': 'price_high_to_low',
    '41': 'price_low_to_high',
    '5': 'most_ratings',
    '6': 'best_seller',
    '7': 'newest',
  };
  return sortNameMap[sortId] || 'most_relevant';
}, []);

// 场景1：分页变化时
const handlePageChange = useCallback(
  async (page: number) => {
    // ... 其他逻辑

    track({
      name: AnalyticsEventNameMap.EVENT_SEARCH_RESULT,
      memo: '搜索结果页各条件搜索',
      properties: {
        keyword: keywords,
        condition: getSortName(getCurrentSortId()),
        bu_type: String(searchQueryParams.bu_type || 'search'),
        module_name: searchQueryParams.module_name,
        content: String(searchQueryParams.content || keywords),
        primary_condition: 'page',
        primary_condition_value: page,
        action_type: 'add',
        result_number: totalCount,
        source_flag: searchQueryParams.source_flag,
        index: searchQueryParams.index,
        items: items.slice(0, 3).map((item) => item.item_number),
      },
    });
  },
  [
    /* 依赖项 */
  ]
);

// 场景2：排序变化时
const handleSort = useCallback(
  async (sortValue: string) => {
    // ... 其他逻辑

    track({
      name: AnalyticsEventNameMap.EVENT_SEARCH_RESULT,
      memo: '搜索结果页各条件搜索',
      properties: {
        keyword: keywords,
        condition: getSortName(sortValue),
        bu_type: String(searchQueryParams.bu_type || 'search'),
        module_name: searchQueryParams.module_name,
        content: String(searchQueryParams.content || keywords),
        primary_condition: 'sort',
        primary_condition_value: getSortName(sortValue),
        action_type: 'add',
        result_number: totalCount,
        source_flag: searchQueryParams.source_flag,
        index: searchQueryParams.index,
        items: items.slice(0, 3).map((item) => item.item_number),
      },
    });
  },
  [
    /* 依赖项 */
  ]
);

// 场景3：页面初始化时
useEffect(() => {
  if (!loading && items.length > 0) {
    track({
      name: AnalyticsEventNameMap.EVENT_SEARCH_RESULT,
      memo: '搜索结果页各条件搜索',
      properties: {
        keyword: keywords,
        condition: getSortName(getCurrentSortId()),
        bu_type: String(searchQueryParams.bu_type || 'search'),
        module_name: searchQueryParams.module_name,
        content: String(searchQueryParams.content || keywords),
        result_number: totalCount,
        source_flag: searchQueryParams.source_flag,
        index: searchQueryParams.index,
        items: items.slice(0, 3).map((item) => item.item_number),
      },
    });
  }
}, [keywords, totalCount, loading]);
```

## 常见问题

### Q1: 看到 EVENT_CLICK_FEEDBACK，应该创建新事件吗？

**A**: ❌ 不应该！这是最常见的错误。

**正确做法**：

1. 在 `common-track.js` 中查找 `EVENT_CLICK_FEEDBACK` 的处理逻辑
2. 找到实际调用的事件名，例如：`sensors.track('event_click', data)`
3. 在 Next.js 的适配器中搜索 `'event_click'`
4. 如果找到，说明 `EVENT_CLICK` 已存在，直接复用
5. 如果需要新参数，在 `ClickEventDTO` 中添加可选参数

**示例**：

```javascript
// Laravel: common-track.js
PubSub.subscribe(PUBSUB_TRACK.EVENT_CLICK_FEEDBACK, function(msg, data) {
  sensors.track('event_click', data);  // ← 实际上报 event_click
});

// Next.js: 复用 EVENT_CLICK，不创建 EVENT_CLICK_FEEDBACK
track({
  name: AnalyticsEventNameMap.EVENT_CLICK,  // ✅ 正确
  // name: AnalyticsEventNameMap.EVENT_CLICK_FEEDBACK,  // ❌ 错误
  properties: { ... }
});
```

### Q2: 如何判断是否应该创建新事件？

**A**: 按照以下流程判断：

1. **在 track 文件中找到实际上报的事件名**
   - 例如：`sensors.track('event_new_feature', data)`

2. **在 Next.js 三个适配器中搜索该事件名**

   ```bash
   # 搜索 'event_new_feature'
   # 在 adapterSensor.ts、adapterYamidata.ts、adapterYmb.ts 中搜索
   ```

3. **根据搜索结果决策**
   - 找到 → 复用已有事件（可能需要添加新参数）
   - 未找到 → 创建新事件

### Q3: 如何处理事件名称不一致的情况？

**A**: 在适配器中分别处理：

- Sensor/Yamidata 使用下划线格式：`event_xxx_xxx`
- Ymb 使用点号格式：`event_xxx.xxx`

### Q4: 如何处理参数格式不一致的情况？

**A**:

- DTO 中统一使用对象格式
- Ymb 适配器的 `commonTrack` 方法会自动转换为数组格式

### Q5: 如何处理 Blade 模板中的内联埋点？

**A**:

1. 找到 Blade 模板中的 `onclick="onMixpanelTrack(...)"`
2. 将其迁移到 React 组件的事件处理函数中
3. 使用 `track()` 方法发送埋点

### Q6: 如何确保三个平台的埋点都正确触发？

**A**:

1. 在 DTO 中定义完整的参数类型
2. 在三个适配器中都添加对应的 case 分支
3. 在浏览器控制台查看埋点日志验证

### Q7: 如何为已有事件添加新参数？

**A**: 在 DTO 中添加可选参数并标注来源：

```typescript
/**
 * 点击事件参数
 *
 * 参考老PC：
 * - 神策埋点: common-track.js EVENT_CLICK → event_click
 * - 【新增】神策埋点: common-track.js EVENT_CLICK_FEEDBACK → event_click (复用)
 */
export type ClickEventDTO = AnalyticsEventDTO<
  (typeof AnalyticsEventNameMap)['EVENT_CLICK'],
  string,
  {
    // 原有参数
    module_name: string;
    content: string;

    // 新增参数（来自 EVENT_CLICK_FEEDBACK 场景）
    feedback_type?: string; // 反馈类型
    feedback_value?: string; // 反馈值

    [key: string]: any;
  }
>;
```

## 相关文件索引

### Laravel 项目

- `resources/views/partials/_sensors.blade.php` - Sensor SDK 初始化
- `resources/views/partials/_yamidata.blade.php` - Yamidata SDK 初始化
- `resources/assets/js/yamibuy-analytics.js` - Ymb SDK 初始化
- `resources/assets/js/enum.js` - 埋点事件常量定义
- `resources/assets/js/track/common-track.js` - Sensor 埋点处理
- `resources/assets/js/track/yamidata-track.js` - Yamidata 埋点处理
- `resources/assets/js/track/mixpanel-track.js` - Ymb 埋点处理

### Next.js 项目

- `src/features/analytics/adapterBase.ts` - 适配器基类
- `src/features/analytics/adapterSensor.ts` - Sensor 适配器
- `src/features/analytics/adapterYamidata.ts` - Yamidata 适配器
- `src/features/analytics/adapterYmb.ts` - Ymb 适配器
- `src/features/analytics/dto.ts` - 事件类型定义
- `src/features/analytics/index.ts` - 埋点管理器
- `src/features/analytics/mapEventName.ts` - 事件名称常量
- `src/features/analytics/provider.tsx` - 埋点 Provider
- `src/features/analytics/README.md` - 埋点系统文档

## 总结

通过这个 AI Prompt 模板，你可以：

1. ✅ 系统化地分析 Laravel 项目中的埋点代码
2. ✅ 识别实际上报的事件名称（而不是被 PubSub 常量名误导）
3. ✅ 正确判断是复用已有事件还是创建新事件
4. ✅ 规范化地在 Next.js 项目中定义或更新事件类型
5. ✅ 统一地在三个适配器中实现事件处理
6. ✅ 正确地在业务代码中调用埋点方法
7. ✅ 确保三个平台的埋点同时触发且参数正确

## 🔑 关键原则（必须遵守）

### 1. 事件复用原则（最重要）

**⚠️ PubSub 常量名 ≠ 实际上报的事件名！**

- ❌ **错误**：看到 `EVENT_CLICK_FEEDBACK` 就创建新事件
- ✅ **正确**：查看 track 文件，发现实际上报 `event_click`，复用 `EVENT_CLICK`

**迁移前必须做**：

1. 在 track 文件中找到 `sensors.track('event_xxx', ...)` 的实际事件名
2. 在 Next.js 适配器中搜索该事件名
3. 找到 → 复用；未找到 → 创建

### 2. 事件名称格式

- **Sensor/Yamidata**: `event_xxx_xxx` (下划线)
- **Ymb**: `event_xxx.xxx` (点号)

### 3. 参数格式

- **DTO**: 对象格式 `{ key: value }`
- **Ymb 适配器**: 自动转换为数组格式

### 4. memo 参数

- 仅 Ymb 使用
- 从老PC的 `onMixpanelTrack` 第一个参数获取

### 5. Blade 埋点

- 需要迁移到 React 组件的事件处理函数中

## ⚠️ 常见错误

### 错误 1：直接根据 PubSub 常量创建新事件

```typescript
// ❌ 错误：看到 EVENT_CLICK_FEEDBACK 就创建新事件
export const AnalyticsEventNameMap = {
  EVENT_CLICK_FEEDBACK: 'EVENT_CLICK_FEEDBACK',
};

// ✅ 正确：查看 track 文件，发现实际上报 event_click，复用已有事件
// 不需要创建新常量，直接使用 EVENT_CLICK
```

### 错误 2：不检查事件是否已存在

```typescript
// ❌ 错误：不检查就创建新事件
// 导致同一个事件有多个常量

// ✅ 正确：先在适配器中搜索 'event_xxx'
// 如果找到，说明事件已存在，复用即可
```

### 错误 3：修改已有事件的必填参数

```typescript
// ❌ 错误：将可选参数改为必填
export type ClickEventDTO = {
  module_name: string;
  new_param: string; // ← 错误！会破坏已有代码
};

// ✅ 正确：新参数设为可选
export type ClickEventDTO = {
  module_name: string;
  new_param?: string; // ← 正确！向后兼容
};
```

## 📋 快速检查清单

迁移前问自己：

1. ❓ 我是否在 track 文件中找到了实际上报的事件名？
2. ❓ 我是否在 Next.js 适配器中搜索过该事件名？
3. ❓ 我是否确认了该事件不存在才创建新事件？
4. ❓ 如果事件已存在，我是否只添加了可选参数？

如果以上任何一个问题的答案是"否"，请重新检查！
