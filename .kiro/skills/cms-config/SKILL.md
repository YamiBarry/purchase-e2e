# CMS Config Skill

管理 Central CMS 配置。当需要查询、创建、更新 CMS 配置项时使用。

## 触发词
CMS, 配置, config, site_config, 开关配置, 功能开关, footer配置

## 环境配置

**测试环境**（默认）：
```bash
CENTRAL_WEB="https://dev-central.yamibuy.tech"
CENTRAL_API="https://dev-centralapi.yamibuy.tech"
```

**生产环境**（需明确指定）：
```bash
CENTRAL_WEB="https://central.yamibuy.net"
CENTRAL_API="https://centralapi.yamibuy.net"
```

## 自动获取 Token

使用内置管理账号自动登录获取 token：

```bash
# 测试环境登录
CENTRAL_API="https://dev-centralapi.yamibuy.tech"
TOKEN=$(curl -s -X POST ${CENTRAL_API}/hub/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin.fp","password":"yami@123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['body']['token'])")
echo "Token: $TOKEN"
```

**Token 缓存**（可选）：
```bash
# 写入缓存文件，避免重复登录
python3 -c "import json,datetime; json.dump({'token':'$TOKEN','obtained_at':datetime.datetime.now().isoformat(),'email':'admin.fp'}, open('.kiro/token-cache.json','w'))"

# 从缓存读取（12小时内有效）
TOKEN=$(python3 -c "import json; print(json.load(open('.kiro/token-cache.json'))['token'])")
```

**备选方式**（手动获取）：
1. 浏览器登录 `https://dev-central.yamibuy.tech`
2. F12 → Network → 随便找一个请求 → 复制 `token` header 的值

## API 说明

### 基础配置

```bash
CENTRAL_WEB="https://dev-central.yamibuy.tech"
CENTRAL_API="https://dev-centralapi.yamibuy.tech"
TOKEN="your_token_here"
SITE_CODE="us"  # us | ca
```

### 1. 查询配置列表

```bash
curl -s "${CENTRAL_API}/content/config/queryList" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ${SITE_CODE}" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web" \
  -d '{
    "keyword": "搜索关键词",
    "status": "",
    "startColumn": 0,
    "pageSize": 20,
    "order": {"orderColumn": "rec_id", "orderRule": "desc"},
    "draw": 1
  }'
```

**响应**：
```json
{
  "messageId": "10000",
  "success": "true",
  "body": {
    "recordsTotal": 2144,
    "recordsFiltered": 12,
    "data": [
      {
        "rec_id": 6461,
        "key": "config_key_name",
        "value": "{\"enabled\": true, ...}",
        "status": "1",
        "desc": "配置描述",
        "site_code": "ca",
        "in_dtm": 1784944877,
        "in_user": "user(id)",
        "edit_dtm": 1785567674,
        "edit_user": "user(id)"
      }
    ]
  }
}
```

### 2. 查询单个配置

```bash
curl -s "${CENTRAL_API}/content/config/queryById/${REC_ID}" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ${SITE_CODE}" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web"
```

### 3. 更新配置

```bash
curl -s "${CENTRAL_API}/content/config/update" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ${SITE_CODE}" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web" \
  -d '{
    "rec_id": 6461,
    "key": "config_key_name",
    "value": "{\"enabled\": true}",
    "status": "1",
    "desc": "配置描述",
    "site_code": "ca"
  }'
```

### 4. 创建配置

```bash
curl -s "${CENTRAL_API}/content/config/add" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ${SITE_CODE}" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web" \
  -d '{
    "key": "new_config_key",
    "value": "{\"enabled\": false}",
    "status": "1",
    "desc": "新配置描述",
    "site_code": "ca"
  }'
```

## 常见配置模式

### 功能开关配置

```json
{
  "enabled": true,
  "start_time": 1700000000,
  "end_time": 1800000000
}
```

### Footer 配置（如团长招募）

配置 key 命名规范：`ca_footer_leader_recruitment_config`

```json
{
  "enabled": true,
  "link_cn": "https://www.yami.com/ca/zh/article/xxx",
  "link_en": "https://www.yami.com/ca/en/article/xxx",
  "text_cn": "团长招募",
  "text_en": "Community Leader Recruitment"
}
```

### 邀请配置

