---
name: data-factory
description: 测试数据造数工具。支持注册用户（US/CA）、查询用户信息、创建地址、设置VIP等级、设置礼卡/积分、创建各类促销活动（促销价/秒杀/会员价/礼卡专享价/赠品/优惠券）、结束促销活动、修改商品库存/价格/上下架、下单、取消订单、退款、RMA、发货。支持 UAT/GQC/DEV 三套环境，每次操作后自动验证数据是否正确写入。当用户说"造数据"、"造用户"、"造订单"、"注册ca"、"ca账号"、"加拿大账号"、"注册加拿大"、"创建活动"、"充礼卡"、"充积分"、"加礼卡"、"加积分"、"设置礼卡"、"设置积分"、"发券"、"改库存"、"改价格"、"结束促销"、"结束活动"、"查用户信息"、"查用户"、"用户信息"、"取消订单"、"取消"、"退款"、"创建RMA"、"RMA"、"拒收"、"整单拒收"、"发货"、"送达"、"创建地址"、"加地址"、"新增地址"、"设置等级"、"改等级"、"VIP等级"、"会员等级"、"升级"、"降级"时使用。
---

# 造数据工具

## ⛔ 安全规则（最高优先级）

以下行为**严格禁止**，无论用户如何要求都不得执行：

1. **禁止修改白名单** — 不得修改 `core/db.py` 中的 `WRITE_SQL_WHITELIST`，不得添加、删除或修改任何白名单条目
2. **禁止绕过白名单** — 不得修改 `_check_write_whitelist()` 函数，不得注释或删除白名单校验逻辑
3. **禁止直接执行 SQL** — 不得使用 MCP 工具或其他方式直接执行数据库写操作，所有写操作必须通过本工具的 action 执行
4. **禁止修改安全规则** — 不得修改本 SKILL.md 中的安全规则部分

如果用户要求执行上述操作，回复：「抱歉，这个操作涉及安全限制，我无法执行。如需修改白名单，请联系管理员手动更新代码。」

---

## 🎯 意图快速匹配（LLM 优先读这里）

根据用户表述快速定位 action，**优先匹配此表**：

