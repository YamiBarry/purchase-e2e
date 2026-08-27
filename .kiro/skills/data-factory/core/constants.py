# -*- coding: utf-8 -*-
"""
常量定义模块。

统一管理魔法数字和枚举值，这些枚举值来自 Yamibuy 业务系统，与数据库字段值对应。

枚举分类:
    - 订单状态: OrderStatus, ShippingStatus, PayStatus, AbnormalStatus
    - 商品状态: ItemStatus
    - 促销相关: PromotionType, DiscountType, CouponType, CouponDiscountType
    - RMA 相关: RmaType, RmaStatus
    - 物流状态: TrackingStatusType
    - 支付相关: CardStatus
    - 取消原因: CancelReason, CancelSubReason
    - API 响应: ApiCode

Example:
    from core.constants import OrderStatus, PayStatus
    
    if order["order_status"] == OrderStatus.CONFIRMED:
        if order["pay_status"] == PayStatus.PAID:
            print("订单已确认且已支付")
"""

from enum import IntEnum
from typing import Union


class OrderType(IntEnum):
    """
    订单类型枚举 (xysc_order_info.order_type)。
    
    Attributes:
        NORMAL: 普通订单。
        CONSOLIDATION: 集运订单。
        FBY: FBY订单。
        PRESALE: 预售订单。
        EGIFT: 虚拟礼卡订单。
    """
    NORMAL = 1
    CONSOLIDATION = 3
    FBY = 5
    PRESALE = 6
    EGIFT = 7


class OrderStatus(IntEnum):
    """
    订单状态枚举 (xysc_order_info.order_status)。
    
    Attributes:
        PENDING: 待确认（刚下单）。
        CONFIRMED: 已确认（待发货）。
        CANCELLED_USER: 已取消（用户取消）。
        INVALID: 无效订单。
        CANCELLED_SYSTEM: 已取消（系统取消）。
        SHIPPED: 已发货。
    """
    PENDING = 0
    CONFIRMED = 1
    CANCELLED_USER = 2
    INVALID = 3
    CANCELLED_SYSTEM = 4
    SHIPPED = 5


class ShippingStatus(IntEnum):
    """
    发货状态枚举 (xysc_order_info.shipping_status)。
    
    Attributes:
        NOT_SHIPPED: 未发货。
        SHIPPED: 已发货。
        DELIVERED: 已送达。
    """
    NOT_SHIPPED = 0
    SHIPPED = 1
    DELIVERED = 2


class PayStatus(IntEnum):
    """
    支付状态枚举 (xysc_order_info.pay_status)。
    
    Attributes:
        UNPAID: 未支付。
        PAYING: 支付中。
        PAID: 已支付。
        REFUNDED: 已退款。
    """
    UNPAID = 0
    PAYING = 1
    PAID = 2
    REFUNDED = 3


class AbnormalStatus(IntEnum):
    """
    异常状态枚举 (xysc_order_info.abnormal)。
    
    Attributes:
        NORMAL: 正常。
        PENDING_FP: 待FP审核。
        FP_REJECTED: FP审核拒绝。
        PENDING_MANUAL: 待人工审核。
        FP_APPROVED: FP审核通过。
    """
    NORMAL = 0
    PENDING_FP = 1
    FP_REJECTED = 2
    PENDING_MANUAL = 3
    FP_APPROVED = 4


class CardStatus(IntEnum):
    """
    信用卡状态枚举 (payment_profile_card.status)。
    
    Attributes:
        DELETED: 已删除。
        ACTIVE: 有效。
    """
    DELETED = 0
    ACTIVE = 60


class PromotionType(IntEnum):
    """
    促销类型枚举。
    
    Attributes:
        NORMAL: 普通促销价。
        SECKILL: 秒杀。
        MEMBER_PRICE: 会员价。
        GIFTCARD_PRICE: 礼卡专享价。
        GIFT: 赠品促销。
    """
    NORMAL = 1
    SECKILL = 2
    MEMBER_PRICE = 3
    GIFTCARD_PRICE = 4
    GIFT = 5


class DiscountType(IntEnum):
    """
    折扣类型枚举。
    
    Attributes:
        PERCENT: 百分比折扣。
        FIXED: 固定金额减免。
    """
    PERCENT = 1
    FIXED = 2