```json
{
  "tier": {
    "threshold": 5,
    "amount_tier1": 10,
    "amount_tier2": 5
  },
  "prizes": {
    "coupon-1": {
      "type": "coupon",
      "give_amount": 10,
      "give_ps_id": "1007282",
      "desc_cn": "$10 优惠券",
      "desc_en": "$10 coupon"
    }
  },
  "rules": { ... }
}
```

## 使用示例

### 示例 1：查找配置

```bash
# 测试环境
CENTRAL_WEB="https://dev-central.yamibuy.tech"
CENTRAL_API="https://dev-centralapi.yamibuy.tech"
TOKEN="vt4_xxx"

# 搜索 footer 相关配置
curl -s "${CENTRAL_API}/content/config/queryList" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ca" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web" \
  -d '{"keyword":"footer","status":"","startColumn":0,"pageSize":20,"order":{"orderColumn":"rec_id","orderRule":"desc"},"draw":1}'
```

### 示例 2：创建功能开关配置

```bash
CENTRAL_WEB="https://dev-central.yamibuy.tech"
CENTRAL_API="https://dev-centralapi.yamibuy.tech"
TOKEN="vt4_xxx"

CONFIG_VALUE=$(cat <<'EOF'
{
  "enabled": true,
  "link_cn": "https://www.yami.com/ca/zh/article/123456",
  "link_en": "https://www.yami.com/ca/en/article/123456"
}
EOF
)

curl -s "${CENTRAL_API}/content/config/add" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ca" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web" \
  -d "{
    \"key\": \"ca_footer_leader_recruitment_config\",
    \"value\": $(echo "$CONFIG_VALUE" | jq -c . | jq -Rs .),
    \"status\": \"1\",
    \"desc\": \"加拿大站 footer 团长招募配置\",
    \"site_code\": \"ca\"
  }"
```

### 示例 3：更新配置（开启功能）

```bash
CENTRAL_WEB="https://dev-central.yamibuy.tech"
CENTRAL_API="https://dev-centralapi.yamibuy.tech"
TOKEN="vt4_xxx"
REC_ID=12345

# 先查询现有配置
EXISTING=$(curl -s "${CENTRAL_API}/content/config/queryById/${REC_ID}" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ca" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web")

# 修改 enabled 为 true
NEW_VALUE=$(echo "$EXISTING" | jq -r '.body.value' | jq '.enabled = true' | jq -c .)

# 更新
curl -s "${CENTRAL_API}/content/config/update" \
  -H "content-type: application/json" \
  -H "origin: ${CENTRAL_WEB}" \
  -H "referer: ${CENTRAL_WEB}/" \
  -H "site_code: ca" \
  -H "token: ${TOKEN}" \
  -H "yami-origin: central-web" \
  -d "{
    \"rec_id\": ${REC_ID},
    \"key\": $(echo "$EXISTING" | jq '.body.key'),
    \"value\": $(echo "$NEW_VALUE" | jq -Rs .),
    \"status\": \"1\",
    \"desc\": $(echo "$EXISTING" | jq '.body.desc'),
    \"site_code\": \"ca\"
  }"
```

## 前端读取 CMS 配置

前端通过 `ec-website-next` 仓库的 service 读取 CMS 配置：

```typescript
// /src/features/footer/service.ts
const footMenuKey = `nb_footer_menu_${configLang}`;
const footCopyrightMenuKey = `nb_footer_copyright_menu_${configLang}`;
```

配置 key 命名规范：
- 多语言配置：`{prefix}_{lang}` (如 `nb_footer_menu_en`, `nb_footer_menu_cn`)
- 功能开关：`{feature}_config` (如 `ca_footer_leader_recruitment_config`)

## 注意事项

1. **默认使用测试环境**：`dev-central.yamibuy.tech` / `dev-centralapi.yamibuy.tech`
2. **生产环境需明确指定**：`central.yamibuy.net` / `centralapi.yamibuy.net`
3. **Token 有效期**：Token 会过期，过期后需重新获取
4. **site_code**：必须正确设置 `us` 或 `ca`，不同站点配置独立
5. **value 字段**：是 JSON 字符串，更新时需要正确转义
6. **status 字段**：`"1"` 表示启用，`"0"` 表示禁用
7. **幂等性**：创建时如果 key 已存在会失败，需要用 update 接口