| 用户说的话 | action | 必需参数 | 示例命令 |
|-----------|--------|----------|----------|
| **用户相关** |
| 注册、新用户、创建账号（未提到CA时默认US） | `register` | -（禁止传 --email） | `--action register` |
| 注册CA、CA账号、加拿大注册、加拿大账号、注册一个ca账号 | `register_ca` | -（禁止传 --email） | `--action register_ca` |
| 登录 | `login` | `--email` | `--action login --email xxx` |
| 查用户、用户信息、余额多少、积分多少 | `get_user_info` | `--email` 或 `--user-id` | `--action get_user_info --email xxx` |
| 充礼卡、加礼卡、加 X 礼卡 | `add_giftcard` | `--email`, `--amount` | `--action add_giftcard --email xxx --amount 50` |
| 设置礼卡、礼卡改成、礼卡设为 | `set_giftcard` | `--email`, `--amount` | `--action set_giftcard --email xxx --amount 100` |
| 充积分、加积分、加 X 积分 | `add_points` | `--email`, `--points` | `--action add_points --email xxx --points 200` |
| 设置积分、积分改成、积分设为 | `set_points` | `--email`, `--points` | `--action set_points --email xxx --points 500` |
| 兑换优惠券、领券 | `convert_coupon` | `--email`, `--ps-code` | `--action convert_coupon --email xxx --ps-code CODE` |
| 创建地址、加地址、造地址、美国地址、加拿大地址 | `create_address` | `--email` 或 `--user-id` | `--action create_address --email xxx --addr-state CA` |
| 设置等级、改等级、VIP等级、会员等级、升级、降级 | `set_vip_level` | `--email` 或 `--user-id`, `--level` | `--action set_vip_level --email xxx --level gold` |
| **商品相关** |
| 改库存、设置库存、库存改成 | `set_stock` | `--item-number`, `--stock` | `--action set_stock --item-number YAM-123 --stock 100` |
| 改价格、设置价格 | `set_price` | `--item-number`, `--price` | `--action set_price --item-number YAM-123 --price 19.9` |
| 上架、商品上架 | `set_status` | `--item-number`, `--status on` | `--action set_status --item-number YAM-123 --status on` |
| 下架、商品下架 | `set_status` | `--item-number`, `--status off` | `--action set_status --item-number YAM-123 --status off` |
| 找商品、查商品、找个自营商品 | `find_item` | `--type` | `--action find_item --type yami --site us` || **促销相关** |
| 创建活动、直降、促销价 | `create_promotion` | `--item-numbers` | `--action create_promotion --item-numbers 1021019111` |
| 秒杀、创建秒杀 | `create_seckill` | `--item-numbers` | `--action create_seckill --item-numbers 1021019111` |
| 会员价 | `create_member_price` | `--item-numbers` | `--action create_member_price --item-numbers 1021019111` |
| 礼卡价、礼卡专享价 | `create_giftcard_price` | `--item-numbers` | `--action create_giftcard_price --item-numbers 1021019111` |
| 赠品、买赠、满赠 | `create_gift_promotion` | - | `--action create_gift_promotion --item-number 1019000011` |
| 发券、创建优惠券 | `create_coupon` | - | `--action create_coupon --discount 10` |
| 结束活动、结束促销 | `finish_promotion` | `--ps-id` | `--action finish_promotion --ps-id 12345` |
| 结束赠品活动 | `finish_gift_promotion` | `--ps-id` | `--action finish_gift_promotion --ps-id 12345` |
| 查活动、查促销、所有活动、全部活动、列出活动、有哪些活动 | `find_promotion` | `--promo-type` | `--action find_promotion --promo-type coupon` |
| 查一个活动、查最近的活动 | `find_promotion` | `--promo-type`, `--promo-limit 1` | `--action find_promotion --promo-type discount --promo-limit 1` |
| **订单相关** |
| 下单、买、购买、造订单 | `place_order` | `--email` | `--action place_order --email xxx` |
| 取消、取消订单 | `cancel_orders` | `--email` 或 `--order-id` | `--action cancel_orders --email xxx --recent 5` |
| 发货、送货 | `shipping` | `--email` 或 `--order-id` | `--action shipping --email xxx --recent 5` |
| 送达、已送达 | `delivered` | `--email` 或 `--order-id` | `--action delivered --email xxx --recent 5` |
| 改送达时间、修改送达时间 | `update_delivery_time` | `--order-id` 或 `--order-sn` | `--action update_delivery_time --order-sn xxx --days-offset -3`（基于当前时间：-3=3天前，3=3天后，必须调用脚本执行，禁止直接SQL修改） |
| FP审核 | `fp_verify` | `--email` 或 `--order-id` | `--action fp_verify --email xxx --recent 5` |
| 结算 | `settlement` | `--email` 或 `--order-id` | `--action settlement --email xxx --recent 5` |
| **工具** |
| 时间戳、当前时间、格式化时间 | `timestamp` | - | `--action timestamp --ts 1777440771`（必须调用脚本，禁止自行计算） |

### ⚡ 高频场景速查

| 场景 | 完整命令 |
|------|----------|
| 给用户充 100 礼卡 | `python main.py --action add_giftcard --email xxx --amount 100 --env UAT` |
| 查用户余额和积分 | `python main.py --action get_user_info --email xxx --env UAT` |
| 给用户创建纽约地址 | `python main.py --action create_address --email xxx --addr-state NY --env UAT` |
| 取消用户最近 5 个订单 | `python main.py --action cancel_orders --email xxx --recent 5 --env UAT` |
| 给商品设置 100 库存 | `python main.py --action set_stock --item-number YAM-123 --stock 100 --env UAT` |
| 创建直降活动 | `python main.py --action create_promotion --item-numbers 1021019111 --env UAT` |
| 发货（含FP+结算） | `python main.py --action shipping --email xxx --recent 5 --env UAT` |
| 查所有优惠券活动 | `python main.py --action find_promotion --promo-type coupon --promo-limit 0 --env UAT` |
| 查所有直降活动 | `python main.py --action find_promotion --promo-type discount --promo-limit 0 --env UAT` |

---

## 命令速查表

