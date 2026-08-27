---
inclusion: agent-requested
---
# 前端技术栈

## 项目分类

### Vue/Nuxt 项目（老项目）
- ec-mobilesite-nb, ec-mobilesite-ssr: Nuxt 2
- ec-website-nb, ec-website-customer-nb, ec-website-sns, ec-website-trade-nb: Vue 2
- ec-mobilesite-rma: Vue 2

### React/Next.js 项目（新项目）
- ec-website-next: React + Next.js + TypeScript
- ec-website-customer-next: React + Next.js + TypeScript

## 通用规范
- 先读取项目的 package.json 了解技术栈和依赖
- 遵循项目现有的目录结构和代码风格
- 组件拆分合理，单文件不超过 300 行
- 使用项目已有的 UI 组件库
- 国际化使用项目已有的 i18n 方案
- 修改后运行 `npm run build` 或 `yarn build` 验证
