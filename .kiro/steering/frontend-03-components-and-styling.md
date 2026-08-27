---
inclusion: fileMatch
fileMatchPattern: '**/ec-website-{customer-next,next}/**'
---

### 组件与样式

- **组件分层**:
  - 基础 UI 组件放 `src/components/ui`，无业务、可复用、尽量“哑组件”。
  - 页面/布局结构在 `src/app/**`，需要的页面级组件可放置到页面的 `_components` 目录。
  - 业务专用组件放对应 `src/features/**/**View.tsx`。
- **客户端组件**: 仅在需要交互/状态/DOM/浏览器 API 时使用 `'use client'`，避免滥用。
- **样式**: 全局样式仅在 `src/app/layout.tsx` 导入 `@/assets/styles/globals.css`。组件内部优先使用CSS Modules

#### 编码要求

- 组件 props 清晰可读，避免使用 `any`。
- 避免深层嵌套与巨型组件，提取小组件提高可读性与可测试性。
- 文件命名统一使用 kebab-case 或 PascalCase（与现有风格保持一致）。
- 组件module.css文件命名要求和组件保持一致，组件名如果为PascalCase，css文件应该为PascalCase.module.css
- 要求module.css内部样式类名使用小驼峰命名

#### 组件文档规范

- **不生成 README.md**：文档说明直接写在组件内部的 JSDoc 注释中
- **示例文件**：只需一个 `example.tsx` 综合示例文件，包含主要使用场景
- **注释要求**：
  - 使用详细的 JSDoc 注释（`@description`, `@example`, `@remarks`, `@param` 等）
  - 注释应清晰明了，包含使用方法、注意事项、依赖要求等关键信息
  - 对外暴露的 API 必须有完整的类型定义和注释说明