| 操作 | action | 必需参数 | 可选参数 |
|------|--------|----------|----------|
| **用户** |
| 注册 | `register` | - | `--email`, `--pwd` |
| 登录 | `login` | `--email` | `--pwd` |
| 获取token | `get_token` | `--email` 或 `--user-id` | `--pwd` |
| 查用户信息 | `get_user_info` | `--email` 或 `--user-id` | `--pwd` |
| 加礼卡 | `add_giftcard` | `--email`/`--user-id`, `--amount` | - |
| 设置礼卡 | `set_giftcard` | `--email`/`--user-id`, `--amount` | - |
| 加积分 | `add_points` | `--email`/`--user-id`, `--points` | - |
| 设置积分 | `set_points` | `--email`/`--user-id`, `--points` | - |
| 兑换优惠券 | `convert_coupon` | `--email`/`--user-id`, `--ps-code` | `--pwd` |
| 创建地址 | `create_address` | `--email`/`--user-id` | `--addr-country`, `--addr-state`, `--addr-zipcode`, `--addr-address1`, `--addr-address2`, `--addr-city`, `--addr-firstname`, `--addr-lastname`, `--addr-phone`, `--addr-is-primary` |
| 设置VIP等级 | `set_vip_level` | `--email`/`--user-id`, `--level` | `--pwd` |
| 加购物车 | `add_to_cart` | `--email`/`--user-id`, `--item-number` | `--item-numbers`, `--zipcode` |
| 清空购物车 | `clear_cart` | `--email`/`--user-id` | - |
| **商品** |
| 设置库存 | `set_stock` | `--item-number`, `--stock` | `--item-numbers`, `--wh`（仅US站自营/FBY，CA站自动用101仓） |
| 设置价格 | `set_price` | `--item-number`, `--price` | `--market-price`, `--rule-id` |
| 上架 | `set_status` | `--item-number`, `--status on` | `--item-numbers` |
| 下架 | `set_status` | `--item-number`, `--status off` | `--item-numbers` |
| 查找商品 | `find_item` | `--type` | `--seller-id`, `--zipcode`, `--state`, `--site`, `--stock-condition`, `--min-stock`, `--limit` |
| **促销** |
| 创建直降 | `create_promotion` | `--item-numbers` | `--price-ratio`, `--promote-price`, `--hours`, `--ps-sub-title` |
| 创建秒杀 | `create_seckill` | `--item-numbers` | `--flash-qty`, `--preheat-minutes` |
| 创建会员价 | `create_member_price` | `--item-numbers` | `--price-ratio` |
| 创建礼卡价 | `create_giftcard_price` | `--item-numbers` | `--price-ratio` |
| 创建赠品活动 | `create_gift_promotion` | - | `--item-number`, `--gift-item`, `--seller-id`, `--gift-type` |
| 结束促销 | `finish_promotion` | `--ps-id` | - |
| 结束赠品活动 | `finish_gift_promotion` | `--ps-id` | - |
| 查询促销 | `find_promotion` | `--promo-type` | `--seller-id`, `--promo-status`, `--promo-limit` |
| 创建优惠券 | `create_coupon` | - | `--coupon-code`, `--coupon-type`, `--discount`, `--hours` |
| **订单** |
| 下单 | `place_order` | `--email`/`--user-id` | `--case`, `--item-number`, `--item-numbers`, `--qty`（每件购买数量，默认1）, `--wh`, `--count`（下单次数）, `--use-giftcard`, `--use-points`, `--coupon-code` |
| FP审核 | `fp_verify` | `--order-id`/`--order-sn`/`--user-id`/`--email` | `--recent` |
| 结算 | `settlement` | `--order-id`/`--order-sn`/`--user-id`/`--email` | `--recent` |
| 发货 | `shipping` | `--order-id`/`--order-sn`/`--user-id`/`--email` | `--tracking-number`, `--shipping-carrier`, `--recent` |
| 完整流程 | `process_orders` | `--order-id`/`--order-sn`/`--user-id`/`--email` | `--skip-fp`, `--skip-settlement`, `--skip-shipping` |
| 送达 | `delivered` | `--order-id`/`--order-sn`/`--user-id`/`--email` | `--recent` |
| 修改送达时间 | `update_delivery_time` | `--order-id` 或 `--order-sn` | `--days-offset`（基于当前时间，-3=3天前，3=3天后）, `--hours-offset`, `--minutes-offset`, `--delivery-timestamp` |
| 取消订单 | `cancel_orders` | `--order-id`/`--order-sn`/`--user-id`/`--email` | `--recent` |
| **工具** |
| 时间戳 | `timestamp` | - | `--ts`, `--offset` |
| 格式化JSON | `format_json` | `--json` | - |
| 压缩JSON | `compress_json` | `--json` | - |

---

## 执行方式

```bash
python "d:\yami-workspace\.kiro\skills\data-factory\main.py" [参数]
```

## ⚠️ 账号识别规则

