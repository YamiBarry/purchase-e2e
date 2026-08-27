---
name: "sql-query"
description: "当需要查询数据库、查看表结构、确认字段类型和枚举值、验证数据时使用。触发词：sql, 数据库, 查询, mysql, 枚举, 表结构, 字段"
---

# 数据库查询

支持多环境的只读数据库查询能力。

## 环境配置

| 环境 | Host | .my.cnf 段 | 用途 |
|------|------|-----------|------|
| **生产从库**（默认） | rds.g3-slave.yamibuy.net | `[client]` | 查现有表结构、确认字段、验证数据 |
| **UAT** | eks-uat-8-cluster...rds.amazonaws.com | `[client_uat]` | UAT 环境测试数据 |
| **DEV** | eks-dev-8-cluster...rds.amazonaws.com | `[client_dev]` | 开发环境测试数据 |
| **GQC** | eks-gqc-8-cluster...rds.amazonaws.com | `[client_gqc]` | GQC 测试环境数据 |

凭据统一存储在 `~/.my.cnf`，不要在命令或对话中暴露密码。

## 使用方式：mysql 命令行

通过 shell 执行 mysql 命令查询数据库：

```bash
# 生产从库（默认，~/.my.cnf [client] 段）
mysql -e "SELECT ..." yamibuy_so

# UAT 环境
mysql --defaults-group-suffix=_uat -e "SELECT ..." yamibuy_so

# DEV 环境
mysql --defaults-group-suffix=_dev -e "SELECT ..." yamibuy_so

# GQC 环境
mysql --defaults-group-suffix=_gqc -e "SELECT ..." yamibuy_so
```

### 关键规则

- **凭据安全**：凭据存储在 `~/.my.cnf` 中，不要在命令中包含明文密码
- **时间戳**：数据库时间字段单位是秒（UNIX timestamp）
- **只读**：仅执行 SELECT/SHOW/DESCRIBE，禁止写操作

### 常用查询示例

```bash
# 查看表结构
mysql -e "SHOW FULL COLUMNS FROM ec_order" yamibuy_so

# 查看表索引
mysql -e "SHOW INDEX FROM ec_order" yamibuy_so

# 查询数据（带 LIMIT）
mysql -e "SELECT * FROM ec_order WHERE order_id = 12345 LIMIT 10" yamibuy_so

# 查询枚举值分布
mysql -e "SELECT DISTINCT status, COUNT(*) FROM ec_order GROUP BY status" yamibuy_so
```

## 常用数据库

| 数据库 | 内容 |
|--------|------|
| yamibuy_master | 主库（商品、供应商等） |
| yamibuy_so | 订单相关 |
| yamibuy_payment | 支付相关 |
| yamibuy_customer | 客户相关 |
| yamibuy_rma | 退货相关 |

## SOP 中的使用场景

| Phase | Agent | 用途 | 环境 |
|-------|-------|------|------|
| Phase 2 | Architect | 查现有表结构，设计 DDL | 生产从库 |
| Phase 3 | Coder | 确认字段类型、枚举值，写 Mapper XML | 生产从库 |
| Phase 3 | Reviewer | 验证 SQL 性能，检查索引 | 生产从库 |
| Phase 3.5 | QA | 验证测试数据，确认集成测试结果 | 测试环境 |
