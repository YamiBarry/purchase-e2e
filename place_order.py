#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yami 测试环境下单脚本（独立版）
================================
不依赖任何内部模块，只需标准库 + mysql-connector-python。

依赖安装：
    pip install mysql-connector-python

用法示例：
    # 最简单：用默认账号在 UAT 下单
    python place_order.py

    # 指定邮箱/环境
    python place_order.py --env UAT --email your@yamibuy.com --pwd 111111

    # 指定商品编号（多个用逗号分隔）
    python place_order.py --items 7750086,7750087

    # 指定商品 + 数量
    python place_order.py --items 7750086:2,7750087:1

    # 下多单
    python place_order.py --count 3

    # 使用礼卡/积分
    python place_order.py --use-giftcard --use-points

    # NJ仓（002）
    python place_order.py --wh 002

    # 完整示例
    python place_order.py --env UAT --email test@yamibuy.com --pwd 111111 --items 7750086 --wh 001 --count 2
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple, Union


# ============================================================
# 配置（按需修改）
# ============================================================

ENV_CONFIG = {
    "UAT": {
        "ec_base":      "https://uat-ecapi.yamibuy.tech",
        "central_base": "https://uat-centralapi.yamibuy.tech",
    },
    "GQC": {
        "ec_base":      "http://gqc-ecapi.yamibuy.tech",
        "central_base": "https://gqc-centralapi.yamibuy.tech",
    },
    "DEV": {
        "ec_base":      "https://dev-ecapi.yamibuy.tech",
        "central_base": "https://dev-centralapi.yamibuy.tech",
    },
}

DB_CONFIGS = {
    "UAT": {
        "host": "eks-uat-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306,
        "user": "yami",
        "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master",
        "connect_timeout": 10,
    },
    "GQC": {
        "host": "eks-gqc-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306,
        "user": "yami",
        "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master",
        "connect_timeout": 10,
    },
    "DEV": {
        "host": "eks-dev-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306,
        "user": "yami",
        "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master",
        "connect_timeout": 10,
    },
}

# 默认测试账号
DEFAULT_EMAIL    = "renee01@yamibuy.com"
DEFAULT_PASSWORD = "111111"

# Stripe 测试 Key（pk_test_*）
STRIPE_PUBLISHABLE_KEY = "pk_test_51Lzo0KA1KmcXQec8x6pOMeHMdRGaU04mRPTrTB13LeGpOfbKFWY8GB97Tb8A0IIwNnOfUTbOSY12RJjGBhdMJetJ00sfkkZOMI"

# 仓库映射
WH_ZIPCODE = {"001": "91789", "002": "04001"}

# 仓库地址模板（结算用）
WH_ADDRESS_TEMPLATES = {
    "001": {
        "firstname": "LA", "lastname": "Wh",
        "address1": "1000 S Stimson Ave", "address2": "",
        "city": "City of Industry", "state": "CA",
        "zipcode": "91789", "country": "United States",
        "phone": "6261234567", "verified": 0, "verify_time": None, "is_primary": 0,
    },
    "002": {
        "firstname": "NJ", "lastname": "Wh",
        "address1": "66 Main St", "address2": "",
        "city": "Kittery", "state": "ME",
        "zipcode": "04001", "country": "United States",
        "phone": "2071234567", "verified": 0, "verify_time": None, "is_primary": 0,
    },
}

REQUEST_TIMEOUT  = 30
VALIDATION_WAIT  = 3


# ============================================================
# HTTP 客户端（纯标准库）
# ============================================================

