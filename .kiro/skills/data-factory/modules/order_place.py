# -*- coding: utf-8 -*-
"""
订单模块
支持所有冒烟下单用例类型，参考 smoke-order-test/smoke_order.py

用例类型：
  1a 全国可售共享库存（购物车仓下单）  1b 对仓下单  1c 购物车仓无货
  1  全国可售自营  2 本地化
  3  大区  3b 大区对仓
  4  大区共享购物车仓  4b 大区共享对仓  4c 大区共享无货
  5  自营预售  6a FBY共享购物车仓  6b FBY共享对仓  6c FBY共享无货
  6  FBY  7 第三方直邮  8 第三方预售  10 第三方礼券  9 虚拟礼卡

默认：1仓（91789）全国可售自营（用例 1）
"""

import json
import time
import sys
import os
from typing import Dict, List, Optional, Union

from core.http_client import HttpClient
from core.db import DbClient
from core.constants import CardStatus
from core.types import ActionResult, AddressInfo, ValidationResult
from core.exceptions import (
    CartError,
    CheckoutError,
    PaymentError,
    ItemNotFoundError,
    UserNotFoundError,
    AuthError,
    CouponError,
)
from validators.order_validator import validate_paid_order
from config import STRIPE_PUBLISHABLE_KEY, PAYMENT_ZIP, REQUEST_TIMEOUT, VALIDATION_WAIT

# 引用 smoke-order-test 的商品查询 SQL
_SMOKE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "smoke-order-test")
if _SMOKE_DIR not in sys.path:
    sys.path.insert(0, _SMOKE_DIR)

# 仓库 zipcode 映射
WH_ZIPCODE_MAP = {"001": "91789", "002": "04001"}

# 两仓地址模板
_WH_ADDRESS_TEMPLATES: Dict[str, Dict[str, Union[str, int, None]]] = {
    "001": {
        "firstname": "LA", "lastname": "Wh", "address1": "1000 S Stimson Ave",
        "address2": "", "city": "City of Industry", "state": "CA",
        "zipcode": "91789", "country": "United States", "phone": "6261234567",
        "verified": 0, "verify_time": None, "is_primary": 0,
    },
    "002": {
        "firstname": "NJ", "lastname": "Wh", "address1": "66 Main St",
        "address2": "", "city": "Kittery", "state": "ME",
        "zipcode": "04001", "country": "United States", "phone": "2071234567",
        "verified": 0, "verify_time": None, "is_primary": 0,
    },
}


# ==================== 信用卡管理 ====================

def _get_user_default_address(client: HttpClient) -> Dict[str, Union[str, int]]:
    """
    查用户地址列表，返回默认地址
    
    Args:
        client: HTTP 客户端
    
    Returns:
        默认地址字典（is_primary=1 优先，否则取第一个），无地址返回空字典
    """
    status, resp = client.get("/ec-customer/address")
    if status == 200 and isinstance(resp.get("body"), list):
        addrs = resp["body"]
        if addrs:
            for addr in addrs:
                if addr.get("is_primary") == 1:
                    return addr
            return addrs[0]
    return {}


def _get_profile_id(client: HttpClient, db: DbClient = None, user_id: int = None) -> Optional[str]:
    """
    获取 4242 测试卡 profile_id
    
    优先查数据库（yamibuy_payment.payment_profile_card），没有则调接口添加。
    注意：status=60 表示有效，status=0 表示已删除
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端（可选）
        user_id: 用户ID（可选，配合 db 使用）
    
    Returns:
        profile_id 字符串，获取失败返回 None
    """
    # 先查 DB（只查有效的卡）
    if db and user_id:
        row = db.query_one(
            f"SELECT profile_id FROM yamibuy_payment.payment_profile_card WHERE user_id = %s AND tail = '4242' AND status = {CardStatus.ACTIVE} AND card_source = 2 LIMIT 1",
            (user_id,)
        )
        if row:
            return row["profile_id"]

    # DB 没有有效的，再查接口确认（接口只返回有效的卡）
    status, resp = client.get("/ec-payment/card_stripe/profiles")
    if status == 200 and resp.get("body"):
        profiles = resp["body"]
        if isinstance(profiles, list):
            for p in profiles:
                if str(p.get("tail", "")) == "4242":
                    return p.get("profile_id")

    # 都没有有效的 4242 卡，添加新卡
    return _add_test_card(client)