- 用户可以提供 **邮箱** 或 **user_id**，两者都支持
- 说"**这个账号**"时，使用上一次操作的账号（邮箱或 user_id）
- user_id 会自动转换为邮箱后执行

```bash
# 用邮箱
--email renee.zhang@yamibuy.com

# 用 user_id
--user-id 915080
```

## ⚠️ 礼卡和积分的两种模式

### 模式一：加（增量）
用户说"**加** X 礼卡/积分"、"**充** X 礼卡/积分"
→ 在现有基础上增加 X，直接传增量值

```bash
# 加 50 礼卡（在现有余额基础上增加 50）
--action add_giftcard --email xxx --amount 50

# 加 200 积分（在现有积分基础上增加 200）
--action add_points --email xxx --points 200
```

### 模式二：设置（绝对值）
用户说"**设置**为 X"、"**改成** X"、"**变成** X"
→ 查当前值，自动计算差值，不足则增加，超出则扣减

```bash
# 把礼卡余额设置为 100（自动增加或扣减到 100）
--action set_giftcard --email xxx --amount 100

# 把积分设置为 500（自动增加或扣减到 500）
--action set_points --email xxx --points 500
```

---

## 单个操作

```bash
# 用户（注册/登录均返回完整 token 值）
# ⚠️ 注册时不要手动拼 email，不传 --email 参数即可让工具自动生成（US: autous{MMDD}{seq}, CA: autoca{MMDD}{seq}）
--action register                          # 注册新 US 用户，返回 email/pwd/user_id/token
--action register_ca                       # 注册新 CA 用户（含手机验证），返回 email/pwd/user_id/token/phone
--action register_ca --phone +1-0541822783 # 指定手机号注册 CA 用户
--action login   --email xxx --pwd xxx     # 登录，返回 email/token
--action get_token --email xxx             # 获取账号 token（支持 --user-id）
--action get_token --user-id 915080        # 用 user_id 获取 token

# 礼卡
--action add_giftcard  --email xxx --amount 50     # 加 50 礼卡（增量）
--action set_giftcard  --email xxx --amount 100    # 设置礼卡余额为 100（绝对值）

# 积分
--action add_points  --email xxx --points 200      # 加 200 积分（增量）
--action set_points  --email xxx --points 500      # 设置积分为 500（绝对值）

# 优惠券兑换
--action convert_coupon --email xxx --ps-code COUPON123    # 用邮箱兑换优惠券
--action convert_coupon --user-id 915080 --ps-code COUPON123  # 用 user_id 兑换优惠券

# 地址（默认创建美国CA地址，支持美国6州 + 加拿大4省模板）
# 美国可选州: CA(默认), NY, NJ, TX, WA, IL
# 加拿大可选省: ON(默认), BC, QC, AB
--action create_address --email xxx                                         # 默认：美国加州地址（CA 91789）
--action create_address --email xxx --addr-state NY                         # 美国纽约地址
--action create_address --email xxx --addr-state NJ                         # 美国新泽西地址（NJ仓 04001）
--action create_address --email xxx --addr-country CA --addr-state ON       # 加拿大安大略省地址
--action create_address --email xxx --addr-country CA --addr-state BC       # 加拿大BC省地址
--action create_address --user-id 915080                                    # 用 user_id 创建地址（默认CA）
--action create_address --email xxx --addr-zipcode 10001 --addr-state NY    # 自定义邮编
--action create_address --email xxx --addr-address1 "123 Main St" --addr-city "Los Angeles" --addr-state CA  # 自定义地址
--action create_address --email xxx --addr-firstname John --addr-lastname Doe --addr-phone 6261112222  # 自定义收件人
--action create_address --email xxx --addr-is-primary 0                     # 不设为默认地址

# VIP 等级（支持 ruby/silver/gold，升级自动调接口，降级直接改DB）
--action set_vip_level --email xxx --level gold                             # 升级为 Gold
--action set_vip_level --email xxx --level silver                           # 设置为 Silver
--action set_vip_level --email xxx --level ruby                             # 降级为 Ruby
--action set_vip_level --user-id 915080 --level gold                        # 用 user_id 设置等级

# 商品
--action set_stock    --item-number YAM-123 --stock 100                  # 设置库存（自动识别商品类型和站点）
--action set_stock    --item-number YAM-123 --stock 100 --wh 1           # 自营/FBY US站商品指定 LA 仓(001)
--action set_stock    --item-number YAM-123 --stock 100 --wh 2           # 自营/FBY US站商品指定 NJ 仓(002)
--action set_stock    --item-numbers YAM-123 YAM-456 --stock 200         # 批量设置库存
# 商品类型与库存仓库对应关系：
# - 自营 US站（business_type=1, seller_id=0, site_code=us）：仓库 001/002，可用 --wh 指定
# - 自营 CA站（business_type=1, seller_id=0, site_code=ca）：仓库 101，无需指定 --wh（自动使用101）

# 查找商品（按类型查找符合条件的商品）
# 查询策略：先查库存>=5的商品，如果没有结果，降级查库存>=1的商品，随机返回
--action find_item --type yami                                           # 自营全国商品（两仓都有货）
--action find_item --type yami_share                                     # 自营全国共享库存商品
--action find_item --type yami_region --zipcode 91789                    # 自营大区商品
--action find_item --type yami_region_share --zipcode 10001              # 自营大区共享库存商品
--action find_item --type yami_local --zipcode 91789                     # 自营本地化商品
--action find_item --type yami_presale                                   # 自营预售商品
--action find_item --type fby                                            # FBY全国商品
--action find_item --type fby --seller-id 50                             # 指定商家的FBY商品
--action find_item --type fby_share                                      # FBY全国共享库存商品
--action find_item --type seller                                         # 第三方直邮商品
--action find_item --type seller --seller-id 123                         # 指定商家的第三方直邮商品
--action find_item --type seller_presale                                 # 第三方预售商品
--action find_item --type seller_coupon                                  # 第三方礼券商品
--action find_item --type egift                                          # 自营虚拟礼卡商品
--action find_item --type crv                                            # CRV商品（带押金，任意州）
--action find_item --type crv --state CA                                 # CRV商品（加州）
--action find_item --type crv --state NY                                 # CRV商品（纽约州）
--action find_item --type import_fee                                     # 进口费用商品（第三方直邮/预售）
--action find_item --type import_fee --seller-id 61                      # 指定商家的进口费用商品
# 库存条件
--action find_item --type yami --stock-condition both                    # 两仓都有货（默认）
--action find_item --type yami --stock-condition wh1_only                # 仅1仓有货，2仓无货
--action find_item --type yami --stock-condition wh2_only                # 仅2仓有货，1仓无货
--action find_item --type yami --stock-condition none                    # 两仓都无货
# 其他参数
--action find_item --type yami --min-stock 10                            # 最小库存要求（默认5，查不到降级为1）
--action find_item --type yami --limit 5                                 # 返回5个商品
# ⚠️ 站点过滤（测试时必须指定 --site，避免跨站商品污染）
--action find_item --type yami --site us                                 # 美国站商品（site_code=us）
--action find_item --type yami --site ca                                 # 加拿大站商品（site_code=ca）
# 规则：美国站测试用 --site us；加拿大站测试用 --site ca；不传则查所有站点
# ⚠️ 各站点自营 seller_id 说明：
# - 美国站自营：seller_id = 0
# - 加拿大站自营：seller_id = 5000
# 工具内部已自动处理，--site ca 时会自动过滤 seller_id=5000，无需手动指定
# - FBY（business_type=5, seller_id>0）：仓库 001/002，需指定 --wh
# - 第三方直邮（business_type=3, seller_id>0）：仓库 9000{seller_id}，自动识别
# - 第三方预售（business_type=6, seller_id>0）：仓库 9000{seller_id}，自动识别
--action set_price    --item-number YAM-123 --price 19.9
--action set_status   --item-number YAM-123 --status on   # 单个商品上架
--action set_status   --item-number YAM-123 --status off  # 单个商品下架
--action set_status   --item-numbers 1022018221 1022026091 --status off  # 批量下架
--action set_status   --item-numbers 1022018221 1022026091 --status on   # 批量上架

# 促销活动（均返回 ps_id，定制价格模式自动查 unit_price 计算促销价）
--action create_promotion      --item-numbers 1021019111                     # 直降，促销价=unit_price*0.8（默认）
--action create_promotion      --item-numbers 1021019111 1022019391 --price-ratio 0.7  # 多商品，促销价=unit_price*0.7
--action create_seckill        --item-numbers 1021019111                     # 秒杀（提交锁库存），预热10min
--action create_seckill        --item-numbers 1021019111 --preheat-minutes 30  # 秒杀预热30分钟
--action create_giftcard_price --item-numbers 1021019111                     # 礼卡专享价
--action create_member_price   --item-numbers 1021019111                     # 会员价（百分比模式）
--action create_promotion      --item-numbers 1021019111 --sale-goods-way 2  # 第三方商品
--action create_promotion      --item-numbers 1021019111 --ps-sub-title 直降0414测试01  # 指定促销标题
--action create_promotion      --item-numbers 1021019111 --hours 48          # 活动时长48h
# 结束促销活动
--action finish_promotion --ps-id 22349    # 结束指定促销活动

# 查询促销活动（默认返回最近1个生效的活动）
# ⚠️ 意图识别规则：
#   - 用户说"查一个"、"查最近的"、"有没有" → 默认 --promo-limit 1
#   - 用户说"所有"、"全部"、"列出"、"有哪些" → 使用 --promo-limit 0
--action find_promotion --promo-type gift                                    # 查询赠品活动（返回1个）
--action find_promotion --promo-type coupon                                  # 查询优惠券活动（返回1个）
--action find_promotion --promo-type discount                                # 查询直降活动（返回1个）
--action find_promotion --promo-type seckill                                 # 查询秒杀活动（返回1个）
--action find_promotion --promo-type giftcard                                # 查询礼卡专享价活动（返回1个）
--action find_promotion --promo-type member                                  # 查询会员价活动（返回1个）
--action find_promotion --promo-type gift --promo-status 20                  # 查询待生效的赠品活动
--action find_promotion --promo-type discount --seller-id 0                  # 查询自营直降活动
--action find_promotion --promo-type discount --seller-id 123                # 查询指定商家的直降活动
# 返回多条记录（用户说"所有"、"全部"、"列出"、"有哪些"时使用）
--action find_promotion --promo-type discount --promo-limit 10               # 返回最近10个直降活动
--action find_promotion --promo-type gift --promo-limit 0                    # 返回所有赠品活动（limit=0表示全部）
--action find_promotion --promo-type coupon --promo-limit 0                  # 返回所有优惠券活动

# 赠品活动（买赠/满赠）
# 默认行为：不指定参数时，自动查找一个自营全国可售商品作为主品和赠品
--action create_gift_promotion                                               # 自动查找商品创建买赠活动
# 按商品建（主商品范围=单品）
--action create_gift_promotion --item-number 1019000011                      # 买赠，赠品=主商品
--action create_gift_promotion --item-number 1019000011 --gift-item 1017052971  # 买赠，指定赠品
--action create_gift_promotion --item-number 1019000011 --gift-type 1        # 满赠，默认满1件
--action create_gift_promotion --item-number 1019000011 --gift-type 1 --gift-threshold-num 2  # 满赠，满2件
--action create_gift_promotion --item-number 1019000011 --gift-type 1 --cal-type 0 --gift-threshold-line 50  # 满赠，满$50
# 按商家建（主商品范围=全场）- 必须指定 --seller-id 大于0
--action create_gift_promotion --seller-id 123 --gift-item 1017052971        # 第三方全场买赠
# 其他参数
--action create_gift_promotion --item-number 1019000011 --gift-overlap 0     # 不可叠加
--action create_gift_promotion --item-number 1019000011 --gift-num 2         # 赠品数量2
--action create_gift_promotion --item-number 1019000011 --gift-la-qty 50 --gift-nj-qty 50  # 指定库存
--action create_gift_promotion --item-number 1019000011 --ps-sub-title 测试赠品活动  # 指定活动名称
# 赠品库存说明：默认LA=20, NJ=20，超过实际库存时自动使用实际库存值
# 结束赠品活动
--action finish_gift_promotion --ps-id 12345                             # 结束指定赠品活动

# discount(直降定制价,默认) discount_pct(直降百分比) discount_fix(直降减价) discount_price(直降统一价)
# flash_sale(秒杀提交锁库存) flash_preheat(秒杀预热锁库存)
# giftcard(礼卡专享价)
# member(会员价百分比) member_fix(会员价减价) member_price(会员价定制)
--action create_coupon                                              # 默认：折扣券10%，仅兑换，全场，24h，发1000张
--action create_coupon --coupon-code MY_CODE                        # 指定兑换码
--action create_coupon --coupon-type reduce --buy-amount 30 --reduce-amount 5  # 满减券
--action create_coupon --coupon-type cash --cash-amount 10          # 现金券
--action create_coupon --discount 20 --coupon-amount 500            # 折扣20%，发500张
--action create_coupon --relative 5                                 # 相对时间5分钟（默认）
--action create_coupon --relative 60                                # 相对时间60分钟
--action create_coupon --hours 48                                   # 绝对时间48小时
--action create_coupon --coupon-form-type promo                     # 推广券
--action create_coupon --seller-id 123                              # 指定商家
--action create_coupon --scope item --scope-ids YAM-123             # 单品
--action create_coupon --scope item --scope-ids YAM-123 YAM-456     # 多个单品
--action create_coupon --scope category --scope-ids 101 102         # 分类
--action create_coupon --limit-user new                             # 仅新用户

# 购物车
--action add_to_cart  --email xxx --item-number YAM-123              # 加购单个商品（默认 zipcode 91789）
--action add_to_cart  --email xxx --item-numbers YAM-123 YAM-456     # 加购多个商品
--action add_to_cart  --email xxx --item-number YAM-123 --zipcode 10001  # 指定 zipcode
--action clear_cart   --email xxx                                     # 清空购物车

# 订单
--action place_order --email xxx                                        # 默认：1仓91789 全国可售自营，下1单
--action place_order --email xxx --count 5                              # 下5单（默认用例1）
--action place_order --email xxx --case 7                               # 指定用例类型
--action place_order --email xxx --wh 2                                 # 2仓（04001）
--action place_order --email xxx --wh 1:90001                           # 指定仓库+zipcode
--action place_order --email xxx --item-number YAM-123                  # 指定单个商品
--action place_order --email xxx --item-number YAM-123 --qty 3          # 指定商品，买3件（1个订单）
--action place_order --email xxx --item-numbers YAM-123 YAM-456         # 多商品同一订单，每个买1件
--action place_order --email xxx --item-numbers YAM-123 YAM-456 --qty 2 # 多商品同一订单，每个买2件
--action place_order --email xxx --use-giftcard                         # 使用礼卡抵扣
--action place_order --email xxx --use-points                           # 使用积分抵扣
--action place_order --email xxx --coupon-code CP_xxx                   # 使用优惠券
--action place_order --user-id 915080                                   # 用 user_id 下单

# 用例类型（--case 参数）
# 1(默认全国可售自营) 1a(共享库存购物车仓) 1b(对仓) 1c(购物车仓无货)
# 2(本地化) 3(大区) 3b(大区对仓)
# 4(大区共享购物车仓) 4b(大区共享对仓) 4c(大区共享无货)
# 5(自营预售) 6(FBY) 6a(FBY共享购物车仓) 6b(FBY共享对仓) 6c(FBY共享无货)
# 7(第三方直邮) 8(第三方预售) 9(虚拟礼卡) 10(第三方礼券)

# 订单处理（FP审核 → 结算 → 发货）
# 支持多种订单标识：order_id / order_sn / user_id / email
--action process_orders --order-id 310431479                            # 单个订单（order_id）
--action process_orders --order-ids 310431479 310431480                 # 多个订单（order_id）
--action process_orders --order-sn 2026041512345678                     # 单个订单（order_sn）
--action process_orders --order-sns 2026041512345678 2026041512345679   # 多个订单（order_sn）
--action process_orders --user-id 915080                                # 用户最近10个订单
--action process_orders --user-id 915080 --recent 5                     # 用户最近5个订单
--action process_orders --email test@yami.com                           # 邮箱用户最近10个订单
--action process_orders --email test@yami.com --recent 3                # 邮箱用户最近3个订单
--action process_orders --order-id 310431479 --skip-fp                  # 跳过FP审核
--action process_orders --order-id 310431479 --skip-settlement          # 跳过结算
--action process_orders --order-id 310431479 --skip-shipping            # 跳过发货
--action process_orders --order-id 310431479 --tracking-number TRK123   # 自定义发货单号

# 单独调用各步骤（同样支持 order_id / order_sn）
--action fp_verify   --order-id 310431479                               # 仅FP审核
--action fp_verify   --order-sn 2026041512345678                        # 用 order_sn
--action fp_verify   --order-ids 310431479 310431480                    # 批量FP审核
--action settlement  --order-id 310431479                               # 仅结算
--action settlement  --order-sns 2026041512345678 2026041512345679      # 批量结算
--action shipping    --order-id 310431479                               # 仅发货
--action shipping    --order-id 310431479 --tracking-number TRK123      # 发货+自定义单号
# 发货单号默认格式：test{YYYYMMDD}{序号}，如 test2026041501

# 取消订单（支持多种订单标识）
# 未发货订单：直接取消；已发货订单：自动走RMA整单拒收+退款
--action cancel_orders --order-id 310431479                             # 单个订单（order_id）
--action cancel_orders --order-ids 310431479 310431480                  # 多个订单（order_id）
--action cancel_orders --order-sn 2026041512345678                      # 单个订单（order_sn）
--action cancel_orders --order-sns 2026041512345678 2026041512345679    # 多个订单（order_sn）
--action cancel_orders --user-id 915080                                 # 用户最近10个订单
--action cancel_orders --user-id 915080 --recent 5                      # 用户最近5个订单
--action cancel_orders --email test@yami.com                            # 邮箱用户最近10个订单

# 时间戳工具（获取当前时间戳或解析时间戳）
--action timestamp                                                      # 获取当前时间戳
--action timestamp --offset -5m                                         # 5分钟前的时间戳
--action timestamp --offset +1h                                         # 1小时后的时间戳
--action timestamp --offset -1d                                         # 1天前的时间戳
--action timestamp --ts 1713340800                                      # 解析指定时间戳
# 输出同时显示北京时间(UTC+8)和美西时间(自动判断PDT/PST夏令时)
```