class HttpClient:
    def __init__(self, ec_base: str, token: Optional[str] = None):
        self.ec_base = ec_base
        self.token   = token

    def _request(self, method: str, path: str,
                 body=None, extra_headers: dict = None,
                 full_url: str = None, raw_body: bytes = None,
                 custom_headers: dict = None) -> Tuple[int, dict]:
        url = full_url or (self.ec_base + path)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            content_type = "application/json"
        elif raw_body is not None:
            data = raw_body
            content_type = "application/x-www-form-urlencoded"
        else:
            data = None
            content_type = "application/json"

        if custom_headers:
            headers = custom_headers
        else:
            headers = {
                "Content-Type":  content_type,
                "Accept":        "application/json",
                "source_flag":   "1",
                "y_platform":    "H5",
                "y_version":     "1",
                "y_language":    "zh_CN",
            }
            if self.token:
                headers["token"] = self.token
            if extra_headers:
                headers.update(extra_headers)

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                resp = json.loads(r.read().decode("utf-8"))
                return r.status, resp
        except urllib.error.HTTPError as e:
            try:
                resp = json.loads(e.read().decode("utf-8"))
            except Exception:
                resp = {"msg": str(e)}
            return e.code, resp
        except Exception as e:
            return 0, {"msg": str(e)}

    def get(self, path: str, extra_headers: dict = None) -> Tuple[int, dict]:
        return self._request("GET", path, extra_headers=extra_headers)

    def post(self, path: str, body=None, extra_headers: dict = None) -> Tuple[int, dict]:
        return self._request("POST", path, body=body, extra_headers=extra_headers)

    def post_raw(self, full_url: str, raw_body: str,
                 custom_headers: dict = None) -> Tuple[int, dict]:
        return self._request("POST", "", raw_body=raw_body.encode("utf-8"),
                             full_url=full_url, custom_headers=custom_headers)

    def put(self, path: str, body=None) -> Tuple[int, dict]:
        return self._request("PUT", path, body=body)

    def delete(self, path: str, body=None, extra_headers: dict = None) -> Tuple[int, dict]:
        return self._request("DELETE", path, body=body, extra_headers=extra_headers)

    @staticmethod
    def is_success(status: int, resp: dict) -> bool:
        if status not in (200, 201):
            return False
        code = resp.get("code") or resp.get("status")
        if code is not None and int(code) not in (0, 200, 201):
            return False
        return True

    @staticmethod
    def get_error(resp: dict) -> str:
        return (resp.get("msg") or resp.get("message") or
                resp.get("error") or str(resp)[:200])


# ============================================================
# 数据库（可选，用于查询 profile_id；查不到也能继续）
# ============================================================

def _db_query_one(cfg: dict, sql: str, params: tuple) -> Optional[dict]:
    """执行单行查询，失败返回 None（不报错）。"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(**cfg)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception:
        return None


def _db_query_all(cfg: dict, sql: str, params: tuple) -> List[dict]:
    """执行多行查询，失败返回空列表。"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(**cfg)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows or []
    except Exception:
        return []


# ============================================================
# 登录
# ============================================================

def login(client: HttpClient, email: str, pwd: str) -> str:
    """登录获取 token，返回 token 字符串。"""
    # Step 1: 获取匿名 token
    status, resp = client.get("/ec-customer/users/get_token")
    if status != 200 or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"获取匿名 token 失败: {HttpClient.get_error(resp)}")
    client.token = resp["body"]["token"]

    # Step 2: 登录
    status, resp = client.post("/ec-customer/users/login",
                               body={"email": email, "pwd": pwd},
                               extra_headers={"y_platform": "H5"})
    if not HttpClient.is_success(status, resp):
        raise RuntimeError(f"登录失败 [{email}]: {HttpClient.get_error(resp)}")
    body = resp.get("body") or {}
    token = body.get("token") if isinstance(body, dict) else None
    if not token:
        raise RuntimeError(f"登录成功但未获取到 token: {resp}")
    client.token = token
    return token


# ============================================================
# 地址管理
# ============================================================

def ensure_address(client: HttpClient, email: str, wh: str = "001",
                   zipcode_override: str = None) -> dict:
    """确保该仓库地址存在，返回 {address_id, zipcode}。"""
    template = WH_ADDRESS_TEMPLATES[wh]
    zipcode  = zipcode_override or template["zipcode"]

    status, resp = client.get("/ec-customer/address")
    if status == 200 and isinstance(resp.get("body"), list):
        for addr in resp["body"]:
            if addr.get("zipcode") == zipcode:
                return {"address_id": addr["address_id"], "zipcode": zipcode}

    body = dict(template)
    body["zipcode"] = zipcode
    body["email"]   = email
    status, resp = client.post("/ec-customer/address", body=body)
    if HttpClient.is_success(status, resp):
        return {"address_id": resp["body"]["address_id"], "zipcode": zipcode}
    raise RuntimeError(f"创建地址失败: {HttpClient.get_error(resp)}")


