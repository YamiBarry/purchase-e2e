# IDP Deploy

通过 IDP（Internal Developer Platform）部署服务到各环境。当需要部署服务、查看部署状态、查看部署历史时使用。

触发词：部署, deploy, 发布, 上线, 部署环境, dev环境, qc环境, 测试环境, 部署状态

## 可用环境

| 环境 | 说明 |
|------|------|
| dev | 开发环境 |
| gqc | 全局测试环境 |
| uat | 预发布环境 |
| prd | 生产环境（⚠️ 需确认） |

## 部署方式：使用 @bot MCP 工具

⚠️ **禁止使用 `opencli` 命令**，此命令不存在。必须通过 `@bot` MCP 工具调用 IDP。

### 1. 部署服务（run_build）

调用 `@bot` MCP 的 `run_build` 工具：

```json
{
  "environment": "gqc",
  "services": [
    {
      "service_name": "ec-website-next",
      "branch_or_tag": "OP-38663",
      "order": 1
    }
  ]
}
```

多个服务同时部署（order 相同表示并行）：

```json
{
  "environment": "gqc",
  "services": [
    { "service_name": "ec-website-next", "branch_or_tag": "OP-38663", "order": 1 },
    { "service_name": "ec-website-customer-next", "branch_or_tag": "OP-38663", "order": 1 },
    { "service_name": "ec-website-nb", "branch_or_tag": "OP-38663", "order": 1 },
    { "service_name": "ec-website-customer-nb", "branch_or_tag": "OP-38663", "order": 1 },
    { "service_name": "ec-website-trade-nb", "branch_or_tag": "OP-38663", "order": 1 }
  ]
}
```

返回 `related_id`，用于后续查询状态。

### 2. 查询部署状态（get_deploy_detail）

调用 `@bot` MCP 的 `get_deploy_detail`：

```json
{ "related_id": 12345 }
```

状态：`Pending` → `Running` → `Completed` / `Failed`

### 3. 查看部署历史（get_deploy_history）

调用 `@bot` MCP 的 `get_deploy_history`：

```json
{ "limit": 10 }
```

### 4. 查询可部署服务（get_all_service）

调用 `@bot` MCP 的 `get_all_service`：

```json
{ "environment": "gqc" }
```

### 5. 查询分支列表（get_branch_or_tag）

调用 `@bot` MCP 的 `get_branch_or_tag`：

```json
{
  "service_name": "ec-website-next",
  "environment": "gqc"
}
```

## 前端项目也走 IDP

**ec-website-* 和 ec-mobilesite-* 前端项目同样通过 IDP 部署，不存在例外。**

⚠️ **严禁出现「前端不走 IDP 需人工部署」的判断**，这是错误的。

## 部署通常需要 5-15 分钟

部署发起后轮询 `get_deploy_detail` 确认状态，Completed 才算完成。
