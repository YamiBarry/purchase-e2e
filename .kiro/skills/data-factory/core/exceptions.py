# -*- coding: utf-8 -*-
"""
自定义异常类模块。

定义造数据工具中使用的业务异常，避免直接使用 sys.exit()。

Example:
    from core.exceptions import UserNotFoundError, ConfigError
    
    if not user:
        raise UserNotFoundError(f"user_id {user_id} 不存在")
"""


class DataFactoryError(Exception):
    """造数据工具基础异常类"""
    def __init__(self, message: str = None, details: dict = None):
        self.details = details or {}
        super().__init__(message or "操作失败")


# ==================== 用户相关异常 ====================

class UserError(DataFactoryError):
    """用户相关异常基类"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class UserNotFoundError(UserError):
    """用户不存在异常"""
    def __init__(self, identifier: str = None, by: str = "email", details: dict = None):
        self.identifier = identifier
        self.by = by
        if identifier:
            msg = f"用户不存在: {by}={identifier}"
        else:
            msg = "用户不存在"
        super().__init__(msg, details)


class UserLoginError(UserError):
    """用户登录失败异常"""
    def __init__(self, email: str = None, reason: str = None, details: dict = None):
        self.email = email
        self.reason = reason
        msg = "用户登录失败"
        if email:
            msg += f" [{email}]"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, details)


class UserRegisterError(UserError):
    """用户注册失败异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "用户注册失败", details)


# ==================== 订单相关异常 ====================

class OrderError(DataFactoryError):
    """订单相关异常基类"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class OrderNotFoundError(OrderError):
    """订单不存在异常"""
    def __init__(self, identifier: str = None, by: str = "order_id", details: dict = None):
        self.identifier = identifier
        self.by = by
        if identifier:
            msg = f"订单不存在: {by}={identifier}"
        else:
            msg = "订单不存在"
        super().__init__(msg, details)


class OrderStatusError(OrderError):
    """订单状态异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "订单状态异常", details)


class CartError(OrderError):
    """购物车异常"""
    def __init__(self, action: str = None, reason: str = None, item_number: str = None, details: dict = None):
        self.action = action
        self.reason = reason
        self.item_number = item_number
        msg = "购物车操作失败"
        if action:
            msg = f"{action}失败"
        if item_number:
            msg += f" [{item_number}]"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, details)


class CheckoutError(OrderError):
    """结算异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "结算失败", details)


class PaymentError(OrderError):
    """支付异常"""
    def __init__(self, message: str = None, order_id: str = None, step: str = None, details: dict = None):
        self.order_id = order_id
        self.step = step
        msg = message or "支付失败"
        if order_id:
            msg += f" [订单: {order_id}]"
        if step:
            msg += f" [步骤: {step}]"
        super().__init__(msg, details)


# ==================== 商品相关异常 ====================

class ItemError(DataFactoryError):
    """商品相关异常基类"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class ItemNotFoundError(ItemError):
    """商品不存在异常"""
    def __init__(self, item_number: str = None, details: dict = None):
        self.item_number = item_number
        if item_number:
            msg = f"商品不存在: {item_number}"
        else:
            msg = "商品不存在"
        super().__init__(msg, details)


class ItemStockError(ItemError):
    """商品库存异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "商品库存异常", details)


class ItemStatusError(ItemError):
    """商品状态异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "商品状态异常", details)


# ==================== 促销相关异常 ====================

class PromotionError(DataFactoryError):
    """促销相关异常基类"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class PromotionNotFoundError(PromotionError):
    """促销活动不存在异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "促销活动不存在", details)


class PromotionCreateError(PromotionError):
    """促销活动创建失败异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "促销活动创建失败", details)


class CouponError(PromotionError):
    """优惠券异常"""
    def __init__(self, action: str = None, reason: str = None, coupon_code: str = None, details: dict = None):
        self.action = action
        self.reason = reason
        self.coupon_code = coupon_code
        msg = "优惠券操作失败"
        if action:
            msg = f"优惠券{action}失败"
        if coupon_code:
            msg += f" [{coupon_code}]"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, details)


# ==================== 资金相关异常 ====================

class BalanceError(DataFactoryError):
    """资金相关异常基类"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class GiftcardError(BalanceError):
    """礼卡异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "礼卡操作失败", details)


class PointsError(BalanceError):
    """积分异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "积分操作失败", details)


# ==================== API 相关异常 ====================

class ApiError(DataFactoryError):
    """API 调用失败异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class ApiRequestError(ApiError):
    """API 请求异常"""
    def __init__(self, endpoint: str = None, status_code: int = None, error_msg: str = None, details: dict = None):
        self.endpoint = endpoint
        self.status_code = status_code
        self.error_msg = error_msg
        msg = "API 请求失败"
        if endpoint:
            msg = f"API 请求失败 [{endpoint}]"
        if status_code:
            msg += f" (状态码: {status_code})"
        if error_msg:
            msg += f": {error_msg}"
        super().__init__(msg, details)


class ApiTimeoutError(ApiError):
    """API 超时异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "API 请求超时", details)


class AuthError(ApiError):
    """认证异常"""
    def __init__(self, message: str = None, token_type: str = None, details: dict = None):
        self.token_type = token_type
        msg = message or "认证失败"
        if token_type:
            msg += f" [类型: {token_type}]"
        super().__init__(msg, details)


# ==================== 数据库相关异常 ====================

class DatabaseError(DataFactoryError):
    """数据库相关异常基类"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message, details)


class DatabaseConnectionError(DatabaseError):
    """数据库连接异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "数据库连接失败", details)


class DatabaseQueryError(DatabaseError):
    """数据库查询异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "数据库查询失败", details)


# ==================== 验证相关异常 ====================

class ValidationError(DataFactoryError):
    """数据验证失败异常"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "数据验证失败", details)


class ConfigError(DataFactoryError):
    """配置错误异常（如缺少必需参数）"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message or "配置错误", details)