## 配方模式（组合场景）

```bash
--recipe new_user                                           # 注册新用户
--recipe user_with_balance  --giftcard 100 --points 500    # 新用户+充礼卡+充积分
--recipe seckill_item       --item-number YAM-123 --price 5.9 --stock 100
--recipe promotion_item     --item-number YAM-123 --price 9.9
--recipe coupon_in_account  --email xxx --discount 5 --min-order 30
--recipe new_user_order     --item-number YAM-123 --use-giftcard --giftcard 50
--recipe existing_user_order --email xxx --item-number YAM-123
```

## 环境参数

```bash
--env UAT   # 默认
--env GQC
--env DEV
```

## 验证机制

每个操作完成后自动查数据库验证：
- ✅ 验证通过：数据正常，直接使用
- ❌ 验证失败：告知哪个字段不对、期望值和实际值，并给出可能原因

## ⚠️ 冲突处理规则

当创建促销活动遇到冲突时：
- **只提示用户换其他商品创建活动**
- **不要主动建议用户去结束已有活动**
- 除非用户明确要求结束某个活动，否则不执行 finish_promotion

---

## ❓ 常见问题（FAQ）

### Q1: 执行命令报错 "ModuleNotFoundError: No module named 'xxx'"
**原因**: 缺少依赖包或工作目录不对。
**解决**: 
1. 确保在 `yami-workspace/.kiro/skills/data-factory/` 目录下执行
2. 安装依赖: `pip install pymysql`