def get_default_address(client: HttpClient) -> dict:
    status, resp = client.get("/ec-customer/address")
    if status == 200 and isinstance(resp.get("body"), list):
        addrs = resp["body"]
        for a in addrs:
            if a.get("is_primary") == 1:
                return a
        if addrs:
            return addrs[0]
    return {}


# ============================================================
# 信用卡（Stripe 4242 测试卡）
# ============================================================

def get_profile_id(client: HttpClient, db_cfg: dict = None,
                   user_id: int = None) -> str:
    """获取 4242 测试卡的 profile_id，不存在则自动添加。"""
    # 先查 DB
    if db_cfg and user_id:
        row = _db_query_one(db_cfg,
            "SELECT profile_id FROM yamibuy_payment.payment_profile_card "
            "WHERE user_id=%s AND tail='4242' AND status=60 AND card_source=2 LIMIT 1",
            (user_id,))
        if row:
            return row["profile_id"]

    # 查接口
    status, resp = client.get("/ec-payment/card_stripe/profiles")
    if status == 200 and resp.get("body"):
        for p in resp["body"]:
            if str(p.get("tail", "")) == "4242":
                return p["profile_id"]

    # 都没有，添加新卡
    return add_test_card(client)


def add_test_card(client: HttpClient) -> str:
    """添加 Stripe 4242 测试卡，返回 profile_id。"""
    addr = get_default_address(client)
    if not addr:
        raise RuntimeError("用户没有收货地址，请先在 APP/网站添加地址后重试。")

    # Step 1: 获取 setup_intent
    status, resp = client.get("/ec-payment/card_stripe/card-secret")
    if not HttpClient.is_success(status, resp):
        raise RuntimeError(f"获取 card-secret 失败: {HttpClient.get_error(resp)}")
    body       = resp.get("body", {})
    si_id      = body.get("set_id") or body.get("setup_intent_id") or body.get("si_id")
    client_secret = body.get("client_secret")
    if not si_id or not client_secret:
        raise RuntimeError(f"未获取到 setup_intent: {body}")

    # Step 2: Stripe confirm
    stripe_url  = f"https://api.stripe.com/v1/setup_intents/{si_id}/confirm"
    stripe_data = f"payment_method=pm_card_visa&client_secret={client_secret}"
    stripe_headers = {
        "Authorization":  f"Bearer {STRIPE_PUBLISHABLE_KEY}",
        "Content-Type":   "application/x-www-form-urlencoded",
    }
    s_status, s_resp = client.post_raw(stripe_url, stripe_data, stripe_headers)
    if s_status >= 400:
        raise RuntimeError(f"Stripe confirm SetupIntent 失败: {str(s_resp)[:200]}")
    pm_id = s_resp.get("payment_method")
    if not pm_id:
        raise RuntimeError(f"Stripe 未返回 payment_method: {s_resp}")

    # Step 3: 保存卡
    profile_body = {
        "pm_id": pm_id, "tail": "4242", "head": "424242",
        "exp_year": "2030", "exp_month": "12",
        "firstname":  addr.get("firstname", "QA"),
        "lastname":   addr.get("lastname",  "Test"),
        "card_type":  "Visa",
        "account_num":         "4242424242424242",
        "origin_account_num":  "4242424242424242",
        "address_id": addr.get("address_id"),
        "address": {
            "firstname": addr.get("firstname", "QA"),
            "lastname":  addr.get("lastname",  "Test"),
            "address1":  addr.get("address1", ""),
            "address2":  addr.get("address2", ""),
            "city":      addr.get("city",     ""),
            "state":     addr.get("state",    ""),
            "zipcode":   addr.get("zipcode",  ""),
            "country":   addr.get("country",  "United States"),
            "phone":     addr.get("phone",    ""),
        },
    }
    status, resp = client.post("/ec-payment/card_stripe/profile", body=profile_body)
    if HttpClient.is_success(status, resp):
        pid = resp.get("body", {}).get("profile_id") if isinstance(resp.get("body"), dict) else None
        if pid:
            return pid

    # 保存失败或拿不到 id，再查一次接口
    status2, resp2 = client.get("/ec-payment/card_stripe/profiles")
    if status2 == 200 and resp2.get("body"):
        for p in resp2["body"]:
            if str(p.get("tail", "")) == "4242":
                return p["profile_id"]
    raise RuntimeError("添加 4242 测试卡失败，请检查账号状态。")


