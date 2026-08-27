# -*- coding: utf-8 -*-
"""
登录 / 注册 / token 管理

注册邮箱规则:
    默认: aitest{MMDD}{序号:02d}@yamibuy.com，如 aitest041001@yamibuy.com
    序号从 01 递增，当天已存在则自动 +1
    用户指定邮箱时直接使用
    默认密码: 111111

Hub admin token 缓存:
    登录后存入 hub_token_cache.json，23小时内复用，过期自动重新登录
    三个环境分开存储
"""

import json
import os
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from config import HUB_ADMIN_ACCOUNT, HUB_TOKEN_CACHE_FILE

if TYPE_CHECKING:
    from core.http_client import HttpClient
    from core.db import DbClient

# token 缓存文件路径（放在 skill 根目录）
_CACHE_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    HUB_TOKEN_CACHE_FILE
)

# Token 缓存有效期（秒）：23 小时
_TOKEN_CACHE_TTL: int = 23 * 3600


# ==================== Hub token 缓存 ====================

def _load_token_cache() -> Dict[str, Any]:
    """
    从文件加载 token 缓存。
    
    Returns:
        缓存字典，格式为 {env: {token, updated_at}}，加载失败返回空字典。
    """
    try:
        if os.path.exists(_CACHE_PATH):
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_token_cache(cache: Dict[str, Any]) -> None:
    """
    保存 token 缓存到文件。
    
    Args:
        cache: 缓存字典，格式为 {env: {token, updated_at}}。
    """
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """
    检查缓存条目是否有效（基于本地缓存时间）。
    
    Args:
        cache_entry: 缓存条目，包含 token 和 updated_at 字段。
    
    Returns:
        True 表示缓存有效（23小时内），False 表示已过期或无效。
    """
    try:
        updated_at = cache_entry.get("updated_at", "")
        if not updated_at:
            return False
        cache_time = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - cache_time).total_seconds() < _TOKEN_CACHE_TTL
    except Exception:
        return False


def _get_hub_token(client: "HttpClient", env: str = "UAT") -> str:
    """
    获取 Hub admin token，带缓存机制。
    
    优先从本地缓存读取，过期则重新登录并更新缓存。
    三个环境（UAT/GQC/DEV）分开存储。
    
    Args:
        client: HTTP 客户端实例。
        env: 环境名称，可选 UAT/GQC/DEV，默认 UAT。
    
    Returns:
        Hub admin token 字符串，获取失败返回空字符串。
    """
    cache = _load_token_cache()
    cache_entry = cache.get(env, {})
    token = cache_entry.get("token", "")

    # 基于本地缓存时间判断是否有效
    if token and _is_cache_valid(cache_entry):
        return token

    # 重新登录
    account = HUB_ADMIN_ACCOUNT.get(env, HUB_ADMIN_ACCOUNT["UAT"])
    url = client.central_base + "/hub/admin/login"
    data = json.dumps({"email": account["email"], "password": account["password"]}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read().decode("utf-8"))
            token = resp.get("body", {}).get("token", "")
    except Exception:
        return ""

    if token:
        cache[env] = {"token": token, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        _save_token_cache(cache)

    return token


# ==================== 邮箱生成 ====================

def _next_aitest_email(db: "DbClient", prefix: str = "autous") -> str:
    """
    生成当天下一个可用的测试邮箱。
    
    邮箱格式: {prefix}{MMDD}{序号:02d}@yamibuy.com
    例如: autous071901@yamibuy.com / autoca071901@yamibuy.com
    
    查询逻辑：查库中该前缀当天最大序号 +1，如果邮箱已存在则继续 +1 直到找到可用的。
    
    Args:
        db: 数据库客户端实例。
        prefix: 邮箱前缀，US 用 "autous"，CA 用 "autoca"。
    
    Returns:
        下一个可用的测试邮箱地址。
    """
    date_str = datetime.now().strftime("%m%d")
    # 查所有匹配的邮箱，取最大序号
    row = db.query_one(
        "SELECT email FROM yamibuy_master.xysc_users WHERE email LIKE %s ORDER BY user_id DESC LIMIT 1",
        (f"{prefix}{date_str}%@yamibuy.com",)
    )
    seq = 0
    if row:
        try:
            seq = int(row["email"].replace(f"{prefix}{date_str}", "").replace("@yamibuy.com", ""))
        except Exception:
            pass
    
    # 从 seq+1 开始尝试，如果已存在则继续递增（防止并发冲突）
    for attempt in range(seq + 1, seq + 20):
        candidate = f"{prefix}{date_str}{attempt:02d}@yamibuy.com"
        exists = db.query_one(
            "SELECT 1 FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
            (candidate,)
        )
        if not exists:
            return candidate
    
    # 兜底：用时间戳保证唯一
    import time
    ts = int(time.time()) % 10000
    return f"{prefix}{date_str}{ts}@yamibuy.com"


# ==================== 登录 / 注册 ====================

def login(client: "HttpClient", email: str, pwd: str) -> str:
    """
    用户登录获取 token。
    
    Args:
        client: HTTP 客户端实例。
        email: 用户邮箱。
        pwd: 用户密码。
    
    Returns:
        登录成功后的 token。
    
    Raises:
        RuntimeError: 获取匿名 token 失败或登录失败。
    """
    status, resp = client.get("/ec-customer/users/get_token")
    if status != 200 or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"获取匿名 token 失败: {client.get_error(resp)}")
    client.token = resp["body"]["token"]

    status, resp = client.post(
        "/ec-customer/users/login",
        body={"email": email, "pwd": pwd},
        extra_headers={"y_platform": "H5"},
    )
    if not client.is_success(status, resp) or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"登录失败 [{email}]: {client.get_error(resp)}")

    token = resp["body"]["token"]
    client.token = token
    return token


