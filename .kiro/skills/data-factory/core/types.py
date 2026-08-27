# -*- coding: utf-8 -*-
"""
类型定义模块。

统一定义项目中使用的类型别名和 TypedDict，提供类型安全支持。

类型分类:
    - 基础类型别名: Environment, ItemNumber, OrderSn 等
    - 验证结果: CheckItem, ValidationResult
    - Action 返回: ActionResult
    - 业务实体: UserInfo, OrderInfo, ItemInfo 等
    - API 响应: ApiResponse

Example:
    from core.types import ActionResult, UserInfo
    
    def get_user(email: str) -> ActionResult:
        user: UserInfo = {"user_id": 1, "email": email}
        return {"success": True, "data": user}
"""

from typing import Any, List, Optional, Union

from typing_extensions import TypedDict


# ==================== 基础类型别名 ====================

#: 环境类型 ("UAT" | "GQC" | "DEV")
Environment = str

#: 商品编号
ItemNumber = str

#: 订单号
OrderSn = str

#: 用户ID
UserId = int

#: 金额（美元）
Amount = float

#: 积分
Points = int


# ==================== 验证结果 ====================

class CheckItem(TypedDict):
    """单个验证项结果。"""
    field: str
    expected: Any
    actual: Any
    ok: bool


class ValidationResult(TypedDict):
    """验证结果汇总。"""
    passed: bool
    checks: List[CheckItem]
    failed_checks: List[CheckItem]
    suggestion: str


# ==================== Action 返回结果 ====================

class ActionResult(TypedDict, total=False):
    """
    Action 函数统一返回格式。
    
    所有 action 函数应返回此类型，确保输出格式一致。
    """
    success: bool
    env: str
    action: str
    data: dict
    validation: ValidationResult
    error: str  # 仅失败时存在
    elapsed: float


# ==================== 用户相关 ====================

class UserInfo(TypedDict, total=False):
    """用户信息。"""
    user_id: int
    email: str
    token: str
    pay_points: int
    giftcard_balance: float
    is_validated: int
    is_phone_validated: int
    is_api_validated: int
    recent_order_sns: List[str]


class RegisterResult(TypedDict):
    """注册结果。"""
    email: str
    pwd: str
    user_id: str
    token: str


# ==================== 订单相关 ====================

class OrderInfo(TypedDict, total=False):
    """订单信息。"""
    order_id: int
    order_sn: str
    purchase_id: int
    user_id: int
    order_status: int
    pay_status: int
    shipping_status: int
    order_amount: float
    add_time: int


class PlaceOrderData(TypedDict, total=False):
    """下单返回数据。"""
    email: str
    order_sns: List[str]
    purchase_id: int
    order_amount: float
    item_numbers: List[str]
    case_id: Union[int, str]
    wh: str
    zipcode: str
    use_giftcard: bool
    use_points: bool
    coupon_code: str


# ==================== 商品相关 ====================

class ItemInfo(TypedDict, total=False):
    """商品信息。"""
    item_number: str
    goods_id: int
    goods_name: str
    shop_price: float
    market_price: float
    goods_number: int  # 库存
    is_on_sale: int
    is_delete: int


class StockInfo(TypedDict):
    """库存信息。"""
    item_number: str
    warehouse: str
    stock: int
    available: int


# ==================== 促销相关 ====================

class PromotionInfo(TypedDict, total=False):
    """促销活动信息。"""
    ps_id: int
    ps_name: str
    ps_type: int
    start_time: int
    end_time: int
    status: int


class CouponInfo(TypedDict, total=False):
    """优惠券信息。"""
    ps_id: int
    coupon_code: str
    ps_code: str
    discount: float
    min_order: float
    start_time: int
    end_time: int


# ==================== 地址相关 ====================

class AddressInfo(TypedDict, total=False):
    """地址信息。"""
    address_id: int
    firstname: str
    lastname: str
    address1: str
    address2: str
    city: str
    state: str
    zipcode: str
    country: str
    phone: str
    is_primary: int


# ==================== 支付相关 ====================

class CardProfile(TypedDict, total=False):
    """信用卡信息。"""
    profile_id: str
    tail: str
    head: str
    card_type: str
    exp_year: str
    exp_month: str


# ==================== API 响应 ====================

class ApiResponse(TypedDict, total=False):
    """API 响应格式。"""
    messageId: str
    message: str
    zhError: str
    body: Any