# ============================================================
# 购物车
# ============================================================

def clear_cart(client: HttpClient):
    status, resp = client.get("/ec-so/cart", extra_headers={"source_flag": "1"})
    if status != 200:
        return
    body = resp.get("body", {})
    if not isinstance(body, dict):
        return
    nums = []
    for seller in body.get("normal_items", []):
        for item in seller.get("items", []):
            n = item.get("item_number")
            if n and n not in nums:
                nums.append(n)
    for item in body.get("error_items", []):
        n = item.get("item_number")
        if n and n not in nums:
            nums.append(n)
    if nums:
        client.delete("/ec-so/cart", body=nums, extra_headers={"source_flag": "1"})


def add_to_cart(client: HttpClient, item_number: str, qty: int):
    status, resp = client.post(
        "/ec-so/cart",
        body=[{"item_number": item_number, "qty": qty, "check_status": 1}],
    )
    body   = resp.get("body", {})
    failed = body.get("failed_items", []) if isinstance(body, dict) else []
    if status != 200 or failed:
        err = failed[0].get("reason", str(failed[0])) if failed else HttpClient.get_error(resp)
        raise RuntimeError(f"加购失败 [{item_number}]: {err}")


def set_cart_zipcode(client: HttpClient, zipcode: str):
    client.put("/ec-customer/zipcode",
               body={"zipcode": zipcode, "country": "United States"})


# ============================================================
# 支付
# ============================================================

def _free_pay(client: HttpClient, purchase_id, amount: float):
    """金额为 0 时用免费支付接口。"""
    pid_str = str(purchase_id)
    md5_pid = hashlib.md5(pid_str.encode()).hexdigest()
    secret  = hashlib.md5((md5_pid + "secret").encode()).hexdigest()
    status, resp = client.post(
        "/ec-payment/free/charge?flow_version=1.0",
        body={"purchase_id": pid_str, "amount": amount, "currency": "USD", "secret": secret},
        extra_headers={"channel": "1", "y_platform": "pc", "y_version": "1"},
    )
    if not HttpClient.is_success(status, resp):
        raise RuntimeError(f"免费支付失败: {HttpClient.get_error(resp)}")


def pay(client: HttpClient, purchase_id, amount: float, profile_id: str):
    """Stripe 支付。"""
    # Step 1: enroll
    status, resp = client.post(
        "/ec-payment/card_stripe/enroll?flow_version=1.0",
        body={"purchase_id": str(purchase_id), "profile_id": profile_id,
              "currency": "USD", "version": 1, "zipcode": "91789", "amount": amount},
        extra_headers={"channel": "1", "y_platform": "pc", "y_version": "1"},
    )
    if not HttpClient.is_success(status, resp):
        raise RuntimeError(f"支付 enroll 失败: {HttpClient.get_error(resp)}")
    b          = resp["body"]
    pi_id      = b.get("pi_id")
    client_secret = b.get("client_secret")
    if not pi_id or not client_secret:
        raise RuntimeError(f"未获取到 pi_id/client_secret: {b}")

    # Step 2: Stripe confirm
    stripe_url  = f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm"
    stripe_data = f"payment_method=pm_card_visa&client_secret={client_secret}"
    stripe_headers = {
        "Authorization": f"Bearer {STRIPE_PUBLISHABLE_KEY}",
        "Content-Type":  "application/x-www-form-urlencoded",
    }
    _, stripe_resp = client.post_raw(stripe_url, stripe_data, stripe_headers)
    stripe_status  = stripe_resp.get("status", "succeeded")

    # Step 3: 通知后端
    status, resp = client.post(
        "/ec-payment/card_stripe/paymentIntent?flow_version=1.0",
        body={"piId": pi_id, "code": stripe_status or "succeeded"},
    )
    if not HttpClient.is_success(status, resp):
        raise RuntimeError(f"支付 paymentIntent 失败: {HttpClient.get_error(resp)}")


