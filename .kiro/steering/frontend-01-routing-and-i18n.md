---
inclusion: fileMatch
fileMatchPattern: '**/ec-website-{customer-next,next}/**'
---

### 路由与国际化（App Router + next-intl）

- **目录约定**: 多语言段位于 `src/app/[lang]/**`，使用 `routing`（`src/common/i18n/routing.ts`）定义 `locales` 与 `defaultLocale`。

#### 编码要求`

- 对于Link组件使用 `import { Link } from '@/common/i18n/navigation';`导入
- 如含多语言，必须在 `src/common/i18n/locales/*.json` 添加文案；严禁硬编码字符串。
