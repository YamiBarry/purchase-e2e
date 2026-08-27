---
inclusion: fileMatch
fileMatchPattern: '**/ec-website-{customer-next,next}/**'
---

### 请求与 API 约定（统一使用 `@/common/request`）

- **禁止**: 不得在业务代码中直接使用 `axios` 或随意 `fetch`（尤其是 EC API）。
- **统一入口**: 所有请求使用 `@/common/request`（`RequestClient`）。该封装自动：
  - 注入 Token（`tokenManager`）与访客 ID、时区、语言等头。
  - 针对 `ecapi.` 域进行 WASM 签名（`apisign_wasm.js`）。
  - 生成并上报请求/响应日志（`/api/log-request`）。
  - 处理错误与 Token 失效（清理并重取匿名 Token）。
- **接口常量**: 统一在 `src/common/constants/ec-api/*` 定义，避免散落字符串。
- **环境代理**: 通过 `NEXT_PUBLIC_EC_API_DOMAIN` / `NEXT_PUBLIC_EC_INTRANET_API_DOMAIN` 与 `NODE_ENV` 自动切换代理。

#### 使用范式

```ts
import request from '@/common/request';
import { getItemInfoAllV4 } from '@/common/constants/ec-api/ec-item';

const res = await request.get(getItemInfoAllV4(), { params: { itemNumber } });
if (res.status === 200) {
  /* ... */
}
```
