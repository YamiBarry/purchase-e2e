---
inclusion: always
---
# Next.js 项目专属规则（Next.js 15.5.x + App Router）

> 配合 `ec-web-global.md` 通用规范使用。冲突时本文件优先。

## 必须（Next.js 特有）
- 必须使用 `pnpm`：`pnpm dev/build/start/lint/lint:fix`。
- 必须遵守 App Router：路由在 `src/app/**`，默认 Server Component。
- 只有需要交互/状态/浏览器 API 时才使用 `'use client'`。
- 必须使用 `@/` 别名导入，禁止深层相对路径级联。
- 必须统一走 `src/common/request`；接口常量放 `src/common/constants/ec-api/**`。
- 必须把跨页面功能放 `src/features/**`，共享状态放 `src/store/**`。
- 必须保持全局样式入口在 `src/app/layout.tsx`。

## 禁止（Next.js 特有）
- 禁止在客户端组件直接 import 服务端组件（需要时用 children 传递）。
- 禁止在 `src/app/**` 堆积复杂业务逻辑或数据转换逻辑。
- 禁止将派生数据存入 React state，或用 `useEffect` 仅做 props → state 同步。
- 禁止为局部需求新增全局状态，能局部 state 就不要上提。
- 禁止随意新增 `src` 二级顶层目录。
