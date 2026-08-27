# -*- coding: utf-8 -*-
"""
Core 模块
提供 HTTP 客户端、数据库客户端、认证、日志、异常、类型等基础设施
"""

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.logger import (
    print_result, output,
    debug, info, warn, error,
    LogLevel, set_log_level, set_log_to_file, get_log_level,
)
from core.constants import (
    OrderStatus, ShippingStatus, PayStatus, AbnormalStatus, CardStatus,
    PromotionType, DiscountType, ItemStatus,
    CouponType, CouponDiscountType,
    RmaType, RmaStatus, TrackingStatusType,
    CancelReason, CancelSubReason,
    ApiCode,
)
from core.utils import (
    get_timestamp, get_timestamp_ms,
    format_datetime, parse_datetime,
    safe_int, safe_float, truncate_str,
    build_in_clause,
    build_error_result, build_success_result,
    wait_for_condition, wait_for_db_condition,
)
from core.mkt_api import MktApiClient
from core.exceptions import (
    DataFactoryError,
    # 用户
    UserError, UserNotFoundError, UserLoginError, UserRegisterError,
    # 订单
    OrderError, OrderNotFoundError, OrderStatusError,
    CartError, CheckoutError, PaymentError,
    # 商品
    ItemError, ItemNotFoundError, ItemStockError, ItemStatusError,
    # 促销
    PromotionError, PromotionNotFoundError, PromotionCreateError, CouponError,
    # 资金
    BalanceError, GiftcardError, PointsError,
    # API
    ApiError, ApiRequestError, ApiTimeoutError, AuthError,
    # 数据库
    DatabaseError, DatabaseConnectionError, DatabaseQueryError,
    # 验证
    ValidationError, ConfigError,
)
from core.types import (
    Environment, ItemNumber, OrderSn, UserId, Amount, Points,
    CheckItem, ValidationResult, ActionResult,
    UserInfo, RegisterResult,
    OrderInfo, PlaceOrderData,
    ItemInfo, StockInfo,
    PromotionInfo, CouponInfo,
    AddressInfo, CardProfile,
    ApiResponse,
)

__all__ = [
    # 客户端
    "HttpClient",
    "DbClient",
    "MktApiClient",
    # 认证
    "_get_hub_token",
    # 日志
    "print_result", "output",
    "debug", "info", "warn", "error",
    "LogLevel", "set_log_level", "set_log_to_file", "get_log_level",
    # 常量枚举
    "OrderStatus", "ShippingStatus", "PayStatus", "AbnormalStatus", "CardStatus",
    "PromotionType", "DiscountType", "ItemStatus",
    "CouponType", "CouponDiscountType",
    "RmaType", "RmaStatus", "TrackingStatusType",
    "CancelReason", "CancelSubReason",
    "ApiCode",
    # 工具函数
    "get_timestamp", "get_timestamp_ms",
    "format_datetime", "parse_datetime",
    "safe_int", "safe_float", "truncate_str",
    "build_in_clause",
    "build_error_result", "build_success_result",
    "wait_for_condition", "wait_for_db_condition",
    # 异常类
    "DataFactoryError",
    "UserError", "UserNotFoundError", "UserLoginError", "UserRegisterError",
    "OrderError", "OrderNotFoundError", "OrderStatusError",
    "CartError", "CheckoutError", "PaymentError",
    "ItemError", "ItemNotFoundError", "ItemStockError", "ItemStatusError",
    "PromotionError", "PromotionNotFoundError", "PromotionCreateError", "CouponError",
    "BalanceError", "GiftcardError", "PointsError",
    "ApiError", "ApiRequestError", "ApiTimeoutError", "AuthError",
    "DatabaseError", "DatabaseConnectionError", "DatabaseQueryError",
    "ValidationError", "ConfigError",
    # 类型定义
    "Environment", "ItemNumber", "OrderSn", "UserId", "Amount", "Points",
    "CheckItem", "ValidationResult", "ActionResult",
    "UserInfo", "RegisterResult",
    "OrderInfo", "PlaceOrderData",
    "ItemInfo", "StockInfo",
    "PromotionInfo", "CouponInfo",
    "AddressInfo", "CardProfile",
    "ApiResponse",
]
