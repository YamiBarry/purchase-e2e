# -*- coding: utf-8 -*-
"""
促销活动模块
支持：直降/秒杀/礼卡专享价/会员价/赠品/优惠券

接口来源：
  创建促销: POST /mkt/promotion/v1/insert
  提交促销: POST /mkt/promotion/v1/submit
  结束促销: POST /mkt/promotion/v1/finish
  查询促销: POST /mkt/promotion/v1/queryList
"""

# 常量
from modules.promotion.constants import (
    PromotionStatus,
    PROMO_TYPE_MODE,
    PROMO_TYPE_NAME,
    CUSTOMIZE_MODES,
    CONFLICT_MSG_IDS,
    PROMO_QUERY_CONFIG,
)

# 辅助函数
from modules.promotion.helpers import (
    get_goods_info_for_mkt,
    parse_promotion_detail,
)

# 创建促销
from modules.promotion.create import action_create_promotion

# 管理促销
from modules.promotion.manage import (
    action_finish_promotion,
    action_find_promotion,
)

# 赠品活动
from modules.promotion.gift import (
    action_create_gift_promotion,
    action_finish_gift_promotion,
)

# 优惠券
from modules.promotion.coupon import (
    action_create_coupon,
)

__all__ = [
    # 常量
    "PromotionStatus",
    "PROMO_TYPE_MODE",
    "PROMO_TYPE_NAME",
    "CUSTOMIZE_MODES",
    "CONFLICT_MSG_IDS",
    "PROMO_QUERY_CONFIG",
    # 辅助函数
    "get_goods_info_for_mkt",
    "parse_promotion_detail",
    # 创建促销
    "action_create_promotion",
    # 管理促销
    "action_finish_promotion",
    "action_find_promotion",
    # 赠品活动
    "action_create_gift_promotion",
    "action_finish_gift_promotion",
    # 优惠券
    "action_create_coupon",
]