def _add_test_card(client: HttpClient) -> str:
    """
    给账号添加 4242424242424242 Stripe 测试卡
    
    账单地址使用用户已有的默认地址。
    流程：
    1. 查用户默认地址（用于账单地址）
    2. GET /ec-payment/card_stripe/card-secret → 获取 setup_intent client_secret
    3. Stripe API confirm SetupIntent（绑定 pm_card_visa）
    4. POST /ec-payment/card_stripe/profile → 保存卡
    
    Args:
        client: HTTP 客户端
    
    Returns:
        profile_id 字符串
    
    Raises:
        AuthError: 用户没有收货地址
        PaymentError: 获取 card-secret 失败、Stripe 确认失败、保存卡失败
    """
    # Step 1: 查用户默认地址
    addr = _get_user_default_address(client)
    if not addr:
        raise AuthError("用户没有收货地址，请先添加地址再绑卡", token_type="address")

    # Step 2: 获取 setup_intent client_secret
    status, resp = client.get("/ec-payment/card_stripe/card-secret")
    if not client.is_success(status, resp):
        raise PaymentError(f"获取 card-secret 失败: {client.get_error(resp)}", step="card-secret")
    body = resp.get("body", {})
    si_id = body.get("set_id") or body.get("setup_intent_id") or body.get("si_id")
    client_secret = body.get("client_secret")
    if not si_id or not client_secret:
        raise PaymentError(f"未获到 setup_intent_id/client_secret: {body}", step="card-secret")

    # Step 3: Stripe confirm SetupIntent（pm_card_visa = 4242 测试卡）
    stripe_url = f"https://api.stripe.com/v1/setup_intents/{si_id}/confirm"
    confirm_data = f"payment_method=pm_card_visa&client_secret={client_secret}"
    stripe_headers = {
        "Authorization": f"Bearer {STRIPE_PUBLISHABLE_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    stripe_status_code, stripe_resp = client.post_raw(stripe_url, confirm_data, stripe_headers, timeout=REQUEST_TIMEOUT)
    if stripe_status_code >= 400:
        raise PaymentError(f"Stripe confirm SetupIntent 失败: {str(stripe_resp)[:200]}", step="stripe-confirm")

    pm_id = stripe_resp.get("payment_method")
    if not pm_id:
        raise PaymentError(f"Stripe 未返回 payment_method: {stripe_resp}", step="stripe-confirm")

    # Step 4: 保存卡，账单地址用用户默认地址
    profile_body = {
        "pm_id": pm_id,
        "tail": "4242",
        "head": "424242",
        "exp_year": "2030",
        "exp_month": "12",
        "firstname": addr.get("firstname", "QA"),
        "lastname": addr.get("lastname", "Test"),
        "card_type": "Visa",
        "account_num": "4242424242424242",
        "origin_account_num": "4242424242424242",
        "address_id": addr.get("address_id"),
        "address": {
            "firstname": addr.get("firstname", "QA"),
            "lastname": addr.get("lastname", "Test"),
            "address1": addr.get("address1", ""),
            "address2": addr.get("address2", ""),
            "city": addr.get("city", ""),
            "state": addr.get("state", ""),
            "zipcode": addr.get("zipcode", ""),
            "country": addr.get("country", "United States"),
            "phone": addr.get("phone", ""),
        },
    }
    status, resp = client.post("/ec-payment/card_stripe/profile", body=profile_body)
    if not client.is_success(status, resp):
        # 可能卡已存在，再查一次（只返回有效的卡，status != 0）
        status2, resp2 = client.get("/ec-payment/card_stripe/profiles")
        if status2 == 200 and resp2.get("body"):
            for p in resp2["body"]:
                # 只匹配有效的 4242 卡（status=60 或接口不返回已删除的卡）
                if str(p.get("tail", "")) == "4242" and p.get("status") != 0:
                    return p.get("profile_id")
        raise PaymentError(f"保存卡失败: {client.get_error(resp)}", step="save-profile")

    body = resp.get("body", {})
    profile_id = body.get("profile_id") if isinstance(body, dict) else None
    if not profile_id:
        status, resp = client.get("/ec-payment/card_stripe/profiles")
        if status == 200 and resp.get("body"):
            for p in resp["body"]:
                # 只匹配有效的 4242 卡
                if str(p.get("tail", "")) == "4242" and p.get("status") != 0:
                    return p.get("profile_id")
    if not profile_id:
        raise PaymentError("添加卡成功但未获取到 profile_id", step="save-profile")
    return profile_id


def _get_pm_id(client: HttpClient, profile_id: str) -> Optional[str]:
    """
    从 profile 获取 Stripe pm_id（备用，当前支付直接用 pm_card_visa）
    
    Args:
        client: HTTP 客户端
        profile_id: 卡 profile_id
    
    Returns:
        pm_id 字符串，获取失败返回 None
    """
    status, resp = client.get(f"/ec-payment/card_stripe/profile?profile_id={profile_id}")
    if status == 200 and resp.get("body"):
        return resp["body"].get("pm_id")
    return None


# ==================== 地址管理 ====================

def _ensure_address(client: HttpClient, email: str, wh_number: str = "001",
                    zipcode_override: str = None) -> Dict[str, Union[int, str]]:
    """
    确保指定仓库的地址存在
    
    Args:
        client: HTTP 客户端
        email: 用户邮箱
        wh_number: 仓库编号（"001" 或 "002"）
        zipcode_override: 自定义 zipcode（可选）
    
    Returns:
        {"address_id": int, "zipcode": str}
    
    Raises:
        AuthError: 创建地址失败
    """
    template = _WH_ADDRESS_TEMPLATES[wh_number]
    zipcode = zipcode_override or template["zipcode"]

    status, resp = client.get("/ec-customer/address")
    if status == 200 and isinstance(resp.get("body"), list):
        for addr in resp["body"]:
            if addr.get("zipcode") == zipcode:
                return {"address_id": addr["address_id"], "zipcode": zipcode}

    body = dict(template)
    body["zipcode"] = zipcode
    body["email"] = email
    status, resp = client.post("/ec-customer/address", body=body)
    if client.is_success(status, resp):
        return {"address_id": resp["body"]["address_id"], "zipcode": zipcode}
    raise AuthError(f"创建地址失败: {client.get_error(resp)}", token_type="address")


# ==================== 购物车 ====================

def _clear_cart(client: HttpClient) -> None:
    """
    清空购物车
    
    Args:
        client: HTTP 客户端
    """
    status, resp = client.get("/ec-so/cart", extra_headers={"source_flag": "1"})
    if status != 200:
        return
    body = resp.get("body", {})
    if not isinstance(body, dict):
        return
    item_numbers = []
    for seller in body.get("normal_items", []):
        for item in seller.get("items", []):
            num = item.get("item_number")
            if num and num not in item_numbers:
                item_numbers.append(num)
    for item in body.get("error_items", []):
        num = item.get("item_number")
        if num and num not in item_numbers:
            item_numbers.append(num)
    if item_numbers:
        client.delete("/ec-so/cart", body=item_numbers, extra_headers={"source_flag": "1"})


def _add_to_cart(client: HttpClient, item_number: str, qty: int) -> None:
    """
    添加商品到购物车
    
    Args:
        client: HTTP 客户端
        item_number: 商品编号
        qty: 数量
    
    Raises:
        CartError: 加购失败
    """
    status, resp = client.post(
        "/ec-so/cart",
        body=[{"item_number": item_number, "qty": qty, "check_status": 1}],
    )
    body = resp.get("body", {})
    failed = body.get("failed_items", []) if isinstance(body, dict) else []
    if status != 200 or failed:
        err = failed[0].get("reason", str(failed[0])) if failed else client.get_error(resp)
        raise CartError("加购", err, item_number)


def _set_cart_zipcode(client: HttpClient, zipcode: str) -> None:
    """
    设置购物车 zipcode
    
    Args:
        client: HTTP 客户端
        zipcode: 邮编
    """
    client.put("/ec-customer/zipcode", body={"zipcode": zipcode, "country": "United States"})


def _convert_coupon(client: HttpClient, ps_code: str) -> bool:
    """
    兑换优惠券到购物车
    
    调用 /ec-so/cart/coupon/convert/{ps_code} 接口
    
    Args:
        client: HTTP 客户端
        ps_code: 优惠券兑换码
    
    Returns:
        是否兑换成功
    """
    status, resp = client.post(
        f"/ec-so/cart/coupon/convert/{ps_code}?group_coupon=best",
        body={},
        extra_headers={"source_flag": "1", "y_platform": "H5"},
    )
    if client.is_success(status, resp):
        return True
    # 如果已经兑换过，也算成功
    error_msg = client.get_error(resp)
    if "已领取" in error_msg or "already" in error_msg.lower():
        return True
    return False


# ==================== 支付 ====================

def _free_pay(client: HttpClient, purchase_id: Union[int, str], checkout_amount: float) -> None:
    """
    免费支付流程（礼卡/积分全额抵扣时使用）
    
    当订单金额为 0 时，调用 /ec-payment/free/charge 接口完成订单。
    
    Args:
        client: HTTP 客户端
        purchase_id: 订单 purchase_id
        checkout_amount: 支付金额（应为 0）
    
    Raises:
        PaymentError: 支付失败
    """
    import hashlib
    
    def get_secret(purchase_id_str: str) -> str:
        """生成 secret，与服务端 PaymentUtil.getSecret 逻辑一致"""
        # Step 1: MD5(purchase_id)
        md5_purchase_id = hashlib.md5(purchase_id_str.encode('utf-8')).hexdigest()
        # Step 2: MD5(md5_purchase_id + "secret")
        secret_string = md5_purchase_id + "secret"
        return hashlib.md5(secret_string.encode('utf-8')).hexdigest()
    
    secret = get_secret(str(purchase_id))
    
    status, resp = client.post(
        "/ec-payment/free/charge?flow_version=1.0",
        body={
            "purchase_id": str(purchase_id),
            "amount": checkout_amount,
            "currency": "USD",
            "secret": secret,
        },
        extra_headers={"channel": "1", "y_platform": "pc", "y_version": "1"},
    )
    if not client.is_success(status, resp):
        raise PaymentError(f"免费支付失败: {client.get_error(resp)}", str(purchase_id), "free_charge")


def _pay(client: HttpClient, purchase_id: Union[int, str], checkout_amount: float, profile_id: str) -> None:
    """
    Stripe 支付流程（复用 smoke-order-test 逻辑）
    
    Args:
        client: HTTP 客户端
        purchase_id: 订单 purchase_id
        checkout_amount: 支付金额
        profile_id: 卡 profile_id
    
    Raises:
        PaymentError: 支付失败
    """
    # Step 1: enroll
    status, resp = client.post(
        "/ec-payment/card_stripe/enroll?flow_version=1.0",
        body={"purchase_id": str(purchase_id), "profile_id": profile_id,
              "currency": "USD", "version": 1, "zipcode": PAYMENT_ZIP,
              "amount": checkout_amount},
        extra_headers={"channel": "1", "y_platform": "pc", "y_version": "1"},
    )
    if not client.is_success(status, resp):
        raise PaymentError(f"enroll 失败: {client.get_error(resp)}", str(purchase_id), "enroll")
    body = resp["body"]
    pi_id = body.get("pi_id")
    client_secret = body.get("client_secret")
    if not pi_id or not client_secret:
        raise PaymentError(f"未获到 pi_id/client_secret: {body}", str(purchase_id), "enroll")

    # Step 2: Stripe confirm（直接用 pm_card_visa 测试卡 token）
    stripe_url = f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm"
    stripe_data = f"payment_method=pm_card_visa&client_secret={client_secret}"
    stripe_headers = {
        "Authorization": f"Bearer {STRIPE_PUBLISHABLE_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    stripe_status_code, stripe_resp = client.post_raw(stripe_url, stripe_data, stripe_headers, timeout=REQUEST_TIMEOUT)
    stripe_status = stripe_resp.get("status")

    # Step 3: 通知服务端
    status, resp = client.post(
        "/ec-payment/card_stripe/paymentIntent?flow_version=1.0",
        body={"piId": pi_id, "code": stripe_status or "succeeded"},
    )
    if not client.is_success(status, resp):
        raise PaymentError(f"支付处理失败: {client.get_error(resp)}", str(purchase_id), "paymentIntent")


# ==================== 下单核心 ====================

def _build_vendor_list(checkout_body: dict) -> List[dict]:
    """
    构建 vendor_list 参数
    
    Args:
        checkout_body: checkout 接口返回的 body
    
    Returns:
        vendor_list 列表
    """
    vendor_list = []
    for seller in checkout_body.get("seller_item_list", []):
        sl = seller.get("shipping_list", [])
        shipping_id = seller.get("shipping_id") or (sl[0].get("shipping_id") or sl[0].get("id") if sl else None)
        vendor_list.append({
            "vendor_id": seller.get("seller_id") or 0,
            "shipping_id": shipping_id,
            "seller_sn": seller.get("seller_sn", ""),
        })
    return vendor_list


def _build_group_list(checkout_body: dict) -> List[dict]:
    """
    构建 group_list 参数
    
    Args:
        checkout_body: checkout 接口返回的 body
    
    Returns:
        group_list 列表
    """
    group_list = []
    for seller in checkout_body.get("seller_item_list", []):
        sl = seller.get("shipping_list", [])
        shipping_id = seller.get("shipping_id") or (sl[0].get("shipping_id") or sl[0].get("id") if sl else None)
        group_list.append({"group_id": seller.get("group_id"), "shipping_id": shipping_id})
    return group_list


def _build_item_list(checkout_body: dict) -> List[dict]:
    """
    构建 item_list 参数
    
    Args:
        checkout_body: checkout 接口返回的 body
    
    Returns:
        item_list 列表
    """
    item_list = []
    for seller in checkout_body.get("seller_item_list", []):
        for item in seller.get("item_list", []):
            item_list.append({"item_number": item.get("item_number"),
                               "qty": item.get("qty", 1), "is_gift": item.get("is_gift", 0)})
    return item_list


def _query_item_from_smoke(case_id: Union[int, str], env: str, wh_number: str = "001", 
                           zipcode: str = None) -> Optional[str]:
    """
    从 smoke-order-test 的 QUERIES 里查商品
    
    Args:
        case_id: 用例ID
        env: 环境
        wh_number: 仓库编号
        zipcode: 邮编（可选）
    
    Returns:
        商品编号，查询失败返回 None
    
    Raises:
        ItemNotFoundError: 查询商品失败
    """
    try:
        from fetch_items import QUERIES, DB_CONFIGS, DB_CONFIG as _DEFAULT_DB
        import mysql.connector
        wh_alt = "002" if wh_number == "001" else "001"
        wh_zip = zipcode or WH_ZIPCODE_MAP.get(wh_number, "91789")
        db_cfg = DB_CONFIGS.get(env, _DEFAULT_DB)
        conn = mysql.connector.connect(**db_cfg)
        info = QUERIES.get(case_id)
        if not info:
            return None
        cursor = conn.cursor()
        cursor.execute(info["sql"].strip().format(
            warehouse=wh_number, zipcode=wh_zip, wh_main=wh_number, wh_alt=wh_alt))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return str(row[0]) if row else None
    except Exception as e:
        raise ItemNotFoundError(f"用例 [{case_id}]: {e}")


def _place_egift_order(client: HttpClient, item_number: str, email: str,
                       profile_id: str, db: DbClient) -> Dict[str, Union[str, int, float]]:
    """
    虚拟礼卡下单（用例 9）
    
    Args:
        client: HTTP 客户端
        item_number: 商品编号
        email: 用户邮箱
        profile_id: 卡 profile_id
        db: 数据库客户端
    
    Returns:
        {"order_sn": str, "purchase_id": int, "amount": float}
    
    Raises:
        ItemNotFoundError: 未查到 goods_id
        CheckoutError: 结算失败
        PaymentError: 支付失败
    """
    # 查 goods_id
    row = db.query_one(
        "SELECT goods_id FROM yamibuy_im.im_item WHERE item_number = %s LIMIT 1",
        (item_number,)
    )
    if not row:
        raise ItemNotFoundError(item_number)
    goods_id = row["goods_id"]

    checkout_params = {
        "is_en_site": 1, "language": "zh_CN", "currency": "USD",
        "business_unit": 0, "order_type": 1, "source_flag": 2,
        "group_coupon": "best", "is_use_point": 0, "is_use_giftcard": 0,
        "vendor_list": [{"seller_sn": 0, "receive_type": 1, "receive_emails": email}],
        "item_list": [{"item_number": item_number, "goods_id": goods_id,
                       "seller_sn": 0, "item_type": 7, "qty": 1}],
    }
    status, resp = client.post("/ec-so/orders/checkout/virtual", body=checkout_params,
                               extra_headers={"source_flag": "2", "y_platform": "pc"})
    if not client.is_success(status, resp) or not isinstance(resp.get("body"), dict):
        raise CheckoutError(f"虚拟订单结算失败: {client.get_error(resp)}")

    checkout_body = resp["body"]
    checkout_amount = checkout_body.get("total_order_amount") or checkout_body.get("total_amount", 0)

    order_body = {
        "is_en_site": 1, "language": "zh_CN", "currency": "USD",
        "business_unit": 0, "order_type": 1, "source_flag": 2,
        "pay_id": 4, "pay_type": 2, "is_use_point": 0, "is_use_giftcard": 0,
        "checkout_amount": checkout_amount, "profile_id": profile_id,
        "flow_version": "1.0",
        "vendor_list": [{"seller_sn": 0, "receive_type": 1, "receive_emails": email}],
        "item_list": [{"item_number": item_number, "goods_id": goods_id,
                       "seller_sn": 0, "item_type": 7, "qty": 1}],
        "group_list": _build_group_list(checkout_body),
    }
    status, resp = client.post("/ec-so/orders/submit/virtual?flow_version=1.0",
                               body=order_body, extra_headers={"source_flag": "2", "y_platform": "pc"})
    if not client.is_success(status, resp) or not isinstance(resp.get("body"), dict):
        raise CheckoutError(f"提交虚拟订单失败: {client.get_error(resp)}")

    body = resp["body"]
    purchase_id = body.get("purchase_id") or body.get("purchaseId")
    orders = body.get("orders") or []
    order_sn = orders[0].get("order_sn") if orders else str(purchase_id)
    _pay(client, purchase_id, checkout_amount, profile_id)
    return {"order_sn": order_sn, "purchase_id": purchase_id, "amount": checkout_amount}


def action_place_order(client: HttpClient, db: DbClient, env: str,
                       email: str,
                       case_id: Union[int, str] = 1,
                       wh_number: str = "001",
                       zipcode_override: str = None,
                       use_giftcard: bool = False,
                       use_points: bool = False,
                       coupon_code: str = None,
                       item_numbers: List[str] = None,
                       qty: int = 1,
                       count: int = 1) -> List[ActionResult]:
    """
    完整下单流程，支持所有冒烟用例类型、多商品、多订单
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        case_id: 用例ID，默认1(全国可售自营)
            支持: 1, 1a, 1b, 1c, 2, 3, 3b, 4, 4b, 4c, 5, 6, 6a, 6b, 6c, 7, 8, 9, 10
        wh_number: 仓库编号，默认 "001"
        zipcode_override: 自定义 zipcode（可选）
        use_giftcard: 是否使用礼卡，默认 False
        use_points: 是否使用积分，默认 False
        coupon_code: 优惠券兑换码（可选）
        item_numbers: 商品列表（多个商品放入同一个订单），支持两种格式：
            - 字符串列表: ["1001", "1002"]（每个商品数量用 qty 参数统一控制）
            - 字典列表: [{"item_number": "1001", "qty": 2}, {"item_number": "1002", "qty": 1}]（每个商品单独指定数量）
            不指定则自动查
        qty: 统一购买数量，当 item_numbers 为字符串列表时生效，默认 1
        count: 下单次数（每次独立下单），默认 1
    
    Returns:
        ActionResult 列表
    """
    results = []
    start_total = time.time()

    try:
        # 对仓用例
        other_wh = "002" if wh_number == "001" else "001"
        is_other_wh_case = str(case_id) in {"1b", "3b", "4b", "6b"}

        # 确保地址存在
        wh_address = _ensure_address(client, email, wh_number, zipcode_override)
        other_wh_address = _ensure_address(client, email, other_wh)

        # 设置购物车 zipcode
        wh_zipcode = zipcode_override or WH_ZIPCODE_MAP.get(wh_number, "91789")
        _set_cart_zipcode(client, wh_zipcode)

        # 确保有 4242 测试卡（先查 DB，没有再添加）
        user_row = db.query_one(
            "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1", (email,)
        )
        user_id = user_row["user_id"] if user_row else None
        profile_id = _get_profile_id(client, db, user_id)
        if not profile_id:
            raise PaymentError("无法获取或添加 4242 测试卡", step="get_profile")

        # 解析 item_numbers，统一为 [{"item_number": str, "qty": int}, ...] 格式
        if not item_numbers:
            item_number = _query_item_from_smoke(case_id, env, wh_number,
                                                  zipcode_override or wh_zipcode)
            if not item_number:
                raise ItemNotFoundError(f"用例 [{case_id}] 的商品，请检查测试环境库存")
            item_list_with_qty = [{"item_number": item_number, "qty": qty}]
        else:
            item_list_with_qty = []
            for entry in item_numbers:
                if isinstance(entry, dict):
                    item_list_with_qty.append({
                        "item_number": str(entry["item_number"]),
                        "qty": int(entry.get("qty", qty)),
                    })
                else:
                    item_list_with_qty.append({"item_number": str(entry), "qty": qty})

        # 保持向后兼容：item_numbers 仍为字符串列表，供后续引用
        item_numbers = [e["item_number"] for e in item_list_with_qty]

        address_id = other_wh_address["address_id"] if is_other_wh_case else wh_address["address_id"]

        for i in range(count):
            start = time.time()
            try:
                # 虚拟礼卡走独立流程（只支持单商品）
                if case_id == 9 or str(case_id) == "9":
                    result = _place_egift_order(client, item_list_with_qty[0]["item_number"], email, profile_id, db)
                    time.sleep(VALIDATION_WAIT)
                    validation = validate_paid_order(db, result["purchase_id"])
                    sub_orders = db.query_all(
                        "SELECT order_sn FROM yamibuy_master.xysc_order_info WHERE purchase_id = %s AND is_separate = 0",
                        (result["purchase_id"],)
                    )
                    order_sns = [r["order_sn"] for r in sub_orders] if sub_orders else [result["order_sn"]]
                    results.append({
                        "success": validation["passed"], "env": env, "action": "place_order",
                        "data": {
                            "email": email,
                            "order_sns": order_sns,
                            "purchase_id": result["purchase_id"],
                            "order_amount": result["amount"],
                            "item_numbers": item_numbers,
                            "case_id": case_id, "wh": wh_number,
                        },
                        "validation": validation, "elapsed": time.time() - start,
                    })
                    continue

                # 普通下单：清购物车，加购所有商品
                _clear_cart(client)
                for entry in item_list_with_qty:
                    _add_to_cart(client, entry["item_number"], entry["qty"])

                # 如果传入了 coupon_code（实际是 ps_code 兑换码），在 checkout 之前兑换优惠券
                if coupon_code:
                    _convert_coupon(client, coupon_code)

                # 结算
                checkout_item_list = [
                    {"item_number": e["item_number"], "qty": e["qty"], "item_type": 1, "is_gift": 0}
                    for e in item_list_with_qty
                ]
                checkout_body_req = {
                    "user_address_id": address_id,
                    "source_flag": 1, "pay_id": 4,
                    "is_use_point": 1 if use_points else 0,
                    "is_use_giftcard": 1 if use_giftcard else 0,
                    "language": "zh_CN", "business_unit": 1, "order_type": 0, "currency": "USD",
                    "group_coupon": "best",  # 自动选择最优优惠券组合
                    "item_list": checkout_item_list,
                }

                status, resp = client.post(
                    "/ec-so/orders/checkout/physical/v2", body=checkout_body_req,
                    extra_headers={"source_flag": "1", "y_platform": "H5"},
                )
                if not client.is_success(status, resp) or not isinstance(resp.get("body"), dict):
                    raise CheckoutError(client.get_error(resp))

                checkout_body = resp["body"]
                # 注意：当礼卡全额抵扣时，total_order_amount = 0.0，不能用 or 判断
                checkout_amount = checkout_body.get("total_order_amount")
                if checkout_amount is None:
                    checkout_amount = checkout_body.get("total_amount", 0)
                # 当使用礼卡全额抵扣时，settlement_amount 为 0
                settlement_amount = checkout_amount

                # 提交订单
                order_body = {
                    "user_address_id": address_id,
                    "pay_id": 4, "pay_type": 2, "source_flag": 1,
                    "is_use_point": 1 if use_points else 0,
                    "is_use_giftcard": 1 if use_giftcard else 0,
                    "language": "zh_CN", "business_unit": 1, "order_type": 0, "currency": "USD",
                    "checkout_amount": checkout_amount, 
                    "settlement_amount": settlement_amount,  # 结算金额（信用卡支付金额）
                    "profile_id": profile_id,
                    "flow_version": "1.0",
                    "group_coupon": "best",  # 自动选择最优优惠券组合
                    "item_list": _build_item_list(checkout_body),
                    "vendor_list": _build_vendor_list(checkout_body),
                    "group_list": _build_group_list(checkout_body),
                }

                status, resp = client.post(
                    "/ec-so/orders/submit/physical/v2?flow_version=1.0", body=order_body,
                    extra_headers={"source_flag": "1", "y_platform": "H5"},
                )
                if not client.is_success(status, resp) or not isinstance(resp.get("body"), dict):
                    body_val = resp.get("body")
                    if isinstance(body_val, list) and body_val:
                        err = body_val[0].get("reason") or body_val[0].get("reason_en") or str(body_val)[:100]
                    else:
                        err = client.get_error(resp)
                    raise CheckoutError(f"提交订单失败: {err}")

                body = resp["body"]
                purchase_id = body.get("purchase_id") or body.get("purchaseId")
                orders = body.get("orders") or []
                order_sn = orders[0].get("order_sn") if orders else str(purchase_id)

                # 支付
                if checkout_amount > 0:
                    # 信用卡支付
                    _pay(client, purchase_id, checkout_amount, profile_id)
                else:
                    # 免费支付（礼卡/积分全额抵扣）
                    _free_pay(client, purchase_id, checkout_amount)

                time.sleep(VALIDATION_WAIT)
                validation = validate_paid_order(db, purchase_id)

                # 查 purchase_id 下所有子单（is_separate=0）
                sub_orders = db.query_all(
                    "SELECT order_sn FROM yamibuy_master.xysc_order_info WHERE purchase_id = %s AND is_separate = 0",
                    (purchase_id,)
                )
                order_sns = [r["order_sn"] for r in sub_orders] if sub_orders else [order_sn]

                results.append({
                    "success": validation["passed"], "env": env, "action": "place_order",
                    "data": {
                        "email": email,
                        "purchase_id": purchase_id,
                        "sub_order_count": len(order_sns),
                        "order_sns": order_sns,
                        "order_amount": checkout_amount,
                        "item_numbers": item_numbers,
                        "qty_per_item": qty,
                        "case_id": case_id, "wh": wh_number, "zipcode": wh_zipcode,
                        "use_giftcard": use_giftcard, "use_points": use_points,
                        "coupon_code": coupon_code or "",
                    },
                    "validation": validation, "elapsed": time.time() - start,
                })

            except Exception as e:
                results.append({
                    "success": False, "env": env, "action": "place_order",
                    "data": {"email": email, "case_id": case_id, "count_index": i + 1},
                    "error": str(e), "elapsed": time.time() - start,
                })

    except Exception as e:
        results.append({
            "success": False, "env": env, "action": "place_order",
            "data": {}, "error": str(e), "elapsed": time.time() - start_total,
        })

    return results