# ============================================================
# Checkout 辅助
# ============================================================

def build_vendor_list(checkout_body: dict) -> list:
    vendor_list = []
    for seller in checkout_body.get("seller_item_list", []):
        sl          = seller.get("shipping_list", [])
        shipping_id = seller.get("shipping_id") or (
            sl[0].get("shipping_id") or sl[0].get("id") if sl else None)
        vendor_list.append({
            "vendor_id":   seller.get("seller_id", 0),
            "shipping_id": shipping_id,
            "seller_sn":   seller.get("seller_sn", ""),
        })
    return vendor_list


def build_group_list(checkout_body: dict) -> list:
    group_list = []
    for seller in checkout_body.get("seller_item_list", []):
        sl          = seller.get("shipping_list", [])
        shipping_id = seller.get("shipping_id") or (
            sl[0].get("shipping_id") or sl[0].get("id") if sl else None)
        group_list.append({"group_id": seller.get("group_id"), "shipping_id": shipping_id})
    return group_list


def build_item_list(checkout_body: dict) -> list:
    item_list = []
    for seller in checkout_body.get("seller_item_list", []):
        for item in seller.get("item_list", []):
            item_list.append({
                "item_number": item.get("item_number"),
                "qty":         item.get("qty", 1),
                "is_gift":     item.get("is_gift", 0),
            })
    return item_list


# ============================================================
# 核心下单函数
# ============================================================