def register(
    client: "HttpClient",
    email: Optional[str] = None,
    pwd: str = "111111",
    db: Optional["DbClient"] = None,
    env: str = "UAT"
) -> Dict[str, Any]:
    """
    注册新用户并完成邮箱验证。
    
    注册流程:
        1. 生成邮箱（默认 aitest{MMDD}{seq}@yamibuy.com）
        2. 获取匿名 token → 注册 → 拿到 token + uid
        3. 调后台接口直接完成邮箱验证
    
    Args:
        client: HTTP 客户端实例。
        email: 用户邮箱，不填则自动生成。
        pwd: 用户密码，默认 111111。
        db: 数据库客户端实例，用于生成邮箱序号。
        env: 环境名称，默认 UAT。
    
    Returns:
        注册结果字典，包含 email, pwd, token, uid。
    
    Raises:
        RuntimeError: 获取匿名 token 失败、注册失败或未返回 token。
    """
    if not email:
        email = _next_aitest_email(db, "autous") if db else f"autous{datetime.now().strftime('%m%d')}01@yamibuy.com"

    # Step 1: 获取匿名 token
    status, resp = client.get("/ec-customer/users/get_token")
    if status != 200 or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"获取匿名 token 失败: {client.get_error(resp)}")
    client.token = resp["body"]["token"]

    # Step 2: 注册
    status, resp = client.post(
        "/ec-customer/users/register",
        body={"email": email, "pwd": pwd, "language": "zh_CN"},
        extra_headers={"y_platform": "H5", "y_language": "zh_CN"},
    )
    if not client.is_success(status, resp):
        raise RuntimeError(f"注册失败 [{email}]: {client.get_error(resp)}")

    body = resp.get("body", {})
    token = body.get("token", "")
    uid = body.get("uid", "")
    if not token:
        raise RuntimeError(f"注册成功但未返回 token: {body}")
    client.token = token

    # Step 3: 后台直接完成邮箱验证
    hub_token = _get_hub_token(client, env)
    orig_token = client.token
    if hub_token:
        client.token = hub_token
    status, resp = client.post(
        "/customer/customers/email/support/verify",
        body={"email": email},
        use_central=True,
    )
    client.token = orig_token
    if not client.is_success(status, resp):
        print(f"  ⚠️  邮箱验证接口失败（不影响造数据）: {client.get_error(resp)}")

    return {"email": email, "pwd": pwd, "token": token, "uid": uid}


