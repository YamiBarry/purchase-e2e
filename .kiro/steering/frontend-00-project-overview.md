---
inclusion: fileMatch
fileMatchPattern: '**/ec-website-{customer-next,next}/**'
---

### 项目总览

- **技术栈**: Next.js 15 (App Router), React 19, TypeScript 5, Tailwind CSS 3, next-intl 4, Zustand 5, ESLint 9, Prettier 3
- **目标场景**: 大型电商站点，强 i18n
- **导入路径**: 一律使用 `@/`（来自 `tsconfig.json`）
- **组件默认类型**: `Server Component`，仅在需要交互/状态/浏览器 API 时加 `'use client'`

#### 目录放置速查

| 用途 | 路径 |
|------|------|
| 静态资源 | `public/**` |
| 路由与页面 | `src/app/[lang]/**` |
| 请求和工具配置 | `src/common/**` |
| 共享 UI 组件 | `src/components/ui/**`（哑组件，无业务） |
| 跨页面业务功能 | `src/features/**`（不允许二级目录，all in one） |
| 数据访问层 | `src/services/**` |
| 全局状态 | `src/store/**` |
| 全局类型 | `src/types/**` |
| i18n 文案 | `src/common/i18n/locales/*.json` |

#### 样式策略
- 优先 Tailwind CSS；Tailwind 无法实现的用 CSS Module
- 全局样式仅在 `src/app/layout.tsx` 引入 `@/assets/styles/globals.css`

#### 常用脚本
- 开发: `pnpm dev` | 构建: `pnpm build` | 启动: `pnpm start`
- 代码规范: `pnpm lint` / `pnpm lint:fix`
- 依赖管理: 统一使用 `pnpm`
