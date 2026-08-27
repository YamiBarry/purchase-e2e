#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亚米冒烟下单工具
支持 10 种商品类型的自动化下单测试，走完整下单+支付流程

用法：
    python smoke_order.py                    # 跑全部用例
    python smoke_order.py --case 1,3,5       # 只跑指定用例
    python smoke_order.py --case 10          # 只跑电子礼品卡
"""

import json
import os
import time
import argparse
import urllib.request
import urllib.error
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
from datetime import datetime

from config import ENV, ENV_CONFIG, TEST_ACCOUNT, PAYMENT_CONFIG, REQUEST_TIMEOUT, STRIPE_PUBLISHABLE_KEY
from test_cases import TEST_CASES
from fetch_items import QUERIES, DB_CONFIG


# ==================== 自动创建测试地址 ====================

# 两个仓的地址模板，key 与 WH_ZIPCODE_MAP 保持一致（"001"/"002"）
_WH_ADDRESS_TEMPLATES = {
    "001": {
        "firstname": "LA",
        "lastname": "Wh",
        "email": "renee01@yamibuy.com",
        "address1": "1000 S Stimson Ave",
        "address2": "",
        "city": "City of Industry",
        "state": "CA",
        "zipcode": "91789",
        "country": "United States",
        "phone": "6261234567",
        "verified": 0,
        "verify_time": None,
        "is_primary": 0,
    },
    "002": {
        "firstname": "NJ",
        "lastname": "Wh",
        "email": "renee01@yamibuy.com",
        "address1": "66 Main St",
        "address2": "",
        "city": "Kittery",
        "state": "ME",
        "zipcode": "04001",
        "country": "United States",
        "phone": "2071234567",
        "verified": 0,
        "verify_time": None,
        "is_primary": 0,
    },
}


# ==================== 动态查库刷新商品编号 ====================

# 仓库编号 → 默认 zipcode 映射（001=1仓LA，002=2仓NJ）
WH_ZIPCODE_MAP = {"001": "91789", "002": "04001"}


def _refresh_item_numbers(cases, wh_number="001", zipcode=None):
    """启动时从数据库动态查询各用例的 item_number，查不到则标记 no_data，连接失败则标记 db_error
    zipcode: 本地化商品 SQL 中使用的 zipcode，若不传则按 wh_number 推导默认值
    """
    wh_main = wh_number
    wh_alt = "002" if wh_number == "001" else "001"
    # zipcode 未指定时按 wh_number 推导默认值
    wh_zip_local = zipcode if zipcode else WH_ZIPCODE_MAP.get(wh_number, "91789")
    try:
        import mysql.connector
    except ImportError:
        print("  ⚠️  未安装 mysql-connector-python")
        for case in cases:
            case["db_error"] = True
        return

    print("  🔍 动态查询商品 item_number...")
    try:
        from fetch_items import DB_CONFIGS, DB_CONFIG as _DEFAULT_DB
        db_cfg = DB_CONFIGS.get(ENV, _DEFAULT_DB)
        conn = mysql.connector.connect(**db_cfg)
    except Exception as e:
        print(f"  ❌ 数据库连接失败: {e}")
        for case in cases:
            case["db_error"] = True
        return

    case_map = {c["id"]: c for c in cases}

    for case_id, info in QUERIES.items():
        if case_id not in case_map:
            continue
        try:
            cursor = conn.cursor()
            cursor.execute(info["sql"].strip().format(warehouse=wh_number, zipcode=wh_zip_local, wh_main=wh_main, wh_alt=wh_alt))
            row = cursor.fetchone()
            cursor.close()
            if row:
                item_number = str(row[0])
                goods_name = str(row[1])
                goods_img = str(row[2]) if len(row) > 2 and row[2] else ""
                case_map[case_id]["item_number"] = item_number
                case_map[case_id]["goods_img"] = goods_img
                print(f"    [{str(case_id).ljust(3)}] {info['name']}: {item_number}  ({goods_name[:30]})")
            else:
                case_map[case_id]["item_number"] = ""
                case_map[case_id]["no_data"] = True
                print(f"    [{str(case_id).ljust(3)}] {info['name']}: 查无商品数据")
        except Exception as e:
            case_map[case_id]["db_error"] = True
            print(f"    [{str(case_id).ljust(3)}] {info['name']}: 查询异常 {e}")

    conn.close()
    print()


EC_BASE = ENV_CONFIG[ENV]["ec_base"]


def _db_query(sql, params=None):
    """执行单条 SQL 查询，返回第一行结果，失败返回 None。动态按当前 ENV 选数据库"""
    try:
        import mysql.connector
        from fetch_items import DB_CONFIGS, DB_CONFIG as _DEFAULT_DB
        db_cfg = DB_CONFIGS.get(ENV, _DEFAULT_DB)
        conn = mysql.connector.connect(**db_cfg)
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception:
        return None

_token = None  # 全局 token 缓存


def _request(method, url, body=None, token=None, extra_headers=None):
    """发送 HTTP 请求，返回 (status_code, response_dict)"""
    headers = {
        "Content-Type": "application/json",
        "y_language": "zh_CN",
    }
    if token:
        headers["token"] = token
    if extra_headers:
        headers.update(extra_headers)

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}
    except Exception as e:
        return 0, {"error": str(e)}


def get(path, base=None, token=None, extra_headers=None):
    url = (base or EC_BASE) + path
    return _request("GET", url, token=token, extra_headers=extra_headers)


def post(path, body, base=None, token=None, extra_headers=None):
    url = (base or EC_BASE) + path
    return _request("POST", url, body=body, token=token, extra_headers=extra_headers)


def put(path, body, base=None, token=None, extra_headers=None):
    url = (base or EC_BASE) + path
    return _request("PUT", url, body=body, token=token, extra_headers=extra_headers)


def delete(path, body, base=None, token=None, extra_headers=None):
    url = (base or EC_BASE) + path
    return _request("DELETE", url, body=body, token=token, extra_headers=extra_headers)


# ==================== 地址管理 ====================

def _ensure_test_address(wh_number, token, zipcode_override=None):
    """确保指定仓库的测试地址存在，不存在则自动创建，返回 address_id 和 zipcode
    wh_number: "001" 或 "002"
    zipcode_override: 若指定则覆盖默认 zipcode（如 --wh 1:90001 时传入 90001）
    """
    template = _WH_ADDRESS_TEMPLATES[wh_number]
    zipcode = zipcode_override if zipcode_override else template["zipcode"]

    # 先查现有地址里有没有对应 zipcode 的
    status, resp = get("/ec-customer/address", token=token)
    if status == 200 and isinstance(resp.get("body"), list):
        for addr in resp["body"]:
            if addr.get("zipcode") == zipcode:
                print(f"  📍 {wh_number}仓地址已存在: address_id={addr['address_id']} zipcode={zipcode}")
                return {"address_id": addr["address_id"], "zipcode": zipcode}

    # 不存在则创建（使用模板，但覆盖 zipcode 和 email）
    create_body = dict(template)
    create_body["zipcode"] = zipcode
    create_body["email"] = TEST_ACCOUNT["email"]
    print(f"  📍 {wh_number}仓地址不存在，自动创建（zipcode={zipcode}）...")
    status, resp = post("/ec-customer/address", body=create_body, token=token)
    if status == 200 and resp.get("messageId") in ("200", "10000"):
        body = resp.get("body", {})
        address_id = body.get("address_id") if isinstance(body, dict) else None
        if address_id:
            print(f"  ✅ 创建成功: address_id={address_id}")
            return {"address_id": address_id, "zipcode": zipcode}
    raise RuntimeError(f"创建{wh_number}仓地址失败: {resp.get('zhError', str(resp)[:100])}")


# ==================== 登录 ====================

def login():
    """登录获取 token，带缓存"""
    global _token
    if _token:
        return _token

    status, resp = get("/ec-customer/users/get_token")
    if status != 200 or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"获取匿名 token 失败: {resp}")
    anon_token = resp["body"]["token"]

    status, resp = post(
        "/ec-customer/users/login",
        body={"email": TEST_ACCOUNT["email"], "pwd": TEST_ACCOUNT["pwd"]},
        token=anon_token,
    )
    if status != 200 or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"登录失败: {resp}")

    _token = resp["body"]["token"]
    uid = resp["body"].get("uid", "")
    print(f"  🔑 登录成功 [{ENV}] uid={uid}")
    return _token


# ==================== 购物车操作 ====================

def _delete_cart_items(item_numbers, token):
    """DELETE /ec-so/cart body 是 item_number 列表"""
    delete("/ec-so/cart", body=item_numbers, token=token, extra_headers={"source_flag": "1"})


def clear_cart(token):
    """清空购物车，处理 normal_items（seller 分组）和 error_items（扁平列表）"""
    status, resp = get("/ec-so/cart", token=token, extra_headers={"source_flag": "1"})
    if status != 200:
        return
    body = resp.get("body", {})
    if not isinstance(body, dict):
        return
    item_numbers = []

    # normal_items: 按 seller 分组，每组下有 items 数组
    for seller in body.get("normal_items", []):
        for item in seller.get("items", []):
            num = item.get("item_number")
            if num and num not in item_numbers:
                item_numbers.append(num)

    # error_items: 扁平数组，直接有 item_number
    for item in body.get("error_items", []):
        num = item.get("item_number")
        if num and num not in item_numbers:
            item_numbers.append(num)

    if item_numbers:
        _delete_cart_items(item_numbers, token)


def add_to_cart(item_number, qty, token):
    """加购商品 POST /ec-so/cart"""
    return post(
        "/ec-so/cart",
        body=[{"item_number": item_number, "qty": qty, "check_status": 1}],
        token=token,
    )


def set_cart_zipcode(zipcode, token):
    """设置购物车 zipcode，影响配送方式匹配 PUT /ec-customer/zipcode"""
    status, resp = put(
        "/ec-customer/zipcode",
        body={"zipcode": zipcode, "country": "United States"},
        token=token,
    )
    if status == 200 and resp.get("messageId") in ("200", "10000"):
        print(f"  📮 购物车 zipcode 已设置为 {zipcode}")
    else:
        print(f"  ⚠️  设置购物车 zipcode 失败: {resp.get('zhError', str(resp)[:80])}")


# ==================== 结算 ====================

def get_checkout_info(address_id, item_number, qty, item_type, token):
    """获取结算页信息 POST /ec-so/orders/checkout/physical/v2"""
    body = {
        "user_address_id": address_id,
        "source_flag": 1,
        "pay_id": 4,
        "is_use_point": 0,
        "is_use_giftcard": 0,
        "language": "zh_CN",
        "business_unit": 1,
        "order_type": 0,
        "currency": "USD",
        "item_list": [{"item_number": item_number, "qty": qty, "item_type": item_type, "is_gift": 0}],
    }
    return post(
        "/ec-so/orders/checkout/physical/v2",
        body=body,
        token=token,
        extra_headers={"source_flag": "1", "y_platform": "H5"},
    )



# ==================== 支付 ====================

def get_user_card_profile(token):
    """获取用户已保存的 4242 测试卡 profile_id（tail=4242）"""
    status, resp = get("/ec-payment/card_stripe/profiles", token=token)
    if status == 200 and resp.get("body"):
        profiles = resp["body"]
        if isinstance(profiles, list):
            # 优先找 tail=4242 的测试卡
            for p in profiles:
                if str(p.get("tail", "")) == "4242":
                    return p.get("profile_id")
            # 没有 4242 则取第一张
            if profiles:
                return profiles[0].get("profile_id")
    return None


def _get_user_default_address(token):
    """查用户地址列表，返回默认地址（is_primary=1 优先，否则取第一个）"""
    status, resp = get("/ec-customer/address", token=token)
    if status == 200 and isinstance(resp.get("body"), list):
        addrs = resp["body"]
        if addrs:
            for addr in addrs:
                if addr.get("is_primary") == 1:
                    return addr
            return addrs[0]
    return {}


def _ensure_4242_card(token):
    """
    确保账号有 4242 测试卡，没有则自动添加。
    先查 DB，再查接口，都没有则添加。
    账单地址使用用户默认地址。
    """
    # 先查接口（DB 查询需要额外依赖，接口查询更简单）
    status, resp = get("/ec-payment/card_stripe/profiles", token=token)
    if status == 200 and resp.get("body"):
        profiles = resp["body"]
        if isinstance(profiles, list):
            for p in profiles:
                if str(p.get("tail", "")) == "4242":
                    print(f"  💳 4242 测试卡已存在: profile_id={p.get('profile_id')}")
                    return p.get("profile_id")

    # 没有 4242 卡，自动添加
    print("  💳 未找到 4242 测试卡，自动添加...")

    # 查用户默认地址（用于账单地址）
    addr = _get_user_default_address(token)
    if not addr:
        print("  ⚠️  用户没有收货地址，无法添加信用卡")
        return None

    # 获取 setup_intent client_secret
    status, resp = get("/ec-payment/card_stripe/card-secret", token=token)
    if status != 200 or resp.get("messageId") not in ("200", "10000"):
        print(f"  ⚠️  获取 card-secret 失败: {resp.get('zhError', str(resp)[:80])}")
        return None
    body = resp.get("body") or {}
    si_id = body.get("set_id") or body.get("setup_intent_id") or body.get("si_id")
    client_secret = body.get("client_secret")
    if not si_id or not client_secret:
        print(f"  ⚠️  未获到 setup_intent_id/client_secret: {body}")
        return None

    # Stripe confirm SetupIntent（pm_card_visa = 4242 测试卡）
    stripe_url = f"https://api.stripe.com/v1/setup_intents/{si_id}/confirm"
    confirm_data = f"payment_method=pm_card_visa&client_secret={client_secret}".encode("utf-8")
    req = urllib.request.Request(
        stripe_url, data=confirm_data,
        headers={"Authorization": f"Bearer {STRIPE_PUBLISHABLE_KEY}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
            stripe_resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  ⚠️  Stripe confirm SetupIntent 失败: {e.read().decode()[:100]}")
        return None

    pm_id = stripe_resp.get("payment_method")
    if not pm_id:
        print(f"  ⚠️  Stripe 未返回 payment_method: {stripe_resp}")
        return None

    # 保存卡，账单地址用用户默认地址
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
    status, resp = post("/ec-payment/card_stripe/profile", body=profile_body, token=token)
    if status == 200 and resp.get("messageId") in ("200", "10000"):
        profile_id = resp.get("body", {}).get("profile_id") if isinstance(resp.get("body"), dict) else None
        if not profile_id:
            # 再查一次
            status2, resp2 = get("/ec-payment/card_stripe/profiles", token=token)
            if status2 == 200 and resp2.get("body"):
                for p in resp2["body"]:
                    if str(p.get("tail", "")) == "4242":
                        profile_id = p.get("profile_id")
                        break
        print(f"  ✅ 4242 测试卡添加成功: profile_id={profile_id}")
        return profile_id
    else:
        # 可能卡已存在，再查一次
        status2, resp2 = get("/ec-payment/card_stripe/profiles", token=token)
        if status2 == 200 and resp2.get("body"):
            for p in resp2["body"]:
                if str(p.get("tail", "")) == "4242":
                    print(f"  💳 4242 测试卡已存在（重查）: profile_id={p.get('profile_id')}")
                    return p.get("profile_id")
        print(f"  ⚠️  添加 4242 测试卡失败: {resp.get('zhError', str(resp)[:80])}")
        return None


def _get_pm_id_from_profile(profile_id, token):
    """从 profile 获取 Stripe pm_id"""
    status, resp = get(
        f"/ec-payment/card_stripe/profile?profile_id={profile_id}",
        token=token,
    )
    if status == 200 and resp.get("body"):
        return resp["body"].get("pm_id")
    return None


def _pay_order(order_sn, purchase_id, checkout_amount, token, profile_id=None):
    """发起支付
    流程：
    1. 调 enroll 创建 PaymentIntent
    2. 用 Stripe API confirm PaymentIntent（绑定支付方式，4242 卡无需 3DS）
    3. 调 paymentIntent 接口处理支付结果
    """
    # 若未传入 profile_id，则动态获取
    if not profile_id:
        profile_id = get_user_card_profile(token)
    if not profile_id:
        return {"success": False, "message": "未找到可用的信用卡 profile"}

    # Step 1: enroll 创建 PaymentIntent
    pay_body = {
        "purchase_id": str(purchase_id),
        "profile_id": profile_id,
        "currency": "USD",
        "version": 1,
        "zipcode": PAYMENT_CONFIG["zip"],
        "amount": checkout_amount,
    }
    status, resp = post(
        "/ec-payment/card_stripe/enroll?flow_version=1.0",
        body=pay_body,
        token=token,
        extra_headers={"channel": "1", "y_platform": "pc", "y_version": "1"},
    )
    if status != 200 or resp.get("messageId") not in ("200", "10000"):
        return {"success": False, "message": f"enroll 失败: {resp.get('message', str(resp)[:100])}"}

    body = resp.get("body", {})
    pi_id = body.get("pi_id")
    client_secret = body.get("client_secret")
    if not pi_id or not client_secret:
        return {"success": False, "message": f"未获到 pi_id/client_secret: {body}"}

    # Step 2: Stripe confirm PaymentIntent（直接用 pm_card_visa 测试卡 token）
    stripe_confirm_url = f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm"
    confirm_body = f"payment_method=pm_card_visa&client_secret={client_secret}"
    req = urllib.request.Request(
        stripe_confirm_url,
        data=confirm_body.encode("utf-8"),
        headers={
            "Authorization": f"Bearer {STRIPE_PUBLISHABLE_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
            stripe_resp = json.loads(r.read().decode("utf-8"))
            stripe_status = stripe_resp.get("status")
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        return {"success": False, "message": f"Stripe confirm 失败: {err[:100]}"}

    # Step 3: 通知服务端支付结果
    status, resp = post(
        "/ec-payment/card_stripe/paymentIntent?flow_version=1.0",
        body={"piId": pi_id, "code": stripe_status or "succeeded"},
        token=token,
    )
    if status != 200 or resp.get("messageId") not in ("200", "10000"):
        return {"success": False, "message": f"支付处理失败: {resp.get('message', str(resp)[:100])}"}
    return {"success": True}


# ==================== 下单核心流程 ====================

def _build_item_list(checkout_body):
    """从结算响应构建 item_list"""
    item_list = []
    for seller in checkout_body.get("seller_item_list", []):
        for item in seller.get("item_list", []):
            item_list.append({
                "item_number": item.get("item_number"),
                "qty": item.get("qty", 1),
                "is_gift": item.get("is_gift", 0),
            })
    return item_list


def _build_group_list(checkout_body):
    """从结算响应构建 group_list（submitV2 校验字段）"""
    group_list = []
    for seller in checkout_body.get("seller_item_list", []):
        group_id = seller.get("group_id")
        shipping_id = seller.get("shipping_id")
        if not shipping_id:
            sl = seller.get("shipping_list", [])
            if sl:
                shipping_id = sl[0].get("shipping_id") or sl[0].get("id")
        group_list.append({"group_id": group_id, "shipping_id": shipping_id})
    return group_list


def _build_vendor_list(checkout_body):
    """从结算响应构建 vendor_list"""
    vendor_list = []
    for seller in checkout_body.get("seller_item_list", []):
        vendor_id = seller.get("seller_id")
        shipping_id = seller.get("shipping_id")
        if not shipping_id:
            sl = seller.get("shipping_list", [])
            if sl:
                shipping_id = sl[0].get("shipping_id") or sl[0].get("id")
        vendor_list.append({
            "vendor_id": vendor_id if vendor_id is not None else 0,
            "shipping_id": shipping_id,
            "seller_sn": seller.get("seller_sn", ""),
        })
    return vendor_list


def _submit_normal_order(checkout_body, address_id, checkout_amount, profile_id, token):
    """提交普通订单 POST /ec-so/orders/submit/physical/v2?flow_version=1.0"""
    order_body = {
        "user_address_id": address_id,
        "pay_id": 4,
        "pay_type": 2,  # 2=stripe
        "source_flag": 1,
        "is_use_point": 0,
        "is_use_giftcard": 0,
        "language": "zh_CN",
        "business_unit": 1,
        "order_type": 0,
        "currency": "USD",
        "checkout_amount": checkout_amount,
        "profile_id": profile_id,
        "flow_version": "1.0",
        "item_list": _build_item_list(checkout_body),
        "vendor_list": _build_vendor_list(checkout_body),
        "group_list": _build_group_list(checkout_body),
    }
    status, resp = post(
        "/ec-so/orders/submit/physical/v2?flow_version=1.0",
        body=order_body,
        token=token,
        extra_headers={"source_flag": "1", "y_platform": "H5"},
    )
    if status != 200 or not isinstance(resp.get("body"), dict):
        body_val = resp.get("body")
        if isinstance(body_val, list) and body_val:
            # 商品级别错误，提取 reason 字段
            err = body_val[0].get("reason") or body_val[0].get("reason_en") or str(body_val)[:100]
        elif isinstance(body_val, str):
            err = body_val
        else:
            err = resp.get("message", str(resp)[:100])
        return {"success": False, "message": f"提交订单失败: {err}"}
    body = resp["body"]
    purchase_id = body.get("purchase_id") or body.get("purchaseId")
    # order_sn 在 orders 列表里，格式如 2026033164300
    orders = body.get("orders") or []
    order_sn = orders[0].get("order_sn") if orders else str(purchase_id)
    return {"success": True, "order_sn": order_sn, "purchase_id": purchase_id}


def place_order(case, token, wh_address=None):
    """执行单个商品类型的完整下单流程，返回 (success, order_sn, purchase_id, message, elapsed)"""
    start = time.time()
    item_number = case["item_number"]
    qty = case["qty"]
    is_egift = case["item_type"] == 7

    expect_fail = case.get("expect_fail", False)
    expect_error = case.get("expect_error", "")

    # 商品数据异常时直接返回失败
    if case.get("db_error"):
        return False, None, None, "数据库连接失败，无法查询商品", 0.0
    if case.get("no_data") or not case.get("item_number"):
        return False, None, None, "未查到商品数据", 0.0

    try:
        # 电子礼品卡走独立流程，不能加购
        if is_egift:
            return _place_egift_order(case, token, start)

        # Step 1: 清空购物车
        clear_cart(token)

        # Step 2: 加购
        status, resp = add_to_cart(item_number, qty, token)
        body = resp.get("body", {})
        failed = body.get("failed_items", []) if isinstance(body, dict) else []
        if status != 200 or failed:
            err_msg = failed[0].get("reason", str(failed[0])) if failed else resp.get('message', str(resp))
            return False, None, None, f"加购失败: {err_msg}", time.time() - start

        # Step 3: 使用预置收货地址（由 --wh 参数决定，1仓/2仓）
        # address_id_override 允许单个用例覆盖默认地址（用于负向用例）
        address_id = case.get("address_id_override") or wh_address["address_id"]

        # Step 4: 结算
        status, resp = get_checkout_info(address_id, item_number, qty, case["item_type"], token)
        checkout_body = resp.get("body", {})
        if status != 200 or not isinstance(checkout_body, dict):
            err = checkout_body if isinstance(checkout_body, str) else resp.get('message', str(resp)[:100])
            return False, None, None, f"结算失败: {err}", time.time() - start

        checkout_amount = checkout_body.get("total_order_amount") or checkout_body.get("total_amount", 0)
        profile_id = get_user_card_profile(token)

        # Step 5: 提交订单
        order_result = _submit_normal_order(checkout_body, address_id, checkout_amount, profile_id, token)
        if not order_result["success"]:
            msg = order_result["message"]
            if expect_fail and expect_error and expect_error in msg:
                return True, None, None, f"预期失败（{expect_error}）✓", time.time() - start
            elif expect_fail:
                return False, None, None, f"预期失败但错误不匹配: {msg}", time.time() - start
            return False, None, None, msg, time.time() - start

        order_sn = order_result["order_sn"]
        purchase_id = order_result.get("purchase_id")

        # Step 6: 支付
        pay_result = _pay_order(order_sn, purchase_id, checkout_amount, token, profile_id)
        if not pay_result["success"]:
            return False, order_sn, purchase_id, f"下单成功但支付失败: {pay_result['message']}", time.time() - start

        if expect_fail:
            return False, order_sn, purchase_id, "预期应失败但下单成功", time.time() - start
        return True, order_sn, purchase_id, "成功", time.time() - start

    except Exception as e:
        return False, None, None, f"异常: {str(e)}", time.time() - start


def _get_egift_goods_id(item_number):
    """从数据库动态查询电子礼品卡的 goods_id"""
    row = _db_query(
        "SELECT goods_id FROM yamibuy_im.im_item WHERE item_number = %s LIMIT 1",
        (item_number,)
    )
    return row[0] if row else None


def _place_egift_order(case, token, start):
    """电子礼品卡独立下单流程
    不能加购，直接调 /ec-so/orders/checkout/virtual 结算
    参数格式参考前端代码 ItemInfoRight.tsx handleCheckout
    """
    item_number = case["item_number"]
    qty = case["qty"]

    # 从数据库动态查询 goods_id（避免硬编码）
    goods_id = _get_egift_goods_id(item_number)
    if not goods_id:
        return False, None, None, f"未查到 item_number={item_number} 对应的 goods_id", time.time() - start

    # 虚拟订单结算（对齐前端参数格式）
    checkout_params = {
        "is_en_site": 1,
        "language": "zh_CN",
        "currency": "USD",
        "business_unit": 0,
        "order_type": 1,
        "source_flag": 2,
        "group_coupon": "best",
        "is_use_point": 0,
        "is_use_giftcard": 0,
        "vendor_list": [{
            "seller_sn": 0,
            "receive_type": 1,  # 1=充値到账户
            "receive_emails": TEST_ACCOUNT["email"],
        }],
        "item_list": [{
            "item_number": item_number,
            "goods_id": goods_id,
            "seller_sn": 0,
            "item_type": 7,
            "qty": qty,
        }],
    }
    status, resp = post(
        "/ec-so/orders/checkout/virtual",
        body=checkout_params,
        token=token,
        extra_headers={"source_flag": "2", "y_platform": "pc"},
    )
    if status != 200 or resp.get("messageId") not in ("200", "10000"):
        err = resp.get("body") if isinstance(resp.get("body"), str) else resp.get('message', str(resp)[:100])
        return False, None, None, f"虚拟订单结算失败: {err}", time.time() - start

    checkout_body = resp.get("body", {})
    if not isinstance(checkout_body, dict):
        return False, None, None, f"结算响应异常: {checkout_body}", time.time() - start

    checkout_amount = checkout_body.get("total_order_amount") or checkout_body.get("total_amount", 0)
    profile_id = get_user_card_profile(token)

    # 提交虚拟订单
    order_body = {
        "is_en_site": 1,
        "language": "zh_CN",
        "currency": "USD",
        "business_unit": 0,
        "order_type": 1,
        "source_flag": 2,
        "pay_id": 4,
        "pay_type": 2,
        "is_use_point": 0,
        "is_use_giftcard": 0,
        "checkout_amount": checkout_amount,
        "profile_id": profile_id,
        "flow_version": "1.0",
        "vendor_list": [{
            "seller_sn": 0,
            "receive_type": 1,
            "receive_emails": TEST_ACCOUNT["email"],
        }],
        "item_list": [{
            "item_number": item_number,
            "goods_id": goods_id,
            "seller_sn": 0,
            "item_type": 7,
            "qty": qty,
        }],
        "group_list": _build_group_list(checkout_body),
    }
    status, resp = post(
        "/ec-so/orders/submit/virtual?flow_version=1.0",
        body=order_body,
        token=token,
        extra_headers={"source_flag": "2", "y_platform": "pc"},
    )
    if status != 200 or not isinstance(resp.get("body"), dict):
        err = resp.get("body") if isinstance(resp.get("body"), str) else resp.get('message', str(resp)[:100])
        return False, None, None, f"提交虚拟订单失败: {err}", time.time() - start

    body = resp["body"]
    purchase_id = body.get("purchase_id") or body.get("purchaseId")
    orders = body.get("orders") or []
    order_sn = orders[0].get("order_sn") if orders else str(purchase_id)

    # 支付（复用已查到的 profile_id，避免重复请求）
    pay_result = _pay_order(order_sn, purchase_id, checkout_amount, token, profile_id)
    if not pay_result["success"]:
        return False, order_sn, purchase_id, f"下单成功但支付失败: {pay_result['message']}", time.time() - start

    return True, order_sn, purchase_id, "成功", time.time() - start


def _query_order_info(purchase_id):
    """下单后查询订单的商品名称、购物车仓、下单仓"""
    row = _db_query("""
        SELECT og.goods_name, oi.cart_warehouse_number, oi.warehouse_number
        FROM yamibuy_master.xysc_order_info oi
        JOIN yamibuy_master.xysc_order_goods og ON oi.order_id = og.order_id
        WHERE oi.purchase_id = %s
        LIMIT 1
    """, (purchase_id,))
    if row:
        return {"goods_name": str(row[0]), "cart_wh": str(row[1] or ""), "order_wh": str(row[2] or "")}
    return {"goods_name": "", "cart_wh": "", "order_wh": ""}


# 需要购物车仓和下单仓不一致的用例
WH_DIFF_CASES = {"1b", "1c", "4b", "4c", "6b", "6c"}


def _check_warehouse(case_id, cart_wh, order_wh):
    """校验仓库是否符合预期，返回 (wh_ok, wh_msg)"""
    if not cart_wh or not order_wh:
        return True, ""  # 查不到仓库信息，不校验
    case_key = str(case_id)
    if case_key in WH_DIFF_CASES:
        ok = cart_wh != order_wh
        msg = "" if ok else f"预期购物车仓和下单仓不一致，实际都是 {order_wh}"
    else:
        ok = cart_wh == order_wh
        msg = "" if ok else f"预期购物车仓和下单仓一致，实际 cart={cart_wh} order={order_wh}"
    return ok, msg


# ==================== 主流程 ====================

def run(case_ids=None, warehouse="1", zipcode_override=None):
    """运行冒烟测试
    warehouse: '1' 或 '2'
    zipcode_override: 自定义 zipcode，覆盖该仓默认值（如 --wh 1:90001 时传入 '90001'）
    """
    print(f"\n{'='*60}")
    print(f"  亚米冒烟下单测试  [{ENV}]  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    cases = [c for c in TEST_CASES if c["enabled"]]
    if case_ids:
        cases = [c for c in cases if c["id"] in case_ids]

    if not cases:
        print("没有可运行的用例")
        return

    try:
        token = login()
    except RuntimeError as e:
        print(f"  ❌ 登录失败: {e}")
        return

    # 仓库编号（用于查库存和地址模板）
    wh_number = "001" if warehouse == "1" else "002"
    other_wh_number = next(k for k in WH_ZIPCODE_MAP if k != wh_number)

    # 确保主仓和对仓地址都存在，动态获取 address_id
    wh_address = _ensure_test_address(wh_number, token, zipcode_override=zipcode_override)
    other_wh_address = _ensure_test_address(other_wh_number, token)

    # 地址处理完后，确保账号有 4242 测试卡
    _ensure_4242_card(token)

    # test_cases.py 中用 "OTHER_WH" 作为占位符，运行时统一替换为对仓动态 address_id
    addr_other = other_wh_address["address_id"]
    for case in cases:
        override = case.get("address_id_override")
        if override is None:
            continue
        # 统一替换为对仓地址（"OTHER_WH" 占位符或旧的写死 id 均视为对仓）
        case["address_id_override"] = addr_other

    # 设置购物车 zipcode（所有 case 统一，由 --wh 参数决定）
    wh_zipcode = zipcode_override if zipcode_override else WH_ZIPCODE_MAP.get(wh_number, "91789")
    set_cart_zipcode(wh_zipcode, token)
    # 动态查库刷新 item_number（按指定仓库查库存）
    _refresh_item_numbers(cases, wh_number, zipcode=wh_zipcode)

    print()
    results = []

    # 负向用例从对应正向用例复制 item_number 和 goods_img
    case_map_by_id = {c["id"]: c for c in cases}
    if "1b" in case_map_by_id and "1a" in case_map_by_id:
        case_map_by_id["1b"]["item_number"] = case_map_by_id["1a"]["item_number"]
        case_map_by_id["1b"]["goods_img"] = case_map_by_id["1a"].get("goods_img", "")
    if "2b" in case_map_by_id and 2 in case_map_by_id:
        case_map_by_id["2b"]["item_number"] = case_map_by_id[2]["item_number"]
        case_map_by_id["2b"]["goods_img"] = case_map_by_id[2].get("goods_img", "")
    if "3b" in case_map_by_id and 3 in case_map_by_id:
        case_map_by_id["3b"]["item_number"] = case_map_by_id[3]["item_number"]
        case_map_by_id["3b"]["goods_img"] = case_map_by_id[3].get("goods_img", "")
    if "6b" in case_map_by_id and "6a" in case_map_by_id:
        case_map_by_id["6b"]["item_number"] = case_map_by_id["6a"]["item_number"]
        case_map_by_id["6b"]["goods_img"] = case_map_by_id["6a"].get("goods_img", "")
    if "4b" in case_map_by_id and 4 in case_map_by_id:
        case_map_by_id["4b"]["item_number"] = case_map_by_id[4]["item_number"]
        case_map_by_id["4b"]["goods_img"] = case_map_by_id[4].get("goods_img", "")

    for case in cases:
        print(f"  [{str(case['id']).ljust(3)}] {case['name']} (item: {case['item_number']})")
        success, order_sn, purchase_id, message, elapsed = place_order(case, token, wh_address)

        if success:
            print(f"       ✅ 成功  order_sn={order_sn}  purchase_id={purchase_id}  耗时 {elapsed:.1f}s")
            order_info = _query_order_info(purchase_id) if purchase_id else {"goods_name": "", "cart_wh": "", "order_wh": ""}
            wh_ok, wh_msg = _check_warehouse(case["id"], order_info["cart_wh"], order_info["order_wh"])
            if not wh_ok:
                print(f"       ⚠️  仓库校验失败: {wh_msg}")
        else:
            print(f"       ❌ 失败  {message}  耗时 {elapsed:.1f}s")
            order_info = {"goods_name": "", "cart_wh": "", "order_wh": ""}
            wh_ok, wh_msg = True, ""

        results.append({
            "id": case["id"],
            "name": case["name"],
            "item_number": case["item_number"],
            "goods_img": case.get("goods_img", ""),
            "goods_name": order_info["goods_name"],
            "cart_wh": order_info["cart_wh"],
            "order_wh": order_info["order_wh"],
            "wh_ok": wh_ok,
            "wh_msg": wh_msg,
            "success": success,
            "order_sn": order_sn,
            "purchase_id": purchase_id,
            "message": message,
            "elapsed": elapsed,
        })
        print()

    passed = sum(1 for r in results if r["success"] and r.get("wh_ok", True))
    total = len(results)
    print(f"{'='*60}")
    print(f"  结果: {passed}/{total} 通过")
    if passed < total:
        print(f"\n  失败用例:")
        for r in results:
            if not r["success"] or not r.get("wh_ok", True):
                reason = r["message"] if not r["success"] else r.get("wh_msg", "仓库校验失败")
                print(f"    [{str(r['id']).ljust(3)}] {r['name']}: {reason}")
    print(f"{'='*60}\n")

    # 生成 HTML 报告
    _generate_html_report(results, passed, total, wh_number, wh_zipcode)

    return results


def _generate_html_report(results, passed, total, wh_number="001", wh_zipcode="91789"):
    """Generate HTML test report"""
    now = datetime.now()
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report", f"report-{now.strftime('%Y%m%d-%H%M%S')}.html")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    now = now.strftime('%Y-%m-%d %H:%M:%S')

    rows = ""
    for idx, r in enumerate(results, 1):
        img_path = r.get("goods_img", "")
        img_url = f"https://cdn.yamibuy.net/{img_path}" if img_path else ""
        img_tag = f'<img src="{img_url}" style="width:60px;height:60px;object-fit:contain;">' if img_url else "-"
        status_icon = "✅" if r["success"] and r.get("wh_ok", True) else "❌"
        status_cls = "success" if r["success"] and r.get("wh_ok", True) else "fail"
        order_info = r["order_sn"] if r["order_sn"] else "-"
        purchase_info = str(r["purchase_id"]) if r["purchase_id"] else "-"
        msg = r["message"] if not r["success"] else "成功"
        if r.get("wh_msg"):
            msg = (msg + " | " + r["wh_msg"]).strip(" | ")
        rows += f"""
        <tr class="{status_cls}">
            <td>{idx}</td>
            <td>用例{r['id']}</td>
            <td>{r['name']}</td>
            <td class="img-cell">{img_tag}</td>
            <td class="goods-name">{r.get('goods_name', '')}</td>
            <td><code>{r['item_number']}</code></td>
            <td class="status">{status_icon}</td>
            <td><code>{order_info}</code></td>
            <td>{purchase_info}</td>
            <td>{r.get('cart_wh', '')}</td>
            <td>{r.get('order_wh', '')}</td>
            <td>{r['elapsed']:.1f}s</td>
            <td class="msg">{msg}</td>
        </tr>"""

    pass_rate = int(passed / total * 100) if total > 0 else 0
    color = "#4caf50" if passed == total else ("#ff9800" if passed > 0 else "#f44336")

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>亚米各种商品类型冒烟下单测试报告</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f5f5f5; color: #333; }}
  .header {{ background: #d32f2f; color: white; padding: 24px 32px; }}
  .header h1 {{ margin: 0; font-size: 22px; }}
  .header p {{ margin: 6px 0 0; opacity: .85; font-size: 14px; }}
  .summary {{ display: flex; gap: 16px; padding: 20px 32px; background: white; border-bottom: 1px solid #eee; }}
  .card {{ flex: 1; background: #fafafa; border-radius: 8px; padding: 16px 20px; text-align: center; border: 1px solid #eee; }}
  .card .num {{ font-size: 32px; font-weight: 700; color: {color}; }}
  .card .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
  .container {{ padding: 24px 32px; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  th {{ background: #f5f5f5; padding: 12px 16px; text-align: left; font-size: 13px; color: #666; border-bottom: 1px solid #eee; }}
  td {{ padding: 12px 16px; font-size: 14px; border-bottom: 1px solid #f0f0f0; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.success td.status {{ color: #4caf50; font-size: 16px; }}
  tr.fail td.status {{ color: #f44336; font-size: 16px; }}
  tr.fail {{ background: #fff8f8; }}
  td.msg {{ color: #888; font-size: 13px; max-width: 260px; word-break: break-all; }}
  code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #555; }}
  .env-tag {{ display: inline-block; background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px; }}
</style>
</head>
<body>
<div class="header">
  <h1>亚米各种商品类型冒烟下单测试报告 <span class="env-tag">{ENV}</span><span class="env-tag">{wh_number}仓 {wh_zipcode}</span></h1>
  <p>执行时间：{now} &nbsp;·&nbsp; 测试账号：{TEST_ACCOUNT['email']}</p>
</div>
<div class="summary">
  <div class="card"><div class="num">{total}</div><div class="label">总用例</div></div>
  <div class="card"><div class="num" style="color:#4caf50">{passed}</div><div class="label">通过</div></div>
  <div class="card"><div class="num" style="color:#f44336">{total-passed}</div><div class="label">失败</div></div>
  <div class="card"><div class="num">{pass_rate}%</div><div class="label">通过率</div></div>
</div>
<div class="container">
  <table>
    <thead>
      <tr>
        <th>序号</th><th>ID</th><th>商品类型</th><th>商品图片</th><th>商品名称</th><th>商品编号</th><th>状态</th><th>订单号</th><th>purchase_id</th><th>购物车仓</th><th>下单仓</th><th>耗时</th><th>备注</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</div>
</body>
</html>"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  📄 HTML 报告已生成: {report_path}")

    # 通知企微：调机器人 /send 接口推送结果
    _notify_wecom(passed, total, report_path)


def _upload_report(report_path: str) -> str:
    """上传 HTML 报告到 CDN，返回远程 URL，失败返回空字符串"""
    try:
        import uuid
        boundary = uuid.uuid4().hex
        with open(report_path, "rb") as f:
            file_data = f.read()
        file_name = os.path.basename(report_path)

        # 手动构造 multipart/form-data
        def field(name, value):
            return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()

        body = (
            field("type", "common") +
            field("channel", "Yamibuy") +
            field("local", "local") +
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\nContent-Type: text/html\r\n\r\n'.encode() +
            file_data +
            f'\r\n--{boundary}--\r\n'.encode()
        )

        req = urllib.request.Request(
            "https://rs.yamibuy.tech/resource/upload",
            data=body,
            headers={
                "token": "example-token",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            body_list = result.get("body", [])
            if body_list:
                url = body_list[0].get("url", "")
                print(f"  📤 报告已上传: {url}")
                return url
    except Exception as e:
        print(f"  ⚠️ 报告上传失败: {e}")
    return ""


def _notify_wecom(passed, total, report_path):
    """跑完后调机器人 /send 接口，主动推送结果给用户"""
    import urllib.request
    import json as _json

    chatid = os.getenv("SMOKE_NOTIFY_CHATID", "dm_renee.zhang")
    notify_url = os.getenv("SMOKE_NOTIFY_URL", "http://localhost:8900/send")

    # 上传报告到 CDN
    cdn_url = _upload_report(report_path)

    status = "✅ 全部通过" if passed == total else f"⚠️ {passed}/{total} 通过"
    if cdn_url:
        msg = f"冒烟下单测试完成 {status}（{passed}/{total}）\n报告链接：{cdn_url}"
    else:
        win_path = report_path
        msg = f"冒烟下单测试完成 {status}（{passed}/{total}）\n报告路径：{win_path}"

    payload = _json.dumps({"chatId": chatid, "content": msg}).encode("utf-8")
    req = urllib.request.Request(notify_url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"  📨 已通知企微 chatid={chatid}")
    except Exception as e:
        print(f"  ⚠️ 企微通知失败: {e}")


# ==================== 入口 ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="亚米冒烟下单测试")
    parser.add_argument("--case", type=str, default=None, help="指定用例 ID，逗号分隔，如 --case 1,3,5")
    parser.add_argument("--wh", type=str, default="1", help="仓库：1=1仓(91789) 2=2仓(04001)，可附加自定义 zipcode，如 --wh 1:90001")
    parser.add_argument("--env", type=str, default=None, help="切换环境：UAT / GQC / DEV，覆盖 config.py 中的 ENV")
    parser.add_argument("--email", type=str, default=None, help="覆盖测试账号邮箱")
    parser.add_argument("--pwd", type=str, default=None, help="覆盖测试账号密码")
    parser.add_argument("--notify-chatid", type=str, default=None, help="测试完成后通知的企微 chatid，如 dm_Phoebe.Song")
    args = parser.parse_args()

    # 切换环境
    if args.env:
        import config as _cfg
        _cfg.ENV = args.env.upper()
        ENV = _cfg.ENV
        EC_BASE = _cfg.ENV_CONFIG[ENV]["ec_base"]
        # 切换环境后同步更新账号为该环境默认账号
        TEST_ACCOUNT.update(_cfg.ENV_ACCOUNT.get(ENV, _cfg.ENV_ACCOUNT["UAT"]))

    # 覆盖账号
    if args.email:
        TEST_ACCOUNT["email"] = args.email
    if args.pwd:
        TEST_ACCOUNT["pwd"] = args.pwd

    # 设置通知 chatid（写入环境变量，供 _notify_wecom 读取）
    if args.notify_chatid:
        os.environ["SMOKE_NOTIFY_CHATID"] = args.notify_chatid

    case_ids = None
    if args.case:
        case_ids = []
        for x in args.case.split(","):
            x = x.strip()
            case_ids.append(int(x) if x.isdigit() else x)

    # 解析 --wh 参数，支持 "1" 或 "1:90001" 格式
    wh_raw = args.wh
    zipcode_override = None
    if ":" in wh_raw:
        warehouse, zipcode_override = wh_raw.split(":", 1)
        zipcode_override = zipcode_override.strip()
    else:
        warehouse = wh_raw

    run(case_ids=case_ids, warehouse=warehouse, zipcode_override=zipcode_override)