def place_order(
    env:             str,
    email:           str,
    pwd:             str,
    item_numbers:    List[str],       # ["item_number"] 或 ["item_number:qty"]
    wh:              str  = "001",
    zipcode_override: str = None,
    use_giftcard:    bool = False,
    use_points:      bool = False,
    coupon_code:     str  = None,
    count:           int  = 1,
) -> List[dict]:
    """
    完整下单流程。

    Parameters
    ----------
    env           : "UAT" / "GQC" / "DEV"
    email         : 下单账号邮箱
    pwd           : 账号密码
    item_numbers  : 商品列表，格式：["12345"] 或 ["12345:2", "67890:1"]（:后面是数量）
    wh            : 仓库编号，"001"=LA / "002"=NJ
    zipcode_override : 自定义 zipcode（可选）
    use_giftcard  : 是否使用礼卡抵扣
    use_points    : 是否使用积分抵扣
    coupon_code   : 优惠券兑换码（ps_code，可选）
    count         : 下单次数

    Returns
    -------
    results : list of dict，每次下单一条记录
        成功: {"success": True,  "order_sns": [...], "purchase_id": ..., "amount": ...}
        失败: {"success": False, "error": "..."}
    """
    cfg = ENV_CONFIG.get(env.upper())
    if not cfg:
        raise ValueError(f"不支持的环境: {env}，可选: UAT / GQC / DEV")

    db_cfg = DB_CONFIGS.get(env.upper())

    client = HttpClient(cfg["ec_base"])
    login(client, email, pwd)

    # 解析商品列表 -> [{item_number, qty}, ...]
    items_with_qty = []
    for entry in item_numbers:
        if ":" in str(entry):
            num, q = str(entry).rsplit(":", 1)
            items_with_qty.append({"item_number": num.strip(), "qty": int(q.strip())})
        else:
            items_with_qty.append({"item_number": str(entry).strip(), "qty": 1})

    if not items_with_qty:
        raise ValueError("item_numbers 不能为空")

    # 确保仓库地址
    other_wh  = "002" if wh == "001" else "001"
    wh_addr   = ensure_address(client, email, wh, zipcode_override)
    other_addr = ensure_address(client, email, other_wh)
    address_id = wh_addr["address_id"]
    zipcode    = zipcode_override or WH_ZIPCODE.get(wh, "91789")
    set_cart_zipcode(client, zipcode)

    # 获取 4242 测试卡
    user_row   = _db_query_one(db_cfg,
        "SELECT user_id FROM yamibuy_master.xysc_users WHERE email=%s LIMIT 1",
        (email,)) if db_cfg else None
    user_id    = user_row["user_id"] if user_row else None
    profile_id = get_profile_id(client, db_cfg, user_id)

    results = []
    for i in range(count):
        t0 = time.time()
        try:
            # 清购物车 -> 加购
            clear_cart(client)
            for entry in items_with_qty:
                add_to_cart(client, entry["item_number"], entry["qty"])

            # 兑换优惠券
            if coupon_code:
                client.post(
                    f"/ec-so/cart/coupon/convert/{coupon_code}?group_coupon=best",
                    body={},
                    extra_headers={"source_flag": "1", "y_platform": "H5"},
                )

            # Checkout
            checkout_item_list = [
                {"item_number": e["item_number"], "qty": e["qty"],
                 "item_type": 1, "is_gift": 0}
                for e in items_with_qty
            ]
            status, resp = client.post(
                "/ec-so/orders/checkout/physical/v2",
                body={
                    "user_address_id": address_id,
                    "source_flag":     1,  "pay_id": 4,
                    "is_use_point":    1 if use_points  else 0,
                    "is_use_giftcard": 1 if use_giftcard else 0,
                    "language":        "zh_CN", "business_unit": 1,
                    "order_type":      0, "currency": "USD",
                    "group_coupon":    "best",
                    "item_list":       checkout_item_list,
                },
                extra_headers={"source_flag": "1", "y_platform": "H5"},
            )
            if not HttpClient.is_success(status, resp) or not isinstance(resp.get("body"), dict):
                raise RuntimeError(f"Checkout 失败: {HttpClient.get_error(resp)}")

            checkout_body   = resp["body"]
            checkout_amount = checkout_body.get("total_order_amount")
            if checkout_amount is None:
                checkout_amount = checkout_body.get("total_amount", 0)

            # 提交订单
            status, resp = client.post(
                "/ec-so/orders/submit/physical/v2?flow_version=1.0",
                body={
                    "user_address_id":   address_id,
                    "pay_id":            4, "pay_type": 2, "source_flag": 1,
                    "is_use_point":      1 if use_points  else 0,
                    "is_use_giftcard":   1 if use_giftcard else 0,
                    "language":          "zh_CN", "business_unit": 1,
                    "order_type":        0, "currency": "USD",
                    "checkout_amount":   checkout_amount,
                    "settlement_amount": checkout_amount,
                    "profile_id":        profile_id,
                    "flow_version":      "1.0",
                    "group_coupon":      "best",
                    "item_list":         build_item_list(checkout_body),
                    "vendor_list":       build_vendor_list(checkout_body),
                    "group_list":        build_group_list(checkout_body),
                },
                extra_headers={"source_flag": "1", "y_platform": "H5"},
            )
            if not HttpClient.is_success(status, resp) or not isinstance(resp.get("body"), dict):
                body_val = resp.get("body")
                if isinstance(body_val, list) and body_val:
                    err = body_val[0].get("reason") or body_val[0].get("reason_en") or str(body_val)[:100]
                else:
                    err = HttpClient.get_error(resp)
                raise RuntimeError(f"提交订单失败: {err}")

            b           = resp["body"]
            purchase_id = b.get("purchase_id") or b.get("purchaseId")
            orders      = b.get("orders") or []
            order_sn    = orders[0].get("order_sn") if orders else str(purchase_id)

            # 支付
            if float(checkout_amount) > 0:
                pay(client, purchase_id, checkout_amount, profile_id)
            else:
                _free_pay(client, purchase_id, checkout_amount)

            # 等待支付处理
            time.sleep(VALIDATION_WAIT)

            # 查子单
            sub_orders = _db_query_all(db_cfg,
                "SELECT order_sn FROM yamibuy_master.xysc_order_info "
                "WHERE purchase_id=%s AND is_separate=0",
                (purchase_id,)) if db_cfg else []
            order_sns = [r["order_sn"] for r in sub_orders] if sub_orders else [order_sn]

            results.append({
                "success":     True,
                "env":         env,
                "email":       email,
                "purchase_id": purchase_id,
                "order_sns":   order_sns,
                "amount":      checkout_amount,
                "items":       [e["item_number"] for e in items_with_qty],
                "wh":          wh,
                "elapsed":     round(time.time() - t0, 1),
            })
            print(f"[{i+1}/{count}] OK  purchase_id={purchase_id}  "
                  f"order_sns={order_sns}  amount=${checkout_amount}")

        except Exception as e:
            results.append({
                "success": False,
                "env":     env,
                "email":   email,
                "error":   str(e),
                "elapsed": round(time.time() - t0, 1),
            })
            print(f"[{i+1}/{count}] FAIL: {e}")

    return results


