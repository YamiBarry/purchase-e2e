# -*- coding: utf-8 -*-
"""
命令行参数解析
定义所有 argparse 参数
"""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description="造数据工具")
    parser.add_argument("--env", default="UAT", help="环境: UAT / GQC / DEV")

    # 操作模式
    parser.add_argument("--action", help="单个操作")
    parser.add_argument("--recipe", help="配方模式（组合场景）")

    # ==================== 通用参数 ====================
    parser.add_argument("--email", help="用户邮箱（与 --user-id 二选一）")
    parser.add_argument("--user-id", dest="user_id", type=int, help="用户 ID（与 --email 二选一）")
    parser.add_argument("--pwd", help="用户密码（get_user_info 时可选，其他操作默认 111111）", default=None)
    parser.add_argument("--phone", help="手机号（CA注册用，不填则随机生成 +1-05XXXXXXXX）")
    parser.add_argument("--item-number", dest="item_number", help="商品编号（单个）")
    parser.add_argument("--item-numbers", dest="item_numbers", nargs="+", help="多个商品编号（多商品下单），配合 --qty 可统一设置数量")
    parser.add_argument("--count", type=int, default=1, help="下单次数，默认 1")
    parser.add_argument("--gift-item", dest="gift_item", help="赠品商品编号")
    parser.add_argument("--amount", type=float, help="礼卡金额")
    parser.add_argument("--points", type=int, help="积分数量")
    parser.add_argument("--ps-code", dest="ps_code", help="优惠券兑换码")
    parser.add_argument("--stock", type=int, help="库存数量")
    parser.add_argument("--price", type=float, help="价格（售价/unit_price）")
    parser.add_argument("--market-price", dest="market_price", type=float, help="市场价（可选，不填保持原值）")
    parser.add_argument("--rule-id", dest="rule_id", type=int, help="区域 rule_id（本地化商品可指定，不填则修改所有区域）")
    parser.add_argument("--status", choices=["on", "off"], help="上下架状态")
    parser.add_argument("--level", help="VIP 等级: ruby / silver / gold")

    # ==================== 优惠券参数 ====================
    parser.add_argument("--discount", type=float, help="折扣百分比（折扣券用）")
    parser.add_argument("--buy-amount", dest="buy_amount", type=float, help="满金额门槛（满减券用）")
    parser.add_argument("--reduce-amount", dest="reduce_amount", type=float, help="减金额（满减券用）")
    parser.add_argument("--cash-amount", dest="cash_amount", type=float, help="现金面额（现金券用）")
    parser.add_argument("--coupon-type", dest="coupon_type", default="discount", help="优惠券类型: discount/reduce/cash")
    parser.add_argument("--coupon-form-type", dest="coupon_form_type", default="platform", help="券形式: platform/promo")
    parser.add_argument("--send-type", dest="send_type", default="redeem", help="发放方式: redeem/receive")
    parser.add_argument("--coupon-amount", dest="coupon_amount", type=int, default=1000, help="发券数量，默认1000")
    parser.add_argument("--hours", type=int, default=24, help="绝对有效期小时数，默认24")
    parser.add_argument("--relative", type=int, default=5, help="相对使用时间（分钟），默认5")
    parser.add_argument("--seller-id", dest="seller_id", type=int, default=None, help="作用商家ID，0=自营，不指定则自动查找")
    parser.add_argument("--scope", default="all", help="作用范围: all/category/brand/item")
    parser.add_argument("--scope-ids", dest="scope_ids", nargs="+", help="范围ID列表（分类/品牌/商品item_number）")
    parser.add_argument("--limit-user", dest="limit_user", default="all", help="领取用户: all/new")
    parser.add_argument("--send-channel", dest="send_channel", type=int, default=0, help="发放渠道: 0=普通 1=员工")
    parser.add_argument("--shipping-group-type", dest="shipping_group_type", type=int, default=1, help="运费券业务类型: 1=亚米物流 3=商家直邮 4=中国集运 6=预售")
    parser.add_argument("--shipping-id", dest="shipping_id", type=int, help="配送方式ID，不填则自动取商家默认")
    parser.add_argument("--coupon-code", dest="coupon_code", help="优惠券兑换码")
    parser.add_argument("--min-order", dest="min_order", type=float, help="满减门槛金额（配方用）")
    parser.add_argument("--qty", type=int, default=1, help="购买数量，下单时每个商品的购买数量，默认1")

    # ==================== 地址参数 ====================
    parser.add_argument("--addr-country", dest="addr_country", default="US", help="地址国家: US=美国(默认), CA=加拿大")
    parser.add_argument("--addr-state", dest="addr_state", help="州/省缩写（美国: CA/NY/TX/WA/IL/NJ，加拿大: ON/BC/QC/AB）")
    parser.add_argument("--addr-zipcode", dest="addr_zipcode", help="地址邮编（不填则使用模板默认值）")
    parser.add_argument("--addr-address1", dest="addr_address1", help="地址行1（不填则使用模板默认值）")
    parser.add_argument("--addr-address2", dest="addr_address2", help="地址行2（可选）")
    parser.add_argument("--addr-city", dest="addr_city", help="城市（不填则使用模板默认值）")
    parser.add_argument("--addr-firstname", dest="addr_firstname", help="名（不填则使用 Test）")
    parser.add_argument("--addr-lastname", dest="addr_lastname", help="姓（不填则使用 User）")
    parser.add_argument("--addr-phone", dest="addr_phone", help="电话（不填则使用模板默认值）")
    parser.add_argument("--addr-is-primary", dest="addr_is_primary", type=int, default=1, help="是否设为默认地址: 1=是(默认) 0=否")

    # ==================== 促销活动参数 ====================
    parser.add_argument("--ps-id", dest="ps_id", type=int, help="促销活动 ps_id（结束活动时使用）")
    parser.add_argument("--promo-type", dest="promo_type", help="促销类型: gift/coupon/discount/seckill/giftcard/member（查询用）或 discount_fix/discount_price/seckill_preheat/member_fix/member_price（创建用）")
    parser.add_argument("--promo-status", dest="promo_status", type=int, help="查询活动状态: 30=生效中(默认) 20=待生效")
    parser.add_argument("--promo-limit", dest="promo_limit", type=int, default=0, help="查询促销活动返回数量，默认0返回全部，设为1只返回最近1个")
    parser.add_argument("--discount-value", dest="discount_value", type=float, help="折扣值（百分比时为10表示10%%OFF，减价时为金额）")
    parser.add_argument("--sale-goods-way", dest="sale_goods_way", default="1", help="支持范围: 1=自营(默认) 2=第三方")
    parser.add_argument("--ps-title", dest="ps_title", default="renee", help="促销组，默认 renee")
    parser.add_argument("--ps-sub-title", dest="ps_sub_title", help="促销标题，默认自动生成")
    parser.add_argument("--preheat-minutes", dest="preheat_minutes", type=int, default=10, help="秒杀预热时间（分钟），默认10")
    parser.add_argument("--flash-qty", dest="flash_qty", type=int, default=10, help="秒杀库存数量（LA仓和NJ仓各自），默认10")
    parser.add_argument("--flash-qty-la", dest="flash_qty_la", type=int, help="秒杀LA仓库存，不填则用 --flash-qty")
    parser.add_argument("--flash-qty-nj", dest="flash_qty_nj", type=int, help="秒杀NJ仓库存，不填则用 --flash-qty")
    parser.add_argument("--exclude-rules", dest="exclude_rules", nargs="+", type=int, help="不参与促销的区域 rule_id 列表")
    parser.add_argument("--price-ratio", dest="price_ratio", type=float, default=0.8, help="定制价格模式下促销价比例，默认0.8（即unit_price*0.8）")
    parser.add_argument("--promote-price", dest="promote_prices", nargs="+", type=float, help="指定商品促销价，多个按 --item-numbers 顺序对应")
    parser.add_argument("--start-time", dest="start_time", type=int, help="开始时间（Unix时间戳），默认当前时间")
    parser.add_argument("--end-time", dest="end_time", type=int, help="结束时间（Unix时间戳），默认24h后")

    # ==================== 赠品活动参数 ====================
    parser.add_argument("--gift-type", dest="gift_type", type=int, default=0, help="赠品类型: 0=买赠(默认) 1=满赠")
    parser.add_argument("--cal-type", dest="cal_type", type=int, default=1, help="满赠计算方式: 0=按金额 1=按数量(默认)")
    parser.add_argument("--gift-threshold-num", dest="gift_threshold_num", type=int, default=1, help="满赠数量门槛，默认1")
    parser.add_argument("--gift-threshold-line", dest="gift_threshold_line", type=float, default=10.0, help="满赠金额门槛，默认10")
    parser.add_argument("--gift-overlap", dest="gift_overlap", type=int, help="叠加规则: 0=不可叠加 1=可叠加(默认)")
    parser.add_argument("--gift-num", dest="gift_num", type=int, default=1, help="赠品数量，默认1")
    parser.add_argument("--gift-la-qty", dest="gift_la_qty", type=int, default=20, help="赠品LA仓库存，默认20")
    parser.add_argument("--gift-nj-qty", dest="gift_nj_qty", type=int, default=20, help="赠品NJ仓库存，默认20")

    # ==================== 下单参数 ====================
    parser.add_argument("--zipcode", help="zipcode（加购时设置，默认 91789）")
    parser.add_argument("--wh", help="仓库: 1(LA/91789) 或 2(NJ/04001) 或 1:zipcode")
    parser.add_argument("--case", help="下单用例类型: 1(默认), 1a, 1b, 2, 3, 4, 5, 6, 7, 8, 9, 10 等")
    parser.add_argument("--giftcard", type=float, default=0, help="礼卡充值金额（配方用）")
    parser.add_argument("--use-giftcard", dest="use_giftcard", action="store_true", help="下单时使用礼卡")
    parser.add_argument("--use-points", dest="use_points", action="store_true", help="下单时使用积分")

    # ==================== 查找商品参数 ====================
    parser.add_argument("--type", dest="item_type", help="商品类型: yami/yami_share/yami_region/yami_region_share/yami_local/yami_presale/fby/fby_share/seller/seller_presale/seller_coupon/egift/crv/import_fee")
    parser.add_argument("--stock-condition", dest="stock_condition", default="both", help="库存条件: both(两仓都有货)/wh1_only(仅1仓有货)/wh2_only(仅2仓有货)/none(两仓都无货)")
    parser.add_argument("--min-stock", dest="min_stock", type=int, default=5, help="最小库存要求，默认5（查不到会降级为1）")
    parser.add_argument("--limit", type=int, default=1, help="返回商品数量，默认1")
    parser.add_argument("--state", help="州缩写（CRV商品用，如 CA/CT/HI/IA/ME/MA/NY/OR/VT）")
    parser.add_argument("--site", help="站点代码: us=美国站, ca=加拿大站（不传则不过滤，查所有站点商品）")

    # ==================== 订单处理参数 ====================
    parser.add_argument("--order-id", dest="order_id", type=int, help="订单ID（单个）")
    parser.add_argument("--order-ids", dest="order_ids", nargs="+", type=int, help="多个订单ID")
    parser.add_argument("--order-sn", dest="order_sn", help="订单编号（单个）")
    parser.add_argument("--order-sns", dest="order_sns", nargs="+", help="多个订单编号")
    parser.add_argument("--recent", type=int, default=10, help="最近N个订单（配合 --user-id 或 --email 使用），默认10")
    parser.add_argument("--tracking-number", dest="tracking_number", help="自定义发货单号")
    parser.add_argument("--shipping-carrier", dest="shipping_carrier", default="7 Hours Express", help="物流公司，默认 7 Hours Express")
    parser.add_argument("--skip-fp", dest="skip_fp", action="store_true", help="跳过FP审核")
    parser.add_argument("--skip-settlement", dest="skip_settlement", action="store_true", help="跳过结算")
    parser.add_argument("--skip-shipping", dest="skip_shipping", action="store_true", help="跳过发货")
    parser.add_argument("--days-offset", dest="days_offset", type=int, help="送达时间偏移天数，正数=未来，负数=过去")
    parser.add_argument("--hours-offset", dest="hours_offset", type=int, help="送达时间偏移小时数，正数=未来，负数=过去")
    parser.add_argument("--minutes-offset", dest="minutes_offset", type=int, help="送达时间偏移分钟数，正数=未来，负数=过去")
    parser.add_argument("--delivery-timestamp", dest="delivery_timestamp", type=int, help="指定送达时间戳（秒）")

    # ==================== 工具参数 ====================
    parser.add_argument("--ts", type=int, help="要解析的时间戳（秒）")
    parser.add_argument("--offset", help="时间偏移量，如 -5m(前5分钟) +1h(后1小时) -1d(前1天)，支持 s/m/h/d")
    parser.add_argument("--json", dest="json_str", help="要格式化的 JSON 字符串")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="预览模式，只显示将要执行的操作，不实际执行")

    return parser


def parse_args():
    """解析命令行参数"""
    parser = create_parser()
    return parser.parse_args()
