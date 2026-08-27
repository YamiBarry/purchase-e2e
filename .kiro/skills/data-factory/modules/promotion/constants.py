# -*- coding: utf-8 -*-
"""
促销活动常量定义
"""


class PromotionStatus:
    """促销活动状态枚举"""
    DRAFT = 10          # 草稿
    PENDING = 20        # 待生效
    ACTIVE = 30         # 生效中
    ENDED = 40          # 已结束
    INVALID = 50        # 已失效
    
    # 优惠券特殊状态（与普通促销不同）
    COUPON_ACTIVE = 50  # 优惠券生效中


# 促销类型 -> discountMode 映射
PROMO_TYPE_MODE = {
    "discount":       "4",   # 直降-定制价格(默认, 促销价=unit_price*0.8)
    "discount_pct":   "1",   # 直降-百分比
    "discount_fix":   "2",   # 直降-统一减价
    "discount_price": "3",   # 直降-统一价
    "seckill":        "5",   # 秒杀-提交锁库存
    "seckill_preheat":"6",   # 秒杀-预热锁库存
    "giftcard":       "7",   # 礼卡专享价
    "member":         "8",   # 会员价-百分比
    "member_fix":     "9",   # 会员价-统一减价
    "member_price":   "10",  # 会员价-定制价格
}

# 促销类型 -> 中文名称映射
PROMO_TYPE_NAME = {
    "discount":       "直降",
    "discount_pct":   "直降",
    "discount_fix":   "直降",
    "discount_price": "直降",
    "seckill":        "秒杀",
    "seckill_preheat":"秒杀",
    "giftcard":       "礼卡专享价",
    "member":         "会员价",
    "member_fix":     "会员价",
    "member_price":   "会员价",
}

# 使用定制价格的模式(需要 customizeList)
CUSTOMIZE_MODES = {"discount", "seckill", "seckill_preheat", "giftcard", "member_price"}

# 冲突错误码
CONFLICT_MSG_IDS = {"41006", "41056", "41057", "41092", "42027", "42028", "42030", "41107", "41108", "41140"}

# ==================== 优惠券相关常量 ====================

class CouponType:
    """优惠券类型枚举"""
    DISCOUNT = 1    # 折扣券
    REDUCE = 2      # 满减券
    CASH = 3        # 现金券
    # 运费券使用 DISCOUNT 类型


class CouponForm:
    """优惠券形式枚举"""
    PLATFORM = 1    # 平台券
    PROMO = 2       # 促销券
    SHIPPING = 3    # 运费券


class CouponSendType:
    """优惠券发放方式枚举"""
    RECEIVE = 1     # 领取
    REDEEM = 2      # 兑换


class CouponScheduleType:
    """优惠券活动类型（mkt_promotion_schedule.type）"""
    COUPON = "12"   # 优惠券活动


class CouponTheme:
    """优惠券主题枚举"""
    DEFAULT = 17    # 默认主题


# 优惠券类型字符串 -> 枚举值映射
COUPON_TYPE_MAP = {
    "discount": CouponType.DISCOUNT,
    "reduce": CouponType.REDUCE,
    "cash": CouponType.CASH,
    "shipping": CouponType.DISCOUNT,  # 运费券使用折扣券类型
}

# 优惠券形式字符串 -> 枚举值映射
COUPON_FORM_MAP = {
    "platform": CouponForm.PLATFORM,
    "promo": CouponForm.PROMO,
}

# 优惠券发放方式字符串 -> 枚举值映射
COUPON_SEND_TYPE_MAP = {
    "receive": CouponSendType.RECEIVE,
    "redeem": CouponSendType.REDEEM,
}


# 活动类型配置（用于查询）
PROMO_QUERY_CONFIG = {
    "gift": {
        "name": "赠品活动",
        "api": "/mkt/giftPromotion/queryList",
        "create_action": "create_gift_promotion",
    },
    "coupon": {
        "name": "优惠券活动",
        "api": "/mkt/couponSchedule/v1/queryCouponList",
        "create_action": "create_coupon",
    },
    "discount": {
        "name": "直降活动",
        "api": "/mkt/promotion/v1/queryList",
        "create_action": "create_promotion",
        "discount_modes": ["1", "2", "3", "4"],
    },
    "seckill": {
        "name": "秒杀活动",
        "api": "/mkt/promotion/v1/queryList",
        "create_action": "create_seckill",
        "discount_modes": ["5", "6"],
    },
    "giftcard": {
        "name": "礼卡专享价活动",
        "api": "/mkt/promotion/v1/queryList",
        "create_action": "create_giftcard_price",
        "discount_modes": ["7"],
    },
    "member": {
        "name": "会员价活动",
        "api": "/mkt/promotion/v1/queryList",
        "create_action": "create_member_price",
        "discount_modes": ["8", "9", "10"],
    },
}
