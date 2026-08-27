# -*- coding: utf-8 -*-
"""
Action Handlers 模块
每个 handler 负责处理一类 action
"""

from handlers.user_handlers import USER_HANDLERS
from handlers.item_handlers import ITEM_HANDLERS
from handlers.promotion_handlers import PROMOTION_HANDLERS
from handlers.order_handlers import ORDER_HANDLERS
from handlers.utils_handlers import UTILS_HANDLERS

# 合并所有 handlers
ACTION_HANDLERS = {
    **USER_HANDLERS,
    **ITEM_HANDLERS,
    **PROMOTION_HANDLERS,
    **ORDER_HANDLERS,
    **UTILS_HANDLERS,
}

# 不需要 email 的 action 集合（这些 action 不依赖用户身份）
NO_EMAIL_ACTIONS = {
    # 用户相关（注册不需要已有 email）
    "register",
    "register_ca",
    # 商品相关
    "set_stock", "set_price", "set_status", "find_item",
    # 促销相关
    "create_promotion", "create_seckill", "create_member_price", "create_giftcard_price",
    "create_coupon", "finish_promotion", "create_gift_promotion", "finish_gift_promotion",
    "find_promotion",
    # 订单处理（支持通过 order_id/order_sn 指定，不一定需要 email）
    "fp_verify", "settlement", "shipping", "process_orders", "cancel_orders", "delivered",
    "update_delivery_time",
    # 工具类
    "timestamp", "format_json", "compress_json",
}

# 需要登录的 action 集合（这些 action 会在 handler 内部调用 login_user）
# 注意：add_to_cart、clear_cart 等虽然需要登录，但它们在 handler 内部自己处理登录
LOGIN_REQUIRED_ACTIONS = {"place_order"}