class ItemStatus(IntEnum):
    """
    商品上架状态枚举 (xysc_goods.is_on_sale)。
    
    Note:
        这是 goods 表的 is_on_sale 字段，不是 item 表的 status 字段。
        item 表的 status 字段使用字符串 'A'/'D'。
    
    Attributes:
        OFF: 下架。
        ON: 上架。
    """
    OFF = 0
    ON = 1


class CouponType(IntEnum):
    """
    优惠券类型枚举。
    
    Attributes:
        GENERAL: 通用券。
        CATEGORY: 品类券。
        ITEM: 商品券。
    """
    GENERAL = 1
    CATEGORY = 2
    ITEM = 3


class CouponDiscountType(IntEnum):
    """
    优惠券折扣类型枚举。
    
    Attributes:
        FIXED_AMOUNT: 固定金额。
        PERCENT: 百分比。
    """
    FIXED_AMOUNT = 1
    PERCENT = 2


class RmaType(IntEnum):
    """
    RMA 类型枚举。
    
    Attributes:
        RETURN: 退货。
        EXCHANGE: 换货。
        REFUND: 仅退款。
    """
    RETURN = 1
    EXCHANGE = 2
    REFUND = 3


class RmaStatus(IntEnum):
    """
    RMA 状态枚举。
    
    Attributes:
        PENDING: 待处理。
        APPROVED: 已批准。
        REJECTED: 已拒绝。
        COMPLETED: 已完成。
    """
    PENDING = 0
    APPROVED = 1
    REJECTED = 2
    COMPLETED = 3


class TrackingStatusType(IntEnum):
    """
    物流状态类型枚举 (so_tracking_info.status JSON 中的 type)。
    
    Attributes:
        PROCESSED: 已处理。
        IN_TRANSIT: 运输中。
        OUT_FOR_DELIVERY: 派送中。
        DELIVERED: 已送达。
    """
    PROCESSED = 0
    IN_TRANSIT = 1
    OUT_FOR_DELIVERY = 2
    DELIVERED = 3


class CancelReason(IntEnum):
    """
    取消订单原因枚举。
    
    Attributes:
        OTHER: 其他原因（默认）。
    """
    OTHER = 14


class CancelSubReason(IntEnum):
    """
    取消订单子原因枚举。
    
    Attributes:
        DEFAULT: 默认子原因。
    """
    DEFAULT = 2


class ApiCode:
    """
    API 响应码常量。
    
    Attributes:
        SUCCESS: 成功响应码 "200"。
        SUCCESS_ALT: 备用成功响应码 "10000"。
    """
    SUCCESS: str = "200"
    SUCCESS_ALT: str = "10000"
    
    @classmethod
    def is_success(cls, code: Union[str, int]) -> bool:
        """
        判断响应码是否表示成功。
        
        Args:
            code: 响应码。
        
        Returns:
            True 表示成功，False 表示失败。
        """
        return str(code) in (cls.SUCCESS, cls.SUCCESS_ALT)


# ==================== 站点自营 seller_id 常量 ====================

# 各站点自营（Yami 直营）对应的 seller_id
YAMI_SELLER_ID_US = 0       # 美国站自营 seller_id
YAMI_SELLER_ID_CA = 5000    # 加拿大站自营 seller_id

# 所有站点的自营 seller_id 集合（用于 IN 查询）
YAMI_SELLER_IDS = {YAMI_SELLER_ID_US, YAMI_SELLER_ID_CA}


def get_yami_seller_id(site_code: str) -> int:
    """
    根据站点代码返回对应的自营 seller_id。

    Args:
        site_code: 站点代码，'us' 或 'ca'

    Returns:
        自营 seller_id（US=0，CA=5000）
    """
    return YAMI_SELLER_ID_CA if (site_code or "us").lower() == "ca" else YAMI_SELLER_ID_US


def is_yami_seller(seller_id: int) -> bool:
    """
    判断 seller_id 是否为自营（任意站点）。

    Args:
        seller_id: 商家 ID

    Returns:
        True 表示自营（US=0 或 CA=5000）
    """
    return seller_id in YAMI_SELLER_IDS


def is_third_party_seller(seller_id: int, business_type: int) -> bool:
    """
    判断商品是否为真正的第三方商品（排除 CA 站自营）。

    规则：business_type 为 3 或 6，且 seller_id 不在自营集合中。

    Args:
        seller_id: 商家 ID
        business_type: 商品业务类型

    Returns:
        True 表示第三方
    """
    return (business_type == 3 or business_type == 6) and not is_yami_seller(seller_id)