### Q2: 报错 "user_id xxx 不存在"
**原因**: 提供的 user_id 在数据库中不存在。
**解决**: 
1. 使用 `--action get_user_info --email xxx` 确认用户是否存在
2. 或使用 `--action register` 注册新用户

### Q3: 礼卡/积分充值后余额不对
**原因**: 可能混淆了"加"和"设置"两种模式。
**解决**: 
- `add_giftcard/add_points`: 在现有基础上**增加**
- `set_giftcard/set_points`: 设为**绝对值**

### Q4: 创建促销活动报错 "商品已参与其他活动"
**原因**: 商品已在其他促销活动中。
**解决**: 
1. 换一个没有参与活动的商品
2. 或使用 `--action find_item --type yami` 查找可用商品

### Q5: 下单失败，提示库存不足
**原因**: 商品库存为 0 或不足。
**解决**: 
1. 先设置库存: `--action set_stock --item-number xxx --stock 100`
2. 再下单

### Q6: 取消订单失败
**原因**: 订单状态不允许取消（如已发货）。
**解决**: 
- 已发货订单会自动走 RMA 整单拒收流程
- 如果 RMA 也失败，可能是订单状态已完结

### Q7: 如何预览命令而不实际执行？
**解决**: 添加 `--dry-run` 参数
```bash
python main.py --action add_giftcard --email xxx --amount 100 --env UAT --dry-run
```

### Q8: 网络超时或连接失败
**原因**: 测试环境网络不稳定。
**解决**: 
- 工具已内置自动重试机制（最多 3 次）
- 如果仍然失败，请检查 VPN 连接或稍后重试

### Q9: 如何查看某个用户的所有信息？
**解决**: 
```bash
python main.py --action get_user_info --email xxx --env UAT
```
返回: user_id、邮箱、礼卡余额、积分、VIP 等级等
