---
inclusion: fileMatch
fileMatchPattern: '**/ec-website-{customer-next,next}/**'
---

### 状态管理（Zustand 优先）

- **定位**: `src/store` 存放客户端状态`。
- **切片**: 按页面或功能拆分 store。
- **可序列化**: 避免在 store 存入不可序列化数据（DOM、类实例、函数引用等）。
