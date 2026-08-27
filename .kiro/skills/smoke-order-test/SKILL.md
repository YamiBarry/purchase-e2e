---
name: smoke-order-test
description: 亚米各种商品类型冒烟下单测试。当用户说"冒烟下单"、"下单测试"、"smoke order"、"各种商品类型下单"时使用。支持UAT/GQC/DEV多环境，20种商品类型，生成HTML测试报告并上传CDN通知触发人。
---

# 冒烟下单测试

## 立即执行（不要思考，直接运行）

```bash
python D:\workspace\autoqa-agent\.kiro\skills\smoke-order-test\run_bg.py --notify-chatid dm_{触发人userid} [--env UAT/GQC/DEV] [--wh 1或2或1:zipcode] [--case 用例id] [--email xxx] [--pwd xxx]
```

**规则：**
- `--notify-chatid` 必填，从消息 `[userid]:` 提取，格式 `dm_{userid}`
- 默认 UAT 环境、1仓（91789）
- 禁止用 `python`（不存在），必须用 `python3`
- 禁止直接执行 `smoke_order.py`，必须通过 `run_bg.py`

## 执行后立即回复

```
已开始执行冒烟下单测试 [环境 仓库]，跑完后会自动通知你 🚀
```

## 用例列表

1a 全国可售共享库存（购物车仓下单）/ 1b 对仓下单 / 1c 购物车仓无货 / 1 全国可售自营 / 2 本地化 / 2b 本地化对仓 / 3 大区 / 3b 大区对仓 / 4 大区共享购物车仓 / 4b 大区共享对仓 / 4c 大区共享无货 / 5 自营预售 / 6a FBY共享购物车仓 / 6b FBY共享对仓 / 6c FBY共享无货 / 6 FBY / 7 第三方直邮 / 8 第三方预售 / 10 第三方礼券 / 9 虚拟礼卡