# ============================================================
# CLI 入口
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Yami 测试环境下单脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认账号 UAT 下单（需要先在 --items 里指定商品）
  python place_order.py --items 7750086

  # 多个商品、指定数量
  python place_order.py --items 7750086:2,7750087:1

  # 指定环境和账号
  python place_order.py --env GQC --email test@yamibuy.com --pwd 111111 --items 1234567

  # 下多单
  python place_order.py --items 7750086 --count 3

  # NJ仓
  python place_order.py --items 7750086 --wh 002

  # 使用礼卡 + 积分
  python place_order.py --items 7750086 --use-giftcard --use-points
        """,
    )
    parser.add_argument("--env",   default="UAT",           help="环境: UAT / GQC / DEV（默认 UAT）")
    parser.add_argument("--email", default=DEFAULT_EMAIL,   help="账号邮箱")
    parser.add_argument("--pwd",   default=DEFAULT_PASSWORD, help="账号密码")
    parser.add_argument("--items", required=True,
                        help="商品编号，多个用逗号分隔，可带数量如 7750086:2,7750087:1")
    parser.add_argument("--wh",    default="001",           help="仓库: 001=LA / 002=NJ（默认 001）")
    parser.add_argument("--zipcode", default=None,          help="自定义 zipcode（可选）")
    parser.add_argument("--use-giftcard",  action="store_true", help="使用礼卡抵扣")
    parser.add_argument("--use-points",    action="store_true", help="使用积分抵扣")
    parser.add_argument("--coupon",        default=None,    help="优惠券兑换码（ps_code）")
    parser.add_argument("--count", type=int, default=1,     help="下单次数（默认 1）")
    return parser.parse_args()


def main():
    args = parse_args()

    # 解析商品列表（支持 "7750086:2,7750087:1" 格式）
    raw_items = [x.strip() for x in args.items.split(",") if x.strip()]

    print(f"\n{'='*55}")
    print(f"  env   : {args.env}")
    print(f"  email : {args.email}")
    print(f"  wh    : {args.wh}  ({WH_ZIPCODE.get(args.wh, '?')})")
    print(f"  items : {raw_items}")
    print(f"  count : {args.count}")
    if args.use_giftcard: print("  giftcard: on")
    if args.use_points:   print("  points  : on")
    if args.coupon:       print(f"  coupon: {args.coupon}")
    print(f"{'='*55}\n")

    results = place_order(
        env             = args.env,
        email           = args.email,
        pwd             = args.pwd,
        item_numbers    = raw_items,
        wh              = args.wh,
        zipcode_override = args.zipcode,
        use_giftcard    = args.use_giftcard,
        use_points      = args.use_points,
        coupon_code     = args.coupon,
        count           = args.count,
    )

    success = sum(1 for r in results if r["success"])
    failed  = len(results) - success
    print(f"\n{'='*55}")
    print(f"  done: {success} ok / {failed} fail / {len(results)} total")
    print(f"{'='*55}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
