---
inclusion: fileMatch
fileMatchPattern: '**/ec-website-{customer-next,next}/**'
---

### 代码风格与质量

- **类型**: 导出/公共 API 明确类型注解；不要使用 `any`；避免不安全断言。
- **控制流**: 使用早返回；处理错误/边界；避免深层嵌套；不要空 `catch`。
- **注释**: 仅在复杂“业务逻辑”处注释；不写显而易见的注释；不使用内联注释。
- **格式**: 遵循现有 ESLint/Prettier；多行优于长一行；避免无关重排。
- **命名**: 含义明确、全词命名；函数用动词；变量用名词；避免缩写。
- **提交**: `pnpm lint:fix` 通过后再提交；Commit 按 Conventional Commits。