def _random_ca_phone() -> str:
    """
    生成随机加拿大手机号，格式: +1-05XXXXXXXX（10位数字）。
    
    Returns:
        随机手机号字符串，如 +1-0541822783。
    """
    import random
    digits = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+1-05{digits}"


def register_ca(
    client: "HttpClient",
    email: Optional[str] = None,
    pwd: str = "111111",
    phone: Optional[str] = None,
    db: Optional["DbClient"] = None,
    env: str = "UAT"
) -> Dict[str, Any]:
    """
    注册 CA 站新用户（含手机验证）。
    
    CA 注册流程:
        1. 生成邮箱（默认 aitest{MMDD}{seq}@yamibuy.com）
        2. 获取匿名 token（带 site_code: ca header）
        3. 发送手机验证码（测试环境固定 123456）
        4. 调用注册接口（dual_verify=1 + 手机号 + 验证码）
        5. 后台直接完成邮箱验证
    
    Args:
        client: HTTP 客户端实例。
        email: 用户邮箱，不填则自动生成。
        pwd: 用户密码，默认 111111。
        phone: 手机号，不填则自动生成随机号（+1-05XXXXXXXX）。
        db: 数据库客户端实例，用于生成邮箱序号。
        env: 环境名称，默认 UAT。
    
    Returns:
        注册结果字典，包含 email, pwd, token, uid, phone。
    
    Raises:
        RuntimeError: 获取匿名 token 失败、发送验证码失败或注册失败。
    """
    if not email:
        email = _next_aitest_email(db, "autoca") if db else f"autoca{datetime.now().strftime('%m%d')}01@yamibuy.com"

    if not phone:
        phone = _random_ca_phone()

    # CA 站通过 site_code header 区分
    ca_headers = {"site_code": "ca", "y_platform": "H5", "y_language": "zh_CN"}

    # Step 1: 获取匿名 token
    status, resp = client.get("/ec-customer/users/get_token", extra_headers=ca_headers)
    if status != 200 or not resp.get("body", {}).get("token"):
        raise RuntimeError(f"获取匿名 token 失败: {client.get_error(resp)}")
    client.token = resp["body"]["token"]

    # Step 2: 发送手机验证码（测试环境 caRegisterPhoneMock=true，验证码固定 123456）
    status, resp = client.post(
        "/ec-customer/users/send_register_phone_code",
        body={"phone": phone},
        extra_headers=ca_headers,
    )
    if not client.is_success(status, resp):
        raise RuntimeError(f"发送手机验证码失败 [{phone}]: {client.get_error(resp)}")

    # Step 3: 注册（dual_verify=1，带手机号和验证码）
    phone_code = "123456"  # 测试环境固定验证码
    status, resp = client.post(
        "/ec-customer/users/register",
        body={
            "email": email,
            "pwd": pwd,
            "mobile_phone": phone,
            "phone_code": phone_code,
            "dual_verify": 1,
            "language": "zh_CN",
        },
        extra_headers=ca_headers,
    )
    if not client.is_success(status, resp):
        raise RuntimeError(f"CA 注册失败 [{email}]: {client.get_error(resp)}")

    body = resp.get("body", {})
    token = body.get("token", "")
    uid = body.get("uid", "")
    if not token:
        raise RuntimeError(f"CA 注册成功但未返回 token: {body}")
    client.token = token

    # Step 4: 后台直接完成邮箱验证
    hub_token = _get_hub_token(client, env)
    orig_token = client.token
    if hub_token:
        client.token = hub_token
    status, resp = client.post(
        "/customer/customers/email/support/verify",
        body={"email": email},
        use_central=True,
    )
    client.token = orig_token
    if not client.is_success(status, resp):
        print(f"  ⚠️  邮箱验证接口失败（不影响造数据）: {client.get_error(resp)}")

    return {"email": email, "pwd": pwd, "token": token, "uid": uid, "phone": phone}
